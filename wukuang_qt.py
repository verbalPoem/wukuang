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
APP_TITLE = "雾框"
SETTINGS_PATH = Path(os.getenv("APPDATA", Path.home())) / "Wukuang" / "settings.json"
DEFAULT_SETTINGS = {
    "theme_mode": "light",
    "draw_mode": "drag",
    "shape_mode": "rect",
    "blur_style": "gaussian",
    "blur_kernel": 61,
    "corner_radius": 18,
    "auto_advance": False,
    "save_mode": "overwrite",
    "prefetch_span": 4,
}


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
        if self._anchor is None or self._current is None:
            return QRect()
        return QRect(self._anchor, self._current).normalized()

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
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "选择一个图片文件夹开始处理")
            return
        if self._display_pixmap is not None:
            painter.drawPixmap(self._display_rect.topLeft(), self._display_pixmap)
        else:
            painter.drawPixmap(self._display_rect, self._pixmap)
        painter.setPen(QPen(QColor(110, 128, 155, 150), 1))
        painter.drawRect(self._display_rect)
        if self._anchor and self._current:
            rect = self._selection_rect()
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
        elif self._mode == "point" and self._anchor is not None:
            previous = self._selection_update_region(self._selection_rect())
            self._current = point
            self.update(previous.united(self._selection_update_region(self._selection_rect())))

    def mouseReleaseEvent(self, _event) -> None:
        if self._mode == "drag" and self._dragging:
            self._dragging = False
            self._commit_selection()

    def _commit_selection(self) -> None:
        if self._anchor is None or self._current is None or self._image_size.isEmpty():
            self._anchor = None
            self._current = None
            self.update()
            return
        widget_rect = QRect(self._anchor, self._current).normalized().intersected(self._display_rect)
        self._anchor = None
        self._current = None
        self.update()
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

    def __init__(self, settings: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings.copy()
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

        title = QLabel("⚙ 偏好设置")
        title.setObjectName("dialogTitle")
        subtitle = QLabel("调整主题、翻页和模糊参数，所有更改会即时生效。")
        subtitle.setObjectName("dialogSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._group_title("界面与交互"))
        self.theme_segment = self._section(layout, "界面主题", [("浅色", "light"), ("深色", "dark")], settings["theme_mode"])
        self.draw_segment = self._section(layout, "框选方式", [("拖拽", "drag"), ("定点", "point")], settings["draw_mode"])
        self.shape_segment = self._section(layout, "模糊形状", [("矩形", "rect"), ("圆形", "circle")], settings["shape_mode"])
        self.save_segment = self._section(layout, "保存策略", [("覆盖原图", "overwrite"), ("单独输出", "separate")], settings["save_mode"])
        self.auto_segment = self._section(layout, "处理后自动跳图", [("关闭", False), ("开启", True)], settings["auto_advance"])
        layout.addWidget(self._group_title("模糊与修复"))
        self.blur_segment = self._section(layout, "模糊样式", [("高斯", "gaussian"), ("马赛克", "pixelate"), ("修复", "inpaint")], settings["blur_style"])
        self.blur_segment.set_tooltip_for_value("inpaint", "这种模糊方式适合去除字体")

        kernel_card = CardFrame()
        kernel_layout = QVBoxLayout(kernel_card)
        kernel_layout.setContentsMargins(16, 16, 16, 16)
        kernel_layout.setSpacing(10)
        kernel_layout.addWidget(self._label("模糊强度"))
        row = QHBoxLayout()
        self.kernel_slider = QSlider(Qt.Orientation.Horizontal)
        self.kernel_slider.setRange(15, 121)
        self.kernel_slider.setValue(int(settings["blur_kernel"]))
        self.kernel_slider.setFixedHeight(28)
        self.kernel_value = QLabel(str(self.kernel_slider.value()))
        self.kernel_value.setObjectName("valueChip")
        row.addWidget(self.kernel_slider)
        row.addWidget(self.kernel_value)
        kernel_layout.addLayout(row)
        layout.addWidget(kernel_card)

        corner_card = CardFrame()
        corner_layout = QVBoxLayout(corner_card)
        corner_layout.setContentsMargins(16, 16, 16, 16)
        corner_layout.setSpacing(10)
        corner_layout.addWidget(self._label("矩形圆角"))
        corner_row = QHBoxLayout()
        self.corner_slider = QSlider(Qt.Orientation.Horizontal)
        self.corner_slider.setRange(0, 120)
        self.corner_slider.setValue(int(settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        self.corner_slider.setFixedHeight(28)
        self.corner_value = QLabel(str(self.corner_slider.value()))
        self.corner_value.setObjectName("valueChip")
        corner_row.addWidget(self.corner_slider)
        corner_row.addWidget(self.corner_value)
        corner_layout.addLayout(corner_row)
        layout.addWidget(corner_card)

        layout.addWidget(self._group_title("性能"))
        prefetch_card = CardFrame()
        prefetch_layout = QVBoxLayout(prefetch_card)
        prefetch_layout.setContentsMargins(16, 16, 16, 16)
        prefetch_layout.setSpacing(10)
        prefetch_layout.addWidget(self._label("预加载邻近图片数"))
        prefetch_row = QHBoxLayout()
        self.prefetch_slider = QSlider(Qt.Orientation.Horizontal)
        self.prefetch_slider.setRange(2, 10)
        self.prefetch_slider.setValue(int(settings["prefetch_span"]))
        self.prefetch_slider.setFixedHeight(28)
        self.prefetch_value = QLabel(str(self.prefetch_slider.value()))
        self.prefetch_value.setObjectName("valueChip")
        prefetch_row.addWidget(self.prefetch_slider)
        prefetch_row.addWidget(self.prefetch_value)
        prefetch_layout.addLayout(prefetch_row)
        layout.addWidget(prefetch_card)

        layout.addStretch(1)

        for segment in (self.theme_segment, self.draw_segment, self.shape_segment, self.blur_segment, self.save_segment, self.auto_segment):
            segment.changed.connect(self._emit_change)
        self.kernel_slider.valueChanged.connect(lambda value: self.kernel_value.setText(str(value)))
        self.kernel_slider.valueChanged.connect(self._emit_change)
        self.corner_slider.valueChanged.connect(lambda value: self.corner_value.setText(str(value)))
        self.corner_slider.valueChanged.connect(self._emit_change)
        self.prefetch_slider.valueChanged.connect(lambda value: self.prefetch_value.setText(str(value)))
        self.prefetch_slider.valueChanged.connect(self._emit_change)

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

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
        if self.kernel_slider.value() % 2 == 0:
            self.kernel_slider.setValue(self.kernel_slider.value() + 1)
        self.changed.emit(
            {
                "theme_mode": self.theme_segment.value(),
                "draw_mode": self.draw_segment.value(),
                "shape_mode": self.shape_segment.value(),
                "blur_style": self.blur_segment.value(),
                "save_mode": self.save_segment.value(),
                "auto_advance": self.auto_segment.value(),
                "blur_kernel": self.kernel_slider.value(),
                "corner_radius": self.corner_slider.value(),
                "prefetch_span": self.prefetch_slider.value(),
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
        title = QLabel(APP_TITLE)
        title.setObjectName("hero")
        title_layout.addWidget(title)
        header_layout.addWidget(title_wrap, 1, Qt.AlignmentFlag.AlignVCenter)
        sidebar.addWidget(header)

        library_card = CardFrame()
        action_layout = QVBoxLayout(library_card)
        action_layout.setContentsMargins(12, 12, 12, 12)
        action_layout.setSpacing(8)
        action_layout.addWidget(QLabel("目录与进度", objectName="sectionTitle"))
        self.choose_button = QPushButton("打开图片目录")
        self.choose_button.setObjectName("primary")
        self.rechoose_button = QPushButton("重新选择")
        self.rechoose_button.setObjectName("secondary")
        self.prev_folder_button = QPushButton("上一文件夹")
        self.prev_folder_button.setObjectName("secondary")
        self.prev_folder_button.setEnabled(False)
        self.next_folder_button = QPushButton("下一文件夹")
        self.next_folder_button.setObjectName("secondary")
        self.next_folder_button.setEnabled(False)
        action_layout.addWidget(self.choose_button)
        action_layout.addWidget(self.rechoose_button)
        action_layout.addWidget(self.prev_folder_button)
        action_layout.addWidget(self.next_folder_button)
        self.sidebar_folder = QLabel("尚未选择目录")
        self.sidebar_folder.setObjectName("folderLine")
        self.sidebar_folder.setWordWrap(True)
        action_layout.addWidget(self.sidebar_folder)
        self.folder_nav_label = QLabel("母目录进度: -")
        self.folder_nav_label.setObjectName("hint")
        action_layout.addWidget(self.folder_nav_label)
        info_strip = QHBoxLayout()
        self.count_label = QLabel("0 / 0")
        self.count_label.setObjectName("count")
        info_strip.addWidget(self.count_label)
        info_strip.addStretch(1)
        self.save_label = QLabel("未开始")
        self.save_label.setObjectName("valueChip")
        info_strip.addWidget(self.save_label)
        action_layout.addLayout(info_strip)
        self.file_label = QLabel("当前文件: -")
        self.file_label.setObjectName("body")
        self.file_label.setWordWrap(True)
        action_layout.addWidget(self.file_label)
        sidebar.addWidget(library_card)

        quick = CardFrame()
        quick_layout = QVBoxLayout(quick)
        quick_layout.setContentsMargins(12, 12, 12, 12)
        quick_layout.setSpacing(8)
        quick_layout.addWidget(QLabel("快速控制", objectName="sectionTitle"))
        self.theme_segment = SegmentedControl([("浅色", "light"), ("深色", "dark")], self.settings["theme_mode"])
        self.draw_segment = SegmentedControl([("拖拽", "drag"), ("定点", "point")], self.settings["draw_mode"])
        self.shape_segment = SegmentedControl([("矩形", "rect"), ("圆形", "circle")], self.settings["shape_mode"])
        self.blur_segment = SegmentedControl([("高斯", "gaussian"), ("马赛克", "pixelate"), ("修复", "inpaint")], self.settings["blur_style"])
        self.blur_segment.set_tooltip_for_value("inpaint", "这种模糊方式适合去除字体")
        for title_text, control in (("主题", self.theme_segment), ("框选方式", self.draw_segment), ("模糊形状", self.shape_segment), ("模糊样式", self.blur_segment)):
            quick_layout.addWidget(self._build_setting_row(title_text, control))
        sidebar.addWidget(quick)

        options = CardFrame()
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_layout.setSpacing(8)
        options_layout.addWidget(QLabel("处理选项", objectName="sectionTitle"))
        self.save_segment = SegmentedControl([("覆盖原图", "overwrite"), ("单独输出", "separate")], self.settings["save_mode"])
        self.auto_segment = SegmentedControl([("关闭", False), ("开启", True)], self.settings["auto_advance"])
        for title_text, control in (("保存策略", self.save_segment), ("自动跳图", self.auto_segment)):
            options_layout.addWidget(self._build_setting_row(title_text, control))
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("模糊强度", objectName="miniTitle"))
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
        corner_row.addWidget(QLabel("矩形圆角", objectName="miniTitle"))
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
        self.option_hint = QLabel("长按 A / D 可以连续快速翻页浏览。")
        self.option_hint.setObjectName("hint")
        options_layout.addWidget(self.option_hint)
        sidebar.addWidget(options)

        shortcut = CardFrame()
        shortcut_layout = QVBoxLayout(shortcut)
        shortcut_layout.setContentsMargins(12, 12, 12, 12)
        shortcut_layout.setSpacing(6)
        shortcut_layout.addWidget(QLabel("快捷操作", objectName="sectionTitle"))
        keys = QLabel("A / D 切图   Shift+A / Shift+D 切文件夹")
        keys.setObjectName("body")
        keys.setWordWrap(True)
        shortcut_layout.addWidget(keys)
        hint = QLabel("Ctrl+Z 撤销，R 重新载入，长按 A 或 D 可连续浏览图片。")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        shortcut_layout.addWidget(hint)
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
        self.folder_pill = QLabel("尚未选择文件夹")
        self.folder_pill.setObjectName("folderPill")
        self.folder_pill.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.prev_button = QPushButton("← A")
        self.prev_button.setObjectName("secondary")
        self.next_button = QPushButton("D →")
        self.next_button.setObjectName("primary")
        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("secondary")
        self.prev_button.setFixedWidth(68)
        self.next_button.setFixedWidth(68)
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
        self.status_label = QLabel("选择一个图片文件夹开始。")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        right_layout.addWidget(status)

    def _bind_actions(self) -> None:
        self.choose_button.clicked.connect(self.choose_folder)
        self.rechoose_button.clicked.connect(self.choose_folder)
        self.prev_folder_button.clicked.connect(self.prev_folder)
        self.next_folder_button.clicked.connect(self.next_folder)
        self.prev_button.clicked.connect(self.prev_image)
        self.next_button.clicked.connect(self.next_image)
        self.settings_button.clicked.connect(self.open_settings)
        self.theme_segment.changed.connect(lambda value: self._apply_setting("theme_mode", value))
        self.draw_segment.changed.connect(lambda value: self._apply_setting("draw_mode", value))
        self.shape_segment.changed.connect(lambda value: self._apply_setting("shape_mode", value))
        self.blur_segment.changed.connect(lambda value: self._apply_setting("blur_style", value))
        self.save_segment.changed.connect(lambda value: self._apply_setting("save_mode", value))
        self.auto_segment.changed.connect(lambda value: self._apply_setting("auto_advance", value))
        self.blur_slider.valueChanged.connect(self._blur_slider_changed)
        self.corner_slider.valueChanged.connect(self._corner_slider_changed)
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
        self._update_ui_labels()
        QTimer.singleShot(20, lambda: enable_windows_titlebar(int(self.winId()), self.settings["theme_mode"] == "dark"))
        if self.settings_window is not None:
            QTimer.singleShot(40, lambda: enable_windows_titlebar(int(self.settings_window.winId()), self.settings["theme_mode"] == "dark"))
        if self.about_window is not None:
            QTimer.singleShot(40, lambda: enable_windows_titlebar(int(self.about_window.winId()), self.settings["theme_mode"] == "dark"))

    def _meta_texts(self) -> tuple[str, str, str, str]:
        return (
            "拖拽松手确认" if self.settings["draw_mode"] == "drag" else "定点两次点击",
            "矩形模糊" if self.settings["shape_mode"] == "rect" else "圆形模糊",
            "高斯模糊" if self.settings["blur_style"] == "gaussian" else ("像素马赛克" if self.settings["blur_style"] == "pixelate" else "智能修复"),
            "覆盖原图" if self.settings["save_mode"] == "overwrite" else "输出到 blurred_output",
        )

    def _update_ui_labels(self) -> None:
        self.blur_slider.blockSignals(True)
        self.blur_slider.setValue(int(self.settings["blur_kernel"]))
        self.blur_slider.blockSignals(False)
        self.blur_value.setText(str(self.settings["blur_kernel"]))
        self.corner_slider.blockSignals(True)
        self.corner_slider.setValue(int(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        self.corner_slider.blockSignals(False)
        self.corner_value.setText(str(self.settings.get("corner_radius", DEFAULT_SETTINGS["corner_radius"])))
        for label, text in zip(self.meta_labels, self._meta_texts(), strict=False):
            label.setText(text)
        self.theme_segment.set_value(self.settings["theme_mode"], emit=False)
        self.draw_segment.set_value(self.settings["draw_mode"], emit=False)
        self.shape_segment.set_value(self.settings["shape_mode"], emit=False)
        self.blur_segment.set_value(self.settings["blur_style"], emit=False)
        self.save_segment.set_value(self.settings["save_mode"], emit=False)
        self.auto_segment.set_value(self.settings["auto_advance"], emit=False)

    def _apply_setting(self, key: str, value: object) -> None:
        self.settings[key] = value
        SettingsStore.save(self.settings)
        if key in {"theme_mode", "draw_mode", "shape_mode", "corner_radius"}:
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
            self.next_image()
            self.flip_direction = 1
            self.flip_hold_timer.start()
            return
        if event.key() == Qt.Key.Key_A:
            self.prev_image()
            self.flip_direction = -1
            self.flip_hold_timer.start()
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
            self.flip_direction = 0
            self.flip_hold_timer.stop()
            self.flip_repeat_timer.stop()
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
            folder = QFileDialog.getExistingDirectory(self, "选择待处理图片文件夹")
        except Exception as exc:
            self.set_status(f"打开目录选择器失败：{exc}")
            return
        if not folder:
            return
        self.load_folder(Path(folder))

    def _sorted_image_paths(self, directory: Path) -> list[Path]:
        return sorted(
            [path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS],
            key=lambda path: path.name.casefold(),
        )

    def _sorted_child_folders(self, parent: Path) -> list[Path]:
        folders: list[Path] = []
        for child in sorted((path for path in parent.iterdir() if path.is_dir()), key=lambda path: path.name.casefold()):
            try:
                if any(item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS for item in child.iterdir()):
                    folders.append(child)
            except OSError:
                continue
        return folders

    def _update_folder_navigation_state(self) -> None:
        if self.folder is None or not self.sibling_folders or self.current_folder_index < 0:
            self.folder_nav_label.setText("母目录进度: -")
            self.prev_folder_button.setEnabled(False)
            self.next_folder_button.setEnabled(False)
            return
        self.folder_nav_label.setText(f"母目录进度: {self.current_folder_index + 1} / {len(self.sibling_folders)}")
        self.prev_folder_button.setEnabled(self.current_folder_index > 0)
        self.next_folder_button.setEnabled(self.current_folder_index < len(self.sibling_folders) - 1)

    def load_folder(self, directory: Path) -> bool:
        try:
            image_paths = self._sorted_image_paths(directory)
        except OSError as exc:
            self.set_status(f"读取文件夹失败：{exc}", kind="error", transient_ms=1800)
            return False
        if not image_paths:
            self.set_status("这个文件夹里没有可处理的图片。", kind="warning", transient_ms=1600)
            return False

        self.image_paths = image_paths
        self.folder = directory
        self.parent_folder = directory.parent if directory.parent != directory else None
        self.sibling_folders = self._sorted_child_folders(self.parent_folder) if self.parent_folder else []
        self.current_folder_index = self.sibling_folders.index(directory) if directory in self.sibling_folders else -1
        self.folder_pill.setText(f"📂 {directory.name}")
        self.folder_pill.setToolTip(str(directory))
        self.sidebar_folder.setText(str(directory))
        self._update_folder_navigation_state()
        self.show_image(0, force=True)
        self.set_status(f"已载入 {len(self.image_paths)} 张图片。", kind="success", transient_ms=1200)
        return True

    def next_folder(self) -> None:
        if self.folder is None or not self.sibling_folders or self.current_folder_index < 0:
            self.set_status("当前目录不在可连续切换的母目录结构中。", kind="warning", transient_ms=1600)
            return
        next_index = self.current_folder_index + 1
        if next_index >= len(self.sibling_folders):
            self.set_status("已经是母目录里的最后一个子文件夹。", kind="warning", transient_ms=1600)
            return
        next_directory = self.sibling_folders[next_index]
        if self.load_folder(next_directory):
            self.set_status(f"已切换到下一个文件夹：{next_directory.name}", kind="success", transient_ms=1500)

    def prev_folder(self) -> None:
        if self.folder is None or not self.sibling_folders or self.current_folder_index < 0:
            self.set_status("当前目录不在可连续切换的母目录结构中。", kind="warning", transient_ms=1600)
            return
        prev_index = self.current_folder_index - 1
        if prev_index < 0:
            self.set_status("已经是母目录里的第一个子文件夹。", kind="warning", transient_ms=1600)
            return
        prev_directory = self.sibling_folders[prev_index]
        if self.load_folder(prev_directory):
            self.set_status(f"已切换到上一个文件夹：{prev_directory.name}", kind="success", transient_ms=1500)

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
        self.file_label.setText(f"当前文件: {self.current_source_path.name}")
        self.save_label.setText("覆盖原图" if self.settings["save_mode"] == "overwrite" else "单独输出")

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
        self.file_label.setText(f"当前文件: {self.current_source_path.name}")
        self.save_label.setText("覆盖原图" if self.settings["save_mode"] == "overwrite" else "单独输出")
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
            self.set_status("选区太小，没有执行模糊。", kind="warning", transient_ms=1400)
            return
        self.undo_stack.append(image.copy())
        self.current_full_image = self._blur_region(image, (left, top, right, bottom))
        self._save_current_image()
        self.cache.clear_path(self.current_source_path)
        self.cache.clear_path(self.output_path(self.current_source_path))
        if self.settings["auto_advance"] and self.current_index < len(self.image_paths) - 1:
            self.next_image()
            self.set_status("已自动保存并跳到下一张。", kind="success", transient_ms=1600)
        else:
            self._refresh_canvas_from_memory()
            self.set_status(f"已模糊区域 ({left}, {top}) - ({right}, {bottom})。", kind="success", transient_ms=1600)

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
        self.save_label.setText("覆盖原图" if self.settings["save_mode"] == "overwrite" else "单独输出")

    def prev_image(self) -> None:
        if self.current_index > 0:
            self.show_image(self.current_index - 1)

    def next_image(self) -> None:
        if self.current_index < len(self.image_paths) - 1:
            self.show_image(self.current_index + 1)

    def reload_current(self) -> None:
        if self.current_index >= 0:
            self.show_image(self.current_index, force=True)
            self.set_status("已重新载入当前图片。", transient_ms=1200)

    def undo_last(self) -> None:
        if not self.undo_stack or self.current_source_path is None:
            self.set_status("当前没有可撤销的操作。", kind="warning", transient_ms=1500)
            return
        self.current_full_image = self.undo_stack.pop()
        self._save_current_image()
        self.cache.clear_path(self.current_source_path)
        self.cache.clear_path(self.output_path(self.current_source_path))
        self._refresh_canvas_from_memory()
        self.set_status("已撤销上一步。", kind="success", transient_ms=1600)

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
        dialog.setWindowTitle("偏好设置")
        dialog.resize(760, 720)
        dialog.setStyleSheet(self._window_stylesheet or self._stylesheet())
        sheet = SettingsDialog(self.settings, dialog)
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
        self.settings.update(data)
        SettingsStore.save(self.settings)
        self._update_ui_labels()
        self._apply_theme()
        if old_theme != self.settings["theme_mode"] and self.settings_window is not None:
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
        dialog.setWindowTitle("关于 雾框")
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        dialog.setStyleSheet(self._window_stylesheet or self._stylesheet())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(10)
        layout.addWidget(QLabel("雾框", objectName="dialogTitle"))
        layout.addWidget(QLabel("开发者：cca&qyx&codex", objectName="sectionTitle"))
        layout.addWidget(QLabel("开发目的：让批量图片打码流程更高效、更顺手，适合长时间连续处理。", objectName="body"))
        close_button = QPushButton("知道了")
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
