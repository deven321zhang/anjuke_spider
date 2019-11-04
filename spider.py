import requests
import pyquery
import time
import json


class Spider(object):
    """
    通用爬虫
    """

    def __init__(self):
        self.base_url = ''
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        }
        self.url_list = []
        self.info_list = []
        self.max_page = 50

    # 获取响应
    def get_response(self, url):
        response = requests.get(url=url, headers=self.headers)
        return response.content.decode()

    def get_url_list(self, resp):
        pyquery_doc = pyquery.PyQuery(resp)
        articles = pyquery_doc('article').items()
        for article in articles:
            self.url_list.append(article('.entry-title a').attr('href'))

    def parse_detail(self, data):
        pass

    def save_as_json(self):
        json.dump(self.info_list, open('itebooks_spider.json', 'w',
                                       encoding='utf-8'), indent=2, ensure_ascii=False)
        print('save file successful')

    def run(self):
        for page_num in range(1, 2):
            url = self.base_url.format(page_num=str(page_num))
            response = self.get_response(url)
            self.get_url_list(response)

            for url in self.url_list:
                time.sleep(1)
                print(url)
                response = self.get_response(url)
                self.parse_detail(response)

            self.save_as_json()
