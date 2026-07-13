"""
AI-powered analysis summary using Claude API.
"""

import aiohttp
import json
import os
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def get_stock_data(ticker: str) -> dict:
    """Gather all available data for a ticker."""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        hist = stock.history(period="30d")

        # Price data
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose")
        price_change = ((current_price - prev_close) / prev_close * 100) if current_price and prev_close else None

        # Volume
        avg_volume = info.get("averageVolume")
        current_volume = info.get("regularMarketVolume")
        volume_ratio = (current_volume / avg_volume) if current_volume and avg_volume else None

        # Fundamentals
        pe = info.get("trailingPE")
        fpe = info.get("forwardPE")
        eps_growth = info.get("earningsGrowth")
        revenue_growth = info.get("revenueGrowth")
        profit_margin = info.get("profitMargins")
        roe = info.get("returnOnEquity")
        debt_equity = info.get("debtToEquity")
        beta = info.get("beta")

        # Technical — RSI
        if not hist.empty:
            close = hist["Close"]
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = -delta.clip(upper=0).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = round(float(rsi.iloc[-1]), 1)
        else:
            rsi_val = None

        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "price": current_price,
            "price_change_pct": price_change,
            "volume_ratio": volume_ratio,
            "pe": pe,
            "forward_pe": fpe,
            "eps_growth": eps_growth,
            "revenue_growth": revenue_growth,
            "profit_margin": profit_margin,
            "roe": roe,
            "debt_equity": debt_equity,
            "beta": beta,
            "rsi": rsi_val,
            "analyst_target": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey", "N/A"),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


async def get_ai_summary(ticker: str) -> str:
    """Get Claude AI analysis of an asset."""
    if not ANTHROPIC_API_KEY:
        return "❌ ANTHROPIC_API_KEY not found in .env file."

    data = get_stock_data(ticker)

    if "error" in data:
        return f"❌ Could not fetch data for *{ticker}*."

    # Build context for Claude
    def fmt(v, suffix="", prefix="", decimals=2):
        if v is None:
            return "N/A"
        return f"{prefix}{v:.{decimals}f}{suffix}"

    context = f"""
Asset: {data['name']} ({data['ticker']})
Sector: {data['sector']}
Current Price: {fmt(data['price'], prefix='$')}
Price Change Today: {fmt(data['price_change_pct'], suffix='%')}
Volume vs Average: {fmt(data['volume_ratio'], suffix='x')}

FUNDAMENTALS:
P/E Ratio: {fmt(data['pe'], decimals=1)}
Forward P/E: {fmt(data['forward_pe'], decimals=1)}
EPS Growth: {fmt(data['eps_growth'] * 100 if data['eps_growth'] else None, suffix='%', decimals=1)}
Revenue Growth: {fmt(data['revenue_growth'] * 100 if data['revenue_growth'] else None, suffix='%', decimals=1)}
Profit Margin: {fmt(data['profit_margin'] * 100 if data['profit_margin'] else None, suffix='%', decimals=1)}
ROE: {fmt(data['roe'] * 100 if data['roe'] else None, suffix='%', decimals=1)}
Debt/Equity: {fmt(data['debt_equity'], decimals=1)}
Beta: {fmt(data['beta'])}

TECHNICAL:
RSI (14): {fmt(data['rsi'], decimals=1)}

ANALYST CONSENSUS:
Price Target: {fmt(data['analyst_target'], prefix='$')}
Recommendation: {data['recommendation'].upper()}
"""

    prompt = f"""You are a professional financial analyst. Analyze the following data for {data['ticker']} and provide a clear, concise summary in plain English.

{context}

Write a 4-5 sentence analysis covering:
1. Current situation (price action, volume)
2. Fundamental health (valuation, growth, profitability)
3. Technical signal (RSI overbought/oversold)
4. Overall verdict — is this a BUY, HOLD, or AVOID right now and why?

Be direct and specific. Use simple language. No jargon. End with a clear one-line verdict."""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as r:
                if r.status == 200:
                    result = await r.json()
                    analysis = result["content"][0]["text"]

                    return (
                        f"🤖 *AI Analysis — {data['ticker']}*\n\n"
                        f"{analysis}\n\n"
                        f"_Powered by Claude AI · Data from Yahoo Finance_"
                    )
                else:
                    error = await r.text()
                    return f"❌ Claude API error: {r.status}\n_{error[:200]}_"

    except Exception as e:
        return f"❌ Error calling Claude API: {e}"
