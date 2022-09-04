import requests
import datetime
import os
import base64

subdomain = os.environ.get('SUBDOMAIN', 'api.sandbox.ebay.com')
app_id = os.environ.get('APP_ID', '')
secret = os.environ.get('SECTRET', '')
token_url = f'https://{subdomain}/identity/v1/oauth2/token'

expiry_time = None
resp_json = None
def fetchCredentials():
  global expiry_time, resp_json
  # check if last fetch is still having valid token
  # Enable this when running on server
  if expiry_time and (datetime.datetime.now() < expiry_time):
    print("Using Previous fetched access token")
    global resp_json
    return resp_json

  client_token = base64.b64encode(f"{app_id}:{secret}".encode('ascii')).decode('ascii')

  headers = {
    'Content-Type': 'application/x-www-form-urlencoded', 
    'Authorization': f'Basic {client_token}'
  }
  request_params = {
    'grant_type': 'client_credentials',
    'scope': 'https://api.ebay.com/oauth/api_scope'
  }
  resp = requests.post(token_url, data=request_params, headers=headers)
  # resp_json is of the form {access_token, expires_in, token_type}
  resp_json = resp.json()
  expiry_time = datetime.datetime.now() + datetime.timedelta(0, int(resp_json['expires_in']))
  
  return resp_json
