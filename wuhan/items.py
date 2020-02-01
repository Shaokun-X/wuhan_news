# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ReportItem(scrapy.Item):
    title = scrapy.Field()
    datetime = scrapy.Field()
    content = scrapy.Field()
    source = scrapy.Field()
