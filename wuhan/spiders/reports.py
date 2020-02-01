import scrapy
import pytz
import re
import logging
from datetime import datetime
from wuhan.items import ReportItem


RE_DATETIME = re.compile(r'\d+年\d+月\d+日 \d+:\d+')
RE_DATETIME_ALT = re.compile(r'\d+-\d+-\d+ \d+:\d+')


class CaixinSpider(scrapy.Spider):
    name = "caixin"

    headers = {
        "Host": "www.caixin.com",
        "Connection": "keep-alive",
        "DNT": 1,
        "Upgrade-Insecure-Requests": 1,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36 Edg/79.0.309.71",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    }

    def start_requests(self):
        base_url = "http://www.caixin.com/search/scroll/0.jsp?page="
        urls = [base_url + str(page) for page in range(1, 30)]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                dont_filter=True,
                headers=CaixinSpider.headers,
            )

    def parse_list(self, response):
        for report in response.xpath('//div[@class="news_content"]//dl'):
            if not report.xpath(".//a[2]/text()").get() in ['[视听频道]', '[音频频道]']:
                report_url = report.xpath(".//a[1]/@href").get()
                # print(report_url)
                yield response.follow(
                    url=report_url,
                    callback=self.parse_report,
                    dont_filter=True,
                    headers=CaixinSpider.headers,
                )

    def parse_report(self, response):
        if int(response.status) in [301, 302]:
            self.logger.info(f'redirect invalid {response.url}')
            return
        if int(response.status) in [404]:
            self.logger.info(f'404 {response.url}')
            return

        content = ''.join(response.xpath('//*[@id="Main_Content_Val"]/p[position()<last()-1]/text()').extract())
        content = content.replace('\u3000\u3000', '\n')

        time_elem = response.xpath('//li[@class="time"]').get() or response.xpath('//*[@id="artInfo"]').get()
        time_str = RE_DATETIME.findall(time_elem)[0]
        time = datetime.strptime(time_str, '%Y年%m月%d日 %H:%M')
        
        title = response.xpath("//h1/text()").get().strip()
        report = ReportItem(
            title=title,
            content=content,
            datetime=time,
            source='财新'
        )
        yield report


class BJNewsSpider(scrapy.Spider):
    name = "bjnews"

    headers = {
        "Host": "www.bjnews.com.cn",
        "Connection": "keep-alive",
        "Referer": "http://www.bjnews.com.cn/",
        "DNT": 1,
        "Upgrade-Insecure-Requests": 1,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36 Edg/79.0.309.71",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    }

    def start_requests(self):
        base_url = "http://www.bjnews.com.cn/realtime?page="
        urls = [base_url + str(page) for page in range(1, 101)]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                dont_filter=True,
                headers=BJNewsSpider.headers
            )

    def parse_list(self, response):
        for report_url in response.xpath('//ul[@id="news_ul"]//a/@href').extract():
            yield response.follow(
                url=report_url,
                callback=self.parse_report,
                dont_filter=True,
                headers=BJNewsSpider.headers
            )

    def parse_report(self, response):
        if int(response.status) in [301, 302]:
            self.logger.info(f'redirect invalid {response.url}')
            return
        if int(response.status) in [404]:
            self.logger.info(f'404 {response.url}')
            return

        content = '\n'.join(response.xpath('//p[position()<last()]/text()').extract())

        time_str = response.xpath('//div[@class="fl ntit_l"]/span[@class="date"]/text()').get()
        time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        
        title = response.xpath("//div[@class='title']/h1/text()").get()
        report = ReportItem(
            title=title,
            content=content,
            datetime=time,
            source='新京报'
        )
        yield report


class ThepaperSpider(scrapy.Spider):
    name = "thepaper"

    headers = {
        "Host": "www.thepaper.cn",
        "Connection": "keep-alive",
        "DNT": 1,
        "Upgrade-Insecure-Requests": 1,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36 Edg/79.0.309.71",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    def start_requests(self):
        # 思想市场板块
        base_url1 = "https://www.thepaper.cn/load_index.jsp?nodeids=25483&topCids=&pageidx="
        # 疫情板块
        base_url2 = "https://www.thepaper.cn/load_index.jsp?nodeids=90069,&channelID=90077&topCids=,5721392,5723044,5722959,5721929,5591325&pageidx="
        urls = [base_url1 + '1']
        # urls += [base_url2 + str(page) for page in range(1, 26)]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                dont_filter=True,
                headers=ThepaperSpider.headers
            )

    def parse_list(self, response):
        for report_url in response.xpath("//h2/a/@href").extract():
            yield response.follow(
                url=report_url,
                callback=self.parse_report,
                dont_filter=True,
                headers=ThepaperSpider.headers
            )

    def parse_report(self, response):
        if int(response.status) in [301, 302]:
            self.logger.info(f'redirect invalid {response.url}')
            return
        if int(response.status) in [404]:
            self.logger.info(f'404 {response.url}')
            return

        content = '\n'.join(
            response.xpath('''//div[@class="news_txt"]//
            descendant-or-self::*[not(self::div[@class="hide_word"]) and not(self::span)]/text()''').extract()
        )

        time_elem = response.xpath("//div[@class='news_about']").get()
        time_str = RE_DATETIME_ALT.findall(time_elem)[0]
        time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        
        title = response.xpath('//h1[@class="news_title"]/text()').get()
        report = ReportItem(
            title=title,
            content=content,
            datetime=time,
            source='澎湃'
        )
        yield report