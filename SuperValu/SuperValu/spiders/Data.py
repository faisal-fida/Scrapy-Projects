import scrapy
from ..Utils import *
from bs4 import BeautifulSoup as bs
from datetime import datetime
import pandas as pd
import json
import os


class DataSpider(scrapy.Spider):
    name = 'Data'
    filenm = "Shop_SuperValu_"+datetime.now().strftime("%d-%m-%Y_%I-%M-%S")
    cmp = {}
    chk_dup = []
    count = 0
    def closed(self, reason):
        if not os.path.exists("Output"):
            os.mkdir("Output")
        cmp = []
        for _, item in self.cmp.items():
            for _, itm in item.items():
                for ittm in itm:
                    cmp.append(ittm)
        df = pd.DataFrame(cmp)
        df.to_excel(f"Output/{self.filenm}.xlsx", index=False)
    
    def start_requests(self):
        yield scrapy.Request(
            url=URL,
            headers=headers,
            callback=self.parse
        )

    def parse(self, response):
        soup = bs(response.body, "xml")
        for item in soup.findAll("url"):
            link = item.find("loc").text
            if "/product/" not in link:
                continue
            prod_id = link.split("-")[-1].strip()
            if prod_id not in self.chk_dup:
                self.chk_dup.append(prod_id)
                yield scrapy.Request(
                    url=API_URL.format(prod_id),
                    headers=headers,
                    dont_filter=True,
                    callback=self.parse_detail
                )

    def parse_detail(self, response):
        json_resp = json.loads(response.body)
        with open("Test.json", "w") as f:
            json.dump(json_resp, f)
        cate, sub_cate = "", ""
        if json_resp.get("categories"):
            if len(json_resp.get("categories")) > 1:
                cate = json_resp.get("categories")[0].get("category")
                sub_cate = json_resp.get("categories")[1].get("category")
            else:
                cate = json_resp.get("categories")[-1].get("category")
        if cate not in list(self.cmp.keys()):
            self.cmp[cate] = {}
        if sub_cate not in list(self.cmp.get(cate).keys()):
            self.cmp.get(cate)[sub_cate] = []
        sku_bar_code = json_resp.get("sku")
        name = json_resp.get("name")
        pack_size = name.split("(")[-1].split(")")[0].strip() if "(" in name else ""
        unit_price = json_resp.get("unitPrice")
        price = json_resp.get("price")
        fnl = {
            "Category": cate,
            "Sub Category": sub_cate,
            "Barcode": sku_bar_code,
            "Product Code": sku_bar_code,
            "Product Name": name,
            "Pack Size": pack_size,
            "Price Per Unit": unit_price,
            "Price": price,
            "Promotion": "NA",
            "On Promo": "No",
            "Promo Validity": "NA",
            "Promo Detail": "NA"
        }
        if json_resp.get("promotions"):
            for item in json_resp.get("promotions")[:1]:
                promo = item.get("description")
                promo_start = datetime.strptime(item.get(
                    "startDate"), "%d/%m/%Y").strftime("%d %b, %Y") if item.get("startDate") else ""
                promo_end = datetime.strptime(item.get(
                    "endDate"), "%d/%m/%Y").strftime("%d %b, %Y") if item.get("endDate") else ""
                fnl["Promotion"] = promo
                fnl["On Promo"] = "Yes"
                fnl["Promo Validity"] = f"{promo_start} - {promo_end}"
        self.cmp.get(cate).get(sub_cate).append(fnl)
        self.count += 1
        self.logger.info(f"Scraped ------------------> {self.count}")