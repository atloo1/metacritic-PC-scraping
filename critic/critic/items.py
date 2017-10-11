# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CriticItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    numCriticReviews = scrapy.Field()
    fractionCriticPositive = scrapy.Field()
    fractionCriticMixed = scrapy.Field()
    fractionCriticNegative = scrapy.Field()
    meanCriticReview = scrapy.Field()
    numUserReviews = scrapy.Field()
    fractionUserPositive = scrapy.Field()
    fractionUserMixed = scrapy.Field()
    fractionUserNegative = scrapy.Field()
    meanUserReview = scrapy.Field()
    esrb = scrapy.Field()
    title = scrapy.Field()
    developer = scrapy.Field()
    publisher = scrapy.Field()
    releaseDate = scrapy.Field()
    genres = scrapy.Field()
    url = scrapy.Field()
    scrapyStatus = scrapy.Field()
    pass
