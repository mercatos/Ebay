import os

is_dev_environment = os.environ.get('is_dev_environment', "0") == "1"
#this object holds the keys for the secrets and is used in creating access token
clientConfig = {
  "production": {
    "client_id": os.environ.get('client_id') or "",
    "client_secret": os.environ.get('client_secret') or "",
    "token_url": 'https://api.ebay.com/identity/v1/oauth2/token',
    "item_url": "https://api.ebay.com/buy/browse/v1/item/"
  },
  "sandbox": {
    "client_id": os.environ.get('client_id') or "",
    "client_secret": os.environ.get('client_secret') or "",
    "token_url":'https://api.sandbox.ebay.com/identity/v1/oauth2/token',
    "item_url": "https://api.sandbox.ebay.com/buy/browse/v1/item/"
  }
}
