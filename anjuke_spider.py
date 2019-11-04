import requests
import pyquery
import time
import json
import re


class AnjukeSpider(object):
    """
    安居客爬虫
    """

    def __init__(self):
        self.base_url = 'https://hf.anjuke.com/community/p{page_num}/'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        self.url_list = []
        self.info_list = []
        self.max_page = 1
        self.base_ajax_url = 'https://hf.anjuke.com/community_ajax/824/price/?cis={house_id}'

    def get_response(self, url):
        response = requests.get(url=url, headers=self.headers, verify=False)
        return response.content

    def get_url_list(self, resp):
        pyquery_doc = pyquery.PyQuery(resp)
        lis = pyquery_doc('.li-itemmod').items()
        for li in lis:
            self.url_list.append(li.attr('link'))
            

    def parse_detail(self, resp):
        info = {}
        pyquery_doc = pyquery.PyQuery(resp)

        dts = pyquery_doc('.basic-infos-box > dl dt').items()
        dds = pyquery_doc('.basic-infos-box > dl dd').items()
        for dt, dd in zip(dts, dds):
            dt_text = dt.text().replace(' ', '')
            if '物业类型' in dt_text:
                info['物业类型'] = dd.text().strip()

            if '物业费' in dt_text:
                info['物业费'] = dd.text().strip()

            if '建造年代' in dt_text:
                info['建造年代'] = dd.text().strip()

            if '容积率' in dt_text:
                info['容积率'] = dd.text().strip()

            if '绿化率' in dt_text:
                info['绿化率'] = dd.text().strip()

            if '所属商圈' in dt_text:
                info['所属商圈'] = dd.text().strip()

        span_elms = pyquery_doc('.houses-sets-mod.j-house-num span').items()
        a_elms = pyquery_doc('.houses-sets-mod.j-house-num a').items()
        for span, a in zip(span_elms, a_elms):
            span_text = span.text().replace(' ', '')
            if '二手房房源数' in span_text:
                info['二手房房源数'] = a.text().strip()

            if '租房源数' in span_text:
                info['租房源数'] = a.text().strip()

        house_url = pyquery_doc('.comm-title > a').attr('href')
        match_obj = re.search(r'commid=(\d+)', house_url, re.S)
        house_id = match_obj.group(1)
        resp = self.get_response(url=self.base_ajax_url.format(house_id=house_id))
        json_str = resp.decode()
        json_dict = json.loads(json_str)
        info['均价'] = json_dict.get('data').get(str(house_id)).get('mid_price')
        self.info_list.append(info)

    def save_as_json(self):
        json.dump(self.info_list, open('itebooks_spider.json', 'w',
                                       encoding='utf-8'), indent=2, ensure_ascii=False)
        print('save file successful')

    def run(self):
        for page_num in range(1, self.max_page + 1):
            url = self.base_url.format(page_num=str(page_num))
            response = self.get_response(url)
            self.get_url_list(response)

        for url in self.url_list:
            time.sleep(1)
            print(url)
            response = self.get_response(url)
            self.parse_detail(response)

        self.save_as_json()


if __name__ == '__main__':
    spider = AnjukeSpider()
    spider.run()
