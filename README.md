#  基于Scrapy-Redis的天眼查爬虫

 代码只保留了几个有代表性的模块进行测试爬取（公司基本信息模块、企业架构图、信息登记模块、风险模块、律诉讼模块），其中设计 text数据处理、json数据处理、翻页处理，最后数据保存值MongoDB。



## 编写难点及解决思路
①网站部分信息需要登陆后才能查看
②网页信息为动态加载同时许多模块都有翻页
③爬取一定数量网页后需要重新登录验证或者机器人识辨

因为个人原因，在登录方面直接使用selenium自动化测试框架帮忙模拟登录，在最后弹出验证码的时候手动打码，登录后提取cookie值保存下来，之后请求时携带此cookie值访问，直到cookie失效时，再重新模拟登录以同样的方式获取新cookie（有资源的人可以直接建立cookie池，本人只用一个账号爬取）。在子模块中涉及翻页的问题，可以建立多个item进行处理。为了保证信息能及时保存下来，会把部分模块单独写一个item，每个item数据提取到后及时yield回去管道进行处理。

##  项目运行
> 下载代码
- git clone git@github.com/MrShowhan/Scrapy-Redis.git
> 安装依赖
- pip install -r requirements.txt
> 配置修改
- setting.py 
指定redis数据库的连接参数  
REDIS_HOST = '127.0.0.1'  
REDIS_PORT = 6379
- pipelines.py
 配置数据库信息  
self.MONGO_URl = 'localhost'  
self.MONGO_DB = 'test' # 数据库名  
self.MONGO_TABLE = 'xxx' # 表名
> 启动项目
- 安装分布式启动，终端进入目录后输入 scrapy runspider tianyancha.py 或直接运行run.py 启动爬虫，再redis-cli lpush tianyancha:start_urls https://www.tianyancha.com/search?key=（查询关键字）


## 菜鸟心得

#### scrapy中cookie设置
一提到scrapy中cookie的设置，大部分人都知道三种设置方式：**setting**、**middlewares**、**spider**。他们对应着三种级别。然后如果手动设置cookie的话，需要在**setting**中设置COOKIES_ENABLED = False。为什么要这样做，或者这样做产生的影响是什么？如果我需要部分请求携带cookie，部分请求不携带（即cookie为空）需要怎么做，带着这些疑问我开始探索，一下是我的总结：

- 第一种：COOKIES_ENABLED = False
> 首次请求：
发起请求时会自动携带setting.py中设定的cookies
如果在爬虫主程序中把cookies封装在headers 里面，然后在scrapy.Request(headers = headers）提交请求时，headers中的cookies会覆盖掉setting.py中设定的cookies。
如果在爬虫主程序中把cookies值封装在cookies 里面，然后在scrapy.Request（cookies= cookies）提交请求时，主程序设置的cookies无效，请求依然携带setting.py中设定的cookies。
再次请求：
与首次请求相同，不存在自动获取网址response的setcookies

总结：优先级 (headers = headers）>setting.py   ，cookies= cookies无效，scrapy不会记录cookies

- 第二种：COOKIES_ENABLED = True 或注释掉
> 首次请求：
程序会自动屏蔽setting.py中设定的cookies，不携带cookies请求
如果在爬虫主程序中把cookies封装在headers 里面，然后在scrapy.Request(headers = headers）提交请求时，headers中的cookies无效，程序依然不携带cookies请求。
如果在爬虫主程序中把cookies值封装在cookies 里面，然后在scrapy.Request（cookies= cookies）提交请求时，程序携带cookies 中设定的cookies值进行请求。
再次请求：
程序会自动获取上一次网址返回的cookies ，并携带发送，
如果请求中携带scrapy.Request（cookies= cookies） ，程序会将设置的cookies值与上一次网址返回的cookies值进行拼接，一起携带发送。（如果某个key重复，这cookies= cookies里面的值优先，覆盖上一次网址返回的cookies值）
cookies 值是以追加的形式，每一次请求都是基于上一次请求的cookies值的基础上追加网址返回cookies值，新设定的cookies值。而不是重新设定

总结：cookies= cookies有效且优先级最高， (headers = headers）和setting.py 无效，scrapy会记录cookies


技巧提示：如果需要所有请求不带cookies进行请求，COOKIES_ENABLED = False，setting.py不设置cookies，特定网址需要携带cookies，可用scrapy.Request(headers = headers）

#### 子模块翻页及yield item 的问题
在网站中存在这许多子模块需要翻页获取数据，而scrapy框架的yield.Request是之上而下的，无法把数据返回上一层，如果把数据完整保存：
- 第一种：结合requests库使用，通过return返回数据给上层。
- 第二种：把一个公司的数据拆分成多个item进行保存，在遇到翻页子模块时新建一个item，分开处理。在最后pipelines里再合并。
本人选择第二种方式，因为有些公司数据量大，如果在某一个模块报错的话，第一种方式的数据回全波丢失，而第二种方式因为是不同的item，那些及时yield回去的item得以保存。
建议：在yield.Request时手动设置priority等级，尽量爬完一页数据里的全部公司信息，再去翻页（深度优先）。
