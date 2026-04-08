<div align="center">
  <p>
    <img alt="Wukuang" height="140px" src="./assets/app-icon.png">
  </p>

[简体中文](./README.md) | [English](./README.en.md)

  <h1>雾框 Wukuang</h1>
  <p>面向数据集去敏感、批量图片打码和人工补漏工作流的本地桌面工具</p>
</div>

<p align="center">
    <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg"></a>
    <a href="https://github.com/verbalPoem/wukuang/releases"><img src="https://img.shields.io/github/v/release/verbalPoem/wukuang?color=ffa"></a>
    <a href=""><img src="https://img.shields.io/badge/python-3.12+-3776AB.svg"></a>
    <a href=""><img src="https://img.shields.io/badge/gui-PySide6-41CD52.svg"></a>
    <a href=""><img src="https://img.shields.io/badge/os-windows-0078D6.svg"></a>
    <a href="https://github.com/verbalPoem/wukuang/releases"><img src="https://img.shields.io/github/downloads/verbalPoem/wukuang/total?label=downloads"></a>
</p>

<p align="center">
  <a href="https://github.com/verbalPoem/wukuang/releases"><strong>下载最新版本 &raquo;</strong></a>
  <br />
  <br />
  <a href="#最新更新">最新更新</a>
  &middot;
  <a href="#项目简介">项目简介</a>
  &middot;
  <a href="#核心能力">核心能力</a>
  &middot;
  <a href="#快速开始">快速开始</a>
  &middot;
  <a href="#开发说明">开发说明</a>
</p>

<img src="./assets/release-cover.png" width="100%" />

## 最新更新

### v1.0.5

- 新增中英文界面切换，支持 `🇨🇳 ZH / 🇺🇸 EN`
- 主界面、设置弹窗、关于弹窗、状态提示支持双语切换
- 顶部前后翻页按钮改为更明显的 emoji 风格
- 修复鼠标长按顶部 `A / D` 按钮时无法连续快速浏览的问题
- 优化 README 结构与展示素材，移除明显占位文案

### v1.0.4

- 优化子文件夹切换逻辑，`上一文件夹 / 下一文件夹` 只按上一级目录中的直接子文件夹名称顺序工作
- 打开目录时不再为了母目录进度预扫描同级子文件夹，移动硬盘场景下更稳定
- 母目录进度改为手动统计，不再影响日常处理速度

### v1.0.3

- 新增固定大小点选模式
- 鼠标移动时实时显示蓝色预览框
- 新增常用尺寸预设：`64 / 96 / 128`

## 项目简介

`雾框 Wukuang` 是一个专门为“批量图片去敏感”设计的本地桌面工作台。

它的目标不是替代自动检测模型，而是服务于这样一种真实工作流：

1. 先用 `YOLO` 或其他检测模型处理掉大部分敏感区域
2. 再由人工快速补掉漏网之鱼
3. 保持“看一张、框一下、下一张”的连续节奏

它特别适合这些场景：

- 数据集去敏感
- 图片审核
- 人脸模糊
- 敏感区域遮挡
- 隐私内容处理
- 自动检测后的人工补漏

## 界面预览

<img src="./assets/app-preview.png" width="100%" />

## 核心能力

- 支持三种框选方式：拖拽、定点、固定大小点选
- 支持两种处理形状：矩形、圆形
- 支持矩形圆角控制，预览框与实际处理结果一致
- 支持三种处理模式：高斯、马赛克、修复（Inpaint）
- 支持自动保存，可覆盖原图或输出到 `blurred_output`
- 支持 `A / D` 切图、长按连续浏览、`Shift + A / Shift + D` 子文件夹切换
- 支持 `Ctrl + Z` 撤销与 `R` 重新载入
- 支持高 DPI 显示
- 支持浅色 / 深色 / 中英双语界面

<details>
<summary><strong>为什么这个工具有价值</strong></summary>

很多时候，真正耗时间的不是模型推理，而是模型跑完以后还要人工再补一遍。

`雾框` 就是为这个环节做的：

- 不追求大而全
- 不让用户做多余操作
- 优先保证连续处理大量图片时的节奏感

</details>

<details>
<summary><strong>功能细节</strong></summary>

- 拖拽松手确认
- 定点两次点击确认
- 固定大小单击处理
- 蓝色预览框实时跟随
- 子文件夹顺序切换
- 母目录进度手动统计
- 状态栏高亮反馈
- 预览缓存与邻近图片预加载

</details>

## 快速开始

### 1. 准备图片目录

- 把待处理图片放入同一个子文件夹
- 支持 `jpg`、`jpeg`、`png`、`bmp`、`webp`

### 2. 打开目录

- 启动应用
- 点击 `打开图片目录`
- 选择要处理的图片文件夹

### 3. 处理图片

- 拖拽框选，或使用定点模式
- 也可以切换到固定大小模式，连续点击完成快速打码
- 按 `D` 下一张，按 `A` 上一张
- 按 `Shift + D / Shift + A` 切换同级子文件夹

### 4. 选择处理方式

- `高斯`：适合人脸和一般敏感区域
- `马赛克`：适合更强遮挡场景
- `修复`：适合去除文字、小块水印、局部遮挡

## 快捷键

| 操作 | 快捷键 |
| :--- | :--- |
| 上一张图片 | `A` |
| 下一张图片 | `D` |
| 连续快速翻页 | 长按 `A / D` |
| 上一个子文件夹 | `Shift + A` |
| 下一个子文件夹 | `Shift + D` |
| 撤销上一步 | `Ctrl + Z` |
| 重新载入当前图片 | `R` |
| 打开目录 | `Ctrl + O` |

## 开发说明

### 运行环境

- Windows 10 / 11
- Python 3.12
- PySide6
- OpenCV
- Pillow
- NumPy

### 从源码运行

```powershell
python face_blur_studio.py
```

### 构建 Windows EXE

```powershell
build_exe.bat
```

### 手动构建

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt pyinstaller
python scripts\generate_brand_assets.py
pyinstaller --noconfirm --clean --windowed --icon assets\app-icon.ico --name BlurStudio face_blur_studio.py
```

## 文档

- [v1.0.4 开发文档](./docs/Wukuang-v1.0.4-开发文档.md)
- [GitHub Releases](https://github.com/verbalPoem/wukuang/releases)

## 项目结构

```text
assets/
  app-icon.ico
  app-icon.png
  app-preview.png
  release-cover.png
  screenshot-sheet.png
scripts/
  generate_brand_assets.py
docs/
  Wukuang-v1.0.4-开发文档.md
face_blur_studio.py
wukuang_qt.py
build_exe.bat
requirements.txt
README.md
README.en.md
LICENSE
```

## 技术栈

- GUI：`PySide6`
- 图像处理：`OpenCV` + `Pillow` + `NumPy`
- 系统适配：`ctypes`
- 打包：`PyInstaller`
- 语言：`Python 3.12`

## 已知说明

- `Inpaint` 更适合小面积修复，不适合大面积复杂内容重建
- 如果原图本身是 `JPEG`，覆盖保存仍受其有损格式限制
- 超大图片首次载入仍可能有等待时间，但当前已通过预览缓存和预加载减轻卡顿

## 关于作者

- 开发者：`cca&qyx&codex`
- 开发目的：让批量图片打码流程更高效、更顺手，适合长时间连续处理

## 开源许可

本项目使用 [MIT License](./LICENSE)。

## 后续规划

- 模型联动的预打码工作流
- 多框批量确认
- 更完整的缩放与平移画布体验
- 更多形状与更细粒度的快捷键自定义

