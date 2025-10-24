
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os
load_dotenv()
CONTENT_LENGTH = int(os.getenv("CONTENT_LENGTH", 350))
DAYS_AGO = int(os.getenv("DAYS_AGO", 7))

START_URLS = [
    "http://lyj.zj.gov.cn/col/col1276365/index.html",
    "http://lyj.zj.gov.cn/col/col1285504/index.html",
]

# === 工具函数 ===
def make_request(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    if 'gb' in r.apparent_encoding.lower():
        r.encoding = 'gbk'
    else:
        r.encoding = 'utf-8'
    return r.text

def parse_news_list_zhejiang(url):
    """抓取单个新闻列表页并返回近一周新闻列表"""
    html = make_request(url)
    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find('script', type='text/xml')
    if not script_tag:
        print(f"未找到新闻记录的 script 标签: {url}")
        return []

    script_content = script_tag.string
    records = re.findall(r'<record><!\[CDATA\[(.*?)\]\]></record>', script_content, re.DOTALL)
    today = datetime.now()
    days_ago_date = today - timedelta(days=DAYS_AGO)

    recent_news = []
    for record in records:
        record_soup = BeautifulSoup(record, 'html.parser')
        link_tag = record_soup.find('a')
        date_td = record_soup.find('td', class_='hui14') or (
            record_soup.find_all('td')[2] if len(record_soup.find_all('td')) > 2 else None
        )
        if not link_tag or not date_td:
            continue

        href = urljoin(url, link_tag.get('href', ''))
        date_str = date_td.get_text().strip()
        try:
            news_date = datetime.strptime(date_str, "%Y-%m-%d")
            if news_date >= days_ago_date:
                recent_news.append({
                    'url': href,
                    'title': link_tag.get('title', ''),
                    'date': date_str
                })
        except ValueError:
            continue
    return recent_news

def parse_news_detail_zhejiang(url):
    """抓取新闻详情文本"""
    try:
        html = make_request(url)
        soup = BeautifulSoup(html, "html.parser")
        content_div = None
        for div in soup.find_all('div'):
            text = div.get_text().strip()
            if len(text) > 200 and len(text.split('\n')) > 3:
                content_div = div
                break

        if content_div:
            for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                element.decompose()
            text = content_div.get_text(separator='\n', strip=True)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'新闻资讯 省内要闻 市县动态 国内外动态 省内要闻 首页 > 新闻资讯 > 省内要闻', '', text, flags=re.DOTALL)
            text = re.sub(r'市县动态.*?> 市县动态', '', text, flags=re.DOTALL)
            text = re.sub(r'访问次数.*?朋友圈', '', text, flags=re.DOTALL)
            if len(text) > CONTENT_LENGTH:
                text = text[:CONTENT_LENGTH] + "..."
            return '浙江省林草信息，' + text
        else:
            return ""
    except Exception as e:
        print(f"抓取新闻详情失败: 错误: {e}")
        return ""

def fetch_zhejiang_news():
    """抓取所有栏目近一周新闻，并返回文本数组"""
    all_news_texts = []
    print("33浙江数据采集开始")
    for url in START_URLS:
        news_list = parse_news_list_zhejiang(url)
        for news in news_list:
            text = parse_news_detail_zhejiang(news['url'])
            if text:
                all_news_texts.append(text)
    print(f"33浙江     ", len(all_news_texts))
    return all_news_texts

if __name__ == "__main__":
    zhejiang_news_list = fetch_zhejiang_news()
    print(f"\n抓取完成，总共获取 {len(zhejiang_news_list)} 条新闻")
    for i, text in enumerate(zhejiang_news_list, 1):
        print(f"{i}、 {text}")

