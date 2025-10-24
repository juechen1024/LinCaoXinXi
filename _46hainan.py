import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os
load_dotenv()
CONTENT_LENGTH = int(os.getenv("CONTENT_LENGTH", 350))
DAYS_AGO = int(os.getenv("DAYS_AGO", 7))

START_URLS = [
    "https://lyj.hainan.gov.cn/ywdt/zwdt/index.html",
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


def parse_news_list_hainan(url, days_ago_date):
    """解析海南新闻列表页，返回近一周新闻链接"""
    html = make_request(url)
    soup = BeautifulSoup(html, "html.parser")
    news_list = []
    has_recent_news = False

    for li in soup.find_all("li"):
        a_tag = li.find("a")
        if not a_tag:
            continue
        href = urljoin(url, a_tag.get("href"))
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", li.text)
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


def parse_news_detail_hainan(url):
    """解析海南新闻详情页并返回正文内容"""
    try:
        html = make_request(url)
        soup = BeautifulSoup(html, "html.parser")

        content_div = None
        for div in soup.find_all('div'):
            text = div.get_text().strip()
            if len(text) > 200 and len(text.split('\n')) > 3:
                content_div = div
                break

        if not content_div:
            return None

        for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            element.decompose()

        text = content_div.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'首页 > 要闻动态 > 工作动态', '', text, flags=re.DOTALL)
        text = text.encode('utf-8', errors='ignore').decode('utf-8')

        return text

    except Exception:
        return None


# === 主函数 ===
def fetch_hainan_news():
    print("46海南数据采集开始")
    all_news = []
    today = datetime.now()
    days_ago_date = today - timedelta(days=DAYS_AGO)
    news_count = 0

    for start_url in START_URLS:
        page = 1
        while True:
            page_url = start_url if page == 1 else f"{start_url.rstrip('.html')}_{page}.html"
            try:
                news_list, has_recent_news = parse_news_list_hainan(page_url, days_ago_date)
            except Exception:
                break

            if not has_recent_news:
                break

            for news in news_list:
                news_count += 1
                text = parse_news_detail_hainan(news["url"])
                if not text:
                    continue
                if len(text) > CONTENT_LENGTH:
                    text = "海南省林草信息，" + text[:CONTENT_LENGTH] + "..."
                all_news.append(text)

            page += 1
    print(f"46海南     ", len(all_news))
    return all_news


def main():
    hainan_news_list = fetch_hainan_news()
    for news in hainan_news_list:
        print("、", news)


if __name__ == "__main__":
    main()
