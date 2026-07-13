"""
Command handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes
from services.fundamentals import get_fundamentals, get_valuation, get_earnings
from services.education import get_lesson, get_glossary


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name if user.first_name else "investor"

    try:
        from main import active_chats
        active_chats.add(update.effective_chat.id)
    except Exception:
        pass

    text = (
        f"👋 Hey, {name}!\n\n"
        "I\'m your *Fundamental Analysis* assistant.\n\n"
        "📚 *What I can teach you:*\n"
        "• Key financial metrics (P/E, EPS, ROE)\n"
        "• How to read earnings reports\n"
        "• Valuation methods (DCF, PEG)\n"
        "• Whether a stock is cheap or expensive\n\n"
        "Type /help to see all commands."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *All available commands:*\n\n"
        "📊 *Stock Analysis*\n"
        "/fundamentals `<ticker>` — full financial metrics\n"
        "_Example: /fundamentals AAPL_\n\n"
        "/earnings `<ticker>` — earnings report\n"
        "_Example: /earnings TSLA_\n\n"
        "/valuation `<ticker>` — cheap or expensive?\n"
        "_Example: /valuation NVDA_\n\n"
        "🪙 *Crypto Analysis*\n"
        "/onchain `<ticker>` — on-chain fundamentals\n"
        "_Example: /onchain BTC_\n\n"
        "📰 *News & Sentiment*\n"
        "/news `<ticker>` — latest news with sentiment\n"
        "_Example: /news BTC_\n\n"
        "/breaking — breaking market news (all sources)\n\n"
        "📊 *Volume & Market*\n"
        "/watchlist — live volume scan of all assets\n\n"
        "🔗 *Correlation*\n"
        "/correlate `<ticker>` — which assets move with it\n"
        "_Example: /correlate BTC_\n\n"
        "/matrix — full correlation matrix of all assets\n\n"
        "🤖 *AI Analysis*\n"
        "/ai `<ticker>` — Claude explains all signals\n"
        "_Example: /ai AAPL_\n\n"
        "🎲 *Probability*\n"
        "/prob `<A>` `<B>` — if A moves, does B follow?\n"
        "_Example: /prob BTC ETH_\n\n"
        "/probmatrix `<ticker>` — full probability matrix\n"
        "_Example: /probmatrix BTC_\n\n"
        "🎯 *AI Picks*\n"
        "/picks — top picks for all timeframes\n"
        "/picks short — best picks for 1-5 days\n"
        "/picks mid — best picks for 2-8 weeks\n"
        "/picks long — best picks for 3-12 months\n\n"
        "📚 *Education*\n"
        "/learn `<topic>` — explain a concept\n"
        "_Example: /learn P/E_\n"
        "_Example: /learn DCF_\n"
        "_Example: /learn beta_\n\n"
        "/glossary — list of all topics\n\n"
        "ℹ️ *General*\n"
        "/start — welcome + activate alerts\n"
        "/help — this help message\n\n"
        "🔔 *Auto alerts (background)*\n"
        "_Breaking news pushed every 5 min_\n"
        "_Volume spikes pushed every 3 min_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def fundamentals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker.\nExample: `/fundamentals AAPL`",
            parse_mode="Markdown"
        )
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔍 Fetching fundamentals for *{ticker}*...", parse_mode="Markdown")
    message = get_fundamentals(ticker)
    await update.message.reply_text(message, parse_mode="Markdown")


async def valuation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker.\nExample: `/valuation AAPL`",
            parse_mode="Markdown"
        )
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"💎 Analyzing valuation for *{ticker}*...", parse_mode="Markdown")
    message = get_valuation(ticker)
    await update.message.reply_text(message, parse_mode="Markdown")


async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker.\nExample: `/earnings TSLA`",
            parse_mode="Markdown"
        )
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"📋 Fetching earnings for *{ticker}*...", parse_mode="Markdown")
    message = get_earnings(ticker)
    await update.message.reply_text(message, parse_mode="Markdown")


async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a topic.\nExample: `/learn P/E`",
            parse_mode="Markdown"
        )
        return
    topic = " ".join(context.args)
    message = get_lesson(topic)
    await update.message.reply_text(message, parse_mode="Markdown")


async def glossary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = get_glossary()
    await update.message.reply_text(message, parse_mode="Markdown")


from services.onchain import get_onchain


async def onchain_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker.\nExample: `/onchain BTC`",
            parse_mode="Markdown"
        )
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔗 Fetching on-chain data for *{ticker}*...", parse_mode="Markdown")
    message = await get_onchain(ticker)
    await update.message.reply_text(message, parse_mode="Markdown")


from services.news_monitor import get_news_for_ticker, get_market_news


async def news_ticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker.\nExample: `/news BTC`",
            parse_mode="Markdown"
        )
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"📰 Fetching news for *{ticker}*...", parse_mode="Markdown")
    message = await get_news_for_ticker(ticker)
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


async def breaking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🌍 Fetching breaking market news...", parse_mode="Markdown")
    message = await get_market_news()
    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


from services.volume_monitor import WATCHLIST, get_current_data


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current watchlist with live volumes."""
    await update.message.reply_text("📊 Scanning watchlist for volume spikes...", parse_mode="Markdown")

    all_tickers = WATCHLIST["crypto"] + WATCHLIST["stocks"] + WATCHLIST["indices"]
    lines = ["📊 *Live Watchlist — Volume Monitor*\n"]

    for ticker in all_tickers:
        data = get_current_data(ticker)
        if not data:
            continue

        clean = ticker.replace("-USD", "")
        ratio = data["volume_ratio"]
        change = data["price_change"]
        price = data["price"]

        if ratio >= 3:
            vol_emoji = "🔥🔥"
        elif ratio >= 2:
            vol_emoji = "🔥"
        elif ratio >= 1.5:
            vol_emoji = "⚡"
        else:
            vol_emoji = "➖"

        price_emoji = "📈" if change > 0 else "📉"
        sign = "+" if change > 0 else ""

        lines.append(
            f"{vol_emoji} *{clean}* — `${price:,.2f}` {price_emoji} `{sign}{change:.1f}%` | Vol: `{ratio:.1f}x`"
        )

    lines.append("\n_🔥 = volume spike · Updates every 3 min_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


from services.correlation import get_correlation_with, get_full_matrix


async def correlate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker.\nExample: `/correlate BTC`",
            parse_mode="Markdown"
        )
        return

    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "30d"

    await update.message.reply_text(
        f"🔗 Calculating correlations for *{ticker}*...\n_This takes ~15 seconds_",
        parse_mode="Markdown"
    )
    message = get_correlation_with(ticker, period)
    await update.message.reply_text(message, parse_mode="Markdown")


async def matrix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📊 Building correlation matrix...\n_This takes ~20 seconds_",
        parse_mode="Markdown"
    )
    message = get_full_matrix()
    await update.message.reply_text(message, parse_mode="Markdown")


from services.ai_summary import get_ai_summary


async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker.\nExample: `/ai AAPL`",
            parse_mode="Markdown"
        )
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(
        f"🤖 Claude is analyzing *{ticker}*...\n_Takes ~10 seconds_",
        parse_mode="Markdown"
    )
    message = await get_ai_summary(ticker)
    await update.message.reply_text(message, parse_mode="Markdown")


from services.ai_picks import get_ai_picks, WATCHLIST as AI_WATCHLIST


async def picks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    timeframe = context.args[0].lower() if context.args else "all"

    if timeframe not in ["short", "mid", "long", "all"]:
        await update.message.reply_text(
            "⚠️ Usage:\n"
            "`/picks` — all timeframes\n"
            "`/picks short` — 1-5 days\n"
            "`/picks mid` — 2-8 weeks\n"
            "`/picks long` — 3-12 months",
            parse_mode="Markdown"
        )
        return

    labels = {
        "short": "short-term (1–5 days)",
        "mid": "mid-term (2–8 weeks)",
        "long": "long-term (3–12 months)",
        "all": "all timeframes",
    }

    await update.message.reply_text(
        f"🤖 Claude is scanning all markets for *{labels[timeframe]}* picks...\n"
        f"_Analyzing {len(AI_WATCHLIST)} assets — takes ~20 seconds_",
        parse_mode="Markdown"
    )

    message = await get_ai_picks(timeframe)
    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )
