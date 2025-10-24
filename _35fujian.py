import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import requests


from dotenv import load_dotenv
import os
load_dotenv()
CONTENT_LENGTH = int(os.getenv("CONTENT_LENGTH", 350))
DAYS_AGO = int(os.getenv("DAYS_AGO", 7))
START_URL = "https://lyj.fujian.gov.cn/zxzx/lydt/"

# === 工具函数 ===
def make_request(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    if 'gb' in r.apparent_encoding.lower():
        r.encoding = 'gbk'
    else:
        r.encoding = 'utf-8'
    return r.text

def parse_news_list_fujian(url):
    """抓取福建省新闻列表页并返回近一周新闻列表"""
    html = make_request(url)
    soup = BeautifulSoup(html, "html.parser")
    news_list_items = soup.find_all("li")
    today = datetime.now()
    days_ago_date = today - timedelta(days=DAYS_AGO)
    recent_news = []

    for li in news_list_items:
        a_tag = li.find("a")
        if not a_tag:
            continue
        href = urljoin(url, a_tag.get("href"))
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', li.text)
        if not date_match:
            continue
        date_str = date_match.group()
        try:
            news_date = datetime.strptime(date_str, "%Y-%m-%d")
            if news_date >= days_ago_date:
                recent_news.append({
                    'url': href,
                    'title': a_tag.get('title', ''),
                    'date': date_str
                })
        except ValueError:
            continue
    return recent_news

def parse_news_content_fujian(url):
    """抓取新闻详情文本"""
    html = make_request(url)
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find('meta', {'name': 'ArticleTitle'})
    title = title_tag['content'] if title_tag else '未找到标题'
    date_tag = soup.find('meta', {'name': 'PubDate'})
    date = date_tag['content'][:10] if date_tag else '未找到日期'

    content_div = soup.find('div', class_='TRS_Editor')
    if content_div:
        paragraphs = content_div.find_all('p')
        text_content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    else:
        text_content = ""

    text = f"{title}\n{date}\n{text_content}"
    if len(text) > CONTENT_LENGTH:
        text = text.replace('\n', '')
        text = "福建省林草信息，" + text[:CONTENT_LENGTH] + "..."
    return text

def fetch_fujian_news():
    """抓取福建省近一周新闻，并返回文本数组"""
    all_news_texts = []
    print("36福建数据采集开始")
    news_list = parse_news_list_fujian(START_URL)
    for idx, news in enumerate(news_list, 1):
        text = parse_news_content_fujian(news['url'])
        all_news_texts.append(text)
    print(f"36福建     ", len(all_news_texts))
    return all_news_texts

if __name__ == "__main__":
    fujian_news_texts = fetch_fujian_news()
    print(f"\n总共获取 {len(fujian_news_texts)} 条新闻")
    for i, text in enumerate(fujian_news_texts, 1):
        print(f"{i}、 {text}")
