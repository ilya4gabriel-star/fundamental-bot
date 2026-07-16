"""
Combined technical + news sentiment prediction.
"""

import yfinance as yf
from services.signals import CRYPTO_TICKERS
from services.news_monitor import fetch_news, simple_sentiment, TICKER_QUERIES


async def _get_news_component(ticker: str) -> dict:
    query = TICKER_QUERIES.get(ticker.upper(), ticker)
    articles = await fetch_news(query, page_size=8)

    total_score = 0
    bull_count = 0
    bear_count = 0
    headlines = []

    for a in articles:
        title = a.get("title", "")
        description = a.get("description", "") or ""
        if not title or title == "[Removed]":
            continue
        emoji, label, score = simple_sentiment(title, description)
        total_score += score
        if score > 0:
            bull_count += 1
        elif score < 0:
            bear_count += 1
        headlines.append((emoji, title))

    if bull_count > bear_count:
        overall = "Bullish"
    elif bear_count > bull_count:
        overall = "Bearish"
    else:
        overall = "Neutral"

    return {
        "score": total_score,
        "label": overall,
        "bull_count": bull_count,
        "bear_count": bear_count,
        "headlines": headlines[:3],
    }


def _get_technical_component(ticker: str, timeframe: str = "short") -> dict:
    yf_ticker = CRYPTO_TICKERS.get(ticker.upper(), f"{ticker.upper()}-USD")

    if timeframe == "short":
        period, interval = "7d", "1h"
    elif timeframe == "mid":
        period, interval = "30d", "4h"
    else:
        period, interval = "90d", "1d"

    hist = yf.Ticker(yf_ticker).history(period=period, interval=interval)
    if hist.empty or len(hist) < 20:
        return None

    close = hist["Close"]
    current_price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2])
    price_change = ((current_price - prev_price) / prev_price) * 100

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    ema9 = float(close.ewm(span=9).mean().iloc[-1])
    ema21 = float(close.ewm(span=21).mean().iloc[-1])

    exp1 = close.ewm(span=12).mean()
    exp2 = close.ewm(span=26).mean()
    macd_hist = float((exp1 - exp2 - (exp1 - exp2).ewm(span=9).mean()).iloc[-1])

    long_score = (2 if rsi < 40 else 0) + (1 if ema9 > ema21 else 0) + (1 if macd_hist > 0 else 0)
    short_score = (2 if rsi > 60 else 0) + (1 if ema9 < ema21 else 0) + (1 if macd_hist < 0 else 0)

    return {
        "price": current_price,
        "price_change": price_change,
        "rsi": rsi,
        "long_score": long_score,
        "short_score": short_score,
    }


async def predict_ticker(ticker: str, timeframe: str = "short") -> str:
    ticker = ticker.upper()
    tech = _get_technical_component(ticker, timeframe)
    if tech is None:
        return f"❌ Not enough price data for *{ticker}*."

    news = await _get_news_component(ticker)

    news_weight = max(-2, min(2, news["score"]))
    long_total = tech["long_score"] + (news_weight if news_weight > 0 else 0)
    short_total = tech["short_score"] + (-news_weight if news_weight < 0 else 0)

    if long_total > short_total + 2:
        verdict = "🚀 STRONG LONG"
    elif long_total > short_total:
        verdict = "📈 LONG"
    elif short_total > long_total + 2:
        verdict = "🔻 STRONG SHORT"
    elif short_total > long_total:
        verdict = "📉 SHORT"
    else:
        verdict = "⚖️ NEUTRAL"

    label = "Short-Term" if timeframe == "short" else "Mid-Term" if timeframe == "mid" else "Long-Term"

    lines = [
        f"🔮 *{ticker} Prediction — {label}*\n",
        f"💵 Price: `${tech['price']:,.4f}` ({'+' if tech['price_change']>0 else ''}{tech['price_change']:.2f}%)",
        f"📊 RSI: `{tech['rsi']:.0f}` | Technical: Long `{tech['long_score']}` vs Short `{tech['short_score']}`",
        f"📰 News: *{news['label']}* ({news['bull_count']} bullish / {news['bear_count']} bearish headlines)\n",
        f"*Verdict: {verdict}*",
    ]

    if news["headlines"]:
        lines.append("\n*Recent headlines:*")
        for emoji, title in news["headlines"]:
            lines.append(f"{emoji} {title}")

    lines.append("\n_⚠️ Not financial advice — combines technical indicators + news sentiment_")
    return "\n".join(lines)


async def predict_watchlist(timeframe: str = "short") -> str:
    results = []
    for ticker in CRYPTO_TICKERS:
        tech = _get_technical_component(ticker, timeframe)
        if tech is None:
            continue
        news = await _get_news_component(ticker)
        news_weight = max(-2, min(2, news["score"]))
        long_total = tech["long_score"] + (news_weight if news_weight > 0 else 0)
        short_total = tech["short_score"] + (-news_weight if news_weight < 0 else 0)
        results.append((ticker, tech["price"], long_total - short_total, tech["rsi"], news["label"]))

    results.sort(key=lambda x: x[2], reverse=True)
    label = "Short-Term" if timeframe == "short" else "Mid-Term" if timeframe == "mid" else "Long-Term"

    lines = [f"🔮 *Watchlist Prediction — {label}*\n", "*Top LONG:*"]
    for ticker, price, net, rsi, news_label in results[:5]:
        if net > 0:
            lines.append(f"🟢 *{ticker}* `${price:,.4f}` Score:+{net} RSI:{rsi:.0f} News:{news_label}")
    lines.append("\n*Top SHORT:*")
    for ticker, price, net, rsi, news_label in reversed(results[-5:]):
        if net < 0:
            lines.append(f"🔴 *{ticker}* `${price:,.4f}` Score:{net} RSI:{rsi:.0f} News:{news_label}")
    lines.append("\n_Use /predict BTC for full details_")
    return "\n".join(lines)
