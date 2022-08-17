#!/usr/bin/env python
import base64
import os
import traceback

import requests

EBAY_CONF = {
    'production': {
        'app_id': os.environ.get('EBAY_PRO_ID', ''),
        'secret': os.environ.get('EBAY_PRO', ''),
        'token_url': 'https://api.ebay.com/identity/v1/oauth2/token',
        'item_url': 'https://api.ebay.com/buy/browse/v1/item/'
    },
    'sandbox': {
        'app_id': os.environ.get('EBAY_SANDBOX_ID', ''),
        'secret': os.environ.get('EBAY_SANDBOX', ''),
        'token_url': 'https://api.sandbox.ebay.com/identity/v1/oauth2/token',
        'item_url': 'https://api.sandbox.ebay.com/buy/browse/v1/item/'
    }
}

LAST_TOKEN = None

def pick_conf():
  global EBAY_CONF
  return EBAY_CONF['production' if EBAY_CONF['production']['secret'] else 'sandbox']

def fetch_credentials():
  # global expiry_time
  global LAST_TOKEN, EBAY_CONF

  try:
    #check if last fetch is still having valid token
    #Enable this when running on server
    # if expiry_time and (datetime.datetime.now() < expiry_time):
    #   print('Using Previous fetched access token')
    #   return LAST_TOKEN
    conf = pick_conf()

    app_id = conf['app_id']
    if not app_id:
      raise Exception('No app_id')

    secret = conf['secret']
    if not secret:
      raise Exception('No secret')

    api_endpoint = conf['token_url']
    client_token = base64.b64encode(f"{app_id}:{secret}".encode('ascii')).decode('ascii')

    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f'Basic {client_token}'}
    request_params = {'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'}

    resp = requests.post(api_endpoint, data=request_params, headers=headers)

    # LAST_TOKEN is of the form {access_token, expires_in, token_type}
    LAST_TOKEN = resp.json()
    # expiry_time = datetime.datetime.now() + datetime.timedelta(0, int(LAST_TOKEN['expires_in']))

  except Exception as ex:
    print('fetchCredentials] Failed to fetch access token')
    raise ex

  return LAST_TOKEN


if __name__ == '__main__':
  print(fetch_credentials())
