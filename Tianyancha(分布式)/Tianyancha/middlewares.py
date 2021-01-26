# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from selenium import webdriver
from urllib.parse import unquote
import time
import random
import re
import redis

class TianyanchaSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class MiddlewareDownloaderMiddleware(object):

    def __init__(self):
        
    #构建UA 池
    user_agents_list = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60',
        'Opera/8.0 (Windows NT 5.1; U; en)',
        'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
        'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2 ',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0) ',
    ]


    def process_request(self, request, spider):
        request.headers['User-Agent']=random.choice(self.user_agents_list)
        request.headers['Cookie'] =  #将提取到的cookie放在这里，注意格式需要字符串，非字典

        if 'https://www.tianyancha.com/login?from'in request.url :
            get_cookies()
            '''部分代码已经省略'''
            return request

        elif 'https://antirobot.tianyancha.com/captcha'in request.url:
            antirobot()
            '''部分代码已经省略'''
            return request
        else:
            return None

    def get_cookies(self,url):
        driver = webdriver.Chrome("D:\chromedriver.exe")
        driver.implicitly_wait(5)
        driver.get(url)
        time.sleep(1)
        driver.find_element_by_xpath(r'//*[text()="密码登录"]').click()
        driver.find_element_by_xpath(r'//input[@id="mobile"]').send_keys('*******')
        driver.find_element_by_xpath(r'//input[@id="password"]').send_keys('*******')
        time.sleep(2)
        driver.find_element_by_xpath(r'//div[@class="btn -xl btn-primary -block"and text()="登录"]').click()
        time.sleep(10)  #自己手动输入验证码
        request = driver.current_url   #登录后会重定向目标网页，需要把这个网页重新返回队列中等待爬取
        cookies_list = driver.get_cookies()
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        cookie_str = str(cookies_dict).replace(': ', '=').replace("'", "").replace(',', ';')[1:-1]  #获取cookie
        driver.close()
        return request

    def antirobot(self,url):
        driver = webdriver.Chrome("D:\chromedriver.exe")
        driver.implicitly_wait(5)
        new_url = re.search(r'https://antirobot.tianyancha.com/captcha/verify\?return_url=(.*)', url).group(1)
        '''因为scrapy的异步问题，直接打开机器人检测的验证码页面，无论如何都会一直报错，所以需要自己构建网址'''
        url_encode = unquote(new_url, 'utf-8')
        driver.get(url_encode)
        time.sleep(1)
        driver.find_element_by_xpath(r'//*[text()="密码登录"]').click()
        driver.find_element_by_xpath(r'//input[@id="mobile"]').send_keys('******')
        driver.find_element_by_xpath(r'//input[@id="password"]').send_keys('******')
        time.sleep(2)
        driver.find_element_by_xpath(r'//div[@class="btn -xl btn-primary -block"and text()="登录"]').click()
        time.sleep(30)  #需要机器人识别，所以需要更多的时间操作，确保能成功登录
        request = driver.current_url
        cookies_list = driver.get_cookies()
        cookies_dict = {}
        for cookie in cookies_list:
            cookies_dict[cookie['name']] = cookie['value']
        cookie_str = str(cookies_dict).replace(': ', '=').replace("'", "").replace(',', ';')[1:-1]  #获取cookie
        driver.close()
        return request

