import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = "8595180062:AAH2wZNeUZV382OdE3ihp_1rlbEz4fLllSg"
COINGECKO_API = "https://api.coingecko.com/api/v3"
CACHE_TTL = 15

SUPPORTED_COINS = {
    "btc": {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC", "color": "#F7931A", "logo_url": "https://cryptologos.cc/logos/bitcoin-btc-logo.png", "premium_emoji_id": "5388686391578220236"},
    "eth": {"id": "ethereum", "name": "Ethereum", "symbol": "ETH", "color": "#627EEA", "logo_url": "https://cryptologos.cc/logos/ethereum-eth-logo.png", "premium_emoji_id": "5388638837700319668"},
    "sol": {"id": "solana", "name": "Solana", "symbol": "SOL", "color": "#14F195", "logo_url": "https://cryptologos.cc/logos/solana-sol-logo.png", "premium_emoji_id": "5389021583710899362"},
    "ton": {"id": "the-open-network", "name": "Toncoin", "symbol": "TON", "color": "#0088CC", "logo_url": "https://cryptologos.cc/logos/toncoin-ton-logo.png", "premium_emoji_id": "5391167177573292334"},
    "bnb": {"id": "binancecoin", "name": "BNB", "symbol": "BNB", "color": "#F3BA2F", "logo_url": "https://cryptologos.cc/logos/bnb-bnb-logo.png", "premium_emoji_id": "5228950845533485175"},
    "xrp": {"id": "ripple", "name": "XRP", "symbol": "XRP", "color": "#23292F", "logo_url": "https://cryptologos.cc/logos/xrp-xrp-logo.png", "premium_emoji_id": "5199595061892904764"},
    "trx": {"id": "tron", "name": "TRON", "symbol": "TRX", "color": "#FF0013", "logo_url": "https://cryptologos.cc/logos/tron-trx-logo.png", "premium_emoji_id": "5199957196355438361"},
    "ltc": {"id": "litecoin", "name": "Litecoin", "symbol": "LTC", "color": "#345D9D", "logo_url": "https://cryptologos.cc/logos/litecoin-ltc-logo.png", "premium_emoji_id": "5413588448751670447"}
}

PREMIUM_EMOJI_ID = "5368324170671202286"
ICE_CREAM_EMOJI_ID = "6068790288191593780"
WATERMARK = "Powered by @conesociety"

ADMIN_IDS = [6369434417]

DEFAULT_COIN_COLOR = "#888888"
DEFAULT_LOGO_URL = "https://cryptologos.cc/logos/generic-crypto-logo.png"
DEFAULT_PREMIUM_EMOJI_ID = "5368324170671202286"
