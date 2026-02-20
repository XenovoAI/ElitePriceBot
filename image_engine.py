from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import asyncio
import aiohttp
from config import WATERMARK

# Logo cache
logo_cache = {}

async def download_logo(url, size=60):
    """Download coin logo"""
    if url in logo_cache:
        return logo_cache[url]
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                if response.status == 200:
                    img_data = await response.read()
                    logo = Image.open(io.BytesIO(img_data))
                    logo = logo.convert('RGBA')
                    logo = logo.resize((size, size), Image.Resampling.LANCZOS)
                    logo_cache[url] = logo
                    return logo
    except:
        pass
    return None

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    fonts_to_try = [
        "arialbd.ttf" if bold else "arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for font in fonts_to_try:
        try:
            return ImageFont.truetype(font, size)
        except:
            continue
    return ImageFont.load_default()

def create_gradient_bg(width, height):
    """Create dark gradient background"""
    img = Image.new('RGB', (width, height), (15, 20, 30))
    draw = ImageDraw.Draw(img)
    
    for y in range(height):
        ratio = y / height
        r = int(15 + (25 - 15) * ratio)
        g = int(20 + (30 - 20) * ratio)
        b = int(30 + (45 - 30) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img

def draw_glassmorphism_card(draw, x, y, w, h, color_rgb, is_positive):
    """Draw glassmorphism card with glow"""
    # Glow effect
    glow_color = (0, 255, 136) if is_positive else (255, 68, 68)
    draw.rounded_rectangle([x-3, y-3, x+w+3, y+h+3], radius=22, fill=glow_color, width=0)
    
    # Card background
    if is_positive:
        bg = (20, 50, 35)
    else:
        bg = (50, 20, 25)
    
    draw.rounded_rectangle([x, y, x+w, y+h], radius=20, fill=bg)
    
    # Border
    border_color = tuple(min(255, int(c * 1.2)) for c in color_rgb)
    draw.rounded_rectangle([x, y, x+w, y+h], radius=20, outline=border_color, width=2)

async def create_top_grid_async(prices_data):
    """Ultra-professional glassmorphism grid"""
    width, height = 1200, 700
    
    # Pure black background
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    coins = ["btc", "eth", "sol", "ton", "ltc", "xrp", "bnb", "trx"]
    tile_w, tile_h = 260, 220
    padding, start_x, start_y = 30, 50, 80
    
    for idx, coin in enumerate(coins):
        if coin not in prices_data:
            continue
        
        data = prices_data[coin]
        row, col = idx // 4, idx % 4
        x = start_x + col * (tile_w + padding)
        y = start_y + row * (tile_h + padding)
        
        change = data["change_24h"]
        color_rgb = hex_to_rgb(data["color"])
        
        # Outer glow (colored border)
        glow_color = color_rgb
        for i in range(4, 0, -1):
            alpha = int(255 * (i / 4))
            glow_rgb = tuple(int(c * (i / 4)) for c in glow_color)
            draw.rounded_rectangle([x-i, y-i, x+tile_w+i, y+tile_h+i], 
                                  radius=25, outline=glow_rgb, width=2)
        
        # Glassmorphism card
        # Dark gradient background
        for dy in range(tile_h):
            ratio = dy / tile_h
            r = int(40 + (60 - 40) * ratio)
            g = int(45 + (65 - 45) * ratio)
            b = int(50 + (70 - 50) * ratio)
            draw.line([(x, y + dy), (x + tile_w, y + dy)], fill=(r, g, b))
        
        # Rounded mask
        mask = Image.new('L', (tile_w, tile_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, tile_w, tile_h], radius=22, fill=255)
        
        # Apply mask
        card_img = img.crop((x, y, x + tile_w, y + tile_h))
        img.paste(card_img, (x, y), mask)
        
        # Redraw on main image
        draw = ImageDraw.Draw(img)
        
        # Logo
        logo_url = data.get("logo_url")
        if logo_url:
            logo = await download_logo(logo_url, 50)
            if logo:
                logo_x = x + (tile_w - 50) // 2
                logo_y = y + 20
                img.paste(logo, (logo_x, logo_y), logo)
        
        # Symbol (below logo)
        font_symbol = get_font(36, bold=True)
        symbol_color = (200, 210, 220)
        bbox_symbol = draw.textbbox((0, 0), data["symbol"], font=font_symbol)
        symbol_width = bbox_symbol[2] - bbox_symbol[0]
        draw.text((x + (tile_w - symbol_width)//2, y + 80), data["symbol"], fill=symbol_color, font=font_symbol)
        
        # Price
        font_price = get_font(28, bold=True)
        price_text = f"${data['price']:,.2f}" if data['price'] < 1000 else f"${data['price']:,.0f}"
        
        # Center price
        bbox = draw.textbbox((0, 0), price_text, font=font_price)
        price_width = bbox[2] - bbox[0]
        draw.text((x + (tile_w - price_width)//2, y + 130), price_text, fill='#FFFFFF', font=font_price)
        
        # Change percentage
        font_change = get_font(22, bold=True)
        change_color = '#00FF88' if change >= 0 else '#FF4444'
        change_text = f"{'+' if change >= 0 else ''}{change:.2f}%"
        
        # Center change
        bbox_change = draw.textbbox((0, 0), change_text, font=font_change)
        change_width = bbox_change[2] - bbox_change[0]
        draw.text((x + (tile_w - change_width)//2, y + 175), change_text, fill=change_color, font=font_change)
    
    # Watermark
    font_watermark = get_font(16)
    draw.text(((width - 200) // 2, height - 35), WATERMARK, fill='#555555', font=font_watermark)
    
    return img

async def create_coin_card_async(coin_data, chart_data=None):
    """Ultra-professional glassmorphism coin card"""
    width, height = 1000, 750
    
    # Pure black background
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color_rgb = hex_to_rgb(coin_data["color"])
    change_24h = coin_data["change_24h"]
    change_7d = coin_data.get("change_7d", 0)
    
    # Main card with colored glow
    card_x, card_y = 40, 40
    card_w, card_h = width - 80, height - 80
    
    # Outer glow effect
    for i in range(6, 0, -1):
        glow_rgb = tuple(int(c * (i / 6)) for c in color_rgb)
        draw.rounded_rectangle([card_x-i, card_y-i, card_x+card_w+i, card_y+card_h+i], 
                              radius=28, outline=glow_rgb, width=3)
    
    # Dark gradient card background
    for dy in range(card_h):
        ratio = dy / card_h
        r = int(35 + (55 - 35) * ratio)
        g = int(40 + (60 - 40) * ratio)
        b = int(45 + (65 - 45) * ratio)
        draw.line([(card_x, card_y + dy), (card_x + card_w, card_y + dy)], fill=(r, g, b))
    
    # Rounded mask
    mask = Image.new('L', (card_w, card_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, card_w, card_h], radius=25, fill=255)
    
    # Apply mask
    card_img = img.crop((card_x, card_y, card_x + card_w, card_y + card_h))
    img.paste(card_img, (card_x, card_y), mask)
    
    # Redraw
    draw = ImageDraw.Draw(img)
    
    # Logo
    logo_url = coin_data.get("logo_url")
    if logo_url:
        logo = await download_logo(logo_url, 70)
        if logo:
            img.paste(logo, (70, 70), logo)
    
    # Coin name
    font_name = get_font(44, bold=True)
    draw.text((160, 80), coin_data["name"], fill='#FFFFFF', font=font_name)
    
    # Price
    font_price = get_font(56, bold=True)
    price_text = f"${coin_data['price']:,.4f}" if coin_data['price'] < 10 else f"${coin_data['price']:,.2f}"
    draw.text((70, 170), price_text, fill=color_rgb, font=font_price)
    
    # Change badges
    badge_y = 260
    badge_w, badge_h = 180, 60
    
    font_label = get_font(14, bold=True)
    font_value = get_font(26, bold=True)
    
    # 24h badge
    draw.text((70, badge_y - 25), "24H CHANGE", fill='#888888', font=font_label)
    bg_24h = (0, 50, 30) if change_24h >= 0 else (50, 0, 20)
    draw.rounded_rectangle([70, badge_y, 70 + badge_w, badge_y + badge_h], radius=30, fill=bg_24h)
    
    # Colored border
    border_24h = '#00FF88' if change_24h >= 0 else '#FF4444'
    draw.rounded_rectangle([70, badge_y, 70 + badge_w, badge_y + badge_h], radius=30, outline=border_24h, width=2)
    
    color_24h = '#00FF88' if change_24h >= 0 else '#FF4444'
    text_24h = f"{'+' if change_24h >= 0 else ''}{change_24h:.2f}%"
    bbox = draw.textbbox((0, 0), text_24h, font=font_value)
    text_w = bbox[2] - bbox[0]
    draw.text((70 + (badge_w - text_w) // 2, badge_y + 17), text_24h, fill=color_24h, font=font_value)
    
    # 7d badge
    weekly_x = 280
    draw.text((weekly_x, badge_y - 25), "7D CHANGE", fill='#888888', font=font_label)
    bg_7d = (0, 50, 30) if change_7d >= 0 else (50, 0, 20)
    draw.rounded_rectangle([weekly_x, badge_y, weekly_x + badge_w, badge_y + badge_h], radius=30, fill=bg_7d)
    
    # Colored border
    border_7d = '#00FF88' if change_7d >= 0 else '#FF4444'
    draw.rounded_rectangle([weekly_x, badge_y, weekly_x + badge_w, badge_y + badge_h], radius=30, outline=border_7d, width=2)
    
    color_7d = '#00FF88' if change_7d >= 0 else '#FF4444'
    text_7d = f"{'+' if change_7d >= 0 else ''}{change_7d:.2f}%"
    bbox_7d = draw.textbbox((0, 0), text_7d, font=font_value)
    text_w_7d = bbox_7d[2] - bbox_7d[0]
    draw.text((weekly_x + (badge_w - text_w_7d) // 2, badge_y + 17), text_7d, fill=color_7d, font=font_value)
    
    # Chart section
    chart_y, chart_h = 380, 270
    chart_w, chart_x = width - 140, 70
    
    # Chart background with glow
    for i in range(3, 0, -1):
        glow_rgb = tuple(int(c * (i / 6)) for c in color_rgb)
        draw.rounded_rectangle([chart_x-i, chart_y-i, chart_x+chart_w+i, chart_y+chart_h+i],
                              radius=18, outline=glow_rgb, width=2)
    
    draw.rounded_rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h],
                          radius=15, fill=(25, 30, 40))
    
    font_chart = get_font(16, bold=True)
    draw.text((chart_x + 10, chart_y - 30), "7-DAY PRICE CHART", fill='#888888', font=font_chart)
    
    if chart_data and len(chart_data) > 10:
        min_price, max_price = min(chart_data), max(chart_data)
        price_range = max_price - min_price if max_price != min_price else 1
        
        # Add padding to chart
        padding = 20
        points = [(chart_x + padding + (i / (len(chart_data) - 1)) * (chart_w - 2*padding), 
                  chart_y + padding + (chart_h - 2*padding) - ((price - min_price) / price_range) * (chart_h - 2*padding)) 
                 for i, price in enumerate(chart_data)]
        
        if len(points) > 1:
            # Draw line with glow
            draw.line(points, fill=color_rgb, width=5)
    else:
        font_msg = get_font(14)
        draw.text((chart_x + chart_w//2 - 60, chart_y + chart_h//2), 
                 "Loading chart...", fill='#666666', font=font_msg)
    
    # Watermark
    font_watermark = get_font(14)
    draw.text((width//2 - 100, height - 40), WATERMARK, fill='#555555', font=font_watermark)
    
    return img

async def create_convert_card_async(coin_data, amount):
    """Ultra-professional glassmorphism converter card"""
    width, height = 900, 700
    
    # Pure black background
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color_rgb = hex_to_rgb(coin_data["color"])
    
    # Main card with colored glow
    card_x, card_y = 40, 40
    card_w, card_h = width - 80, height - 80
    
    # Outer glow
    for i in range(6, 0, -1):
        glow_rgb = tuple(int(c * (i / 6)) for c in color_rgb)
        draw.rounded_rectangle([card_x-i, card_y-i, card_x+card_w+i, card_y+card_h+i], 
                              radius=28, outline=glow_rgb, width=3)
    
    # Dark gradient background
    for dy in range(card_h):
        ratio = dy / card_h
        r = int(35 + (55 - 35) * ratio)
        g = int(40 + (60 - 40) * ratio)
        b = int(45 + (65 - 45) * ratio)
        draw.line([(card_x, card_y + dy), (card_x + card_w, card_y + dy)], fill=(r, g, b))
    
    # Rounded mask
    mask = Image.new('L', (card_w, card_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, card_w, card_h], radius=25, fill=255)
    card_img = img.crop((card_x, card_y, card_x + card_w, card_y + card_h))
    img.paste(card_img, (card_x, card_y), mask)
    
    draw = ImageDraw.Draw(img)
    
    # Title
    font_title = get_font(38, bold=True)
    draw.text((width//2 - 130, 70), "🍦 CONVERTER", fill='#FFFFFF', font=font_title)
    
    # Input box
    input_y, input_h, input_x = 170, 100, 100
    input_w = width - 200
    
    # Input glow
    for i in range(2, 0, -1):
        glow_rgb = tuple(int(c * (i / 4)) for c in color_rgb)
        draw.rounded_rectangle([input_x-i, input_y-i, input_x+input_w+i, input_y+input_h+i], 
                              radius=52, outline=glow_rgb, width=2)
    
    draw.rounded_rectangle([input_x, input_y, input_x + input_w, input_y + input_h], 
                          radius=50, fill=(25, 35, 45))
    draw.rounded_rectangle([input_x, input_y, input_x + input_w, input_y + input_h], 
                          radius=50, outline=color_rgb, width=2)
    
    # Logo
    logo_url = coin_data.get("logo_url")
    if logo_url:
        logo = await download_logo(logo_url, 65)
        if logo:
            img.paste(logo, (input_x + 20, input_y + 18), logo)
    
    font_coin = get_font(34, bold=True)
    draw.text((input_x + 100, input_y + 35), coin_data["name"], fill='#FFFFFF', font=font_coin)
    
    font_amount = get_font(38, bold=True)
    amount_text = f"{amount:,.4f}" if amount < 1000 else f"{amount:,.2f}"
    draw.text((input_x + input_w - 240, input_y + 32), amount_text, fill=color_rgb, font=font_amount)
    
    # Arrow
    arrow_y = input_y + input_h + 60
    font_arrow = get_font(52)
    draw.text((width//2 - 20, arrow_y), "↓", fill='#666666', font=font_arrow)
    
    # Output box
    output_y = arrow_y + 100
    
    # Output glow (green)
    for i in range(2, 0, -1):
        glow_rgb = tuple(int(c * (i / 4)) for c in hex_to_rgb('#00FF88'))
        draw.rounded_rectangle([input_x-i, output_y-i, input_x+input_w+i, output_y+input_h+i], 
                              radius=52, outline=glow_rgb, width=2)
    
    draw.rounded_rectangle([input_x, output_y, input_x + input_w, output_y + input_h], 
                          radius=50, fill=(25, 35, 45))
    draw.rounded_rectangle([input_x, output_y, input_x + input_w, output_y + input_h], 
                          radius=50, outline='#00FF88', width=2)
    
    usd_value = amount * coin_data['price']
    usd_text = f"${usd_value:,.2f}"
    
    draw.text((input_x + 30, output_y + 35), "USD", fill='#FFFFFF', font=font_coin)
    draw.text((input_x + input_w - 300, output_y + 32), usd_text, fill='#00FF88', font=font_amount)
    
    # Watermark
    font_watermark = get_font(14)
    draw.text((width//2 - 100, height - 40), WATERMARK, fill='#555555', font=font_watermark)
    
    return img

async def create_ath_card_async(coin_data):
    """Ultra-professional glassmorphism ATH card"""
    from datetime import datetime
    width, height = 900, 800
    
    # Pure black background
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color_rgb = hex_to_rgb(coin_data["color"])
    
    # Main card with colored glow
    card_x, card_y = 40, 40
    card_w, card_h = width - 80, height - 80
    
    # Outer glow
    for i in range(6, 0, -1):
        glow_rgb = tuple(int(c * (i / 6)) for c in color_rgb)
        draw.rounded_rectangle([card_x-i, card_y-i, card_x+card_w+i, card_y+card_h+i], 
                              radius=28, outline=glow_rgb, width=3)
    
    # Dark gradient background
    for dy in range(card_h):
        ratio = dy / card_h
        r = int(35 + (55 - 35) * ratio)
        g = int(40 + (60 - 40) * ratio)
        b = int(45 + (65 - 45) * ratio)
        draw.line([(card_x, card_y + dy), (card_x + card_w, card_y + dy)], fill=(r, g, b))
    
    # Rounded mask
    mask = Image.new('L', (card_w, card_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, card_w, card_h], radius=25, fill=255)
    card_img = img.crop((card_x, card_y, card_x + card_w, card_y + card_h))
    img.paste(card_img, (card_x, card_y), mask)
    
    draw = ImageDraw.Draw(img)
    
    # Title with logo
    logo_url = coin_data.get("logo_url")
    if logo_url:
        logo = await download_logo(logo_url, 65)
        if logo:
            img.paste(logo, (70, 70), logo)
    
    font_title = get_font(38, bold=True)
    draw.text((155, 82), f"{coin_data['name']} ATH", fill='#FFFFFF', font=font_title)
    
    y_pos, spacing = 190, 130
    badge_w, badge_h = 650, 80
    badge_x = (width - badge_w) // 2
    
    font_label = get_font(16, bold=True)
    font_value = get_font(36, bold=True)
    
    # ATH Price
    draw.text((badge_x + 20, y_pos - 30), "ALL-TIME HIGH", fill='#888888', font=font_label)
    
    # Glow for ATH badge
    for i in range(2, 0, -1):
        glow_rgb = tuple(int(c * (i / 4)) for c in hex_to_rgb('#00FF88'))
        draw.rounded_rectangle([badge_x-i, y_pos-i, badge_x+badge_w+i, y_pos+badge_h+i], 
                              radius=42, outline=glow_rgb, width=2)
    
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, fill=(0, 50, 30))
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, outline='#00FF88', width=2)
    draw.text((badge_x + 30, y_pos + 22), f"${coin_data['ath']:,.2f}", fill='#00FF88', font=font_value)
    
    # ATH Date
    y_pos += spacing
    draw.text((badge_x + 20, y_pos - 30), "ATH DATE", fill='#888888', font=font_label)
    ath_date = datetime.fromisoformat(coin_data['ath_date'].replace('Z', '+00:00'))
    date_text = ath_date.strftime("%B %d, %Y")
    
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, fill=(25, 35, 45))
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, outline='#666666', width=2)
    draw.text((badge_x + 30, y_pos + 22), date_text, fill='#FFFFFF', font=get_font(32, bold=True))
    
    # Current Price
    y_pos += spacing
    draw.text((badge_x + 20, y_pos - 30), "CURRENT PRICE", fill='#888888', font=font_label)
    
    # Glow for current price
    for i in range(2, 0, -1):
        glow_rgb = tuple(int(c * (i / 4)) for c in color_rgb)
        draw.rounded_rectangle([badge_x-i, y_pos-i, badge_x+badge_w+i, y_pos+badge_h+i], 
                              radius=42, outline=glow_rgb, width=2)
    
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, fill=(int(color_rgb[0] * 0.2), int(color_rgb[1] * 0.2), int(color_rgb[2] * 0.2)))
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, outline=color_rgb, width=2)
    draw.text((badge_x + 30, y_pos + 22), f"${coin_data['price']:,.2f}", fill=color_rgb, font=font_value)
    
    # Down from ATH
    y_pos += spacing
    percent_down = ((coin_data['ath'] - coin_data['price']) / coin_data['ath']) * 100
    draw.text((badge_x + 20, y_pos - 30), "DOWN FROM ATH", fill='#888888', font=font_label)
    
    # Glow for down badge
    for i in range(2, 0, -1):
        glow_rgb = tuple(int(c * (i / 4)) for c in hex_to_rgb('#FF4444'))
        draw.rounded_rectangle([badge_x-i, y_pos-i, badge_x+badge_w+i, y_pos+badge_h+i], 
                              radius=42, outline=glow_rgb, width=2)
    
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, fill=(50, 0, 20))
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_w, y_pos + badge_h], 
                          radius=40, outline='#FF4444', width=2)
    draw.text((badge_x + 30, y_pos + 22), f"-{percent_down:.2f}%", fill='#FF4444', font=font_value)
    
    # Watermark
    font_watermark = get_font(14)
    draw.text((width//2 - 100, height - 40), WATERMARK, fill='#555555', font=font_watermark)
    
    return img

def image_to_bytes(img):
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio
