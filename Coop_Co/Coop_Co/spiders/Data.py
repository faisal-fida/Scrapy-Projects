import scrapy
from ..Utils import *
import pandas as pd
import os


class DataSpider(scrapy.Spider):
    name = 'Data'

    print("Enter Name for Output file:")
    filenm = input()
    cmp = []
    count = 0
    def closed(self, reason):
        if not os.path.exists("Output"):
            os.mkdir("Output")
        df = pd.DataFrame(self.cmp)
        df.to_excel(f"Output/{self.filenm}.xlsx", index=False)
    
    def start_requests(self):
        yield scrapy.Request(
            url=URL,
            headers=headers,
            meta={"proxy": prxy},
            callback=self.parse
        )

    def parse(self, response):
        for item in response.xpath("//section[contains(@id, 'member-price')] | //section[contains(@id, 'everyday-essentials')]"):
            sec_title = item.xpath(".//h3[contains(@class, 'section-title')]/text()").get()
            if URL == "https://www.coop.co.uk/products/deals/everyday-essentials":
                sec_title = "Everyday Essentials"
            if not sec_title:
                continue
            for itm in item.xpath(".//article"):
                title = itm.xpath(".//h3[contains(@class, 'card__title')]/text()").get().strip()
                price = " ".join(" ".join(itm.xpath(".//p[contains(@class, 'card__price')]//text()").getall()).split())
                fnl = {
                    "Section": sec_title,
                    "Title": title,
                    "Price": price
                }
                for i, ittm in enumerate(itm.xpath(".//ul[contains(@class, 'deals__list')]/li")):
                    deal_title = ittm.xpath(".//strong[contains(@class, 'deals__item__title')]/text()").get()
                    deal_date = ittm.xpath(".//span[contains(@class, 'item__date')]/text()").get().replace("until", "").strip()
                    fnl[f"Promotion#{i+1} Title"] = deal_title
                    fnl[f"Promotion#{i+1} Until"] = deal_date
                self.cmp.append(fnl)
                self.count += 1
                self.logger.info(f"Scraped ---------------> {self.count}")
