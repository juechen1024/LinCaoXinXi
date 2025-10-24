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
    "https://lcj.shanxi.gov.cn/zxyw/xxkb/index",  # 省局动态
    "https://lcj.shanxi.gov.cn/zxyw/lqjs/index",  # 林局建设
    "https://lcj.shanxi.gov.cn/zxyw/sxlq/index"   # 市县林情
]


# === 工具函数 ===
def make_request(url):
    """请求页面内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    content_type = resp.headers.get('Content-Type', '').lower()
    if 'charset=gbk' in content_type or 'charset=gb2312' in content_type:
        resp.encoding = 'gbk'
    else:
        resp.encoding = 'utf-8'
    return resp.text

def parse_news_list_sanxi(url):
    """解析新闻列表页，返回满足时间要求的新闻链接"""
    html = make_request(url)
    soup = BeautifulSoup(html, "html.parser")
    news_list = []
    has_recent_news = False
    days_ago_date = datetime.now() - timedelta(days=DAYS_AGO)

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


def parse_news_detail_sanxi(url):
    """解析新闻详情页并返回正文内容"""
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

        # 清理杂项元素
        for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
            element.decompose()

        text = content_div.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'来源.*?分享', '', text, flags=re.DOTALL)
        return text

    except Exception as e:
        print(f"获取新闻详情失败: {e}")
        return None


def fetch_shnxi_news():
    """主函数：获取山西省林草局近一周新闻"""
    print(f"14山西数据采集开始")
    all_news = []
    for start_url in START_URLS:
        page = 1
        while True:
            if page == 1:
                url = f"{start_url}.html"
            else:
                url = f"{start_url}_{page - 1}.html"

            news_list, has_recent_news = parse_news_list_sanxi(url)

            if not has_recent_news:
                break

            for i, news in enumerate(news_list, 1):
                text = parse_news_detail_sanxi(news["url"])
                if not text:
                    continue
                # 截取长度
                if len(text) > CONTENT_LENGTH:
                    display_text = "山西省林草信息，" + text[:CONTENT_LENGTH] + "..."
                else:
                    display_text = "山西省林草信息，" + text
                all_news.append(display_text)
            page += 1
    print(f"14山西     ", len(all_news))
    return all_news


def main():
    sanxi_news_list = fetch_shnxi_news()
    for i, text in enumerate(sanxi_news_list, 1):
        print(f"{i}: {text}")


if __name__ == "__main__":
    main()
