from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
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
    """ConeSociety daily board with centered symbols and tighter premium spacing."""
    width, height = 1080, 1350
    img = Image.new("RGBA", (width, height), (6, 10, 16, 255))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        t = y / max(1, height - 1)
        draw.line([(0, y), (width, y)], fill=(int(6 + 5 * t), int(10 + 14 * t), int(16 + 10 * t)))

    bg_glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(bg_glow)
    gd.ellipse([230, 930, 850, 1540], fill=(15, 198, 154, 78))
    gd.ellipse([-180, 1060, 440, 1640], fill=(10, 80, 68, 36))
    gd.ellipse([700, 1080, 1320, 1660], fill=(10, 100, 80, 30))
    bg_glow = bg_glow.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img, bg_glow)
    draw = ImageDraw.Draw(img)

    draw.rectangle([28, 26, width - 28, height - 26], outline=(24, 154, 136, 132), width=2)

    brand_left = "CONE"
    brand_right = "SOCIETY"
    f_brand = get_font(33, bold=True)
    f_daily = get_font(25, bold=True)
    bw1 = draw.textbbox((0, 0), brand_left, font=f_brand)[2]
    bw2 = draw.textbbox((0, 0), brand_right, font=f_brand)[2]
    start_x = (width - (bw1 + bw2)) // 2
    draw.text((start_x, 46), brand_left, fill="#F3F7FF", font=f_brand)
    draw.text((start_x + bw1, 46), brand_right, fill="#18D7A2", font=f_brand)
    dw = draw.textbbox((0, 0), "Daily", font=f_daily)[2]
    draw.text(((width - dw) // 2, 100), "Daily", fill="#F5F8FF", font=f_daily)

    coins = ["btc", "eth", "sol", "ltc", "ton", "xrp", "trx", "bnb"]
    cols = 3
    margin_x = 68
    gap_x = 26
    gap_y = 26
    grid_top = 170
    tile_w = (width - (2 * margin_x) - (gap_x * (cols - 1))) // cols
    tile_h = 244

    def format_price(price):
        if price >= 1000:
            return f"${price:,.2f}"
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
        accent = hex_to_rgb(data.get("color", "#6E7A8C"))

        shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle([x + 2, y + 6, x + tile_w + 2, y + tile_h + 6], radius=26, fill=(0, 0, 0, 95))
        shadow = shadow.filter(ImageFilter.GaussianBlur(3))
        img = Image.alpha_composite(img, shadow)
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle([x, y, x + tile_w, y + tile_h], radius=26, fill=(29, 32, 40))
        draw.rounded_rectangle([x, y, x + tile_w, y + tile_h], radius=26, outline=(122, 130, 146), width=1)
        draw.rounded_rectangle([x + 10, y + 10, x + tile_w - 10, y + 18], radius=3, fill=(95, 103, 122, 140))

        accent_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ad = ImageDraw.Draw(accent_layer)
        ad.ellipse([x + tile_w // 2 - 128, y + tile_h - 72, x + tile_w // 2 + 128, y + tile_h + 92], fill=(accent[0], accent[1], accent[2], 125))
        accent_layer = accent_layer.filter(ImageFilter.GaussianBlur(18))
        img = Image.alpha_composite(img, accent_layer)
        draw = ImageDraw.Draw(img)

        for py in range(y + 54, y + tile_h - 24, 34):
            draw.line([(x + 18, py), (x + tile_w - 18, py)], fill=(45, 50, 63), width=1)

        symbol = data.get("symbol", coin.upper()).upper()
        symbol_font = get_font(23, bold=True)
        symbol_w = draw.textbbox((0, 0), symbol, font=symbol_font)[2]
        logo_size = 42
        row_y = y + 22
        logo_url = data.get("logo_url")
        logo = await download_logo(logo_url, logo_size) if logo_url else None
        gap = 12 if logo else 0
        row_w = (logo_size + gap + symbol_w) if logo else symbol_w
        row_x = x + (tile_w - row_w) // 2
        if logo:
            img.paste(logo, (row_x, row_y), logo)
        draw.text((row_x + (logo_size + gap if logo else 0), row_y + 2), symbol, fill="#F2F6FC", font=symbol_font)

        price_txt = format_price(float(data["price"]))
        fp = get_font(30, bold=True)
        pw = draw.textbbox((0, 0), price_txt, font=fp)[2]
        draw.text((x + (tile_w - pw) // 2, y + 102), price_txt, fill="#F8FBFF", font=fp)

        ch = f"{'+' if change >= 0 else ''}{change:.2f}%"
        fc = get_font(24, bold=True)
        cw = draw.textbbox((0, 0), ch, font=fc)[2]
        draw.text((x + (tile_w - cw) // 2, y + 172), ch, fill=("#23FF3B" if change >= 0 else "#FF1A1A"), font=fc)

    wm = f"{WATERMARK} | {datetime.now().strftime('%H:%M:%S')}"
    fw = get_font(10, bold=True)
    ww = draw.textbbox((0, 0), wm, font=fw)[2]
    draw.text(((width - ww) // 2, height - 34), wm, fill="#A9CFC7", font=fw)

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
    width, height = 1600, 900
    accent = hex_to_rgb(coin_data["color"])
    price = float(coin_data["price"])
    change_24h = float(coin_data["change_24h"])
    usd_change_24h = price * (change_24h / 100.0)

    def ui_font(size, bold=False):
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

    def make_logo_badge(logo_img, size, fallback_text):
        badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        bd = ImageDraw.Draw(badge)
        bd.ellipse([0, 0, size - 1, size - 1], fill=(18, 22, 28), outline=(120, 126, 136), width=1)
        if logo_img:
            fit = ImageOps.contain(logo_img.convert("RGBA"), (size - 10, size - 10), Image.Resampling.LANCZOS)
            badge.alpha_composite(fit, ((size - fit.width) // 2, (size - fit.height) // 2))
        else:
            ch = (fallback_text[:1] if fallback_text else "?").upper()
            f = ui_font(int(size * 0.52), bold=True)
            tw = bd.textbbox((0, 0), ch, font=f)[2]
            th = bd.textbbox((0, 0), ch, font=f)[3]
            bd.text(((size - tw) // 2, (size - th) // 2 - 1), ch, fill="#FFFFFF", font=f)
        return badge

    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    def fit_font(text, max_w, start_size, min_size, bold=True):
        size = start_size
        while size >= min_size:
            f = ui_font(size, bold=bold)
            if draw.textbbox((0, 0), text, font=f)[2] <= max_w:
                return f
            size -= 2
        return ui_font(min_size, bold=bold)

    for y in range(height):
        t = y / max(1, height - 1)
        draw.line([(0, y), (width, y)], fill=(int(0 + 10 * t), int(0 + 8 * t), int(0 + 14 * t)))

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([width // 2 - 250, height - 205, width // 2 + 250, height + 215], fill=(accent[0], accent[1], accent[2], 120))
    glow = glow.filter(ImageFilter.GaussianBlur(24))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    draw.rectangle([52, 52, width - 52, height - 52], outline=(72, 82, 96, 170), width=2)

    left, right = "CONE", "SOCIETY"
    fb = ui_font(72, bold=True)
    lw = draw.textbbox((0, 0), left, font=fb)[2]
    rw = draw.textbbox((0, 0), right, font=fb)[2]
    tx = (width - (lw + rw)) // 2
    draw.text((tx, 40), left, fill="#F4F7FD", font=fb)
    draw.text((tx + lw, 40), right, fill="#17D39D", font=fb)

    px, py = 120, 150
    pw, ph = width - 240, height - 210
    panel_shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    psd = ImageDraw.Draw(panel_shadow)
    psd.rounded_rectangle([px + 3, py + 8, px + pw + 3, py + ph + 8], radius=78, fill=(0, 0, 0, 95))
    panel_shadow = panel_shadow.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(img, panel_shadow)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=78, fill=(20, 20, 24, 232), outline=(128, 136, 148, 184), width=2)
    draw.rounded_rectangle([px + 12, py + 12, px + pw - 12, py + 20], radius=4, fill=(160, 168, 184, 55))

    pill_x, pill_y = px + 42, py + 56
    pill_w, pill_h = 610, 140
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=58, fill=(66, 66, 70, 210), outline=(114, 120, 130, 165), width=1)

    symbol = coin_data.get("symbol", coin_data.get("name", "")).upper()
    symbol_font = fit_font(symbol, pill_w - 190, 80, 56, bold=True)
    symbol_w = draw.textbbox((0, 0), symbol, font=symbol_font)[2]
    logo_size = 88
    logo = await download_logo(coin_data.get("logo_url"), logo_size) if coin_data.get("logo_url") else None
    logo_badge = make_logo_badge(logo, logo_size, symbol)
    group_w = logo_size + 20 + symbol_w
    group_x = pill_x + (pill_w - group_w) // 2
    logo_y = pill_y + (pill_h - logo_size) // 2
    img.paste(logo_badge, (group_x, logo_y), logo_badge)
    symbol_y = pill_y + (pill_h - draw.textbbox((0, 0), symbol, font=symbol_font)[3]) // 2 - 4
    draw.text((group_x + logo_size + 20, symbol_y), symbol, fill="#F5F7FB", font=symbol_font)

    if price >= 1000:
        price_text = f"${price:,.2f}"
    elif price >= 1:
        price_text = f"${price:,.2f}"
    elif price >= 0.01:
        price_text = f"${price:,.4f}"
    else:
        price_text = f"${price:,.6f}"
    price_font = fit_font(price_text, 640, 126, 92, bold=True)
    draw.text((pill_x, py + 270), price_text, fill="#F6F8FC", font=price_font)

    metric_x = px + pw - 510
    metric_w, metric_h = 460, 186

    def metric_card(y, value_text, is_positive):
        draw.rounded_rectangle([metric_x, y, metric_x + metric_w, y + metric_h], radius=48, fill=(85, 85, 90, 188), outline=(128, 136, 146, 180), width=1)
        label = "CHANGE (24H)"
        label_font = fit_font(label, metric_w - 56, 54, 38, bold=True)
        lw2 = draw.textbbox((0, 0), label, font=label_font)[2]
        draw.text((metric_x + (metric_w - lw2) // 2, y + 26), label, fill="#F0F4F8", font=label_font)
        val_font = fit_font(value_text, metric_w - 64, 92, 62, bold=True)
        vw = draw.textbbox((0, 0), value_text, font=val_font)[2]
        col = "#26FF2B" if is_positive else "#FF1515"
        draw.text((metric_x + (metric_w - vw) // 2, y + 92), value_text, fill=col, font=val_font)

    percent_txt = f"{'+' if change_24h >= 0 else ''}{change_24h:.2f}%"
    usd_txt = f"{'+' if usd_change_24h >= 0 else '-'}${abs(usd_change_24h):,.2f}"
    metric_card(py + 56, percent_txt, change_24h >= 0)
    metric_card(py + 292, usd_txt, usd_change_24h >= 0)

    wm = f"{WATERMARK} | {datetime.now().strftime('%H:%M:%S')}"
    ww = draw.textbbox((0, 0), wm, font=ui_font(23, bold=False))[2]
    draw.text(((width - ww) // 2, height - 42), wm, fill="#A8AFBA", font=ui_font(23, bold=False))

    return img.convert("RGB")

async def create_convert_card_async(coin_data, amount, cross_data=None):
    """Premium converter card with USD + ETH/SOL/TON rows and overlap-safe typography."""
    width, height = 1200, 760
    accent = hex_to_rgb(coin_data["color"])
    usd_value = amount * float(coin_data["price"])
    symbol = (coin_data.get("symbol") or coin_data.get("name", "COIN")).upper()
    amount_text = f"{amount:,.4f}" if amount < 10 else f"{amount:,.2f}"
    usd_text = f"${usd_value:,.2f}"
    cross_data = cross_data or {}

    def cv_font(size, bold=False):
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

    def fit_font(text, max_w, start_size, min_size=16, bold=True):
        size = start_size
        while size >= min_size:
            f = cv_font(size, bold=bold)
            tw = draw.textbbox((0, 0), text, font=f)[2]
            if tw <= max_w:
                return f
            size -= 2
        return cv_font(min_size, bold=bold)

    def format_amount(v):
        if v >= 1000:
            return f"{v:,.2f}"
        if v >= 1:
            return f"{v:,.4f}"
        if v >= 0.01:
            return f"{v:,.5f}"
        return f"{v:,.6f}"

    # Background
    img = Image.new("RGB", (width, height), (20, 28, 42))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(22 + (40 - 22) * t)
        g = int(30 + (52 - 30) * t)
        b = int(45 + (74 - 45) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Main panel + depth
    panel_x, panel_y = 56, 62
    panel_w, panel_h = width - 112, height - 124
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([panel_x + 8, panel_y + 14, panel_x + panel_w + 8, panel_y + panel_h + 14], radius=36, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=36, fill=(19, 30, 47))
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=36, outline=(128, 153, 190), width=2)
    draw.rounded_rectangle([panel_x + 9, panel_y + 9, panel_x + panel_w - 9, panel_y + panel_h - 9], radius=31, outline=(74, 95, 130), width=1)

    def draw_value_with_unit(x, y, value_text, unit_text, max_w, value_color, unit_color):
        unit_font = cv_font(32, bold=True)
        unit_w = draw.textbbox((0, 0), unit_text, font=unit_font)[2]
        value_font = fit_font(value_text, max_w - unit_w - 14, 60, 24, bold=True)
        value_w = draw.textbbox((0, 0), value_text, font=value_font)[2]
        draw.text((x, y), value_text, fill=value_color, font=value_font)
        draw.text((x + value_w + 14, y + max(0, (value_font.size - unit_font.size) // 2)), unit_text, fill=unit_color, font=unit_font)

    # Title
    title = "CRYPTO CONVERTER"
    tf = cv_font(56, bold=True)
    tw = draw.textbbox((0, 0), title, font=tf)[2]
    tx = (width - tw) // 2
    ty = panel_y + 52
    draw.text((tx + 1, ty + 2), title, fill=(8, 14, 25), font=tf)
    draw.text((tx, ty), title, fill="#F4F9FF", font=tf)

    # Left source box
    lx, ly = panel_x + 40, panel_y + 244
    lw, lh = 390, 132
    draw.rounded_rectangle([lx + 2, ly + 6, lx + lw + 2, ly + lh + 6], radius=38, fill=(0, 0, 0, 90))
    draw.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=38, fill=(52, 72, 102))
    draw.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=38, outline=tuple(min(255, int(c * 1.25)) for c in accent), width=3)

    # Logo badge in source box
    src_logo = None
    logo_url = coin_data.get("logo_url")
    if logo_url:
        src_logo = await download_logo(logo_url, 58)
    badge = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse([0, 0, 71, 71], fill=(20, 30, 45), outline=tuple(min(255, int(c * 1.3)) for c in accent), width=2)
    if src_logo:
        fit = ImageOps.contain(src_logo.convert("RGBA"), (46, 46), Image.Resampling.LANCZOS)
        badge.alpha_composite(fit, ((72 - fit.width) // 2, (72 - fit.height) // 2))
    else:
        f = cv_font(30, bold=True)
        c = symbol[:1] if symbol else "?"
        cw = bd.textbbox((0, 0), c, font=f)[2]
        ch = bd.textbbox((0, 0), c, font=f)[3]
        bd.text(((72 - cw) // 2, (72 - ch) // 2 - 1), c, fill="#F7FBFF", font=f)
    img.paste(badge, (lx + 22, ly + 30), badge)

    left_text = f"{amount_text} {symbol}"
    left_font = fit_font(left_text, 260, 56, 26, bold=True)
    draw.text((lx + 108, ly + 43), left_text, fill="#F2F7FF", font=left_font)

    # Arrow
    draw.text((lx + lw + 20, ly + 36), "=>", fill="#F4F8FF", font=cv_font(64, bold=True))

    # Right result panel (4 rows: USD + ETH + SOL + TON)
    rx, ry = panel_x + 548, panel_y + 154
    rw, rh = 522, 430
    draw.rounded_rectangle([rx + 3, ry + 8, rx + rw + 3, ry + rh + 8], radius=30, fill=(0, 0, 0, 95))
    draw.rounded_rectangle([rx, ry, rx + rw, ry + rh], radius=30, fill=(25, 37, 56))
    draw.rounded_rectangle([rx, ry, rx + rw, ry + rh], radius=30, outline=(82, 106, 142), width=2)

    row_h = rh // 4
    for i in range(1, 4):
        y = ry + i * row_h
        draw.line([(rx, y), (rx + rw, y)], fill=(66, 86, 116), width=2)

    # Load target logos
    target_symbols = ["eth", "sol", "ton"]
    target_logos = {}
    for ts in target_symbols:
        td = cross_data.get(ts) or cross_data.get(ts.upper())
        if td and td.get("logo_url"):
            target_logos[ts] = await download_logo(td["logo_url"], 34)

    # USD row
    draw.text((rx + 28, ry + 12), "TOTAL VALUE", fill="#9FB3CE", font=cv_font(18, bold=False))
    draw_value_with_unit(rx + 28, ry + 34, usd_text, "USD", rw - 56, "#FFFFFF", "#AFC1DA")

    # Coin rows
    for idx, ts in enumerate(target_symbols, start=1):
        td = cross_data.get(ts) or cross_data.get(ts.upper())
        row_y = ry + idx * row_h
        if td and float(td.get("price", 0)) > 0:
            conv = usd_value / float(td["price"])
            txt_num = format_amount(conv)
            txt_unit = ts.upper()
        else:
            txt_num = "--"
            txt_unit = ts.upper()

        # Small logo badge
        bx, by = rx + 26, row_y + 26
        mini = Image.new("RGBA", (44, 44), (0, 0, 0, 0))
        md = ImageDraw.Draw(mini)
        md.ellipse([0, 0, 43, 43], fill=(34, 50, 72), outline=(93, 120, 155), width=1)
        logo = target_logos.get(ts)
        if logo:
            fit = ImageOps.contain(logo.convert("RGBA"), (28, 28), Image.Resampling.LANCZOS)
            mini.alpha_composite(fit, ((44 - fit.width) // 2, (44 - fit.height) // 2))
        else:
            sfont = cv_font(18, bold=True)
            ch = ts[:1].upper()
            sw = md.textbbox((0, 0), ch, font=sfont)[2]
            sh = md.textbbox((0, 0), ch, font=sfont)[3]
            md.text(((44 - sw) // 2, (44 - sh) // 2 - 1), ch, fill="#EAF2FF", font=sfont)
        img.paste(mini, (bx, by), mini)

        draw.text((rx + 84, row_y + 16), f"{txt_unit} EQUIV", fill="#8FA6C7", font=cv_font(16, bold=False))
        if td:
            draw_value_with_unit(rx + 84, row_y + 38, txt_num, txt_unit, rw - 118, "#EAF2FF", "#C8D8F2")
        else:
            row_font = fit_font(f"{txt_num} {txt_unit}", rw - 118, 44, 22, bold=True)
            draw.text((rx + 84, row_y + 36), f"{txt_num} {txt_unit}", fill="#9AAEC9", font=row_font)

    # Footer
    wm = "Powered by @conesociety"
    wf = cv_font(22, bold=False)
    ww = draw.textbbox((0, 0), wm, font=wf)[2]
    draw.text(((width - ww) // 2, panel_y + panel_h - 48), wm, fill="#8FA4C2", font=wf)

    return img

async def create_ath_card_async(coin_data):
    """Premium ATH card with 3D glass style and overlap-safe text."""
    from datetime import datetime

    width, height = 1200, 760
    accent = hex_to_rgb(coin_data["color"])
    ath = float(coin_data.get("ath", 0))
    current = float(coin_data.get("price", 0))
    down_pct = ((ath - current) / ath * 100) if ath > 0 else 0.0

    def ath_font(size, bold=False):
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

    def fit_font(draw_obj, text, max_w, start_size, min_size=16, bold=True):
        size = start_size
        while size >= min_size:
            f = ath_font(size, bold=bold)
            tw = draw_obj.textbbox((0, 0), text, font=f)[2]
            if tw <= max_w:
                return f
            size -= 2
        return ath_font(min_size, bold=bold)

    img = Image.new("RGB", (width, height), (20, 28, 42))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(22 + (40 - 22) * t)
        g = int(30 + (52 - 30) * t)
        b = int(45 + (74 - 45) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    panel_x, panel_y = 56, 52
    panel_w, panel_h = width - 112, height - 104
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([panel_x + 8, panel_y + 14, panel_x + panel_w + 8, panel_y + panel_h + 14], radius=36, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=36, fill=(19, 30, 47))
    draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h], radius=36, outline=(128, 153, 190), width=2)
    draw.rounded_rectangle([panel_x + 9, panel_y + 9, panel_x + panel_w - 9, panel_y + panel_h - 9], radius=31, outline=(74, 95, 130), width=1)

    # Accent strip
    for dy in range(7):
        t = dy / 6
        col = tuple(min(255, int(c * (1.2 - 0.3 * t))) for c in accent)
        draw.rounded_rectangle([panel_x + 24, panel_y + 16 + dy, panel_x + panel_w - 24, panel_y + 19 + dy], radius=3, fill=col)

    # Header coin pill
    pill_x, pill_y = panel_x + panel_w - 340, panel_y + 40
    pill_w, pill_h = 284, 88
    draw.rounded_rectangle([pill_x + 2, pill_y + 6, pill_x + pill_w + 2, pill_y + pill_h + 6], radius=38, fill=(0, 0, 0, 90))
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=38, fill=(58, 78, 108))
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=38, outline=(128, 154, 192), width=2)

    # Logo badge
    logo = None
    if coin_data.get("logo_url"):
        logo = await download_logo(coin_data["logo_url"], 52)
    badge = Image.new("RGBA", (56, 56), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse([0, 0, 55, 55], fill=(20, 30, 45), outline=tuple(min(255, int(c * 1.25)) for c in accent), width=2)
    if logo:
        fit = ImageOps.contain(logo.convert("RGBA"), (36, 36), Image.Resampling.LANCZOS)
        badge.alpha_composite(fit, ((56 - fit.width) // 2, (56 - fit.height) // 2))
    else:
        s = (coin_data.get("symbol", "?")[:1]).upper()
        sf = ath_font(24, bold=True)
        sw = bd.textbbox((0, 0), s, font=sf)[2]
        sh = bd.textbbox((0, 0), s, font=sf)[3]
        bd.text(((56 - sw) // 2, (56 - sh) // 2 - 1), s, fill="#F2F7FF", font=sf)
    img.paste(badge, (pill_x + 14, pill_y + 16), badge)

    sym = (coin_data.get("symbol") or coin_data.get("name", "COIN")).upper()
    draw.text((pill_x + 84, pill_y + 26), sym, fill="#F4F7FC", font=ath_font(36, bold=True))

    # Title
    title = f"{coin_data['name']} ALL-TIME HIGH"
    tf = fit_font(draw, title, panel_w - 420, 50, 24, bold=True)
    draw.text((panel_x + 47, panel_y + 55), title, fill=(8, 14, 25), font=tf)
    draw.text((panel_x + 46, panel_y + 52), title, fill="#F4F9FF", font=tf)

    # Date parse
    try:
        ath_date = datetime.fromisoformat(str(coin_data.get("ath_date", "")).replace("Z", "+00:00"))
        date_text = ath_date.strftime("%b %d, %Y")
    except Exception:
        date_text = str(coin_data.get("ath_date", "N/A"))[:20]

    # Value rows
    rows = [
        ("ALL-TIME HIGH", f"${ath:,.2f}", "#38F2A1", (12, 66, 50), (56, 248, 173)),
        ("CURRENT PRICE", f"${current:,.2f}", "#FFB238", (70, 52, 18), (255, 188, 86)),
        ("ATH DATE", date_text, "#DCE9FF", (41, 57, 81), (105, 131, 171)),
        ("DOWN FROM ATH", f"-{down_pct:.2f}%", "#FF6D78", (88, 28, 38), (255, 108, 121)),
    ]

    row_x = panel_x + 42
    row_w = panel_w - 84
    row_h = 96
    row_gap = 14
    start_y = panel_y + 164

    for i, (label, value, vcol, bg, outline) in enumerate(rows):
        y = start_y + i * (row_h + row_gap)
        draw.rounded_rectangle([row_x + 2, y + 6, row_x + row_w + 2, y + row_h + 6], radius=28, fill=(0, 0, 0, 88))
        draw.rounded_rectangle([row_x, y, row_x + row_w, y + row_h], radius=28, fill=bg)
        draw.rounded_rectangle([row_x, y, row_x + row_w, y + row_h], radius=28, outline=outline, width=2)
        draw.rounded_rectangle([row_x + 14, y + 10, row_x + row_w - 14, y + 18], radius=4, fill=(255, 255, 255, 34))
        draw.text((row_x + 24, y + 18), label, fill="#B8C8E2", font=ath_font(20, bold=False))

        vf = fit_font(draw, value, row_w - 56, 50, 24, bold=True)
        draw.text((row_x + 24, y + 44), value, fill=vcol, font=vf)

    wm = "Powered by @conesociety"
    wf = ath_font(22, bold=False)
    ww = draw.textbbox((0, 0), wm, font=wf)[2]
    draw.text(((width - ww) // 2, panel_y + panel_h - 48), wm, fill="#8FA4C2", font=wf)

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
