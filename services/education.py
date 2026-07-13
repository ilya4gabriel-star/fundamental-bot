"""
Education service — explains fundamental analysis concepts.
"""

GLOSSARY = {
    "p/e": {
        "title": "P/E Ratio (Price-to-Earnings)",
        "text": (
            "📚 *P/E Ratio — Price to Earnings*\n\n"
            "The P/E ratio tells you how much investors pay for $1 of company earnings.\n\n"
            "*Formula:* `P/E = Stock Price ÷ EPS`\n\n"
            "*How to read it:*\n"
            "• P/E < 15 — 🟢 Potentially undervalued\n"
            "• P/E 15-25 — 🟡 Fair value for most companies\n"
            "• P/E > 35 — 🔴 High expectations priced in\n\n"
            "*Example:*\n"
            "Stock price = $100, EPS = $5\n"
            "P/E = 100 ÷ 5 = *20x*\n"
            "You're paying $20 for every $1 of earnings.\n\n"
            "⚠️ *Important:* Compare P/E within the same industry — tech companies naturally have higher P/E than banks."
        )
    },
    "eps": {
        "title": "EPS (Earnings Per Share)",
        "text": (
            "📚 *EPS — Earnings Per Share*\n\n"
            "EPS shows how much profit a company makes per share of stock.\n\n"
            "*Formula:* `EPS = Net Income ÷ Shares Outstanding`\n\n"
            "*How to read it:*\n"
            "• Higher EPS = more profitable per share\n"
            "• Growing EPS = company expanding profits\n"
            "• Declining EPS = shrinking profitability ⚠️\n\n"
            "*Example:*\n"
            "Net income = $10B, Shares = 1B\n"
            "EPS = 10B ÷ 1B = *$10 per share*\n\n"
            "💡 Always compare EPS to previous quarters to spot trends."
        )
    },
    "roe": {
        "title": "ROE (Return on Equity)",
        "text": (
            "📚 *ROE — Return on Equity*\n\n"
            "ROE measures how efficiently a company uses shareholder money to generate profit.\n\n"
            "*Formula:* `ROE = Net Income ÷ Shareholders Equity`\n\n"
            "*How to read it:*\n"
            "• ROE > 20% — 🟢 Excellent\n"
            "• ROE 10-20% — 🟡 Good\n"
            "• ROE < 10% — 🔴 Poor use of capital\n\n"
            "*Example:*\n"
            "Apple ROE is ~150% — extremely efficient.\n"
            "Banks average ~10%.\n\n"
            "⚠️ High debt can artificially inflate ROE — always check debt levels too."
        )
    },
    "dcf": {
        "title": "DCF (Discounted Cash Flow)",
        "text": (
            "📚 *DCF — Discounted Cash Flow*\n\n"
            "DCF is a valuation method that estimates a company's value based on its future cash flows.\n\n"
            "*Core idea:* $100 today is worth more than $100 in 5 years due to inflation and risk.\n\n"
            "*Steps:*\n"
            "1. Estimate future cash flows (5-10 years)\n"
            "2. Apply a discount rate (usually 8-12%)\n"
            "3. Calculate present value of all future cash\n"
            "4. Compare to current market cap\n\n"
            "*If DCF value > Market Cap* — 🟢 potentially undervalued\n"
            "*If DCF value < Market Cap* — 🔴 potentially overvalued\n\n"
            "⚠️ DCF is very sensitive to assumptions — small changes in growth rate drastically change the result."
        )
    },
    "market cap": {
        "title": "Market Capitalization",
        "text": (
            "📚 *Market Cap — Market Capitalization*\n\n"
            "Market cap is the total value of all a company's shares.\n\n"
            "*Formula:* `Market Cap = Stock Price × Total Shares`\n\n"
            "*Categories:*\n"
            "• Mega cap: > $200B (Apple, Microsoft)\n"
            "• Large cap: $10B-$200B\n"
            "• Mid cap: $2B-$10B\n"
            "• Small cap: $300M-$2B\n"
            "• Micro cap: < $300M\n\n"
            "*Example:*\n"
            "Apple price = $200, Shares = 15B\n"
            "Market Cap = $200 × 15B = *$3 Trillion*\n\n"
            "💡 Market cap ≠ company value. Use it alongside P/E, DCF for full picture."
        )
    },
    "peg": {
        "title": "PEG Ratio",
        "text": (
            "📚 *PEG Ratio — Price/Earnings to Growth*\n\n"
            "PEG improves on P/E by factoring in earnings growth rate.\n\n"
            "*Formula:* `PEG = P/E ÷ Annual EPS Growth Rate`\n\n"
            "*How to read it:*\n"
            "• PEG < 1 — 🟢 Undervalued relative to growth\n"
            "• PEG = 1 — 🟡 Fairly valued\n"
            "• PEG > 2 — 🔴 Overvalued\n\n"
            "*Example:*\n"
            "P/E = 30, Growth = 30%\n"
            "PEG = 30 ÷ 30 = *1.0* — fairly valued\n\n"
            "💡 PEG is especially useful for growth stocks where high P/E alone looks scary."
        )
    },
    "beta": {
        "title": "Beta",
        "text": (
            "📚 *Beta — Market Sensitivity*\n\n"
            "Beta measures how much a stock moves relative to the overall market (S&P 500).\n\n"
            "*How to read it:*\n"
            "• Beta = 1 — moves exactly with market\n"
            "• Beta > 1 — more volatile than market (e.g. 1.5 = 50% more volatile)\n"
            "• Beta < 1 — less volatile (defensive stocks)\n"
            "• Beta < 0 — moves opposite to market (rare)\n\n"
            "*Examples:*\n"
            "• Tesla Beta ~2.0 — very volatile\n"
            "• Coca-Cola Beta ~0.6 — stable\n"
            "• Gold ETF Beta ~0.1 — almost no correlation\n\n"
            "💡 High beta = higher risk AND higher potential return."
        )
    },
    "dividend": {
        "title": "Dividend Yield",
        "text": (
            "📚 *Dividend Yield*\n\n"
            "Dividend yield shows how much a company pays in dividends relative to its stock price.\n\n"
            "*Formula:* `Yield = Annual Dividend ÷ Stock Price × 100`\n\n"
            "*How to read it:*\n"
            "• 0% — growth company, reinvests all profits\n"
            "• 1-3% — 🟡 moderate income\n"
            "• 4-6% — 🟢 solid income stock\n"
            "• >7% — ⚠️ check if sustainable\n\n"
            "*Example:*\n"
            "Stock = $100, Annual dividend = $4\n"
            "Yield = 4 ÷ 100 = *4%*\n\n"
            "⚠️ Very high yields can be a trap — the stock price may have crashed."
        )
    },
}


def get_lesson(topic: str) -> str:
    topic = topic.lower().strip()

    # Try exact match first
    if topic in GLOSSARY:
        return GLOSSARY[topic]["text"]

    # Try partial match
    for key, value in GLOSSARY.items():
        if topic in key or key in topic:
            return value["text"]

    return (
        f"❌ Topic *{topic}* not found.\n\n"
        "Use /glossary to see all available topics."
    )


def get_glossary() -> str:
    lines = ["📚 *Available topics to learn:*\n"]
    for key, value in GLOSSARY.items():
        lines.append(f"• `/learn {key}` — {value['title']}")
    lines.append("\n_More topics coming soon!_")
    return "\n".join(lines)
