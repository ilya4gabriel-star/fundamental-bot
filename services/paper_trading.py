"""
Paper trading service.
Virtual money, real prices.
"""

import json
import os
from datetime import datetime
import yfinance as yf

PAPER_FILE = "paper_trading.json"
STARTING_BALANCE = 10000.0

CRYPTO_TICKERS = {"BTC", "ETH", "XRP", "SOL", "BNB", "ADA", "DOGE", "MATIC"}


def load_data() -> dict:
    if not os.path.exists(PAPER_FILE):
        return {}
    with open(PAPER_FILE, "r") as f:
        return json.load(f)


def save_data(data: dict):
    with open(PAPER_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_user(chat_id: int) -> dict:
    data = load_data()
    key = str(chat_id)
    if key not in data:
        data[key] = {
            "balance": STARTING_BALANCE,
            "positions": {},
            "history": [],
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_trades": 0,
        }
        save_data(data)
    return data[key]


def save_user(chat_id: int, user: dict):
    data = load_data()
    data[str(chat_id)] = user
    save_data(data)


def get_price(ticker: str) -> float:
    try:
        symbol = f"{ticker}-USD" if ticker in CRYPTO_TICKERS else ticker
        stock = yf.Ticker(symbol)
        return float(stock.fast_info.last_price)
    except Exception:
        return None


def buy(chat_id: int, ticker: str, amount_usd: float) -> str:
    ticker = ticker.upper()
    user = get_user(chat_id)

    if amount_usd <= 0:
        return "❌ Amount must be greater than 0."

    if amount_usd > user["balance"]:
        return (
            f"❌ Insufficient balance.\n"
            f"Available: `${user['balance']:,.2f}`\n"
            f"Required: `${amount_usd:,.2f}`"
        )

    price = get_price(ticker)
    if not price:
        return f"❌ Could not fetch price for *{ticker}*. Check the ticker."

    shares = amount_usd / price
    user["balance"] -= amount_usd

    if ticker in user["positions"]:
        # Average down/up
        pos = user["positions"][ticker]
        total_shares = pos["shares"] + shares
        total_cost = pos["avg_price"] * pos["shares"] + amount_usd
        pos["shares"] = total_shares
        pos["avg_price"] = total_cost / total_shares
        pos["total_invested"] = pos.get("total_invested", 0) + amount_usd
    else:
        user["positions"][ticker] = {
            "shares": shares,
            "avg_price": price,
            "total_invested": amount_usd,
        }

    user["history"].append({
        "type": "BUY",
        "ticker": ticker,
        "shares": shares,
        "price": price,
        "amount_usd": amount_usd,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    user["total_trades"] += 1
    save_user(chat_id, user)

    return (
        f"✅ *BUY executed — {ticker}*\n\n"
        f"💵 Amount: `${amount_usd:,.2f}`\n"
        f"📈 Price: `${price:,.2f}`\n"
        f"🔢 Shares: `{shares:.6f}`\n"
        f"💰 Remaining balance: `${user['balance']:,.2f}`"
    )


def sell(chat_id: int, ticker: str, amount_usd: float) -> str:
    ticker = ticker.upper()
    user = get_user(chat_id)

    if ticker not in user["positions"]:
        return f"❌ You don't have any *{ticker}* position."

    pos = user["positions"][ticker]
    price = get_price(ticker)
    if not price:
        return f"❌ Could not fetch price for *{ticker}*."

    current_value = pos["shares"] * price

    if amount_usd > current_value:
        return (
            f"❌ Not enough {ticker} to sell.\n"
            f"Position value: `${current_value:,.2f}`\n"
            f"Requested: `${amount_usd:,.2f}`"
        )

    shares_to_sell = amount_usd / price
    pnl = (price - pos["avg_price"]) * shares_to_sell
    pnl_pct = ((price - pos["avg_price"]) / pos["avg_price"]) * 100

    pos["shares"] -= shares_to_sell
    user["balance"] += amount_usd

    if pos["shares"] < 0.000001:
        del user["positions"][ticker]

    user["history"].append({
        "type": "SELL",
        "ticker": ticker,
        "shares": shares_to_sell,
        "price": price,
        "amount_usd": amount_usd,
        "pnl": pnl,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    user["total_trades"] += 1
    save_user(chat_id, user)

    pnl_emoji = "📈" if pnl >= 0 else "📉"
    sign = "+" if pnl >= 0 else ""

    return (
        f"✅ *SELL executed — {ticker}*\n\n"
        f"💵 Amount: `${amount_usd:,.2f}`\n"
        f"📉 Price: `${price:,.2f}`\n"
        f"🔢 Shares sold: `{shares_to_sell:.6f}`\n"
        f"{pnl_emoji} P&L: `{sign}${pnl:,.2f}` ({sign}{pnl_pct:.1f}%)\n"
        f"💰 New balance: `${user['balance']:,.2f}`"
    )


def get_balance(chat_id: int) -> str:
    user = get_user(chat_id)
    balance = user["balance"]
    positions = user["positions"]

    total_positions_value = 0
    position_lines = []

    for ticker, pos in positions.items():
        price = get_price(ticker)
        if price:
            current_value = pos["shares"] * price
            pnl = current_value - pos["total_invested"]
            pnl_pct = (pnl / pos["total_invested"]) * 100
            total_positions_value += current_value
            emoji = "📈" if pnl >= 0 else "📉"
            sign = "+" if pnl >= 0 else ""
            position_lines.append(
                f"{emoji} *{ticker}*: `${current_value:,.2f}` ({sign}{pnl_pct:.1f}%)"
            )

    total_value = balance + total_positions_value
    total_pnl = total_value - STARTING_BALANCE
    total_pnl_pct = (total_pnl / STARTING_BALANCE) * 100
    total_emoji = "📈" if total_pnl >= 0 else "📉"
    total_sign = "+" if total_pnl >= 0 else ""

    lines = [
        f"💼 *Paper Trading Account*\n",
        f"💵 Cash: `${balance:,.2f}`",
        f"📊 Positions: `${total_positions_value:,.2f}`",
        f"{'─'*25}",
        f"💰 Total Value: `${total_value:,.2f}`",
        f"{total_emoji} Total P&L: `{total_sign}${total_pnl:,.2f}` ({total_sign}{total_pnl_pct:.1f}%)\n",
    ]

    if position_lines:
        lines.append("*Open Positions:*")
        lines.extend(position_lines)
    else:
        lines.append("_No open positions_")

    lines.append(f"\n_Total trades: {user['total_trades']} · Started with $10,000_")
    lines.append("_Use /buy or /sell to trade_")

    return "\n".join(lines)


def get_positions(chat_id: int) -> str:
    user = get_user(chat_id)
    positions = user["positions"]

    if not positions:
        return "📭 No open positions.\n\nUse `/buy BTC 100` to open one."

    lines = ["📊 *Open Positions*\n"]

    for ticker, pos in positions.items():
        price = get_price(ticker)
        if not price:
            continue

        current_value = pos["shares"] * price
        pnl = current_value - pos["total_invested"]
        pnl_pct = (pnl / pos["total_invested"]) * 100
        emoji = "📈" if pnl >= 0 else "📉"
        sign = "+" if pnl >= 0 else ""

        lines.append(
            f"{emoji} *{ticker}*\n"
            f"   Shares: `{pos['shares']:.6f}`\n"
            f"   Avg Price: `${pos['avg_price']:,.2f}`\n"
            f"   Current: `${price:,.2f}`\n"
            f"   Value: `${current_value:,.2f}`\n"
            f"   P&L: `{sign}${pnl:,.2f}` ({sign}{pnl_pct:.1f}%)\n"
        )

    return "\n".join(lines)


def get_history(chat_id: int) -> str:
    user = get_user(chat_id)
    history = user["history"][-10:]  # Last 10 trades

    if not history:
        return "📭 No trade history yet."

    lines = ["📋 *Trade History (last 10)*\n"]

    for trade in reversed(history):
        t = trade["type"]
        ticker = trade["ticker"]
        amount = trade["amount_usd"]
        price = trade["price"]
        date = trade["date"]
        emoji = "🟢" if t == "BUY" else "🔴"

        line = f"{emoji} *{t} {ticker}* — `${amount:,.2f}` @ `${price:,.2f}` · _{date}_"
        if t == "SELL" and "pnl" in trade:
            sign = "+" if trade["pnl"] >= 0 else ""
            line += f"\n   P&L: `{sign}${trade['pnl']:,.2f}`"
        lines.append(line)

    return "\n".join(lines)


def reset_account(chat_id: int) -> str:
    data = load_data()
    data[str(chat_id)] = {
        "balance": STARTING_BALANCE,
        "positions": {},
        "history": [],
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_trades": 0,
    }
    save_data(data)
    return "🔄 *Account reset!*\n\nNew balance: `$10,000.00`\nGood luck! 🚀"
