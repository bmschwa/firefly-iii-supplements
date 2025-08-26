import importlib

import requests

from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_balance_get_request_options import AccountsBalanceGetRequestOptions
from plaid.model.accounts_get_response import AccountsGetResponse
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_sync_request_options import TransactionsSyncRequestOptions

loader = importlib.import_module("plaid-ffiii-connector-config-loader")
plaid_client, config, ffiii_url, ffiii_pat  = loader.plaid_client, loader.config, loader.firefly_iii_url, loader.firefly_iii_pat

print(config)

to_reconcile = (308, "dORmZ481R5SK7bJz35LEHJJdoRMpD1IKLp51X")


ff_account_id, plaid_account_id = to_reconcile


def account_id_2_accesstoken(plaid_account_id):
    d = dict([(acctd['plaidAccountId'], acctd['plaidItemAccessToken'])
        for acctd in config.get('fireflyPlaidConnector2', {}).get('accounts', [])])
    return d[plaid_account_id]


abgr = AccountsBalanceGetRequest(access_token=account_id_2_accesstoken(plaid_account_id),
                          options=AccountsBalanceGetRequestOptions(account_ids=[plaid_account_id,]))

balr = plaid_client.accounts_balance_get(abgr)

response = AccountsGetResponse(accounts=balr.accounts, item=balr.item, request_id=balr.request_id)



# Current & available balances retrieved

tsr = TransactionsSyncRequest(access_token=account_id_2_accesstoken(plaid_account_id),
                        count=100,
                        cursor='',
                        options=TransactionsSyncRequestOptions(
                            account_id=plaid_account_id,
                            include_original_description=True,
                         ))

tsrr = plaid_client.transactions_sync(tsr)


#######

result = requests.get('/'.join([ffiii_url, 'api', 'v1', 'accounts', str(ff_account_id), 'transactions']),
                      headers={'Content-Type': 'application/json',
                               'accept': 'application/vnd.api+json',
                               'Authorization': f"Bearer {ffiii_pat}"
                               }
                      )
print(result.json())

# Todo: https://api-docs.firefly-iii.org/#/data/bulkUpdateTransactions
#       https://docs.firefly-iii.org/references/firefly-iii/api/specials/






