"""
Volume spike detection + news correlation monitor.
Alerts when volume moves fast AND correlates with breaking news.
"""

import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Assets to monitor
WATCHLIST = {
    "crypto": ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "BNB-USD"],
    "stocks": ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META"],
    "indices": ["SPY", "QQQ", "GLD"],
}

# Volume spike threshold — alert if volume is X times above average
SPIKE_THRESHOLD = 2.0  # 2x average = alert

# Store previous volumes to detect spikes
previous_volumes = {}
previous_prices = {}


def get_current_data(ticker: str) -> dict:
    """Get current price and volume for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d", interval="1h")
        if hist.empty:
            return None

        current_volume = hist["Volume"].iloc[-1]
        avg_volume = hist["Volume"].iloc[:-1].mean()
        current_price = hist["Close"].iloc[-1]
        prev_price = hist["Close"].iloc[-2]
        price_change = ((current_price - prev_price) / prev_price) * 100

        return {
            "ticker": ticker,
            "price": current_price,
            "price_change": price_change,
            "volume": current_volume,
            "avg_volume": avg_volume,
            "volume_ratio": current_volume / avg_volume if avg_volume > 0 else 0,
        }
    except Exception:
        return None


async def get_related_news(ticker: str) -> str:
    """Get latest news headline for a ticker."""
    if not NEWS_API_KEY:
        return None

    clean_ticker = ticker.replace("-USD", "")
    queries = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "XRP": "XRP OR Ripple",
        "SOL": "Solana",
        "BNB": "Binance",
        "AAPL": "Apple stock",
        "TSLA": "Tesla stock",
        "NVDA": "Nvidia stock",
        "MSFT": "Microsoft stock",
        "AMZN": "Amazon stock",
        "GOOGL": "Google stock",
        "META": "Meta stock",
        "SPY": "S&P 500",
        "QQQ": "Nasdaq",
        "GLD": "Gold",
    }
    query = queries.get(clean_ticker, clean_ticker)

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": NEWS_API_KEY,
            "pageSize": 1,
            "sortBy": "publishedAt",
            "language": "en",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.json()
                    articles = data.get("articles", [])
                    if articles:
                        title = articles[0].get("title", "")
                        source = articles[0].get("source", {}).get("name", "")
                        url = articles[0].get("url", "")
                        if title and title != "[Removed]":
                            return f"[{title}]({url}) — _{source}_"
    except Exception:
        pass
    return None


def format_spike_alert(data: dict, news: str = None) -> str:
    """Format a volume spike alert message."""
    ticker = data["ticker"].replace("-USD", "")
    price = data["price"]
    price_change = data["price_change"]
    volume_ratio = data["volume_ratio"]

    # Direction
    if price_change > 0:
        price_emoji = "📈"
        direction = "UP"
    else:
        price_emoji = "📉"
        direction = "DOWN"

    # Volume intensity
    if volume_ratio >= 5:
        intensity = "🔥🔥🔥 EXTREME"
    elif volume_ratio >= 3:
        intensity = "🔥🔥 HIGH"
    else:
        intensity = "🔥 ELEVATED"

    sign = "+" if price_change > 0 else ""

    lines = [
        f"⚡ *VOLUME SPIKE ALERT — {ticker}*",
        f"",
        f"{price_emoji} Price: `${price:,.2f}` ({sign}{price_change:.2f}%)",
        f"📊 Volume: `{volume_ratio:.1f}x` above average — {intensity}",
        f"🧭 Direction: *{direction}*",
        f"🕐 Time: `{datetime.now().strftime('%H:%M:%S')}`",
    ]

    if news:
        lines.append(f"")
        lines.append(f"📰 *Latest news:*")
        lines.append(news)

    lines.append("")
    lines.append("_This may indicate a major market move — check charts immediately_")

    return "\n".join(lines)


async def monitor_volumes(app, chat_ids: set):
    """Background task — monitors volumes every 3 minutes."""
    all_tickers = (
        WATCHLIST["crypto"] +
        WATCHLIST["stocks"] +
        WATCHLIST["indices"]
    )

    while True:
        await asyncio.sleep(180)  # Every 3 minutes

        for ticker in all_tickers:
            try:
                data = get_current_data(ticker)
                if not data:
                    continue

                volume_ratio = data["volume_ratio"]

                # Check if this is a new spike (not already alerted)
                prev_ratio = previous_volumes.get(ticker, 0)

                if volume_ratio >= SPIKE_THRESHOLD and prev_ratio < SPIKE_THRESHOLD:
                    # New spike detected — get related news
                    news = await get_related_news(ticker)
                    message = format_spike_alert(data, news)

                    # Send to all active chats
                    for chat_id in chat_ids:
                        try:
                            await app.bot.send_message(
                                chat_id=chat_id,
                                text=message,
                                parse_mode="Markdown",
                                disable_web_page_preview=True
                            )
                        except Exception as e:
                            print(f"Error sending volume alert: {e}")

                previous_volumes[ticker] = volume_ratio

            except Exception as e:
                print(f"Volume monitor error for {ticker}: {e}")

        await asyncio.sleep(1)  # Small delay between tickers
