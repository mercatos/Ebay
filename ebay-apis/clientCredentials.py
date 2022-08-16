import requests
# import datetime
import base64
from clientConfig import is_dev_environment, clientConfig

# expiry_time = None
resp_json = None

def fetchCredentials():
  # global expiry_time
  global resp_json
  
  try:
    #check if last fetch is still having valid token
    #Enable this when running on server
    # if expiry_time and (datetime.datetime.now() < expiry_time):
    #   print("Using Previous fetched access token")
    #   return resp_json
    client_config = clientConfig.get("production " if not is_dev_environment else "sandbox")
    client_id = client_config.get("client_id", "")
    client_secret = client_config.get("client_secret", "")
    api_endpoint = client_config.get("token_url", "")
    client_token = base64.b64encode(f"{client_id}:{client_secret}".encode('ascii')).decode("ascii")

    headers = {
      'Content-Type': 'application/x-www-form-urlencoded', 
      'Authorization': f'Basic {client_token}' #this is a sandbox token
    }
    request_params = {
      'grant_type': 'client_credentials',
      'scope': 'https://api.ebay.com/oauth/api_scope'
    }

    print("Fetching access token")
    
    resp = requests.post(api_endpoint, data=request_params, headers=headers)
    
    # resp_json is of the form {access_token, expires_in, token_type}
    resp_json = resp.json()
    # expiry_time = datetime.datetime.now() + datetime.timedelta(0, int(resp_json['expires_in']))
    print("Finshed fetching access token")

  except Exception as e:
    import traceback
    print("Failed to fetch access token", e)
    print("Error stack trace", traceback.format_exc())
  
  return resp_json