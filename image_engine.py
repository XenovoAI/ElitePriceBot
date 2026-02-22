from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import asyncio
import aiohttp
import random
from datetime import datetime
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
    # Increase font size by 40% for better visibility on VPS
    size = int(size * 1.4)
    
    fonts_to_try = [
        "arialbd.ttf" if bold else "arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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
    """Mobile-first 3D board: crisp portrait layout for Telegram."""
    width, height = 1080, 1350
    img = Image.new("RGB", (width, height), (11, 17, 30))
    draw = ImageDraw.Draw(img)

    # High-contrast vertical background gradient
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(10 + 10 * t)
        g = int(18 + 12 * t)
        b = int(30 + 26 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Soft aurora accents (no blur)
    accent = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ad = ImageDraw.Draw(accent)
    ad.ellipse([-180, -130, 400, 360], fill=(0, 170, 255, 28))
    ad.ellipse([650, -120, 1260, 420], fill=(0, 255, 190, 20))
    ad.ellipse([240, 920, 980, 1540], fill=(255, 120, 0, 18))
    img = Image.alpha_composite(img.convert("RGBA"), accent)
    draw = ImageDraw.Draw(img)

    coins = ["btc", "eth", "sol", "ton", "ltc", "xrp", "bnb", "trx"]
    cols = 2
    margin_x = 42
    gap_x = 30
    gap_y = 26
    grid_top = 146
    tile_w = (width - (2 * margin_x) - gap_x) // cols
    tile_h = 268

    def format_price(price):
        if price >= 1000:
            return f"${price:,.0f}"
        if price >= 1:
            return f"${price:,.2f}"
        if price >= 0.01:
            return f"${price:,.4f}"
        return f"${price:,.6f}"

    # Header
    title = "CONE MARKET BOARD"
    subtitle = "Top 8 coins | live 24h change"
    font_title = get_font(26, bold=True)
    font_sub = get_font(12)
    tw = draw.textbbox((0, 0), title, font=font_title)[2]
    sw = draw.textbbox((0, 0), subtitle, font=font_sub)[2]
    draw.text(((width - tw) // 2, 38), title, fill="#F1F5FF", font=font_title)
    draw.text(((width - sw) // 2, 88), subtitle, fill="#A5B4CC", font=font_sub)

    for idx, coin in enumerate(coins):
        if coin not in prices_data:
            continue

        data = prices_data[coin]
        row, col = idx // cols, idx % cols
        x = margin_x + col * (tile_w + gap_x)
        y = grid_top + row * (tile_h + gap_y)
        change = float(data["change_24h"])
        color_rgb = hex_to_rgb(data.get("color", "#7A879A"))

        # 3D card shadow
        shadow = Image.new("RGBA", (tile_w + 28, tile_h + 28), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle([14, 14, tile_w + 14, tile_h + 14], radius=30, fill=(0, 0, 0, 90))
        img.alpha_composite(shadow, (x - 6, y + 10))

        # Outer glow frame
        frame = tuple(min(255, int(c * 1.15)) for c in color_rgb)
        draw.rounded_rectangle([x - 2, y - 2, x + tile_w + 2, y + tile_h + 2], radius=26, outline=frame, width=3)

        # Card body gradient
        for dy in range(tile_h):
            t = dy / max(1, tile_h - 1)
            r = int(36 + 10 * t)
            g = int(46 + 10 * t)
            b = int(62 + 18 * t)
            draw.line([(x, y + dy), (x + tile_w, y + dy)], fill=(r, g, b))

        # Top highlight + bottom bevel (3D feel)
        draw.rounded_rectangle([x + 14, y + 12, x + tile_w - 14, y + 24], radius=6, fill=frame)
        draw.line([(x + 16, y + 38), (x + tile_w - 16, y + 38)], fill=(255, 255, 255, 120), width=1)
        draw.line([(x + 14, y + tile_h - 10), (x + tile_w - 14, y + tile_h - 10)], fill=(0, 0, 0), width=2)
        draw.line([(x + tile_w - 10, y + 14), (x + tile_w - 10, y + tile_h - 12)], fill=(0, 0, 0), width=2)

        # Inner border
        draw.rounded_rectangle([x + 1, y + 1, x + tile_w - 1, y + tile_h - 1], radius=24, outline=(85, 100, 128), width=1)

        # Logo
        logo_url = data.get("logo_url")
        logo_size = 64
        if logo_url:
            logo = await download_logo(logo_url, logo_size)
            if logo:
                img.paste(logo, (x + (tile_w - logo_size) // 2, y + 42), logo)

        # Symbol
        symbol = data.get("symbol", coin.upper())
        font_symbol = get_font(22, bold=True)
        sw2 = draw.textbbox((0, 0), symbol, font=font_symbol)[2]
        draw.text((x + (tile_w - sw2) // 2, y + 118), symbol, fill="#EAF0FB", font=font_symbol, stroke_width=1, stroke_fill="#1A2130")

        # Price
        price_text = format_price(float(data["price"]))
        font_price = get_font(20, bold=True)
        pw = draw.textbbox((0, 0), price_text, font=font_price)[2]
        draw.text((x + (tile_w - pw) // 2, y + 172), price_text, fill="#FFFFFF", font=font_price)

        # Change badge
        change_text = f"{'+' if change >= 0 else ''}{change:.2f}%"
        font_change = get_font(16, bold=True)
        twc = draw.textbbox((0, 0), change_text, font=font_change)[2]
        pill_w = max(136, twc + 34)
        pill_h = 46
        px = x + (tile_w - pill_w) // 2
        py = y + 210
        if change >= 0:
            pill_bg = (9, 72, 56)
            pill_fg = "#08F0A0"
        else:
            pill_bg = (92, 30, 38)
            pill_fg = "#FF5D66"
        draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=22, fill=pill_bg, outline=pill_fg, width=2)
        draw.text((px + (pill_w - twc) // 2, py + 8), change_text, fill=pill_fg, font=font_change)

    # Footer
    font_wm = get_font(11)
    ts = datetime.now().strftime("%H:%M:%S")
    watermark_text = f"{WATERMARK} - {ts}"
    ww = draw.textbbox((0, 0), watermark_text, font=font_wm)[2]
    draw.text(((width - ww) // 2, height - 36), watermark_text, fill="#8795AD", font=font_wm)

    return img.convert("RGB")

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
    badge_y = 280
    badge_w, badge_h = 220, 75
    
    font_label = get_font(11, bold=True)
    font_value = get_font(22, bold=True)
    
    # 24h badge
    draw.text((70, badge_y - 30), "24H CHANGE", fill='#888888', font=font_label)
    bg_24h = (0, 50, 30) if change_24h >= 0 else (50, 0, 20)
    draw.rounded_rectangle([70, badge_y, 70 + badge_w, badge_y + badge_h], radius=30, fill=bg_24h)
    
    # Colored border
    border_24h = '#00FF88' if change_24h >= 0 else '#FF4444'
    draw.rounded_rectangle([70, badge_y, 70 + badge_w, badge_y + badge_h], radius=30, outline=border_24h, width=2)
    
    color_24h = '#00FF88' if change_24h >= 0 else '#FF4444'
    text_24h = f"{'+' if change_24h >= 0 else ''}{change_24h:.2f}%"
    bbox = draw.textbbox((0, 0), text_24h, font=font_value)
    text_w = bbox[2] - bbox[0]
    draw.text((70 + (badge_w - text_w) // 2, badge_y + 22), text_24h, fill=color_24h, font=font_value)
    
    # 7d badge
    weekly_x = 320
    draw.text((weekly_x, badge_y - 30), "7D CHANGE", fill='#888888', font=font_label)
    bg_7d = (0, 50, 30) if change_7d >= 0 else (50, 0, 20)
    draw.rounded_rectangle([weekly_x, badge_y, weekly_x + badge_w, badge_y + badge_h], radius=30, fill=bg_7d)
    
    # Colored border
    border_7d = '#00FF88' if change_7d >= 0 else '#FF4444'
    draw.rounded_rectangle([weekly_x, badge_y, weekly_x + badge_w, badge_y + badge_h], radius=30, outline=border_7d, width=2)
    
    color_7d = '#00FF88' if change_7d >= 0 else '#FF4444'
    text_7d = f"{'+' if change_7d >= 0 else ''}{change_7d:.2f}%"
    bbox_7d = draw.textbbox((0, 0), text_7d, font=font_value)
    text_w_7d = bbox_7d[2] - bbox_7d[0]
    draw.text((weekly_x + (badge_w - text_w_7d) // 2, badge_y + 22), text_7d, fill=color_7d, font=font_value)
    
    # Chart section
    chart_y, chart_h = 400, 270
    chart_w, chart_x = width - 140, 70
    
    # Chart background with glow
    for i in range(3, 0, -1):
        glow_rgb = tuple(int(c * (i / 6)) for c in color_rgb)
        draw.rounded_rectangle([chart_x-i, chart_y-i, chart_x+chart_w+i, chart_y+chart_h+i],
                              radius=18, outline=glow_rgb, width=2)
    
    draw.rounded_rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h],
                          radius=15, fill=(25, 30, 40))
    
    font_chart = get_font(12, bold=True)
    draw.text((chart_x + 10, chart_y - 35), "7-DAY PRICE CHART", fill='#888888', font=font_chart)
    
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
    
    # Watermark with timestamp (prevents Telegram cache in groups)
    font_watermark = get_font(10)
    timestamp = datetime.now().strftime("%H:%M:%S")
    watermark_text = f"{WATERMARK} • {timestamp}"
    draw.text((width//2 - 140, height - 40), watermark_text, fill='#555555', font=font_watermark)
    
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
    
    # Watermark with timestamp (prevents Telegram cache in groups)
    font_watermark = get_font(10)
    timestamp = datetime.now().strftime("%H:%M:%S")
    watermark_text = f"{WATERMARK} • {timestamp}"
    draw.text((width//2 - 140, height - 40), watermark_text, fill='#555555', font=font_watermark)
    
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
    
    # Watermark with timestamp (prevents Telegram cache in groups)
    font_watermark = get_font(10)
    timestamp = datetime.now().strftime("%H:%M:%S")
    watermark_text = f"{WATERMARK} • {timestamp}"
    draw.text((width//2 - 140, height - 40), watermark_text, fill='#555555', font=font_watermark)
    
    return img

def image_to_bytes(img):
    """Convert image to bytes with aggressive cache-busting for Telegram groups"""
    import random
    import time
    
    # Method 1: Add invisible random noise to multiple pixels
    draw = ImageDraw.Draw(img)
    for _ in range(5):
        x, y = random.randint(0, img.width-1), random.randint(0, img.height-1)
        current_pixel = img.getpixel((x, y))
        
        if isinstance(current_pixel, tuple):
            new_pixel = tuple(min(255, max(0, c + random.randint(-2, 2))) for c in current_pixel)
            draw.point((x, y), fill=new_pixel)
    
    # Method 2: Add timestamp metadata to PNG
    from PIL import PngImagePlugin
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("timestamp", str(time.time()))
    metadata.add_text("random", str(random.randint(1000000, 9999999)))
    
    bio = io.BytesIO()
    img.save(bio, format='PNG', pnginfo=metadata)
    bio.seek(0)
    return bio
