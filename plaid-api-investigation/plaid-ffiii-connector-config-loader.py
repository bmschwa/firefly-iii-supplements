import os
import yaml

config_file = os.environ.get("FF_III_CONNECTOR_2_CONFIG")
cursor_file = os.environ.get("FF_III_CONNECTOR_2_CURSOR")

import plaid
from plaid.api import plaid_api

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
firefly_iii_url = config.get('fireflyPlaidConnector2', {}).get('firefly').get('url')
firefly_iii_pat = config.get('fireflyPlaidConnector2', {}).get('firefly').get('personalAccessToken')

