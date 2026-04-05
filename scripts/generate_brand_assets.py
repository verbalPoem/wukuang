from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import textwrap


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "msyhbd.ttc" if bold else "msyh.ttc",
        "Microsoft YaHei UI Bold.ttf" if bold else "Microsoft YaHei UI.ttf",
        "simhei.ttf" if bold else "simsun.ttc",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_gradient(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(image)
    top = (7, 18, 32)
    bottom = (19, 59, 96)
    for y in range(size):
        t = y / max(1, size - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)) + (255,)
        draw.line((0, y, size, y), fill=color)
    return image


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int, bold: bool = False, min_size: int = 16):
    size = start_size
    while size >= min_size:
        font = get_font(size, bold=bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return get_font(min_size, bold=bold)


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def build_icon(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    radius = int(size * 0.24)

    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    tile_box = (int(size * 0.18), int(size * 0.18), int(size * 0.82), int(size * 0.82))
    td.rounded_rectangle(tile_box, radius=radius, fill=(16, 32, 56, 255))
    td.rounded_rectangle(tile_box, radius=radius, outline=(97, 137, 194, 118), width=max(4, size // 170))

    screen_box = (int(size * 0.28), int(size * 0.25), int(size * 0.72), int(size * 0.58))
    td.rounded_rectangle(screen_box, radius=int(size * 0.08), fill=(31, 58, 92, 255), outline=(124, 170, 240, 220), width=max(8, size // 64))

    fog = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    fd.ellipse((int(size * 0.36), int(size * 0.31), int(size * 0.64), int(size * 0.53)), fill=(240, 246, 255, 228))
    fd.rounded_rectangle((int(size * 0.33), int(size * 0.47), int(size * 0.67), int(size * 0.54)), radius=int(size * 0.03), fill=(116, 204, 255, 238))
    fd.ellipse((int(size * 0.43), int(size * 0.30), int(size * 0.57), int(size * 0.37)), fill=(255, 255, 255, 128))
    fog = fog.filter(ImageFilter.GaussianBlur(radius=size // 42))
    tile.alpha_composite(fog)

    base = (int(size * 0.39), int(size * 0.63), int(size * 0.61), int(size * 0.68))
    td.rounded_rectangle(base, radius=int(size * 0.018), fill=(195, 222, 255, 220))
    td.rounded_rectangle((int(size * 0.33), int(size * 0.69), int(size * 0.67), int(size * 0.75)), radius=int(size * 0.028), fill=(195, 222, 255, 220))

    image.alpha_composite(tile)
    return image


def build_social_preview() -> Image.Image:
    canvas = make_gradient(1600)
    canvas = canvas.resize((1600, 900))
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((80, 90, 1520, 810), radius=48, fill=(11, 24, 40, 235))
    icon = build_icon(420).resize((320, 320), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (120, 220))

    title_font = get_font(88, bold=True)
    sub_font = get_font(34)
    body_font = get_font(26)
    draw.text((500, 220), "雾框", fill=(247, 250, 255), font=title_font)
    draw.text((500, 330), "Wukuang", fill=(145, 180, 219), font=sub_font)
    desc = "为高频批量打码设计的本地桌面工具。拖拽或定点框选，立即处理，适合连续浏览与快速修改。"
    y = 420
    for line in wrap_lines(draw, desc, body_font, 860):
        draw.text((500, y), line, fill=(214, 225, 239), font=body_font)
        y += 42
    return canvas


def build_release_cover() -> Image.Image:
    canvas = make_gradient(1800).resize((1800, 1000))
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((70, 70, 1730, 930), radius=48, fill=(8, 18, 31, 236))
    icon = build_icon(520).resize((360, 360), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (115, 180))

    title_font = get_font(100, bold=True)
    sub_font = get_font(38)
    body_font = get_font(28)
    pill_font = get_font(24, bold=True)

    draw.text((540, 170), "雾框", fill=(245, 249, 255), font=title_font)
    draw.text((540, 300), "Wukuang", fill=(144, 180, 219), font=sub_font)
    lines = [
        "面向大量图片审核与打码流程的本地桌面工作台",
        "支持拖拽框选、定点拉框、圆形/矩形处理、自动保存、A/D 快速切图",
    ]
    y = 390
    for line in lines:
        font = fit_text(draw, line, 980, 28)
        draw.text((540, y), line, fill=(219, 229, 240), font=font)
        y += 52

    pills = ["高 DPI 更清晰", "深浅色主题", "自动保存", "Windows EXE"]
    x = 540
    y = 530
    for pill in pills:
        bbox = draw.textbbox((0, 0), pill, font=pill_font)
        width = bbox[2] - bbox[0] + 42
        draw.rounded_rectangle((x, y, x + width, y + 52), radius=24, fill=(23, 197, 94))
        draw.text((x + 21, y + 12), pill, fill=(8, 18, 31), font=pill_font)
        x += width + 16

    draw.rounded_rectangle((1120, 610, 1620, 860), radius=30, fill=(13, 29, 48))
    draw.text((1170, 655), "开源仓库推荐名", fill=(242, 247, 255), font=get_font(28, bold=True))
    draw.text((1170, 710), "wukuang", fill=(94, 226, 185), font=get_font(42, bold=True))
    desc_font = get_font(22)
    for idx, line in enumerate(wrap_lines(draw, "适合 GitHub 展示、Release 封面与下载页说明。", desc_font, 380)):
        draw.text((1170, 780 + idx * 28), line, fill=(173, 196, 221), font=desc_font)
    return canvas


def build_screenshot_sheet() -> Image.Image:
    canvas = make_gradient(1800).resize((1800, 1200))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((60, 60, 1740, 1140), radius=46, fill=(8, 18, 31, 236))

    title_font = get_font(70, bold=True)
    sub_font = get_font(26)
    draw.text((95, 90), "雾框发布页素材", fill=(246, 250, 255), font=title_font)
    subtitle = "图标、主界面和工作流程素材可直接用于 GitHub README 或 Release 页面。"
    for idx, line in enumerate(wrap_lines(draw, subtitle, sub_font, 1460)):
        draw.text((95, 185 + idx * 34), line, fill=(156, 184, 215), font=sub_font)

    assets = {
        "应用图标": ASSETS / "app-icon-preview.png",
        "界面预览": ASSETS / "app-preview.png",
        "工作流程": ASSETS / "workflow.png",
    }
    positions = [
        ("应用图标", (95, 270, 840, 620)),
        ("界面预览", (960, 270, 1705, 620)),
        ("工作流程", (95, 690, 1705, 1070)),
    ]

    label_font = get_font(28, bold=True)
    for label, box in positions:
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(box, radius=28, fill=(13, 29, 48))
        image_path = assets[label]
        if image_path.exists():
            image = Image.open(image_path).convert("RGBA")
            target_w = x2 - x1 - 36
            target_h = y2 - y1 - 70
            scale = min(target_w / image.width, target_h / image.height)
            resized = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
            px = x1 + (x2 - x1 - resized.width) // 2
            py = y1 + 48 + (target_h - resized.height) // 2
            canvas.alpha_composite(resized, (px, py))
        fitted = fit_text(draw, label, x2 - x1 - 44, 28, bold=True)
        draw.text((x1 + 22, y1 + 16), label, fill=(241, 247, 255), font=fitted)
    return canvas


def main() -> None:
    icon = build_icon()
    png_path = ASSETS / "app-icon.png"
    ico_path = ASSETS / "app-icon.ico"
    social_path = ASSETS / "app-icon-preview.png"
    release_cover_path = ASSETS / "release-cover.png"
    screenshot_sheet_path = ASSETS / "screenshot-sheet.png"

    icon.save(png_path)
    icon.save(ico_path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    build_social_preview().save(social_path)
    build_release_cover().save(release_cover_path)
    build_screenshot_sheet().save(screenshot_sheet_path)


if __name__ == "__main__":
    main()
