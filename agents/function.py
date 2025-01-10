import asyncio
import multiprocessing
import uuid
import aiohttp
import requests
from six import text_type

from .setting import subscriptionKey, customConfigId,base_url,api_key
import json
from .init import cities
from typing import Dict, Any, Annotated, List, Type, Callable, Awaitable, Optional

# uvicorn web:app --port 9910 --ssl-keyfile avatar.haifeng.ai/privkey1.pem --ssl-certfile avatar.haifeng.ai/fullchain1.pem --host 0.0.0.0
from openai import OpenAI
from multiprocessing import Process, Queue
import scrapy
from bs4 import BeautifulSoup
from scrapy import crawler

from twisted.internet import reactor


#函数库###################################################################
# with open('apify_api_key.txt', 'r') as file:
#     apify_api_key = file.read().strip()  # 读取并去除文件内容的前后空白字符
# # 设置环境变量
# os.environ['APIFY_API_KEY'] = apify_api_key

from .init import config_list_path

def load_config(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)


async def fetch_completion(session, url, api_key, model, messages):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    async with session.post(url, headers=headers, json=data) as response:
        if response.status != 200:
            raise Exception(f"Error: {response.status} {await response.text()}")
        return await response.json()


async def sum_model_api(text: str, query: str) -> str:
    # 从 model.json 文件加载配置
    config = load_config(config_list_path)  # 假设这个函数是你已经实现的
    api_key = config[0]['api_key']
    model = config[0]['model']
    base_url = config[0]['base_url']

    # 构建消息
    messages = [
        {"role": "system", "content": "given the context information and not prior knowledge answer the query "},
        {"role": "user", "content": text},
        {"role": "user", "content": f'总结文本主体内容，主体在{query}里包含'}
    ]

    async with aiohttp.ClientSession() as session:
        response_json = await fetch_completion(session, f"{base_url}/chat/completions", api_key, model, messages)

    # 返回模型的回答
    return response_json['choices'][0]['message']['content']

# def sum_model_api(text: str,query:str) -> str:
#     # 从 model.json 文件加载配置
#
#     config = load_config(config_list_path)
#     api_key = config[0]['api_key']
#     client = OpenAI(api_key=api_key, base_url=config[0]['base_url'])
#
#     # 构建消息
#     messages = [
#         {"role": "system", "content": "given the context information and not prior knowledge answer the query "},
#         {"role": "user", "content": text},
#         {"role": "user", "content":f'总结文本主体内容，主体在{query}里包含' },
#     ]
#
#     # 调用 API
#     response =client.chat.completions.create(
#         model=config[0]['model'],
#         messages=messages,
#         stream=False
#     )
#
#     # 返回模型的回答
#     return response.choices[0].message.content

g_callback = None


def get_weather(city_name: str)-> Dict[str, Any]:
    # 获取对应的拼音
    location = cities.get(city_name)
    if not location:
        raise ValueError(f"City '{city_name}' not found in the dictionary.")
    # 构造 URl
    url = f'{base_url}?key={api_key}&location={location}&language=zh-Hans&unit=c&start=-1&days=5'
    # 发送网络请求
    response = requests.get(url)
    if response.status_code == 200:
        # 解析和返回结果
        return response.json()
    else:
        # 处理请求失败的情况
        response.raise_for_status()

def install_callback(callback):
    global g_callback
    g_callback=callback
    return g_callback
from pydantic import BaseModel

# def send_prompt(prompt: str, websocket) -> None:
#     """发送提示到 WebSocket 客户端."""
#     print("正在发送提示")
#     print(json.dumps({"prompt": prompt}))
#     websocket.send(json.dumps({"prompt": prompt}))



async def getinput(prompt: str) -> str:
    global g_callback
    if g_callback:
        response = await g_callback(prompt)
        return response
    return ""

def generate_session_id():
    return str(uuid.uuid4())


#本地客户端的输入代码
def getuseinput(prompt: str) -> str:
    # 示例实现
    user_input = input(prompt)  # 使用提示词作为用户输入的提示
    return user_input

# 函数映射字典
class MySpider(scrapy.Spider):
    name = "my_spider"

    def __init__(self, urls=None, result_queue=None, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.start_urls = urls or []
        self.result_queue = result_queue  # Store the result queue
        print("初始化完成")
        self.a=0
    def parse(self, response):
        content_selectors = [
            'body',
            'article',
            'main',
            'div.content',
            'div.post',
            'p',
        ]

        print("url",response)
        soup = BeautifulSoup(response.text, 'html.parser')
        print("get title")
        title = soup.title.get_text(strip=True) if soup.title else ''
        content = []
        print("getting content")
        for selector in content_selectors:
            #print("解析网站结构中",selector)
            elements = soup.select(selector)
            for element in elements:

                text = element.get_text(strip=True)
                if text:
                    content.append(text)


        #print("解析晚成")
        #print("解析结果是：", content)
        total_length = sum(len(text) for text in content)
        #print("解析结果的长度:", total_length)
        self.a=self.a+total_length
        #print("总长度",self.a)
               # Store the result in the queue
        result = {
            'url': response.url,
            'title': title,
            'content': ' '.join(content)
        }
        self.result_queue.put(result)  # Put the result into the queue



send_links_callback =None
def set_callback(callback):
    print("callback成功安装")
    global send_links_callback
    send_links_callback = callback

# async def scrape_with_scrapy(urls):
#     q = Queue()  # Create a queue for results
#     all_results = []
#     def f(q, urls):
#         try:
#             runner = crawler.CrawlerRunner()
#             deferred = runner.crawl(MySpider, urls=urls, result_queue=q)
#             deferred.addBoth(lambda _: reactor.stop())
#             reactor.run()
#         except Exception as e:
#             q.put(e)  # Put exception into the queue if occurs
#
#     p = Process(target=f, args=(q, urls))
#     p.start()
#     p.join()
#     while not q.empty():  # Collect results from the queue
#         result = q.get()
#         if isinstance(result, Exception):
#             raise result  # Raise any exceptions encountered
#         all_results.append(result)
#     print("爬取的结果是:",all_results)
#     return all_results # Return the list of results
async def scrape_with_scrapy(urls):
    q = multiprocessing.Queue()  # Create a queue for results (use multiprocessing.Queue for process-safe)
    all_results = []
    es_q = multiprocessing.Queue()

    def f(es_q, urls):
        try:
            runner = crawler.CrawlerRunner()
            deferred = runner.crawl(MySpider, urls=urls, result_queue=q)
            deferred.addBoth(lambda _: reactor.stop())  # Stop the reactor once crawling is done
            reactor.run()  # Start the Twisted reactor event loop
            es_q.put(None)
        except Exception as e:
            es_q.put(e)  # Put exception into the queue if occurs

    p = multiprocessing.Process(target=f, args=(es_q, urls))
    p.start()
    #p.join()
    ex = es_q.get()

    if ex is not None:
        raise ex

    # Collect results from the queue after the process ends
    while not q.empty():
        result = q.get()
        all_results.append(result)
    # print("爬取的结果是:", all_results)
    # total_content_length = sum(len(result['content']) for result in all_results)
    # print("爬取的内容总长度:", total_content_length)
    return all_results  # Return the list of results

# 在包含 bingsearch_answer 的文件中，定义一个全局字典
first_call_flags = {}

async def bingsearch_answer(
    query: str,  # query 是一个字符串类型
    session_id: Optional[str] = None,  # session_id 是一个可选的字符串
      # 回调函数参数，类型为可选的函数
) -> str:
    print(session_id)
    searchTerm = f"{query}"
    url = f'https://api.bing.microsoft.com/v7.0/custom/search?q={searchTerm}&customconfig={customConfigId}'
    headers = {'Ocp-Apim-Subscription-Key': subscriptionKey}


    global first_call_flags
    # 检查 session_id 是否在 first_call_flags 中
    if session_id not in first_call_flags:
        first_call_flags[session_id] = True  # 初始化为 True
    if first_call_flags[session_id]:
        await send_links_callback(json.dumps({"statuses": "searching sites", "text": "searching sites"}), text_type='statuses')
        first_call_flags[session_id] = False  # 发送后将其置为 False


    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                res = []

                #scraped_contents=[]
                successful_links_info = []
                contents=''
                if 'webPages' in data:
                    for page in data['webPages']['value']:
                        link_info = {
                            'url': page['url'],
                            "name": page['name'],
                            'siteName': page.get('siteName')
                        }
                        res.append(link_info)
                    #print("抓取的网站:", res)
                    links = [item['url'] for item in res]
                    links=links[:5]
                    #print("links：",links)
                    scraped_content = await scrape_with_scrapy(links)
                    # scraped_contents.append(scraped_content)
                    # print("scraped_contents",scraped_contents)
                    for item ,original_info in zip(scraped_content, res):
                        if item:  # 确保爬取成功
                            contents += item.get('content', '')
                            #print("hahahahaah",original_info)
                            # 将 link_info 添加到 successful_links 列表
                            successful_links_info.append(original_info)
                #await send_links_callback(successful_links)
                #print("scscscscsc",successful_links_info)
                #successful_links_str = "\n".join(successful_links)
                #仿真###########
                successful_links_info = [
                    {
                        "url": "https://example.com/article1",
                        "name": "Article 1",
                        "siteName": "Example Site 1"
                    },
                    {
                        "url": "https://example.com/article2",
                        "name": "Article 2",
                        "siteName": "Example Site 2"
                    },
                    {
                        "url": "https://example.com/article3",
                        "name": "Article 3",
                        "siteName": "Example Site 3"
                    }
                ]
                ##########3
                successful_links_json = json.dumps({"datatype": "link", "data": successful_links_info},
                                                   ensure_ascii=False)
                #print("sujson", successful_links_json)
                print("正在发送链接")
                await send_links_callback(text=successful_links_json,text_type='json')
                print("发送完毕")
                num_found = len(successful_links_info)
                reference_message = f"找到了{num_found}篇资料作为参考，分别是：\n"
                # 在此处修改，使用 successful_links_info 中的数据
                reference_message += "\n".join(f"({item['siteName']}){item['name']}：{item['url']}" for item in successful_links_info)
                print("爬取的总信息是：",contents)
                answer=await sum_model_api(text=contents,query=query)

                    #将结果写入文件
                    # with open('scraped_contents.txt', 'a', encoding='utf-8') as f:
                    #     for item in scraped_contents:
                    #         f.write(f"URL: {item['url']}\n")
                    #         f.write(f"Content: {item['content']}\n")
                    #         f.write('\n')  # 添加一个空行以分隔不同条目
                return f"{reference_message}\n\n{answer}"
            elif response.status == 401:
                await asyncio.sleep(5)
                successful_links_info = [
                    {
                        "url": "https://example.com/article1",
                        "name": "Article 1",
                        "siteName": "Example Site 1"
                    },
                    {
                        "url": "https://example.com/article2",
                        "name": "Article 2",
                        "siteName": "Example Site 2"
                    },
                    {
                        "url": "https://example.com/article3",
                        "name": "Article 3",
                        "siteName": "Example Site 3"
                    }
                ]
                ##########3
                successful_links_json = json.dumps({"datatype": "link", "data": successful_links_info},
                                                   ensure_ascii=False)
                #print("sujson", successful_links_json)
                print("正在发送链接")
                await send_links_callback(text=successful_links_json,text_type='json')
                print("发送完毕")
                return"胡泽红"
            else:
                print(f"请求失败，状态码: {response.status}, 消息: {await response.text()}")
#抓取的网站: [{'url': 'https://new.qq.com/rain/a/20241005A04DG600', 'siteName': '腾讯新闻'}, {'url': 'https://www.bilibili.com/video/BV1y9xsePEmJ/', 'siteName': '哔哩哔哩'}, {'url': 'https://k.sina.com.cn/article_2131593523_7f0d893302001galo.html', 'siteName': '新浪'}]


#同步的谷歌
# def get_scraped_contents(query: str) -> List[str]:
#     api_key = 'AIzaSyAceACHETCsQcYZX0Vomv7Cr7ov9-V-9iM'
#     cx = '9361a038cc155475d'
#     url = f'https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}&c2coff=1&lr="lang_zh-CN"'
#     print("url",url)
#     response = requests.get(url)
#     data = response.json()
#     links = [item['link'] for item in data['items']][:1]
#     #[item['url'] for item in data['data']['webPages']['value']]
#     print("links",links)
#     scraped_contents = []
#     for url in links:
#         i=1
#         print(f"正在抓取第{i}个网页资料")
#         content = scrape_page(url)  # 假设 scrape_page 函数已经定义
#         scraped_contents.append(content)
#         i+=1
#
#     return scraped_contents




async def main():
    query = "霁月难逢，彩云易散"
    await bingsearch_answer(query)

if __name__ == "__main__":
    asyncio.run(main())






