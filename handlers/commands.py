"""
Bot command handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes
from services.fundamentals import get_fundamentals, get_valuation, get_earnings
from services.education import get_lesson, get_glossary
from services.signals import get_signal, scan_all_signals
from services.predict import predict_ticker, predict_watchlist
from services.rate_limiter import check_rate_limit
from services.paper_trading import buy, sell, get_balance, get_positions, get_history, reset_account


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
        "I'm your *Fundamental Analysis* assistant.\n\n"
        "📚 *What I can teach you:*\n"
        "• Key financial metrics (P/E, EPS, ROE)\n"
        "• How to read earnings reports\n"
        "• Valuation methods (DCF, PEG)\n"
        "• Long/Short signals for crypto\n\n"
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
        "📈 *Signals*\n"
        "/signal `<ticker>` `<short/mid/long>` — Long/Short signal\n"
        "_Example: /signal BTC short_\n\n"
        "/scan `<short/mid/long>` — scan all cryptos\n"
        "_Example: /scan short_\n\n"
        "/predict `<ticker>` `<short/mid/long>` \u2014 technical + news prediction\n"
        "_Example: /predict BTC_\n\n"
        "📰 *News*\n"
        "/news `<ticker>` — latest news\n"
        "/breaking — breaking market news\n\n"
        "📊 *Volume*\n"
        "/watchlist — live volume scan\n\n"
        "🔗 *Correlation*\n"
        "/correlate `<ticker>` — asset correlations\n"
        "/matrix — full correlation matrix\n\n"
        "📐 *Variance*\n"
        "/variance `<ticker>` — volatility analysis\n\n"
        "🎲 *Probability*\n"
        "/prob `<A>` `<B>` — probability calculator\n"
        "/probmatrix `<ticker>` — probability matrix\n\n"
        "🤖 *AI (3 requests/hour)*\n"
        "/ai `<ticker>` — Claude explains all signals\n"
        "/picks `<short/mid/long>` — AI top picks\n\n"
        "💼 *Paper Trading*\n"
        "/balance — virtual portfolio\n"
        "/buy `<ticker>` `<amount>` — buy\n"
        "/sell `<ticker>` `<amount>` — sell\n"
        "/positions — open positions\n"
        "/history — trade history\n"
        "/reset — reset to $10,000\n\n"
        "📚 *Education*\n"
        "/learn `<topic>` — explain a concept\n"
        "/glossary — all topics\n\n"
        "🔔 *Auto alerts*\n"
        "_Breaking news every 5 min_\n"
        "_Volume spikes every 3 min_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def fundamentals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/fundamentals AAPL`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔍 Fetching fundamentals for *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(get_fundamentals(ticker), parse_mode="Markdown")


async def valuation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/valuation AAPL`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"💎 Analyzing *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(get_valuation(ticker), parse_mode="Markdown")


async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/earnings TSLA`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"📋 Fetching earnings for *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(get_earnings(ticker), parse_mode="Markdown")


async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/learn P/E`", parse_mode="Markdown")
        return
    await update.message.reply_text(get_lesson(" ".join(context.args)), parse_mode="Markdown")


async def glossary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_glossary(), parse_mode="Markdown")


async def onchain_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/onchain BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔗 Fetching on-chain data for *{ticker}*...", parse_mode="Markdown")
    from services.onchain import get_onchain
    message = await get_onchain(ticker)
    await update.message.reply_text(message, parse_mode="Markdown")


async def news_ticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/news BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"📰 Fetching news for *{ticker}*...", parse_mode="Markdown")
    from services.news_monitor import get_news_for_ticker
    message = await get_news_for_ticker(ticker)
    await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)


async def breaking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🌍 Fetching breaking market news...", parse_mode="Markdown")
    from services.news_monitor import get_market_news
    message = await get_market_news()
    await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from services.volume_monitor import WATCHLIST, get_current_data
    await update.message.reply_text("📊 Scanning watchlist...", parse_mode="Markdown")
    all_tickers = WATCHLIST["crypto"] + WATCHLIST["stocks"] + WATCHLIST["indices"]
    lines = ["📊 *Live Watchlist*\n"]
    for ticker in all_tickers:
        data = get_current_data(ticker)
        if not data:
            continue
        clean = ticker.replace("-USD", "")
        ratio = data["volume_ratio"]
        change = data["price_change"]
        price_val = data["price"]
        vol_emoji = "🔥🔥" if ratio >= 3 else "🔥" if ratio >= 2 else "⚡" if ratio >= 1.5 else "➖"
        price_emoji = "📈" if change > 0 else "📉"
        sign = "+" if change > 0 else ""
        lines.append(f"{vol_emoji} *{clean}* — `${price_val:,.2f}` {price_emoji} `{sign}{change:.1f}%` | Vol: `{ratio:.1f}x`")
    lines.append("\n_🔥 = volume spike_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def correlate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/correlate BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "30d"
    await update.message.reply_text(f"🔗 Calculating correlations for *{ticker}*...", parse_mode="Markdown")
    from services.correlation import get_correlation_with
    await update.message.reply_text(get_correlation_with(ticker, period), parse_mode="Markdown")


async def matrix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📊 Building correlation matrix...", parse_mode="Markdown")
    from services.correlation import get_full_matrix
    await update.message.reply_text(get_full_matrix(), parse_mode="Markdown")


async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/ai AAPL`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🤖 Claude analyzing *{ticker}*...", parse_mode="Markdown")
    from services.ai_summary import get_ai_summary
    message = await get_ai_summary(ticker)
    await update.message.reply_text(message, parse_mode="Markdown")


async def picks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    timeframe = context.args[0].lower() if context.args else "all"
    if timeframe not in ["short", "mid", "long", "all"]:
        timeframe = "all"
    labels = {"short": "short-term", "mid": "mid-term", "long": "long-term", "all": "all timeframes"}
    await update.message.reply_text(f"🤖 Scanning for *{labels[timeframe]}* picks...", parse_mode="Markdown")
    from services.ai_picks import get_ai_picks
    message = await get_ai_picks(timeframe)
    await update.message.reply_text(message, parse_mode="Markdown")


async def prob_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ Example: `/prob BTC ETH`", parse_mode="Markdown")
        return
    ticker_a = context.args[0].upper()
    ticker_b = context.args[1].upper()
    move_pct = float(context.args[2]) if len(context.args) > 2 else 3.0
    direction = context.args[3].lower() if len(context.args) > 3 else "up"
    lag_days = int(context.args[4]) if len(context.args) > 4 else 1
    if direction not in ["up", "down"]: direction = "up"
    await update.message.reply_text("🎲 Calculating probability...", parse_mode="Markdown")
    from services.probability import calculate_probability, format_probability
    result = calculate_probability(ticker_a, ticker_b, move_pct, direction, lag_days)
    await update.message.reply_text(format_probability(result), parse_mode="Markdown")


async def probmatrix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/probmatrix BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    move_pct = float(context.args[1]) if len(context.args) > 1 else 3.0
    await update.message.reply_text(f"🎲 Building probability matrix for *{ticker}*...", parse_mode="Markdown")
    from services.probability import get_full_probability_matrix
    await update.message.reply_text(get_full_probability_matrix(ticker, move_pct), parse_mode="Markdown")


async def variance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/variance BTC`", parse_mode="Markdown")
        return
    from services.variance import calculate_variance, compare_variance
    if len(context.args) >= 2 and context.args[1].upper() in ["BTC","ETH","XRP","SOL","BNB","AAPL","TSLA","NVDA","MSFT","AMZN","META","GOOGL","SPY","QQQ","GLD"]:
        tickers = [a.upper() for a in context.args]
        await update.message.reply_text("📐 Comparing volatility...", parse_mode="Markdown")
        await update.message.reply_text(compare_variance(tickers), parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "30d"
    await update.message.reply_text(f"📐 Calculating variance for *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(calculate_variance(ticker, period), parse_mode="Markdown")


async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "📊 *Signal Generator*\n\n"
            "`/signal BTC short` — 1-3 days\n"
            "`/signal ETH mid` — 1-2 weeks\n"
            "`/signal SOL long` — 1-3 months",
            parse_mode="Markdown"
        )
        return
    ticker = context.args[0].upper()
    timeframe = context.args[1].lower() if len(context.args) > 1 else "short"
    if timeframe not in ["short","mid","long"]: timeframe = "short"
    await update.message.reply_text(f"📊 Analyzing *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(get_signal(ticker, timeframe), parse_mode="Markdown")


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    timeframe = context.args[0].lower() if context.args else "short"
    if timeframe not in ["short","mid","long"]: timeframe = "short"
    await update.message.reply_text("🔍 Scanning all cryptos...\n_~30 seconds_", parse_mode="Markdown")
    await update.message.reply_text(scan_all_signals(timeframe), parse_mode="Markdown")


async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed, msg = check_rate_limit(update.effective_chat.id)
    if not allowed:
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    try:
        if not context.args:
            await update.message.reply_text("⏳ Scanning watchlist (technical + news)...", parse_mode="Markdown")
            result = await predict_watchlist()
            await update.message.reply_text(result, parse_mode="Markdown", disable_web_page_preview=True)
            return

        ticker = context.args[0].upper()
        timeframe = context.args[1].lower() if len(context.args) > 1 else "short"
        await update.message.reply_text(f"⏳ Analyzing *{ticker}*...", parse_mode="Markdown")
        result = await predict_ticker(ticker, timeframe)
        await update.message.reply_text(result, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"❌ Prediction error: {e}", parse_mode="Markdown")


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_balance(update.effective_chat.id), parse_mode="Markdown")


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Example: `/buy BTC 100`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    try: amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Amount must be a number.", parse_mode="Markdown")
        return
    await update.message.reply_text(f"⏳ Buying *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(buy(update.effective_chat.id, ticker, amount), parse_mode="Markdown")


async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Example: `/sell BTC 100`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    try: amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Amount must be a number.", parse_mode="Markdown")
        return
    await update.message.reply_text(f"⏳ Selling *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(sell(update.effective_chat.id, ticker, amount), parse_mode="Markdown")


async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_positions(update.effective_chat.id), parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_history(update.effective_chat.id), parse_mode="Markdown")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(reset_account(update.effective_chat.id), parse_mode="Markdown")
