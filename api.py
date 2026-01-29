import aiohttp
import asyncio
from datetime import datetime, timedelta
from config import COINGECKO_API, CACHE_TTL, SUPPORTED_COINS

class PriceCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key):
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=CACHE_TTL):
                return self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

cache = PriceCache()

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None

async def get_coin_price(coin_symbol):
    cached = cache.get(f"price_{coin_symbol}")
    if cached:
        return cached
    
    coin_info = SUPPORTED_COINS.get(coin_symbol.lower())
    if not coin_info:
        return None
    
    coin_id = coin_info["id"]
    url = f"{COINGECKO_API}/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
    
    data = await fetch_json(url)
    if not data:
        return None
    
    result = {
        "symbol": coin_info["symbol"],
        "name": coin_info["name"],
        "price": data["market_data"]["current_price"]["usd"],
        "change_24h": data["market_data"]["price_change_percentage_24h"],
        "change_7d": data["market_data"]["price_change_percentage_7d"],
        "ath": data["market_data"]["ath"]["usd"],
        "ath_date": data["market_data"]["ath_date"]["usd"],
        "color": coin_info["color"],
        "logo_url": coin_info.get("logo_url")
    }
    
    cache.set(f"price_{coin_symbol}", result)
    return result

async def get_all_prices():
    cached = cache.get("all_prices")
    if cached:
        return cached
    
    coin_ids = ",".join([info["id"] for info in SUPPORTED_COINS.values()])
    url = f"{COINGECKO_API}/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_change=true"
    
    data = await fetch_json(url)
    if not data:
        return None
    
    result = {}
    for symbol, info in SUPPORTED_COINS.items():
        coin_id = info["id"]
        if coin_id in data:
            result[symbol] = {
                "symbol": info["symbol"],
                "name": info["name"],
                "price": data[coin_id]["usd"],
                "change_24h": data[coin_id].get("usd_24h_change", 0),
                "color": info["color"],
                "logo_url": info.get("logo_url")
            }
    
    cache.set("all_prices", result)
    return result

async def get_price_chart(coin_symbol, days=7):
    cached = cache.get(f"chart_{coin_symbol}_{days}")
    if cached:
        return cached
    
    coin_info = SUPPORTED_COINS.get(coin_symbol.lower())
    if not coin_info:
        return None
    
    coin_id = coin_info["id"]
    url = f"{COINGECKO_API}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    
    data = await fetch_json(url)
    if not data or "prices" not in data:
        return None
    
    prices = [price[1] for price in data["prices"]]
    cache.set(f"chart_{coin_symbol}_{days}", prices)
    return prices
