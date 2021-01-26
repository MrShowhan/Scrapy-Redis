# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from Tianyancha.items import TianyanchaItem
from Tianyancha.items import UpdateItem
from Tianyancha.Equity_distribution_model import GetData
from scrapy_redis.spiders import RedisCrawlSpider
import re
import time

import json
class TianyanchaSpider(RedisCrawlSpider):
    name = 'tianyancha'
    allowed_domains = ['tianyancha.com']
    # start_urls = ['https://www.tianyancha.com/search?key=%E6%B3%B0%E5%AF%8C']
    redis_key = 'tianyancha:start_urls'

    linkextractor_company =r'https://www.tianyancha.com/company/\d+'
    linkextractor_page =r'https://www.tianyancha.com/search/p[1-5]\d{0}\?key='  #非VIP只能查看前5页
    rules = (
        Rule(LinkExtractor(allow=linkextractor_company), callback='parse_item'),
        Rule(LinkExtractor(allow=linkextractor_page), follow=True)
    )

    def parse_item(self, response):
        item = TianyanchaItem()
        item['id'] =re.search(r'https://www.tianyancha.com/company/(\d+)',response.url).group(1)    #公司id
        item['company_name'] = response.xpath('//div[@class="header"]/*[@class="name"]/text()').extract_first()
        item['company_tag'] = response.xpath('//div[@class="tag-list"]/child::*/text()').extract()  #通过child直接定位简易标签
        item['company_detail'] = self.company_detail(response)
        item['logo'] = response.xpath('//div[@class="logo -w100"]/img/@data-src').extract_first()
        item['registration_information']=self.registration_information(response)
        url_background = 'https://capi.tianyancha.com/cloud-company-background/company/enterpriseMap?gid={}'.format(item['id'])
        yield scrapy.Request(url=url_background,callback=self.parse_background,meta={'item':item},priority=3)

    def parse_background(self, response):
        item = response.meta['item']
        item['background'] = self.company_background(response)
        holder_and_investorList =GetData(item['id']).get_json()
        item['equity_distribution_model'] = holder_and_investorList.get('data')
        url_risk = 'https://www.tianyancha.com/company/company_risk.xhtml?id={}'.format(item['id'])
        yield scrapy.Request(url_risk,callback=self.parse_risk,meta={'item':item},priority=8)

    def parse_risk(self, response):
        item = response.meta['item']
        item['risk'] = self.risk(response)
        yield item      #把公司基本信息先yield回pipelines保存
        url_lawsuit = 'https://www.tianyancha.com/pagination/lawsuit.xhtml?ps=30&pn=1&id={}'.format(item['id'])
        yield scrapy.Request(url_lawsuit, callback=self.parse_lawsuit, priority=5,meta={'item':item})

    def parse_lawsuit(self, response):
        item = response.meta['item']
        item1 = UpdateItem() #重新创建一个专门的item保存法律诉讼信息
        item1['id']=item['id']  #提取item的公司id至item1使用
        item1['lawsuit'] = self.lawsuit(response)
        yield item1     #因为涉及翻页,每一次翻页时都要把上一页的信息yield回去
        page = response.xpath('//ul[@class="pagination"]/li')
        if len(page) > 1:   #判断是否需要翻页，及构造最大页码
            page_mud = page[-2].xpath('.//text()').extract_first().replace('...', '')
            for i in range(2, int(page_mud) + 1):
                url = 'https://www.tianyancha.com/pagination/lawsuit.xhtml?ps=30&pn={}&id={}'.format(i, item['id'])
                yield scrapy.Request(url,callback=self.parse_lawsuit_page,priority=5,meta={'item':item})


    def parse_lawsuit_page(self,response):  #处理翻页后的数据，与parse_lawsuit函数一样。
        item = response.meta['item']
        item1 = UpdateItem()
        item1['id'] = item['id']
        item1['lawsuit'] = self.lawsuit(response)
        yield item1 #因为涉及翻页,每一次翻页时都要把上一页的信息yield回去

    def company_detail(self,response):
        '''
        处理公司基本信息模块，返回公司电话、邮箱、网址、地址、简介
        '''
        dict = {}
        item = response.xpath('//div[@class="detail "]//span[@class="label"]')
        for i in range(3):
            i = item[i]
            key = i.xpath('./text()').extract_first()[:-1]
            value = i.xpath('./following-sibling::*[1]//text()').extract()
            dict[key] = value
        address = response.xpath('//*[@id="company_base_info_address"]/text()').extract_first()
        if address == None:
            dict['地址'] = '暂无信息'
        else:
            dict['地址'] = address.strip()
        info = response.xpath('//*[@id="company_base_info_detail"]/text()').extract_first()
        if info == None:
            dict['简介'] = '暂无信息'
        else:
            dict['简介'] = info.strip()
        return dict

    def company_background(self,response):
        '''
        提取公司企业架构图内的信息：股东、高管、历史股东、对外投资、分支机构、历史法定代表人。目前已经实现前两个。
        '''
        result = json.loads(response.text)
        dict = {}
        holders = {}        #股东模块
        holder = result.get('data').get('holder')
        for i in range(len(holder)):
            d = {}
            if holder[i].get('tagList'):    #不是每一个都用
                tagList = holder[i].get('tagList')
                tag = []
                for j in tagList:
                    tag.append(j.get('name'))
                d['tagList'] = tag
            d['name'] = holder[i].get('name')
            d['percent'] = holder[i].get('percent')
            holders[str(i)] = d          #遍历每一个股东信息并做成字典，以序号为key
        dict['holders'] = holders   #以所有股东信息为vaule，存入字典中，key为holders

        staff = result.get('data').get('staff')
        staffs = {}     #高管模块
        for i in range(len(staff)):
            d = {}
            d['name'] = staff[i].get('name')
            d['typeJoin'] = staff[i].get('typeJoin')
            staffs[str(i)] = d           #遍历每一个高管信息并做成字典，以序号为key
        dict['staff'] = staffs      #以所有高管信息为vaule，存入字典中，key为holders
        return dict

    def registration_information(self,response):
        '''
        处理信息登记模块，返回一个包含登记信息的字典
        '''
        title = response.xpath('//div[@id="nav-main-baseInfo"]/span[@class="data-title"]/text()').extract_first()
        if title =='工商信息':
            data = response.xpath('//div[@id="_container_baseInfo"]//tr/following-sibling:: */td/span/text()|//div[@id="_container_baseInfo"]//tr/following-sibling:: */td/text()').extract()
            data.remove('注册资本')
            try:
                data.remove('查看更多')
                data.remove('查看更多')
            except:
                pass
            d=dict(zip(data[::2],data[1::2]))
            return d
        elif title =='登记信息':
            data = response.xpath('//div[@id="_container_baseInfo"]//tr/td//span/text()|//div[@id="_container_baseInfo"]//tr/td/text()').extract()
            d = dict(zip(data[::2], data[1::2]))
            return d

    def risk(self,response):
        '''
        简单处理风险模块，在没有vip的情况下使用，仅为简单的条数提醒，后续需继续完善
        '''
        key = response.xpath('//span[@class="risk"]/text()').extract()
        value = response.xpath('//span[@class="tag tag-risk-count -new"]/text()').extract()
        value = [i.replace('\xa0', ' ') for i in value]
        dict = {}
        for i in range(3):
            dict[key[i]] = value[i]
        return dict

    def lawsuit(self, response):
        '''
        处理法律诉讼模块
        '''
        first_list = ['裁判日期', '案件名称', '案号', '案由', '案件身份', '裁判结果', '审理法院', '发布日期']
        key = response.xpath('//table[@class="table"]/tbody/tr')
        d = {}
        for i in key:
            list1 = []
            li = i.xpath('./td')
            for l in li:
                a = l.xpath('.//text()').extract()
                if len(a) > 1:
                    b = ",".join(a).replace('\xa0\xa0,...\xa0,更多', '')
                    list1.append(b)
                else:
                    list1.append(a[0])
            d[list1[0]] = dict(zip(first_list, list1[1:]))
        return d
