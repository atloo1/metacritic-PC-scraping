# -*- coding: utf-8 -*-
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from string import ascii_lowercase as alphabet
import re, calendar, datetime
from bs4 import BeautifulSoup
from critic.items import CriticItem

class MetacriticSpider(CrawlSpider):
    name = 'metacritic'
    allowed_domains = ['metacritic.com']
    monthAbbrs = {name: num for num, name in enumerate(calendar.month_abbr) if num}

    start_urls = [r'http://www.metacritic.com/browse/games/title/pc/' + i for i in alphabet] + \
                 [r'http://www.metacritic.com/browse/games/title/pc']  # a-z + '#' games

    rules = (
            Rule(LinkExtractor(
                # any non 0 page of # games
                allow=[r'http://www.metacritic.com/browse/games/title/pc\?page=[1-9]{1,3}',
                       # any non 0 page of a-z games
                r'http://www.metacritic.com/browse/games/title/pc/[a-z]\?page=[1-9]{1,3}']
            )
                ),

            Rule(LinkExtractor(
                deny=[r'http://www.metacritic.com/game/pc/\S+/',
                # anything deeper than /pc/gamePage
                r'http://www.metacritic.com/game/pc/[a-z0-9\-\!]+[\?\=]'],
                # '=' & '?' in /pc/gamePage appended after gamePage
                allow=[r'http://www.metacritic.com/game/pc/[^\/]+']
            ),
                # '/' not in /pc/here ; likely a game page
                callback='parse_item',follow=True
                )
            ,)

    def parse_item(self,response):
        minUserReviews = 4  #no aggregate user score until this criteria met
        output = CriticItem()
        criticReviewCounts = response.css('.critic_reviews_module .count').extract()
        criticReviewCount = int(BeautifulSoup(response.css('.highlight_metascore .count a').extract_first(),'html.parser').span.contents[-1])
        output['numCriticReviews'] = criticReviewCount
        if criticReviewCount > 0:
            for span in ['.positive ','.mixed ','.negative ']:  #3 possible CSS selectors containing critic metascore
                try: meanCriticReview = str(BeautifulSoup(response.css(span+'span').extract_first(), 'html.parser').span)
                except TypeError: continue
                output['meanCriticReview'] = int(re.search(r'[0-9]+',meanCriticReview).group(0))
            # get fractionCritic_
            for field, value in zip(['fractionCriticPositive','fractionCriticMixed','fractionCriticNegative'],criticReviewCounts):
                output[field] = int(re.search(r'\d+', str(BeautifulSoup(value, 'html.parser'))).group(0))/criticReviewCount

        try:
            userReviewCounts = response.css('.user_reviews_module .count').extract()    #negative, mixed, positive
            userReviewCount = 0
            for i in range(len(userReviewCounts)): userReviewCount += int(re.search(r'\d+', str(BeautifulSoup(userReviewCounts[i], 'html.parser'))).group(0))
            numUserReviews = str(BeautifulSoup(response.css('.feature_userscore p').extract_first(),'html.parser').p.contents[1].contents[-1])
            if re.search('Be the first to review!',numUserReviews) or userReviewCount == 0: #no user aggregate, fractions
                output['numUserReviews'] = 0
            else:   #get fractionUser_
                for field, value in zip(['fractionUserPositive', 'fractionUserMixed', 'fractionUserNegative'],userReviewCounts):
                    output[field] = int(re.search(r'\d+', str(BeautifulSoup(value, 'html.parser'))).group(0))/userReviewCount
                if re.search(r'Awaiting (\d) more rating', numUserReviews):    #no aggregate, has fractions
                    output['numUserReviews'] = minUserReviews - int(re.search(r'Awaiting (\d) more [rR]ating', numUserReviews).group(1))    #'rating' or 'Ratings'
                    output['meanUserReview'] = None
                else:   #has aggregate, fractions
                    output['numUserReviews'] = int(re.search(r'(\d+) [rR]ating', numUserReviews).group(1))
                    meanUserReview = str(BeautifulSoup(response.css('.large').extract()[-2], 'html.parser'))
                    output['meanUserReview'] = float(re.search(r'>(.+)<', meanUserReview).group(1))*10
        except TypeError:   #game not released, not taking user reviews & no fractionUser_
            output['numUserReviews'] = 0
        try:
            output['esrb'] = BeautifulSoup(response.css('.product_rating .data').extract_first(),'html.parser').span.contents[0]
        except TypeError: pass  #no rating provided so skip it
        title = BeautifulSoup(response.css('.product_title .hover_none span').extract_first(),'html.parser').span.prettify().replace('\n','')
        output['title'] = re.search(r'<span itemprop=\"name\"> ([^\\]+)<',title).group(1).replace('&amp;','&')  # '&' gets parsed as '&amp;'
        devAndPub = 0   #number of entries in the developer and publisher fields
        try:
            developer = BeautifulSoup(response.css('.developer .data').extract_first(), 'html.parser').prettify().replace('\n','')
            output['developer'] = re.search(r'<span class=\"data\"> ([^\\]+)<',developer).group(1).replace('&amp;','&')  # '&' gets parsed as '&amp;'
            devAndPub += 1
        except TypeError: pass  #developer not provided so skip it
        try:
            publisher = BeautifulSoup(response.css('.publisher span').extract()[-1],'html.parser').prettify().replace('\n','')
            output['publisher'] = re.search(r'<span itemprop=\"name\"> ([^\\]+)<', publisher).group(1).replace('&amp;','&')  # '&' gets parsed as '&amp;'
            devAndPub += 1
        except IndexError: pass  #publisher not provided so skip it
        if devAndPub == 1:  # if only dev or pub is populated make them the same
                try: output['developer'] = output['publisher']
                except KeyError: output['publisher'] = output['developer']
        releaseDate = BeautifulSoup(response.css('.release_data .data').extract_first(),'html.parser').prettify().replace('\n','')
        if re.search(r'datePublished\"> (\w+)(\s+\d+),(\s+\d+)',releaseDate):   #has month, day, year
            releaseDate = re.search(r'datePublished\"> (\w+)(\s+\d+),(\s+\d+)', releaseDate)
            month = MetacriticSpider.monthAbbrs[releaseDate.group(1)]
            day = int(releaseDate.group(2).strip())
            year = int(releaseDate.group(3).strip())
            output['releaseDate'] = str(datetime.datetime(year, month, day))
        elif re.search(r'datePublished\"> TBA (\d+)<',releaseDate): #has a TBA year release
            output['releaseDate'] = int(re.search(r'\"datePublished\"> TBA (\d+)<',releaseDate).group(1))
        genreList = response.css('.product_genre .data').extract()
        genres = [re.search('\\n(.*)\\n',BeautifulSoup(genre, 'html.parser').prettify()).group(1).lstrip() for genre in genreList]
        if len(genres) > 0: output['genres'] = ', '.join(set(genres))   #remove duplicate genre entries

        output['url'] = response.url
        output['scrapyStatus'] = response.status
        yield output