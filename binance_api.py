import aiohttp
import asyncio
from datetime import datetime, timedelta
from config import SUPPORTED_COINS

class BinancePriceUpdater:
    def __init__(self):
        self.prices = {}
        self.coin_details = {}  # Don't use this cache anymore
        self.chart_data = {}
        self.last_update = None
        self.is_running = False
        
        # Binance symbol mapping
        self.binance_symbols = {
            "btc": "BTCUSDT",
            "eth": "ETHUSDT",
            "sol": "SOLUSDT",
            "ton": "TONUSDT",
            "bnb": "BNBUSDT",
            "xrp": "XRPUSDT",
            "trx": "TRXUSDT",
            "ltc": "LTCUSDT"
        }
    
    async def fetch_all_prices(self):
        """Fetch all prices from Binance (instant, no rate limit)"""
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Create lookup dict
                        ticker_data = {item['symbol']: item for item in data}
                        
                        result = {}
                        for symbol, info in SUPPORTED_COINS.items():
                            binance_symbol = self.binance_symbols.get(symbol)
                            if binance_symbol and binance_symbol in ticker_data:
                                ticker = ticker_data[binance_symbol]
                                result[symbol] = {
                                    "symbol": info["symbol"],
                                    "name": info["name"],
                                    "price": float(ticker["lastPrice"]),
                                    "change_24h": float(ticker["priceChangePercent"]),
                                    "color": info["color"],
                                    "logo_url": info.get("logo_url")
                                }
                        
                        self.prices = result
                        self.last_update = datetime.now()
                        print(f"✅ Binance: {len(result)} coins updated")
                        return True
                    else:
                        print(f"❌ Binance API error: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Binance fetch error: {e}")
            return False
    
    async def fetch_coin_details(self, coin_symbol):
        """Fetch detailed coin data from Binance - supports ANY coin"""
        try:
            # Try to get from config first
            coin_info = SUPPORTED_COINS.get(coin_symbol.lower())
            
            # If not in config, try to find on Binance
            binance_symbol = f"{coin_symbol.upper()}USDT"
            
            # Get 24h ticker
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
            
            print(f"🔍 Fetching {coin_symbol.upper()} from Binance: {binance_symbol}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                    print(f"📡 Response status for {binance_symbol}: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Use config data if available, otherwise use defaults
                        if coin_info:
                            name = coin_info["name"]
                            symbol = coin_info["symbol"]
                            color = coin_info["color"]
                            logo_url = coin_info.get("logo_url")
                            premium_emoji_id = coin_info.get("premium_emoji_id")
                            coingecko_id = coin_info.get("id")
                        else:
                            # Default values for unsupported coins
                            from config import DEFAULT_COIN_COLOR, DEFAULT_LOGO_URL, DEFAULT_PREMIUM_EMOJI_ID
                            name = coin_symbol.upper()
                            symbol = coin_symbol.upper()
                            color = DEFAULT_COIN_COLOR
                            logo_url = DEFAULT_LOGO_URL
                            premium_emoji_id = DEFAULT_PREMIUM_EMOJI_ID
                            coingecko_id = coin_symbol.lower()
                        
                        # Calculate 7d change (approximate from 24h)
                        change_7d = float(data["priceChangePercent"]) * 3.5
                        
                        # Fetch real ATH data from CoinGecko with retry
                        ath_price = float(data["lastPrice"]) * 2  # Better fallback
                        ath_date = "2021-01-01T00:00:00.000Z"  # Fallback date
                        
                        # Try CoinGecko with retries
                        for attempt in range(3):
                            try:
                                # Get ATH from CoinGecko (free API, no key needed)
                                coingecko_url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
                                print(f"🔍 Attempt {attempt + 1}: Fetching ATH from CoinGecko for {coin_symbol.upper()} (ID: {coingecko_id})")
                                
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                    'Accept': 'application/json'
                                }
                                
                                async with session.get(coingecko_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as cg_response:
                                    print(f"📡 CoinGecko status: {cg_response.status}")
                                    
                                    if cg_response.status == 200:
                                        cg_data = await cg_response.json()
                                        
                                        # Debug: Print what we got
                                        if "market_data" in cg_data:
                                            print(f"✅ Got market_data for {coin_symbol}")
                                            if "ath" in cg_data["market_data"] and "usd" in cg_data["market_data"]["ath"]:
                                                print(f"✅ Got ATH data for {coin_symbol}")
                                                ath_price = float(cg_data["market_data"]["ath"]["usd"])
                                                print(f"✅ ATH Price: ${ath_price:,.8f}")
                                                
                                                # Get ATH date if available
                                                if "ath_date" in cg_data["market_data"] and "usd" in cg_data["market_data"]["ath_date"]:
                                                    ath_date = cg_data["market_data"]["ath_date"]["usd"]
                                                    print(f"✅ ATH Date: {ath_date}")
                                                else:
                                                    print(f"⚠️ No ath_date in market_data for {coin_symbol}, using fallback")
                                                
                                                print(f"✅ Got real ATH for {coin_symbol.upper()}: ${ath_price:,.8f} on {ath_date}")
                                                break  # Success, exit retry loop
                                            else:
                                                print(f"⚠️ No ath in market_data for {coin_symbol}")
                                        else:
                                            print(f"⚠️ No market_data in CoinGecko response for {coin_symbol}")
                                    elif cg_response.status == 429:
                                        print(f"⚠️ CoinGecko rate limit, waiting 3 seconds...")
                                        await asyncio.sleep(3)
                                    else:
                                        error_text = await cg_response.text()
                                        print(f"⚠️ CoinGecko returned status {cg_response.status}: {error_text[:200]}")
                                        
                            except asyncio.TimeoutError:
                                print(f"⚠️ CoinGecko timeout for {coin_symbol} (attempt {attempt + 1})")
                                if attempt < 2:
                                    await asyncio.sleep(2)
                            except Exception as e:
                                print(f"⚠️ CoinGecko error (attempt {attempt + 1}): {e}")
                                if attempt < 2:
                                    await asyncio.sleep(2)
                        
                        result = {
                            "symbol": symbol,
                            "name": name,
                            "price": float(data["lastPrice"]),
                            "change_24h": float(data["priceChangePercent"]),
                            "change_7d": change_7d,
                            "ath": ath_price,
                            "ath_date": ath_date,
                            "color": color,
                            "logo_url": logo_url,
                            "premium_emoji_id": premium_emoji_id
                        }
                        
                        # Don't cache - always fetch fresh
                        print(f"✅ Successfully fetched {coin_symbol.upper()} - ATH: ${ath_price:,.2f} on {ath_date}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ Binance API error for {binance_symbol}: {response.status} - {error_text}")
        except Exception as e:
            print(f"❌ Failed to fetch {coin_symbol} details: {e}")
        return None
    
    async def fetch_chart_data(self, coin_symbol, days=7):
        """Fetch chart data from Binance - supports ANY coin"""
        try:
            # Try to get from config first, otherwise use uppercase symbol
            coin_info = SUPPORTED_COINS.get(coin_symbol.lower())
            if coin_info:
                binance_symbol = self.binance_symbols.get(coin_symbol.lower())
            else:
                binance_symbol = f"{coin_symbol.upper()}USDT"
            
            if not binance_symbol:
                binance_symbol = f"{coin_symbol.upper()}USDT"
            
            # Get klines (candlestick data)
            interval = "1h"  # 1 hour intervals
            limit = days * 24  # 7 days = 168 hours
            
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={interval}&limit={limit}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract close prices
                        prices = [float(candle[4]) for candle in data]
                        
                        self.chart_data[coin_symbol] = prices
                        return prices
        except Exception as e:
            print(f"❌ Failed to fetch {coin_symbol} chart: {e}")
        return None
    
    async def fetch_all_data(self):
        """Fetch all data from Binance"""
        try:
            # Fetch basic prices
            success = await self.fetch_all_prices()
            if not success:
                print("⚠️ Using cached data")
                return
            
            # Fetch details and charts for all coins
            for symbol in SUPPORTED_COINS.keys():
                await self.fetch_coin_details(symbol)
                await asyncio.sleep(0.1)  # Small delay
            
            for symbol in SUPPORTED_COINS.keys():
                await self.fetch_chart_data(symbol)
                await asyncio.sleep(0.1)
            
            print("✅ All Binance data updated")
            
        except Exception as e:
            print(f"❌ Failed to fetch all data: {e}")
    
    async def start(self, update_interval=30):
        """Start background price updater"""
        self.is_running = True
        print(f"🚀 Binance updater started (updates every {update_interval}s)")
        
        # Initial fetch
        await self.fetch_all_data()
        
        # Background loop
        while self.is_running:
            await asyncio.sleep(update_interval)
            await self.fetch_all_data()
    
    def stop(self):
        """Stop background updater"""
        self.is_running = False
        print("⏹️ Binance updater stopped")
    
    def get_all_prices(self):
        """Get cached prices"""
        return self.prices
    
    def get_coin_details(self, coin_symbol):
        """Get cached coin details or return None to trigger fetch"""
        # Always return None to force fresh fetch - fixes cache issues
        return None
    
    async def get_coin_details_async(self, coin_symbol):
        """Get coin details - always fetch fresh to avoid cache issues"""
        # Always fetch fresh data to fix GC vs DM cache issues
        return await self.fetch_coin_details(coin_symbol)
    
    def get_chart_data(self, coin_symbol):
        """Get cached chart data"""
        return self.chart_data.get(coin_symbol.lower())

# Global instance
binance_updater = BinancePriceUpdater()
