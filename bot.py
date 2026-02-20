import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, BotCommand, MessageEntity
from config import BOT_TOKEN, SUPPORTED_COINS, PREMIUM_EMOJI_ID, ICE_CREAM_EMOJI_ID, ADMIN_IDS
from api import get_coin_price, get_all_prices, get_price_chart
from binance_api import binance_updater
from image_engine import (
    create_top_grid_async, create_coin_card_async, create_ath_card_async, 
    create_convert_card_async, image_to_bytes
)
from database import add_user, get_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def set_bot_commands():
    """Set bot commands menu"""
    commands = [
        BotCommand(command="start", description="🚀 Start the bot"),
        BotCommand(command="help", description="📖 Help & instructions"),
        BotCommand(command="top", description="📊 Top 8 coins grid"),
        BotCommand(command="btc", description="₿ Bitcoin price"),
        BotCommand(command="eth", description="Ξ Ethereum price"),
        BotCommand(command="sol", description="◎ Solana price"),
        BotCommand(command="ton", description="💎 Toncoin price"),
        BotCommand(command="bnb", description="🔶 BNB price"),
        BotCommand(command="xrp", description="✕ XRP price"),
        BotCommand(command="trx", description="⚡ TRON price"),
        BotCommand(command="ltc", description="Ł Litecoin price"),
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Track user
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    welcome_text = """🚀 <b>Welcome to Cone Price Bot!</b>

Get beautiful crypto price cards instantly.

<b>📊 Available Commands:</b>

<b>Price Cards:</b>
• /top - View top 8 coins in a grid
• /crypto &lt;symbol&gt; - ANY cryptocurrency!
• /btc, /eth, /sol, /ton, /bnb, /xrp, /trx, /ltc

<b>Advanced:</b>
• /ath &lt;coin&gt; - All-time high info
• /convert &lt;amount&gt; &lt;coin&gt; - Convert to USD

<b>Examples:</b>
• /crypto doge
• /crypto shib
• /crypto ada

<b>🍦 Powered by @conesociety</b>
<b>Supports 1000+ coins from Binance!</b>"""
    await message.answer(welcome_text, parse_mode="HTML")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """<b>📖 Cone Price Bot Help</b>

<b>How to use:</b>

<b>1. View All Coins:</b>
Send /top to see a beautiful grid of all 8 supported cryptocurrencies with live prices and 24h changes.

<b>2. Individual Coin Cards:</b>
• /btc - ₿ Bitcoin
• /eth - Ξ Ethereum
• /sol - ◎ Solana
• /ton - 💎 Toncoin
• /bnb - 🔶 BNB
• /xrp - ✕ XRP
• /trx - ⚡ TRON
• /ltc - Ł Litecoin

Each card shows:
• Current price
• 24h change
• 7-day change
• Price chart

<b>3. All-Time High:</b>
Send /ath followed by coin symbol
Example: /ath sol

<b>4. Currency Converter:</b>
Send /convert followed by amount and coin
Example: /convert 20 ton

<b>🍦 Powered by @conesociety</b>"""
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    try:
        prices = await get_all_prices()
        if not prices:
            await message.answer("❌ Failed to fetch prices. Please try again.")
            return
        
        img = await create_top_grid_async(prices)
        img_bytes = image_to_bytes(img)
        
        # Unique filename with timestamp to prevent caching
        import time
        filename = f"top_coins_{int(time.time())}.png"
        photo = BufferedInputFile(img_bytes.read(), filename=filename)
        
        # Build caption parts
        part1 = "🪙 "
        part2 = "Top 8 Cryptocurrencies\n\n"
        part3 = "🍦 Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=PREMIUM_EMOJI_ID),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await message.answer_photo(photo, caption=caption, caption_entities=entities)
        
    except Exception as e:
        logger.error(f"Error in /top: {e}")
        await message.answer("❌ An error occurred. Please try again.")

async def handle_coin_command(message: types.Message, coin_symbol: str):
    try:
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"❌ Failed to fetch {coin_symbol.upper()} data.")
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
        part1 = "🪙 "
        part2 = f"{coin_data['name']} ({coin_data['symbol']})\n\n"
        part3 = "🍦 Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await message.answer_photo(photo, caption=caption, caption_entities=entities)
        
    except Exception as e:
        logger.error(f"Error in /{coin_symbol}: {e}")
        await message.answer("❌ An error occurred. Please try again.")

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
                "❌ <b>Invalid format!</b>\n\n"
                "<b>Usage:</b> /crypto &lt;symbol&gt;\n\n"
                "<b>Examples:</b>\n"
                "• /crypto doge\n"
                "• /crypto shib\n"
                "• /crypto ada\n"
                "• /crypto avax\n\n"
                "<b>Supports 1000+ coins from Binance!</b>",
                parse_mode="HTML"
            )
            return
        
        coin_symbol = args[1].lower()
        
        # Fetch coin data
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"❌ Coin '{coin_symbol.upper()}' not found on Binance.\n\nMake sure the symbol is correct (e.g., 'doge' not 'dogecoin')")
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
        part1 = "🪙 "
        part2 = f"{coin_data['name']} ({coin_data['symbol']})\n\n"
        part3 = "🍦 Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await message.answer_photo(photo, caption=caption, caption_entities=entities)
        
    except Exception as e:
        logger.error(f"Error in /crypto: {e}")
        await message.answer("❌ An error occurred. Please try again or check if the coin symbol is correct.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Admin only - bot statistics"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        stats = get_stats()
        
        stats_text = f"""📊 <b>Bot Statistics</b>

<b>👥 Users:</b>
• Total Users: {stats['total_users']}
• Total Commands: {stats['total_commands']}

<b>⚙️ System:</b>
• Status: ✅ Running
• Supported Coins: {len(SUPPORTED_COINS)} + 1000+ via /crypto
• Update Interval: 30 seconds
• API: Binance (No rate limits)

<b>📋 Commands:</b>
• /top - Grid view
• /crypto &lt;symbol&gt; - Any coin
• Individual: /btc, /eth, /sol, etc.
• /ath &lt;coin&gt; - ATH info
• /convert &lt;amount&gt; &lt;coin&gt; - Converter

🍦 Powered by @conesociety"""
        
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
        "📢 <b>Broadcast Feature</b>\n\n"
        "This feature requires a user database.\n"
        "Would you like me to implement user tracking?",
        parse_mode="HTML"
    )

@dp.message(Command("ath"))
async def cmd_ath(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Invalid format!</b>\n\n"
                "<b>Usage:</b> /ath &lt;coin&gt;\n\n"
                "<b>Examples:</b>\n"
                "• /ath sol\n"
                "• /ath btc\n"
                "• /ath eth\n\n"
                "<b>Supported coins:</b> btc, eth, sol, ton, bnb, xrp, trx, ltc",
                parse_mode="HTML"
            )
            return
        
        coin_symbol = args[1].lower()
        if coin_symbol not in SUPPORTED_COINS:
            await message.answer(
                f"❌ <b>Unsupported coin!</b>\n\n"
                f"<b>Supported coins:</b> {', '.join(SUPPORTED_COINS.keys())}",
                parse_mode="HTML"
            )
            return
        
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"❌ Failed to fetch {coin_symbol.upper()} data. Please try again.")
            return
        
        img = await create_ath_card_async(coin_data)
        img_bytes = image_to_bytes(img)
        
        # Unique filename with timestamp to prevent caching
        import time
        filename = f"{coin_symbol}_ath_{int(time.time())}.png"
        photo = BufferedInputFile(img_bytes.read(), filename=filename)
        premium_id = coin_data.get('premium_emoji_id', PREMIUM_EMOJI_ID)
        
        # Build caption parts
        part1 = "🪙 "
        part2 = f"{coin_data['name']} All-Time High\n\n"
        part3 = "🍦 Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await message.answer_photo(photo, caption=caption, caption_entities=entities)
        
    except Exception as e:
        logger.error(f"Error in /ath: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("convert"))
async def cmd_convert(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.answer(
                "❌ <b>Invalid format!</b>\n\n"
                "<b>Usage:</b> /convert &lt;amount&gt; &lt;coin&gt;\n\n"
                "<b>Examples:</b>\n"
                "• /convert 20 ton\n"
                "• /convert 0.5 btc\n"
                "• /convert 100 xrp\n\n"
                "<b>Supported coins:</b> btc, eth, sol, ton, bnb, xrp, trx, ltc",
                parse_mode="HTML"
            )
            return
        
        try:
            amount = float(args[1])
        except ValueError:
            await message.answer("❌ Invalid amount. Please enter a valid number.")
            return
        
        coin_symbol = args[2].lower()
        if coin_symbol not in SUPPORTED_COINS:
            await message.answer(
                f"❌ <b>Unsupported coin!</b>\n\n"
                f"<b>Supported coins:</b> {', '.join(SUPPORTED_COINS.keys())}",
                parse_mode="HTML"
            )
            return
        
        coin_data = await get_coin_price(coin_symbol)
        if not coin_data:
            await message.answer(f"❌ Failed to fetch {coin_symbol.upper()} data. Please try again.")
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
        part1 = "🪙 "
        part2 = f"{amount} {coin_data['symbol']} = ${usd_value:,.2f} USD\n\n"
        part3 = "🍦 Powered by @conesociety"
        caption = part1 + part2 + part3
        
        # Calculate UTF-16 offset for ice cream emoji
        ice_cream_offset = len(part1.encode('utf-16-le')) // 2 + len(part2.encode('utf-16-le')) // 2
        
        # Create custom emoji entities
        entities = [
            MessageEntity(type="custom_emoji", offset=0, length=2, custom_emoji_id=premium_id),
            MessageEntity(type="custom_emoji", offset=ice_cream_offset, length=2, custom_emoji_id=ICE_CREAM_EMOJI_ID)
        ]
        
        await message.answer_photo(photo, caption=caption, caption_entities=entities)
        
    except Exception as e:
        logger.error(f"Error in /convert: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message(Command("price"))
async def cmd_price(message: types.Message):
    """Quick price check command"""
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "❌ <b>Usage:</b> /price &lt;coin&gt;\n\n"
                "<b>Example:</b> /price btc\n\n"
                "Or use individual commands like /btc for detailed cards!",
                parse_mode="HTML"
            )
            return
        
        coin_symbol = args[1].lower()
        if coin_symbol not in SUPPORTED_COINS:
            await message.answer(
                f"❌ <b>Unsupported coin!</b>\n\n"
                f"<b>Supported:</b> {', '.join(SUPPORTED_COINS.keys())}",
                parse_mode="HTML"
            )
            return
        
        await handle_coin_command(message, coin_symbol)
        
    except Exception as e:
        logger.error(f"Error in /price: {e}")
        await message.answer("❌ An error occurred. Please try again.")

@dp.message()
async def handle_unknown(message: types.Message):
    """Handle unknown messages"""
    if message.text and message.text.startswith('/'):
        await message.answer(
            "❓ <b>Unknown command!</b>\n\n"
            "Send /start to see all available commands.\n"
            "Send /help for detailed instructions.\n"
            "Try /crypto &lt;symbol&gt; for any cryptocurrency!\n\n"
            "🍦 Powered by @conesociety",
            parse_mode="HTML"
        )

async def main():
    logger.info("Starting Cone Price Bot...")
    
    # Start Binance background updater (30 sec - no rate limit!)
    asyncio.create_task(binance_updater.start(update_interval=30))
    
    await set_bot_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
