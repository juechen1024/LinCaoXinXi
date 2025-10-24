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
    "http://www.xzly.gov.cn/xinxi/jiguan1",
    "http://www.xzly.gov.cn/xinxi/jiguan3",
    "http://www.xzly.gov.cn/xinxi/jiguan4",
    "http://www.xzly.gov.cn/xinxi/jiguan5",
    "http://www.xzly.gov.cn/xinxi/jiguan6",
    "http://www.xzly.gov.cn/xinxi/jiguan7",
    "http://www.xzly.gov.cn/xinxi/jiguan8",
    "http://www.xzly.gov.cn/xinxi/jiguan9",
    "http://www.xzly.gov.cn/xinxi/jiguan10",
    "http://www.xzly.gov.cn/xinxi/jiguan14",
    "http://www.xzly.gov.cn/xinxi/jiguan15",
    "http://www.xzly.gov.cn/xinxi/difang"
]


def make_request(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    if 'gb' in r.apparent_encoding.lower():
        r.encoding = 'gbk'
    else:
        r.encoding = 'utf-8'
    return r.text


def parse_news_list_xizang(url, days_ago_date):
    html = make_request(url)
    soup = BeautifulSoup(html, 'html.parser')
    news_list = []
    has_recent_news = False

    ul = soup.find("ul", class_="ui-list-news heading-square")
    if not ul:
        return news_list, has_recent_news

    for li in ul.find_all("li"):
        a_tag = li.find("a")
        if not a_tag:
            continue
        href = urljoin(url, a_tag.get("href"))
        date_span = li.find("span", class_="news-date")
        if not date_span:
            continue
        try:
            news_date = datetime.strptime(date_span.text.strip(), "%Y/%m/%d")
            if news_date >= days_ago_date:
                news_list.append({"url": href, "date": news_date})
                has_recent_news = True
        except ValueError:
            continue
    return news_list, has_recent_news


def parse_news_detail_xizang(url):
    html = make_request(url)
    soup = BeautifulSoup(html, 'html.parser')

    # 标题
    title_tag = soup.find('meta', {'name': 'ArticleTitle'})
    title = title_tag['content'] if title_tag else ''
    # 日期
    date_tag = soup.find('meta', {'name': 'PubDate'})
    date = date_tag['content'][:10] if date_tag else ''
    # 内容区域
    content_div = None
    for div in soup.find_all('div'):
        text = div.get_text().strip()
        if len(text) > 200 and len(text.split('\n')) > 3:
            content_div = div
            break
    if content_div:
        for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            element.decompose()
        text = content_div.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'西藏林业信息网.*?正文', '', text, flags=re.DOTALL)
        text = re.sub(r'【.*?】', '', text, flags=re.DOTALL)
    else:
        text = ''

    text = f"{title}\n{date}\n{text}".strip()
    if len(text) > CONTENT_LENGTH:
        text = "西藏自治区林草信息，"+text[:CONTENT_LENGTH] + "..."
    return text


def fetch_xizang_news():
    print("54西藏数据采集开始")
    all_news = []
    today = datetime.now()
    days_ago_date = today - timedelta(days=DAYS_AGO)

    for start_url in START_URLS:
        page = 1
        while True:
            page_url = f"{start_url}?page={page}"
            news_list, has_recent_news = parse_news_list_xizang(page_url, days_ago_date)
            if not has_recent_news:
                break
            for news in news_list:
                try:
                    text = parse_news_detail_xizang(news["url"])
                    all_news.append(text)
                except Exception:
                    continue
            page += 1
    print(f"54西藏     ", len(all_news))
    return all_news


if __name__ == "__main__":
    xizang_news_list = fetch_xizang_news()
    for news in xizang_news_list:
        print("、、", news)
