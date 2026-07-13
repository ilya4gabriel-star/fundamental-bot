"""
Correlation matrix service.
Shows which assets move together.
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
    "SPY": "SPY",
    "QQQ": "QQQ",
    "GLD": "GLD",
}


def get_returns(tickers: list, period: str = "30d") -> pd.DataFrame:
    """Download price data and calculate daily returns."""
    data = {}
    for name, ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if not hist.empty:
                closes = hist["Close"]
                closes.index = closes.index.tz_localize(None)
                data[name] = closes.pct_change().dropna()
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df.dropna()
    return df


def interpret_correlation(corr: float) -> tuple:
    """Returns (emoji, label) for a correlation value."""
    if corr >= 0.8:
        return "🟢", "Very strong"
    elif corr >= 0.6:
        return "🟢", "Strong"
    elif corr >= 0.4:
        return "🟡", "Moderate"
    elif corr >= 0.2:
        return "🟡", "Weak"
    elif corr >= -0.2:
        return "⚪", "No correlation"
    elif corr >= -0.5:
        return "🔴", "Weak negative"
    else:
        return "🔴", "Strong negative"


def get_correlation_with(target: str, period: str = "30d") -> str:
    """Get correlation of one asset with all others."""
    target = target.upper()

    if target not in WATCHLIST:
        return f"❌ *{target}* not in watchlist.\n\nAvailable: {', '.join(WATCHLIST.keys())}"

    tickers = list(WATCHLIST.items())
    df = get_returns(tickers, period)

    if df.empty or target not in df.columns:
        return f"❌ Could not fetch data for *{target}*."

    correlations = df.corr()[target].drop(target).sort_values(ascending=False)

    lines = [
        f"🔗 *Correlation with {target}* (last {period})\n",
        f"_How much other assets move with {target}_\n",
    ]

    for asset, corr in correlations.items():
        emoji, label = interpret_correlation(corr)
        bar_filled = int(abs(corr) * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        sign = "+" if corr >= 0 else ""
        lines.append(f"{emoji} *{asset}* `{bar}` `{sign}{corr:.2f}` — {label}")

    lines.append(f"\n💡 *How to use this:*")
    lines.append(f"• Correlation > 0.8 = assets move almost together")
    lines.append(f"• Correlation ~0 = assets move independently")
    lines.append(f"• Correlation < -0.5 = assets move opposite")
    lines.append(f"\n_Use /correlate <ticker> to check any asset_")

    return "\n".join(lines)


def get_full_matrix(period: str = "30d") -> str:
    """Get full correlation matrix for all watchlist assets."""
    tickers = list(WATCHLIST.items())
    df = get_returns(tickers, period)

    if df.empty:
        return "❌ Could not fetch data for correlation matrix."

    corr_matrix = df.corr()

    lines = [f"📊 *Full Correlation Matrix* (last {period})\n"]

    # Group assets by correlation clusters
    crypto = ["BTC", "ETH", "XRP", "SOL", "BNB"]
    stocks = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "META"]
    indices = ["SPY", "QQQ", "GLD"]

    groups = [("🪙 Crypto", crypto), ("📈 Stocks", stocks), ("📊 Indices", indices)]

    for group_name, group_tickers in groups:
        lines.append(f"*{group_name}:*")
        available = [t for t in group_tickers if t in corr_matrix.columns]

        for ticker in available:
            others = [t for t in available if t != ticker]
            avg_corr = corr_matrix.loc[ticker, others].mean() if others else 0
            emoji, label = interpret_correlation(avg_corr)
            lines.append(f"{emoji} *{ticker}* avg correlation with group: `{avg_corr:.2f}`")

        lines.append("")

    # Find most and least correlated pairs
    pairs = []
    assets = list(corr_matrix.columns)
    for i in range(len(assets)):
        for j in range(i+1, len(assets)):
            pairs.append((assets[i], assets[j], corr_matrix.loc[assets[i], assets[j]]))

    pairs.sort(key=lambda x: x[2], reverse=True)

    lines.append("🔝 *Most correlated pairs:*")
    for a, b, c in pairs[:3]:
        lines.append(f"• {a} & {b}: `{c:.2f}`")

    lines.append("\n🔻 *Least correlated pairs:*")
    for a, b, c in sorted(pairs, key=lambda x: x[2])[:3]:
        lines.append(f"• {a} & {b}: `{c:.2f}`")

    lines.append("\n_Use /correlate <ticker> for detailed view_")

    return "\n".join(lines)
