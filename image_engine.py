from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
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

    def make_logo_badge(logo_img, size, accent_rgb, fallback_text):
        """Create crisp circular logo badge with ring + fallback."""
        badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        bd = ImageDraw.Draw(badge)
        outer = tuple(min(255, int(c * 1.25)) for c in accent_rgb)
        inner = tuple(min(255, int(c * 0.55 + 28)) for c in accent_rgb)

        bd.ellipse([0, 0, size - 1, size - 1], fill=(15, 22, 33, 255), outline=outer, width=2)
        bd.ellipse([3, 3, size - 4, size - 4], fill=inner)

        if logo_img:
            logo_rgba = logo_img.convert("RGBA")
            inset = int(size * 0.16)
            content_size = (size - inset * 2, size - inset * 2)
            logo_fit = ImageOps.contain(logo_rgba, content_size, Image.Resampling.LANCZOS)
            lx = (size - logo_fit.width) // 2
            ly = (size - logo_fit.height) // 2
            badge.alpha_composite(logo_fit, (lx, ly))
        else:
            ch = (fallback_text[:1] if fallback_text else "?").upper()
            f = ui_font(max(16, int(size * 0.42)), bold=True)
            tw = bd.textbbox((0, 0), ch, font=f)[2]
            th = bd.textbbox((0, 0), ch, font=f)[3]
            bd.text(((size - tw) // 2, (size - th) // 2 - 1), ch, fill="#F7FBFF", font=f)

        return badge

    # Clean classic background (brighter contrast)
    img = Image.new("RGB", (width, height), (18, 27, 40))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(20 + (34 - 20) * t)
        g = int(30 + (44 - 30) * t)
        b = int(45 + (68 - 45) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Main board (3D depth + glass)
    x0, y0 = 56, 44
    bw, bh = width - 112, height - 96
    board_shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(board_shadow)
    sdraw.rounded_rectangle([x0 + 8, y0 + 14, x0 + bw + 8, y0 + bh + 14], radius=34, fill=(0, 0, 0, 95))
    board_shadow = board_shadow.filter(ImageFilter.GaussianBlur(8))
    img = Image.alpha_composite(img.convert("RGBA"), board_shadow).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=34, fill=(24, 36, 52))
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=34, outline=(98, 118, 147), width=2)
    draw.rounded_rectangle([x0 + 8, y0 + 8, x0 + bw - 8, y0 + bh - 8], radius=28, outline=(66, 84, 110), width=1)
    sheen = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shd = ImageDraw.Draw(sheen)
    shd.polygon([(x0 + 10, y0 + 14), (x0 + bw - 10, y0 + 14), (x0 + bw - 110, y0 + 82), (x0 + 120, y0 + 82)], fill=(180, 210, 255, 22))
    img = Image.alpha_composite(img.convert("RGBA"), sheen).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Accent strip and corner glow for a richer premium look
    strip_h = 8
    for dy in range(strip_h):
        t = dy / max(1, strip_h - 1)
        col = tuple(min(255, int(c * (0.85 + 0.25 * (1 - t)))) for c in accent)
        draw.rounded_rectangle([x0 + 22, y0 + 16 + dy, x0 + bw - 22, y0 + 20 + dy], radius=3, fill=col)
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([x0 - 40, y0 - 40, x0 + 250, y0 + 220], fill=(accent[0], accent[1], accent[2], 26))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Coin pill top-right
    pill_x, pill_y = x0 + bw - 312, 96
    pill_w, pill_h = 262, 86
    draw.rounded_rectangle([pill_x + 2, pill_y + 6, pill_x + pill_w + 2, pill_y + pill_h + 6], radius=38, fill=(0, 0, 0, 80))
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=38, fill=(87, 103, 129))
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=38, outline=(146, 164, 194), width=2)
    draw.rounded_rectangle([pill_x + 16, pill_y + 10, pill_x + pill_w - 16, pill_y + 20], radius=5, fill=(190, 214, 242, 45))
    logo = None
    logo_url = coin_data.get("logo_url")
    if logo_url:
        logo = await download_logo(logo_url, 46)
    logo_badge = make_logo_badge(logo, 52, accent, coin_data.get("symbol", ""))
    img.paste(logo_badge, (pill_x + 12, pill_y + 17), logo_badge)
    symbol = coin_data.get("symbol", "").upper()
    draw.text((pill_x + 76, pill_y + 24), symbol if symbol else coin_data["name"], fill="#F4F7FC", font=ui_font(28, bold=True))

    # Header row (fit price text so it never overlaps the coin pill)
    num_text = f"{price:,.4f}" if price < 10 else f"{price:,.2f}"
    price_x = 100
    max_price_width = (pill_x - 18) - price_x
    price_font_size = 62
    price_font = ui_font(price_font_size, bold=True)
    full_text = f"${num_text}"
    while price_font_size >= 34:
        price_font = ui_font(price_font_size, bold=True)
        tw = draw.textbbox((0, 0), full_text, font=price_font)[2]
        if tw <= max_price_width:
            break
        price_font_size -= 2
    price_font = ui_font(price_font_size, bold=True)
    dollar_w = draw.textbbox((0, 0), "$", font=price_font)[2]
    draw.text((price_x + 1, 99), "$", fill=(0, 0, 0), font=price_font)
    draw.text((price_x + dollar_w + 9, 99), num_text, fill=(0, 0, 0), font=price_font)
    draw.text((price_x, 96), "$", fill="#FFC24A", font=price_font)
    draw.text((price_x + dollar_w + 8, 96), num_text, fill="#FFFFFF", font=price_font)

    # Metric boxes
    label_font = ui_font(20, bold=False)
    value_font = ui_font(44, bold=True)

    def metric_box(mx, my, label, value):
        pos = value >= 0
        box_bg = (40, 57, 80)
        draw.rounded_rectangle([mx + 2, my + 6, mx + 502, my + 92], radius=24, fill=(0, 0, 0, 88))
        draw.rounded_rectangle([mx, my, mx + 500, my + 86], radius=24, fill=box_bg)
        draw.rounded_rectangle([mx, my, mx + 500, my + 86], radius=24, outline=(86, 106, 138), width=1)
        draw.rounded_rectangle([mx + 10, my + 8, mx + 490, my + 14], radius=4, fill=(104, 126, 160))
        draw.text((mx + 26, my + 12), label, fill="#A8BAD8", font=label_font)
        txt = f"{'+' if pos else ''}{value:.2f}%"
        col = "#4FF28A" if pos else "#FF6D78"
        draw.text((mx + 26, my + 40), txt, fill=col, font=value_font)
        arrow = "▲" if pos else "▼"
        draw.text((mx + 446, my + 30), arrow, fill=col, font=ui_font(36, bold=True))

    metric_box(x0 + 28, 232, "24H CHANGE", change_24h)
    metric_box(x0 + 548, 232, "7D CHANGE", change_7d)

    # Chart frame
    chart_x, chart_y = x0 + 32, 348
    chart_w, chart_h = bw - 64, 286
    draw.rounded_rectangle([chart_x + 2, chart_y + 6, chart_x + chart_w + 2, chart_y + chart_h + 6], radius=8, fill=(0, 0, 0, 90))
    draw.rounded_rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h], radius=8, fill=(22, 33, 49))
    draw.rounded_rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h], radius=8, outline=(97, 118, 150), width=1)

    grid_col = (90, 111, 141)
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

        line_col = tuple(min(255, int(c * 1.3)) for c in accent)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        area = pts + [(pts[-1][0], chart_y + chart_h - 2), (pts[0][0], chart_y + chart_h - 2)]
        od.polygon(area, fill=(line_col[0], line_col[1], line_col[2], 58))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.line(pts, fill=(line_col[0], line_col[1], line_col[2],), width=10)
        draw.line(pts, fill=line_col, width=6)
        glow_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        god = ImageDraw.Draw(glow_overlay)
        god.line(pts, fill=(line_col[0], line_col[1], line_col[2], 90), width=14)
        glow_overlay = glow_overlay.filter(ImageFilter.GaussianBlur(5))
        img = Image.alpha_composite(img.convert("RGBA"), glow_overlay).convert("RGB")
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

    # Title
    title = "CRYPTO CONVERTER"
    tf = cv_font(64, bold=True)
    tw = draw.textbbox((0, 0), title, font=tf)[2]
    draw.text(((width - tw) // 2, panel_y + 46), title, fill="#F4F9FF", font=tf)

    # Left source box
    lx, ly = panel_x + 46, panel_y + 258
    lw, lh = 360, 132
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
    left_font = fit_font(left_text, 230, 62, 26, bold=True)
    draw.text((lx + 108, ly + 43), left_text, fill="#F2F7FF", font=left_font)

    # Arrow
    draw.text((lx + lw + 18, ly + 28), "=", fill="#EAF2FF", font=cv_font(74, bold=True))
    draw.text((lx + lw + 70, ly + 20), ">", fill="#FFE6C0", font=cv_font(96, bold=True))

    # Right result panel (4 rows: USD + ETH + SOL + TON)
    rx, ry = panel_x + 550, panel_y + 158
    rw, rh = 520, 430
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
    usd_font = fit_font(usd_text, rw - 54, 66, 30, bold=True)
    uw = draw.textbbox((0, 0), usd_text, font=usd_font)[2]
    draw.text((rx + 28, ry + 18), usd_text, fill="#FFFFFF", font=usd_font)
    usd_label_x = min(rx + rw - 94, rx + 28 + uw + 10)
    draw.text((usd_label_x, ry + 38), "USD", fill="#9FB3CE", font=cv_font(40, bold=False))

    # Coin rows
    for idx, ts in enumerate(target_symbols, start=1):
        td = cross_data.get(ts) or cross_data.get(ts.upper())
        row_y = ry + idx * row_h
        if td and float(td.get("price", 0)) > 0:
            conv = usd_value / float(td["price"])
            txt = f"{format_amount(conv)} {ts.upper()}"
        else:
            txt = f"-- {ts.upper()}"

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

        row_font = fit_font(txt, rw - 120, 50, 24, bold=True)
        color = "#D8E7FF" if td else "#9AAEC9"
        draw.text((rx + 84, row_y + 22), txt, fill=color, font=row_font)

    # Footer
    wm = "Powered by @conesociety"
    wf = cv_font(48, bold=False)
    ww = draw.textbbox((0, 0), wm, font=wf)[2]
    draw.text(((width - ww) // 2, panel_y + panel_h - 72), wm, fill="#8FA4C2", font=wf)

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
    draw.text((pill_x + 84, pill_y + 24), sym, fill="#F4F7FC", font=ath_font(40, bold=True))

    # Title
    title = f"{coin_data['name']} ALL-TIME HIGH"
    tf = fit_font(draw, title, panel_w - 420, 54, 26, bold=True)
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
    row_h = 108
    row_gap = 18
    start_y = panel_y + 154

    for i, (label, value, vcol, bg, outline) in enumerate(rows):
        y = start_y + i * (row_h + row_gap)
        draw.rounded_rectangle([row_x + 2, y + 6, row_x + row_w + 2, y + row_h + 6], radius=28, fill=(0, 0, 0, 88))
        draw.rounded_rectangle([row_x, y, row_x + row_w, y + row_h], radius=28, fill=bg)
        draw.rounded_rectangle([row_x, y, row_x + row_w, y + row_h], radius=28, outline=outline, width=2)
        draw.rounded_rectangle([row_x + 14, y + 10, row_x + row_w - 14, y + 18], radius=4, fill=(255, 255, 255, 34))
        draw.text((row_x + 24, y + 20), label, fill="#B8C8E2", font=ath_font(25, bold=False))

        vf = fit_font(draw, value, row_w - 56, 58, 26, bold=True)
        draw.text((row_x + 24, y + 50), value, fill=vcol, font=vf)

    wm = "Powered by @conesociety"
    wf = ath_font(48, bold=False)
    ww = draw.textbbox((0, 0), wm, font=wf)[2]
    draw.text(((width - ww) // 2, panel_y + panel_h - 74), wm, fill="#8FA4C2", font=wf)

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
