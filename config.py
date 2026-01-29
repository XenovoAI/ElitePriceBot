import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8232424140:AAFMGt41gheLHQ7XAJgks5wOOcuY_aom6Ls")
if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
    BOT_TOKEN = "8232424140:AAFMGt41gheLHQ7XAJgks5wOOcuY_aom6Ls"
COINGECKO_API = "https://api.coingecko.com/api/v3"
CACHE_TTL = 15  # Reduced to 15 seconds for faster updates

SUPPORTED_COINS = {
    "btc": {
        "id": "bitcoin", 
        "name": "Bitcoin", 
        "symbol": "BTC", 
        "color": "#F7931A",
        "logo_url": "https://cryptologos.cc/logos/bitcoin-btc-logo.png"
    },
    "eth": {
        "id": "ethereum", 
        "name": "Ethereum", 
        "symbol": "ETH", 
        "color": "#627EEA",
        "logo_url": "https://cryptologos.cc/logos/ethereum-eth-logo.png"
    },
    "sol": {
        "id": "solana", 
        "name": "Solana", 
        "symbol": "SOL", 
        "color": "#14F195",
        "logo_url": "https://cryptologos.cc/logos/solana-sol-logo.png"
    },
    "ton": {
        "id": "the-open-network", 
        "name": "Toncoin", 
        "symbol": "TON", 
        "color": "#0088CC",
        "logo_url": "https://cryptologos.cc/logos/toncoin-ton-logo.png"
    },
    "bnb": {
        "id": "binancecoin", 
        "name": "BNB", 
        "symbol": "BNB", 
        "color": "#F3BA2F",
        "logo_url": "https://cryptologos.cc/logos/bnb-bnb-logo.png"
    },
    "xrp": {
        "id": "ripple", 
        "name": "XRP", 
        "symbol": "XRP", 
        "color": "#23292F",
        "logo_url": "https://cryptologos.cc/logos/xrp-xrp-logo.png"
    },
    "trx": {
        "id": "tron", 
        "name": "TRON", 
        "symbol": "TRX", 
        "color": "#FF0013",
        "logo_url": "https://cryptologos.cc/logos/tron-trx-logo.png"
    },
    "ltc": {
        "id": "litecoin", 
        "name": "Litecoin", 
        "symbol": "LTC", 
        "color": "#345D9D",
        "logo_url": "https://cryptologos.cc/logos/litecoin-ltc-logo.png"
    }
}

WATERMARK = "Powered by @minielite"
