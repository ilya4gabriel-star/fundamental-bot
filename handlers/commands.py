"""
Bot command handlers.
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.market import get_crypto_price, get_stock_price, format_price_message
from services.analysis import analyze, format_analysis
from services.alerts import add_alert, format_alerts, remove_alert
from services.charts import generate_chart
from services.portfolio import add_asset, get_portfolio_summary, remove_asset as remove_portfolio_asset
from services.news_monitor import get_news_for_ticker, get_market_news
from services.correlation import get_correlation_with, get_full_matrix
from services.variance import calculate_variance, compare_variance
from services.probability import calculate_probability, format_probability, get_full_probability_matrix, WATCHLIST as PROB_WATCHLIST
from services.signals import get_signal, scan_all_signals
from services.rate_limiter import get_cached, set_cached, check_rate_limit
from services.paper_trading import buy, sell, get_balance, get_positions, get_history, reset_account

CRYPTO_TICKERS = {"BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "MATIC"}


def asset_keyboard(ticker: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Chart", callback_data=f"chart_{ticker}"),
            InlineKeyboardButton("🔬 Analyze", callback_data=f"analyze_{ticker}"),
        ],
        [
            InlineKeyboardButton("🔔 Alert above", callback_data=f"alertabove_{ticker}"),
            InlineKeyboardButton("🔔 Alert below", callback_data=f"alertbelow_{ticker}"),
        ]
    ])


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
        "• Whether a stock is cheap or expensive\n\n"
        "Type /help to see all commands."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *All available commands:*\n\n"
        "📊 *Stock Analysis*\n"
        "/fundamentals `<ticker>` — full financial metrics\n"
        "/earnings `<ticker>` — earnings report\n"
        "/valuation `<ticker>` — cheap or expensive?\n\n"
        "🪙 *Crypto Analysis*\n"
        "/onchain `<ticker>` — on-chain fundamentals\n\n"
        "📈 *Signals*\n"
        "/signal `<ticker>` `<short/mid/long>` — Long/Short signal\n"
        "_Example: /signal BTC short_\n\n"
        "/scan `<short/mid/long>` — scan all cryptos\n\n"
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
        "ℹ️ *General*\n"
        "/start — welcome\n"
        "/help — this message\n\n"
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
    from services.fundamentals import get_fundamentals
    await update.message.reply_text(get_fundamentals(ticker), parse_mode="Markdown")


async def valuation_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/valuation AAPL`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"💎 Analyzing *{ticker}*...", parse_mode="Markdown")
    from services.fundamentals import get_valuation
    await update.message.reply_text(get_valuation(ticker), parse_mode="Markdown")


async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/earnings TSLA`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"📋 Fetching earnings for *{ticker}*...", parse_mode="Markdown")
    from services.fundamentals import get_earnings
    await update.message.reply_text(get_earnings(ticker), parse_mode="Markdown")


async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/learn P/E`", parse_mode="Markdown")
        return
    from services.education import get_lesson
    await update.message.reply_text(get_lesson(" ".join(context.args)), parse_mode="Markdown")


async def glossary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from services.education import get_glossary
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


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/price BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔍 Looking up *{ticker}*...", parse_mode="Markdown")
    if ticker in CRYPTO_TICKERS:
        data = await get_crypto_price(ticker)
    else:
        data = get_stock_price(ticker)
    await update.message.reply_text(format_price_message(data), parse_mode="Markdown", reply_markup=asset_keyboard(ticker))


async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/chart BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    msg = await update.message.reply_text(f"📊 Generating chart for *{ticker}*...", parse_mode="Markdown")
    path = generate_chart(ticker)
    if path:
        await update.message.reply_photo(photo=open(path, "rb"), caption=f"*{ticker}* — 7 Day Chart", parse_mode="Markdown")
        os.remove(path)
    else:
        await update.message.reply_text("❌ Could not generate chart.")
    await msg.delete()


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/analyze BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(format_analysis(analyze(ticker)), parse_mode="Markdown")


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 3:
        await update.message.reply_text("⚠️ Example: `/alert BTC above 70000`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    direction = context.args[1].lower()
    try:
        target = float(context.args[2])
    except ValueError:
        await update.message.reply_text("⚠️ Price must be a number.", parse_mode="Markdown")
        return
    await update.message.reply_text(add_alert(update.effective_chat.id, ticker, target, direction), parse_mode="Markdown")


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(format_alerts(update.effective_chat.id), parse_mode="Markdown")


async def removealert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/removealert 1`", parse_mode="Markdown")
        return
    try:
        await update.message.reply_text(remove_alert(update.effective_chat.id, int(context.args[0])-1), parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a valid number.", parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    if data.startswith("chart_"):
        ticker = data.split("_")[1]
        path = generate_chart(ticker)
        if path:
            await query.message.reply_photo(photo=open(path, "rb"), caption=f"*{ticker}* — 7 Day Chart", parse_mode="Markdown")
            os.remove(path)
    elif data.startswith("analyze_"):
        ticker = data.split("_")[1]
        await query.message.reply_text(format_analysis(analyze(ticker)), parse_mode="Markdown")
    elif data.startswith("alertabove_"):
        ticker = data.split("_")[1]
        data2 = await get_crypto_price(ticker) if ticker in CRYPTO_TICKERS else get_stock_price(ticker)
        if data2:
            target = round(data2["price"] * 1.05, 2)
            await query.message.reply_text(add_alert(chat_id, ticker, target, "above") + "\n_(+5%)_", parse_mode="Markdown")
    elif data.startswith("alertbelow_"):
        ticker = data.split("_")[1]
        data2 = await get_crypto_price(ticker) if ticker in CRYPTO_TICKERS else get_stock_price(ticker)
        if data2:
            target = round(data2["price"] * 0.95, 2)
            await query.message.reply_text(add_alert(chat_id, ticker, target, "below") + "\n_(−5%)_", parse_mode="Markdown")


async def news_ticker_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/news BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"📰 Fetching news for *{ticker}*...", parse_mode="Markdown")
    message = await get_news_for_ticker(ticker)
    await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)


async def breaking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🌍 Fetching breaking market news...", parse_mode="Markdown")
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
    await update.message.reply_text(f"🔗 Calculating correlations for *{ticker}*...\n_~15 seconds_", parse_mode="Markdown")
    await update.message.reply_text(get_correlation_with(ticker, period), parse_mode="Markdown")


async def matrix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📊 Building correlation matrix...\n_~20 seconds_", parse_mode="Markdown")
    await update.message.reply_text(get_full_matrix(), parse_mode="Markdown")


async def ai_safe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/ai AAPL`", parse_mode="Markdown")
        return
    chat_id = update.effective_chat.id
    ticker = context.args[0].upper()
    allowed, msg = check_rate_limit(chat_id)
    if not allowed:
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    cached = get_cached(f"ai_{ticker}")
    if cached:
        await update.message.reply_text(cached + "\n\n_⚡ Cached — refreshes every 30 min_", parse_mode="Markdown")
        return
    await update.message.reply_text(f"🤖 Claude analyzing *{ticker}*...\n_~10 seconds_", parse_mode="Markdown")
    from services.ai_summary import get_ai_summary
    message = await get_ai_summary(ticker)
    set_cached(f"ai_{ticker}", message)
    await update.message.reply_text(message, parse_mode="Markdown")


async def picks_safe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    timeframe = context.args[0].lower() if context.args else "all"
    if timeframe not in ["short", "mid", "long", "all"]:
        await update.message.reply_text("⚠️ Use: `/picks short/mid/long/all`", parse_mode="Markdown")
        return
    allowed, msg = check_rate_limit(chat_id)
    if not allowed:
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    cached = get_cached(f"picks_{timeframe}")
    if cached:
        await update.message.reply_text(cached + "\n\n_⚡ Cached — refreshes every 30 min_", parse_mode="Markdown")
        return
    labels = {"short": "short-term", "mid": "mid-term", "long": "long-term", "all": "all timeframes"}
    await update.message.reply_text(f"🤖 Scanning markets for *{labels[timeframe]}* picks...\n_~20 seconds_", parse_mode="Markdown")
    from services.ai_picks import get_ai_picks
    message = await get_ai_picks(timeframe)
    set_cached(f"picks_{timeframe}", message)
    await update.message.reply_text(message, parse_mode="Markdown")


async def prob_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ Example: `/prob BTC ETH` or `/prob BTC SOL 5 up`", parse_mode="Markdown")
        return
    ticker_a = context.args[0].upper()
    ticker_b = context.args[1].upper()
    move_pct = float(context.args[2]) if len(context.args) > 2 else 3.0
    direction = context.args[3].lower() if len(context.args) > 3 else "up"
    lag_days = int(context.args[4]) if len(context.args) > 4 else 1
    if direction not in ["up", "down"]:
        direction = "up"
    await update.message.reply_text(f"🎲 Calculating probability...\n_Analyzing 1 year of data..._", parse_mode="Markdown")
    result = calculate_probability(ticker_a, ticker_b, move_pct, direction, lag_days)
    await update.message.reply_text(format_probability(result), parse_mode="Markdown")


async def probmatrix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/probmatrix BTC`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    move_pct = float(context.args[1]) if len(context.args) > 1 else 3.0
    await update.message.reply_text(f"🎲 Building probability matrix for *{ticker}*...\n_~30 seconds_", parse_mode="Markdown")
    from services.probability import get_full_probability_matrix
    await update.message.reply_text(get_full_probability_matrix(ticker, move_pct), parse_mode="Markdown")


async def variance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/variance BTC` or `/variance BTC ETH SOL`", parse_mode="Markdown")
        return
    if len(context.args) >= 2 and context.args[1].upper() in ["BTC","ETH","XRP","SOL","BNB","AAPL","TSLA","NVDA","MSFT","AMZN","META","GOOGL","SPY","QQQ","GLD"]:
        tickers = [a.upper() for a in context.args]
        await update.message.reply_text(f"📐 Comparing volatility...", parse_mode="Markdown")
        await update.message.reply_text(compare_variance(tickers), parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "30d"
    await update.message.reply_text(f"📐 Calculating variance for *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(calculate_variance(ticker, period), parse_mode="Markdown")


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_balance(update.effective_chat.id), parse_mode="Markdown")


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Example: `/buy BTC 100`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Amount must be a number.", parse_mode="Markdown")
        return
    await update.message.reply_text(f"⏳ Executing BUY *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(buy(update.effective_chat.id, ticker, amount), parse_mode="Markdown")


async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Example: `/sell BTC 100`", parse_mode="Markdown")
        return
    ticker = context.args[0].upper()
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Amount must be a number.", parse_mode="Markdown")
        return
    await update.message.reply_text(f"⏳ Executing SELL *{ticker}*...", parse_mode="Markdown")
    await update.message.reply_text(sell(update.effective_chat.id, ticker, amount), parse_mode="Markdown")


async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_positions(update.effective_chat.id), parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_history(update.effective_chat.id), parse_mode="Markdown")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(reset_account(update.effective_chat.id), parse_mode="Markdown")


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
    if timeframe not in ["short", "mid", "long"]:
        timeframe = "short"
    await update.message.reply_text(f"📊 Analyzing *{ticker}* signal...", parse_mode="Markdown")
    await update.message.reply_text(get_signal(ticker, timeframe), parse_mode="Markdown")


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    timeframe = context.args[0].lower() if context.args else "short"
    if timeframe not in ["short", "mid", "long"]:
        timeframe = "short"
    await update.message.reply_text(f"🔍 Scanning all cryptos...\n_~30 seconds_", parse_mode="Markdown")
    await update.message.reply_text(scan_all_signals(timeframe), parse_mode="Markdown")


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(get_portfolio_summary(update.effective_chat.id), parse_mode="Markdown")
        return
    if context.args[0].lower() == "add":
        if len(context.args) < 4:
            await update.message.reply_text("⚠️ Example: `/portfolio add BTC 0.5 60000`", parse_mode="Markdown")
            return
        ticker = context.args[1].upper()
        try:
            amount = float(context.args[2])
            buy_price = float(context.args[3])
        except ValueError:
            await update.message.reply_text("⚠️ Amount and price must be numbers.", parse_mode="Markdown")
            return
        await update.message.reply_text(add_asset(update.effective_chat.id, ticker, amount, buy_price), parse_mode="Markdown")


async def removeportfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Example: `/removeportfolio 1`", parse_mode="Markdown")
        return
    try:
        await update.message.reply_text(remove_portfolio_asset(update.effective_chat.id, int(context.args[0])-1), parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a valid number.", parse_mode="Markdown")
