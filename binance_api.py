import aiohttp
import asyncio
from datetime import datetime
from config import (
    SUPPORTED_COINS,
    LIVECOINWATCH_API_KEY,
    LCW_SYMBOL_MAP,
    DEFAULT_COIN_COLOR,
    DEFAULT_LOGO_URL,
    DEFAULT_PREMIUM_EMOJI_ID,
)


class BinancePriceUpdater:
    def __init__(self):
        self.prices = {}
        self.coin_details = {}
        self.chart_data = {}
        self.last_update = None
        self.is_running = False

        self.binance_symbols = {
            "btc": "BTCUSDT",
            "eth": "ETHUSDT",
            "sol": "SOLUSDT",
            "ton": "TONUSDT",
            "bnb": "BNBUSDT",
            "xrp": "XRPUSDT",
            "trx": "TRXUSDT",
            "ltc": "LTCUSDT",
        }

    async def fetch_all_prices(self):
        """Fetch all supported prices from Binance."""
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        print(f"Binance API error: {response.status}")
                        return False

                    data = await response.json()
                    ticker_data = {item["symbol"]: item for item in data}

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
                                "logo_url": info.get("logo_url"),
                            }

                    self.prices = result
                    self.last_update = datetime.now()
                    print(f"Binance updated {len(result)} coins")
                    return True
        except Exception as e:
            print(f"Binance fetch error: {e}")
            return False

    async def _resolve_coingecko_id(self, session, coin_symbol, coin_info):
        if coin_info and coin_info.get("id"):
            return coin_info["id"]

        try:
            url = f"https://api.coingecko.com/api/v3/search?query={coin_symbol}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                coins = data.get("coins", [])
                symbol_lower = coin_symbol.lower()

                for coin in coins:
                    if coin.get("symbol", "").lower() == symbol_lower:
                        return coin.get("id")

                if coins:
                    return coins[0].get("id")
        except Exception as e:
            print(f"CoinGecko id lookup failed for {coin_symbol}: {e}")

        return None

    async def _fetch_ath_from_coingecko(self, session, coin_symbol, coin_info):
        coin_id = await self._resolve_coingecko_id(session, coin_symbol, coin_info)
        if not coin_id:
            return None

        try:
            url = (
                f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                "?localization=false&tickers=false&market_data=true"
                "&community_data=false&developer_data=false&sparkline=false"
            )
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                market_data = data.get("market_data", {})
                ath_price = market_data.get("ath", {}).get("usd")
                ath_date = market_data.get("ath_date", {}).get("usd")

                if ath_price:
                    return float(ath_price), (ath_date or "2021-01-01T00:00:00.000Z")
        except Exception as e:
            print(f"CoinGecko ATH lookup failed for {coin_symbol}: {e}")

        return None

    async def _fetch_ath_from_binance(self, session, binance_symbol):
        """Approximate ATH from Binance weekly candles and return price + candle date."""
        try:
            url = (
                "https://api.binance.com/api/v3/klines"
                f"?symbol={binance_symbol}&interval=1w&limit=1500"
            )
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status != 200:
                    return None

                candles = await response.json()
                if not candles:
                    return None

                ath_candle = max(candles, key=lambda c: float(c[2]))
                ath_price = float(ath_candle[2])
                ath_ts_ms = int(ath_candle[0])
                ath_date = datetime.utcfromtimestamp(ath_ts_ms / 1000).isoformat() + "Z"
                return ath_price, ath_date
        except Exception as e:
            print(f"Binance ATH fallback failed for {binance_symbol}: {e}")
            return None

    async def _fetch_details_from_coingecko(self, session, coin_symbol, coin_info):
        coin_id = await self._resolve_coingecko_id(session, coin_symbol, coin_info)
        if not coin_id:
            return None

        try:
            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                f"?vs_currency=usd&ids={coin_id}&price_change_percentage=24h,7d"
            )
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status != 200:
                    return None

                rows = await response.json()
                if not rows:
                    return None

                row = rows[0]
                if coin_info:
                    name = coin_info["name"]
                    symbol = coin_info["symbol"]
                    color = coin_info["color"]
                    logo_url = coin_info.get("logo_url")
                    premium_emoji_id = coin_info.get("premium_emoji_id")
                else:
                    name = row.get("name", coin_symbol.upper())
                    symbol = row.get("symbol", coin_symbol.upper()).upper()
                    color = DEFAULT_COIN_COLOR
                    logo_url = row.get("image", DEFAULT_LOGO_URL)
                    premium_emoji_id = DEFAULT_PREMIUM_EMOJI_ID

                price = float(row.get("current_price") or 0)
                change_24h = float(row.get("price_change_percentage_24h") or 0)
                change_7d = float(
                    row.get("price_change_percentage_7d_in_currency")
                    if row.get("price_change_percentage_7d_in_currency") is not None
                    else change_24h * 3.5
                )
                ath_price = float(row.get("ath") or (price * 2))
                ath_date = row.get("ath_date") or "2021-01-01T00:00:00.000Z"

                return {
                    "symbol": symbol,
                    "name": name,
                    "price": price,
                    "change_24h": change_24h,
                    "change_7d": change_7d,
                    "ath": ath_price,
                    "ath_date": ath_date,
                    "color": color,
                    "logo_url": logo_url,
                    "premium_emoji_id": premium_emoji_id,
                }
        except Exception as e:
            print(f"CoinGecko fallback failed for {coin_symbol}: {e}")

        return None

    async def _fetch_details_from_livecoinwatch(self, session, coin_symbol, coin_info):
        if not LIVECOINWATCH_API_KEY:
            return None

        try:
            if coin_info and "lcw_code" in coin_info:
                lcw_code = coin_info["lcw_code"]
            elif coin_symbol in LCW_SYMBOL_MAP:
                lcw_code = LCW_SYMBOL_MAP[coin_symbol]
            else:
                lcw_code = coin_symbol.upper()

            url = "https://api.livecoinwatch.com/coins/single"
            headers = {
                "content-type": "application/json",
                "x-api-key": LIVECOINWATCH_API_KEY,
            }
            payload = {"currency": "USD", "code": lcw_code, "meta": True}

            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 404:
                    payload["code"] = coin_symbol.upper()
                    async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as retry_response:
                        if retry_response.status != 200:
                            return None
                        data = await retry_response.json()
                elif response.status == 200:
                    data = await response.json()
                else:
                    return None

            if coin_info:
                name = coin_info["name"]
                symbol = coin_info["symbol"]
                color = coin_info["color"]
                logo_url = coin_info.get("logo_url")
                premium_emoji_id = coin_info.get("premium_emoji_id")
            else:
                name = data.get("name", coin_symbol.upper())
                symbol = data.get("symbol", coin_symbol.upper())
                color = data.get("color", DEFAULT_COIN_COLOR)
                logo_url = data.get("png64", DEFAULT_LOGO_URL)
                premium_emoji_id = DEFAULT_PREMIUM_EMOJI_ID

            price = float(data.get("rate") or 0)
            delta = data.get("delta", {})
            change_24h = (float(delta.get("day", 1.0)) - 1.0) * 100
            change_7d = (float(delta.get("week", 1.0)) - 1.0) * 100
            ath_price = float(data.get("allTimeHighUSD") or (price * 2))

            return {
                "symbol": symbol,
                "name": name,
                "price": price,
                "change_24h": change_24h,
                "change_7d": change_7d,
                "ath": ath_price,
                "ath_date": "2021-01-01T00:00:00.000Z",
                "color": color,
                "logo_url": logo_url,
                "premium_emoji_id": premium_emoji_id,
            }
        except Exception as e:
            print(f"LiveCoinWatch fallback failed for {coin_symbol}: {e}")
            return None

    async def fetch_coin_details(self, coin_symbol):
        """Fetch coin details with Binance primary and robust fallbacks."""
        try:
            coin_symbol = coin_symbol.lower()
            coin_info = SUPPORTED_COINS.get(coin_symbol)
            binance_symbol = f"{coin_symbol.upper()}USDT"
            binance_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"

            async with aiohttp.ClientSession() as session:
                async with session.get(binance_url, timeout=aiohttp.ClientTimeout(total=4)) as response:
                    if response.status == 200:
                        data = await response.json()

                        if coin_info:
                            name = coin_info["name"]
                            symbol = coin_info["symbol"]
                            color = coin_info["color"]
                            logo_url = coin_info.get("logo_url")
                            premium_emoji_id = coin_info.get("premium_emoji_id")
                        else:
                            name = coin_symbol.upper()
                            symbol = coin_symbol.upper()
                            color = DEFAULT_COIN_COLOR
                            logo_url = DEFAULT_LOGO_URL
                            premium_emoji_id = DEFAULT_PREMIUM_EMOJI_ID

                        price = float(data.get("lastPrice") or 0)
                        change_24h = float(data.get("priceChangePercent") or 0)
                        change_7d = change_24h * 3.5

                        ath_price = price * 2
                        ath_date = "2021-01-01T00:00:00.000Z"

                        cg_ath = await self._fetch_ath_from_coingecko(session, coin_symbol, coin_info)
                        if cg_ath:
                            ath_price, ath_date = cg_ath
                        else:
                            # Secondary CoinGecko path: lighter endpoint that often survives when the
                            # full coin endpoint is rate-limited.
                            cg_details = await self._fetch_details_from_coingecko(session, coin_symbol, coin_info)
                            if cg_details and cg_details.get("ath"):
                                ath_price = cg_details["ath"]
                                ath_date = cg_details.get("ath_date", ath_date)

                        if ath_price == price * 2:
                            binance_ath = await self._fetch_ath_from_binance(session, binance_symbol)
                            if binance_ath:
                                ath_price, ath_date = binance_ath

                        if ath_price == price * 2 and LIVECOINWATCH_API_KEY:
                            lcw_result = await self._fetch_details_from_livecoinwatch(session, coin_symbol, coin_info)
                            if lcw_result and lcw_result.get("ath"):
                                ath_price = lcw_result["ath"]

                        return {
                            "symbol": symbol,
                            "name": name,
                            "price": price,
                            "change_24h": change_24h,
                            "change_7d": change_7d,
                            "ath": ath_price,
                            "ath_date": ath_date,
                            "color": color,
                            "logo_url": logo_url,
                            "premium_emoji_id": premium_emoji_id,
                        }

                cg_result = await self._fetch_details_from_coingecko(session, coin_symbol, coin_info)
                if cg_result:
                    return cg_result

                lcw_result = await self._fetch_details_from_livecoinwatch(session, coin_symbol, coin_info)
                if lcw_result:
                    return lcw_result

                return None
        except Exception as e:
            print(f"Failed to fetch {coin_symbol} details: {e}")
            return None

    async def fetch_chart_data(self, coin_symbol, days=7):
        """Fetch chart data from Binance - supports any USDT pair."""
        try:
            coin_info = SUPPORTED_COINS.get(coin_symbol.lower())
            if coin_info:
                binance_symbol = self.binance_symbols.get(coin_symbol.lower())
            else:
                binance_symbol = f"{coin_symbol.upper()}USDT"

            if not binance_symbol:
                binance_symbol = f"{coin_symbol.upper()}USDT"

            interval = "1h"
            limit = days * 24
            url = (
                "https://api.binance.com/api/v3/klines"
                f"?symbol={binance_symbol}&interval={interval}&limit={limit}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    prices = [float(candle[4]) for candle in data]
                    self.chart_data[coin_symbol] = prices
                    return prices
        except Exception as e:
            print(f"Failed to fetch {coin_symbol} chart: {e}")
            return None

    async def fetch_all_data(self):
        """Fetch all data from Binance in the background."""
        try:
            success = await self.fetch_all_prices()
            if not success:
                print("Using cached data")
                return

            for symbol in SUPPORTED_COINS.keys():
                await self.fetch_coin_details(symbol)
                await asyncio.sleep(0.1)

            for symbol in SUPPORTED_COINS.keys():
                await self.fetch_chart_data(symbol)
                await asyncio.sleep(0.1)

            print("All Binance data updated")
        except Exception as e:
            print(f"Failed to fetch all data: {e}")

    async def start(self, update_interval=30):
        """Start background price updater."""
        self.is_running = True
        print(f"Updater started (every {update_interval}s)")

        await self.fetch_all_data()

        while self.is_running:
            await asyncio.sleep(update_interval)
            await self.fetch_all_data()

    def stop(self):
        """Stop background updater."""
        self.is_running = False
        print("Updater stopped")

    def get_all_prices(self):
        """Get cached prices."""
        return self.prices

    def get_coin_details(self, coin_symbol):
        """Disabled cache lookup to always serve fresh data."""
        return None

    async def get_coin_details_async(self, coin_symbol):
        """Get coin details fresh from upstream APIs."""
        return await self.fetch_coin_details(coin_symbol)

    def get_chart_data(self, coin_symbol):
        """Get cached chart data."""
        return self.chart_data.get(coin_symbol.lower())


binance_updater = BinancePriceUpdater()

