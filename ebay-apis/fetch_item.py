#!/usr/bin/env python
import requests
import client_credentials


def fetch_item(item_id):
  conf = client_credentials.pick_conf()
  api_endpoint = conf['item_url']

  credentials = client_credentials.fetch_credentials()

  headers = {'Authorization': f"Bearer {credentials['access_token']}"}

  response = requests.get(f"{api_endpoint}{item_id}", params={'fieldgroups': 'PRODUCT'}, headers=headers)

  return response.json()


if __name__ == '__main__':
  #sample id taken from ebay forum
  print(fetch_item('v1|110198777511|410084241125'))
