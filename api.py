from binance_api import binance_updater

async def get_all_prices():
    """Get all prices from Binance (instant)"""
    prices = binance_updater.get_all_prices()
    if prices:
        return prices
    # Warm up once on demand so /top doesn't fail right after restart
    success = await binance_updater.fetch_all_prices()
    if success:
        return binance_updater.get_all_prices()
    return {}

async def get_coin_price(coin_symbol):
    """Get coin details from Binance (instant) - fetches any coin"""
    return await binance_updater.get_coin_details_async(coin_symbol)

async def get_price_chart(coin_symbol, days=7):
    """Get chart data from Binance (instant) - always fetch fresh"""
    return await binance_updater.fetch_chart_data(coin_symbol, days)
