from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import aiohttp
import asyncio
from datetime import datetime
from config import WATERMARK
import os

# Cache for downloaded logos
logo_cache = {}

async def download_logo(url, size=50):
    """Download and cache coin logo with faster timeout"""
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
    except Exception as e:
        print(f"Failed to download logo from {url}: {e}")
    
    return None

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    fonts_to_try = [
        "arialbd.ttf" if bold else "arial.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "segoeui.ttf",
        "calibri.ttf"
    ]
    for font in fonts_to_try:
        try:
            return ImageFont.truetype(font, size)
        except:
            continue
    return ImageFont.load_default()

def create_gradient(width, height, color_start, color_end, direction='vertical'):
    """Create a gradient image"""
    base = Image.new('RGB', (width, height), color_start)
    top = Image.new('RGB', (width, height), color_end)
    mask = Image.new('L', (width, height))
    mask_data = []
    
    for y in range(height):
        for x in range(width):
            if direction == 'vertical':
                mask_data.append(int(255 * (y / height)))
            else:
                mask_data.append(int(255 * (x / width)))
    
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def draw_rounded_rectangle(draw, coords, radius, fill, outline=None, width=0):
    x1, y1, x2, y2 = coords
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
    draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)
    
    if outline and width > 0:
        draw.arc([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=outline, width=width)
        draw.arc([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=outline, width=width)
        draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=width)
        draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=width)
        draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=width)
        draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=width)

def draw_coin_logo(img, logo, x, y, size):
    """Paste a coin logo onto the image"""
    if logo:
        try:
            # Ensure both images are in the same mode
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Create a circular mask
            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, size, size], fill=255)
            
            # Create a temporary image to paste the logo
            temp = Image.new('RGBA', img.size, (0, 0, 0, 0))
            temp.paste(logo, (x, y), mask)
            
            # Composite the temp image onto the main image
            img = Image.alpha_composite(img, temp)
            
            return img
        except Exception as e:
            print(f"Failed to paste logo: {e}")
    return img


async def create_top_grid_async(prices_data):
    """Create a professional grid with real coin logos - optimized"""
    width, height = 1200, 750
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)
    
    coins = ["btc", "eth", "sol", "ton", "ltc", "xrp", "bnb", "trx"]
    
    # Card dimensions
    tile_width = 360
    tile_height = 150
    padding = 25
    start_x = 40
    start_y = 40
    
    for idx, coin in enumerate(coins):
        if coin not in prices_data:
            continue
        
        data = prices_data[coin]
        row = idx // 3
        col = idx % 3
        
        x = start_x + col * (tile_width + padding)
        y = start_y + row * (tile_height + padding)
        
        change = data["change_24h"]
        base_color = hex_to_rgb(data["color"])
        
        # Create gradient background
        if change >= 0:
            color_start = (int(base_color[0] * 0.15), int(base_color[1] * 0.2), int(base_color[2] * 0.15))
            color_end = (int(base_color[0] * 0.25), int(base_color[1] * 0.35), int(base_color[2] * 0.25))
        else:
            color_start = (int(base_color[0] * 0.15), int(base_color[1] * 0.15), int(base_color[2] * 0.15))
            color_end = (int(base_color[0] * 0.25), int(base_color[1] * 0.2), int(base_color[2] * 0.2))
        
        # Create tile gradient
        tile_gradient = create_gradient(tile_width, tile_height, color_start, color_end, 'vertical')
        
        # Create rounded mask
        mask = Image.new('L', (tile_width, tile_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, tile_width, tile_height], radius=25, fill=255)
        
        # Paste gradient with rounded corners
        img.paste(tile_gradient, (x, y), mask)
        
        # Add border
        border_color = tuple(min(255, int(c * 0.6)) for c in base_color)
        draw.rounded_rectangle([x, y, x + tile_width, y + tile_height], radius=25, 
                              outline=border_color, width=2)
        
        # Draw coin logo (skip if takes too long)
        icon_size = 40
        icon_x = x + 20
        icon_y = y + 20
        
        logo_url = data.get("logo_url")
        if logo_url:
            try:
                logo = await asyncio.wait_for(download_logo(logo_url, icon_size), timeout=1.0)
                if logo:
                    img = draw_coin_logo(img, logo, icon_x, icon_y, icon_size)
                    draw = ImageDraw.Draw(img)
            except asyncio.TimeoutError:
                pass  # Skip logo if it takes too long
        
        # Fonts
        font_name = get_font(32, bold=True)
        font_price = get_font(56, bold=True)
        font_change = get_font(28, bold=True)
        
        # Draw coin name
        draw.text((icon_x + icon_size + 15, y + 28), data["name"], fill='white', font=font_name)
        
        # Draw price
        price_text = f"${data['price']:,.2f}" if data['price'] < 1000 else f"${data['price']:,.0f}"
        price_color = base_color
        draw.text((x + 20, y + 70), price_text, fill=price_color, font=font_price)
        
        # Draw change percentage
        change_color = '#00ff88' if change >= 0 else '#ff4444'
        change_text = f"{'+' if change >= 0 else ''}{change:.2f}%"
        draw.text((x + 20, y + 115), change_text, fill=change_color, font=font_change)
    
    # Add watermark
    font_watermark = get_font(22)
    draw.text((50, height - 40), WATERMARK, fill='#555555', font=font_watermark)
    
    return img



async def create_coin_card_async(coin_data, chart_data=None):
    """Create a professional coin card with patterned background like reference"""
    width, height = 1000, 650
    
    # Main background with pattern
    img = Image.new('RGB', (width, height), color='#000000')
    
    # Coin color
    color_rgb = hex_to_rgb(coin_data["color"])
    
    # Create patterned background border (like TON logo pattern)
    pattern_color = (int(color_rgb[0] * 0.4), int(color_rgb[1] * 0.5), int(color_rgb[2] * 0.5))
    
    # Draw outer rounded rectangle with pattern color
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([30, 30, width - 30, height - 30], radius=35, fill=pattern_color)
    
    # Inner black card
    draw.rounded_rectangle([50, 50, width - 50, height - 50], radius=30, fill='#000000')
    
    # Top right: Coin name badge
    badge_width = 280
    badge_height = 70
    badge_x = width - badge_width - 90
    badge_y = 80
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_width, badge_y + badge_height], 
                          radius=35, fill='#e8f0f8')
    
    # Download and draw coin logo on badge
    icon_size = 50
    icon_x = badge_x + 15
    icon_y = badge_y + 10
    
    logo_url = coin_data.get("logo_url")
    if logo_url:
        try:
            logo = await asyncio.wait_for(download_logo(logo_url, icon_size), timeout=1.0)
            if logo:
                img = draw_coin_logo(img, logo, icon_x, icon_y, icon_size)
        except asyncio.TimeoutError:
            pass
    
    # Coin name on badge
    font_badge = get_font(38, bold=True)
    draw = ImageDraw.Draw(img)  # Recreate draw after image modification
    draw.text((icon_x + icon_size + 15, badge_y + 18), coin_data["name"], fill='#000000', font=font_badge)
    
    # Large price display (left side)
    font_price = get_font(90, bold=True)
    price_text = f"${coin_data['price']:,.4f}" if coin_data['price'] < 10 else f"${coin_data['price']:,.2f}"
    draw.text((90, 90), price_text, fill=color_rgb, font=font_price)
    
    # Change badges section
    change_24h = coin_data["change_24h"]
    change_7d = coin_data.get("change_7d", 0)
    
    badge_y = 210
    badge_width_change = 200
    badge_height_change = 70
    
    # Daily change label and badge
    font_label = get_font(20, bold=True)
    font_change_value = get_font(38, bold=True)
    
    draw.text((90, badge_y), "DAILY CHANGE", fill='#ff4444', font=font_label)
    
    # Daily change pill
    change_bg = (80, 20, 20) if change_24h < 0 else (20, 80, 40)
    draw.rounded_rectangle([90, badge_y + 30, 90 + badge_width_change, badge_y + 30 + badge_height_change], 
                          radius=35, fill=change_bg)
    
    change_color_24h = '#ff4444' if change_24h < 0 else '#00ff88'
    change_text_24h = f"{'+' if change_24h >= 0 else ''}{change_24h:.2f}%"
    
    # Center text in pill
    text_bbox = draw.textbbox((0, 0), change_text_24h, font=font_change_value)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = 90 + (badge_width_change - text_width) // 2
    draw.text((text_x, badge_y + 45), change_text_24h, fill=change_color_24h, font=font_change_value)
    
    # Weekly change label and badge
    weekly_x = 320
    draw.text((weekly_x, badge_y), "WEEKLY CHANGE", fill='#ff4444' if change_7d < 0 else '#00ff88', font=font_label)
    
    # Weekly change pill
    change_bg_7d = (80, 20, 20) if change_7d < 0 else (20, 80, 40)
    draw.rounded_rectangle([weekly_x, badge_y + 30, weekly_x + badge_width_change, badge_y + 30 + badge_height_change], 
                          radius=35, fill=change_bg_7d)
    
    change_color_7d = '#ff4444' if change_7d < 0 else '#00ff88'
    change_text_7d = f"{'+' if change_7d >= 0 else ''}{change_7d:.2f}%"
    
    # Center text in pill
    text_bbox_7d = draw.textbbox((0, 0), change_text_7d, font=font_change_value)
    text_width_7d = text_bbox_7d[2] - text_bbox_7d[0]
    text_x_7d = weekly_x + (badge_width_change - text_width_7d) // 2
    draw.text((text_x_7d, badge_y + 45), change_text_7d, fill=change_color_7d, font=font_change_value)
    
    # Chart section
    if chart_data and len(chart_data) > 1:
        chart_y = 380
        chart_height = 180
        chart_width = width - 180
        chart_x = 90
        
        min_price = min(chart_data)
        max_price = max(chart_data)
        price_range = max_price - min_price if max_price != min_price else 1
        
        # Calculate points
        points = []
        for i, price in enumerate(chart_data):
            x = chart_x + (i / (len(chart_data) - 1)) * chart_width
            y = chart_y + chart_height - ((price - min_price) / price_range) * chart_height
            points.append((x, y))
        
        # Draw filled area under line
        if len(points) > 1:
            fill_points = points + [(chart_x + chart_width, chart_y + chart_height), (chart_x, chart_y + chart_height)]
            
            # Create semi-transparent fill
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            fill_color = (80, 20, 20, 120) if change_7d < 0 else (*color_rgb, 80)
            overlay_draw.polygon(fill_points, fill=fill_color)
            
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # Draw line
            line_color = (180, 40, 40) if change_7d < 0 else color_rgb
            draw.line(points, fill=line_color, width=4)
        
        # Draw date labels
        font_date = get_font(16)
        dates = ["Jan. 22", "Jan. 23", "Jan. 24", "Jan. 25", "Jan. 26", "Jan. 27", "Jan. 28", "Jan. 29"]
        for i in range(0, 8, 2):  # Show every other date
            x = chart_x + (i / 7) * chart_width
            draw.text((x - 20, chart_y + chart_height + 10), dates[i], fill='#666666', font=font_date)
    
    return img



async def create_convert_card_async(coin_data, amount):
    """Create a professional conversion card with patterned background"""
    width, height = 900, 650
    
    # Main background
    img = Image.new('RGB', (width, height), color='#000000')
    
    color_rgb = hex_to_rgb(coin_data["color"])
    
    # Create patterned background border
    pattern_color = (int(color_rgb[0] * 0.4), int(color_rgb[1] * 0.5), int(color_rgb[2] * 0.5))
    
    draw = ImageDraw.Draw(img)
    # Outer rounded rectangle with pattern color
    draw.rounded_rectangle([30, 30, width - 30, height - 30], radius=35, fill=pattern_color)
    
    # Inner black card
    draw.rounded_rectangle([50, 50, width - 50, height - 50], radius=30, fill='#000000')
    
    # Top input section (coin)
    input_y = 120
    input_height = 80
    input_x = 100
    input_width = width - 200
    
    draw.rounded_rectangle([input_x, input_y, input_x + input_width, input_y + input_height], 
                          radius=40, fill='#c8d5e8')
    
    # Coin logo
    icon_size = 50
    icon_x = input_x + 20
    icon_y = input_y + 15
    
    logo_url = coin_data.get("logo_url")
    if logo_url:
        try:
            logo = await asyncio.wait_for(download_logo(logo_url, icon_size), timeout=1.0)
            if logo:
                img = draw_coin_logo(img, logo, icon_x, icon_y, icon_size)
        except asyncio.TimeoutError:
            pass
    
    draw = ImageDraw.Draw(img)  # Recreate draw
    
    # Coin name
    font_coin = get_font(38, bold=True)
    draw.text((icon_x + icon_size + 20, input_y + 22), coin_data["name"], fill='#000000', font=font_coin)
    
    # Amount
    font_amount = get_font(46, bold=True)
    amount_text = f"{amount:,.4f}" if amount < 1000 else f"{amount:,.2f}"
    amount_bbox = draw.textbbox((0, 0), amount_text, font=font_amount)
    amount_width = amount_bbox[2] - amount_bbox[0]
    draw.text((input_x + input_width - amount_width - 30, input_y + 18), amount_text, fill='#000000', font=font_amount)
    
    # Conversion arrow/icon
    arrow_y = input_y + input_height + 40
    arrow_badge_size = 100
    arrow_x = width // 2 - arrow_badge_size // 2
    
    draw.rounded_rectangle([arrow_x, arrow_y, arrow_x + arrow_badge_size, arrow_y + 50], 
                          radius=25, fill='#4a5568')
    
    font_label = get_font(22, bold=True)
    draw.text((arrow_x + 18, arrow_y + 12), "Value", fill='#c8d5e8', font=font_label)
    
    # Bottom output section (USD)
    output_y = arrow_y + 90
    draw.rounded_rectangle([input_x, output_y, input_x + input_width, output_y + input_height], 
                          radius=40, fill='#c8d5e8')
    
    # USD value
    usd_value = amount * coin_data['price']
    usd_text = f"${usd_value:,.2f}"
    draw.text((input_x + 30, output_y + 18), usd_text, fill='#000000', font=font_amount)
    
    # USD badge
    usd_badge_width = 140
    usd_badge_x = input_x + input_width - usd_badge_width - 20
    draw.rounded_rectangle([usd_badge_x, output_y + 15, usd_badge_x + usd_badge_width, output_y + 65], 
                          radius=30, fill='#4a5568')
    
    font_usd = get_font(32, bold=True)
    draw.text((usd_badge_x + 25, output_y + 22), "USD", fill='white', font=font_usd)
    
    # Dollar icon
    dollar_size = 35
    dollar_x = usd_badge_x + 95
    dollar_y = output_y + 20
    draw.ellipse([dollar_x, dollar_y, dollar_x + dollar_size, dollar_y + dollar_size], fill='#c8d5e8')
    draw.text((dollar_x + 8, dollar_y + 2), "$", fill='#000000', font=get_font(24, bold=True))
    
    return img

async def create_ath_card_async(coin_data):
    """Create a professional ATH card with patterned background"""
    width, height = 900, 700
    
    # Main background
    img = Image.new('RGB', (width, height), color='#000000')
    
    color_rgb = hex_to_rgb(coin_data["color"])
    
    # Create patterned background border
    pattern_color = (int(color_rgb[0] * 0.4), int(color_rgb[1] * 0.5), int(color_rgb[2] * 0.5))
    
    draw = ImageDraw.Draw(img)
    # Outer rounded rectangle with pattern color
    draw.rounded_rectangle([30, 30, width - 30, height - 30], radius=35, fill=pattern_color)
    
    # Inner black card
    draw.rounded_rectangle([50, 50, width - 50, height - 50], radius=30, fill='#000000')
    
    # Title section with logo
    title_y = 80
    title_height = 70
    title_x = 90
    title_width = width - 180
    
    # White title badge
    draw.rounded_rectangle([title_x, title_y, title_x + title_width, title_y + title_height], 
                          radius=35, fill='#e8f0f8')
    
    # Coin logo
    icon_size = 50
    icon_x = title_x + 20
    icon_y = title_y + 10
    
    logo_url = coin_data.get("logo_url")
    if logo_url:
        try:
            logo = await asyncio.wait_for(download_logo(logo_url, icon_size), timeout=1.0)
            if logo:
                img = draw_coin_logo(img, logo, icon_x, icon_y, icon_size)
        except asyncio.TimeoutError:
            pass
    
    draw = ImageDraw.Draw(img)  # Recreate draw
    
    # Title text
    font_title = get_font(38, bold=True)
    draw.text((icon_x + icon_size + 20, title_y + 18), f"{coin_data['name']} ATH", fill='#000000', font=font_title)
    
    # Info sections with rounded badges
    y_pos = 200
    spacing = 100
    badge_width = 600
    badge_height = 70
    badge_x = (width - badge_width) // 2
    
    font_label = get_font(20)
    font_value = get_font(42, bold=True)
    
    # ATH Price
    draw.text((badge_x + 20, y_pos - 25), "ALL-TIME HIGH", fill='#888888', font=font_label)
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_width, y_pos + badge_height], 
                          radius=35, fill='#1a3a2a')
    draw.text((badge_x + 30, y_pos + 18), f"${coin_data['ath']:,.2f}", fill='#00ff88', font=font_value)
    
    # ATH Date
    y_pos += spacing
    draw.text((badge_x + 20, y_pos - 25), "ATH DATE", fill='#888888', font=font_label)
    ath_date = datetime.fromisoformat(coin_data['ath_date'].replace('Z', '+00:00'))
    date_text = ath_date.strftime("%B %d, %Y")
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_width, y_pos + badge_height], 
                          radius=35, fill='#2a2a3a')
    draw.text((badge_x + 30, y_pos + 18), date_text, fill='white', font=get_font(38, bold=True))
    
    # Current Price
    y_pos += spacing
    draw.text((badge_x + 20, y_pos - 25), "CURRENT PRICE", fill='#888888', font=font_label)
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_width, y_pos + badge_height], 
                          radius=35, fill=(int(color_rgb[0] * 0.3), int(color_rgb[1] * 0.3), int(color_rgb[2] * 0.3)))
    draw.text((badge_x + 30, y_pos + 18), f"${coin_data['price']:,.2f}", fill=color_rgb, font=font_value)
    
    # Down from ATH
    y_pos += spacing
    percent_down = ((coin_data['ath'] - coin_data['price']) / coin_data['ath']) * 100
    draw.text((badge_x + 20, y_pos - 25), "DOWN FROM ATH", fill='#888888', font=font_label)
    draw.rounded_rectangle([badge_x, y_pos, badge_x + badge_width, y_pos + badge_height], 
                          radius=35, fill='#3a1a1a')
    draw.text((badge_x + 30, y_pos + 18), f"-{percent_down:.2f}%", fill='#ff4444', font=font_value)
    
    return img

def image_to_bytes(img):
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio
