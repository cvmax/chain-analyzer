"""
新闻与社交媒体情绪数据采集
- Crypto 专业媒体新闻抓取
- 社交媒体情绪分析
"""
import time
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from config import API_CONFIG, SUPPORTED_CHAINS, NEWS_RSS_SOURCES
from .http_utils import http_get as requests_get

CACHE = {}

# 情绪关键词词典
POSITIVE_KEYWORDS = [
    "bullish", "upgrade", "partnership", "launch", "growth", "adoption",
    "integration", "milestone", "record", "rally", "breakout", "accumulation",
    "利好", "升级", "合作", "增长", "采用", "突破", "新高", "里程碑",
    "mainnet", "airdrop", "listing", "funding", "investment"
]

NEGATIVE_KEYWORDS = [
    "hack", "exploit", "crash", "dump", "bearish", "downgrade", "lawsuit",
    "sec", "regulation", "ban", "vulnerability", "delay", "scam", "selloff",
    "黑客", "攻击", "漏洞", "暴跌", "诉讼", "监管", "禁止", "风险",
    "rugpull", "phishing", "shutdown", "bankruptcy", "liquidation"
]


def _cached(key, fetcher, ttl=600):
    now = time.time()
    if key in CACHE and CACHE[key][0] > now - ttl:
        return CACHE[key][1]
    data = fetcher()
    CACHE[key] = (now, data)
    return data


def _analyze_sentiment(text):
    """简单的文本情绪分析"""
    text_lower = text.lower()
    positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw.lower() in text_lower)
    negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw.lower() in text_lower)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    return "neutral"


def _extract_keywords(text, chain_id):
    """检查文本是否与目标链相关"""
    chain = SUPPORTED_CHAINS.get(chain_id, {})
    keywords = [
        chain.get("name", "").lower(),
        chain.get("symbol", "").lower(),
        chain_id.lower(),
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords if kw)


def fetch_rss_news():
    """抓取 RSS 新闻源"""
    all_news = []
    for source in NEWS_RSS_SOURCES:
        try:
            r = requests_get(source, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (compatible; ChainAnalyzer/1.0)"
            })
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                for item in root.iter("item"):
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    description = item.find("description")

                    title_text = title.text if title is not None else ""
                    desc_text = description.text if description is not None else ""

                    # 清理 HTML 标签
                    desc_text = re.sub(r"<[^>]+>", "", desc_text)[:300]

                    all_news.append({
                        "title": title_text,
                        "url": link.text if link is not None else "",
                        "date": pub_date.text if pub_date is not None else "",
                        "description": desc_text,
                        "source": source.split("/")[2],
                        "sentiment": _analyze_sentiment(title_text + " " + desc_text),
                    })
        except Exception:
            continue

    return all_news


def fetch_cryptopanic_news(chain_id):
    """从 CryptoPanic 获取特定代币的新闻"""
    cfg = API_CONFIG["cryptopanic"]
    chain = SUPPORTED_CHAINS.get(chain_id, {})
    symbol = chain.get("symbol", chain_id).upper()

    if not cfg["api_key"]:
        return []

    try:
        r = requests_get(f"{cfg['base_url']}/posts/", params={
            "auth_token": cfg["api_key"],
            "currencies": symbol,
            "kind": "news",
            "public": "true",
        }, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
            news = []
            for item in results[:20]:
                news.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "date": item.get("published_at", ""),
                    "source": item.get("source", {}).get("title", ""),
                    "sentiment": _analyze_sentiment(
                        item.get("title", "") + " " + (item.get("description", "") or "")
                    ),
                    "votes": item.get("votes", {}).get("total", 0),
                })
            return news
    except Exception:
        pass
    return []


def get_news_for_chain(chain_id):
    """获取与特定链相关的新闻"""
    def _fetch():
        all_news = []

        # 1. CryptoPanic
        cp_news = fetch_cryptopanic_news(chain_id)
        all_news.extend(cp_news)

        # 2. RSS 新闻 (过滤相关)
        rss_news = fetch_rss_news()
        filtered = [n for n in rss_news if _extract_keywords(
            n.get("title", "") + " " + n.get("description", ""), chain_id
        )]
        all_news.extend(filtered[:10])

        # 3. 去重排序
        seen = set()
        unique_news = []
        for n in all_news:
            key = n.get("title", "")[:50]
            if key not in seen:
                seen.add(key)
                unique_news.append(n)

        # 按日期排序
        unique_news.sort(key=lambda x: x.get("date", ""), reverse=True)

        # 情绪统计
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for n in unique_news:
            sentiment_counts[n.get("sentiment", "neutral")] += 1

        total = len(unique_news) or 1
        overall_sentiment = (
            "偏多" if sentiment_counts["positive"] / total > 0.5
            else "偏空" if sentiment_counts["negative"] / total > 0.5
            else "中性"
        )

        return {
            "total_articles": len(unique_news),
            "articles": unique_news[:30],
            "sentiment_breakdown": sentiment_counts,
            "overall_sentiment": overall_sentiment,
        }

    return _cached(f"news_{chain_id}", _fetch)


def get_all_news():
    """获取所有链的新闻汇总"""
    all_news = {}
    for chain_id in SUPPORTED_CHAINS:
        all_news[chain_id] = get_news_for_chain(chain_id)
    return all_news