import xml.etree.ElementTree as ET
import argparse, copy, os, searchItem


def processDatabase(file_res):
    clone = ET.parse(file_res)
    node_xml = """<Offer>
        <ID>{ID}</ID>
        <MarketplaceIdEnum>{MarketplaceIdEnum}</MarketplaceIdEnum>
        <ProductTitle>{ProductTitle}</ProductTitle>
        <ProductBrand>{ProductBrand}</ProductBrand>
        <ProductGtins>{ProductGtins}</ProductGtins>
        <GroductImage>{GroductImage}</GroductImage>
        <CategoryID>{CategoryID}</CategoryID>
        <CategoryIDPath>{CategoryIDPath}</CategoryIDPath>
        <CategoryPath>{CategoryPath}</CategoryPath>
        <Condition>{Condition}</Condition>
        <ConditionID>{ConditionID}</ConditionID>
        <Price>{Price}</Price>
      </Offer>"""

    file_xml = file = open(os.path.abspath(file_res.name), 'rt').read().lower()
    tree = ET.fromstring(file_xml)

    pos = 1
    products = tree.findall('.//product')
    for item in products:
      prod_id = item.find('.//id').text
      manufacturer = item.find('.//manufacturer').text
      model = item.find('.//model').text
      prod_type = item.find('.//type').text
      price = item.find('.//price').text
      category_id = item.find('.//categoryid').text
      category_name = item.find('.//categoryname').text

      items, errors = searchItem.getItemDetails("%s %s %s" % (manufacturer, model, prod_type), 10, 0)

      if items:
        product = clone.find('.//Product[%s]/Ebay' % pos)
        print(product)

        for item in items:
          print(item)
          # processed = node_xml % {
          #     'ID': ,
          #     'MarketplaceIdEnum': ,
          #     'ProductTitle': ,
          #     'ProductBrand': ,
          #     'ProductGtins': ,
          #     'GroductImage': ,
          #     'CategoryID': ,
          #     'CategoryIDPath': ,
          #     'CategoryPath': ,
          #     'Condition': ,
          #     'ConditionID': ,
          #     'Price': 
          #   }

          pass
      
      pos += 1

 
      


parser = argparse.ArgumentParser()
parser.add_argument(
    '-f', '--file',
    default='../sample/test.data.xml',
    help='The input database file. Note that the ouput database file will have the name output appended to it',
    type=argparse.FileType('r'),
)

if __name__ == '__main__':
    args = parser.parse_args()
    processDatabase(args.file) 
