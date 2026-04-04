from __future__ import annotations

import ctypes
from ctypes import wintypes
import math
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageTk


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
APP_TITLE = "雾框"
THEME_COLORS = {
    "dark": {
        "root_bg": "#09111f",
        "panel_bg": "#0f1b2d",
        "card_bg": "#13233b",
        "canvas_bg": "#07111d",
        "canvas_border": "#19304d",
        "hero_fg": "#f5f7fb",
        "sub_fg": "#91a4bf",
        "section_fg": "#dfe8f5",
        "body_fg": "#b8c7dd",
        "count_fg": "#ffffff",
        "chip_bg": "#12243d",
        "chip_fg": "#dbe7fb",
        "status_bg": "#0d1829",
        "status_fg": "#d0def2",
        "primary_bg": "#22c55e",
        "primary_active": "#34d399",
        "primary_pressed": "#16a34a",
        "primary_fg": "#08111d",
        "secondary_bg": "#1d3658",
        "secondary_active": "#28497a",
        "secondary_pressed": "#16324f",
        "secondary_fg": "#eef4ff",
        "accent": "#6ee7b7",
        "image_border": "#4b6282",
    },
    "light": {
        "root_bg": "#eef4fb",
        "panel_bg": "#dce8f7",
        "card_bg": "#ffffff",
        "canvas_bg": "#d6e2f1",
        "canvas_border": "#b4c3d7",
        "hero_fg": "#10233c",
        "sub_fg": "#50657f",
        "section_fg": "#1a3353",
        "body_fg": "#57708f",
        "count_fg": "#15314f",
        "chip_bg": "#c5d6ea",
        "chip_fg": "#15314f",
        "status_bg": "#d4e1f0",
        "status_fg": "#173250",
        "primary_bg": "#14b45c",
        "primary_active": "#27c96c",
        "primary_pressed": "#0e944b",
        "primary_fg": "#ffffff",
        "secondary_bg": "#c7d7ea",
        "secondary_active": "#b8cce3",
        "secondary_pressed": "#aac0db",
        "secondary_fg": "#173250",
        "accent": "#0ea5e9",
        "image_border": "#7c94b1",
    },
}


def enable_high_dpi() -> None:
    if not hasattr(ctypes, "windll"):
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except OSError:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except OSError:
            pass


def enable_windows_titlebar(hwnd: int, dark: bool) -> None:
    if not hwnd or not hasattr(ctypes, "windll"):
        return
    value = ctypes.c_int(1 if dark else 0)
    for attribute in (20, 19):
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                wintypes.DWORD(attribute),
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except OSError:
            continue


@dataclass
class DisplayMetrics:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    scale: float = 1.0


@dataclass
class SelectionBox:
    start_x: int
    start_y: int
    end_x: int
    end_y: int


class BlurStudioApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1680x1040")
        self.root.minsize(1280, 860)

        self.image_paths: list[Path] = []
        self.current_index = -1
        self.current_image: Image.Image | None = None
        self.preview_photo: ImageTk.PhotoImage | None = None
        self.current_source_path: Path | None = None
        self.output_dir: Path | None = None
        self.folder_path: Path | None = None
        self.display = DisplayMetrics()
        self.undo_stack: list[Image.Image] = []

        self.theme_mode = tk.StringVar(value="dark")
        self.draw_mode = tk.StringVar(value="drag")
        self.shape_mode = tk.StringVar(value="rect")
        self.blur_kernel = tk.IntVar(value=61)
        self.status_text = tk.StringVar(value="选择一个图片文件夹开始。")
        self.folder_text = tk.StringVar(value="尚未选择文件夹")
        self.count_text = tk.StringVar(value="0 / 0")
        self.filename_text = tk.StringVar(value="当前文件: -")
        self.save_text = tk.StringVar(value="自动保存: 未开始")
        self.theme_text = tk.StringVar()
        self.mode_text = tk.StringVar()
        self.shape_text = tk.StringVar()

        self.drag_start: tuple[int, int] | None = None
        self.anchor_point: tuple[int, int] | None = None
        self.selection_item: int | None = None
        self.hover_preview: int | None = None
        self.last_cursor: tuple[int, int] | None = None

        self.icon_png_path = Path(__file__).resolve().parent / "assets" / "app-icon.png"
        self._load_window_icon()

        self._configure_style()
        self._build_layout()
        self._bind_events()
        self._apply_theme(initial=True)
        self.root.after(80, self._refresh_titlebar_theme)

    def _load_window_icon(self) -> None:
        if self.icon_png_path.exists():
            try:
                icon = tk.PhotoImage(file=str(self.icon_png_path))
                self.root.iconphoto(True, icon)
                self.root._icon_ref = icon
            except tk.TclError:
                pass

    def _configure_style(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.root.option_add("*Font", "{Microsoft YaHei UI} 11")

    def _build_layout(self) -> None:
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.sidebar = ttk.Frame(self.root, padding=24, style="Panel.TFrame")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_rowconfigure(6, weight=1)

        self.main = ttk.Frame(self.root, padding=(16, 16, 20, 20), style="App.TFrame")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.hero_label = ttk.Label(self.sidebar, text=APP_TITLE, style="Hero.TLabel")
        self.hero_label.grid(row=0, column=0, sticky="w")
        self.subhero_label = ttk.Label(
            self.sidebar,
            text="高频批量打码工作台。高 DPI 更清晰，支持拖拽与定点两种框选方式。",
            style="SubHero.TLabel",
            wraplength=300,
            justify="left",
        )
        self.subhero_label.grid(row=1, column=0, sticky="w", pady=(8, 22))

        self.action_card = ttk.Frame(self.sidebar, padding=16, style="Card.TFrame")
        self.action_card.grid(row=2, column=0, sticky="ew")
        self.action_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.action_card, text="开始处理", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.action_card,
            text="选择图片目录后会自动创建 blurred_output，后续每次打码都会即时保存。",
            style="Body.TLabel",
            wraplength=270,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 14))
        ttk.Button(
            self.action_card,
            text="选择图片文件夹",
            command=self.choose_folder,
            style="Primary.TButton",
        ).grid(row=2, column=0, sticky="ew")

        self.info_card = ttk.Frame(self.sidebar, padding=16, style="Card.TFrame")
        self.info_card.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        self.info_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.info_card, text="当前进度", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self.info_card, textvariable=self.count_text, style="Count.TLabel").grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Label(self.info_card, textvariable=self.filename_text, style="Body.TLabel", wraplength=270).grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Label(self.info_card, textvariable=self.save_text, style="Body.TLabel", wraplength=270).grid(
            row=3, column=0, sticky="w", pady=(6, 0)
        )

        self.control_card = ttk.Frame(self.sidebar, padding=16, style="Card.TFrame")
        self.control_card.grid(row=4, column=0, sticky="ew", pady=(16, 0))
        self.control_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.control_card, text="绘制与主题", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.control_card,
            text="拖拽模式更直接，定点模式更适合精确框选。可在矩形和圆形模糊间切换，并支持深浅色界面。",
            style="Body.TLabel",
            wraplength=270,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 14))

        self.theme_button = ttk.Button(
            self.control_card,
            textvariable=self.theme_text,
            style="Secondary.TButton",
            command=self.toggle_theme,
        )
        self.theme_button.grid(row=2, column=0, sticky="ew")
        self.mode_button = ttk.Button(
            self.control_card,
            textvariable=self.mode_text,
            style="Secondary.TButton",
            command=self.toggle_draw_mode,
        )
        self.mode_button.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.shape_button = ttk.Button(
            self.control_card,
            textvariable=self.shape_text,
            style="Secondary.TButton",
            command=self.toggle_shape_mode,
        )
        self.shape_button.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        ttk.Label(self.control_card, text="模糊强度", style="Section.TLabel").grid(
            row=5, column=0, sticky="w", pady=(18, 0)
        )
        ttk.Scale(
            self.control_card,
            from_=15,
            to=121,
            variable=self.blur_kernel,
            command=self._normalize_blur_kernel,
            style="Muted.Horizontal.TScale",
        ).grid(row=6, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(self.control_card, text="建议范围: 41-81", style="Body.TLabel").grid(
            row=7, column=0, sticky="w", pady=(10, 0)
        )

        self.shortcut_card = ttk.Frame(self.sidebar, padding=16, style="Card.TFrame")
        self.shortcut_card.grid(row=6, column=0, sticky="sew", pady=(16, 0))
        self.shortcut_card.grid_columnconfigure(0, weight=1)
        ttk.Label(self.shortcut_card, text="快捷操作", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.shortcut_lines = [
            "当前模式可点击按钮切换",
            "A: 上一张图片",
            "D: 下一张图片",
            "Ctrl+Z: 撤销当前图片上一次模糊",
            "R: 重新载入当前图片",
        ]
        for index, line in enumerate(self.shortcut_lines, start=1):
            ttk.Label(self.shortcut_card, text=line, style="Body.TLabel", wraplength=270).grid(
                row=index, column=0, sticky="w", pady=(8 if index == 1 else 6, 0)
            )

        self.top_bar = ttk.Frame(self.main, style="App.TFrame")
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.top_bar.grid_columnconfigure(0, weight=1)

        self.folder_chip = tk.Label(
            self.top_bar,
            textvariable=self.folder_text,
            padx=18,
            pady=11,
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.folder_chip.grid(row=0, column=0, sticky="w")

        self.nav_frame = ttk.Frame(self.top_bar, style="App.TFrame")
        self.nav_frame.grid(row=0, column=1, sticky="e")
        ttk.Button(self.nav_frame, text="上一张 A", style="Secondary.TButton", command=self.prev_image).grid(
            row=0, column=0, padx=(0, 10)
        )
        ttk.Button(self.nav_frame, text="下一张 D", style="Primary.TButton", command=self.next_image).grid(
            row=0, column=1
        )

        self.canvas_frame = tk.Frame(self.main, highlightthickness=1, bd=0)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew")
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame, bd=0, highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.status_bar = tk.Label(
            self.main,
            textvariable=self.status_text,
            anchor="w",
            padx=16,
            pady=12,
            font=("Microsoft YaHei UI", 11),
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(14, 0))

    def _bind_events(self) -> None:
        self.root.bind("<KeyPress-a>", lambda _event: self.prev_image())
        self.root.bind("<KeyPress-d>", lambda _event: self.next_image())
        self.root.bind("<Control-z>", lambda _event: self.undo_last_blur())
        self.root.bind("<KeyPress-r>", lambda _event: self.reload_current())
        self.canvas.bind("<ButtonPress-1>", self._on_left_click)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_release)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Configure>", lambda _event: self.render_image())

    def _apply_theme(self, initial: bool = False) -> None:
        colors = THEME_COLORS[self.theme_mode.get()]
        self.root.configure(bg=colors["root_bg"])

        self.style.configure("App.TFrame", background=colors["root_bg"])
        self.style.configure("Panel.TFrame", background=colors["panel_bg"])
        self.style.configure("Card.TFrame", background=colors["card_bg"], relief="flat")
        self.style.configure(
            "Hero.TLabel", background=colors["panel_bg"], foreground=colors["hero_fg"], font=("Microsoft YaHei UI", 28, "bold")
        )
        self.style.configure(
            "SubHero.TLabel", background=colors["panel_bg"], foreground=colors["sub_fg"], font=("Microsoft YaHei UI", 11)
        )
        self.style.configure(
            "Section.TLabel", background=colors["card_bg"], foreground=colors["section_fg"], font=("Microsoft YaHei UI", 12, "bold")
        )
        self.style.configure(
            "Body.TLabel", background=colors["card_bg"], foreground=colors["body_fg"], font=("Microsoft YaHei UI", 11)
        )
        self.style.configure(
            "Count.TLabel", background=colors["card_bg"], foreground=colors["count_fg"], font=("Microsoft YaHei UI", 22, "bold")
        )
        self.style.configure(
            "Primary.TButton",
            background=colors["primary_bg"],
            foreground=colors["primary_fg"],
            borderwidth=0,
            focusthickness=0,
            focuscolor=colors["primary_bg"],
            padding=(16, 12),
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", colors["primary_active"]), ("pressed", colors["primary_pressed"])],
            foreground=[("active", colors["primary_fg"]), ("pressed", colors["primary_fg"])],
        )
        self.style.configure(
            "Secondary.TButton",
            background=colors["secondary_bg"],
            foreground=colors["secondary_fg"],
            borderwidth=0,
            focusthickness=0,
            focuscolor=colors["secondary_bg"],
            padding=(14, 11),
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.style.map(
            "Secondary.TButton",
            background=[("active", colors["secondary_active"]), ("pressed", colors["secondary_pressed"])],
            foreground=[("active", colors["secondary_fg"]), ("pressed", colors["secondary_fg"])],
        )
        self.style.configure(
            "Muted.Horizontal.TScale",
            background=colors["card_bg"],
            troughcolor=colors["canvas_bg"],
        )

        self.folder_chip.configure(bg=colors["chip_bg"], fg=colors["chip_fg"])
        self.canvas_frame.configure(bg=colors["canvas_bg"], highlightbackground=colors["canvas_border"])
        self.canvas.configure(bg=colors["canvas_bg"])
        self.status_bar.configure(bg=colors["status_bg"], fg=colors["status_fg"])

        self.theme_text.set(f"主题: {'深色' if self.theme_mode.get() == 'dark' else '浅色'}")
        self.mode_text.set(f"框选方式: {'拖拽' if self.draw_mode.get() == 'drag' else '定点'}")
        self.shape_text.set(f"模糊形状: {'矩形' if self.shape_mode.get() == 'rect' else '圆形'}")

        if not initial:
            self.render_image()
            self._refresh_preview_overlay()
            self._refresh_titlebar_theme()

    def _refresh_titlebar_theme(self) -> None:
        self.root.update_idletasks()
        enable_windows_titlebar(self.root.winfo_id(), self.theme_mode.get() == "dark")

    def toggle_theme(self) -> None:
        self.theme_mode.set("light" if self.theme_mode.get() == "dark" else "dark")
        self._apply_theme()
        self.status_text.set(f"已切换到{'浅色' if self.theme_mode.get() == 'light' else '深色'}主题。")

    def toggle_draw_mode(self) -> None:
        self.draw_mode.set("point" if self.draw_mode.get() == "drag" else "drag")
        self._clear_interaction_state()
        self._apply_theme()
        self.status_text.set(
            "当前为定点模式：先点一下起点，再移动鼠标，第二次点击确认。"
            if self.draw_mode.get() == "point"
            else "当前为拖拽模式：按住左键拉框，松手立即模糊。"
        )

    def toggle_shape_mode(self) -> None:
        self.shape_mode.set("circle" if self.shape_mode.get() == "rect" else "rect")
        self._refresh_preview_overlay()
        self._apply_theme()
        self.status_text.set(f"已切换到{'圆形' if self.shape_mode.get() == 'circle' else '矩形'}模糊。")

    def _normalize_blur_kernel(self, _value: str) -> None:
        kernel = max(15, int(self.blur_kernel.get()))
        if kernel % 2 == 0:
            kernel += 1
        self.blur_kernel.set(kernel)

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="选择待处理图片文件夹")
        if not selected:
            return

        folder = Path(selected)
        image_paths = sorted(path for path in folder.iterdir() if path.suffix.lower() in SUPPORTED_EXTENSIONS)
        if not image_paths:
            self.status_text.set("这个文件夹里没有可处理的图片。")
            return

        self.folder_path = folder
        self.output_dir = folder / "blurred_output"
        self.output_dir.mkdir(exist_ok=True)

        self.image_paths = image_paths
        self.folder_text.set(f"工作目录: {folder}")
        self.status_text.set(f"已载入 {len(image_paths)} 张图片，开始框选即可自动保存。")
        self.open_image(0)

    def open_image(self, index: int) -> None:
        if not self.image_paths:
            return

        index = max(0, min(index, len(self.image_paths) - 1))
        self.current_index = index
        self.current_source_path = self.image_paths[index]
        self.undo_stack.clear()
        self._clear_interaction_state()

        initial_path = self._preferred_load_path(self.current_source_path)
        self.current_image = Image.open(initial_path).convert("RGB")
        self.count_text.set(f"{index + 1} / {len(self.image_paths)}")
        self.filename_text.set(f"当前文件: {self.current_source_path.name}")
        self.save_text.set(f"自动保存: {self._output_path(self.current_source_path).name}")
        self.render_image()

    def prev_image(self) -> None:
        if self.current_index > 0:
            self.open_image(self.current_index - 1)
            self.status_text.set("已切换到上一张图片。")

    def next_image(self) -> None:
        if self.current_index < len(self.image_paths) - 1:
            self.open_image(self.current_index + 1)
            self.status_text.set("已切换到下一张图片。")

    def reload_current(self) -> None:
        if self.current_source_path is None:
            return
        self.open_image(self.current_index)
        self.status_text.set("已重新载入当前图片。")

    def undo_last_blur(self) -> None:
        if not self.undo_stack or self.current_source_path is None:
            self.status_text.set("当前没有可撤销的模糊操作。")
            return
        self.current_image = self.undo_stack.pop()
        self._save_current_image()
        self.render_image()
        self.status_text.set("已撤销上一次模糊并自动保存。")

    def render_image(self) -> None:
        self.canvas.delete("all")
        if self.current_image is None:
            self._render_empty_state()
            return

        canvas_width = max(self.canvas.winfo_width(), 100)
        canvas_height = max(self.canvas.winfo_height(), 100)
        image_width, image_height = self.current_image.size
        scale = min(canvas_width / image_width, canvas_height / image_height)
        display_width = max(1, int(image_width * scale))
        display_height = max(1, int(image_height * scale))
        offset_x = (canvas_width - display_width) // 2
        offset_y = (canvas_height - display_height) // 2
        self.display = DisplayMetrics(offset_x, offset_y, display_width, display_height, scale)

        preview = self.current_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.canvas.create_image(offset_x, offset_y, anchor="nw", image=self.preview_photo)
        self.canvas.create_rectangle(
            offset_x - 1,
            offset_y - 1,
            offset_x + display_width + 1,
            offset_y + display_height + 1,
            outline=THEME_COLORS[self.theme_mode.get()]["image_border"],
            width=1,
        )
        self._refresh_preview_overlay()

    def _render_empty_state(self) -> None:
        width = max(self.canvas.winfo_width(), 100)
        height = max(self.canvas.winfo_height(), 100)
        self.canvas.create_text(
            width / 2,
            height / 2 - 28,
            text="选择一个图片文件夹开始处理",
            fill=THEME_COLORS[self.theme_mode.get()]["section_fg"],
            font=("Microsoft YaHei UI", 28, "bold"),
        )
        self.canvas.create_text(
            width / 2,
            height / 2 + 22,
            text="支持拖拽与定点两种框选方式，可切换矩形和圆形模糊",
            fill=THEME_COLORS[self.theme_mode.get()]["sub_fg"],
            font=("Microsoft YaHei UI", 12),
        )

    def _on_left_click(self, event: tk.Event) -> None:
        if self.current_image is None:
            return

        if self.draw_mode.get() == "drag":
            self.drag_start = (event.x, event.y)
            self._remove_selection_item()
            return

        if self.anchor_point is None:
            self.anchor_point = (event.x, event.y)
            self.last_cursor = (event.x, event.y)
            self._refresh_preview_overlay()
            self.status_text.set("已记录起点，移动鼠标调整框大小，再点一次确认。")
            return

        selection = SelectionBox(
            start_x=self.anchor_point[0],
            start_y=self.anchor_point[1],
            end_x=event.x,
            end_y=event.y,
        )
        self.anchor_point = None
        self._apply_selection(selection)

    def _on_drag_motion(self, event: tk.Event) -> None:
        if self.draw_mode.get() != "drag" or self.drag_start is None:
            return
        self.last_cursor = (event.x, event.y)
        self._draw_preview(self.drag_start[0], self.drag_start[1], event.x, event.y)

    def _on_drag_release(self, event: tk.Event) -> None:
        if self.draw_mode.get() != "drag" or self.drag_start is None:
            return
        selection = SelectionBox(
            start_x=self.drag_start[0],
            start_y=self.drag_start[1],
            end_x=event.x,
            end_y=event.y,
        )
        self.drag_start = None
        self._apply_selection(selection)

    def _on_mouse_move(self, event: tk.Event) -> None:
        self.last_cursor = (event.x, event.y)
        if self.draw_mode.get() == "point" and self.anchor_point is not None:
            self._draw_preview(self.anchor_point[0], self.anchor_point[1], event.x, event.y)

    def _apply_selection(self, selection: SelectionBox) -> None:
        self._remove_selection_item()
        if self.current_image is None:
            return

        image_box = self._canvas_to_image_box(selection)
        if image_box is None:
            self.status_text.set("框选区域太小或超出图片范围，没有执行模糊。")
            return

        self.undo_stack.append(self.current_image.copy())
        self.current_image = self._blur_region(self.current_image, image_box, self.shape_mode.get())
        self._save_current_image()
        self.render_image()

        left, top, right, bottom = image_box
        shape_name = "圆形" if self.shape_mode.get() == "circle" else "矩形"
        self.status_text.set(f"已对{shape_name}区域 ({left}, {top}) - ({right}, {bottom}) 执行模糊并自动保存。")

    def _draw_preview(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        self._remove_selection_item()
        colors = THEME_COLORS[self.theme_mode.get()]
        coords = (start_x, start_y, end_x, end_y)
        if self.shape_mode.get() == "circle":
            self.selection_item = self.canvas.create_oval(
                *coords,
                outline=colors["accent"],
                width=3,
                dash=(7, 4),
            )
        else:
            self.selection_item = self.canvas.create_rectangle(
                *coords,
                outline=colors["accent"],
                width=3,
                dash=(7, 4),
            )

    def _refresh_preview_overlay(self) -> None:
        if self.draw_mode.get() == "point" and self.anchor_point and self.last_cursor:
            self._draw_preview(self.anchor_point[0], self.anchor_point[1], self.last_cursor[0], self.last_cursor[1])
        elif self.draw_mode.get() != "point" and self.drag_start is None:
            self._remove_selection_item()

    def _remove_selection_item(self) -> None:
        if self.selection_item is not None:
            self.canvas.delete(self.selection_item)
            self.selection_item = None

    def _clear_interaction_state(self) -> None:
        self.drag_start = None
        self.anchor_point = None
        self.last_cursor = None
        self._remove_selection_item()

    def _preferred_load_path(self, source_path: Path) -> Path:
        output = self._output_path(source_path)
        return output if output.exists() else source_path

    def _output_path(self, source_path: Path) -> Path:
        if self.output_dir is None:
            return source_path
        return self.output_dir / source_path.name

    def _canvas_to_image_box(self, selection: SelectionBox) -> tuple[int, int, int, int] | None:
        if self.current_image is None:
            return None

        left = min(selection.start_x, selection.end_x)
        top = min(selection.start_y, selection.end_y)
        right = max(selection.start_x, selection.end_x)
        bottom = max(selection.start_y, selection.end_y)

        display_left = self.display.x
        display_top = self.display.y
        display_right = self.display.x + self.display.width
        display_bottom = self.display.y + self.display.height

        left = max(left, display_left)
        top = max(top, display_top)
        right = min(right, display_right)
        bottom = min(bottom, display_bottom)

        if right - left < 6 or bottom - top < 6:
            return None

        scale = self.display.scale or 1.0
        image_width, image_height = self.current_image.size
        img_left = max(0, min(image_width, int((left - display_left) / scale)))
        img_top = max(0, min(image_height, int((top - display_top) / scale)))
        img_right = max(0, min(image_width, int(math.ceil((right - display_left) / scale))))
        img_bottom = max(0, min(image_height, int(math.ceil((bottom - display_top) / scale))))

        if img_right - img_left < 2 or img_bottom - img_top < 2:
            return None
        return img_left, img_top, img_right, img_bottom

    def _blur_region(self, image: Image.Image, box: tuple[int, int, int, int], shape: str) -> Image.Image:
        left, top, right, bottom = box
        working = np.array(image).copy()
        region = working[top:bottom, left:right].copy()
        kernel = self.blur_kernel.get()
        if kernel % 2 == 0:
            kernel += 1

        blurred = cv2.GaussianBlur(region, (kernel, kernel), 0)
        if shape == "circle":
            mask_image = Image.new("L", (right - left, bottom - top), 0)
            ImageDraw.Draw(mask_image).ellipse((0, 0, right - left - 1, bottom - top - 1), fill=255)
            mask = np.array(mask_image)
            result_region = region.copy()
            result_region[mask > 0] = blurred[mask > 0]
            working[top:bottom, left:right] = result_region
        else:
            working[top:bottom, left:right] = blurred
        return Image.fromarray(working)

    def _save_current_image(self) -> None:
        if self.current_image is None or self.current_source_path is None:
            return
        output_path = self._output_path(self.current_source_path)
        self.current_image.save(output_path, quality=95)
        self.save_text.set(f"自动保存: {output_path.name}")


def main() -> None:
    enable_high_dpi()
    root = tk.Tk()
    app = BlurStudioApp(root)
    app.render_image()
    root.mainloop()


if __name__ == "__main__":
    main()
