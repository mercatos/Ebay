import requests
import datetime

sandbox_url = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'
prod_url = 'https://api.ebay.com/identity/v1/oauth2/token'

expiry_time = None
resp_json = None
def fetchCredentials():
  global expiry_time
  #check if last fetch is still having valid token
  #Enable this when running on server
  # if expiry_time and (datetime.datetime.now() < expiry_time):
  #   print("Using Previous fetched access token")
  #   return resp_json
  
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded', 
    'Authorization': 'Basic QWR2ZXJ0TWUtZGVhbHMtU0JYLTdiMWFjNDEwMi1jYzQ4YjM0MDpTQlgtYjFhYzQxMDJmNzVhLTA5NjUtNGIyZC1hOGQ0LTY5MWQ=' #this is a sandbox token
  }
  request_params = {
    'grant_type': 'client_credentials',
    'scope': 'https://api.ebay.com/oauth/api_scope'
  }
  resp = requests.post(sandbox_url, data=request_params, headers=headers)
  # resp_json is of the form {access_token, expires_in, token_type}
  resp_json = resp.json()
  expiry_time = datetime.datetime.now() + datetime.timedelta(0, int(resp_json['expires_in']))
  # print(resp.text, resp.headers, resp.json())
  return resp_json