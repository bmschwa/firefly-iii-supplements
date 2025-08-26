import os
import datetime
from collections import defaultdict
from decimal import Decimal

import pandas as pd
import yaml

import requests

config_file = os.environ.get("FF_III_CONNECTOR_2_CONFIG")
cursor_file = os.environ.get("FF_III_CONNECTOR_2_CURSOR")

import plaid
from plaid.api import plaid_api
from plaid.exceptions import ApiException
from plaid.model.accounts_get_request import AccountsGetRequest

with open(config_file) as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise

# plaid docs: https://plaid.com/docs/api/
# ffiii docs: https://api-docs.firefly-iii.org/#


pc = config.get('fireflyPlaidConnector2', {}).get('plaid')
plaid_conf = plaid.Configuration(
    host=pc['url'],
    api_key={
        'clientId': pc['clientId'],
        'secret': pc['secret']
    }
)

plaid_api_client = plaid.ApiClient(plaid_conf)
plaid_client = plaid_api.PlaidApi(plaid_api_client)


# Lets get info about what connections we have connected (this could be for multiple users)


revoke_these = ["access-production-891102ad-7a44-4c93-999f-c70f5b34f6f3", "access-production-c5ceb062-7c49-42a6-a7db-dd61d4fe2ac6"]
from plaid.model.item_access_token_invalidate_request import ItemAccessTokenInvalidateRequest
from plaid.model.item_remove_request import ItemRemoveRequest

for r in revoke_these:
    iati = ItemAccessTokenInvalidateRequest(r)

    # Retrieves a new one
    #rr = plaid_client.item_access_token_invalidate(iati)
    #print(f"Invalidated: {rr}")

    irr = ItemRemoveRequest(access_token=r)
    try:
        rr = plaid_client.item_remove(irr)
    except(plaid.exceptions.ApiException):
        print("Could not remove... probably wasn't there...")
    else:
        print(f"Removed: {rr}")


# Sort for unique creds from plai :)
discovered_ff_accts = set()
discovered_plaid_accts = set()
unique_plaid = defaultdict(list)
ff_acct_plaid_key_map = {}
plaid_acct_to_inst = {}
for acctd in config.get('fireflyPlaidConnector2', {}).get('accounts', []):
    unique_plaid[acctd['plaidItemAccessToken']].append((acctd['fireflyAccountId'], acctd['plaidAccountId']))
    ff_acct_plaid_key_map[acctd['plaidAccountId']] = acctd['plaidItemAccessToken']
    if acctd['plaidAccountId'] in discovered_plaid_accts:
        print(f"Plaid Account {acctd['plaidAccountId']} already in this file")
    else:
        discovered_plaid_accts.add(acctd['plaidAccountId'])

print(f"{len(unique_plaid)} Sets of plaid creds")

########################################################################################################################
#
# lets just see what the state of our access tokens is like,.
#
#
from plaid.model.auth_get_request import AuthGetRequest
for t in unique_plaid.keys():
    try:
        auth_response = plaid_client.auth_get( AuthGetRequest(access_token=t) )
    except ApiException as e:
        print(f"FAILED ON {t}: {e}")
    else:
        print(auth_response)


##############################



firefly_iii_url = config.get('fireflyPlaidConnector2', {}).get('firefly').get('url')
firefly_iii_pat = config.get('fireflyPlaidConnector2', {}).get('firefly').get('personalAccessToken')

plaid_ff_acct_match = []
tmp_plaid_acct = {}
for acctd in config.get('fireflyPlaidConnector2', {}).get('accounts', []):

    if acctd['fireflyAccountId'] in discovered_ff_accts:
        print(f"Already saw firefly account {acctd['fireflyAccountId']}")
    else:
        discovered_ff_accts.add(acctd['fireflyAccountId'])

    result = requests.get('/'.join([firefly_iii_url, 'api', 'v1', 'accounts', str(acctd['fireflyAccountId'])]),
                           headers={'Content-Type': 'application/json',
                                    'accept': 'application/vnd.api+json',
                                    'Authorization': f"Bearer {firefly_iii_pat}"
                            }
                          )

    if not result.ok:
        print(f"Failed getting....{acctd['fireflyAccountId']}")

    try:
        token_map = unique_plaid.pop(acctd['plaidItemAccessToken']) # Look up the access token for this plaid acct; it may be used by multiple accounts
    except KeyError:
        print(f"Already requested for {acctd['plaidItemAccessToken']} ({acctd['fireflyAccountId']}; {acctd['plaidAccountId']})")
        plaid_ff_acct_match.append((tmp_plaid_acct.pop(acctd['plaidAccountId']), result.json()['data']))

    else:
        accounts_get_request = AccountsGetRequest(
           access_token=acctd['plaidItemAccessToken']
        )
        acct_get_response = plaid_client.accounts_get(accounts_get_request)


        print(f"Using access token {acctd['plaidItemAccessToken']}, received data on {', '.join([p['account_id'] for p in acct_get_response['accounts']])}")
        for plaid_acct in acct_get_response['accounts']:
            matched = False
            plaid_acct_to_inst[plaid_acct.account_id] = (acct_get_response.item.institution_id,
                                                         acct_get_response.item.institution_name,
                                                         acct_get_response.item.item_id)
            for ff_acct_id, plaid_acct_id in token_map:

                if plaid_acct['account_id'] == plaid_acct_id and ff_acct_id == acctd['fireflyAccountId']:
                    plaid_ff_acct_match.append((plaid_acct, result.json()['data']))
                    print(f"Matched {plaid_acct['account_id']} with {ff_acct_id} using {acctd['plaidItemAccessToken']}")
                    matched = True
            if not matched:
                tmp_plaid_acct[plaid_acct['account_id']] = plaid_acct
                print(f"Retrieved info for Plaid account {plaid_acct['account_id']} using token {acctd['plaidItemAccessToken']}; saving for later")

assert(len(unique_plaid) == 0)
for pid, pacc in tmp_plaid_acct.items():
    print(f"Received information for account {pid} from Plaid; not included in ff?")

# all equeal counts: matched & discovered
if len(plaid_ff_acct_match) != len(discovered_ff_accts) or len(plaid_ff_acct_match) != len(discovered_plaid_accts):
    print(f"Mismatched Plaid Accounts: {', '.join(set([a.account_id for (a, b) in plaid_ff_acct_match]).symmetric_difference(discovered_plaid_accts))}")
    print(f"Mismatched Firefly Accounts: {', '.join(map(str, set([int(b['id']) for (a, b) in plaid_ff_acct_match]).symmetric_difference(discovered_ff_accts)))}")

data_pd = []

cents = Decimal("0.01")
for plaid_acct, ff_acct in plaid_ff_acct_match:
    plaid_instid, plaid_instname, plaid_itemid = plaid_acct_to_inst[plaid_acct.account_id]
    data_pd.append(
        {
            "ff_id": int(ff_acct['id']),
            "ff_name": ff_acct['attributes']['name'],
            "ff_updated_at_dt": datetime.datetime.fromisoformat(ff_acct['attributes']['updated_at']),
            "ff_last_activity_dt": datetime.datetime.fromisoformat(ff_acct['attributes']['last_activity']),
            "ff_current_balance_dt": datetime.datetime.fromisoformat(ff_acct['attributes']['current_balance_date']),
            "ff_current_balance": Decimal(ff_acct['attributes']['current_balance']).quantize(cents),
            "ff_current_active": ff_acct['attributes']['active'],

            "plaid_id": plaid_acct.account_id,
            "plaid_name": plaid_acct.name,
            "plaid_type": plaid_acct.type,
            "plaid_subtype": plaid_acct.subtype,
            "plaid_official_name": plaid_acct.official_name,
            "plaid_current_balance": Decimal(plaid_acct.balances.current).quantize(cents),

            "plaid_institution_name": plaid_instname,
            "plaid_institution_id": plaid_instid,
            "plaid_itemid": plaid_itemid,
        }
    )

banking_df = pd.DataFrame.from_records(data_pd)
banking_df.to_csv("sensitive_banking.csv")

# https://stackoverflow.com/a/30691921
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print(banking_df)