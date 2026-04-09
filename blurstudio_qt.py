from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from collections import OrderedDict
from pathlib import Path
import site
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

for site_dir in [site.getusersitepackages(), *site.getsitepackages()]:
    pyside_dir = Path(site_dir) / "PySide6"
    shiboken_dir = Path(site_dir) / "shiboken6"
    if pyside_dir.exists():
        os.environ["PATH"] = f"{pyside_dir};{pyside_dir / 'lib'};{shiboken_dir};{os.environ.get('PATH', '')}"
        if hasattr(os, "add_dll_directory"):
            for dll_dir in (pyside_dir, pyside_dir / "lib", pyside_dir / "plugins", shiboken_dir):
                if dll_dir.exists():
                    os.add_dll_directory(str(dll_dir))

import shiboken6  # noqa: F401

from PySide6.QtCore import QEasingCurve, QPoint, Property, QRect, QSize, Qt, QPropertyAnimation, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFontMetrics, QIcon, QImage, QImageReader, QKeyEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QFileDialog, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QSizePolicy, QSlider, QVBoxLayout, QWidget


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
APP_TITLE = "BlurStudio"
SETTINGS_PATH = Path(os.getenv("APPDATA", Path.home())) / "BlurStudio" / "settings.json"
DEFAULT_SETTINGS = {
    "theme_mode": "light",
    "ui_language": "zh",
    "draw_mode": "drag",
    "shape_mode": "rect",
    "blur_style": "gaussian",
    "blur_kernel": 61,
    "corner_radius": 18,
    "fixed_box_width": 180,
    "fixed_box_height": 180,
    "auto_advance": False,
    "save_mode": "overwrite",
    "prefetch_span": 4,
}

I18N = {
    "zh": {
        "app_title": "BlurStudio",
        "tagline": "面向批量图片打码与数据集去敏感的本地桌面工具",
        "dir_progress_title": "目录与进度",
        "open_folder": "打开图片目录",
        "rechoose_folder": "重新选择",
        "prev_folder": "上一文件夹",
        "next_folder": "下一文件夹",
        "parent_progress_unknown": "母目录进度: 未统计",
        "parent_progress_none": "母目录进度: -",
        "count_parent_progress": "统计母目录进度",
        "folder_not_selected": "尚未选择目录",
        "current_file": "当前文件: {name}",
        "not_started": "未开始",
        "quick_controls": "快速控制",
        "processing_options": "处理选项",
        "shortcuts_title": "快捷操作",
        "shortcuts_keys": "A / D 切图   Shift+A / Shift+D 切文件夹",
        "shortcuts_hint": "Ctrl+Z 撤销，R 重新载入，长按 A 或 D 可连续浏览图片。",
        "theme": "主题",
        "language": "语言",
        "draw_mode": "框选方式",
        "shape_mode": "模糊形状",
        "blur_style": "模糊样式",
        "save_mode": "保存策略",
        "auto_advance": "自动跳图",
        "blur_strength": "模糊强度",
        "corner_radius": "矩形圆角",
        "fixed_width": "固定宽度",
        "fixed_height": "固定高度",
        "option_hint": "长按 A / D 可以连续快速翻页浏览。",
        "folder_placeholder": "尚未选择文件夹",
        "status_ready": "选择一个图片文件夹开始。",
        "draw_drag": "拖拽",
        "draw_point": "定点",
        "draw_fixed": "固定",
        "draw_drag_meta": "拖拽松手确认",
        "draw_point_meta": "定点两次点击",
        "draw_fixed_meta": "固定大小点选",
        "shape_rect": "矩形",
        "shape_circle": "圆形",
        "shape_rect_meta": "矩形模糊",
        "shape_circle_meta": "圆形模糊",
        "blur_gaussian": "高斯",
        "blur_pixelate": "马赛克",
        "blur_inpaint": "修复",
        "blur_gaussian_meta": "高斯模糊",
        "blur_pixelate_meta": "像素马赛克",
        "blur_inpaint_meta": "智能修复",
        "inpaint_tooltip": "这种模糊方式适合去除字体",
        "save_overwrite": "覆盖原图",
        "save_separate": "单独输出",
        "save_overwrite_meta": "覆盖原图",
        "save_separate_meta": "输出到 blurred_output",
        "off": "关闭",
        "on": "开启",
        "preset_custom": "自定",
        "prev_btn": "⏮️ A",
        "next_btn": "D ⏭️",
        "settings_btn": "⚙",
        "choose_folder_dialog": "选择待处理图片文件夹",
        "choose_folder_failed": "打开目录选择器失败：{error}",
        "read_folder_failed": "读取文件夹失败：{error}",
        "folder_empty": "这个文件夹里没有可处理的图片。",
        "loaded_images": "已载入 {count} 张图片。",
        "outside_folder_nav": "当前目录不在可连续切换的母目录结构中。",
        "last_folder": "已经是母目录里的最后一个子文件夹。",
        "first_folder": "已经是母目录里的第一个子文件夹。",
        "switched_next_folder": "已切换到下一个文件夹：{name}",
        "switched_prev_folder": "已切换到上一个文件夹：{name}",
        "parent_progress_done": "已统计母目录进度。",
        "no_parent_progress": "当前目录没有可统计的母目录。",
        "selection_too_small": "选区太小，没有执行模糊。",
        "auto_saved_next": "已自动保存并跳到下一张。",
        "selection_saved": "已模糊区域 ({left}, {top}) - ({right}, {bottom})。",
        "reloaded": "已重新载入当前图片。",
        "undo_empty": "当前没有可撤销的操作。",
        "undo_done": "已撤销上一步。",
        "settings_title": "偏好设置",
        "settings_header": "⚙ 界面设置",
        "settings_subtitle": "放一些不常改的偏好项，例如语言和深浅主题。",
        "group_ui": "界面偏好",
        "fixed_size_box": "固定大小框",
        "width": "宽度",
        "height": "高度",
        "prefetch": "预加载邻近图片数",
        "about_title": "关于 BlurStudio",
        "about_name": "BlurStudio",
        "about_dev": "开发者：cca&qyx&codex",
        "about_goal": "开发目的：让批量图片打码流程更高效、更顺手，适合长时间连续处理。",
        "about_ok": "知道了",
        "canvas_empty": "选择一个图片文件夹开始处理",
    },
    "en": {
        "app_title": "BlurStudio",
        "tagline": "A local desktop tool for batch image blurring and dataset desensitization",
        "dir_progress_title": "Folders & Progress",
        "open_folder": "Open Image Folder",
        "rechoose_folder": "Choose Again",
        "prev_folder": "Previous Folder",
        "next_folder": "Next Folder",
        "parent_progress_unknown": "Parent Progress: Not counted",
        "parent_progress_none": "Parent Progress: -",
        "count_parent_progress": "Count Parent Progress",
        "folder_not_selected": "No folder selected",
        "current_file": "Current File: {name}",
        "not_started": "Not started",
        "quick_controls": "Quick Controls",
        "processing_options": "Processing",
        "shortcuts_title": "Shortcuts",
        "shortcuts_keys": "A / D images   Shift+A / Shift+D folders",
        "shortcuts_hint": "Ctrl+Z undo, R reload, hold A or D for continuous browsing.",
        "theme": "Theme",
        "language": "Language",
        "draw_mode": "Selection Mode",
        "shape_mode": "Blur Shape",
        "blur_style": "Blur Style",
        "save_mode": "Save Mode",
        "auto_advance": "Auto Next",
        "blur_strength": "Blur Strength",
        "corner_radius": "Corner Radius",
        "fixed_width": "Fixed Width",
        "fixed_height": "Fixed Height",
        "option_hint": "Hold A / D for continuous fast browsing.",
        "folder_placeholder": "No folder selected",
        "status_ready": "Choose an image folder to begin.",
        "draw_drag": "Drag",
        "draw_point": "Point",
        "draw_fixed": "Fixed",
        "draw_drag_meta": "Drag and release",
        "draw_point_meta": "Two-click point mode",
        "draw_fixed_meta": "Fixed-size single click",
        "shape_rect": "Rectangle",
        "shape_circle": "Circle",
        "shape_rect_meta": "Rectangle blur",
        "shape_circle_meta": "Circle blur",
        "blur_gaussian": "Gaussian",
        "blur_pixelate": "Pixelate",
        "blur_inpaint": "Inpaint",
        "blur_gaussian_meta": "Gaussian blur",
        "blur_pixelate_meta": "Pixel mosaic",
        "blur_inpaint_meta": "Smart repair",
        "inpaint_tooltip": "Best for removing text and small overlays",
        "save_overwrite": "Overwrite",
        "save_separate": "Separate Output",
        "save_overwrite_meta": "Overwrite original",
        "save_separate_meta": "Save to blurred_output",
        "off": "Off",
        "on": "On",
        "preset_custom": "Custom",
        "prev_btn": "⏮️ A",
        "next_btn": "D ⏭️",
        "settings_btn": "⚙",
        "choose_folder_dialog": "Choose image folder",
        "choose_folder_failed": "Failed to open folder picker: {error}",
        "read_folder_failed": "Failed to read folder: {error}",
        "folder_empty": "This folder does not contain supported images.",
        "loaded_images": "Loaded {count} images.",
        "outside_folder_nav": "This folder is not part of a navigable parent-folder structure.",
        "last_folder": "Already at the last child folder.",
        "first_folder": "Already at the first child folder.",
        "switched_next_folder": "Switched to next folder: {name}",
        "switched_prev_folder": "Switched to previous folder: {name}",
        "parent_progress_done": "Parent-folder progress counted.",
        "no_parent_progress": "No parent folder available for progress counting.",
        "selection_too_small": "Selection is too small to process.",
        "auto_saved_next": "Saved and moved to the next image.",
        "selection_saved": "Processed region ({left}, {top}) - ({right}, {bottom}).",
        "reloaded": "Reloaded current image.",
        "undo_empty": "Nothing to undo.",
        "undo_done": "Undid the last action.",
        "settings_title": "Preferences",
        "settings_header": "⚙ Interface Settings",
        "settings_subtitle": "Only low-frequency preferences live here, such as language and theme.",
        "group_ui": "Interface Preferences",
        "fixed_size_box": "Fixed-size Box",
        "width": "Width",
        "height": "Height",
        "prefetch": "Neighbor Prefetch Count",
        "about_title": "About BlurStudio",
        "about_name": "BlurStudio",
        "about_dev": "Developers: cca&qyx&codex",
        "about_goal": "Purpose: make batch image masking faster and smoother for long review sessions.",
        "about_ok": "Close",
        "canvas_empty": "Choose an image folder to begin processing",
    },
}


def tr(lang: str, key: str, **kwargs) -> str:
    table = I18N.get(lang, I18N["zh"])
    text = table.get(key, I18N["zh"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)
THEMES = {
    "light": {
        "window": "#edf2f8",
        "sidebar": "#f7f9fc",
        "card": "#ffffff",
        "toolbar": "#f1f5fa",
        "canvas": "#dfe7f1",
        "border": "#d5deea",
        "text": "#162335",
        "muted": "#6d7c92",
        "chip": "#e8eef7",
        "chip_text": "#31445f",
        "primary": "#2b6ff0",
        "primary_hover": "#4681f4",
        "accent": "#5d8fff",
        "shadow": "rgba(19, 33, 56, 0.10)",
        "divider": "rgba(76, 99, 138, 0.12)",
    },
    "dark": {
        "window": "#14171c",
        "sidebar": "#1b2027",
        "card": "#242b34",
        "toolbar": "#20262f",
        "canvas": "#101318",
        "border": "#303948",
        "text": "#eef3fb",
        "muted": "#a7b1c1",
        "chip": "#2a323d",
        "chip_text": "#f1f5fc",
        "primary": "#5f8fff",
        "primary_hover": "#79a5ff",
        "accent": "#7da7ff",
        "shadow": "rgba(0, 0, 0, 0.34)",
        "divider": "rgba(182, 196, 221, 0.10)",
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


def enable_windows_titlebar(win_id: int, dark: bool) -> None:
    if not win_id or not hasattr(ctypes, "windll"):
        return
    value = ctypes.c_int(1 if dark else 0)
    for attribute in (20, 19):
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(win_id),
                wintypes.DWORD(attribute),
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except OSError:
            continue


class SettingsStore:
    @staticmethod
    def load() -> dict:
        data = DEFAULT_SETTINGS.copy()
        if SETTINGS_PATH.exists():
            try:
                loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    for key in data:
                        if key in loaded:
                            data[key] = loaded[key]
            except (OSError, json.JSONDecodeError):
                pass
        return data

    @staticmethod
    def save(data: dict) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class PreviewCache:
    def __init__(self, max_items: int = 72) -> None:
        self.max_items = max_items
        self._cache: OrderedDict[tuple[str, int, int], QPixmap] = OrderedDict()

    def get(self, key: tuple[str, int, int]) -> QPixmap | None:
        value = self._cache.pop(key, None)
        if value is not None:
            self._cache[key] = value
        return value

    def put(self, key: tuple[str, int, int], value: QPixmap) -> None:
        self._cache[key] = value
        while len(self._cache) > self.max_items:
            self._cache.popitem(last=False)

    def clear_path(self, path: Path) -> None:
        for key in [item for item in self._cache if item[0] == str(path)]:
            self._cache.pop(key, None)


class CardFrame(QFrame):
    def __init__(self, object_name: str = "card", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setFrameShape(QFrame.Shape.NoFrame)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(8, 14, 28, 18))
        self.setGraphicsEffect(shadow)


class LogoBadge(QWidget):
    clicked = Signal()

    def __init__(self, icon_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap(str(icon_path)) if icon_path.exists() else QPixmap()
        self._hover_scale = 1.0
        self._anim = QPropertyAnimation(self, b"hoverScale", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(58, 58)
        self.setToolTip("查看开发者信息")

    def get_hover_scale(self) -> float:
        return self._hover_scale

    def set_hover_scale(self, value: float) -> None:
        self._hover_scale = value
        self.update()

    hoverScale = Property(float, get_hover_scale, set_hover_scale)

    def _animate_to(self, value: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover_scale)
        self._anim.setEndValue(value)
        self._anim.start()

    def enterEvent(self, _event) -> None:
        self._animate_to(1.08)

    def leaveEvent(self, _event) -> None:
        self._animate_to(1.0)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(3, 3, -3, -3)
        if not self._pixmap.isNull():
            icon_size = int(46 * self._hover_scale)
            scaled = self._pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2 - int((self._hover_scale - 1.0) * 10)
            painter.drawPixmap(x, y, scaled)
        else:
            painter.setPen(QColor(43, 111, 240))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(18)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "雾")


class SegmentedControl(QWidget):
    changed = Signal(object)

    def __init__(self, options: list[tuple[str, object]], value: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: list[tuple[QPushButton, object]] = []
        self._labels: list[tuple[str, object]] = options[:]
        self._value = value
        self.setObjectName("Segmented")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)
        for label, option_value in options:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setProperty("segment", True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            button.setMinimumHeight(34)
            button.setMinimumWidth(0)
            button.clicked.connect(lambda checked=False, v=option_value: self.set_value(v))
            layout.addWidget(button)
            self._buttons.append((button, option_value))
        self.set_value(value, emit=False)

    def set_value(self, value: object, emit: bool = True) -> None:
        self._value = value
        for button, option_value in self._buttons:
            button.setChecked(option_value == value)
            button.style().unpolish(button)
            button.style().polish(button)
        if emit:
            self.changed.emit(value)

    def value(self) -> object:
        return self._value

    def minimumSizeHint(self):
        return QSize(80, 42)

    def set_labels(self, options: list[tuple[str, object]]) -> None:
        self._labels = options[:]
        self._refresh_labels()

    def set_tooltip_for_value(self, value: object, tooltip: str) -> None:
        for button, option_value in self._buttons:
            if option_value == value:
                button.setToolTip(tooltip)
                return

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        spacing = self.layout().spacing()
        left, _, right, _ = self.layout().getContentsMargins()
        available = max(20, self.width() - left - right - spacing * max(0, len(self._buttons) - 1))
        cell_width = max(12, available // max(1, len(self._buttons)))
        for button, option_value in self._buttons:
            source = next(label for label, value in self._labels if value == option_value)
            metrics = QFontMetrics(button.font())
            button.setText(metrics.elidedText(source, Qt.TextElideMode.ElideRight, cell_width - 14))


class ImageCanvas(QWidget):
    selection_committed = Signal(QRect)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._pixmap: QPixmap | None = None
        self._image_size = QSize()
        self._display_rect = QRect()
        self._display_pixmap: QPixmap | None = None
        self._display_size = QSize()
        self._shape = "rect"
        self._mode = "drag"
        self._corner_radius = 18
        self._fixed_box_size = QSize(
            int(DEFAULT_SETTINGS["fixed_box_width"]),
            int(DEFAULT_SETTINGS["fixed_box_height"]),
        )
        self._empty_text = tr("zh", "canvas_empty")
        self._dragging = False
        self._anchor: QPoint | None = None
        self._current: QPoint | None = None

    def set_preview(self, pixmap: QPixmap | None, image_size: QSize) -> None:
        self._pixmap = pixmap
        self._image_size = image_size
        self._display_pixmap = None
        self._display_size = QSize()
        self._dragging = False
        self._anchor = None
        self._current = None
        self.update()

    def set_modes(self, draw_mode: str, shape_mode: str) -> None:
        self._mode = draw_mode
        self._shape = shape_mode
        self.update()

    def set_corner_radius(self, radius: int) -> None:
        self._corner_radius = max(0, int(radius))
        self.update()

    def set_fixed_box_size(self, width: int, height: int) -> None:
        self._fixed_box_size = QSize(max(8, int(width)), max(8, int(height)))
        self.update()

    def set_empty_text(self, text: str) -> None:
        self._empty_text = text
        self.update()

    def _update_display_rect(self) -> None:
        if self._pixmap is None or self._pixmap.isNull():
            self._display_rect = QRect()
            self._display_pixmap = None
            self._display_size = QSize()
            return
        scaled = self._pixmap.size()
        scaled.scale(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self._display_rect = QRect((self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2, scaled.width(), scaled.height())
        if self._display_pixmap is None or self._display_size != scaled:
            self._display_pixmap = self._pixmap.scaled(
                scaled,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._display_size = scaled

    def resizeEvent(self, event) -> None:
        self._display_pixmap = None
        self._display_size = QSize()
        super().resizeEvent(event)

    def _selection_rect(self) -> QRect:
        if self._mode == "fixed" and self._current is not None:
            return self._fixed_widget_rect(self._current)
        if self._anchor is None or self._current is None:
            return QRect()
        return QRect(self._anchor, self._current).normalized()

    def _fixed_widget_rect(self, point: QPoint) -> QRect:
        if self._image_size.isEmpty() or self._display_rect.isEmpty():
            return QRect()
        x_scale = self._display_rect.width() / max(1, self._image_size.width())
        y_scale = self._display_rect.height() / max(1, self._image_size.height())
        rect_width = max(6, int(self._fixed_box_size.width() * x_scale))
        rect_height = max(6, int(self._fixed_box_size.height() * y_scale))
        left = point.x() - rect_width // 2
        top = point.y() - rect_height // 2
        left = max(self._display_rect.left(), min(left, self._display_rect.right() - rect_width + 1))
        top = max(self._display_rect.top(), min(top, self._display_rect.bottom() - rect_height + 1))
        return QRect(left, top, rect_width, rect_height).intersected(self._display_rect)

    def _selection_update_region(self, rect: QRect) -> QRect:
        if rect.isEmpty():
            return QRect()
        pad = 8
        return rect.adjusted(-pad, -pad, pad, pad)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._update_display_rect()
        if self._pixmap is None or self._pixmap.isNull():
            painter.setPen(QColor(120, 136, 156))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._empty_text)
            return
        if self._display_pixmap is not None:
            painter.drawPixmap(self._display_rect.topLeft(), self._display_pixmap)
        else:
            painter.drawPixmap(self._display_rect, self._pixmap)
        painter.setPen(QPen(QColor(110, 128, 155, 150), 1))
        painter.drawRect(self._display_rect)
        rect = self._selection_rect()
        if not rect.isEmpty():
            painter.setPen(QPen(QColor(89, 140, 255), 2, Qt.PenStyle.DashLine))
            if self._shape == "circle":
                painter.drawEllipse(rect)
            else:
                radius = min(self._display_corner_radius(), rect.width() // 2, rect.height() // 2)
                if radius > 0:
                    painter.drawRoundedRect(rect, radius, radius)
                else:
                    painter.drawRect(rect)

    def _display_corner_radius(self) -> int:
        if self._image_size.isEmpty() or self._display_rect.isEmpty():
            return max(0, self._corner_radius)
        scale = min(
            self._display_rect.width() / max(1, self._image_size.width()),
            self._display_rect.height() / max(1, self._image_size.height()),
        )
        return max(0, int(self._corner_radius * scale))

    def _inside_image(self, point: QPoint) -> bool:
        return self._display_rect.contains(point)

    def mousePressEvent(self, event) -> None:
        point = event.position().toPoint()
        if not self._inside_image(point):
            return
        previous = self._selection_update_region(self._selection_rect())
        if self._mode == "drag":
            self._dragging = True
            self._anchor = point
            self._current = point
        elif self._mode == "fixed":
            self._anchor = None
            self._current = point
            self._commit_selection()
        else:
            if self._anchor is None:
                self._anchor = point
                self._current = point
            else:
                self._current = point
                self._commit_selection()
        self.update(previous.united(self._selection_update_region(self._selection_rect())))

    def mouseMoveEvent(self, event) -> None:
        point = event.position().toPoint()
        if self._mode == "drag" and self._dragging:
            previous = self._selection_update_region(self._selection_rect())
            self._current = point
            self.update(previous.united(self._selection_update_region(self._selection_rect())))
        elif self._mode == "fixed":
            previous = self._selection_update_region(self._selection_rect())
            self._current = point if self._inside_image(point) else None
            self.update(previous.united(self._selection_update_region(self._selection_rect())))
        elif self._mode == "point" and self._anchor is not None:
            previous = self._selection_update_region(self._selection_rect())
            self._current = point
            self.update(previous.united(self._selection_update_region(self._selection_rect())))

    def mouseReleaseEvent(self, _event) -> None:
        if self._mode == "drag" and self._dragging:
            self._dragging = False
            self._commit_selection()

    def _commit_selection(self) -> None:
        if self._mode == "fixed":
            if self._current is None or self._image_size.isEmpty():
                self._current = None
                self.update()
                return
            widget_rect = self._fixed_widget_rect(self._current)
            self._emit_selection_rect(widget_rect)
            return
        if self._anchor is None or self._current is None or self._image_size.isEmpty():
            self._anchor = None
            self._current = None
            self.update()
            return
        widget_rect = QRect(self._anchor, self._current).normalized().intersected(self._display_rect)
        self._anchor = None
        self._current = None
        self.update()
        self._emit_selection_rect(widget_rect)

    def _emit_selection_rect(self, widget_rect: QRect) -> None:
        if widget_rect.width() < 6 or widget_rect.height() < 6:
            return
        x_ratio = self._image_size.width() / max(1, self._display_rect.width())
        y_ratio = self._image_size.height() / max(1, self._display_rect.height())
        image_rect = QRect(
            int((widget_rect.left() - self._display_rect.left()) * x_ratio),
            int((widget_rect.top() - self._display_rect.top()) * y_ratio),
            max(2, int(widget_rect.width() * x_ratio)),
            max(2, int(widget_rect.height() * y_ratio)),
        )
        self.selection_committed.emit(image_rect)


class SettingsDialog(QWidget):
    changed = Signal(dict)

    def __init__(self, settings: dict, language: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings.copy()
        self.language = language
        self.setObjectName("settingsRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        shell.addWidget(self.scroll)

        body = QWidget()
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel(tr(self.language, "settings_header"))
        title.setObjectName("dialogTitle")
        subtitle = QLabel(tr(self.language, "settings_subtitle"))
        subtitle.setObjectName("dialogSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._group_title(tr(self.language, "group_ui")))
        theme_options = [("浅色", "light"), ("深色", "dark")] if self.language == "zh" else [("Light", "light"), ("Dark", "dark")]
        self.theme_segment = self._section(
            layout,
            tr(self.language, "theme"),
            theme_options,
            settings["theme_mode"],
        )
        self.language_segment = self._section(
            layout,
            tr(self.language, "language"),
            [("🇨🇳", "zh"), ("🇺🇸", "en")],
            settings.get("ui_language", DEFAULT_SETTINGS["ui_language"]),
        )
        self.language_segment.set_tooltip_for_value("zh", "Chinese")
        self.language_segment.set_tooltip_for_value("en", "English")

        layout.addStretch(1)

        for segment in (self.theme_segment, self.language_segment):
            segment.changed.connect(self._emit_change)

    def _group_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("groupTitle")
        return label

    def _section(self, layout: QVBoxLayout, title: str, options: list[tuple[str, object]], value: object) -> SegmentedControl:
        card = CardFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._label(title))
        segment = SegmentedControl(options, value)
        card_layout.addWidget(segment)
        layout.addWidget(card)
        return segment

    def _emit_change(self) -> None:
        self.changed.emit(
            {
                "theme_mode": self.theme_segment.value(),
                "ui_language": self.language_segment.value(),
            }
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsStore.load()
        self.theme = THEMES[self.settings["theme_mode"]]
        self.cache = PreviewCache()
        self.image_size_cache: dict[Path, QSize] = {}
        self.image_paths: list[Path] = []
        self.current_index = -1
        self.folder: Path | None = None
        self.parent_folder: Path | None = None
        self.sibling_folders: list[Path] = []
        self.current_folder_index = -1
        self._folder_progress_counted = False
        self.current_source_path: Path | None = None
        self.current_full_image: Image.Image | None = None
        self.undo_stack: list[Image.Image] = []
        self.flip_direction = 0
        self.flip_hold_timer = QTimer(self)
        self.flip_hold_timer.setSingleShot(True)
        self.flip_hold_timer.setInterval(240)
        self.flip_hold_timer.timeout.connect(self._start_flip_repeat)
        self.flip_repeat_timer = QTimer(self)
        self.flip_repeat_timer.setInterval(58)
        self.flip_repeat_timer.timeout.connect(self._flip_step)
        self.prefetch_timer = QTimer(self)
        self.prefetch_timer.setSingleShot(True)
        self.prefetch_timer.setInterval(90)
        self.prefetch_timer.timeout.connect(self._run_prefetch)
        self._pending_prefetch_index: int | None = None
        self.settings_sheet: SettingsDialog | None = None
        self.settings_window: QDialog | None = None
        self.about_window: QDialog | None = None
        self._window_stylesheet = ""
        self.status_reset_timer = QTimer(self)
        self.status_reset_timer.setSingleShot(True)
        self.status_reset_timer.timeout.connect(self._clear_status_highlight)

        self.setWindowTitle(APP_TITLE)
        icon_path = resource_path("assets", "app-icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1680, 1040)
        self.setMinimumSize(1360, 900)
        self._build_ui()
        self._bind_actions()
        self._apply_theme()
        self._update_ui_labels()
        QTimer.singleShot(0, self._sync_sidebar_width)
        QTimer.singleShot(80, lambda: enable_windows_titlebar(int(self.winId()), self.settings["theme_mode"] == "dark"))

    def _lang(self) -> str:
        return str(self.settings.get("ui_language", DEFAULT_SETTINGS["ui_language"]))

    def _t(self, key: str, **kwargs) -> str:
        return tr(self._lang(), key, **kwargs)

    def _theme_options(self) -> list[tuple[str, object]]:
        if self._lang() == "zh":
            return [("浅色", "light"), ("深色", "dark")]
        return [("Light", "light"), ("Dark", "dark")]

    def _language_options(self) -> list[tuple[str, object]]:
        return [("🇨🇳", "zh"), ("🇺🇸", "en")]

    def _draw_options(self) -> list[tuple[str, object]]:
        return [(self._t("draw_drag"), "drag"), (self._t("draw_point"), "point"), (self._t("draw_fixed"), "fixed")]

    def _shape_options(self) -> list[tuple[str, object]]:
        return [(self._t("shape_rect"), "rect"), (self._t("shape_circle"), "circle")]

    def _blur_options(self) -> list[tuple[str, object]]:
        return [(self._t("blur_gaussian"), "gaussian"), (self._t("blur_pixelate"), "pixelate"), (self._t("blur_inpaint"), "inpaint")]

    def _save_options(self) -> list[tuple[str, object]]:
        return [(self._t("save_overwrite"), "overwrite"), (self._t("save_separate"), "separate")]

    def _auto_options(self) -> list[tuple[str, object]]:
        return [(self._t("off"), False), (self._t("on"), True)]

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar_host = QWidget()
        self.sidebar_host = sidebar_host
        sidebar_host.setObjectName("sidebarHost")
        sidebar_host.setFixedWidth(372)
        sidebar_shell = QVBoxLayout(sidebar_host)
        sidebar_shell.setContentsMargins(0, 0, 0, 0)
        sidebar_shell.setSpacing(0)

        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_shell.addWidget(self.sidebar_scroll)
        shell.addWidget(sidebar_host)

        sidebar_body = QWidget()
        self.sidebar_body = sidebar_body
        sidebar_body.setMinimumWidth(0)
        sidebar_body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.sidebar_scroll.setWidget(sidebar_body)
        sidebar = QVBoxLayout(sidebar_body)
        sidebar.setContentsMargins(12, 14, 14, 14)
        sidebar.setSpacing(8)

        header = CardFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 14, 14, 14)
        header_layout.setSpacing(12)
        logo_path = resource_path("assets", "app-icon.ico")
        if not logo_path.exists():
            logo_path = resource_path("assets", "app-icon.png")
        self.logo_badge = LogoBadge(logo_path)
        self.logo_badge.clicked.connect(self.show_about_dialog)
        header_layout.addWidget(self.logo_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        title_wrap = QWidget()
        title_layout = QVBoxLayout(title_wrap)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        self.title_label = QLabel(self._t("app_title"))
        self.title_label.setObjectName("hero")
        title_layout.addWidget(self.title_label)
        self.tagline_label = QLabel(self._t("tagline"))
        self.tagline_label.setObjectName("hint")
        self.tagline_label.setWordWrap(True)
        title_layout.addWidget(self.tagline_label)
        header_layout.addWidget(title_wrap, 1, Qt.AlignmentFlag.AlignVCenter)
        sidebar.addWidget(header)

        library_card = CardFrame()
        action_layout = QVBoxLayout(library_card)
        action_layout.setContentsMargins(12, 12, 12, 12)
        action_layout.setSpacing(8)
        self.library_title_label = QLabel(self._t("dir_progress_title"), objectName="sectionTitle")
        action_layout.addWidget(self.library_title_label)
        self.choose_button = QPushButton(self._t("open_folder"))
        self.choose_button.setObjectName("primary")
        self.rechoose_button = QPushButton(self._t("rechoose_folder"))
        self.rechoose_button.setObjectName("secondary")
        self.prev_folder_button = QPushButton(self._t("prev_folder"))
        self.prev_folder_button.setObjectName("secondary")
        self.prev_folder_button.setEnabled(False)
        self.next_folder_button = QPushButton(self._t("next_folder"))
        self.next_folder_button.setObjectName("secondary")
        self.next_folder_button.setEnabled(False)
        action_layout.addWidget(self.choose_button)
        action_layout.addWidget(self.rechoose_button)
        action_layout.addWidget(self.prev_folder_button)
        action_layout.addWidget(self.next_folder_button)
        self.sidebar_folder = QLabel(self._t("folder_not_selected"))
        self.sidebar_folder.setObjectName("folderLine")
        self.sidebar_folder.setWordWrap(True)
        action_layout.addWidget(self.sidebar_folder)
        self.folder_nav_label = QLabel(self._t("parent_progress_none"))
        self.folder_nav_label.setObjectName("hint")
        action_layout.addWidget(self.folder_nav_label)
        self.count_parent_progress_button = QPushButton(self._t("count_parent_progress"))
        self.count_parent_progress_button.setObjectName("secondary")
        self.count_parent_progress_button.setEnabled(False)
        action_layout.addWidget(self.count_parent_progress_button)
        info_strip = QHBoxLayout()
        self.count_label = QLabel("0 / 0")
        self.count_label.setObjectName("count")
        info_strip.addWidget(self.count_label)
        info_strip.addStretch(1)
        self.save_label = QLabel(self._t("not_started"))
        self.save_label.setObjectName("valueChip")
        info_strip.addWidget(self.save_label)
        action_layout.addLayout(info_strip)
        self.file_label = QLabel(self._t("current_file", name="-"))
        self.file_label.setObjectName("body")
        self.file_label.setWordWrap(True)
        action_layout.addWidget(self.file_label)
        sidebar.addWidget(library_card)

        quick = CardFrame()
        quick_layout = QVBoxLayout(quick)
        quick_layout.setContentsMargins(12, 12, 12, 12)
        quick_layout.setSpacing(8)
        self.quick_title_label = QLabel(self._t("quick_controls"), objectName="sectionTitle")
        quick_layout.addWidget(self.quick_title_label)
        self.draw_segment = SegmentedControl(self._draw_options(), self.settings["draw_mode"])
        self.shape_segment = SegmentedControl(self._shape_options(), self.settings["shape_mode"])
        self.blur_segment = SegmentedControl(self._blur_options(), self.settings["blur_style"])
        self.blur_segment.set_tooltip_for_value("inpaint", self._t("inpaint_tooltip"))
        self.draw_row = self._build_setting_row(self._t("draw_mode"), self.draw_segment)
        self.shape_row = self._build_setting_row(self._t("shape_mode"), self.shape_segment)
        self.blur_row = self._build_setting_row(self._t("blur_style"), self.blur_segment)
        for row in (self.draw_row, self.shape_row, self.blur_row):
            quick_layout.addWidget(row)
        sidebar.addWidget(quick)

        options = CardFrame()
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_layout.setSpacing(8)
        self.options_title_label = QLabel(self._t("processing_options"), objectName="sectionTitle")
        options_layout.addWidget(self.options_title_label)
        self.save_segment = SegmentedControl(self._save_options(), self.settings["save_mode"])
        self.auto_segment = SegmentedControl(self._auto_options(), self.settings["auto_advance"])
        self.save_row = self._build_setting_row(self._t("save_mode"), self.save_segment)
        self.auto_row = self._build_setting_row(self._t("auto_advance"), self.auto_segment)
        options_layout.addWidget(self.save_row)
        options_layout.addWidget(self.auto_row)
        slider_row = QHBoxLayout()
        self.blur_strength_label = QLabel(self._t("blur_strength"), objectName="miniTitle")
        slider_row.addWidget(self.blur_strength_label)
        slider_row.addStretch(1)
        self.blur_value = QLabel(str(self.settings["blur_kernel"]))
        self.blur_value.setObjectName("valueChip")
        slider_row.addWidget(self.blur_value)
        options_layout.addLayout(slider_row)
        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(15, 121)
        self.blur_slider.setValue(int(self.settings["blur_kernel"]))
        self.blur_slider.setFixedHeight(28)
        options_layout.addWidget(self.blur_slider)
        corner_row = QHBoxLayout()
        self.corner_radius_label = QLabel(self._t("corner_radius"), objectName="miniTitle")
        corner_row.addWidget(self.corner_radius_label)
        corner_row.addStretch(1)
        self.corner_value = QLabel(str(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        self.corner_value.setObjectName("valueChip")
        corner_row.addWidget(self.corner_value)
        options_layout.addLayout(corner_row)
        self.corner_slider = QSlider(Qt.Orientation.Horizontal)
        self.corner_slider.setRange(0, 120)
        self.corner_slider.setValue(int(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        self.corner_slider.setFixedHeight(28)
        options_layout.addWidget(self.corner_slider)
        fixed_width_row = QHBoxLayout()
        self.fixed_width_label = QLabel(self._t("fixed_width"), objectName="miniTitle")
        fixed_width_row.addWidget(self.fixed_width_label)
        fixed_width_row.addStretch(1)
        self.fixed_width_value = QLabel(str(int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"]))))
        self.fixed_width_value.setObjectName("valueChip")
        fixed_width_row.addWidget(self.fixed_width_value)
        options_layout.addLayout(fixed_width_row)
        self.fixed_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.fixed_width_slider.setRange(20, 1200)
        self.fixed_width_slider.setValue(int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"])))
        self.fixed_width_slider.setFixedHeight(28)
        options_layout.addWidget(self.fixed_width_slider)
        fixed_height_row = QHBoxLayout()
        self.fixed_height_label = QLabel(self._t("fixed_height"), objectName="miniTitle")
        fixed_height_row.addWidget(self.fixed_height_label)
        fixed_height_row.addStretch(1)
        self.fixed_height_value = QLabel(str(int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"]))))
        self.fixed_height_value.setObjectName("valueChip")
        fixed_height_row.addWidget(self.fixed_height_value)
        options_layout.addLayout(fixed_height_row)
        self.fixed_height_slider = QSlider(Qt.Orientation.Horizontal)
        self.fixed_height_slider.setRange(20, 1200)
        self.fixed_height_slider.setValue(int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"])))
        self.fixed_height_slider.setFixedHeight(28)
        options_layout.addWidget(self.fixed_height_slider)
        self.fixed_preset_segment = SegmentedControl([("64", "64"), ("96", "96"), ("128", "128"), (self._t("preset_custom"), "custom")], "custom")
        self.fixed_preset_segment.set_value(
            self._fixed_preset_value(
                int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"])),
                int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"])),
            ),
            emit=False,
        )
        options_layout.addWidget(self.fixed_preset_segment)
        self.option_hint = QLabel(self._t("option_hint"))
        self.option_hint.setObjectName("hint")
        options_layout.addWidget(self.option_hint)
        sidebar.addWidget(options)

        shortcut = CardFrame()
        shortcut_layout = QVBoxLayout(shortcut)
        shortcut_layout.setContentsMargins(12, 12, 12, 12)
        shortcut_layout.setSpacing(6)
        self.shortcuts_title_label = QLabel(self._t("shortcuts_title"), objectName="sectionTitle")
        shortcut_layout.addWidget(self.shortcuts_title_label)
        self.shortcuts_keys_label = QLabel(self._t("shortcuts_keys"))
        self.shortcuts_keys_label.setObjectName("body")
        self.shortcuts_keys_label.setWordWrap(True)
        shortcut_layout.addWidget(self.shortcuts_keys_label)
        self.shortcuts_hint_label = QLabel(self._t("shortcuts_hint"))
        self.shortcuts_hint_label.setObjectName("hint")
        self.shortcuts_hint_label.setWordWrap(True)
        shortcut_layout.addWidget(self.shortcuts_hint_label)
        sidebar.addWidget(shortcut)
        sidebar.addStretch(1)

        right = QWidget()
        shell.addWidget(right, 1)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        topbar = CardFrame("toolbar")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(12, 10, 12, 10)
        top_layout.setSpacing(8)
        self.folder_pill = QLabel(self._t("folder_placeholder"))
        self.folder_pill.setObjectName("folderPill")
        self.folder_pill.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.prev_button = QPushButton(self._t("prev_btn"))
        self.prev_button.setObjectName("secondary")
        self.next_button = QPushButton(self._t("next_btn"))
        self.next_button.setObjectName("primary")
        self.settings_button = QPushButton(self._t("settings_btn"))
        self.settings_button.setObjectName("secondary")
        self.prev_button.setFixedWidth(84)
        self.next_button.setFixedWidth(84)
        self.settings_button.setFixedWidth(46)
        top_layout.addWidget(self.folder_pill, 1)
        top_layout.addWidget(self.prev_button)
        top_layout.addWidget(self.next_button)
        top_layout.addWidget(self.settings_button)
        right_layout.addWidget(topbar)

        pill_row = QHBoxLayout()
        pill_row.setSpacing(8)
        self.meta_labels: list[QLabel] = []
        for _ in range(4):
            label = QLabel("")
            label.setObjectName("metaPill")
            self.meta_labels.append(label)
            pill_row.addWidget(label, 1)
        right_layout.addLayout(pill_row)

        canvas_card = CardFrame("canvasCard")
        canvas_layout = QVBoxLayout(canvas_card)
        canvas_layout.setContentsMargins(10, 10, 10, 10)
        self.canvas = ImageCanvas()
        self.canvas.setMinimumHeight(520)
        canvas_layout.addWidget(self.canvas)
        right_layout.addWidget(canvas_card, 1)

        status = CardFrame("statusCard")
        self.status_card = status
        status_layout = QHBoxLayout(status)
        status_layout.setContentsMargins(14, 8, 14, 8)
        self.status_label = QLabel(self._t("status_ready"))
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        right_layout.addWidget(status)

    def _bind_actions(self) -> None:
        self.choose_button.clicked.connect(self.choose_folder)
        self.rechoose_button.clicked.connect(self.choose_folder)
        self.prev_folder_button.clicked.connect(self.prev_folder)
        self.next_folder_button.clicked.connect(self.next_folder)
        self.count_parent_progress_button.clicked.connect(self.count_parent_progress)
        self.prev_button.pressed.connect(lambda: self._begin_flip(-1))
        self.next_button.pressed.connect(lambda: self._begin_flip(1))
        self.prev_button.released.connect(self._stop_flip)
        self.next_button.released.connect(self._stop_flip)
        self.settings_button.clicked.connect(self.open_settings)
        self.draw_segment.changed.connect(lambda value: self._apply_setting("draw_mode", value))
        self.shape_segment.changed.connect(lambda value: self._apply_setting("shape_mode", value))
        self.blur_segment.changed.connect(lambda value: self._apply_setting("blur_style", value))
        self.save_segment.changed.connect(lambda value: self._apply_setting("save_mode", value))
        self.auto_segment.changed.connect(lambda value: self._apply_setting("auto_advance", value))
        self.blur_slider.valueChanged.connect(self._blur_slider_changed)
        self.corner_slider.valueChanged.connect(self._corner_slider_changed)
        self.fixed_width_slider.valueChanged.connect(self._fixed_width_slider_changed)
        self.fixed_height_slider.valueChanged.connect(self._fixed_height_slider_changed)
        self.fixed_preset_segment.changed.connect(self._fixed_preset_changed)
        self.canvas.selection_committed.connect(self.apply_selection)

        choose_action = QAction("Choose", self)
        choose_action.setShortcut("Ctrl+O")
        choose_action.triggered.connect(self.choose_folder)
        self.addAction(choose_action)

    def _build_setting_row(self, title_text: str, control: QWidget) -> QWidget:
        row = QWidget()
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        label = QLabel(title_text)
        label.setObjectName("miniTitle")
        layout.addWidget(label)
        layout.addWidget(control)
        row.title_label = label
        return row

    def _sync_sidebar_width(self) -> None:
        if not hasattr(self, "sidebar_scroll") or not hasattr(self, "sidebar_body"):
            return
        viewport_width = self.sidebar_scroll.viewport().width()
        if viewport_width <= 0:
            return
        # Keep the scroll content locked to the visible viewport so controls never spill horizontally.
        self.sidebar_body.setFixedWidth(max(0, viewport_width - 1))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_sidebar_width()

    def _stylesheet(self) -> str:
        c = self.theme
        return f"""
        QMainWindow, QDialog {{
            background: {c['window']};
        }}
        QWidget {{
            background: transparent;
            color: {c['text']};
            font-family: 'Microsoft YaHei UI';
            font-size: 11pt;
        }}
        QWidget#appRoot, QWidget#settingsRoot {{
            background: {c['window']};
        }}
        QWidget#settingsRoot, QWidget#settingsRoot QWidget {{
            color: {c['text']};
        }}
        QWidget#sidebarHost {{
            background: {c['sidebar']};
            border-right: 1px solid {c['divider']};
        }}
        QLabel {{
            background: transparent;
        }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 6px 2px 6px 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(120, 138, 166, 0.42);
            border-radius: 4px;
            min-height: 36px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(120, 138, 166, 0.62);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
            height: 0px;
        }}
        QFrame#card, QFrame#toolbar, QFrame#canvasCard, QFrame#statusCard {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['card']},
                stop:1 {c['toolbar']});
            border: 1px solid {c['border']};
            border-radius: 20px;
        }}
        QFrame#toolbar, QFrame#statusCard {{
            background: {c['toolbar']};
            border-radius: 18px;
        }}
        QFrame#statusCard[statusKind="success"] {{
            background: rgba(56, 176, 110, 0.12);
            border: 1px solid rgba(56, 176, 110, 0.34);
        }}
        QFrame#statusCard[statusKind="warning"] {{
            background: rgba(245, 166, 35, 0.12);
            border: 1px solid rgba(245, 166, 35, 0.34);
        }}
        QFrame#statusCard[statusKind="error"] {{
            background: rgba(228, 86, 73, 0.12);
            border: 1px solid rgba(228, 86, 73, 0.34);
        }}
        QFrame#canvasCard {{
            background: {c['canvas']};
            border-radius: 24px;
        }}
        QLabel#hero {{ font-size: 22pt; font-weight: 700; }}
        QLabel#groupTitle {{
            font-size: 10pt;
            font-weight: 700;
            color: {c['muted']};
            padding: 6px 4px 0 4px;
        }}
        QLabel#subtitle, QLabel#body, QLabel#hint, QLabel#dialogSubtitle, QLabel#miniTitle, QLabel#folderLine, QLabel#statusLabel {{
            color: {c['muted']};
        }}
        QLabel#statusLabel[statusKind="success"] {{
            color: #2d8a57;
            font-weight: 700;
        }}
        QLabel#statusLabel[statusKind="warning"] {{
            color: #b27705;
            font-weight: 700;
        }}
        QLabel#statusLabel[statusKind="error"] {{
            color: #d04b3e;
            font-weight: 700;
        }}
        QLabel#sectionTitle {{ font-size: 10.8pt; font-weight: 700; }}
        QLabel#count {{ font-size: 18pt; font-weight: 700; }}
        QLabel#folderLine {{
            padding: 2px 2px 6px 2px;
        }}
        QLabel#folderPill, QLabel#metaPill, QLabel#valueChip {{
            background: {c['chip']};
            color: {c['chip_text']};
            border: 1px solid {c['border']};
            border-radius: 12px;
            padding: 6px 10px;
            font-weight: 700;
        }}
        QLabel#valueChip {{ min-width: 36px; qproperty-alignment: AlignCenter; }}
        QPushButton {{
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            min-height: 38px;
            padding: 8px 14px;
            font-weight: 700;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['card']},
                stop:1 {c['chip']});
            color: {c['chip_text']};
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['card']},
                stop:1 rgba(255,255,255,0.08));
            border-color: {c['accent']};
        }}
        QPushButton:pressed {{
            padding-top: 10px;
            padding-bottom: 8px;
        }}
        QPushButton#primary {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['primary_hover']},
                stop:1 {c['primary']});
            border-color: rgba(255,255,255,0.14);
            color: white;
        }}
        QPushButton#primary:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['accent']},
                stop:1 {c['primary_hover']});
            border-color: rgba(255,255,255,0.22);
        }}
        QWidget#Segmented {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255,255,255,0.03),
                stop:1 rgba(0,0,0,0.10));
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 18px;
        }}
        QPushButton[segment="true"] {{
            border: 1px solid rgba(255,255,255,0.02);
            border-radius: 14px;
            min-height: 34px;
            padding: 6px 10px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255,255,255,0.02),
                stop:1 rgba(0,0,0,0.08));
            color: {c['chip_text']};
            font-size: 10.4pt;
        }}
        QPushButton[segment="true"]:checked {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['primary_hover']},
                stop:1 {c['primary']});
            border-color: rgba(255,255,255,0.16);
            color: white;
        }}
        QPushButton[segment="true"]:hover {{
            background: rgba(255,255,255,0.06);
            border-color: rgba(255,255,255,0.06);
        }}
        QPushButton[segment="true"]:checked:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c['accent']},
                stop:1 {c['primary_hover']});
        }}
        QSlider {{
            min-height: 28px;
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: rgba(255,255,255,0.08);
            border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{
            background: {c['primary']};
            border-radius: 2px;
        }}
        QSlider::add-page:horizontal {{
            background: rgba(255,255,255,0.08);
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 18px;
            margin: -7px 0;
            border-radius: 9px;
            background: white;
            border: 2px solid {c['primary']};
        }}
        QDialog {{
            border: 1px solid {c['border']};
        }}
        QLabel#dialogTitle {{ font-size: 24pt; font-weight: 700; }}
        """

    def _apply_theme(self) -> None:
        self.theme = THEMES[self.settings["theme_mode"]]
        stylesheet = self._stylesheet()
        self._window_stylesheet = stylesheet
        self.setStyleSheet(stylesheet)
        if self.settings_window is not None:
            self.settings_window.setStyleSheet(stylesheet)
            if self.settings_sheet is not None:
                self.settings_sheet.setStyleSheet(stylesheet)
        if self.about_window is not None:
            self.about_window.setStyleSheet(stylesheet)
        self.canvas.set_modes(self.settings["draw_mode"], self.settings["shape_mode"])
        self.canvas.set_corner_radius(int(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        self.canvas.set_fixed_box_size(
            int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"])),
            int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"])),
        )
        self._update_ui_labels()
        QTimer.singleShot(20, lambda: enable_windows_titlebar(int(self.winId()), self.settings["theme_mode"] == "dark"))
        if self.settings_window is not None:
            QTimer.singleShot(40, lambda: enable_windows_titlebar(int(self.settings_window.winId()), self.settings["theme_mode"] == "dark"))
        if self.about_window is not None:
            QTimer.singleShot(40, lambda: enable_windows_titlebar(int(self.about_window.winId()), self.settings["theme_mode"] == "dark"))

    def _meta_texts(self) -> tuple[str, str, str, str]:
        return (
            self._t("draw_drag_meta") if self.settings["draw_mode"] == "drag" else (self._t("draw_point_meta") if self.settings["draw_mode"] == "point" else self._t("draw_fixed_meta")),
            self._t("shape_rect_meta") if self.settings["shape_mode"] == "rect" else self._t("shape_circle_meta"),
            self._t("blur_gaussian_meta") if self.settings["blur_style"] == "gaussian" else (self._t("blur_pixelate_meta") if self.settings["blur_style"] == "pixelate" else self._t("blur_inpaint_meta")),
            self._t("save_overwrite_meta") if self.settings["save_mode"] == "overwrite" else self._t("save_separate_meta"),
        )

    def _fixed_preset_value(self, width: int, height: int) -> str:
        if width == height and width in {64, 96, 128}:
            return str(width)
        return "custom"

    def _update_ui_labels(self) -> None:
        self.setWindowTitle(self._t("app_title"))
        self.title_label.setText(self._t("app_title"))
        self.tagline_label.setText(self._t("tagline"))
        self.library_title_label.setText(self._t("dir_progress_title"))
        self.choose_button.setText(self._t("open_folder"))
        self.rechoose_button.setText(self._t("rechoose_folder"))
        self.prev_folder_button.setText(self._t("prev_folder"))
        self.next_folder_button.setText(self._t("next_folder"))
        self.count_parent_progress_button.setText(self._t("count_parent_progress"))
        self.quick_title_label.setText(self._t("quick_controls"))
        self.options_title_label.setText(self._t("processing_options"))
        self.shortcuts_title_label.setText(self._t("shortcuts_title"))
        self.shortcuts_keys_label.setText(self._t("shortcuts_keys"))
        self.shortcuts_hint_label.setText(self._t("shortcuts_hint"))
        self.blur_strength_label.setText(self._t("blur_strength"))
        self.corner_radius_label.setText(self._t("corner_radius"))
        self.fixed_width_label.setText(self._t("fixed_width"))
        self.fixed_height_label.setText(self._t("fixed_height"))
        self.option_hint.setText(self._t("option_hint"))
        self.prev_button.setText(self._t("prev_btn"))
        self.next_button.setText(self._t("next_btn"))
        self.settings_button.setText(self._t("settings_btn"))
        self.draw_row.title_label.setText(self._t("draw_mode"))
        self.shape_row.title_label.setText(self._t("shape_mode"))
        self.blur_row.title_label.setText(self._t("blur_style"))
        self.save_row.title_label.setText(self._t("save_mode"))
        self.auto_row.title_label.setText(self._t("auto_advance"))
        self.draw_segment.set_labels(self._draw_options())
        self.shape_segment.set_labels(self._shape_options())
        self.blur_segment.set_labels(self._blur_options())
        self.blur_segment.set_tooltip_for_value("inpaint", self._t("inpaint_tooltip"))
        self.save_segment.set_labels(self._save_options())
        self.auto_segment.set_labels(self._auto_options())
        self.fixed_preset_segment.set_labels([("64", "64"), ("96", "96"), ("128", "128"), (self._t("preset_custom"), "custom")])
        self.blur_slider.blockSignals(True)
        self.blur_slider.setValue(int(self.settings["blur_kernel"]))
        self.blur_slider.blockSignals(False)
        self.blur_value.setText(str(self.settings["blur_kernel"]))
        self.corner_slider.blockSignals(True)
        self.corner_slider.setValue(int(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        self.corner_slider.blockSignals(False)
        self.corner_value.setText(str(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        self.fixed_width_slider.blockSignals(True)
        self.fixed_width_slider.setValue(int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"])))
        self.fixed_width_slider.blockSignals(False)
        self.fixed_width_value.setText(str(int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"]))))
        self.fixed_height_slider.blockSignals(True)
        self.fixed_height_slider.setValue(int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"])))
        self.fixed_height_slider.blockSignals(False)
        self.fixed_height_value.setText(str(int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"]))))
        self.fixed_preset_segment.set_value(
            self._fixed_preset_value(
                int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"])),
                int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"])),
            ),
            emit=False,
        )
        for label, text in zip(self.meta_labels, self._meta_texts(), strict=False):
            label.setText(text)
        if self.folder is None:
            self.folder_pill.setText(self._t("folder_placeholder"))
            self.sidebar_folder.setText(self._t("folder_not_selected"))
            self.file_label.setText(self._t("current_file", name="-"))
            self.status_label.setText(self._t("status_ready"))
        self.draw_segment.set_value(self.settings["draw_mode"], emit=False)
        self.shape_segment.set_value(self.settings["shape_mode"], emit=False)
        self.blur_segment.set_value(self.settings["blur_style"], emit=False)
        self.save_segment.set_value(self.settings["save_mode"], emit=False)
        self.auto_segment.set_value(self.settings["auto_advance"], emit=False)
        self.canvas.set_empty_text(self._t("canvas_empty"))
        self._update_folder_navigation_state()

    def _apply_setting(self, key: str, value: object) -> None:
        self.settings[key] = value
        SettingsStore.save(self.settings)
        if key in {"theme_mode", "ui_language", "draw_mode", "shape_mode", "corner_radius", "fixed_box_width", "fixed_box_height"}:
            self._apply_theme()
        else:
            self._update_ui_labels()
        if key == "save_mode" and self.current_index >= 0:
            self.show_image(self.current_index, force=True)

    def _blur_slider_changed(self, value: int) -> None:
        if value % 2 == 0:
            value += 1
        self.settings["blur_kernel"] = value
        self.blur_value.setText(str(value))
        SettingsStore.save(self.settings)

    def _corner_slider_changed(self, value: int) -> None:
        self.settings["corner_radius"] = int(value)
        self.corner_value.setText(str(value))
        self.canvas.set_corner_radius(int(value))
        SettingsStore.save(self.settings)

    def _fixed_width_slider_changed(self, value: int) -> None:
        self.settings["fixed_box_width"] = int(value)
        self.fixed_width_value.setText(str(value))
        self.canvas.set_fixed_box_size(
            int(value),
            int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"])),
        )
        self.fixed_preset_segment.set_value(
            self._fixed_preset_value(
                int(value),
                int(self.settings.get("fixed_box_height", DEFAULT_SETTINGS["fixed_box_height"])),
            ),
            emit=False,
        )
        SettingsStore.save(self.settings)

    def _fixed_height_slider_changed(self, value: int) -> None:
        self.settings["fixed_box_height"] = int(value)
        self.fixed_height_value.setText(str(value))
        self.canvas.set_fixed_box_size(
            int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"])),
            int(value),
        )
        self.fixed_preset_segment.set_value(
            self._fixed_preset_value(
                int(self.settings.get("fixed_box_width", DEFAULT_SETTINGS["fixed_box_width"])),
                int(value),
            ),
            emit=False,
        )
        SettingsStore.save(self.settings)

    def _fixed_preset_changed(self, value: object) -> None:
        if value == "custom":
            return
        size = int(value)
        self.fixed_width_slider.setValue(size)
        self.fixed_height_slider.setValue(size)

    def _begin_flip(self, direction: int) -> None:
        if direction > 0:
            self.next_image()
        elif direction < 0:
            self.prev_image()
        self.flip_direction = direction
        self.flip_hold_timer.start()

    def _stop_flip(self) -> None:
        self.flip_direction = 0
        self.flip_hold_timer.stop()
        self.flip_repeat_timer.stop()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return
        if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and event.key() == Qt.Key.Key_D:
            self.next_folder()
            return
        if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and event.key() == Qt.Key.Key_A:
            self.prev_folder()
            return
        if event.key() == Qt.Key.Key_D:
            self._begin_flip(1)
            return
        if event.key() == Qt.Key.Key_A:
            self._begin_flip(-1)
            return
        if event.key() == Qt.Key.Key_R:
            self.reload_current()
            return
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_Z:
            self.undo_last()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return
        if event.key() in (Qt.Key.Key_A, Qt.Key.Key_D):
            self._stop_flip()
            return
        super().keyReleaseEvent(event)

    def _start_flip_repeat(self) -> None:
        if self.flip_direction != 0:
            self.flip_repeat_timer.start()

    def _flip_step(self) -> None:
        if self.flip_direction > 0:
            self.next_image()
        elif self.flip_direction < 0:
            self.prev_image()

    def choose_folder(self) -> None:
        try:
            folder = QFileDialog.getExistingDirectory(self, self._t("choose_folder_dialog"))
        except Exception as exc:
            self.set_status(self._t("choose_folder_failed", error=exc), kind="error", transient_ms=1800)
            return
        if not folder:
            return
        self.load_folder(Path(folder))

    def _sorted_image_paths(self, directory: Path) -> list[Path]:
        with os.scandir(directory) as iterator:
            paths = [
                Path(entry.path)
                for entry in iterator
                if entry.is_file() and Path(entry.name).suffix.lower() in SUPPORTED_EXTENSIONS
            ]
        return sorted(paths, key=lambda path: path.name.casefold())

    def _ensure_sibling_folders_loaded(self) -> None:
        if self.folder is None or self.parent_folder is None:
            self.sibling_folders = []
            self.current_folder_index = -1
            return
        if self.sibling_folders and 0 <= self.current_folder_index < len(self.sibling_folders):
            return
        try:
            with os.scandir(self.parent_folder) as iterator:
                self.sibling_folders = sorted(
                    [Path(entry.path) for entry in iterator if entry.is_dir()],
                    key=lambda path: path.name.casefold(),
                )
        except OSError:
            self.sibling_folders = []
        self.current_folder_index = self.sibling_folders.index(self.folder) if self.folder in self.sibling_folders else -1

    def _update_folder_navigation_state(self) -> None:
        if self.folder is None:
            self.folder_nav_label.setText(self._t("parent_progress_none"))
            self.count_parent_progress_button.setEnabled(False)
            self.prev_folder_button.setEnabled(False)
            self.next_folder_button.setEnabled(False)
            return
        self._ensure_sibling_folders_loaded()
        self.count_parent_progress_button.setEnabled(self.parent_folder is not None)
        if not self._folder_progress_counted:
            self.folder_nav_label.setText(self._t("parent_progress_unknown"))
        elif not self.sibling_folders or self.current_folder_index < 0:
            self.folder_nav_label.setText(self._t("parent_progress_none"))
        else:
            prefix = "母目录进度" if self._lang() == "zh" else "Parent Progress"
            self.folder_nav_label.setText(f"{prefix}: {self.current_folder_index + 1} / {len(self.sibling_folders)}")
        self.prev_folder_button.setEnabled(self.current_folder_index > 0)
        self.next_folder_button.setEnabled(
            bool(self.sibling_folders) and self.current_folder_index >= 0 and self.current_folder_index < len(self.sibling_folders) - 1
        )

    def count_parent_progress(self) -> None:
        if self.folder is None or self.parent_folder is None:
            self.set_status(self._t("no_parent_progress"), kind="warning", transient_ms=1500)
            return
        self._ensure_sibling_folders_loaded()
        self._folder_progress_counted = True
        self._update_folder_navigation_state()
        self.set_status(self._t("parent_progress_done"), kind="success", transient_ms=1200)

    def load_folder(self, directory: Path) -> bool:
        try:
            image_paths = self._sorted_image_paths(directory)
        except OSError as exc:
            self.set_status(self._t("read_folder_failed", error=exc), kind="error", transient_ms=1800)
            return False
        if not image_paths:
            self.set_status(self._t("folder_empty"), kind="warning", transient_ms=1600)
            return False

        self.image_paths = image_paths
        self.folder = directory
        self.parent_folder = directory.parent if directory.parent != directory else None
        self.sibling_folders = []
        self.current_folder_index = -1
        self._folder_progress_counted = False
        self.folder_pill.setText(f"📂 {directory.name}")
        self.folder_pill.setToolTip(str(directory))
        self.sidebar_folder.setText(str(directory))
        self._update_folder_navigation_state()
        self.show_image(0, force=True)
        self.set_status(self._t("loaded_images", count=len(self.image_paths)), kind="success", transient_ms=1200)
        return True

    def next_folder(self) -> None:
        self._ensure_sibling_folders_loaded()
        if self.folder is None or not self.sibling_folders or self.current_folder_index < 0:
            self.set_status(self._t("outside_folder_nav"), kind="warning", transient_ms=1600)
            return
        next_index = self.current_folder_index + 1
        if next_index >= len(self.sibling_folders):
            self.set_status(self._t("last_folder"), kind="warning", transient_ms=1600)
            return
        next_directory = self.sibling_folders[next_index]
        if self.load_folder(next_directory):
            self.current_folder_index = next_index
            self.set_status(self._t("switched_next_folder", name=next_directory.name), kind="success", transient_ms=1500)

    def prev_folder(self) -> None:
        self._ensure_sibling_folders_loaded()
        if self.folder is None or not self.sibling_folders or self.current_folder_index < 0:
            self.set_status(self._t("outside_folder_nav"), kind="warning", transient_ms=1600)
            return
        prev_index = self.current_folder_index - 1
        if prev_index < 0:
            self.set_status(self._t("first_folder"), kind="warning", transient_ms=1600)
            return
        prev_directory = self.sibling_folders[prev_index]
        if self.load_folder(prev_directory):
            self.current_folder_index = prev_index
            self.set_status(self._t("switched_prev_folder", name=prev_directory.name), kind="success", transient_ms=1500)

    def preferred_path(self, source: Path) -> Path:
        if self.settings["save_mode"] == "overwrite":
            return source
        output_dir = self.folder / "blurred_output"
        output_dir.mkdir(exist_ok=True)
        output = output_dir / source.name
        return output if output.exists() else source

    def output_path(self, source: Path) -> Path:
        if self.settings["save_mode"] == "overwrite":
            return source
        output_dir = self.folder / "blurred_output"
        output_dir.mkdir(exist_ok=True)
        return output_dir / source.name

    def _image_size(self, path: Path) -> QSize:
        if path not in self.image_size_cache:
            reader = QImageReader(str(path))
            size = reader.size()
            self.image_size_cache[path] = size if size.isValid() else QSize(1, 1)
        return self.image_size_cache[path]

    def _load_preview(self, path: Path, target: QSize) -> QPixmap:
        key = (str(path), max(640, target.width()), max(480, target.height()))
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        size = reader.size()
        if size.isValid():
            scaled = size.scaled(QSize(key[1], key[2]), Qt.AspectRatioMode.KeepAspectRatio)
            reader.setScaledSize(scaled)
        image = reader.read()
        if image.isNull():
            pil = Image.open(path).convert("RGB")
            pil.thumbnail((key[1], key[2]))
            data = pil.convert("RGBA").tobytes("raw", "RGBA")
            image = QImage(data, pil.width, pil.height, QImage.Format.Format_RGBA8888).copy()
        pixmap = QPixmap.fromImage(image)
        self.cache.put(key, pixmap)
        return pixmap

    def prefetch_neighbors(self, index: int) -> None:
        if not self.image_paths or self.folder is None:
            return
        target = QSize(max(640, self.canvas.width()), max(480, self.canvas.height()))
        span = int(self.settings["prefetch_span"])
        for delta in range(1, span + 1):
            for candidate in (index + delta, index - delta):
                if 0 <= candidate < len(self.image_paths):
                    self._load_preview(self.preferred_path(self.image_paths[candidate]), target)

    def _schedule_prefetch(self, index: int) -> None:
        self._pending_prefetch_index = index
        self.prefetch_timer.start()

    def _run_prefetch(self) -> None:
        if self._pending_prefetch_index is None:
            return
        self.prefetch_neighbors(self._pending_prefetch_index)

    def _pixmap_from_pil(self, image: Image.Image, target: QSize) -> QPixmap:
        preview = image.copy()
        preview.thumbnail((max(640, target.width()), max(480, target.height())))
        rgba = preview.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimage = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888).copy()
        return QPixmap.fromImage(qimage)

    def _refresh_canvas_from_memory(self) -> None:
        if self.current_full_image is None or self.current_source_path is None:
            return
        target = QSize(max(640, self.canvas.width()), max(480, self.canvas.height()))
        pixmap = self._pixmap_from_pil(self.current_full_image, target)
        path = self.output_path(self.current_source_path)
        self.image_size_cache[path] = QSize(self.current_full_image.width, self.current_full_image.height)
        self.canvas.set_preview(pixmap, QSize(self.current_full_image.width, self.current_full_image.height))
        self.count_label.setText(f"{self.current_index + 1} / {len(self.image_paths)}")
        self.file_label.setText(self._t("current_file", name=self.current_source_path.name))
        self.save_label.setText(self._t("save_overwrite") if self.settings["save_mode"] == "overwrite" else self._t("save_separate"))

    def show_image(self, index: int, force: bool = False, clear_undo: bool = True) -> None:
        if not self.image_paths or self.folder is None:
            return
        index = max(0, min(index, len(self.image_paths) - 1))
        if index == self.current_index and not force:
            return
        self.current_index = index
        self.current_source_path = self.image_paths[index]
        self.current_full_image = None
        if clear_undo:
            self.undo_stack.clear()
        path = self.preferred_path(self.current_source_path)
        preview = self._load_preview(path, QSize(max(640, self.canvas.width()), max(480, self.canvas.height())))
        self.canvas.set_preview(preview, self._image_size(path))
        self.count_label.setText(f"{index + 1} / {len(self.image_paths)}")
        self.file_label.setText(self._t("current_file", name=self.current_source_path.name))
        self.save_label.setText(self._t("save_overwrite") if self.settings["save_mode"] == "overwrite" else self._t("save_separate"))
        self._schedule_prefetch(index)

    def ensure_full_image(self) -> Image.Image | None:
        if self.current_source_path is None:
            return None
        if self.current_full_image is None:
            self.current_full_image = Image.open(self.preferred_path(self.current_source_path)).convert("RGB")
        return self.current_full_image

    def apply_selection(self, rect: QRect) -> None:
        image = self.ensure_full_image()
        if image is None or self.current_source_path is None:
            return
        left = max(0, rect.left())
        top = max(0, rect.top())
        right = min(image.width, rect.left() + rect.width())
        bottom = min(image.height, rect.top() + rect.height())
        if right - left < 2 or bottom - top < 2:
            self.set_status(self._t("selection_too_small"), kind="warning", transient_ms=1400)
            return
        self.undo_stack.append(image.copy())
        self.current_full_image = self._blur_region(image, (left, top, right, bottom))
        self._save_current_image()
        self.cache.clear_path(self.current_source_path)
        self.cache.clear_path(self.output_path(self.current_source_path))
        if self.settings["auto_advance"] and self.current_index < len(self.image_paths) - 1:
            self.next_image()
            self.set_status(self._t("auto_saved_next"), kind="success", transient_ms=1600)
        else:
            self._refresh_canvas_from_memory()
            self.set_status(self._t("selection_saved", left=left, top=top, right=right, bottom=bottom), kind="success", transient_ms=1600)

    def _blur_region(self, image: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
        left, top, right, bottom = box
        working = np.array(image).copy()
        region = working[top:bottom, left:right].copy()
        kernel = int(self.settings["blur_kernel"])
        if kernel % 2 == 0:
            kernel += 1
        if self.settings["blur_style"] == "inpaint":
            full_mask = Image.new("L", (image.width, image.height), 0)
            mask_draw = ImageDraw.Draw(full_mask)
            bounds = (left, top, right - 1, bottom - 1)
            if self.settings["shape_mode"] == "circle":
                mask_draw.ellipse(bounds, fill=255)
            else:
                radius = max(0, int(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
                radius = min(radius, max(0, (right - left) // 2), max(0, (bottom - top) // 2))
                if radius > 0:
                    mask_draw.rounded_rectangle(bounds, radius=radius, fill=255)
                else:
                    mask_draw.rectangle(bounds, fill=255)
            working_bgr = cv2.cvtColor(working, cv2.COLOR_RGB2BGR)
            repaired = cv2.inpaint(working_bgr, np.array(full_mask), 3, cv2.INPAINT_TELEA)
            return Image.fromarray(cv2.cvtColor(repaired, cv2.COLOR_BGR2RGB))
        elif self.settings["blur_style"] == "pixelate":
            block = max(2, kernel // 8)
            small = cv2.resize(region, (max(2, region.shape[1] // block), max(2, region.shape[0] // block)), interpolation=cv2.INTER_LINEAR)
            blurred = cv2.resize(small, (region.shape[1], region.shape[0]), interpolation=cv2.INTER_NEAREST)
        else:
            blurred = cv2.GaussianBlur(region, (kernel, kernel), 0)
        if self.settings["shape_mode"] == "circle":
            mask_image = Image.new("L", (right - left, bottom - top), 0)
            ImageDraw.Draw(mask_image).ellipse((0, 0, right - left - 1, bottom - top - 1), fill=255)
            mask = np.array(mask_image)
            region[mask > 0] = blurred[mask > 0]
            working[top:bottom, left:right] = region
        else:
            radius = max(0, int(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
            if radius > 0:
                radius = min(radius, max(0, (right - left) // 2), max(0, (bottom - top) // 2))
                mask_image = Image.new("L", (right - left, bottom - top), 0)
                ImageDraw.Draw(mask_image).rounded_rectangle(
                    (0, 0, right - left - 1, bottom - top - 1),
                    radius=radius,
                    fill=255,
                )
                mask = np.array(mask_image)
                region[mask > 0] = blurred[mask > 0]
                working[top:bottom, left:right] = region
            else:
                working[top:bottom, left:right] = blurred
        return Image.fromarray(working)

    def _save_current_image(self) -> None:
        if self.current_source_path is None or self.current_full_image is None:
            return
        target = self.output_path(self.current_source_path)
        save_kwargs = {}
        if target.suffix.lower() in {".jpg", ".jpeg"}:
            save_kwargs["quality"] = 100
            save_kwargs["subsampling"] = 0
            save_kwargs["optimize"] = False
            save_kwargs["progressive"] = False
        elif target.suffix.lower() == ".png":
            save_kwargs["compress_level"] = 0
        self.current_full_image.save(target, **save_kwargs)
        self.save_label.setText(self._t("save_overwrite") if self.settings["save_mode"] == "overwrite" else self._t("save_separate"))

    def prev_image(self) -> None:
        if self.current_index > 0:
            self.show_image(self.current_index - 1)

    def next_image(self) -> None:
        if self.current_index < len(self.image_paths) - 1:
            self.show_image(self.current_index + 1)

    def reload_current(self) -> None:
        if self.current_index >= 0:
            self.show_image(self.current_index, force=True)
            self.set_status(self._t("reloaded"), transient_ms=1200)

    def undo_last(self) -> None:
        if not self.undo_stack or self.current_source_path is None:
            self.set_status(self._t("undo_empty"), kind="warning", transient_ms=1500)
            return
        self.current_full_image = self.undo_stack.pop()
        self._save_current_image()
        self.cache.clear_path(self.current_source_path)
        self.cache.clear_path(self.output_path(self.current_source_path))
        self._refresh_canvas_from_memory()
        self.set_status(self._t("undo_done"), kind="success", transient_ms=1600)

    def open_settings(self) -> None:
        if self.settings_window is not None and self.settings_window.isVisible():
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        self.settings_window = None
        self.settings_sheet = None
        dialog = QDialog(self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        dialog.setObjectName("settingsDialog")
        dialog.setWindowTitle(self._t("settings_title"))
        dialog.resize(760, 720)
        dialog.setStyleSheet(self._window_stylesheet or self._stylesheet())
        sheet = SettingsDialog(self.settings, self._lang(), dialog)
        sheet.setStyleSheet(self._window_stylesheet or self._stylesheet())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sheet)
        sheet.changed.connect(self._apply_settings_from_dialog)
        dialog.finished.connect(self._clear_settings_refs)
        dialog.show()
        self.settings_sheet = sheet
        self.settings_window = dialog
        QTimer.singleShot(40, lambda: enable_windows_titlebar(int(dialog.winId()), self.settings["theme_mode"] == "dark"))

    def _clear_settings_refs(self) -> None:
        self.settings_sheet = None
        self.settings_window = None

    def _apply_settings_from_dialog(self, data: dict) -> None:
        old_theme = self.settings["theme_mode"]
        old_language = self.settings.get("ui_language", DEFAULT_SETTINGS["ui_language"])
        self.settings.update(data)
        SettingsStore.save(self.settings)
        self._update_ui_labels()
        self._apply_theme()
        if (old_theme != self.settings["theme_mode"] or old_language != self.settings.get("ui_language")) and self.settings_window is not None:
            geometry = self.settings_window.geometry()
            self.settings_window.close()
            QTimer.singleShot(30, lambda g=geometry: self._reopen_settings(g))
        if self.current_index >= 0:
            self.show_image(self.current_index, force=True)

    def _reopen_settings(self, geometry: QRect) -> None:
        self.open_settings()
        if self.settings_window is not None:
            self.settings_window.setGeometry(geometry)

    def show_about_dialog(self) -> None:
        if self.about_window is not None and self.about_window.isVisible():
            self.about_window.raise_()
            self.about_window.activateWindow()
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("about_title"))
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        dialog.setStyleSheet(self._window_stylesheet or self._stylesheet())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)
        layout.addWidget(QLabel(self._t("about_name"), objectName="dialogTitle"))
        layout.addWidget(QLabel(self._t("about_dev"), objectName="sectionTitle"))
        layout.addWidget(QLabel(self._t("about_goal"), objectName="body"))
        close_button = QPushButton(self._t("about_ok"))
        close_button.setObjectName("primary")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        dialog.finished.connect(lambda *_: setattr(self, "about_window", None))
        dialog.resize(520, 240)
        dialog.show()
        self.about_window = dialog
        QTimer.singleShot(40, lambda: enable_windows_titlebar(int(dialog.winId()), self.settings["theme_mode"] == "dark"))

    def _clear_status_highlight(self) -> None:
        self.status_card.setProperty("statusKind", "info")
        self.status_label.setProperty("statusKind", "info")
        self.status_card.style().unpolish(self.status_card)
        self.status_card.style().polish(self.status_card)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def set_status(self, text: str, kind: str = "info", transient_ms: int = 0) -> None:
        self.status_label.setText(text)
        self.status_card.setProperty("statusKind", kind)
        self.status_label.setProperty("statusKind", kind)
        self.status_card.style().unpolish(self.status_card)
        self.status_card.style().polish(self.status_card)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        if transient_ms > 0:
            self.status_reset_timer.start(transient_ms)
        else:
            self.status_reset_timer.stop()


def main() -> None:
    enable_high_dpi()
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_TITLE)
    icon_path = resource_path("assets", "app-icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.showMaximized()
    app.exec()
