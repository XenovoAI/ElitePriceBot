from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import asyncio
import aiohttp
import random
from datetime import datetime, timedelta
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
    """Premium 3D board template with bold typography and crisp mobile layout."""
    width, height = 1080, 1350
    img = Image.new("RGBA", (width, height), (8, 12, 24, 255))
    draw = ImageDraw.Draw(img)

    # Deep navy gradient background
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(8 + (22 - 8) * t)
        g = int(12 + (20 - 12) * t)
        b = int(24 + (40 - 24) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Premium ambient shapes
    ambient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ad = ImageDraw.Draw(ambient)
    ad.ellipse([-160, -120, 440, 420], fill=(0, 170, 255, 26))
    ad.ellipse([610, -80, 1260, 520], fill=(0, 235, 160, 22))
    ad.ellipse([130, 980, 980, 1700], fill=(255, 150, 50, 15))
    img = Image.alpha_composite(img, ambient)
    draw = ImageDraw.Draw(img)

    # Header plate
    draw.rounded_rectangle([140, 28, width - 140, 118], radius=30, fill=(20, 30, 52, 170), outline=(60, 82, 124, 180), width=2)
    title = "CONE MARKET BOARD"
    subtitle = "Premium Top 8 | Live 24H"
    font_title = get_font(28, bold=True)
    font_sub = get_font(12, bold=True)
    tw = draw.textbbox((0, 0), title, font=font_title)[2]
    sw = draw.textbbox((0, 0), subtitle, font=font_sub)[2]
    draw.text(((width - tw) // 2, 46), title, fill="#F5F8FF", font=font_title)
    draw.text(((width - sw) // 2, 88), subtitle, fill="#C2D0EA", font=font_sub)

    coins = ["btc", "eth", "sol", "ton", "ltc", "xrp", "bnb", "trx"]
    cols = 2
    margin_x = 42
    gap_x = 30
    gap_y = 24
    grid_top = 148
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

    for idx, coin in enumerate(coins):
        if coin not in prices_data:
            continue

        data = prices_data[coin]
        row, col = idx // cols, idx % cols
        x = margin_x + col * (tile_w + gap_x)
        y = grid_top + row * (tile_h + gap_y)
        change = float(data["change_24h"])
        color_rgb = hex_to_rgb(data.get("color", "#7A879A"))

        # Drop shadow stack for 3D depth
        shadow1 = Image.new("RGBA", (tile_w + 44, tile_h + 44), (0, 0, 0, 0))
        sd1 = ImageDraw.Draw(shadow1)
        sd1.rounded_rectangle([20, 20, tile_w + 20, tile_h + 20], radius=30, fill=(0, 0, 0, 95))
        img.alpha_composite(shadow1, (x - 12, y + 10))

        shadow2 = Image.new("RGBA", (tile_w + 24, tile_h + 24), (0, 0, 0, 0))
        sd2 = ImageDraw.Draw(shadow2)
        sd2.rounded_rectangle([10, 10, tile_w + 10, tile_h + 10], radius=28, fill=(0, 0, 0, 70))
        img.alpha_composite(shadow2, (x - 4, y + 6))

        # Outer neon frame
        frame = tuple(min(255, int(c * 1.2)) for c in color_rgb)
        draw.rounded_rectangle([x - 2, y - 2, x + tile_w + 2, y + tile_h + 2], radius=26, outline=frame, width=3)

        # Card body with dark metallic gradient
        for dy in range(tile_h):
            t = dy / max(1, tile_h - 1)
            r = int(34 + (46 - 34) * t)
            g = int(42 + (56 - 42) * t)
            b = int(58 + (78 - 58) * t)
            draw.line([(x, y + dy), (x + tile_w, y + dy)], fill=(r, g, b))

        # Upper sheen and beveled edges
        draw.rounded_rectangle([x + 14, y + 12, x + tile_w - 14, y + 24], radius=6, fill=frame)
        draw.line([(x + 16, y + 34), (x + tile_w - 16, y + 34)], fill=(235, 242, 255, 140), width=1)
        draw.line([(x + 14, y + tile_h - 9), (x + tile_w - 14, y + tile_h - 9)], fill=(10, 14, 22), width=2)
        draw.line([(x + tile_w - 10, y + 14), (x + tile_w - 10, y + tile_h - 12)], fill=(10, 14, 22), width=2)
        draw.rounded_rectangle([x + 1, y + 1, x + tile_w - 1, y + tile_h - 1], radius=24, outline=(84, 99, 126), width=1)

        # Rank chip
        rank_bg = (20, 30, 48)
        rank_fg = "#BFD2F7"
        draw.rounded_rectangle([x + 16, y + 16, x + 74, y + 44], radius=12, fill=rank_bg, outline=(87, 104, 138), width=1)
        draw.text((x + 29, y + 21), f"#{idx + 1}", fill=rank_fg, font=get_font(10, bold=True))

        # Logo
        logo_url = data.get("logo_url")
        logo_size = 64
        if logo_url:
            logo = await download_logo(logo_url, logo_size)
            if logo:
                img.paste(logo, (x + (tile_w - logo_size) // 2, y + 42), logo)

        # Symbol (bold with stroke)
        symbol = data.get("symbol", coin.upper())
        font_symbol = get_font(24, bold=True)
        sw2 = draw.textbbox((0, 0), symbol, font=font_symbol)[2]
        draw.text(
            (x + (tile_w - sw2) // 2, y + 118),
            symbol,
            fill="#F0F4FE",
            font=font_symbol,
            stroke_width=1,
            stroke_fill="#12192A",
        )

        # Price (bolder)
        price_text = format_price(float(data["price"]))
        font_price = get_font(22, bold=True)
        pw = draw.textbbox((0, 0), price_text, font=font_price)[2]
        draw.text((x + (tile_w - pw) // 2, y + 171), price_text, fill="#FFFFFF", font=font_price)

        # Change badge (high contrast)
        change_text = f"{'+' if change >= 0 else ''}{change:.2f}%"
        font_change = get_font(17, bold=True)
        twc = draw.textbbox((0, 0), change_text, font=font_change)[2]
        pill_w = max(142, twc + 36)
        pill_h = 48
        px = x + (tile_w - pill_w) // 2
        py = y + 209
        if change >= 0:
            pill_bg = (7, 76, 58)
            pill_fg = "#09F2A2"
        else:
            pill_bg = (92, 29, 39)
            pill_fg = "#FF626C"
        draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=23, fill=pill_bg, outline=pill_fg, width=2)
        draw.text((px + (pill_w - twc) // 2, py + 9), change_text, fill=pill_fg, font=font_change)

    # Footer
    font_wm = get_font(11, bold=True)
    ts = datetime.now().strftime("%H:%M:%S")
    watermark_text = f"{WATERMARK} - {ts}"
    ww = draw.textbbox((0, 0), watermark_text, font=font_wm)[2]
    draw.text(((width - ww) // 2, height - 36), watermark_text, fill="#95A5C2", font=font_wm)

    return img.convert("RGB")

async def create_top_lux_grid_async(prices_data):
    """Luxury black-gold demo board for /toplux."""
    width, height = 1080, 1350
    img = Image.new("RGBA", (width, height), (7, 7, 9, 255))
    draw = ImageDraw.Draw(img)

    # Black-gold backdrop
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(8 + (22 - 8) * t)
        g = int(8 + (18 - 8) * t)
        b = int(10 + (20 - 10) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    gl = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.ellipse([-160, -120, 400, 380], fill=(255, 202, 95, 24))
    gd.ellipse([680, -100, 1260, 480], fill=(201, 147, 56, 18))
    gd.ellipse([140, 940, 980, 1660], fill=(255, 170, 70, 12))
    img = Image.alpha_composite(img, gl)
    draw = ImageDraw.Draw(img)

    # Header plate
    draw.rounded_rectangle([130, 28, width - 130, 120], radius=28, fill=(22, 19, 16, 210), outline=(196, 146, 62, 210), width=2)
    draw.text(((width - draw.textbbox((0, 0), "ELITE MARKET BOARD", font=get_font(27, bold=True))[2]) // 2, 46),
              "ELITE MARKET BOARD", fill="#F9E3B0", font=get_font(27, bold=True))
    sub = "Top 8 coins | Luxury Demo"
    draw.text(((width - draw.textbbox((0, 0), sub, font=get_font(12, bold=True))[2]) // 2, 90),
              sub, fill="#D2B98A", font=get_font(12, bold=True))

    coins = ["btc", "eth", "sol", "ton", "ltc", "xrp", "bnb", "trx"]
    cols = 2
    margin_x, gap_x, gap_y = 42, 30, 24
    grid_top = 148
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

    for idx, coin in enumerate(coins):
        if coin not in prices_data:
            continue
        data = prices_data[coin]
        row, col = idx // cols, idx % cols
        x = margin_x + col * (tile_w + gap_x)
        y = grid_top + row * (tile_h + gap_y)
        change = float(data["change_24h"])

        # Deep shadow
        sh = Image.new("RGBA", (tile_w + 40, tile_h + 40), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([18, 18, tile_w + 18, tile_h + 18], radius=30, fill=(0, 0, 0, 110))
        img.alpha_composite(sh, (x - 10, y + 10))

        # Card body
        for dy in range(tile_h):
            t = dy / max(1, tile_h - 1)
            r = int(26 + (40 - 26) * t)
            g = int(24 + (34 - 24) * t)
            b = int(22 + (30 - 22) * t)
            draw.line([(x, y + dy), (x + tile_w, y + dy)], fill=(r, g, b))

        gold = (214, 165, 75)
        draw.rounded_rectangle([x - 2, y - 2, x + tile_w + 2, y + tile_h + 2], radius=26, outline=gold, width=3)
        draw.rounded_rectangle([x + 14, y + 12, x + tile_w - 14, y + 24], radius=6, fill=gold)
        draw.line([(x + 16, y + 34), (x + tile_w - 16, y + 34)], fill=(255, 233, 182, 150), width=1)
        draw.rounded_rectangle([x + 1, y + 1, x + tile_w - 1, y + tile_h - 1], radius=24, outline=(116, 95, 57), width=1)

        # Logo + texts
        logo_url = data.get("logo_url")
        if logo_url:
            logo = await download_logo(logo_url, 64)
            if logo:
                img.paste(logo, (x + (tile_w - 64) // 2, y + 42), logo)

        symbol = data.get("symbol", coin.upper())
        fs = get_font(24, bold=True)
        fw = draw.textbbox((0, 0), symbol, font=fs)[2]
        draw.text((x + (tile_w - fw) // 2, y + 118), symbol, fill="#FFF4D7", font=fs, stroke_width=1, stroke_fill="#1A1511")

        price = format_price(float(data["price"]))
        fp = get_font(22, bold=True)
        pw = draw.textbbox((0, 0), price, font=fp)[2]
        draw.text((x + (tile_w - pw) // 2, y + 171), price, fill="#FFFFFF", font=fp)

        ch = f"{'+' if change >= 0 else ''}{change:.2f}%"
        fc = get_font(17, bold=True)
        cw = draw.textbbox((0, 0), ch, font=fc)[2]
        pill_w, pill_h = max(142, cw + 36), 48
        px, py = x + (tile_w - pill_w) // 2, y + 209
        if change >= 0:
            bg, fg = (27, 76, 54), "#15F19F"
        else:
            bg, fg = (89, 33, 38), "#FF6C74"
        draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=23, fill=bg, outline=fg, width=2)
        draw.text((px + (pill_w - cw) // 2, py + 9), ch, fill=fg, font=fc)

    # Footer
    wm = f"{WATERMARK} - {datetime.now().strftime('%H:%M:%S')}"
    fw = get_font(11, bold=True)
    ww = draw.textbbox((0, 0), wm, font=fw)[2]
    draw.text(((width - ww) // 2, height - 36), wm, fill="#BBA57C", font=fw)

    return img.convert("RGB")

async def create_coin_card_async(coin_data, chart_data=None):
    width, height = 1200, 760
    accent = hex_to_rgb(coin_data["color"])
    price = float(coin_data["price"])
    change_24h = float(coin_data["change_24h"])
    change_7d = float(coin_data.get("change_7d", 0))

    def ui_font(size, bold=False):
        """Card-specific typography: cleaner and less oversized than global font helper."""
        fonts = [
            "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for f in fonts:
            try:
                return ImageFont.truetype(f, size)
            except:
                continue
        return ImageFont.load_default()

    # Clean classic background
    img = Image.new("RGB", (width, height), (15, 22, 33))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(18 + (28 - 18) * t)
        g = int(24 + (33 - 24) * t)
        b = int(34 + (49 - 34) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Main board
    x0, y0 = 56, 44
    bw, bh = width - 112, height - 96
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=34, fill=(20, 28, 40))
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=34, outline=(72, 88, 112), width=2)
    draw.rounded_rectangle([x0 + 8, y0 + 8, x0 + bw - 8, y0 + bh - 8], radius=28, outline=(52, 66, 88), width=1)

    # Header row
    num_text = f"{price:,.4f}" if price < 10 else f"{price:,.2f}"
    draw.text((104, 96), "$", fill=coin_data["color"], font=ui_font(52, bold=True))
    draw.text((156, 96), num_text, fill="#EEF3FA", font=ui_font(72, bold=True))

    # Coin pill top-right
    pill_x, pill_y = x0 + bw - 312, 96
    pill_w, pill_h = 262, 86
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=38, fill=(72, 86, 108))
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=38, outline=(112, 128, 153), width=2)
    logo = None
    logo_url = coin_data.get("logo_url")
    if logo_url:
        logo = await download_logo(logo_url, 44)
    if logo:
        img.paste(logo, (pill_x + 16, pill_y + 21), logo)
    symbol = coin_data.get("symbol", "").upper()
    draw.text((pill_x + 74, pill_y + 24), symbol if symbol else coin_data["name"], fill="#F4F7FC", font=ui_font(48, bold=True))

    # Metric boxes
    label_font = ui_font(39, bold=False)
    value_font = ui_font(54, bold=True)

    def metric_box(mx, my, label, value):
        pos = value >= 0
        box_bg = (34, 47, 66)
        draw.rounded_rectangle([mx, my, mx + 500, my + 86], radius=24, fill=box_bg)
        draw.rounded_rectangle([mx, my, mx + 500, my + 86], radius=24, outline=(63, 79, 104), width=1)
        draw.text((mx + 26, my + 10), label, fill="#8F9FB8", font=label_font)
        txt = f"{'+' if pos else ''}{value:.2f}%"
        col = "#42D575" if pos else "#FF646B"
        draw.text((mx + 26, my + 34), txt, fill=col, font=value_font)
        arrow = "▲" if pos else "▼"
        draw.text((mx + 444, my + 24), arrow, fill=col, font=ui_font(48, bold=True))

    metric_box(x0 + 28, 232, "24H CHANGE", change_24h)
    metric_box(x0 + 548, 232, "7D CHANGE", change_7d)

    # Chart frame
    chart_x, chart_y = x0 + 32, 348
    chart_w, chart_h = bw - 64, 286
    draw.rounded_rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h], radius=8, fill=(21, 29, 42))
    draw.rounded_rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h], radius=8, outline=(81, 98, 124), width=1)

    grid_col = (76, 92, 116)
    for i in range(1, 5):
        gy = chart_y + int(i * chart_h / 5)
        draw.line([(chart_x, gy), (chart_x + chart_w, gy)], fill=grid_col, width=1)
    for i in range(1, 8):
        gx = chart_x + int(i * chart_w / 8)
        draw.line([(gx, chart_y), (gx, chart_y + chart_h)], fill=grid_col, width=1)

    if chart_data and len(chart_data) > 10:
        # Smooth noisy candles for a cleaner premium curve
        smooth = []
        win = 3
        for i in range(len(chart_data)):
            lo = max(0, i - win)
            hi = min(len(chart_data), i + win + 1)
            smooth.append(sum(chart_data[lo:hi]) / (hi - lo))

        mn, mx = min(smooth), max(smooth)
        rng = mx - mn if mx != mn else 1.0
        pad_x, pad_y = 12, 14
        pts = []
        n = len(smooth)
        for i, p in enumerate(smooth):
            px = chart_x + pad_x + (i / (n - 1)) * (chart_w - 2 * pad_x)
            py = chart_y + pad_y + (chart_h - 2 * pad_y) - ((p - mn) / rng) * (chart_h - 2 * pad_y)
            pts.append((px, py))

        line_col = tuple(min(255, int(c * 1.15)) for c in accent)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        area = pts + [(pts[-1][0], chart_y + chart_h - 2), (pts[0][0], chart_y + chart_h - 2)]
        od.polygon(area, fill=(line_col[0], line_col[1], line_col[2], 44))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.line(pts, fill=line_col, width=6)
    else:
        draw.text((chart_x + chart_w // 2 - 80, chart_y + chart_h // 2 - 12), "Loading chart...", fill="#8C9CB3", font=ui_font(20))

    # Date ticks
    tick_font = ui_font(20, bold=False)
    now = datetime.now()
    ticks = [(now - timedelta(days=day_back)).strftime("%b %d").upper() for day_back in range(7, -1, -1)]
    for i, t in enumerate(ticks):
        tx = chart_x + 4 + i * ((chart_w - 8) // 7)
        draw.text((tx, chart_y + chart_h + 10), t, fill="#8596AE", font=tick_font)

    # Watermark
    wm = "Powered by @conesociety"
    ww = draw.textbbox((0, 0), wm, font=ui_font(26, bold=False))[2]
    draw.text(((width - ww) // 2, height - 28), wm, fill="#9EB0C7", font=ui_font(26, bold=False))

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
