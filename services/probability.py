"""
Probability calculator.
"""

import yfinance as yf
import pandas as pd
import numpy as np

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


def get_returns(ticker: str, period: str = "1y") -> pd.Series:
    yf_ticker = WATCHLIST.get(ticker.upper(), ticker.upper())
    try:
        hist = yf.Ticker(yf_ticker).history(period=period)
        if hist.empty:
            return None
        closes = hist["Close"]
        closes.index = closes.index.tz_localize(None)
        return closes.pct_change().dropna()
    except Exception:
        return None


def calculate_probability(ticker_a, ticker_b, move_pct=3.0, direction="up", lag_days=1, period="1y"):
    returns_a = get_returns(ticker_a, period)
    returns_b = get_returns(ticker_b, period)

    if returns_a is None or returns_b is None:
        return {"error": "Could not fetch data"}

    df = pd.DataFrame({"a": returns_a, "b": returns_b}).dropna()
    if len(df) < 30:
        return {"error": "Not enough data"}

    threshold = move_pct / 100
    trigger_days = df[df["a"] >= threshold].index if direction == "up" else df[df["a"] <= -threshold].index

    if len(trigger_days) == 0:
        return {"error": f"No days found where {ticker_a} moved {move_pct}%+ {direction}"}

    follow_count = 0
    total_count = 0
    b_returns_after = []

    for day in trigger_days:
        day_pos = df.index.get_loc(day)
        future_positions = range(day_pos + 1, min(day_pos + 1 + lag_days, len(df)))
        if not list(future_positions):
            continue
        future_return = df["b"].iloc[list(future_positions)].sum()
        b_returns_after.append(future_return * 100)
        total_count += 1
        if direction == "up" and future_return > 0:
            follow_count += 1
        elif direction == "down" and future_return < 0:
            follow_count += 1

    if total_count == 0:
        return {"error": "Not enough trigger events"}

    return {
        "ticker_a": ticker_a.upper(),
        "ticker_b": ticker_b.upper(),
        "move_pct": move_pct,
        "direction": direction,
        "lag_days": lag_days,
        "probability": (follow_count / total_count) * 100,
        "follow_count": follow_count,
        "total_count": total_count,
        "avg_return_b": np.mean(b_returns_after) if b_returns_after else 0,
        "max_return_b": max(b_returns_after) if b_returns_after else 0,
        "min_return_b": min(b_returns_after) if b_returns_after else 0,
        "correlation": df["a"].corr(df["b"]),
        "period": period,
    }


def format_probability(result: dict) -> str:
    if "error" in result:
        return f"❌ {result['error']}"

    a = result["ticker_a"]
    b = result["ticker_b"]
    prob = result["probability"]
    direction = result["direction"]
    move = result["move_pct"]
    lag = result["lag_days"]
    corr = result["correlation"]
    avg = result["avg_return_b"]
    total = result["total_count"]

    if prob >= 75:
        prob_emoji, prob_label = "🟢", "Very High"
    elif prob >= 60:
        prob_emoji, prob_label = "🟢", "High"
    elif prob >= 45:
        prob_emoji, prob_label = "🟡", "Moderate"
    elif prob >= 30:
        prob_emoji, prob_label = "🟠", "Low"
    else:
        prob_emoji, prob_label = "🔴", "Very Low"

    dir_emoji = "📈" if direction == "up" else "📉"
    avg_sign = "+" if avg > 0 else ""
    bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))

    lines = [
        f"🎲 *Probability Calculator*\n",
        f"*When {a} moves {dir_emoji} {direction} {move}%+,*",
        f"*does {b} follow within {lag} day(s)?*\n",
        f"{prob_emoji} *Probability: {prob:.1f}%* — {prob_label}",
        f"`{bar}`\n",
        f"📊 *Based on {total} historical events* (last {result['period']})\n",
        f"📈 *{b} average return after:* `{avg_sign}{avg:.2f}%`",
        f"🔝 Best case: `+{result['max_return_b']:.2f}%`",
        f"🔻 Worst case: `{result['min_return_b']:.2f}%`\n",
        f"🔗 *Correlation:* `{corr:.2f}`\n",
        f"💡 *What this means:*",
    ]

    if prob >= 70:
        lines.append(f"Historically when {a} goes {direction} {move}%+, {b} follows {prob:.0f}% of the time. Strong signal.")
    elif prob >= 50:
        lines.append(f"Slight tendency for {b} to follow {a}. Use with other signals.")
    else:
        lines.append(f"{b} does NOT reliably follow {a}'s {direction} moves.")

    return "\n".join(lines)


def get_full_probability_matrix(target: str, move_pct: float = 3.0) -> str:
    target = target.upper()
    others = [t for t in WATCHLIST.keys() if t != target]

    lines = [
        f"🎲 *Probability Matrix — {target}*",
        f"_When {target} moves +{move_pct}%, probability each asset follows (1 day)_\n",
    ]

    results = []
    for other in others:
        result = calculate_probability(target, other, move_pct, "up", 1, "1y")
        if "error" not in result:
            results.append((other, result["probability"], result["avg_return_b"]))

    results.sort(key=lambda x: x[1], reverse=True)

    for ticker, prob, avg in results:
        emoji = "🟢" if prob >= 70 else "🟡" if prob >= 50 else "🟠" if prob >= 30 else "🔴"
        bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))
        avg_sign = "+" if avg > 0 else ""
        lines.append(f"{emoji} *{ticker}* `{bar}` `{prob:.0f}%` avg: `{avg_sign}{avg:.1f}%`")

    lines.append(f"\n_Use /prob {target} ETH 3 up — for detailed analysis_")
    return "\n".join(lines)
