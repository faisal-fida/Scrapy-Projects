import scrapy
import json

USERNAME = "x55pal@hotmail.co.uk"
PASSWORD = "lifestyle"

class ProductsSpider(scrapy.Spider):
    name = 'products'
    allowed_domains = ['api2.parfetts.co.uk']
    start_urls = ['https://api2.parfetts.co.uk/parfetts/categories']

    def start_requests(self):
        url = 'https://api2.parfetts.co.uk/parfetts/auth/login'

        headers = {
                'content-type': 'application/json;charset=UTF-8',
        }

        cred = {
                "email": USERNAME,
                "password": PASSWORD
                }

        yield scrapy.Request(url, method='POST', headers=headers, body=json.dumps(cred))

    def parse(self, response):
        response = json.loads(response.text)
        token = response['data']['token']

        url = 'https://api2.parfetts.co.uk/parfetts/categories'
        yield scrapy.Request(url, callback=self.parse_categoroes, cb_kwargs={'token' : token})


    def parse_categoroes(self, response, token):
        headers = {
                    'authorization': 'Bearer ' + token,
                    'branchid': '2',
                    'customer': '2387',
                    'content-type': 'application/json;charset=UTF-8',
                }

        response = json.loads(response.text)['children']
        categories = [r['slug'] for r in response]

        for category in categories[:]:
            url = f'https://api2.parfetts.co.uk/parfetts/products/post-search?page=1'

            data = {
                    "slugs": [],
                    "categories": [category],
                    "brands": [],
                    "sortOrder": 1,
                    "search": None,
                    "my_categories": []
                }

            yield scrapy.Request(url, method='POST', headers=headers, body=json.dumps(data), callback=self.parse_products, cb_kwargs={'post_data':data, 'token': token})

    
    def parse_products(self, response, post_data, token):
        response = json.loads(response.text)

        # Initialize a counter attribute if it's not already set
        if not hasattr(self, 'counter'):
            self.counter = 0

        for prod in response['products']['data']:
            for pack in prod['packs']:
                product = {}

                product['Product ID'] = prod['id']
 
                try:
                    barcodes = prod['packs'][0]['barcodes'].split(', ')
                except KeyError:
                    barcodes = []

                for idx, barcode in enumerate(barcodes):
                    product[f'Barcode {idx}'] = str(barcode).replace("FREE TEX","")

                product['Category'] = prod['categories'][0]['name']
                
                product['Sub Category'] = ""
                if len(prod['categories']) > 1:
                    product['Sub Category'] = prod['categories'][1]['name']
                product['Product'] = prod['name']

                product['Price'] = '£ ' + str(pack['price'])
                product['Base Price'] = ""
                product['Promotion'] = ""
                product['Offer ends'] = ""
                if pack['hasPromotedPrice']:
                    product['Base Price'] = '£ ' + str(pack['standardPrice'])
                    product['Promotion'] = 'SAVE ' + str(round(pack['standardPrice'] - pack['price'], 1))
                    product['Offer ends'] = pack['promoEndDate']['date'].split()[0].replace('-','/')
                    
                product['RRP'] = '£ ' + str(pack['rrp'])
                product['POR'] = pack['por']
                product['VAT'] = prod['vatRate']
                product['Pack Size'] = f"{pack['quantity']} x {pack['uos']}"
            
                yield product
                #self.logger.error(f"Scrapped: {product['Product']}")
                # Increment the counter
                self.counter += 1
                if self.counter % 1000 == 0:
                    self.logger.info(f"Scrapped: {self.counter}")


        next = response['products']['next_page_url']
        if next:
            headers = {
                        'authorization': 'Bearer ' + token,
                        'branchid': '2',
                        'customer': '2387',
                        'content-type': 'application/json;charset=UTF-8',
                    }

            yield scrapy.Request(next, method='POST', headers=headers, body=json.dumps(post_data), callback=self.parse_products, cb_kwargs={'post_data':post_data, 'token':token})

