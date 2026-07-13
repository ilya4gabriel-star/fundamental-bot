"""
Crypto on-chain fundamentals service.
"""

import aiohttp
import yfinance as yf

CRYPTO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "BNB": "binancecoin",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "MATIC": "matic-network",
}


async def get_onchain(ticker: str) -> str:
    ticker = ticker.upper()
    coin_id = CRYPTO_IDS.get(ticker, ticker.lower())

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status != 200:
                    return f"❌ Could not fetch data for *{ticker}*. Check the ticker."

                data = await r.json()
                market = data.get("market_data", {})
                dev = data.get("developer_data", {})
                community = data.get("community_data", {})

                name = data.get("name", ticker)
                symbol = data.get("symbol", "").upper()
                rank = data.get("market_cap_rank", "N/A")
                description_lines = data.get("description", {}).get("en", "")[:200]

                price = market.get("current_price", {}).get("usd")
                ath = market.get("ath", {}).get("usd")
                ath_change = market.get("ath_change_percentage", {}).get("usd")
                market_cap = market.get("market_cap", {}).get("usd")
                volume = market.get("total_volume", {}).get("usd")
                circulating = market.get("circulating_supply")
                total_supply = market.get("total_supply")
                max_supply = market.get("max_supply")
                change_24h = market.get("price_change_percentage_24h")
                change_7d = market.get("price_change_percentage_7d")
                change_30d = market.get("price_change_percentage_30d")

                # Market cap / volume ratio (liquidity indicator)
                mcap_vol_ratio = (market_cap / volume) if market_cap and volume else None

                # Supply analysis
                if circulating and max_supply:
                    supply_pct = (circulating / max_supply) * 100
                    supply_note = f"{supply_pct:.1f}% of max supply in circulation"
                    if supply_pct > 90:
                        supply_emoji = "🔴"
                    elif supply_pct > 70:
                        supply_emoji = "🟡"
                    else:
                        supply_emoji = "🟢"
                elif circulating and total_supply:
                    supply_pct = (circulating / total_supply) * 100
                    supply_note = f"{supply_pct:.1f}% of total supply in circulation"
                    supply_emoji = "⚪"
                else:
                    supply_note = "N/A"
                    supply_emoji = "⚪"

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

                def fmt_supply(v):
                    if not v:
                        return "N/A"
                    if v >= 1e9:
                        return f"{v/1e9:.2f}B"
                    if v >= 1e6:
                        return f"{v/1e6:.2f}M"
                    return f"{v:,.0f}"

                def fmt_pct(v):
                    if v is None:
                        return "N/A"
                    sign = "+" if v > 0 else ""
                    emoji = "📈" if v > 0 else "📉"
                    return f"{emoji} `{sign}{v:.1f}%`"

                lines = [
                    f"🔗 *{name} ({symbol}) — On-Chain Fundamentals*",
                    f"🏆 Market Rank: #{rank}\n",

                    f"💵 *Price*",
                    f"Current: `${price:,.4f}`" if price and price < 1 else f"Current: `${price:,.2f}`" if price else "Current: `N/A`",
                    f"24h: {fmt_pct(change_24h)}",
                    f"7d: {fmt_pct(change_7d)}",
                    f"30d: {fmt_pct(change_30d)}",
                    f"ATH: `${ath:,.2f}` ({ath_change:.1f}% from ATH)\n" if ath and ath_change else "",

                    f"📊 *Market Data*",
                    f"Market Cap: `{fmt_num(market_cap)}`",
                    f"24h Volume: `{fmt_num(volume)}`",
                    f"MCap/Volume Ratio: `{mcap_vol_ratio:.1f}x`" if mcap_vol_ratio else "MCap/Volume: `N/A`",
                    f"_Lower ratio = more liquid and actively traded_\n",

                    f"🔄 *Supply Analysis*",
                    f"Circulating: `{fmt_supply(circulating)}`",
                    f"Total Supply: `{fmt_supply(total_supply)}`",
                    f"Max Supply: `{fmt_supply(max_supply)}`",
                    f"{supply_emoji} {supply_note}\n",

                    f"👨‍💻 *Developer Activity*",
                    f"GitHub Stars: `{dev.get('stars', 'N/A')}`",
                    f"Forks: `{dev.get('forks', 'N/A')}`",
                    f"Commits (4 weeks): `{dev.get('commit_count_4_weeks', 'N/A')}`",
                    f"Active Issues: `{dev.get('total_issues', 'N/A')}`\n",

                    f"👥 *Community*",
                    f"Twitter Followers: `{community.get('twitter_followers', 'N/A'):,}`" if community.get('twitter_followers') else "Twitter: `N/A`",
                    f"Reddit Subscribers: `{community.get('reddit_subscribers', 'N/A'):,}`" if community.get('reddit_subscribers') else "Reddit: `N/A`",
                ]

                return "\n".join([l for l in lines if l])

    except Exception as e:
        return f"❌ Error fetching on-chain data for *{ticker}*: {e}"
