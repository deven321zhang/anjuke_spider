import requests
import pyquery
import time
import json
import requests
import re
import csv, codecs
import numpy as np

requests.packages.urllib3.disable_warnings()


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
        self.url_list = json.load(open('url_list.json', 'r', encoding='utf-8'))
        self.info_list = json.load(open('info_list.json', 'r', encoding='utf-8'))
        with open('current_page.txt', 'r', encoding='utf-8') as f: 
            self.current_page = int(f.read()) + 1
        self.max_page = 50
        self.sleep_time = 0.3
        self.base_ajax_url = 'https://hf.anjuke.com/community_ajax/824/price/?cis={house_id}'

    def get_response(self, url):
        try:
            response = requests.get(url=url, headers=self.headers, verify=False, allow_redirects=False)
            print('url: {} - code: {}'.format(url, response.status_code))
            if response.status_code == 200:
                return response.content
            else:
                # 重定向验证， 在这里打断点， 打开浏览器手动验证 
                response = requests.get(url=url, headers=self.headers, verify=False, allow_redirects=False)
                return response.content
        except requests.ConnectionError as e:
            print('url: {} - e: {}'.format(url, e))
            response = requests.get(url=url, headers=self.headers, verify=False, allow_redirects=False)

    def get_url_list(self, resp):
        pyquery_doc = pyquery.PyQuery(resp)
        lis = pyquery_doc('.li-itemmod').items()
        for li in lis:
            self.url_list.append(li.attr('link'))
            

    def parse_detail(self, resp):
        info = {}
        pyquery_doc = pyquery.PyQuery(resp)

        house_url = pyquery_doc('.comm-title > a').attr('href')
        match_obj = re.search(r'l1=(\d+\.\d+)&l2=(\d+\.\d+).*?commid=(\d+)', house_url, re.S)
        
        info['房源id'] = match_obj.group(3)
        info['纬度'] = match_obj.group(1)
        info['经度'] = match_obj.group(2)
        info['房源名称'] = pyquery_doc('.comm-title > a').attr('title')

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
                rent_num = a.text().strip()
                info['租房源数'] = rent_num
                if rent_num == '暂无数据':
                    info['租金价格中位数'] = '暂无数据'
                else:
                    info['租金价格中位数'] = self.get_rent_middle(url=a.attr('href'))

        match_obj = re.search(r'"comm_midprice":"(\d+)"', resp.decode(), re.S)
        info['均价'] = match_obj.group(1)
        self.info_list.append(info)

    def get_rent_middle(self, url):
        price_list = []
        next_url = url
        while True:
            resp = self.get_response(url=next_url)
            doc = pyquery.PyQuery(resp)
            prices = doc('.m-house-list > li .price > span')
            for price in prices.items():
                price_list.append(int(price.text().strip()))
            next_url = doc('.iNxt').attr('href')
            if not next_url:
                break
        return np.median(price_list)
    


    def save_as_json(self):
        json.dump(self.info_list, open('final_info.json', 'w',
                                       encoding='utf-8'), indent=2, ensure_ascii=False)
        print('save file successful')

    def save_to_csv(self):
        f = codecs.open('anjuke.csv', 'a', encoding='utf8')
        f.seek(0)
        # 从当前位置截断字符串
        f.truncate()
        fieldnames = ['房源id', '纬度', '经度', '房源名称', '物业类型', '物业费', '建造年代', '绿化率', '所属商圈', '二手房房源数', '租房源数', '均价', '租金价格中位数']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()

        for item in self.info_list:
            writer.writerow(item)

        f.close()

    def run(self):
        for page_num in range(self.current_page, self.max_page + 1):
            self.current_page = page_num
            url = self.base_url.format(page_num=str(page_num))
            response = self.get_response(url)
            self.get_url_list(response)

        while self.url_list:
            url = self.url_list.pop()
            time.sleep(self.sleep_time)
            response = self.get_response(url)
            self.parse_detail(response)

        self.save_as_json()
        self.save_to_csv()

        # 重置临时存储的数据
        with open('current_page.txt', 'w', encoding='utf-8') as f:
            f.write(str(0))
        json.dump([], open('url_list.json', 'w',
                                    encoding='utf-8'), indent=2, ensure_ascii=False)
        json.dump([], open('info_list.json', 'w',
                                    encoding='utf-8'), indent=2, ensure_ascii=False)
        


if __name__ == '__main__':
    try:
        spider = AnjukeSpider()
        spider.run()
    except Exception as e:
        print('e: {}'.format(e))
        with open('current_page.txt', 'w', encoding='utf-8') as f:
            f.write(str(spider.current_page))
        json.dump(spider.url_list, open('url_list.json', 'w',
                                    encoding='utf-8'), indent=2, ensure_ascii=False)
        json.dump(spider.info_list, open('info_list.json', 'w',
                                    encoding='utf-8'), indent=2, ensure_ascii=False)
