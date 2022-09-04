import xml.etree.ElementTree as ET
import argparse, os, searchItem, getCredentials
from datetime import datetime, timezone

def processDatabase(file_res):
    credentials = getCredentials.fetchCredentials()
    known_items = {}
    clone = ET.parse(file_res)
    node_xml = """
    
    <Offer>
        <ID>{ID}</ID>
        <UpdateDate>{UpdateDate}</UpdateDate>
        <FoundDate>{FoundDate}</FoundDate>
        <MarketplaceIDEnum>{MarketplaceIDEnum}</MarketplaceIDEnum>
        <ProductTitle><![CDATA[{ProductTitle}]]></ProductTitle>
        <ProductBrand>{ProductBrand}</ProductBrand>
        <ProductGTIN>{ProductGTIN}</ProductGTIN>
        <ProductImage><![CDATA[{ProductImage}]]></ProductImage>
        <CategoryID>{CategoryID}</CategoryID>
        <CategoryIDPath><![CDATA[{CategoryIDPath}]]></CategoryIDPath>
        <CategoryPath><![CDATA[{CategoryPath}]]></CategoryPath>
        <Condition>{Condition}</Condition>
        <ConditionID>{ConditionID}</ConditionID>
        <Price>{Price}</Price>
        <ItemLocationCountry>{ItemLocationCountry}</ItemLocationCountry>
        <SellerUsername>{SellerUsername}</SellerUsername>
        <SellerSellerAccountType>{SellerSellerAccountType}</SellerSellerAccountType>
    </Offer>

"""

    file_name = os.path.abspath(file_res.name)
    file_xml = file = open(file_name, 'rt').read().lower()
    tree = ET.fromstring(file_xml)

    pos = 1
    products = tree.findall('.//product')
    for item in products:
      manufacturer = item.find('.//manufacturer').text
      model = item.find('.//model').text
      prod_type = item.find('.//type').text
      price = item.find('.//price').text

      product_list, errors = searchItem.getItemSummary(search_string="%s %s %s" % (manufacturer, model, prod_type),
      limit=10, offset=0, fieldgroups='PRODUCT', return_raw=True)

      if product_list:
        ebay_elm = clone.find('.//Product[%s]/Ebay' % pos)

        for product_item in product_list:
          data = {}
          if 'itemId' in product_item:
            data['ID'] = product_item['itemId']
          else:
            continue

          if 'price' in product_item and (float(product_item['price']['value'])/float(price)) >= 0.8:
            data['Price'] = product_item['price']['value']
          else:
            continue

          if product_item['itemId'] in known_items:
            details = known_items[product_item['itemId']]
          else:
            details = searchItem.getItem(product_item['itemId'], credentials)
            known_items[product_item['itemId']] = details

          if details == None:
            continue

          cat_id_path = ''
          for cat in product_item['categories']:
            cat_id_path += ',' + cat['categoryId']

          data['MarketplaceIDEnum'] = details['listingMarketplaceId'] if 'listingMarketplaceId' in details else ""
          data['ProductTitle'] = details['title'] if 'title' in details else ""
          data['ProductBrand'] = details['brand'] if 'brand' in details else ""
          data['ProductGTIN'] = details['gtin'] if 'gtin' in details else ""
          data['ProductImage'] = details['image']['imageUrl'] if 'image' in details else ""
          data['CategoryID'] = details['categoryId'] if 'categoryId' in details else ""
          data['CategoryPath'] = details['categoryPath'] if 'categoryPath' in details else ""
          data['Condition'] = details['condition'] if 'condition' in details else ""
          data['ConditionID'] = details['conditionId'] if 'conditionId' in details else ""

          data['ItemLocationCountry'] = details['itemLocation']['country'] if 'itemLocation' in details else ""
          data['SellerUsername'] = details['seller']['username'] if 'seller' in details else ""
          data['FoundDate'] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
          data['UpdateDate'] = product_item['itemCreationDate'] if 'itemCreationDate' in product_item else ""
          data['CategoryIDPath'] = cat_id_path
          data['SellerSellerAccountType'] = ''

          processed = node_xml.format_map(data)
          ebay_elm.append(ET.fromstring(processed))

      pos += 1

    new_file_name = os.path.splitext(file_name)[0] + '.output.xml'
    f = open(new_file_name, "w+")
    f.write('<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(clone.getroot(), encoding='unicode'))
    f.close()

parser = argparse.ArgumentParser()
parser.add_argument(
    '-f', '--file',
    default='./test.data.xml',
    help='The input database file. Note that the ouput database file will have the name output appended to it',
    type=argparse.FileType('r'),
)

if __name__ == '__main__':
    args = parser.parse_args()
    processDatabase(args.file)
