import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from config import BOT_TOKEN
from handlers.commands import (
    start, help_command,
    fundamentals_command, valuation_command, earnings_command,
    learn_command, glossary_command, onchain_command,
    news_ticker_command, breaking_command,
    watchlist_command, correlate_command, matrix_command,
    ai_command, picks_command,
    prob_command, probmatrix_command, variance_command,
    signal_command, scan_command,
    balance_command, buy_command, sell_command,
    positions_command, history_command, reset_command
)
from services.news_monitor import monitor_breaking_news
from services.volume_monitor import monitor_volumes

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
active_chats = set()

async def post_init(app):
    asyncio.create_task(monitor_breaking_news(app, active_chats))
    asyncio.create_task(monitor_volumes(app, active_chats))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("fundamentals", fundamentals_command))
    app.add_handler(CommandHandler("valuation", valuation_command))
    app.add_handler(CommandHandler("earnings", earnings_command))
    app.add_handler(CommandHandler("learn", learn_command))
    app.add_handler(CommandHandler("glossary", glossary_command))
    app.add_handler(CommandHandler("onchain", onchain_command))
    app.add_handler(CommandHandler("news", news_ticker_command))
    app.add_handler(CommandHandler("breaking", breaking_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("correlate", correlate_command))
    app.add_handler(CommandHandler("matrix", matrix_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("picks", picks_command))
    app.add_handler(CommandHandler("prob", prob_command))
    app.add_handler(CommandHandler("probmatrix", probmatrix_command))
    app.add_handler(CommandHandler("variance", variance_command))
    app.add_handler(CommandHandler("signal", signal_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("sell", sell_command))
    app.add_handler(CommandHandler("positions", positions_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.run_polling()

if __name__ == "__main__":
    main()
