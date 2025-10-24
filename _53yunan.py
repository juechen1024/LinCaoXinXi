# -*- coding: utf-8 -*-
"""
云南省林业和草原局近一周新闻爬虫（无彩色打印，无Word保存）
"""
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
load_dotenv()
CONTENT_LENGTH = int(os.getenv("CONTENT_LENGTH", 350))
DAYS_AGO = int(os.getenv("DAYS_AGO", 7))
START_URLS = [
    "http://lcj.yn.gov.cn/html/mainnews",
]


def make_request(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    if 'gb' in r.apparent_encoding.lower():
        r.encoding = 'gbk'
    else:
        r.encoding = 'utf-8'
    return r.text


def parse_news_list_yunan(url, days_ago_date):
    """解析新闻列表页"""
    html = make_request(url)
    soup = BeautifulSoup(html, 'html.parser')
    news_list = []
    has_recent_news = False

    for li in soup.find_all("li"):
        a_tag = li.find("a")
        if not a_tag:
            continue
        href = urljoin(url, a_tag.get("href"))
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', li.text)
        if not date_match:
            continue
        try:
            news_date = datetime.strptime(date_match.group(), "%Y-%m-%d")
            if news_date >= days_ago_date:
                news_list.append({"url": href, "date": news_date})
                has_recent_news = True
        except ValueError:
            continue
    return news_list, has_recent_news


def parse_news_detail_yunan(url):
    """解析新闻详情页"""
    html = make_request(url)
    soup = BeautifulSoup(html, 'html.parser')

    # 获取标题
    title_tag = soup.find('meta', {'name': 'ArticleTitle'})
    title = title_tag['content'] if title_tag else '未找到标题'
    # 获取日期
    date_tag = soup.find('meta', {'name': 'PubDate'})
    date = date_tag['content'][:10] if date_tag else ''
    # 获取内容
    content_div = None
    for div in soup.find_all('div'):
        text = div.get_text().strip()
        if len(text) > 200 and len(text.split('\n')) > 3:
            content_div = div
            break
    if content_div:
        for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            element.decompose()
        paragraphs = content_div.find_all('p')
        text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    else:
        text = ''
    text = f"{title}\n{date}\n{text}"
    text = re.sub(r'\s+', ' ', text)
    if len(text) > CONTENT_LENGTH:
        text = "云南省林草信息"+text[:CONTENT_LENGTH] + "..."
    return text


def fetch_yunnan_news():
    print("53云南数据采集开始")
    all_news = []
    today = datetime.now()
    days_ago_date = today - timedelta(days=DAYS_AGO)

    for start_url in START_URLS:
        page = 1
        while True:
            page_url = start_url if page == 1 else f"{start_url.rstrip('/')}_{page}.html"
            try:
                news_list, has_recent_news = parse_news_list_yunan(page_url, days_ago_date)
            except Exception:
                break
            if not has_recent_news:
                break
            for news in news_list:
                try:
                    text = parse_news_detail_yunan(news["url"])
                    all_news.append(text)
                except Exception:
                    continue
            page += 1
    print(f"53云南     ", len(all_news))
    return all_news


if __name__ == "__main__":
    yunnan_news_list = fetch_yunnan_news()
    for news in yunnan_news_list:
        print("、、", news)
