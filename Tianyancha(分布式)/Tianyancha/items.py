# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TianyanchaItem(scrapy.Item):
    company_name = scrapy.Field()
    company_tag = scrapy.Field()
    company_detail = scrapy.Field()
    logo = scrapy.Field()
    background = scrapy.Field()
    id = scrapy.Field()
    equity_distribution_model = scrapy.Field()
    registration_information = scrapy.Field()
    risk = scrapy.Field()
    _id = scrapy.Field()

class UpdateItem(scrapy.Item):
    id = scrapy.Field()
    lawsuit = scrapy.Field()