# Cone Price Bot 🍦

A production-ready Telegram bot that generates beautiful crypto price cards for @conesociety.

## Features

✨ **Beautiful Image Cards** - Professional trading app style
📊 **Top 8 Coins Grid** - BTC, ETH, SOL, TON, BNB, XRP, TRX, LTC
💎 **Individual Coin Cards** - Detailed price info with 7-day charts
🏆 **All-Time High Tracking** - ATH prices and dates
💱 **Currency Converter** - Convert crypto to USD
⚡ **Fast & Cached** - 15-second cache to avoid API spam
🎨 **Branded** - Every image includes "Powered by @conesociety"

## Commands

- `/start` - Welcome message
- `/top` - Top 8 coins grid
- `/btc`, `/eth`, `/sol`, `/ton`, `/bnb`, `/xrp`, `/trx`, `/ltc` - Individual coin cards
- `/ath <coin>` - All-time high info (e.g., `/ath sol`)
- `/convert <amount> <coin>` - Convert to USD (e.g., `/convert 20 ton`)

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ConePriceBot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the bot

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your bot token:

```
BOT_TOKEN=your_telegram_bot_token_here
```

### 4. Get your bot token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Set username to `@ConePriceBot` (or your preferred name)
4. Copy the token and paste it in `.env`

### 5. Run the bot

```bash
python bot.py
```

## VPS Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/conepricebot.service`:

```ini
[Unit]
Description=Cone Price Bot Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ConePriceBot
ExecStart=/usr/bin/python3 /path/to/ConePriceBot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable conepricebot
sudo systemctl start conepricebot
sudo systemctl status conepricebot
```

### Using screen (Quick method)

```bash
screen -S conepricebot
python bot.py
# Press Ctrl+A then D to detach
```

Reattach later:

```bash
screen -r conepricebot
```

## Project Structure

```
ConePriceBot/
├── bot.py              # Main bot logic
├── api.py              # CoinGecko API integration
├── image_engine.py     # Image generation with Pillow
├── config.py           # Configuration and constants
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── .env.example       # Example environment file
└── README.md          # This file
```

## Tech Stack

- **Python 3.8+**
- **Aiogram 3.x** - Modern async Telegram bot framework
- **Pillow** - Image generation
- **aiohttp** - Async HTTP requests
- **CoinGecko API** - Free crypto price data (no API key required)

## Customization

### Add more coins

Edit `config.py` and add to `SUPPORTED_COINS`:

```python
"doge": {"id": "dogecoin", "name": "Dogecoin", "symbol": "DOGE", "color": "#C2A633"}
```

### Change cache duration

Edit `config.py`:

```python
CACHE_TTL = 60  # 60 seconds
```

### Customize watermark

Edit `config.py`:

```python
WATERMARK = "Powered by @conesociety"
```

## Troubleshooting

### Bot doesn't respond

- Check if bot token is correct in `.env`
- Verify bot is running: `ps aux | grep bot.py`
- Check logs for errors

### Images look wrong

- Ensure Pillow is installed: `pip install Pillow`
- On Linux, install font support: `sudo apt-get install fonts-dejavu-core`

### API errors

- CoinGecko has rate limits (50 calls/minute)
- Cache helps reduce API calls
- Wait a minute and try again

## License

MIT License - Feel free to modify and use for your projects.

## Support

For issues or questions, contact @conesociety on Telegram.

---

**🍦 Powered by @conesociety**
