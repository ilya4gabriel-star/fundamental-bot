"""
Fundamental analysis service.
"""

import yfinance as yf


def fmt_pct(v):
    if v is None:
        return "N/A"
    sign = "+" if v > 0 else ""
    return f"{sign}{v*100:.1f}%"


def fmt_num(v):
    if not v:
        return "N/A"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"


def get_fundamentals(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        name = info.get("longName", ticker)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        current = info.get("currentPrice") or info.get("regularMarketPrice")

        # Valuation
        market_cap = info.get("marketCap")
        pe = info.get("trailingPE")
        fpe = info.get("forwardPE")
        eps = info.get("trailingEps")
        pb = info.get("priceToBook")
        ps = info.get("priceToSalesTrailing12Months")
        peg = info.get("pegRatio")

        # Profitability
        revenue = info.get("totalRevenue")
        revenue_growth = info.get("revenueGrowth")
        earnings_growth = info.get("earningsGrowth")
        profit_margin = info.get("profitMargins")
        gross_margin = info.get("grossMargins")
        operating_margin = info.get("operatingMargins")
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        ebitda = info.get("ebitda")

        # Risk & Health
        debt_equity = info.get("debtToEquity")
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")
        beta = info.get("beta")
        short_ratio = info.get("shortRatio")

        # Dividends
        div_yield = info.get("dividendYield")
        payout_ratio = info.get("payoutRatio")

        # Analyst
        target = info.get("targetMeanPrice")
        recommendation = info.get("recommendationKey", "N/A").upper()

        # P/E verdict
        if pe:
            if pe < 15:
                pe_note = "🟢 Cheap"
            elif pe < 25:
                pe_note = "🟡 Fair"
            elif pe < 35:
                pe_note = "🟠 Premium"
            else:
                pe_note = "🔴 Expensive"
        else:
            pe_note = ""

        # ROE verdict
        if roe:
            if roe > 0.2:
                roe_note = "🟢"
            elif roe > 0.1:
                roe_note = "🟡"
            else:
                roe_note = "🔴"
        else:
            roe_note = ""

        lines = [
            f"📊 *{name} ({ticker.upper()})*",
            f"🏭 {sector} — {industry}",
            f"💵 Current Price: `{f'${current:.2f}' if current else 'N/A'}`\n",

            f"💰 *Valuation*",
            f"Market Cap: `{fmt_num(market_cap)}`",
            f"P/E Ratio: `{f'{pe:.1f}' if pe else 'N/A'}` {pe_note}",
            f"Forward P/E: `{f'{fpe:.1f}' if fpe else 'N/A'}`",
            f"EPS: `{f'${eps:.2f}' if eps else 'N/A'}`",
            f"Price/Book: `{f'{pb:.1f}' if pb else 'N/A'}`",
            f"Price/Sales: `{f'{ps:.1f}' if ps else 'N/A'}`",
            f"PEG Ratio: `{f'{peg:.1f}' if peg else 'N/A'}`\n",

            f"📈 *Profitability*",
            f"Revenue: `{fmt_num(revenue)}`",
            f"Revenue Growth: `{fmt_pct(revenue_growth)}`",
            f"Earnings Growth: `{fmt_pct(earnings_growth)}`",
            f"Gross Margin: `{fmt_pct(gross_margin)}`",
            f"Operating Margin: `{fmt_pct(operating_margin)}`",
            f"Profit Margin: `{fmt_pct(profit_margin)}`",
            f"EBITDA: `{fmt_num(ebitda)}`",
            f"ROE: `{fmt_pct(roe)}` {roe_note}",
            f"ROA: `{fmt_pct(roa)}`\n",

            f"⚖️ *Financial Health*",
            f"Debt/Equity: `{f'{debt_equity:.1f}' if debt_equity else 'N/A'}`",
            f"Current Ratio: `{f'{current_ratio:.2f}' if current_ratio else 'N/A'}`",
            f"Quick Ratio: `{f'{quick_ratio:.2f}' if quick_ratio else 'N/A'}`",
            f"Beta: `{f'{beta:.2f}' if beta else 'N/A'}`",
            f"Short Ratio: `{f'{short_ratio:.1f}' if short_ratio else 'N/A'}`\n",

            f"💸 *Dividends*",
            f"Dividend Yield: `{fmt_pct(div_yield)}`",
            f"Payout Ratio: `{fmt_pct(payout_ratio)}`\n",

            f"🎯 *Analyst Consensus*",
            f"Recommendation: `{recommendation}`",
        ]

        if target and current:
            upside = ((target - current) / current) * 100
            sign = "+" if upside > 0 else ""
            lines.append(f"Price Target: `${target:.2f}` ({sign}{upside:.1f}% upside)")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Could not fetch fundamentals for *{ticker}*. Check the ticker.\n_{e}_"


def get_valuation(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        name = info.get("longName", ticker)
        pe = info.get("trailingPE")
        fpe = info.get("forwardPE")
        pb = info.get("priceToBook")
        ps = info.get("priceToSalesTrailing12Months")
        peg = info.get("pegRatio")
        target = info.get("targetMeanPrice")
        current = info.get("currentPrice") or info.get("regularMarketPrice")

        lines = [f"💎 *Valuation — {name} ({ticker.upper()})*\n"]

        if pe:
            if pe < 10:
                verdict = "🟢 Very cheap"
                explain = "P/E below 10 — deeply undervalued or troubled"
            elif pe < 20:
                verdict = "🟢 Reasonable"
                explain = "P/E 10-20 — fair for most industries"
            elif pe < 35:
                verdict = "🟡 Premium"
                explain = "P/E 20-35 — priced for growth"
            else:
                verdict = "🔴 Expensive"
                explain = "P/E above 35 — high expectations priced in"
            lines.append(f"P/E Ratio: `{pe:.1f}` — {verdict}\n_{explain}_\n")

        if fpe:
            lines.append(f"Forward P/E: `{fpe:.1f}`")
            if pe and fpe < pe:
                lines.append("_Earnings expected to grow ✅_\n")
            elif pe and fpe > pe:
                lines.append("_Earnings expected to shrink ⚠️_\n")

        if pb:
            lines.append(f"Price/Book: `{pb:.1f}`")
            if pb < 1:
                lines.append("_Trading below book value — potential bargain_\n")
            elif pb > 5:
                lines.append("_High premium to book value_\n")

        if ps:
            lines.append(f"Price/Sales: `{ps:.1f}`")

        if peg:
            lines.append(f"PEG Ratio: `{peg:.1f}`")
            if peg < 1:
                lines.append("_PEG < 1 — undervalued relative to growth ✅_\n")

        if target and current:
            upside = ((target - current) / current) * 100
            sign = "+" if upside > 0 else ""
            lines.append(f"\n🎯 Analyst target: `${target:.2f}`")
            lines.append(f"Current price: `${current:.2f}`")
            lines.append(f"Upside: `{sign}{upside:.1f}%`")

        return "\n".join(lines)
    except Exception:
        return f"❌ Could not fetch valuation for *{ticker}*."


def get_earnings(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        name = info.get("longName", ticker)
        eps = info.get("trailingEps")
        eps_fwd = info.get("forwardEps")
        revenue = info.get("totalRevenue")
        earnings_growth = info.get("earningsGrowth")
        revenue_growth = info.get("revenueGrowth")
        next_earnings = info.get("mostRecentQuarter")

        lines = [
            f"📋 *Earnings Report — {name} ({ticker.upper()})*\n",
            f"💵 Revenue: `{fmt_num(revenue)}`",
            f"📈 Revenue Growth: `{fmt_pct(revenue_growth)}`",
            f"💰 EPS (TTM): `{f'${eps:.2f}' if eps else 'N/A'}`",
            f"🔮 Forward EPS: `{f'${eps_fwd:.2f}' if eps_fwd else 'N/A'}`",
            f"📊 Earnings Growth: `{fmt_pct(earnings_growth)}`",
        ]

        if next_earnings:
            lines.append(f"\n🗓 Last quarter: `{next_earnings}`")

        lines.append("\n💡 *What this means:*")
        if earnings_growth and earnings_growth > 0.2:
            lines.append("✅ Strong earnings growth — company expanding fast")
        elif earnings_growth and earnings_growth > 0:
            lines.append("🟡 Moderate growth — stable business")
        elif earnings_growth:
            lines.append("🔴 Earnings declining — investigate why")

        return "\n".join(lines)
    except Exception:
        return f"❌ Could not fetch earnings for *{ticker}*."
