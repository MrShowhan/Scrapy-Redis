from scrapy.cmdline import execute

# scrapy runspider tianyancha.py
# redis-cli lpush tianyancha:start_urls https://www.tianyancha.com/search?key=******
execute(['scrapy','runspider','tianyancha.py'])