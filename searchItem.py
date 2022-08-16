import requests
import getCredentials
import utils

prod_url_search = 'https://api.ebay.com/buy/browse/v1/item/'
sandbox_url_search = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search'

def getItemDetails(search_string, limit=15, offset=0, condition='New', buyingOption='FIXED_PRICE', deliveryCountry='US'):
  credentials = getCredentials.fetchCredentials()
  headers = {
    'Authorization': f"Bearer {credentials['access_token']}"
  }
  fc = utils.getConditionId(condition)
  response = requests.get(f"{sandbox_url_search}", 
    params={
      'q': search_string, 
      'limit': limit, 
      'offset': offset, 
      'filter': 'conditionIds:{'+fc+'}&buyingOption:{'+buyingOption+'}&deliveryCountry:'+deliveryCountry
    },
    headers=headers
  )
  response_json = response.json()
  required_data = []
  if 'itemSummaries' in response_json:
    for item in response_json['itemSummaries']:
      required_data.append({
        'Item ID': item['title'],
        'Item Title': item['itemId'],
        'Price': item['price'],
        'buyingOption': item['buyingOptions'],
        'condition': item['condition'],
        'URL': item['itemWebUrl']
      })

    return required_data


# --- Buying Options ---
# FIXED_PRICE
# AUCTION
# BEST_OFFER
# CLASSIFIED_AD

print(getItemDetails('laptop', 15, 0, 'Used|Excellent - Refurbished', 'FIXED_PRICE', 'US'))
    