import requests
import clientCredentials

prod_url = 'https://api.ebay.com/buy/browse/v1/item/'
sandbox_url = 'https://api.sandbox.ebay.com/buy/browse/v1/item/'

def getItemDetails(item_id):
  credentials = clientCredentials.fetchCredentials() #get credentials either by fetching or reusing the old token
  headers = {
    'Authorization': f"Bearer {credentials['access_token']}"
  }
  response = requests.get(f"{sandbox_url}{item_id}", params={'fieldgroups': 'PRODUCT'}, headers=headers)
  response_json = response.json()
  required_data = {
    'title': response_json['title'],
    'description': response_json['description'],
    'brand': '',
    'gtins': '',
    'image': response_json['image'], # this is again an object with a key imageUrl
    'mpns': '',
    'itemLocation': response_json['itemLocation'], # this is again an object with keys city, postalCode, country
    'price': response_json['price'], # this is again an object with value and currency
    'buyingOption': response_json['buyingOptions'],
    'condition': response_json['condition']
  }
  print(required_data)

#sample id taken from ebay forum
getItemDetails('v1|110198777511|410084241125')