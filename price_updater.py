import asyncio
import aiohttp
import logging
from datetime import datetime
from config import COINGECKO_API, SUPPORTED_COINS

logger = logging.getLogger(__name__)

class PriceUpdater:
    def __init__(self):
        self.prices = {}
        self.coin_details = {}
        self.chart_data = {}
        self.last_update = None
        self.is_running = False
    
    async def fetch_all_prices(self):
        """Fetch all coin prices from CoinGecko"""
        try:
            coin_ids = ",".join([info["id"] for info in SUPPORTED_COINS.values()])
            url = f"{COINGECKO_API}/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_change=true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
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
                        
                        self.prices = result
                        self.last_update = datetime.now()
                        logger.info(f"✅ Prices updated: {len(result)} coins")
                        return True
                    else:
                        logger.error(f"❌ API error: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Failed to fetch prices: {e}")
            return False
    
    async def fetch_all_data(self):
        """Fetch all prices, details, and charts in parallel"""
        try:
            # Fetch basic prices first
            success = await self.fetch_all_prices()
            if not success:
                logger.warning("⚠️ Using cached data")
                return
            
            # Add delay to avoid rate limit
            await asyncio.sleep(2)
            
            # Fetch details and charts for all coins in parallel (with limit)
            for symbol in SUPPORTED_COINS.keys():
                await self.fetch_and_cache_coin_details(symbol)
                await asyncio.sleep(0.5)  # Small delay between requests
            
            await asyncio.sleep(1)
            
            for symbol in SUPPORTED_COINS.keys():
                await self.fetch_and_cache_chart(symbol)
                await asyncio.sleep(0.5)
            
            logger.info("✅ All data updated (prices + details + charts)")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch all data: {e}")
    
    async def fetch_and_cache_coin_details(self, coin_symbol):
        """Fetch and cache coin details"""
        try:
            coin_info = SUPPORTED_COINS.get(coin_symbol.lower())
            if not coin_info:
                return
            
            coin_id = coin_info["id"]
            url = f"{COINGECKO_API}/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.coin_details[coin_symbol] = {
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
        except Exception as e:
            logger.error(f"❌ Failed to cache {coin_symbol} details: {e}")
    
    async def fetch_and_cache_chart(self, coin_symbol, days=7):
        """Fetch and cache chart data"""
        try:
            coin_info = SUPPORTED_COINS.get(coin_symbol.lower())
            if not coin_info:
                return
            
            coin_id = coin_info["id"]
            url = f"{COINGECKO_API}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "prices" in data:
                            self.chart_data[coin_symbol] = [price[1] for price in data["prices"]]
        except Exception as e:
            logger.error(f"❌ Failed to cache {coin_symbol} chart: {e}")
    
    async def start(self, update_interval=60):
        """Start background price updater"""
        self.is_running = True
        logger.info(f"🚀 Price updater started (updates every {update_interval}s)")
        
        # Initial fetch
        await self.fetch_all_data()
        
        # Background loop
        while self.is_running:
            await asyncio.sleep(update_interval)
            await self.fetch_all_data()
    
    def stop(self):
        """Stop background updater"""
        self.is_running = False
        logger.info("⏹️ Price updater stopped")
    
    def get_all_prices(self):
        """Get cached prices"""
        return self.prices
    
    def get_coin_details(self, coin_symbol):
        """Get cached coin details"""
        return self.coin_details.get(coin_symbol.lower())
    
    def get_chart_data(self, coin_symbol):
        """Get cached chart data"""
        return self.chart_data.get(coin_symbol.lower())

# Global instance
price_updater = PriceUpdater()
