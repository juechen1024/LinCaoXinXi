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
    "https://lcj.qinghai.gov.cn/xwdt/snxw",
]


def make_request(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    if 'gb' in r.apparent_encoding.lower():
        r.encoding = 'gbk'
    else:
        r.encoding = 'utf-8'
    return r.text


def parse_news_list_qinghai(url, days_ago_date):
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


def parse_news_detail_qinghai(url):
    html = make_request(url)
    soup = BeautifulSoup(html, 'html.parser')

    # 提取标题
    title_div = soup.find('div', class_='con-tt')
    title = title_div.get_text(strip=True) if title_div else ''

    # 提取日期
    time_span = soup.find('span', class_='con-mar')
    if time_span:
        time_text = time_span.get_text(strip=True)
        date = time_text.replace('时间：', '')[:10] if '时间：' in time_text else time_text[:10]
    else:
        date = ''

    # 提取新闻内容
    content_div = None
    all_divs = soup.find_all('div')
    for div in all_divs:
        text = div.get_text().strip()
        if len(text) > 200 and len(text.split('\n')) > 3:
            content_div = div
            break

    if content_div:
        for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            element.decompose()
        text = content_div.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'您的位置.*?详细内容', '', text, flags=re.DOTALL)
        text = re.sub(r'来源：.*?发布时间：', '发布时间：', text)
        text = re.sub(r'浏览次数.*?大 】', '', text, flags=re.DOTALL)
    else:
        text = ''

    full_text = f"{title}\n{date}\n{text}"
    if len(full_text) > CONTENT_LENGTH:
        full_text = full_text[:CONTENT_LENGTH] + "..."
    return full_text


def fetch_qinghai_news():
    print("63青海数据采集开始")
    all_news = []
    today = datetime.now()
    days_ago_date = today - timedelta(days=DAYS_AGO)

    for start_url in START_URLS:
        page = 1
        while True:
            page_url = f"{start_url}_1" if page == 1 else f"{start_url}_{page}"
            news_list, has_recent_news = parse_news_list_qinghai(page_url, days_ago_date)
            if not has_recent_news:
                break
            for news in news_list:
                try:
                    text = parse_news_detail_qinghai(news["url"])
                    all_news.append(text)
                except Exception:
                    continue
            page += 1
    print(f"63青海     ", len(all_news))
    return all_news


if __name__ == "__main__":
    qinghai_news_list = fetch_qinghai_news()
    for news in qinghai_news_list:
        print("、、", news)
