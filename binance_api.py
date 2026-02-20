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
        """Fetch detailed coin data from Binance or LiveCoinWatch - supports ANY coin"""
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
                        else:
                            # Default values for unsupported coins
                            from config import DEFAULT_COIN_COLOR, DEFAULT_LOGO_URL, DEFAULT_PREMIUM_EMOJI_ID
                            name = coin_symbol.upper()
                            symbol = coin_symbol.upper()
                            color = DEFAULT_COIN_COLOR
                            logo_url = DEFAULT_LOGO_URL
                            premium_emoji_id = DEFAULT_PREMIUM_EMOJI_ID
                        
                        # Calculate 7d change (approximate from 24h)
                        change_7d = float(data["priceChangePercent"]) * 3.5
                        
                        # Fetch real ATH data from LiveCoinWatch
                        ath_price = float(data["lastPrice"]) * 2  # Better fallback
                        ath_date = "2021-01-01T00:00:00.000Z"  # Fallback date
                        
                        # Try LiveCoinWatch API (free, 10k requests/day)
                        from config import LIVECOINWATCH_API_KEY, LCW_SYMBOL_MAP
                        
                        if LIVECOINWATCH_API_KEY:
                            try:
                                # Get the correct LiveCoinWatch code
                                if coin_info and "lcw_code" in coin_info:
                                    lcw_code = coin_info["lcw_code"]
                                elif coin_symbol.lower() in LCW_SYMBOL_MAP:
                                    lcw_code = LCW_SYMBOL_MAP[coin_symbol.lower()]
                                else:
                                    lcw_code = coin_symbol.upper()
                                
                                lcw_url = "https://api.livecoinwatch.com/coins/single"
                                headers = {
                                    'content-type': 'application/json',
                                    'x-api-key': LIVECOINWATCH_API_KEY
                                }
                                payload = {
                                    "currency": "USD",
                                    "code": lcw_code,
                                    "meta": True
                                }
                                
                                print(f"🔍 Fetching ATH from LiveCoinWatch for {coin_symbol.upper()} (code: {lcw_code})")
                                
                                async with session.post(lcw_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as lcw_response:
                                    print(f"📡 LiveCoinWatch status: {lcw_response.status}")
                                    
                                    if lcw_response.status == 200:
                                        lcw_data = await lcw_response.json()
                                        
                                        if "allTimeHighUSD" in lcw_data and lcw_data["allTimeHighUSD"]:
                                            ath_price = float(lcw_data["allTimeHighUSD"])
                                            print(f"✅ Got real ATH from LiveCoinWatch for {coin_symbol.upper()}: ${ath_price:,.8f}")
                                        else:
                                            print(f"⚠️ No allTimeHighUSD in LiveCoinWatch response for {coin_symbol}")
                                    elif lcw_response.status == 401:
                                        print(f"⚠️ LiveCoinWatch API key invalid or missing")
                                    elif lcw_response.status == 404:
                                        print(f"⚠️ Coin {lcw_code} not found on LiveCoinWatch, trying uppercase symbol")
                                        # Fallback: try with uppercase symbol
                                        payload["code"] = coin_symbol.upper()
                                        async with session.post(lcw_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as retry_response:
                                            if retry_response.status == 200:
                                                retry_data = await retry_response.json()
                                                if "allTimeHighUSD" in retry_data and retry_data["allTimeHighUSD"]:
                                                    ath_price = float(retry_data["allTimeHighUSD"])
                                                    print(f"✅ Got real ATH from LiveCoinWatch (retry) for {coin_symbol.upper()}: ${ath_price:,.8f}")
                                    else:
                                        error_text = await lcw_response.text()
                                        print(f"⚠️ LiveCoinWatch returned status {lcw_response.status}: {error_text[:200]}")
                                        
                            except asyncio.TimeoutError:
                                print(f"⚠️ LiveCoinWatch timeout for {coin_symbol}")
                            except Exception as e:
                                print(f"⚠️ LiveCoinWatch error: {e}")
                        else:
                            print(f"⚠️ No LiveCoinWatch API key configured, using fallback ATH")
                        
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
                        # Binance failed - try to get ALL data from LiveCoinWatch
                        print(f"⚠️ Binance failed for {binance_symbol}, trying LiveCoinWatch as primary source")
                        
                        from config import LIVECOINWATCH_API_KEY, LCW_SYMBOL_MAP
                        
                        if not LIVECOINWATCH_API_KEY:
                            error_text = await response.text()
                            print(f"❌ Binance API error for {binance_symbol}: {response.status} - {error_text}")
                            return None
                        
                        try:
                            # Get the correct LiveCoinWatch code
                            if coin_info and "lcw_code" in coin_info:
                                lcw_code = coin_info["lcw_code"]
                            elif coin_symbol.lower() in LCW_SYMBOL_MAP:
                                lcw_code = LCW_SYMBOL_MAP[coin_symbol.lower()]
                            else:
                                lcw_code = coin_symbol.upper()
                            
                            lcw_url = "https://api.livecoinwatch.com/coins/single"
                            headers = {
                                'content-type': 'application/json',
                                'x-api-key': LIVECOINWATCH_API_KEY
                            }
                            payload = {
                                "currency": "USD",
                                "code": lcw_code,
                                "meta": True
                            }
                            
                            print(f"🔍 Fetching ALL data from LiveCoinWatch for {coin_symbol.upper()} (code: {lcw_code})")
                            
                            async with session.post(lcw_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as lcw_response:
                                print(f"📡 LiveCoinWatch status: {lcw_response.status}")
                                
                                if lcw_response.status == 200:
                                    lcw_data = await lcw_response.json()
                                    
                                    # Use config data if available, otherwise use LiveCoinWatch data
                                    if coin_info:
                                        name = coin_info["name"]
                                        symbol = coin_info["symbol"]
                                        color = coin_info["color"]
                                        logo_url = coin_info.get("logo_url")
                                        premium_emoji_id = coin_info.get("premium_emoji_id")
                                    else:
                                        from config import DEFAULT_COIN_COLOR, DEFAULT_LOGO_URL, DEFAULT_PREMIUM_EMOJI_ID
                                        name = lcw_data.get("name", coin_symbol.upper())
                                        symbol = lcw_data.get("symbol", coin_symbol.upper())
                                        color = lcw_data.get("color", DEFAULT_COIN_COLOR)
                                        logo_url = lcw_data.get("png64", DEFAULT_LOGO_URL)
                                        premium_emoji_id = DEFAULT_PREMIUM_EMOJI_ID
                                    
                                    # Get price and changes from LiveCoinWatch
                                    price = float(lcw_data.get("rate", 0))
                                    delta = lcw_data.get("delta", {})
                                    change_24h = (float(delta.get("day", 1.0)) - 1.0) * 100
                                    change_7d = (float(delta.get("week", 1.0)) - 1.0) * 100
                                    
                                    # Get ATH
                                    ath_price = float(lcw_data.get("allTimeHighUSD", price * 2))
                                    ath_date = "2021-01-01T00:00:00.000Z"
                                    
                                    result = {
                                        "symbol": symbol,
                                        "name": name,
                                        "price": price,
                                        "change_24h": change_24h,
                                        "change_7d": change_7d,
                                        "ath": ath_price,
                                        "ath_date": ath_date,
                                        "color": color,
                                        "logo_url": logo_url,
                                        "premium_emoji_id": premium_emoji_id
                                    }
                                    
                                    print(f"✅ Successfully fetched {coin_symbol.upper()} from LiveCoinWatch - Price: ${price:,.8f}, ATH: ${ath_price:,.8f}")
                                    return result
                                elif lcw_response.status == 404:
                                    print(f"⚠️ Coin {lcw_code} not found on LiveCoinWatch, trying uppercase")
                                    payload["code"] = coin_symbol.upper()
                                    async with session.post(lcw_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as retry_response:
                                        if retry_response.status == 200:
                                            retry_data = await retry_response.json()
                                            
                                            if coin_info:
                                                name = coin_info["name"]
                                                symbol = coin_info["symbol"]
                                                color = coin_info["color"]
                                                logo_url = coin_info.get("logo_url")
                                                premium_emoji_id = coin_info.get("premium_emoji_id")
                                            else:
                                                from config import DEFAULT_COIN_COLOR, DEFAULT_LOGO_URL, DEFAULT_PREMIUM_EMOJI_ID
                                                name = retry_data.get("name", coin_symbol.upper())
                                                symbol = retry_data.get("symbol", coin_symbol.upper())
                                                color = retry_data.get("color", DEFAULT_COIN_COLOR)
                                                logo_url = retry_data.get("png64", DEFAULT_LOGO_URL)
                                                premium_emoji_id = DEFAULT_PREMIUM_EMOJI_ID
                                            
                                            price = float(retry_data.get("rate", 0))
                                            delta = retry_data.get("delta", {})
                                            change_24h = (float(delta.get("day", 1.0)) - 1.0) * 100
                                            change_7d = (float(delta.get("week", 1.0)) - 1.0) * 100
                                            ath_price = float(retry_data.get("allTimeHighUSD", price * 2))
                                            ath_date = "2021-01-01T00:00:00.000Z"
                                            
                                            result = {
                                                "symbol": symbol,
                                                "name": name,
                                                "price": price,
                                                "change_24h": change_24h,
                                                "change_7d": change_7d,
                                                "ath": ath_price,
                                                "ath_date": ath_date,
                                                "color": color,
                                                "logo_url": logo_url,
                                                "premium_emoji_id": premium_emoji_id
                                            }
                                            
                                            print(f"✅ Successfully fetched {coin_symbol.upper()} from LiveCoinWatch (retry) - Price: ${price:,.8f}, ATH: ${ath_price:,.8f}")
                                            return result
                                else:
                                    error_text = await lcw_response.text()
                                    print(f"❌ LiveCoinWatch error: {lcw_response.status} - {error_text[:200]}")
                                    return None
                                    
                        except Exception as e:
                            print(f"❌ LiveCoinWatch fallback failed: {e}")
                            return None
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
