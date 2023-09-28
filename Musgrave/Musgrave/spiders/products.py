import scrapy
import pandas as pd
from datetime import datetime
from ..Utils import auth_token
import json
import os

class ProductsSpider(scrapy.Spider):
    name = 'products'

    # handle_httpstatus_list = [x for x in range(400, 600)]

    # print("Enter Name for Output file:")
    p_date = datetime.now().strftime("%Y%m%d")
    filenm = f"Musgrave_products{p_date}"
    cmp = []
    count = 0
    def closed(self, reason):
        if not os.path.exists("Output"):
            os.mkdir("Output")
        df = pd.DataFrame(self.cmp)
        df.to_csv(f"Output/{self.filenm}.csv", encoding="UTF-8", index=False)

    def start_requests(self):
        url = 'https://www-api.musgravemarketplace.ie/INTERSHOP/rest/WFS/musgrave-MWPIRL-Site/-;loc=en_IE;cur=EUR/personalization'
        headers = {
                'authentication-token': auth_token,
            }
        yield scrapy.Request(url, headers=headers)

    def parse(self, response):
        data = json.loads(response.text)
        pg_id = data['pgid']
        
        url = f'https://www-api.musgravemarketplace.ie/INTERSHOP/rest/WFS/musgrave-MWPIRL-Site/-;loc=en_IE;cur=EUR/categories;spgid={pg_id}?imageView=NO-IMAGE&view=tree&limit=1&omitHasOnlineProducts=true'
        headers = {
                'accept': 'application/json'
            }
        yield scrapy.Request(url, headers=headers,  callback=self.parse_category, cb_kwargs={'pg_id':pg_id})
        

    def parse_category(self, response, pg_id):
        data = json.loads(response.text)
        headers = {
                    'authentication-token': auth_token,
                }

        for cat in data['elements'][0]['subCategories']:
            url = f'https://www-api.musgravemarketplace.ie/INTERSHOP/rest/WFS/musgrave-MWPIRL-Site/-;loc=en_IE;cur=EUR/categories;spgid={pg_id}/SmallMediumEnterprisesWebHierarchy/{cat["id"]}/products?attrs=sku,salePrice,listPrice,availability,manufacturer,image,minOrderQuantity,inStock,promotions,packingUnit,productMasterSKU,estimatedDeliveryDate,supplier,taxRate,size,pricePerKilo,listPricePerKilo,isPromotionalPrice,UCIV,RRP,POR&labelAttributeGroup=PRODUCT_LABEL_ATTRIBUTES&attributeGroup=PRODUCT_API_ATTRIBUTES&amount=500&offset=0&returnSortKeys=true&productFilter=fallback_searchquerydefinition&sortKey=Position'
            yield scrapy.Request(url, headers=headers, callback=self.parse_product, cb_kwargs={'category_id':cat['id'], 'category' : cat['name'],'pg_id':pg_id})

    def parse_product(self, response, category_id, category, pg_id):
        data = json.loads(response.text)
        for product in data['elements']:
            title = product['title']
            size = ''
            pro_code = ''
            listPrice = ''
            salePrice = ''
            ean_code = ''
            brand = ''
            vat = ''
            promo = ''
            stock = ''

            for attribute in product['attributes']:
                if attribute['name'] == 'size':
                    size = attribute['value']
                if attribute['name'] == 'sku':
                    pro_code = attribute['value']
                if attribute['name'] == 'listPrice':
                    listPrice = attribute['value']['value']
                if attribute['name'] == 'salePrice':
                    salePrice = attribute['value']['value']
                if attribute['name'] == 'manufacturer':
                    brand = attribute['value']
                if attribute['name'] == 'taxRate':
                    vat = str(attribute['value'] * 100) + '%'
                if attribute['name'] == 'isPromotionalPrice':
                    promo = 'Yes' if attribute['value'] else 'No'
                if attribute['name'] == 'inStock':
                    stock = 'In Stock' if attribute['value'] else 'Sold Out'
            
            for attribute in product['attributeGroup']['attributes']: 
                if attribute['name'] == 'EANCode':
                    ean_code = attribute['value']

            product = { 
                    "Category" : category,
                    "Product Code" : pro_code,
                    "EAN Code" : ean_code,
                    "Product Name" : title,
                    "Product Size" : size,
                    "List Price" : listPrice,
                    "Sale Price" : salePrice,
                    'VAT' : vat,
                    "Brand" : brand,
                    "On Promo" : promo,
                    "Stock": stock
                }
            self.cmp.append(product)
            self.logger.info(f"Scraped Product: {product['Product Name']} ({product['Product Code']})")

        headers = {
                    'authentication-token': auth_token,
                }

        # if skus:
        #     sku_str = '&skus='.join(skus)
        #     url = 'https://www-api.musgravemarketplace.ie/INTERSHOP/rest/WFS/musgrave-MWPIRL-Site/-;loc=en_IE;cur=EUR/inventory?skus='+ sku_str
        #     yield scrapy.Request(url, callback=self.parse_inventory, headers=headers, cb_kwargs={'products':products})

        if 'offset' in data and len(data['elements']) > 0:
            offset = data['offset'] + 500
            url = f'https://www-api.musgravemarketplace.ie/INTERSHOP/rest/WFS/musgrave-MWPIRL-Site/-;loc=en_IE;cur=EUR/categories;spgid={pg_id}/SmallMediumEnterprisesWebHierarchy/{category_id}/products?attrs=sku,salePrice,listPrice,availability,manufacturer,image,minOrderQuantity,inStock,promotions,packingUnit,productMasterSKU,estimatedDeliveryDate,supplier,taxRate,size,pricePerKilo,listPricePerKilo,isPromotionalPrice,UCIV,RRP,POR&labelAttributeGroup=PRODUCT_LABEL_ATTRIBUTES&attributeGroup=PRODUCT_API_ATTRIBUTES&amount=500&offset={offset}&returnSortKeys=true&productFilter=fallback_searchquerydefinition&sortKey=Position'
            yield scrapy.Request(url, headers=headers, callback=self.parse_product, cb_kwargs={'category_id':category_id, 'category' : category,'pg_id':pg_id})



    def parse_inventory(self, response, products):
        data = json.loads(response.text)

        for item in data['elements']:
            product = products[item['sku']]
            product['Stock'] = 'In Stock' if item['inStock'] else 'Sold Out'

            self.cmp.append(product)
            self.logger.info(f"Scraped Product: {product['Product Name']} ({product['Product Code']})")
