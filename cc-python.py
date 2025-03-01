#!/usr/bin/env python
from llog import log
import json
import hashlib
import base62
import base64
import os
import pymysql
import requests

def short_hash(text):
    """Generate a short hash of text for secure logging"""
    return hashlib.md5(str(text).encode()).hexdigest()[:8] if text else "none"

def retrieve_token(site_abbr='DE'):
    if not hasattr(retrieve_token, '_cache'):
        retrieve_token._cache = {
            'token': {},
            'oce_setting': None
        }
    
    if site_abbr in retrieve_token._cache['token']:
        log(f"retrieve_token] Using cached token for {site_abbr}")
        return retrieve_token._cache['token'][site_abbr]

    try:
        us, pw = base62.decodebytes(os.environ['M2B'])[3:].split(b':')
        co = pymysql.connect(host='100.97.175.75', port=3306, user=us, password=pw, database='base_ebay')
        cu = co.cursor()
        
        cu.execute("SELECT token FROM base_ebay.oce_kb_ebay_sites WHERE abbreviation = %s", (site_abbr,))
        token_result = cu.fetchone()
        token = token_result[0] if token_result else None
        
        if token:
            retrieve_token._cache['token'][site_abbr] = token
        
        # Get oce_setting if not already cached
        if retrieve_token._cache['oce_setting'] is None:
            cu.execute("SELECT value FROM `oce_setting` WHERE `key` = 'ebay_general_settings'")
            oce_result = cu.fetchone()
            if oce_result and oce_result[0]:
                try:
                    settings = json.loads(oce_result[0])
                    general_settings = settings.get('general', {})
                    app_id = general_settings.get('app_id', 'missing_app_id')
                    cert_id = general_settings.get('cert_id', 'missing_cert_id')
                    retrieve_token._cache['oce_setting'] = {
                        'app_id': app_id,
                        'cert_id': cert_id
                    }
                    log(f"retrieve_token] Cached oce_setting: app_id=[hash: {short_hash(app_id)}], cert_id=[hash: {short_hash(cert_id)}]")
                except (json.JSONDecodeError, AttributeError, TypeError) as e:
                    log(f"Failed to parse oce_setting JSON: {e}")
                    # Set default empty values to prevent repeated query attempts
                    retrieve_token._cache['oce_setting'] = {
                        'app_id': 'missing_app_id',
                        'cert_id': 'missing_cert_id'
                    }
        
        co.close()
        return token
    except KeyError:
        log("M2B environment variable not set")
        return None
    except Exception as e:
        log(f"Error retrieving token: {e}")
        return None

def parse_token(token):
    if not token:
        return None
    
    try:
        js = json.loads(token)
        access_token = js.get('access_token', '')
        log(f"parse_token] access_token: [hash: {short_hash(access_token)}]")
        return {
            'token_type': js.get('token_type'),
            'access_token': access_token,
            'expires_in': int(js.get('expires_in', 0)),
            'refresh_token': js.get('refresh_token'),
            'refresh_expires_in': int(js.get('refresh_token_expires_in', 0)),
        }
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        return {
            'raw': token,
            'error': str(e)
        }

def refresh_token_using_refresh_token(site_abbr='DE'):
    """Refresh the access token using the refresh token without client secret"""
    # Get the original token JSON
    old_token_json = retrieve_token(site_abbr)
    print("=== OLD TOKEN JSON ===")
    print(old_token_json)
    
    token_info = parse_token(old_token_json)
    if not token_info or 'refresh_token' not in token_info:
        log("No valid refresh token available")
        return None
        
    refresh_token = token_info.get('refresh_token')
    log(f"Found refresh token: [hash: {short_hash(refresh_token)}]")
    
    # Get app_id and cert_id from cache
    if not hasattr(retrieve_token, '_cache') or retrieve_token._cache['oce_setting'] is None:
        log("oce_setting not cached yet, initializing...")
        retrieve_token()
    
    if (not hasattr(retrieve_token, '_cache') or 
        not retrieve_token._cache['oce_setting'] or 
        retrieve_token._cache['oce_setting']['app_id'] == 'missing_app_id' or 
        retrieve_token._cache['oce_setting']['cert_id'] == 'missing_cert_id'):
        log("Missing app_id or cert_id from cache")
        return None
    
    app_id = retrieve_token._cache['oce_setting']['app_id']
    cert_id = retrieve_token._cache['oce_setting']['cert_id']
    log(f"Using app_id: [hash: {short_hash(app_id)}] and cert_id: [hash: {short_hash(cert_id)}]")
    
    auth_url = 'https://api.ebay.com/identity/v1/oauth2/token'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()}'
    }

    # According to eBay docs (https://developer.ebay.com/api-docs/static/oauth-refresh-token-request.html),
    # the scope parameter is technically optional, but recommended to maintain consistent access rights.
    # Setting scope to all required permissions ensures the refreshed token has the same authorization.
    # New refresh tokens may be issued when the existing refresh token is about to expire.
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        #'scope': 'https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly https://api.ebay.com/oauth/api_scope/sell.finances https://api.ebay.com/oauth/api_scope/sell.payment.dispute https://api.ebay.com/oauth/api_scope/commerce.identity.readonly https://api.ebay.com/oauth/api_scope/commerce.notification.subscription https://api.ebay.com/oauth/api_scope/commerce.notification.subscription.readonly'
    }
    log(data)

    try:
        log("Attempting to refresh token")
        response = requests.post(auth_url, headers=headers, data=data)
        log(f"Refresh status: {response.status_code}")

        if response.status_code == 200:
            # Clone the old token data first
            try:
                old_token_data = json.loads(old_token_json)
                new_token = old_token_data.copy()  # Clone the old token to preserve all fields
            except (json.JSONDecodeError, TypeError):
                # If old token can't be parsed, start with empty dict
                new_token = {}
                
            # Update with new response data
            new_token.update(response.json())
            log(new_token)
            
            # This preserves refresh_token naturally if not present in the response
            # But let's add explicit logging for clarity
            if 'refresh_token' not in response.json():
                log("eBay didn't return a refresh token in response, using preserved one")
            
            # Print the new token
            new_token_json = json.dumps(new_token)
            print("\n=== NEW TOKEN JSON ===")
            print(new_token_json)
            
            # Save old token to file before updating database
            from datetime import datetime
            
            # Create backup folder if it doesn't exist
            backup_dir = "token_backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Save old token with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_dir}/token_{site_abbr}_{timestamp}.json"
            
            with open(backup_file, "w") as f:
                f.write(old_token_json)
            log(f"Backed up old token to {backup_file}")
                
            # Update the token in the database (commented out for now)
            try:
                us, pw = base62.decodebytes(os.environ['M2B'])[3:].split(b':')
                co = pymysql.connect(host='100.97.175.75', port=3306, user=us, password=pw, database='base_ebay')
                cu = co.cursor()
                
                # Commented out database update
                cu.execute(
                    "UPDATE base_ebay.oce_kb_ebay_sites SET token = %s WHERE abbreviation = %s",
                    (new_token_json, site_abbr)
                )
                co.commit()
                log(f"Database update for site {site_abbr} commited")
                
                # Clear the cache to ensure the next retrieval gets the new token
                if hasattr(retrieve_token, '_cache') and site_abbr in retrieve_token._cache['token']:
                    del retrieve_token._cache['token'][site_abbr]
                
                co.close()
                return new_token
            except Exception as e:
                log(f"Error connecting to database: {e}")
                return new_token
        else:
            log(f"Token refresh failed: {response.status_code}")
            try:
                error_details = response.json()
                log(f"Error details: {error_details}")
            except:
                log(f"Error response: {response.text[:200]}")
            return None
    except Exception as e:
        log(f"Error refreshing token: {e}")
        return None

def search_items(search_string, limit=5, access_token=None):
    # Get token if not provided
    if not access_token:
        token_info = parse_token(retrieve_token())
        if not token_info:
            return None, "Failed to retrieve token"
        access_token = token_info.get('access_token')
        log(f"Using access token: [hash: {short_hash(access_token)}]")
    
    search_url = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
    headers = {
        'Authorization': f"Bearer {access_token}"
    }
    
    params = {
        'q': search_string,
        'limit': limit
    }
    
    try:
        response = requests.get(search_url, params=params, headers=headers)
        log(f"HTTP Status: {response.status_code}")
        
        # Check for token expiration (401 Unauthorized)
        if response.status_code == 401:
            log("Token appears to be expired, attempting refresh")
            new_token_info = refresh_token_using_refresh_token()
            
            if new_token_info and 'access_token' in new_token_info:
                new_access_token = new_token_info['access_token']
                log(f"Retrying with new token: [hash: {short_hash(new_access_token)}]")
                # Retry the search with the new token
                return search_items(search_string, limit, new_access_token)
        
        # Check for other HTTP errors
        if response.status_code != 200:
            error_message = f"HTTP Error: {response.status_code}"
            try:
                error_json = response.json()
                if 'errors' in error_json:
                    error_details = [err.get('message', '') for err in error_json.get('errors', [])]
                    error_message += f" - {', '.join(error_details)}"
                log(f"Error response: {error_json}")
            except:
                if response.text:
                    error_message += f" - {response.text[:100]}"
            return None, error_message
            
        response_json = response.json()
        log(f"Response JSON: {response_json.keys()}")
        
        if 'itemSummaries' in response_json:
            items = []
            for item in response_json['itemSummaries']:
                items.append({
                    'title': item.get('title'),
                    'id': item.get('itemId'),
                    'price': item.get('price', {}).get('value'),
                    'currency': item.get('price', {}).get('currency'),
                    'url': item.get('itemWebUrl')
                })
            return items, None
        elif 'warnings' in response_json:
            errors = [warn.get('message') for warn in response_json.get('warnings', [])]
            return None, errors
        else:
            return [], None
    except Exception as e:
        log(f"Exception: {e}")
        return None, str(e)


def test_token():
    # Test #1: First retrieval - should fetch from DB
    token = retrieve_token()
    if not token:
        log("Failed to retrieve token")
        return False
    
    parsed = parse_token(token)
    expected_fields = ['token_type', 'access_token', 'expires_in', 'refresh_token', 'refresh_expires_in']
    for field in expected_fields:
        if field not in parsed:
            log(f"Missing field: {field}")
            return False
    
    # Test #2: Second retrieval - should use cache
    token2 = retrieve_token()
    if token != token2:
        log("Cache verification failed - tokens don't match")
        return False
    
    # Test #3: Check oce_setting was cached
    if not hasattr(retrieve_token, '_cache') or not retrieve_token._cache['oce_setting']:
        log("Failed to retrieve oce_setting from cache")
        return False
    
    oce_setting = retrieve_token._cache['oce_setting']
    
    if 'app_id' not in oce_setting or 'cert_id' not in oce_setting:
        log(f"Missing app_id or cert_id in oce_setting: {oce_setting.keys()}")
        return False
    
    log('test_token.. pass')
    return True

def test_search():
    items, error = search_items("laptop", 3)
    if error:
        log(f"Search failed: {error}")
    else:
        log(f"Found {len(items)} items")
        for item in items:
            log(f"- {item['title']} ({item['price']} {item['currency']})")
    log('test_search.. done')

if __name__ == "__main__":
    test_token()
    test_search()
