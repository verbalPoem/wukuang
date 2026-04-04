from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "msyhbd.ttc" if bold else "msyh.ttc",
        "Microsoft YaHei UI Bold.ttf" if bold else "Microsoft YaHei UI.ttf",
        "simhei.ttf" if bold else "simsun.ttc",
        "arialbd.ttf" if bold else "arial.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def gradient_background(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)
    return image


def rounded_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: tuple[int, int, int], radius: int) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def save_banner() -> None:
    img = gradient_background((1600, 900), (7, 15, 28), (18, 43, 72))
    draw = ImageDraw.Draw(img)

    rounded_panel(draw, (70, 80, 1530, 820), (12, 24, 41), 36)
    rounded_panel(draw, (950, 130, 1470, 760), (17, 34, 58), 26)
    rounded_panel(draw, (1020, 220, 1400, 520), (8, 17, 29), 20)
    rounded_panel(draw, (1020, 550, 1400, 690), (24, 46, 76), 20)
    rounded_panel(draw, (130, 180, 890, 760), (9, 17, 29), 28)

    title_font = font(86, bold=True)
    sub_font = font(34)
    body_font = font(28)
    pill_font = font(24, bold=True)

    draw.text((130, 120), "雾框", fill=(245, 249, 255), font=title_font)
    draw.text((130, 225), "一框即糊的本地图片打码工具", fill=(156, 183, 214), font=sub_font)
    draw.text((130, 290), "适合批量处理人脸、敏感部位与其他需要快速模糊的区域", fill=(196, 214, 236), font=body_font)

    pills = ["鼠标拖拽即打码", "自动保存", "A/D 快速切图", "Ctrl+Z 撤销"]
    x = 130
    y = 370
    for pill in pills:
        bbox = draw.textbbox((0, 0), pill, font=pill_font)
        width = bbox[2] - bbox[0] + 40
        rounded_panel(draw, (x, y, x + width, y + 54), (22, 197, 94), 24)
        draw.text((x + 20, y + 12), pill, fill=(7, 15, 28), font=pill_font)
        x += width + 18

    draw.text((130, 470), "现代深色工作台界面", fill=(245, 249, 255), font=font(42, bold=True))
    draw.text((130, 530), "处理结果默认输出到 blurred_output，不覆盖原图。", fill=(166, 190, 219), font=body_font)
    draw.text((130, 580), "适合整理完后直接上传到 GitHub 展示。", fill=(166, 190, 219), font=body_font)

    draw.text((1045, 155), "界面预览", fill=(240, 246, 255), font=font(30, bold=True))
    draw.rectangle((1060, 260, 1350, 470), outline=(110, 231, 183), width=4)
    draw.line((1075, 280, 1210, 360), fill=(91, 165, 255), width=12)
    draw.line((1210, 360, 1295, 410), fill=(91, 165, 255), width=12)
    draw.text((1045, 570), "左侧控制面板", fill=(230, 238, 250), font=font(26, bold=True))
    draw.text((1045, 610), "右侧大画布预览", fill=(169, 190, 216), font=font(24))
    draw.text((1045, 645), "适合连续批量作业", fill=(169, 190, 216), font=font(24))

    img.save(ASSETS / "banner.png")


def save_preview() -> None:
    img = gradient_background((1400, 920), (9, 18, 32), (14, 32, 52))
    draw = ImageDraw.Draw(img)

    rounded_panel(draw, (40, 40, 1360, 880), (8, 16, 28), 30)
    rounded_panel(draw, (70, 70, 370, 850), (14, 28, 47), 24)
    rounded_panel(draw, (400, 70, 1330, 150), (12, 26, 43), 20)
    rounded_panel(draw, (400, 180, 1330, 850), (5, 12, 22), 28)
    rounded_panel(draw, (95, 235, 345, 410), (19, 35, 58), 18)
    rounded_panel(draw, (95, 435, 345, 620), (19, 35, 58), 18)
    rounded_panel(draw, (95, 645, 345, 820), (19, 35, 58), 18)

    draw.text((95, 95), "雾框", fill=(247, 250, 255), font=font(48, bold=True))
    draw.text((95, 155), "为大量图片快速框选并自动模糊保存", fill=(147, 173, 207), font=font(20))
    draw.text((105, 255), "开始处理", fill=(235, 242, 251), font=font(24, bold=True))
    draw.text((105, 295), "选择图片文件夹", fill=(180, 203, 229), font=font(18))
    draw.text((105, 455), "当前进度", fill=(235, 242, 251), font=font(24, bold=True))
    draw.text((105, 500), "18 / 240", fill=(255, 255, 255), font=font(42, bold=True))
    draw.text((105, 560), "当前文件: IMG_1088.jpg", fill=(180, 203, 229), font=font(18))
    draw.text((105, 665), "快捷操作", fill=(235, 242, 251), font=font(24, bold=True))
    draw.text((105, 710), "A 上一张  D 下一张", fill=(180, 203, 229), font=font(18))
    draw.text((105, 745), "Ctrl+Z 撤销  R 重载", fill=(180, 203, 229), font=font(18))

    draw.text((430, 95), "工作目录: C:/photoshoot/session_01", fill=(220, 233, 249), font=font(24, bold=True))
    draw.text((1085, 97), "上一张", fill=(223, 236, 250), font=font(20, bold=True))
    draw.text((1190, 97), "下一张", fill=(9, 18, 32), font=font(20, bold=True))
    rounded_panel(draw, (1045, 82, 1150, 126), (29, 54, 88), 18)
    rounded_panel(draw, (1160, 82, 1275, 126), (34, 197, 94), 18)

    photo = gradient_background((820, 560), (27, 52, 83), (56, 93, 136))
    pd = ImageDraw.Draw(photo)
    pd.ellipse((90, 120, 320, 360), fill=(228, 196, 170))
    pd.rectangle((380, 110, 710, 470), fill=(42, 67, 105))
    pd.rectangle((190, 420, 650, 520), fill=(28, 44, 70))
    pd.rounded_rectangle((130, 150, 290, 310), radius=12, outline=(110, 231, 183), width=7)
    pd.rounded_rectangle((490, 210, 620, 315), radius=12, outline=(110, 231, 183), width=7)
    img.paste(photo, (455, 230))

    draw.text((470, 770), "鼠标拖拽拉框后立即模糊，保存动作自动完成。", fill=(194, 213, 235), font=font(24))
    img.save(ASSETS / "app-preview.png")


def save_workflow() -> None:
    img = gradient_background((1400, 700), (8, 16, 29), (16, 37, 61))
    draw = ImageDraw.Draw(img)
    draw.text((70, 55), "工作流程", fill=(245, 249, 255), font=font(54, bold=True))
    draw.text((70, 125), "从打开文件夹到连续切图，一套动作尽量压缩到最短。", fill=(157, 184, 214), font=font(24))

    cards = [
        ("1", "选择文件夹", "载入待处理图片，并自动创建 blurred_output 输出目录"),
        ("2", "拖拽框选", "左键拉框，松开后马上对框选区域执行模糊"),
        ("3", "自动保存", "每次处理后立即写入输出目录，不需要手动点保存"),
        ("4", "快速切图", "按 A / D 在上一张和下一张之间连续处理"),
    ]

    x = 70
    for num, title, body in cards:
        rounded_panel(draw, (x, 220, x + 290, 590), (12, 24, 41), 28)
        rounded_panel(draw, (x + 28, 250, x + 102, 324), (34, 197, 94), 24)
        draw.text((x + 50, 266), num, fill=(7, 15, 28), font=font(34, bold=True))
        draw.text((x + 28, 360), title, fill=(241, 246, 255), font=font(30, bold=True))
        draw.multiline_text((x + 28, 420), body, fill=(173, 195, 220), font=font(20), spacing=10)
        x += 320

    img.save(ASSETS / "workflow.png")


def main() -> None:
    save_banner()
    save_preview()
    save_workflow()


if __name__ == "__main__":
    main()
