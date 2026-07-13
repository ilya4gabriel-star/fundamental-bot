"""
News monitoring and sentiment analysis service.
"""

import aiohttp
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from dotenv import load_dotenv
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Keywords that indicate market-moving news
BREAKING_KEYWORDS = [
    "crash", "surge", "ban", "hack", "bankrupt", "collapse",
    "record high", "record low", "rate hike", "rate cut", "fed",
    "sanctions", "war", "ceasefire", "acquisition", "merger",
    "ipo", "sec", "arrest", "fraud", "regulation", "lawsuit",
    "earnings beat", "earnings miss", "layoffs", "recession"
]

# News sources by category
SOURCES = {
    "financial": "bloomberg,reuters,the-wall-street-journal,cnbc,financial-times,business-insider,fortune",
    "crypto": "crypto-coins-news,coindesk",
    "geopolitical": "bbc-news,associated-press,the-guardian,al-jazeera-english,reuters",
}

TICKER_QUERIES = {
    "BTC": "Bitcoin OR BTC",
    "ETH": "Ethereum OR ETH",
    "XRP": "XRP OR Ripple",
    "SOL": "Solana OR SOL",
    "AAPL": "Apple Inc OR AAPL stock",
    "TSLA": "Tesla OR TSLA stock",
    "NVDA": "Nvidia OR NVDA stock",
    "MSFT": "Microsoft OR MSFT stock",
    "GOOGL": "Google OR Alphabet OR GOOGL",
    "AMZN": "Amazon OR AMZN stock",
}


def simple_sentiment(title: str, description: str = "") -> tuple:
    """Returns (emoji, label, score) based on keyword analysis."""
    text = (title + " " + description).lower()

    bullish = [
        "surge", "soar", "rally", "gain", "rise", "jump", "bull",
        "high", "record", "growth", "up", "positive", "buy", "boom",
        "beat", "exceed", "profit", "approve", "launch", "partner",
        "acquire", "breakthrough", "upgrade", "outperform"
    ]
    bearish = [
        "crash", "drop", "fall", "plunge", "bear", "low", "down",
        "sell", "loss", "decline", "fear", "risk", "warn", "dump",
        "miss", "fail", "ban", "hack", "bankrupt", "fraud", "lawsuit",
        "downgrade", "underperform", "recession", "layoff"
    ]

    bull_score = sum(1 for w in bullish if w in text)
    bear_score = sum(1 for w in bearish if w in text)

    if bull_score > bear_score + 1:
        return "🟢", "Bullish", bull_score - bear_score
    elif bear_score > bull_score + 1:
        return "🔴", "Bearish", -(bear_score - bull_score)
    return "⚪", "Neutral", 0


def is_breaking(title: str, description: str = "") -> bool:
    """Returns True if news is potentially market-moving."""
    text = (title + " " + description).lower()
    return any(kw in text for kw in BREAKING_KEYWORDS)


async def fetch_news(query: str, sources: str = None, page_size: int = 5) -> list:
    """Fetch news from NewsAPI."""
    if not NEWS_API_KEY:
        return []

    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "language": "en",
    }
    if sources:
        params["sources"] = sources

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                NEWS_API_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("articles", [])
    except Exception as e:
        print(f"NewsAPI error: {e}")
    return []


async def get_news_for_ticker(ticker: str) -> str:
    """Get formatted news for a specific ticker."""
    query = TICKER_QUERIES.get(ticker.upper(), ticker)
    all_sources = f"{SOURCES['financial']},{SOURCES['crypto']},{SOURCES['geopolitical']}"

    articles = await fetch_news(query, page_size=7)

    if not articles:
        return f"❌ No recent news found for *{ticker}*."

    lines = [f"📰 *Latest News — {ticker.upper()}*\n"]
    bull_count = 0
    bear_count = 0

    for a in articles[:6]:
        title = a.get("title", "")
        url = a.get("url", "")
        source = a.get("source", {}).get("name", "")
        published = a.get("publishedAt", "")[:10]
        description = a.get("description", "") or ""

        if not title or title == "[Removed]":
            continue

        emoji, label, score = simple_sentiment(title, description)
        breaking = "🚨 " if is_breaking(title, description) else ""

        if score > 0:
            bull_count += 1
        elif score < 0:
            bear_count += 1

        if url:
            lines.append(f"{breaking}{emoji} [{title}]({url})")
        else:
            lines.append(f"{breaking}{emoji} {title}")
        lines.append(f"_— {source} · {published}_\n")

    # Overall sentiment summary
    total = bull_count + bear_count
    if total > 0:
        lines.append("─" * 20)
        if bull_count > bear_count:
            lines.append(f"📊 *Overall sentiment: Bullish* ({bull_count} positive, {bear_count} negative articles)")
        elif bear_count > bull_count:
            lines.append(f"📊 *Overall sentiment: Bearish* ({bear_count} negative, {bull_count} positive articles)")
        else:
            lines.append(f"📊 *Overall sentiment: Mixed* ({bull_count} positive, {bear_count} negative articles)")

    return "\n".join(lines)


async def get_market_news() -> str:
    """Get general market-moving news."""
    queries = [
        ("Markets", "stock market OR S&P 500 OR Wall Street"),
        ("Crypto", "cryptocurrency OR Bitcoin OR crypto market"),
        ("Macro", "Federal Reserve OR interest rates OR inflation OR GDP"),
        ("Geopolitical", "war OR sanctions OR trade war OR geopolitical"),
    ]

    lines = ["🌍 *Breaking Market News*\n"]

    for category, query in queries:
        articles = await fetch_news(query, page_size=2)
        if articles:
            lines.append(f"*{category}:*")
            for a in articles[:2]:
                title = a.get("title", "")
                url = a.get("url", "")
                source = a.get("source", {}).get("name", "")

                if not title or title == "[Removed]":
                    continue

                emoji, _, _ = simple_sentiment(title)
                breaking = "🚨 " if is_breaking(title) else ""

                if url:
                    lines.append(f"{breaking}{emoji} [{title}]({url})")
                else:
                    lines.append(f"{breaking}{emoji} {title}")
                lines.append(f"_— {source}_\n")

    return "\n".join(lines)


async def monitor_breaking_news(app, chat_ids: list):
    """Background task — monitors news every 5 minutes and pushes breaking alerts."""
    seen_urls = set()

    monitor_queries = [
        "stock market crash OR market surge OR fed rate",
        "bitcoin crash OR bitcoin surge OR crypto ban",
        "war OR sanctions OR major acquisition OR IPO",
        "earnings beat OR earnings miss OR bankruptcy",
    ]

    while True:
        await asyncio.sleep(300)  # Every 5 minutes

        for query in monitor_queries:
            articles = await fetch_news(query, page_size=3)

            for article in articles:
                url = article.get("url", "")
                title = article.get("title", "")
                description = article.get("description", "") or ""
                source = article.get("source", {}).get("name", "")

                if not title or title == "[Removed]" or url in seen_urls:
                    continue

                if is_breaking(title, description):
                    seen_urls.add(url)
                    emoji, label, _ = simple_sentiment(title, description)

                    message = (
                        f"🚨 *BREAKING NEWS*\n\n"
                        f"{emoji} *{label}*\n\n"
                        f"{title}\n\n"
                        f"_— {source}_"
                    )
                    if url:
                        message += f"\n\n[Read more]({url})"

                    for chat_id in chat_ids:
                        try:
                            await app.bot.send_message(
                                chat_id=chat_id,
                                text=message,
                                parse_mode="Markdown",
                                disable_web_page_preview=True
                            )
                        except Exception as e:
                            print(f"Error sending news alert: {e}")

        # Keep seen_urls from growing too large
        if len(seen_urls) > 500:
            seen_urls = set(list(seen_urls)[-200:])
