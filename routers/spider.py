import asyncio
import multiprocessing
import shutil
from datetime import datetime
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from sqlalchemy.util import await_only
from twisted.internet import reactor, defer
import os
import urllib.parse
import re
import scrapy
from bs4 import BeautifulSoup
from fastapi import APIRouter, Request, Body
from routers.kdb import get_user_path, change_source
from db import spider_db,file_db
from twisted.internet.threads import deferToThread
from db import spider_db,file_db
from kdbmanager import kdbm
from urllib.parse import urlparse
from apis.version1.route_login import get_resource

settings = get_project_settings()
settings.set('DEPTH_LIMIT', 2)

router = APIRouter()
spider_instance = None
# 解析相对URL为绝对URL

# Scrapy Spider
# Scrapy Spider
class MainContentSpider(scrapy.Spider):
    name = "main_content"
    start_urls = []  # 默认空列表，可以在外部传入
    total_count = 0
    links = []
    def __init__(self, urls=None, output_file=None,*args, **kwargs):

        if urls:
            self.start_urls = urls
        super().__init__(*args, **kwargs)
        self.base_urls = []
        self.output_file = output_file

        if self.start_urls:
            # 遍历所有的 start_urls 来解析并存储它们的域名
            for url in self.start_urls:
                # 解析 URL 并获取域名部分
                parsed_url = urllib.parse.urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                self.base_urls.append(base_url)
        else:
            print("Warning: start_urls is empty!")

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse, meta={'depth': 1})

    def parse(self, response):
        self.links.append(response.url)
        self.total_count +=1
        import trafilatura
        content = trafilatura.extract(response.text)
        current_depth = response.meta.get('depth', 1)
        # 将提取的内容写入文件
        file_path = self.output_file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"***************************************************************\n")
            f.write(f"url : {response.url}:\n")
            f.write(f"{content}\n")
            f.write(f"***************************************************************\n")

        # 提取所有链接并跟踪
        for relative_url in response.css('a::attr(href)').getall():
            # 直接使用 Scrapy 的 response.follow() 方法，它会自动处理相对 URL 和完整 URL
            full_url = response.urljoin(relative_url)
            # 获取链接的域名
            full_url_domain = urlparse(full_url).netloc
            base_url_domains = [urlparse(base_url).netloc for base_url in self.base_urls]
            print(f"Checking if '链接{full_url}的域名{full_url_domain}' is in {base_url_domains}: {full_url_domain in base_url_domains}")
            # 检查该域名是否在 self.base_urls 中
            if full_url_domain in base_url_domains and full_url not in self.links:
                yield response.follow(full_url, self.parse, headers=response.request.headers,
                                      meta={'depth': current_depth + 1})

#pcp_page_front.html
# 执行 Scrapy 爬虫的同步方法(创建爬虫deferred)
def create_scrapy_spider(url, output_file,depth_limit):
    settings = get_project_settings()
    settings.set('DEPTH_LIMIT', depth_limit)

    settings.set('ROBOTSTXT_OBEY', False)
    runner = CrawlerRunner(settings)
    deferred = runner.crawl(MainContentSpider, urls=[url], output_file=output_file)
    #deferred.addBoth(lambda _: reactor.stop())
    # 将 defer 对象返回给 Twisted 用来等待爬虫结束
    deferred.addCallback(lambda _: reactor.callFromThread(reactor.stop))  # 使用 callFromThread 来停止 reactor
    return deferred



# 异步版本的 get_T_url_local 函数
def get_T_url_local(kdb_id,user_id,urls,output_file,depth_limit,queue):
    #实际上是路径

    # 异步包裹的函数
    def wrapper(url):
        # 使用 deferToThread 来启动爬虫，确保不会阻塞 asyncio 的事件循环
        deferred = deferToThread(create_scrapy_spider, url, output_file,depth_limit)
        reactor.run()
        return deferred

    # 启动并等待多个任务
    d_list = [wrapper(url) for url in urls]
    d_all = defer.DeferredList(d_list)
    queue.put(d_all)

    return  d_all
def start_process(kdb_id, user_id, urls, output_file, depth_limit,queue):
    process = Process(target=get_T_url_local, args=(kdb_id, user_id, urls, output_file,depth_limit, queue))
    process.start()
    process.join()
#运行爬虫
async def run_spider(kdb_id, user_id, urls, output_file, depth_limit,queue):
    await asyncio.to_thread(start_process, kdb_id, user_id, urls, output_file,depth_limit, queue)
    # 获取进程返回的结果
    return queue.get()

async def copyfile(urls,upload_file, res_file,filename,kdb_id):
    shutil.copy(upload_file, res_file)
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    await spider_db.insert_spider_data(urls, formatted_time, filename,upload_file)
    await file_db.insert_file_info(kdb_id, True, formatted_time, upload_file)
from multiprocessing import Process,Queue
@router.post("/spider")
# 启动 Twisted 事件循环
async def start_spider(request:Request):
    try:
        import shutil
        body =  await request.json()  # 获取请求体
        kdb_id = body.get('kdb_id')  # 提取 kdb_date
        user_id = request.cookies.get("current_user")
        resource = get_resource(request, "create_kdb")
        depth_limit = body.get("depth_limit", 1)
        urls = body.get("urls")
        if not urls or (isinstance(urls, list) and len(urls) != 1) or (isinstance(urls, str) and not urls.strip()):
            return {"is_successful": False, "message":resource.get("spider_d_mes")}
        file_name = body.get("file_name")
        file_name += ".txt"
        #这里已经路径+文件名的拼接
        output_file = os.path.join(get_user_path(), user_id, kdb_id, "uploaded_files", file_name)
        output_res_file = os.path.join(get_user_path(), user_id, kdb_id, "res_files")
        queue = Queue()
        # 异步执行爬虫任务
        result = await run_spider(kdb_id, user_id, urls, output_file,depth_limit, queue)

        await copyfile(urls,output_file,output_res_file,file_name,kdb_id)
        change_source(user_id, kdb_id, 1, 1)
        print("重建知识库 来自爬虫")
        kdb = kdbm.create_or_get_rag(kdb_id=kdb_id)
        res_file_path = os.path.join(output_res_file, file_name)
        print("重建知识库 来自爬虫 文件的路径是：", res_file_path)
        await kdb.add_document(file_path=res_file_path)

        return {"is_successful": True,"message":resource.get("spider_suf")}

    except Exception as e:
        return {"is_successful": False, "message":resource.get("spider_fail")}

    

