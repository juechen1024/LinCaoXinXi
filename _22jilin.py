
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
    "https://jllc.jl.gov.cn/xxfb/xydt/jlyw/index",  # 吉林要闻
    "https://jllc.jl.gov.cn/xxfb/xydt/dfdt/index",  # 地方动态
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


def parse_news_list_jilin(url):
    """解析吉林省新闻列表页，返回满足时间要求的新闻链接"""
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


def parse_news_detail_jilin(url):
    """解析新闻详情页并返回正文内容"""
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
        for p in content_div.find_all('p'):
            if any(keyword in p.get_text() for keyword in ['您当前的位置', '首页 >', '林草资讯']):
                p.decompose()

        text = content_div.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '', text)
        text = re.sub(r'\s+', '', text)
        text = text.strip()
        # 去掉栏目多余文字
        text = re.sub(r'您所在的位置.*?>', '', text, flags=re.DOTALL)
        text = re.sub(r'信息发布.*?地方动态', '', text, flags=re.DOTALL)
        text = re.sub(r'字体.*?小', '', text, flags=re.DOTALL)
        text = re.sub(r'来源.*?(?=日期)', '', text, flags=re.DOTALL)
        return text

    except Exception as e:
        print(f"获取新闻详情失败: {e}")
        return None


def fetch_jilin_news():
    """主函数：获取吉林省林草局近一周新闻"""
    print("22吉林数据采集开始")
    all_news = []

    for start_url in START_URLS:
        page = 1
        while True:
            # 构建分页 URL
            if page == 1:
                url = start_url + ".html"
            else:
                url = f"{start_url}_{page - 1}.html"

            news_list, has_recent_news = parse_news_list_jilin(url)
            if not has_recent_news:
                break

            for i, news in enumerate(news_list, 1):
                text = parse_news_detail_jilin(news["url"])
                if not text:
                    continue
                if len(text) > CONTENT_LENGTH:
                    display_text = "吉林省林草信息，" + text[:CONTENT_LENGTH] + "..."
                else:
                    display_text = "吉林省林草信息，" + text
                all_news.append(display_text)
            page += 1

    print(f"22吉林     ", len(all_news))
    return all_news


def main():
    jilin_news_list = fetch_jilin_news()
    for i, text in enumerate(jilin_news_list, 1):
        print(f"{i}: {text}")


if __name__ == "__main__":
    main()
