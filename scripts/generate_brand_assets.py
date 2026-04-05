from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


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


def build_icon(size: int = 1024) -> Image.Image:
    image = make_gradient(size)
    radius = int(size * 0.23)

    ambient = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ad = ImageDraw.Draw(ambient)
    ad.ellipse((int(size * 0.14), int(size * 0.16), int(size * 0.76), int(size * 0.78)), fill=(72, 132, 255, 105))
    ad.ellipse((int(size * 0.34), int(size * 0.22), int(size * 0.92), int(size * 0.82)), fill=(54, 225, 208, 68))
    ambient = ambient.filter(ImageFilter.GaussianBlur(radius=size // 9))
    image.alpha_composite(ambient)

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (int(size * 0.14), int(size * 0.12), int(size * 0.86), int(size * 0.84)),
        radius=radius,
        fill=(0, 0, 0, 120),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=size // 26))
    image.alpha_composite(shadow, (0, int(size * 0.02)))

    card = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle(
        (int(size * 0.14), int(size * 0.10), int(size * 0.86), int(size * 0.82)),
        radius=radius,
        fill=(11, 22, 37, 255),
        outline=(94, 122, 170, 92),
        width=max(4, size // 180),
    )

    inner = (int(size * 0.24), int(size * 0.20), int(size * 0.76), int(size * 0.62))
    cd.rounded_rectangle(inner, radius=int(size * 0.10), outline=(121, 174, 255, 255), width=max(12, size // 44))

    for x1, y1, x2, y2 in (
        (0.27, 0.24, 0.38, 0.28),
        (0.27, 0.24, 0.31, 0.35),
        (0.62, 0.24, 0.73, 0.28),
        (0.69, 0.24, 0.73, 0.35),
        (0.27, 0.54, 0.38, 0.58),
        (0.27, 0.47, 0.31, 0.58),
        (0.62, 0.54, 0.73, 0.58),
        (0.69, 0.47, 0.73, 0.58),
    ):
        cd.rounded_rectangle(
            (int(size * x1), int(size * y1), int(size * x2), int(size * y2)),
            radius=max(10, size // 90),
            fill=(187, 216, 255, 255),
        )

    fog = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    fd.ellipse((int(size * 0.34), int(size * 0.29), int(size * 0.66), int(size * 0.58)), fill=(235, 243, 255, 228))
    fd.rounded_rectangle(
        (int(size * 0.30), int(size * 0.49), int(size * 0.70), int(size * 0.56)),
        radius=int(size * 0.035),
        fill=(80, 227, 198, 242),
    )
    fd.ellipse((int(size * 0.43), int(size * 0.27), int(size * 0.57), int(size * 0.38)), fill=(255, 255, 255, 126))
    fog = fog.filter(ImageFilter.GaussianBlur(radius=size // 42))
    card.alpha_composite(fog)

    bottom_font = get_font(int(size * 0.12), bold=True)
    text = "WK"
    bbox = cd.textbbox((0, 0), text, font=bottom_font)
    text_w = bbox[2] - bbox[0]
    cd.text(((size - text_w) / 2, size * 0.67), text, fill=(242, 247, 255, 210), font=bottom_font)

    image.alpha_composite(card)
    return image


def build_social_preview() -> Image.Image:
    canvas = make_gradient(1600)
    canvas = canvas.resize((1600, 900))
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((80, 90, 1520, 810), radius=48, fill=(11, 24, 40, 235))
    icon = build_icon(420).resize((320, 320), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (120, 220))

    title_font = get_font(88, bold=True)
    sub_font = get_font(36)
    body_font = get_font(28)
    draw.text((500, 220), "雾框", fill=(247, 250, 255), font=title_font)
    draw.text((500, 330), "Wukuang", fill=(145, 180, 219), font=sub_font)
    draw.text((500, 420), "为高频批量打码设计的本地桌面工具。", fill=(214, 225, 239), font=body_font)
    draw.text((500, 470), "拖拽或定点框选，立即模糊，适合连续浏览与快速处理。", fill=(214, 225, 239), font=body_font)
    return canvas


def build_release_cover() -> Image.Image:
    canvas = make_gradient(1800).resize((1800, 1000))
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle((70, 70, 1730, 930), radius=48, fill=(8, 18, 31, 236))
    icon = build_icon(520).resize((360, 360), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (115, 180))

    title_font = get_font(104, bold=True)
    sub_font = get_font(40)
    body_font = get_font(30)
    pill_font = get_font(24, bold=True)

    draw.text((540, 170), "雾框", fill=(245, 249, 255), font=title_font)
    draw.text((540, 300), "Wukuang", fill=(144, 180, 219), font=sub_font)
    draw.text((540, 390), "面向大量图片审核与打码流程的本地桌面工作台", fill=(219, 229, 240), font=body_font)
    draw.text((540, 445), "支持拖拽框选、定点拉框、圆形/矩形模糊、自动保存、A/D 快速切图。", fill=(219, 229, 240), font=body_font)

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
    draw.text((1170, 780), "适合 GitHub 展示、Release 封面、社媒分享", fill=(173, 196, 221), font=get_font(22))
    return canvas


def build_screenshot_sheet() -> Image.Image:
    canvas = make_gradient(1800).resize((1800, 1200))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((60, 60, 1740, 1140), radius=46, fill=(8, 18, 31, 236))

    title_font = get_font(76, bold=True)
    sub_font = get_font(28)
    draw.text((95, 90), "雾框发布页素材", fill=(246, 250, 255), font=title_font)
    draw.text((95, 185), "图标、主界面和工作流程可直接用于 GitHub README 或 Release 页面。", fill=(156, 184, 215), font=sub_font)

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

    label_font = get_font(30, bold=True)
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
        draw.text((x1 + 22, y1 + 16), label, fill=(241, 247, 255), font=label_font)
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
