import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os
load_dotenv()
CONTENT_LENGTH = int(os.getenv("CONTENT_LENGTH", 350))
DAYS_AGO = int(os.getenv("DAYS_AGO", 7))

START_URLS = [
    "https://lyj.jiangsu.gov.cn/col/col7197/index.html?uid=209921&pageNum=1",  # 省局动态
    "https://lyj.jiangsu.gov.cn/col/col7085/index.html?uid=223903&pageNum=1",  # 林局建设
]



def make_request(url):
    """请求页面内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    time.sleep(1)  # 延迟避免请求过快
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    content_type = resp.headers.get('Content-Type', '').lower()
    if 'charset=gbk' in content_type or 'charset=gb2312' in content_type:
        resp.encoding = 'gbk'
    else:
        resp.encoding = 'utf-8'
    return resp.text


def parse_news_list_jiangsu(base_url):
    """解析新闻列表页，返回近一周新闻条目"""

    html = make_request(base_url)
    soup = BeautifulSoup(html, "html.parser")
    script_tags = soup.find_all("script", type="text/xml")
    recent_news = []
    days_ago_date = datetime.now() - timedelta(days=DAYS_AGO)
    for script in script_tags:
        cdata_content = script.string
        if not cdata_content:
            continue
        records = re.findall(r'<record><!\[CDATA\[(.*?)\]\]></record>', cdata_content, re.DOTALL)
        for record in records:
            record_soup = BeautifulSoup(record, 'html.parser')
            a_tag = record_soup.find('a')
            date_span = record_soup.find('span', class_='bt-data-time')
            if not a_tag or not a_tag.get('href') or not date_span:
                continue
            full_url = urljoin(base_url, a_tag['href'])
            date_match = re.search(r'\[(\d{4}-\d{2}-\d{2})\]', date_span.text)
            if not date_match:
                continue
            date_str = date_match.group(1)
            try:
                news_date = datetime.strptime(date_str, "%Y-%m-%d")
                if news_date >= days_ago_date:
                    recent_news.append({
                        'url': full_url,
                        'title': a_tag.get('title', '').strip() or a_tag.text.strip(),
                        'date': date_str
                    })
            except ValueError:
                print(f"日期解析失败: {date_str}")
                continue

    return recent_news


def fetch_news_detail_jiangsu(news_item):
    """获取新闻详细文本内容"""
    try:
        html = make_request(news_item['url'])
        soup = BeautifulSoup(html, 'html.parser')
        content_div = soup.find('div', id='zoom')
        if content_div:
            for element in content_div.find_all(['a', 'nav', 'header', 'footer', 'aside', 'script', 'style']):
                element.decompose()
            text = content_div.get_text(separator=' ', strip=True)
            text = f"{news_item['title']} 发布日期: {news_item['date']} {text}"
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > CONTENT_LENGTH:
                text = text[:CONTENT_LENGTH] + "..."
            return text
        return "未能找到新闻内容区域"
    except Exception as e:
        return f"获取新闻内容失败: {str(e)}"


def fetch_jiangsu_news():
    """抓取江苏省林业局近一周新闻，返回数组"""
    print("32江苏数据采集开始")
    all_news_texts = []

    print(f"开始采集数据")
    for url in START_URLS:
        recent_news = parse_news_list_jiangsu(url)
        for news_item in recent_news:
            content = fetch_news_detail_jiangsu(news_item)
            all_news_texts.append(content)
    print(f"32江苏     ", len(all_news_texts))
    return all_news_texts


if __name__ == "__main__":
    jiangsu_news_list = fetch_jiangsu_news()
    for i, text in enumerate(jiangsu_news_list, 1):
        print(f"{i}: {text}")
