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

# === 常量配置 ===
START_URLS = [
    "https://lyj.henan.gov.cn/lyzx/zbbd/index.html",
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

def parse_news_list_henan(url, days_ago_date):
    """解析河南省新闻列表页，返回近一周新闻链接"""
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

def parse_news_detail_henan(url):
    """解析河南省新闻详情页并返回正文内容"""
    try:
        html = make_request(url)
        soup = BeautifulSoup(html, "html.parser")

        # 找正文区域
        content_div = None
        for div in soup.find_all('div'):
            text = div.get_text().strip()
            if len(text) > 200 and len(text.split('\n')) > 3:
                content_div = div
                break

        if not content_div:
            return None

        # 清理无关元素
        for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            element.decompose()

        text = content_div.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # 防止极端乱码，强制 UTF-8 编码
        text = text.encode('utf-8', errors='ignore').decode('utf-8')

        return text

    except Exception as e:
        print(f"获取新闻详情失败: {e}")
        return None

def fetch_henan_news():
    """主函数：获取河南省林草局近一周新闻"""
    print(f"41河南数据采集开始")
    all_news = []
    today = datetime.now()
    days_ago_date = today - timedelta(days=DAYS_AGO)

    for start_url in START_URLS:
        page = 1
        while True:
            page_url = start_url if page == 1 else f"{start_url.rstrip('.html')}_{page - 1}.html"
            news_list, has_recent_news = parse_news_list_henan(page_url, days_ago_date)

            if not has_recent_news:
                break

            for i, news in enumerate(news_list, 1):
                text = parse_news_detail_henan(news["url"])
                if not text:
                    continue
                # 截取长度
                if len(text) > CONTENT_LENGTH:
                    display_text = "河南省林草信息，" + text[:CONTENT_LENGTH] + "..."
                else:
                    display_text = "河南省林草信息，" + text
                all_news.append(display_text)

            page += 1

    print(f"41河南     ", len(all_news))
    return all_news

def main():
    henan_news_list = fetch_henan_news()
    for news in henan_news_list:
        print("、",news)

if __name__ == "__main__":
    main()
