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
    "http://lyhcyj.hlj.gov.cn/lyhcyj/c107199/common_list.shtml",  # 工作动态
    "http://lyhcyj.hlj.gov.cn/lyhcyj/c107201/common_list.shtml",  # 重点工作
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


def parse_news_list_heilongjiang(url):
    """解析新闻列表页，返回满足时间要求的新闻链接"""
    html = make_request(url)
    soup = BeautifulSoup(html, "html.parser")
    news_list = []
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
                news_list.append({
                    "url": href,
                    "date": news_date,
                    "title": a_tag.get("title", "").strip()
                })
        except ValueError:
            continue
    return news_list


def parse_news_detail_heilongjiang(url):
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
        for element in content_div.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style',
                                             'a', 'table', 'img', 'figure', 'form',
                                             'button', 'input', 'select', 'textarea']):
            element.decompose()
        for p in content_div.find_all('p'):
            if any(keyword in p.get_text() for keyword in ['您当前的位置', '首页 >', '林草资讯']):
                p.decompose()

        text = content_div.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    except Exception as e:
        print(f"获取新闻详情失败: {e}")
        return None


def fetch_heilongjiang_news():
    """主函数：获取黑龙江省林草局近一周新闻"""
    print("23黑龙江数据采集开始")
    all_news = []
    for start_url in START_URLS:
        news_list = parse_news_list_heilongjiang(start_url)
        for i, news in enumerate(news_list, 1):
            text = parse_news_detail_heilongjiang(news["url"])
            if not text:
                continue
            # 截取长度
            display_text = "黑龙江省林草信息," + text[:CONTENT_LENGTH] + "..." if len(text) > CONTENT_LENGTH else text
            all_news.append(display_text)
    print(f"23黑龙江     ", len(all_news))
    return all_news


def main():
    heilongjiang_news_list = fetch_heilongjiang_news()
    for i, text in enumerate(heilongjiang_news_list, 1):
        print(f"{i}: {text}")


if __name__ == "__main__":
    main()
