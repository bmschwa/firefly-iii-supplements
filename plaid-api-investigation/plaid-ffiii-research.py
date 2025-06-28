import os
from collections import defaultdict

import yaml

import requests

config_file = os.environ.get("FF_III_CONNECTOR_2_CONFIG")
cursor_file = os.environ.get("FF_III_CONNECTOR_2_CURSOR")

import plaid
from plaid.api import plaid_api
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

# Sort for unique creds from plai :)
discovered_ff_accts = set()
discovered_plaid_accts = set()
unique_plaid = defaultdict(list)
ff_acct_plaid_key_map = {}
for acctd in config.get('fireflyPlaidConnector2', {}).get('accounts', []):
    unique_plaid[acctd['plaidItemAccessToken']].append((acctd['fireflyAccountId'], acctd['plaidAccountId']))
    ff_acct_plaid_key_map[acctd['plaidAccountId']] = acctd['plaidItemAccessToken']
    if acctd['plaidAccountId'] in discovered_plaid_accts:
        print(f"Plaid Account {acctd['plaidAccountId']} already in this file")
    else:
        discovered_plaid_accts.add(acctd['plaidAccountId'])

print(f"{len(unique_plaid)} Sets of plaid creds")

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
print("matched firefly accounts with plaid accounts")


