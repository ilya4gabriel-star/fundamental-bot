"""
AI-powered top picks service.
Claude analyzes all assets and picks the best opportunities.
"""

import aiohttp
import json
import os
from dotenv import load_dotenv
import yfinance as yf

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

WATCHLIST = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "XRP": "XRP-USD",
    "SOL": "SOL-USD",
    "BNB": "BNB-USD",
    "AAPL": "AAPL",
    "TSLA": "TSLA",
    "NVDA": "NVDA",
    "MSFT": "MSFT",
    "AMZN": "AMZN",
    "META": "META",
    "GOOGL": "GOOGL",
    "SPY": "SPY",
    "QQQ": "QQQ",
    "GLD": "GLD",
}


def get_quick_data(ticker: str, yf_ticker: str) -> dict:
    """Get key metrics for one asset quickly."""
    try:
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        hist = stock.history(period="30d")

        if hist.empty:
            return None

        close = hist["Close"]
        current = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        week_ago = float(close.iloc[-5]) if len(close) >= 5 else prev
        month_ago = float(close.iloc[0])

        change_1d = ((current - prev) / prev) * 100
        change_7d = ((current - week_ago) / week_ago) * 100
        change_30d = ((current - month_ago) / month_ago) * 100

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        # Volume ratio
        avg_vol = hist["Volume"].iloc[:-1].mean()
        curr_vol = hist["Volume"].iloc[-1]
        vol_ratio = float(curr_vol / avg_vol) if avg_vol > 0 else 1.0

        # EMA trend
        ema20 = float(close.ewm(span=20).mean().iloc[-1])
        ema50 = float(close.ewm(span=50).mean().iloc[-1])
        trend = "UP" if ema20 > ema50 else "DOWN"

        return {
            "ticker": ticker,
            "price": round(current, 2),
            "change_1d": round(change_1d, 2),
            "change_7d": round(change_7d, 2),
            "change_30d": round(change_30d, 2),
            "rsi": round(rsi, 1),
            "volume_ratio": round(vol_ratio, 2),
            "trend": trend,
            "pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps_growth": info.get("earningsGrowth"),
            "beta": info.get("beta"),
            "analyst_target": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey", "N/A"),
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


async def get_ai_picks(timeframe: str = "all") -> str:
    """Get AI-powered top picks for specified timeframe."""
    if not ANTHROPIC_API_KEY:
        return "❌ ANTHROPIC_API_KEY not found in .env file."

    # Collect data for all assets
    all_data = []
    for ticker, yf_ticker in WATCHLIST.items():
        data = get_quick_data(ticker, yf_ticker)
        if data:
            all_data.append(data)

    if not all_data:
        return "❌ Could not fetch market data."

    # Build data summary for Claude
    lines = []
    for d in all_data:
        pe_str = f"PE={d['pe']:.1f}" if d['pe'] else "PE=N/A"
        target_str = f"Target=${d['analyst_target']:.2f}" if d['analyst_target'] else "Target=N/A"
        eps_str = f"EPSgrowth={d['eps_growth']*100:.1f}%" if d['eps_growth'] else "EPSgrowth=N/A"
        lines.append(
            f"{d['ticker']}: Price=${d['price']} | "
            f"1d={d['change_1d']:+.1f}% | "
            f"7d={d['change_7d']:+.1f}% | "
            f"30d={d['change_30d']:+.1f}% | "
            f"RSI={d['rsi']} | "
            f"Vol={d['volume_ratio']}x | "
            f"Trend={d['trend']} | "
            f"{pe_str} | {eps_str} | "
            f"Beta={d['beta'] or 'N/A'} | "
            f"{target_str} | "
            f"Analyst={d['recommendation'].upper()}"
        )

    market_data = "\n".join(lines)

    if timeframe == "short":
        timeframe_prompt = """Focus ONLY on SHORT-TERM picks (1-5 days).
Look for: oversold RSI (<35), high volume spikes (>1.5x), strong momentum, recent price bounces.
Ignore long-term fundamentals — focus on technical setups."""
        title = "⚡ Short-Term Picks (1–5 days)"

    elif timeframe == "mid":
        timeframe_prompt = """Focus ONLY on MID-TERM picks (2-8 weeks).
Look for: recovering trend (EMA crossovers), reasonable RSI (30-60), improving fundamentals, analyst upgrades.
Balance between technical momentum and fundamental value."""
        title = "📅 Mid-Term Picks (2–8 weeks)"

    elif timeframe == "long":
        timeframe_prompt = """Focus ONLY on LONG-TERM picks (3-12 months).
Look for: strong fundamentals (earnings growth, low PE relative to growth, high ROE), analyst price targets with large upside, low beta for stability or high growth potential.
Ignore short-term price noise — focus on business quality."""
        title = "🏆 Long-Term Picks (3–12 months)"

    else:
        timeframe_prompt = """Give picks for ALL THREE timeframes:
- SHORT (1-5 days): technical setups, momentum, oversold bounces
- MID (2-8 weeks): trend recovery, improving fundamentals
- LONG (3-12 months): strong business quality, analyst upside, growth"""
        title = "🎯 Top Picks — All Timeframes"

    prompt = f"""You are a professional trading analyst. Analyze this real market data and give your top picks.

MARKET DATA (today):
{market_data}

TASK: {timeframe_prompt}

For each pick provide:
1. Ticker and current price
2. Why it's a good pick for this timeframe (2-3 specific reasons using the data)
3. Key risk to watch
4. Entry suggestion (buy now / wait for dip to X / wait for confirmation)

Give 3-5 picks. Be specific, direct, and use the actual numbers from the data.
Format each pick clearly with the ticker name as a header.
End with a brief market overview sentence."""

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
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=aiohttp.ClientTimeout(total=45),
            ) as r:
                if r.status == 200:
                    result = await r.json()
                    analysis = result["content"][0]["text"]

                    return (
                        f"🤖 *{title}*\n\n"
                        f"{analysis}\n\n"
                        f"⚠️ _This is AI analysis for educational purposes only — not financial advice_\n"
                        f"_Powered by Claude AI · Live market data_"
                    )
                else:
                    error = await r.text()
                    return f"❌ Claude API error: {r.status}"

    except Exception as e:
        return f"❌ Error: {e}"
