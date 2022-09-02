from distutils.log import error
import warnings
import requests
import getCredentials
import utils

prod_url_search = 'https://api.ebay.com/buy/browse/v1/item/'
sandbox_url_search = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search'
sandbox_url_item = 'https://api.sandbox.ebay.com/buy/browse/v1/item/'

def getItemSummary(search_string,
                    limit=15, 
                    offset=0, 
                    condition=None, 
                    buyingOption=None,
                    deliveryCountry=None,
                    epid=None,
                    credentials=None,
                    return_raw=False,
                    fieldgroups=None):
  credentials = credentials or getCredentials.fetchCredentials()
  headers = {
    'Authorization': f"Bearer {credentials['access_token']}"
  }
  params = {
    'q': search_string,
    'limit': limit,
    'offset': offset,
  }

  filter = ''
  comma = ''
  if condition:
    fc = utils.getConditionId(condition)
    filter += 'conditionIds:{'+fc+'}'
    comma = ','

  if buyingOption:
    filter += comma + 'buyingOptions:{'+buyingOption+'}'
    comma = ','

  if deliveryCountry:
    filter += comma + 'deliveryCountry:'+deliveryCountry

  if filter != '':
    params['filter'] = filter

  if epid:
    params['epid'] = epid

  if fieldgroups:
    params['fieldgroups'] = 'PRODUCT'
    
  response = requests.get(f"{sandbox_url_search}", 
    params=params,
    headers=headers
  )
  response_json = response.json()

  required_data = []
  errors = []
  if 'itemSummaries' in response_json:
    if return_raw:
      return response_json['itemSummaries'], None

    for item in response_json['itemSummaries']:
      required_data.append({
        'Item ID': item['title'],
        'Item Title': item['itemId'],
        'Price': item['price'],
        'buyingOption': item['buyingOptions'],
        'condition': item['condition'],
        'URL': item['itemWebUrl']
      })
    return required_data, None
    
  elif 'warnings' in response_json:
    for warn in response_json['warnings']:
      errors.append(warn['message'])
    return None, errors
  else:
    return [], None



def getItem(itemId, credentials=None):
  credentials = credentials or getCredentials.fetchCredentials()
  headers = {
    'Authorization': f"Bearer {credentials['access_token']}"
  }
    
  response = requests.get(f"{sandbox_url_item}" + itemId, 
    headers=headers
  )
  response_json = response.json()

  return response_json

# --- Buying Options ---
# FIXED_PRICE
# AUCTION
# BEST_OFFER
# CLASSIFIED_AD


if __name__ == "__main__":
  items, errors = getItemSummary('laptop', 15, 0, 'Used|Excellent - Refurbished|Good', 'FIXED_PRICE', 'US')
  print(items, errors)
