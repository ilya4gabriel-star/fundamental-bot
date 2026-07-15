"""
Long/Short signal generator.
"""

import yfinance as yf
import numpy as np

CRYPTO_TICKERS = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "XRP": "XRP-USD",
    "SOL": "SOL-USD", "BNB": "BNB-USD", "ADA": "ADA-USD",
    "DOGE": "DOGE-USD", "AVAX": "AVAX-USD", "LINK": "LINK-USD",
    "DOT": "DOT-USD", "ATOM": "ATOM-USD", "LTC": "LTC-USD",
}


def get_signal(ticker: str, timeframe: str = "short") -> str:
    ticker = ticker.upper()
    yf_ticker = CRYPTO_TICKERS.get(ticker, f"{ticker}-USD")

    if timeframe == "short":
        period, interval, label = "7d", "1h", "Short-Term (1-3 days)"
    elif timeframe == "mid":
        period, interval, label = "30d", "4h", "Mid-Term (1-2 weeks)"
    else:
        period, interval, label = "90d", "1d", "Long-Term (1-3 months)"

    try:
        hist = yf.Ticker(yf_ticker).history(period=period, interval=interval)
        if hist.empty or len(hist) < 20:
            return f"Not enough data for {ticker}."

        close = hist["Close"]
        volume = hist["Volume"]
        high = hist["High"]
        low = hist["Low"]

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
        ema50 = float(close.ewm(span=50).mean().iloc[-1])

        exp1 = close.ewm(span=12).mean()
        exp2 = close.ewm(span=26).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9).mean()
        macd_hist = float((macd - signal_line).iloc[-1])

        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        upper_band = float((sma20 + 2 * std20).iloc[-1])
        lower_band = float((sma20 - 2 * std20).iloc[-1])
        bb_position = (current_price - lower_band) / (upper_band - lower_band) * 100

        avg_vol = float(volume.rolling(20).mean().iloc[-1])
        curr_vol = float(volume.iloc[-1])
        vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1

        long_score = 0
        short_score = 0
        signals = []

        if rsi < 30:
            long_score += 3
            signals.append(("🟢", f"RSI {rsi:.0f} — heavily oversold"))
        elif rsi < 40:
            long_score += 2
            signals.append(("🟢", f"RSI {rsi:.0f} — oversold"))
        elif rsi > 70:
            short_score += 3
            signals.append(("🔴", f"RSI {rsi:.0f} — heavily overbought"))
        elif rsi > 60:
            short_score += 2
            signals.append(("🔴", f"RSI {rsi:.0f} — overbought"))
        else:
            signals.append(("⚪", f"RSI {rsi:.0f} — neutral"))

        if ema9 > ema21 > ema50:
            long_score += 2
            signals.append(("🟢", "EMA bullish alignment (9>21>50)"))
        elif ema9 < ema21 < ema50:
            short_score += 2
            signals.append(("🔴", "EMA bearish alignment (9<21<50)"))
        elif ema9 > ema21:
            long_score += 1
            signals.append(("🟡", "EMA9 > EMA21 — short-term bullish"))
        else:
            short_score += 1
            signals.append(("🟡", "EMA9 < EMA21 — short-term bearish"))

        if macd_hist > 0:
            long_score += 2
            signals.append(("🟢", f"MACD bullish ({macd_hist:.4f})"))
        else:
            short_score += 2
            signals.append(("🔴", f"MACD bearish ({macd_hist:.4f})"))

        if bb_position < 20:
            long_score += 2
            signals.append(("🟢", f"Near lower Bollinger Band ({bb_position:.0f}%)"))
        elif bb_position > 80:
            short_score += 2
            signals.append(("🔴", f"Near upper Bollinger Band ({bb_position:.0f}%)"))
        else:
            signals.append(("⚪", f"Bollinger position {bb_position:.0f}%"))

        if vol_ratio > 2.0:
            if price_change > 0:
                long_score += 2
                signals.append(("🟢", f"Volume spike {vol_ratio:.1f}x with price UP"))
            else:
                short_score += 2
                signals.append(("🔴", f"Volume spike {vol_ratio:.1f}x with price DOWN"))
        elif vol_ratio > 1.3:
            signals.append(("🟡", f"Elevated volume {vol_ratio:.1f}x"))

        long_pct = (long_score / max(long_score + short_score, 1)) * 100

        if long_score > short_score + 3:
            verdict = "🚀 STRONG LONG"
            action = f"Entry: `${current_price:,.4f}` | SL: `${current_price*0.95:,.4f}` | TP: `${current_price*1.10:,.4f}`"
        elif long_score > short_score:
            verdict = "📈 LONG"
            action = f"Entry: `${current_price:,.4f}` | SL: `${current_price*0.96:,.4f}` | TP: `${current_price*1.08:,.4f}`"
        elif short_score > long_score + 3:
            verdict = "🔻 STRONG SHORT"
            action = f"Entry: `${current_price:,.4f}` | SL: `${current_price*1.05:,.4f}` | TP: `${current_price*0.90:,.4f}`"
        elif short_score > long_score:
            verdict = "📉 SHORT"
            action = f"Entry: `${current_price:,.4f}` | SL: `${current_price*1.04:,.4f}` | TP: `${current_price*0.92:,.4f}`"
        else:
            verdict = "⚖️ NEUTRAL"
            action = "No clear signal — wait for confirmation"

        long_bar = "█" * int(long_pct/10) + "░" * (10-int(long_pct/10))
        short_bar = "█" * int((100-long_pct)/10) + "░" * (10-int((100-long_pct)/10))

        lines = [
            f"📊 *{ticker} — {label}*\n",
            f"💵 Price: `${current_price:,.4f}` ({'+' if price_change>0 else ''}{price_change:.2f}%)\n",
            f"*Verdict: {verdict}*",
            f"🟢 LONG  `{long_bar}` {long_pct:.0f}%",
            f"🔴 SHORT `{short_bar}` {100-long_pct:.0f}%",
            f"Score: Long `{long_score}` vs Short `{short_score}`\n",
            "*Indicators:*",
        ]
        for emoji, text in signals:
            lines.append(f"{emoji} {text}")
        lines.append(f"\n*Action:* {action}")
        lines.append("_⚠️ Not financial advice_")
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error: {e}"


def scan_all_signals(timeframe: str = "short") -> str:
    results = []
    for ticker, yf_ticker in CRYPTO_TICKERS.items():
        try:
            period = "7d" if timeframe == "short" else "30d" if timeframe == "mid" else "90d"
            interval = "1h" if timeframe == "short" else "4h" if timeframe == "mid" else "1d"
            hist = yf.Ticker(yf_ticker).history(period=period, interval=interval)
            if hist.empty or len(hist) < 20:
                continue
            close = hist["Close"]
            current_price = float(close.iloc[-1])
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = -delta.clip(upper=0).rolling(14).mean()
            rs = gain / loss
            rsi = float((100 - (100 / (1 + rs))).iloc[-1])
            ema9 = float(close.ewm(span=9).mean().iloc[-1])
            ema21 = float(close.ewm(span=21).mean().iloc[-1])
            exp1 = close.ewm(span=12).mean()
            exp2 = close.ewm(span=26).mean()
            macd_hist = float((exp1 - exp2 - (exp1-exp2).ewm(span=9).mean()).iloc[-1])
            long_score = (2 if rsi < 40 else 0) + (1 if ema9 > ema21 else 0) + (1 if macd_hist > 0 else 0)
            short_score = (2 if rsi > 60 else 0) + (1 if ema9 < ema21 else 0) + (1 if macd_hist < 0 else 0)
            results.append((ticker, current_price, long_score - short_score, rsi))
        except Exception:
            pass

    results.sort(key=lambda x: x[2], reverse=True)
    label = "Short-Term" if timeframe == "short" else "Mid-Term" if timeframe == "mid" else "Long-Term"
    lines = [f"🔍 *Crypto Scan — {label}*\n", "*Top LONG:*"]
    for ticker, price, net, rsi in results[:5]:
        if net > 0:
            lines.append(f"🟢 *{ticker}* `${price:,.4f}` Score:+{net} RSI:{rsi:.0f}")
    lines.append("\n*Top SHORT:*")
    for ticker, price, net, rsi in reversed(results[-5:]):
        if net < 0:
            lines.append(f"🔴 *{ticker}* `${price:,.4f}` Score:{net} RSI:{rsi:.0f}")
    lines.append("\n_Use /signal BTC short for details_")
    return "\n".join(lines)
