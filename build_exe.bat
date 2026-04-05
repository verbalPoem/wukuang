@echo off
setlocal

if not exist .venv (
    py -3.12 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python scripts\generate_brand_assets.py

py -3.12 -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name BlurStudio ^
  --icon assets\app-icon.ico ^
  --add-data "assets\app-icon.ico;assets" ^
  face_blur_studio.py

echo.
echo Build finished. EXE is in dist\BlurStudio\ or dist\BlurStudio.exe depending on PyInstaller output.
pause
