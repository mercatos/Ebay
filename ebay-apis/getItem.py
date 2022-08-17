import requests
import clientCredentials
from clientConfig import clientConfig, is_dev_environment

def getItemDetails(item_id):
  client_config = clientConfig.get("production " if not is_dev_environment else "sandbox")
  api_endpoint = client_config.get("item_url", "")

  credentials = clientCredentials.fetchCredentials() #get credentials either by fetching or reusing the old token
  
  if not credentials:
    raise Exception("Unable to fetch product details due to no access token")
  
  headers = {
    'Authorization': f"Bearer {credentials['access_token']}"
  }
  
  print("Fetching product details")
  
  response = requests.get(f"{api_endpoint}{item_id}", params={'fieldgroups': 'PRODUCT'}, headers=headers)
  
  response_json = response.json()
  product_data = response_json.get('product', {})
  required_data = {
    'title': product_data.get('title', ''),
    'description': product_data.get('description', ''),
    'brand': product_data.get('brand', ''),
    'gtins': product_data.get('gtins', []),
    'image': product_data.get('image', {}), # this is again an object with a key imageUrl
    'mpns': product_data.get('mpns', []),
    'itemLocation': response_json.get('itemLocation', {}), # this is again an object with keys city, postalCode, country
    'price': response_json.get('price', {}), # this is again an object with value and currency
    'buyingOption': response_json.get('buyingOptions', []),
    'condition': response_json.get('condition', '')
  }
  
  print(required_data)
  print("Finshed fetching product details")
  
  return required_data

#sample id taken from ebay forum
getItemDetails('v1|110198777511|410084241125')