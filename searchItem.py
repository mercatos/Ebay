from distutils.log import error
import warnings
import requests
import getCredentials
import utils, os

subdomain = os.environ.get('SUBDOMAIN', 'api.sandbox.ebay.com')

search_url = f'https://{subdomain}/buy/browse/v1/item_summary/search'
item_url = f'https://{subdomain}/buy/browse/v1/item/'

def getItemSummary(search_string,
                    limit=15, 
                    offset=0, 
                    condition=None, 
                    buyingOption=None,
                    deliveryCountry=None,
                    epid=None,
                    return_raw=False):
  credentials = getCredentials.fetchCredentials()
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
    
  response = requests.get(f"{search_url}",
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



def getItem(itemId):
  credentials = getCredentials.fetchCredentials()
  headers = {
    'Authorization': f"Bearer {credentials['access_token']}"
  }
    
  response = requests.get(f"{item_url}" + itemId,
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
  items, errors = getItemSummary('laptop', 15, 0, 'Used|Excellent - Refurbished|Good|New', 'FIXED_PRICE', 'US')
  print(items, errors)
