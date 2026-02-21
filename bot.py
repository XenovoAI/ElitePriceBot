import asyncio
import logging
from datetime import datetime, timezone
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, BotCommand, MessageEntity
from aiogram.exceptions import TelegramBadRequest
from config import BOT_TOKEN, SUPPORTED_COINS, PREMIUM_EMOJI_ID, ICE_CREAM_EMOJI_ID, ADMIN_IDS, LIVECOINWATCH_API_KEY
from api import get_coin_price, get_all_prices, get_price_chart
from binance_api import binance_updater
from image_engine import (
    create_top_grid_async, create_coin_card_async, create_ath_card_async, 
    create_convert_card_async, image_to_bytes
)
from database import (
    add_user,
    get_stats,
    create_alert,
    list_user_alerts,
    delete_user_alert,
    clear_user_alerts,
    get_active_alerts,
    update_alert_last_price,
    mark_alert_triggered,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ALERT_CHECK_INTERVAL = 20

async def send_photo_safe(
    message: types.Message,
    photo: BufferedInputFile,
    caption: str,
    entities: list[MessageEntity]
):
    """Send photo with custom emoji entities, then fallback without entities if Telegram rejects them."""
    try:
        await message.answer_photo(photo, caption=caption, caption_entities=entities)
    except TelegramBadRequest as exc:
        logger.warning(f"Falling back to plain caption: {exc}")
        await message.answer_photo(photo, caption=caption)

async def set_bot_commands():
    """Set bot commands menu"""
    commands = [
        BotCommand(command="start", description="ðŸš€ Start the bot"),
        BotCommand(command="help", description="ðŸ“– Help & instructions"),
        BotCommand(command="top", description="ðŸ“Š Top 8 coins grid"),
        BotCommand(command="btc", description="â‚¿ Bitcoin price"),
        BotCommand(command="eth", description="Îž Ethereum price"),
        BotCommand(command="sol", description="â—Ž Solana price"),
        BotCommand(command="ton", description="ðŸ’Ž Toncoin price"),
        BotCommand(command="bnb", description="ðŸ”¶ BNB price"),
        BotCommand(command="xrp", description="âœ• XRP price"),
        BotCommand(command="trx", description="âš¡ TRON price"),
        BotCommand(command="ltc", description="Å Litecoin price"),
        BotCommand(command="alert", description="Set price alert"),
        BotCommand(command="alerts", description="List my alerts"),
    ]
    await bot.set_my_commands(commands)

async def alert_monitor_loop():
    """Background worker: checks active alerts and sends notifications."""
    logger.info(f"Alert monitor started (every {ALERT_CHECK_INTERVAL}s)")
    while True:
        try:
            active_alerts = get_active_alerts()
            if not active_alerts:
                await asyncio.sleep(ALERT_CHECK_INTERVAL)
                continue

            symbols = sorted({a.get("coin_symbol", "").lower() for a in active_alerts if a.get("coin_symbol")})
            price_map = {}
            for symbol in symbols:
                coin_data = await get_coin_price(symbol)
                if coin_data:
                    price_map[symbol] = float(coin_data.get("price", 0))
                await asyncio.sleep(0.05)

            for alert in active_alerts:
                alert_id = alert.get("id")
                symbol = alert.get("coin_symbol", "").lower()
                target = float(alert.get("target_price", 0))
                direction = alert.get("direction", "above")
                current = price_map.get(symbol)
                if current is None:
                    continue

                prev = alert.get("last_checked_price")
                crossed = False
                if prev is None:
                    crossed = current >= target if direction == "above" else current <= target
                else:
                    prev = float(prev)
                    if direction == "above":
                        crossed = prev < target <= current
                    else:
                        crossed = prev > target >= current

                if crossed:
                    message_text = (
                        "🔔 <b>Price Alert Triggered</b>\n\n"
                        f"• Coin: <b>{symbol.upper()}</b>\n"
                        f"• Target: <b>${target:,.6f}</b>\n"
                        f"• Current: <b>${current:,.6f}</b>\n"
                        f"• Direction: <b>{direction}</b>\n"
                        f"• Alert ID: <code>{alert_id}</code>\n\n"
                        "Set next alert: <code>/alert btc 70000</code>"
                    )
                    try:
                        await bot.send_message(alert["chat_id"], message_text, parse_mode="HTML")
                        mark_alert_triggered(alert_id, current)
                        logger.info(f"Alert {alert_id} triggered for user {alert.get('user_id')}")
                    except Exception as send_exc:
                        logger.error(f"Failed to send alert {alert_id}: {send_exc}")
                else:
                    update_alert_last_price(alert_id, current)
        except Exception as e:
            logger.error(f"Alert monitor error: {e}")

        await asyncio.sleep(ALERT_CHECK_INTERVAL)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Track user
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    welcome_text = """ðŸš€ <b>Welcome to Cone Price Bot!</b>

Get beautiful crypto price cards instantly.

<b>ðŸ“Š Available Commands:</b>

<b>Price Cards:</b>
â€¢ /top - View top 8 coins in a grid
â€¢ /crypto &lt;symbol&gt; - ANY cryptocurrency!
â€¢ /btc, /eth, /sol, /ton, /bnb, /xrp, /trx, /ltc

<b>Advanced:</b>
â€¢ /ath &lt;coin&gt; - All-time high info
â€¢ /convert &lt;amount&gt; &lt;coin&gt; - Convert to USD

<b>Examples:</b>
â€¢ /crypto doge
â€¢ /crypto shib
â€¢ /crypto ada

<b>ðŸ¦ Powered by @conesociety</b>
<b>Supports 1000+ coins from Binance!</b>"""
    await message.answer(welcome_text, parse_mode="HTML")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """<b>ðŸ“– Cone Price Bot Help</b>

<b>How to use:</b>

<b>1. View All Coins:</b>
Send /top to see a beautiful grid of all 8 supported cryptocurrencies with live prices and 24h changes.

<b>2. Individual Coin Cards:</b>
â€¢ /btc - â‚¿ Bitcoin
â€¢ /eth - Îž Ethereum
â€¢ /sol - â—Ž Solana
â€¢ /ton - ðŸ’Ž Toncoin
â€¢ /bnb - ðŸ”¶ BNB
â€¢ /xrp - âœ• XRP
â€¢ /trx - âš¡ TRON
â€¢ /ltc - Å Litecoin

Each card shows:
â€¢ Current price
â€¢ 24h change
â€¢ 7-day change
â€¢ Price chart

<b>3. All-Time High:</b>
Send /ath followed by coin symbol
Example: /ath sol

<b>4. Currency Converter:</b>
Send /convert followed by amount and coin
Example: /convert 20 ton

<b>ðŸ¦ Powered by @conesociety</b>"""
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    try:
        prices = await get_all_prices()
        if not prices:
            await message.answer("âŒ Failed to fetch prices. Please try again.")
            return
        
        img = await create_top_grid_async(prices)
        img_bytes = image_to_bytes(img)
        
        # Unique filename with timestamp to prevent caching
        import time
        filename = f"top_coins_{int(time.time())}.png"
        photo = BufferedInputFile(img_bytes.read(), filename=filename)
        
        # Build caption parts
        part1 = "ðŸª™ "
        part2 = "Top 8 Cryptocurrencies\n\n"
        part3 = "ðŸ¦ Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=PREMIUM_EMOJI_ID),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await send_photo_safe(message, photo, caption, entities)
        
    except Exception as e:
        logger.error(f"Error in /top: {e}")
        await message.answer("âŒ An error occurred. Please try again.")

async def handle_coin_command(message: types.Message, coin_symbol: str):
    try:
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"âŒ Failed to fetch {coin_symbol.upper()} data.")
            return
        
        chart_data = await get_price_chart(coin_symbol, days=7)
        
        img = await create_coin_card_async(coin_data, chart_data)
        img_bytes = image_to_bytes(img)
        
        # Unique filename with timestamp to prevent caching
        import time
        filename = f"{coin_symbol}_{int(time.time())}.png"
        photo = BufferedInputFile(img_bytes.read(), filename=filename)
        premium_id = coin_data.get('premium_emoji_id', PREMIUM_EMOJI_ID)
        logger.info(f"Using premium emoji ID for {coin_symbol}: {premium_id}")
        
        # Build caption parts
        part1 = "ðŸª™ "
        part2 = f"{coin_data['name']} ({coin_data['symbol']})\n\n"
        part3 = "ðŸ¦ Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await send_photo_safe(message, photo, caption, entities)
        
    except Exception as e:
        logger.error(f"Error in /{coin_symbol}: {e}")
        await message.answer("âŒ An error occurred. Please try again.")

@dp.message(Command("btc"))
async def cmd_btc(message: types.Message):
    await handle_coin_command(message, "btc")

@dp.message(Command("eth"))
async def cmd_eth(message: types.Message):
    await handle_coin_command(message, "eth")

@dp.message(Command("sol"))
async def cmd_sol(message: types.Message):
    await handle_coin_command(message, "sol")

@dp.message(Command("ton"))
async def cmd_ton(message: types.Message):
    await handle_coin_command(message, "ton")

@dp.message(Command("bnb"))
async def cmd_bnb(message: types.Message):
    await handle_coin_command(message, "bnb")

@dp.message(Command("xrp"))
async def cmd_xrp(message: types.Message):
    await handle_coin_command(message, "xrp")

@dp.message(Command("trx"))
async def cmd_trx(message: types.Message):
    await handle_coin_command(message, "trx")

@dp.message(Command("ltc"))
async def cmd_ltc(message: types.Message):
    await handle_coin_command(message, "ltc")

@dp.message(Command("crypto"))
async def cmd_crypto(message: types.Message):
    """Universal crypto command - supports ANY coin"""
    try:
        # Track user
        add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "âŒ <b>Invalid format!</b>\n\n"
                "<b>Usage:</b> /crypto &lt;symbol&gt;\n\n"
                "<b>Examples:</b>\n"
                "â€¢ /crypto doge\n"
                "â€¢ /crypto shib\n"
                "â€¢ /crypto ada\n"
                "â€¢ /crypto avax\n\n"
                "<b>Supports 1000+ coins from Binance!</b>",
                parse_mode="HTML"
            )
            return
        
        coin_symbol = args[1].lower()
        
        # Fetch coin data
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"âŒ Coin '{coin_symbol.upper()}' not found on Binance.\n\nMake sure the symbol is correct (e.g., 'doge' not 'dogecoin')")
            return
        
        chart_data = await get_price_chart(coin_symbol, days=7)
        
        img = await create_coin_card_async(coin_data, chart_data)
        img_bytes = image_to_bytes(img)
        
        # Unique filename with timestamp to prevent caching
        import time
        filename = f"{coin_symbol}_{int(time.time())}.png"
        photo = BufferedInputFile(img_bytes.read(), filename=filename)
        premium_id = coin_data.get('premium_emoji_id', PREMIUM_EMOJI_ID)
        
        # Build caption parts
        part1 = "ðŸª™ "
        part2 = f"{coin_data['name']} ({coin_data['symbol']})\n\n"
        part3 = "ðŸ¦ Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await send_photo_safe(message, photo, caption, entities)
        
    except Exception as e:
        logger.error(f"Error in /crypto: {e}")
        await message.answer("âŒ An error occurred. Please try again or check if the coin symbol is correct.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Admin only - bot statistics"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        stats = get_stats()
        
        stats_text = f"""ðŸ“Š <b>Bot Statistics</b>

<b>ðŸ‘¥ Users:</b>
â€¢ Total Users: {stats['total_users']}
â€¢ Total Commands: {stats['total_commands']}

<b>âš™ï¸ System:</b>
â€¢ Status: âœ… Running
â€¢ Supported Coins: {len(SUPPORTED_COINS)} + 1000+ via /crypto
â€¢ Update Interval: 30 seconds
â€¢ API: Binance (No rate limits)

<b>ðŸ“‹ Commands:</b>
â€¢ /top - Grid view
â€¢ /crypto &lt;symbol&gt; - Any coin
â€¢ Individual: /btc, /eth, /sol, etc.
â€¢ /ath &lt;coin&gt; - ATH info
â€¢ /convert &lt;amount&gt; &lt;coin&gt; - Converter

ðŸ¦ Powered by @conesociety"""
        
        await message.answer(stats_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in /stats: {e}")
        await message.answer(f"Error: {e}")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    """Admin only - broadcast message"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    await message.answer(
        "ðŸ“¢ <b>Broadcast Feature</b>\n\n"
        "This feature requires a user database.\n"
        "Would you like me to implement user tracking?",
        parse_mode="HTML"
    )

@dp.message(Command("health"))
async def cmd_health(message: types.Message):
    """Admin only - health checks for upstream APIs and bot state."""
    if message.from_user.id not in ADMIN_IDS:
        return

    async def check_get(session: aiohttp.ClientSession, url: str, timeout_sec: int = 6):
        started = asyncio.get_running_loop().time()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout_sec)) as response:
                elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)
                ok = 200 <= response.status < 300
                return ok, response.status, elapsed_ms, ""
        except Exception as exc:
            elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)
            return False, 0, elapsed_ms, str(exc)

    async def check_lcw(session: aiohttp.ClientSession, timeout_sec: int = 8):
        if not LIVECOINWATCH_API_KEY:
            return None, 0, 0, "not configured"

        started = asyncio.get_running_loop().time()
        url = "https://api.livecoinwatch.com/coins/single"
        headers = {"content-type": "application/json", "x-api-key": LIVECOINWATCH_API_KEY}
        payload = {"currency": "USD", "code": "BTC", "meta": False}
        try:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=timeout_sec)) as response:
                elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)
                ok = 200 <= response.status < 300
                return ok, response.status, elapsed_ms, ""
        except Exception as exc:
            elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)
            return False, 0, elapsed_ms, str(exc)

    try:
        stats = get_stats()

        async with aiohttp.ClientSession() as session:
            binance_ping = await check_get(session, "https://api.binance.com/api/v3/ping")
            binance_ticker = await check_get(session, "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT")
            coingecko_ping = await check_get(session, "https://api.coingecko.com/api/v3/ping")
            livecoinwatch_ping = await check_lcw(session)

        def fmt_status(label: str, probe):
            ok, status, ms, err = probe
            icon = "âœ…" if ok else "âŒ"
            if err:
                return f"â€¢ {label}: {icon} status={status or 'ERR'} ({ms}ms) - {err}"
            return f"â€¢ {label}: {icon} status={status} ({ms}ms)"

        last_update = "never"
        if binance_updater.last_update:
            last_update = binance_updater.last_update.isoformat()

        health_lines = [
            "ðŸ©º <b>Bot Health</b>",
            "",
            f"â€¢ Checked At (UTC): {datetime.now(timezone.utc).isoformat()}",
            f"â€¢ Updater Running: {'âœ…' if binance_updater.is_running else 'âŒ'}",
            f"â€¢ Last Price Cache Update: {last_update}",
            f"â€¢ Cached Prices: {len(binance_updater.get_all_prices())}",
            f"â€¢ Cached Charts: {len(binance_updater.chart_data)}",
            f"â€¢ Active Alerts: {len(get_active_alerts())}",
            f"â€¢ Total Users: {stats.get('total_users', 0)}",
            f"â€¢ Total Commands: {stats.get('total_commands', 0)}",
            "",
            "<b>Upstream APIs</b>",
            fmt_status("Binance /ping", binance_ping),
            fmt_status("Binance BTC ticker", binance_ticker),
            fmt_status("CoinGecko /ping", coingecko_ping),
        ]

        if livecoinwatch_ping[0] is None:
            health_lines.append("â€¢ LiveCoinWatch: âšª not configured")
        else:
            health_lines.append(fmt_status("LiveCoinWatch BTC", livecoinwatch_ping))

        await message.answer("\n".join(health_lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in /health: {e}")
        await message.answer("âŒ Failed to run health checks.")

@dp.message(Command("alerts"))
async def cmd_alerts(message: types.Message):
    """List active alerts for current user."""
    try:
        add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        alerts = list_user_alerts(message.from_user.id, only_active=True)
        if not alerts:
            await message.answer(
                "📋 <b>Your active alerts: 0</b>\n\n"
                "Create one with:\n"
                "<code>/alert btc 70000</code>",
                parse_mode="HTML",
            )
            return

        lines = ["📋 <b>Your Active Alerts</b>", ""]
        for a in alerts:
            lines.append(
                f"• ID <code>{a['id']}</code> | <b>{a['coin_symbol'].upper()}</b> "
                f"{a['direction']} <b>${a['target_price']:,.6f}</b>"
            )
        lines.append("")
        lines.append("Delete one: <code>/alert delete 3</code>")
        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in /alerts: {e}")
        await message.answer("❌ Failed to fetch alerts.")

@dp.message(Command("alert"))
async def cmd_alert(message: types.Message):
    """Create/delete alerts with easy syntax."""
    try:
        add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "🔔 <b>Price Alert</b>\n\n"
                "<b>Create:</b> <code>/alert btc 70000</code>\n"
                "<b>Create (explicit):</b> <code>/alert btc 70000 above</code>\n"
                "<b>Delete:</b> <code>/alert delete 3</code>\n"
                "<b>Clear all:</b> <code>/alert clear</code>\n"
                "<b>List:</b> <code>/alerts</code>\n\n"
                "Works for all valid coin symbols.",
                parse_mode="HTML",
            )
            return

        if args[1].lower() == "clear":
            deleted_count = clear_user_alerts(message.from_user.id, only_active=True)
            await message.answer(
                f"✅ Cleared <b>{deleted_count}</b> active alert(s).",
                parse_mode="HTML",
            )
            return

        if args[1].lower() == "delete":
            if len(args) < 3:
                await message.answer("❌ Usage: <code>/alert delete 3</code>", parse_mode="HTML")
                return
            try:
                alert_id = int(args[2])
            except ValueError:
                await message.answer("❌ Alert ID must be a number.")
                return

            deleted = delete_user_alert(message.from_user.id, alert_id)
            if deleted:
                await message.answer(f"✅ Alert <code>{alert_id}</code> deleted.", parse_mode="HTML")
            else:
                await message.answer("❌ Alert not found (or not yours).")
            return

        if len(args) < 3:
            await message.answer(
                "❌ Usage: <code>/alert btc 70000</code>\n"
                "or <code>/alert btc 70000 above</code>",
                parse_mode="HTML",
            )
            return

        symbol = args[1].lower().strip()
        try:
            target_price = float(args[2].replace(",", ""))
            if target_price <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ Invalid target price. Example: <code>/alert btc 70000</code>", parse_mode="HTML")
            return

        coin_data = await get_coin_price(symbol)
        if not coin_data:
            await message.answer(
                f"❌ Coin <b>{symbol.upper()}</b> not found.\n"
                "Use valid symbol like btc, eth, ton, doge, pepe...",
                parse_mode="HTML",
            )
            return

        current_price = float(coin_data.get("price", 0))
        if current_price <= 0:
            await message.answer("❌ Unable to fetch current price. Try again in a moment.")
            return

        explicit_direction = None
        if len(args) >= 4:
            direction_arg = args[3].strip().lower()
            direction_map = {
                "above": "above",
                "up": "above",
                "gt": "above",
                "below": "below",
                "down": "below",
                "lt": "below",
            }
            explicit_direction = direction_map.get(direction_arg)
            if not explicit_direction:
                await message.answer(
                    "❌ Invalid direction. Use <code>above</code> or <code>below</code>.\n"
                    "Example: <code>/alert btc 70000 above</code>",
                    parse_mode="HTML",
                )
                return

        direction = explicit_direction or ("above" if current_price < target_price else "below")

        user_active_alerts = list_user_alerts(message.from_user.id, only_active=True)
        if len(user_active_alerts) >= 20:
            await message.answer("❌ Max 20 active alerts allowed per user.")
            return

        for a in user_active_alerts:
            if (
                a["coin_symbol"] == symbol
                and float(a["target_price"]) == float(target_price)
                and a["direction"] == direction
            ):
                await message.answer("⚠️ Same alert already exists.")
                return

        new_alert = create_alert(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            coin_symbol=symbol,
            target_price=target_price,
            direction=direction,
            created_price=current_price,
        )

        await message.answer(
            "✅ <b>Alert created</b>\n\n"
            f"• ID: <code>{new_alert['id']}</code>\n"
            f"• Coin: <b>{symbol.upper()}</b>\n"
            f"• Current: <b>${current_price:,.6f}</b>\n"
            f"• Target: <b>${target_price:,.6f}</b>\n"
            f"• Direction: <b>{direction}</b>\n\n"
            "View all: <code>/alerts</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error in /alert: {e}")
        await message.answer("❌ Failed to create alert.")

@dp.message(Command("ath"))
async def cmd_ath(message: types.Message):
    """ATH command - supports ANY coin from Binance"""
    try:
        # Track user
        add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "âŒ <b>Invalid format!</b>\n\n"
                "<b>Usage:</b> /ath &lt;coin&gt;\n\n"
                "<b>Examples:</b>\n"
                "â€¢ /ath sol\n"
                "â€¢ /ath btc\n"
                "â€¢ /ath eth\n"
                "â€¢ /ath doge\n"
                "â€¢ /ath sui\n\n"
                "<b>Supports 1000+ coins from Binance!</b>",
                parse_mode="HTML"
            )
            return
        
        coin_symbol = args[1].lower()
        
        # Fetch coin data (works for any coin)
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"âŒ Coin '{coin_symbol.upper()}' not found on Binance.\n\nMake sure the symbol is correct (e.g., 'doge' not 'dogecoin')")
            return
        
        img = await create_ath_card_async(coin_data)
        img_bytes = image_to_bytes(img)
        
        # Unique filename with timestamp to prevent caching
        import time
        filename = f"{coin_symbol}_ath_{int(time.time())}.png"
        photo = BufferedInputFile(img_bytes.read(), filename=filename)
        premium_id = coin_data.get('premium_emoji_id', PREMIUM_EMOJI_ID)
        
        # Build caption parts
        part1 = "ðŸª™ "
        part2 = f"{coin_data['name']} All-Time High\n\n"
        part3 = "ðŸ¦ Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await send_photo_safe(message, photo, caption, entities)
        
    except Exception as e:
        logger.error(f"Error in /ath: {e}")
        await message.answer("âŒ An error occurred. Please try again or check if the coin symbol is correct.")

@dp.message(Command("convert"))
async def cmd_convert(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.answer(
                "âŒ <b>Invalid format!</b>\n\n"
                "<b>Usage:</b> /convert &lt;amount&gt; &lt;coin&gt;\n\n"
                "<b>Examples:</b>\n"
                "â€¢ /convert 20 ton\n"
                "â€¢ /convert 0.5 btc\n"
                "â€¢ /convert 100 xrp\n\n"
                "<b>Supported coins:</b> btc, eth, sol, ton, bnb, xrp, trx, ltc",
                parse_mode="HTML"
            )
            return
        
        try:
            amount = float(args[1])
        except ValueError:
            await message.answer("âŒ Invalid amount. Please enter a valid number.")
            return
        
        coin_symbol = args[2].lower()
        if coin_symbol not in SUPPORTED_COINS:
            await message.answer(
                f"âŒ <b>Unsupported coin!</b>\n\n"
                f"<b>Supported coins:</b> {', '.join(SUPPORTED_COINS.keys())}",
                parse_mode="HTML"
            )
            return
        
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"âŒ Failed to fetch {coin_symbol.upper()} data. Please try again.")
            return
        
        img = await create_convert_card_async(coin_data, amount)
        img_bytes = image_to_bytes(img)
        
        # Unique filename with timestamp to prevent caching
        import time
        filename = f"convert_{coin_symbol}_{int(time.time())}.png"
        photo = BufferedInputFile(img_bytes.read(), filename=filename)
        usd_value = amount * coin_data['price']
        premium_id = coin_data.get('premium_emoji_id', PREMIUM_EMOJI_ID)
        
        # Build caption parts
        part1 = "ðŸª™ "
        part2 = f"{amount} {coin_data['symbol']} = ${usd_value:,.2f} USD\n\n"
        part3 = "ðŸ¦ Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await send_photo_safe(message, photo, caption, entities)
        
    except Exception as e:
        logger.error(f"Error in /convert: {e}")
        await message.answer("âŒ An error occurred. Please try again.")

@dp.message(Command("price"))
async def cmd_price(message: types.Message):
    """Quick price check command"""
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "âŒ <b>Usage:</b> /price &lt;coin&gt;\n\n"
                "<b>Example:</b> /price btc\n\n"
                "Or use individual commands like /btc for detailed cards!",
                parse_mode="HTML"
            )
            return
        
        coin_symbol = args[1].lower()
        if coin_symbol not in SUPPORTED_COINS:
            await message.answer(
                f"âŒ <b>Unsupported coin!</b>\n\n"
                f"<b>Supported:</b> {', '.join(SUPPORTED_COINS.keys())}",
                parse_mode="HTML"
            )
            return
        
        await handle_coin_command(message, coin_symbol)
        
    except Exception as e:
        logger.error(f"Error in /price: {e}")
        await message.answer("âŒ An error occurred. Please try again.")

@dp.message()
async def handle_unknown(message: types.Message):
    """Handle unknown messages"""
    if not message.text:
        return

    # Do not spam groups when users run commands for other bots/admin tools.
    if message.chat.type != "private":
        return

    text = message.text.strip()
    if text in {"/", "//"}:
        return

    if text.startswith('/'):
        await message.answer(
            "â“ <b>Unknown command!</b>\n\n"
            "Send /start to see all available commands.\n"
            "Send /help for detailed instructions.\n"
            "Try /crypto &lt;symbol&gt; for any cryptocurrency!\n\n"
            "ðŸ¦ Powered by @conesociety",
            parse_mode="HTML"
        )

async def main():
    logger.info("Starting Cone Price Bot...")
    
    # Start Binance background updater (30 sec - no rate limit!)
    asyncio.create_task(binance_updater.start(update_interval=30))
    asyncio.create_task(alert_monitor_loop())
    
    await set_bot_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
