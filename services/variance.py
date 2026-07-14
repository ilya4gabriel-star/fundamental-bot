"""
Variance and volatility calculator.
"""

import yfinance as yf
import numpy as np
import pandas as pd


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


def calculate_variance(ticker: str, period: str = "30d") -> str:
    """Calculate variance and volatility metrics for an asset."""
    yf_ticker = WATCHLIST.get(ticker.upper(), ticker.upper())

    try:
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period=period)

        if hist.empty or len(hist) < 5:
            return f"❌ Not enough data for *{ticker}*."

        close = hist["Close"]
        returns = close.pct_change().dropna()

        # Core stats
        current_price = float(close.iloc[-1])
        mean_return = float(returns.mean()) * 100
        variance = float(returns.var()) * 100
        std_dev = float(returns.std()) * 100
        daily_vol = std_dev

        # Annualized volatility
        annual_vol = daily_vol * np.sqrt(252)

        # Price range
        period_high = float(close.max())
        period_low = float(close.min())
        price_range = ((period_high - period_low) / period_low) * 100

        # Confidence intervals (68%, 95%, 99%)
        z_68 = 1.0
        z_95 = 1.96
        z_99 = 2.58

        days_ahead = 7
        vol_7d = daily_vol * np.sqrt(days_ahead)

        low_68 = current_price * (1 - z_68 * vol_7d / 100)
        high_68 = current_price * (1 + z_68 * vol_7d / 100)
        low_95 = current_price * (1 - z_95 * vol_7d / 100)
        high_95 = current_price * (1 + z_95 * vol_7d / 100)
        low_99 = current_price * (1 - z_99 * vol_7d / 100)
        high_99 = current_price * (1 + z_99 * vol_7d / 100)

        # Sharpe-like ratio (return / risk)
        sharpe = mean_return / std_dev if std_dev > 0 else 0

        # Max drawdown
        rolling_max = close.cummax()
        drawdown = ((close - rolling_max) / rolling_max) * 100
        max_drawdown = float(drawdown.min())

        # Volatility regime
        if annual_vol < 20:
            vol_regime = "🟢 Low volatility"
            vol_note = "Stable asset — good for conservative positions"
        elif annual_vol < 40:
            vol_regime = "🟡 Moderate volatility"
            vol_note = "Normal trading range — manageable risk"
        elif annual_vol < 80:
            vol_regime = "🟠 High volatility"
            vol_note = "Use smaller position sizes"
        else:
            vol_regime = "🔴 Extreme volatility"
            vol_note = "Very risky — only small speculative positions"

        # Best and worst days
        best_day = float(returns.max()) * 100
        worst_day = float(returns.min()) * 100

        lines = [
            f"📐 *Variance Calculator — {ticker.upper()}*",
            f"_Period: {period} · {len(returns)} trading days_\n",

            f"💵 Current Price: `${current_price:,.2f}`\n",

            f"📊 *Volatility Metrics*",
            f"Daily Volatility: `{daily_vol:.2f}%`",
            f"Annual Volatility: `{annual_vol:.1f}%`",
            f"Variance: `{variance:.4f}`",
            f"Std Deviation: `{std_dev:.2f}%`\n",

            f"🎯 *Volatility Regime*",
            f"{vol_regime}",
            f"_{vol_note}_\n",

            f"📈 *Price Statistics*",
            f"Mean Daily Return: `{mean_return:+.3f}%`",
            f"Best Day: `+{best_day:.2f}%`",
            f"Worst Day: `{worst_day:.2f}%`",
            f"Max Drawdown: `{max_drawdown:.2f}%`",
            f"Period Range: `{price_range:.1f}%` (${period_low:,.2f} — ${period_high:,.2f})\n",

            f"🔮 *7-Day Price Forecast Range*",
            f"68% probability: `${low_68:,.2f}` — `${high_68:,.2f}`",
            f"95% probability: `${low_95:,.2f}` — `${high_95:,.2f}`",
            f"99% probability: `${low_99:,.2f}` — `${high_99:,.2f}`\n",

            f"⚖️ *Risk/Return*",
            f"Sharpe Ratio: `{sharpe:.2f}`",
        ]

        if sharpe > 0.5:
            lines.append("_Good risk-adjusted return ✅_")
        elif sharpe > 0:
            lines.append("_Positive but weak risk-adjusted return 🟡_")
        else:
            lines.append("_Negative risk-adjusted return 🔴_")

        lines.append(f"\n_Use /variance {ticker} 90d for longer period_")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error calculating variance for *{ticker}*: {e}"


def compare_variance(tickers: list, period: str = "30d") -> str:
    """Compare volatility across multiple assets."""
    results = []

    for ticker in tickers:
        yf_ticker = WATCHLIST.get(ticker.upper(), ticker.upper())
        try:
            hist = yf.Ticker(yf_ticker).history(period=period)
            if hist.empty:
                continue
            returns = hist["Close"].pct_change().dropna()
            daily_vol = float(returns.std()) * 100
            annual_vol = daily_vol * np.sqrt(252)
            mean_ret = float(returns.mean()) * 100
            sharpe = mean_ret / daily_vol if daily_vol > 0 else 0
            results.append((ticker.upper(), daily_vol, annual_vol, sharpe))
        except Exception:
            pass

    if not results:
        return "❌ Could not fetch data."

    results.sort(key=lambda x: x[2])

    lines = [f"📐 *Volatility Comparison* (last {period})\n"]

    for ticker, daily, annual, sharpe in results:
        if annual < 20:
            emoji = "🟢"
        elif annual < 40:
            emoji = "🟡"
        elif annual < 80:
            emoji = "🟠"
        else:
            emoji = "🔴"

        lines.append(
            f"{emoji} *{ticker}* — Daily: `{daily:.2f}%` | Annual: `{annual:.1f}%` | Sharpe: `{sharpe:.2f}`"
        )

    lines.append("\n_Sorted by volatility (low → high)_")
    return "\n".join(lines)
