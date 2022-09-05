# search on Ebay via API --> JSON
Search products via keyword query and compare prices on [Ebay via API](https://developer.ebay.com/api-docs/buy/browse/overview.html).

Developer account required: https://developer.ebay.com/develop/apis

The script allows you to make the following requests to Ebay via the API and get the result in JSON format:

## 1. Search for products using the API:

  https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search

## 2. Get information about a product by its ID on Ebay: 

https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem

- price and price type (auction or fixed price)
- header
- description
- category
- condition of the goods (new / used ...)
- product location
- pictures
- ....

# Configuration
To run, the scripts require the following environment variables to be set"
APP_ID The Ebay API or Sandbox API App ID
SECRET Ebay API or Sandbox API App Secret
SUBDOMAIN this can either be api.ebay.com or api.sandbox.ebay.com. If left blank, api.sandbox.ebay.com is used

For convinience, there is an example.env file in the repository. Make a copy and rename it to .env.
Set the appropriate values.
Also included is a file load_env.sh. Before running any command run `source load_env.sh`. That will set the variables

#Unit tests
Added the first unit test in the tests. Data for the test is a series of pickeled results from actual API requests.
To install dependencies, use the requirements_dev.txt
