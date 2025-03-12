#!/usr/bin/env python
from datetime import datetime, timedelta
from llog import log
import base62
import base64
import hashlib
import json
import os
import pymysql
import requests
import xml.etree.ElementTree as ET


def short_hash(text):
    """Generate a short hash of text for secure logging"""
    return hashlib.md5(str(text).encode()).hexdigest()[:8] if text else "none"


def get_db_connection():
    if not hasattr(get_db_connection, '_connection'):
        get_db_connection._connection = None

    if get_db_connection._connection:
        return get_db_connection._connection

    us, pw = base62.decodebytes(os.environ['M2B'])[3:].split(b':')
    connection = pymysql.connect(
        host='100.97.175.75', port=3306, user=us, password=pw, database='base_ebay')
    get_db_connection._connection = connection
    return connection


def retrieve_token():
    if not hasattr(retrieve_token, '_cache'):
        retrieve_token._cache = None

    if retrieve_token._cache:
        return retrieve_token._cache

    co = get_db_connection()
    cu = co.cursor()

    cu.execute(
        "SELECT token FROM base_ebay.oce_kb_ebay_sites WHERE abbreviation = 'DE'")
    token_result = cu.fetchone()
    token = token_result[0]

    cu.execute(
        "SELECT value FROM `oce_setting` WHERE `key` = 'ebay_general_settings'")
    oce_result = cu.fetchone()

    settings = json.loads(oce_result[0])
    general_settings = settings.get('general')
    if not general_settings:
        raise ValueError("Missing 'general' section in ebay_general_settings")

    app_id = general_settings.get('app_id')
    cert_id = general_settings.get('cert_id')

    if not app_id or not cert_id:
        raise ValueError("Missing app_id or cert_id in ebay_general_settings")

    oce_setting = {
        'app_id': app_id,
        'cert_id': cert_id,
        'dev_id': general_settings.get('dev_id')
    }

    retrieve_token._cache = (token, oce_setting)
    return retrieve_token._cache


def parse_token(token):
    if not token:
        raise ValueError("Token is empty or None")

    try:
        js = json.loads(token)
        access_token = js.get('access_token')
        if not access_token:
            raise ValueError("Token missing 'access_token' field")

        return {
            'token_type': js.get('token_type'),
            'access_token': access_token,
            'expires_in': int(js.get('expires_in', 0)),
            'refresh_token': js.get('refresh_token'),
            'refresh_expires_in': int(js.get('refresh_token_expires_in', 0)),
        }
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        raise ValueError(f"Error parsing token: {e}")


def refresh_token_using_refresh_token():
    """Refresh the access token using the refresh token without client secret"""
    # Get the original token JSON, in order to preserve refresh_token
    token, oce_setting = retrieve_token()
    old_token_json = token

    try:
        token_obj = json.loads(old_token_json)
        if 'refresh_token' not in token_obj:
            raise ValueError("Old token JSON doesn't contain refresh_token")
    except json.JSONDecodeError:
        raise ValueError("Failed to parse old token JSON")

    token_info = parse_token(old_token_json)
    if not token_info or 'refresh_token' not in token_info:
        raise ValueError("No valid refresh token available")

    refresh_token = token_info.get('refresh_token')
    log(f"Found refresh token: [hash: {short_hash(refresh_token)}]")

    app_id = oce_setting['app_id']
    cert_id = oce_setting['cert_id']
    log(f"Using app_id: [hash: {short_hash(app_id)}] and cert_id: [hash: {short_hash(cert_id)}]")

    # According to eBay docs (https://developer.ebay.com/api-docs/static/oauth-refresh-token-request.html),
    # the scope parameter is technically optional, but recommended to maintain consistent access rights.
    # Setting scope to all required permissions ensures the refreshed token has the same authorization.
    # New refresh tokens may be issued when the existing refresh token is about to expire.
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        # 'scope': 'https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly https://api.ebay.com/oauth/api_scope/sell.finances https://api.ebay.com/oauth/api_scope/sell.payment.dispute https://api.ebay.com/oauth/api_scope/commerce.identity.readonly https://api.ebay.com/oauth/api_scope/commerce.notification.subscription https://api.ebay.com/oauth/api_scope/commerce.notification.subscription.readonly'
    }

    try:
        log("Attempting to refresh token")
        response = requests.post(
            'https://api.ebay.com/identity/v1/oauth2/token',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()}'
            },
            data=data
        )
        log(f"api.ebay.com/identity/v1/oauth2/token: {response.status_code}")

        if response.status_code == 200:
            old_token_data = json.loads(old_token_json)
            new_token = old_token_data.copy()  # Clone the old token to preserve all fields

            new_token.update(response.json())

            if 'refresh_token' not in response.json():
                log("eBay didn't return `refresh_token` in response, using preserved one")

            new_token_json = json.dumps(new_token)

            backup_dir = "token_backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_dir}/token_{timestamp}.json"

            with open(backup_file, "w") as f:
                f.write(old_token_json)
            log(f"Backed up old token to {backup_file}")

            co = get_db_connection()
            cu = co.cursor()

            cu.execute(
                "UPDATE base_ebay.oce_kb_ebay_sites SET token = %s WHERE abbreviation = 'DE'",
                (new_token_json,)
            )
            co.commit()
            log(f"oce_kb_ebay_sites commit ☑")

            # Clear the cache to ensure the next retrieval gets the new token
            if hasattr(retrieve_token, '_cache'):
                retrieve_token._cache = None

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
    if not access_token:
        token, _ = retrieve_token()
        token_info = parse_token(token)
        access_token = token_info['access_token']

    response = requests.get('https://api.ebay.com/buy/browse/v1/item_summary/search',
                            params={'q': search_string, 'limit': limit},
                            headers={'Authorization': f"Bearer {access_token}"})

    if response.status_code == 401:
        error_text = response.text
        log(f"Auth error: {error_text}")
        log("Token appears to be expired, attempting refresh")
        new_token_info = refresh_token_using_refresh_token()

        if new_token_info and 'access_token' in new_token_info:
            new_access_token = new_token_info['access_token']
            log(
                f"Retrying with new token: [hash: {short_hash(new_access_token)}]")
            return search_items(search_string, limit, new_access_token)

    if response.status_code != 200:
        raise RuntimeError(f"({response.status_code}, {response.text})")

    response_json = response.json()

    if 'warnings' in response_json:
        warnings = [warn.get('message', 'Unknown warning')
                    for warn in response_json.get('warnings', [])]
        log(f"eBay warnings: {warnings}")

    items = []
    if 'itemSummaries' in response_json:
        for item in response_json['itemSummaries']:
            items.append({
                'title': item.get('title'),
                'id': item.get('itemId'),
                'price': item.get('price', {}).get('value'),
                'currency': item.get('price', {}).get('currency'),
                'url': item.get('itemWebUrl')
            })
    return items


def test_token():
    token, oce_setting = retrieve_token()
    if not token:
        raise RuntimeError("Failed to retrieve token")

    parsed = parse_token(token)
    expected_fields = ['token_type', 'access_token',
                       'expires_in', 'refresh_token', 'refresh_expires_in']
    for field in expected_fields:
        if field not in parsed:
            log(f"Missing field: {field}")
            raise ValueError(f"Missing field in token: {field}")

    token2, oce_setting2 = retrieve_token()
    assert token == token2, "Cache verification failed - tokens don't match"

    if 'app_id' not in oce_setting or 'cert_id' not in oce_setting:
        raise ValueError(
            f"Missing app_id or cert_id in oce_setting: {oce_setting.keys()}")

    log('test_token.. pass')


def test_search():
    search_keyword = "laptop"
    items = search_items(search_keyword, 3)

    if not items or len(items) == 0:
        raise ValueError(f"No items found for keyword '{search_keyword}'")

    matched_items = 0
    for item in items:
        title = item.get('title', '').lower()
        if search_keyword.lower() in title:
            matched_items += 1
            log(f"✓ Match: {item['title']} ({item['price']} {item['currency']})")
        else:
            log(f"✗ No match: {item['title']} ({item['price']} {item['currency']})")

    if matched_items == 0:
        raise ValueError(f"None of {len(items)} matched '{search_keyword}'")

    log(f"test_search.. pass ({matched_items}/{len(items)} items matched keyword)")


def test_orders(after_refresh=False):
    token, oce_setting = retrieve_token()
    token_info = parse_token(token)
    access_token = token_info['access_token']

    now = datetime.now()
    dtill = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    dfrom = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    log(f"test_orders] start_date: {dfrom}, end_date: {dtill}")

    # cf. `function getOrderFromEbay` in “model-cron.php”
    xml_feed = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_feed += '<GetOrdersRequest xmlns="urn:ebay:apis:eBLBaseComponents">\n'
    xml_feed += '<ErrorLanguage>en_US</ErrorLanguage>\n'
    xml_feed += '<WarningLevel>High</WarningLevel>\n'
    xml_feed += f'<CreateTimeFrom>{dfrom}</CreateTimeFrom>\n'
    xml_feed += f'<CreateTimeTo>{dtill}</CreateTimeTo>\n'
    xml_feed += '<OrderRole>Seller</OrderRole>\n'
    xml_feed += '<OrderStatus>Completed</OrderStatus>\n'
    xml_feed += '</GetOrdersRequest>\n'

    headers = {
        'X-EBAY-API-COMPATIBILITY-LEVEL': '967',
        'X-EBAY-API-DEV-NAME': oce_setting['dev_id'],
        'X-EBAY-API-APP-NAME': oce_setting['app_id'],
        'X-EBAY-API-CERT-NAME': oce_setting['cert_id'],
        'X-EBAY-API-CALL-NAME': 'GetOrders',
        # select id_ebay_countries from oce_kb_ebay_sites where abbreviation = 'DE'
        # select profile_name, ebay_site, ebay_category_id from oce_kb_ebay_profiles
        'X-EBAY-API-SITEID': '77',  # DE is 77
        'X-EBAY-API-IAF-TOKEN': access_token,
        'Content-Type': 'text/xml'
    }

    response = requests.post(
        'https://api.ebay.com/ws/api.dll', headers=headers, data=xml_feed)
    assert response.status_code == 200, f"!200: {response.status_code}"
    ct = response.headers.get('Content-Type')
    assert ct == "text/xml;charset=UTF-8", f"!xml: {ct}"
    with open('test_orders.xml', 'w', encoding='utf-8') as f:
        f.write(response.text)  # For inspection

    root = ET.fromstring(response.text)
    ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
    ack = root.find('.//ebay:Ack', ns)
    err = ''
    if ack is not None and ack.text == 'Failure':
        log('GetOrders Failure')
        err += 'GetOrders Failure'
        for error in root.findall('.//ebay:Errors', ns):
            short_message = error.find('.//ebay:ShortMessage', ns)
            log(f"short_message: {short_message.text}")
            err += ' short_message: ' + short_message.text
            long_message = error.find('.//ebay:LongMessage', ns)
            log(f"long_message: {long_message.text}")
            err += ' long_message: ' + long_message.text
            error_code = error.find('.//ebay:ErrorCode', ns)
            log(f"error_code: {error_code.text}")
            err += ' error_code: ' + error_code.text
            if not after_refresh and error_code.text == '932':  # token expired
                refresh_token_using_refresh_token()
                test_orders(after_refresh=True)
                return
    if err:
        raise RuntimeError(err)

    for order in root.findall('.//ebay:Order', ns):
        order_id = order.find('ebay:OrderID', ns).text
        log(f"order_id: {order_id}")
        order_status = order.find('ebay:OrderStatus', ns).text
        log(f"order_status: {order_status}")
        amount_paid = order.find('ebay:AmountPaid', ns).text
        log(f"amount_paid: {amount_paid}")
        buyer_user_id = order.find('ebay:BuyerUserID', ns).text
        log(f"buyer_user_id: {buyer_user_id}")

        shipping_address = order.find('ebay:ShippingAddress', ns)
        shipping_name = shipping_address.find('ebay:Name', ns).text
        log(f"shipping_name: {shipping_name}")
        shipping_city = shipping_address.find('ebay:CityName', ns).text
        log(f"shipping_city: {shipping_city}")
        shipping_state = shipping_address.find('ebay:StateOrProvince', ns).text
        log(f"shipping_state: {shipping_state}")
        shipping_country = shipping_address.find('ebay:Country', ns).text
        log(f"shipping_country: {shipping_country}")

        items = []
        for transaction in order.findall('.//ebay:Transaction', ns):
            item = transaction.find('ebay:Item', ns)
            item_title = item.find('ebay:Title', ns).text
            item_id = item.find('ebay:ItemID', ns).text
            items.append({'item_id': item_id, 'title': item_title})
            log(f"item_id: {item_id}, title: {item_title}")


if __name__ == "__main__":
    if not 'M2B' in os.environ:
        log('!M2B')
        exit(0)

    test_token()
    test_orders()
    # test_search()
