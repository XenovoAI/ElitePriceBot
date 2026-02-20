# LiveCoinWatch API Setup

The bot now uses LiveCoinWatch API for accurate ATH (All-Time High) data instead of CoinGecko.

## Why LiveCoinWatch?
- **Free tier**: 10,000 requests per day
- **No rate limiting issues**: Unlike CoinGecko which heavily rate limits
- **Accurate ATH data**: Provides `allTimeHighUSD` for all coins
- **Fast and reliable**: Better uptime and response times

## Setup Instructions

### 1. Get Your Free API Key

1. Go to https://www.livecoinwatch.com/tools/api
2. Sign up for a free account
3. Copy your API key from the dashboard

### 2. Add API Key to .env File

Open your `.env` file and add:

```bash
LIVECOINWATCH_API_KEY=your_api_key_here
```

### 3. Restart the Bot

```bash
sudo systemctl restart conebot
```

### 4. Test It

Try any ATH command:
```
/ath ton
/ath btc
/ath sol
```

You should now see accurate ATH data in the logs:
```
✅ Got real ATH from LiveCoinWatch for TON: $8.25000000
```

## Supported Coins

The bot automatically maps coin symbols to LiveCoinWatch codes:
- **TON** → TONCOIN (special mapping)
- **BTC, ETH, SOL, BNB, XRP, etc.** → Direct mapping
- **1000+ coins** supported from Binance

## Troubleshooting

### "No LiveCoinWatch API key configured"
- Make sure you added `LIVECOINWATCH_API_KEY` to your `.env` file
- Restart the bot after adding the key

### "LiveCoinWatch API key invalid"
- Double-check your API key is correct
- Make sure there are no extra spaces in the `.env` file

### "Coin not found on LiveCoinWatch"
- The bot will automatically retry with the uppercase symbol
- If still failing, the coin might not be on LiveCoinWatch
- Fallback ATH (2x current price) will be used

## Fallback Behavior

If LiveCoinWatch fails or API key is missing:
- ATH Price: 2x current price (better than nothing)
- ATH Date: January 1, 2021 (placeholder)

This ensures the bot always works, even without the API key!
