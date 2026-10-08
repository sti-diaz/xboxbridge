# Genera en .\final:
#   XboxBridge.exe        -> version portable (un solo archivo)
#   XboxBridge_Setup.exe  -> instalador (Inno Setup)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Icono .ico e imagenes del asistente de instalacion a partir de logo.png
python -c @"
from PIL import Image
logo = Image.open('logo.png').convert('RGBA')
logo.save('icon.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
bg = (11, 23, 16)
def card(w, h, s):
    im = Image.new('RGB', (w, h), bg)
    l = logo.resize((s, s), Image.LANCZOS)
    im.paste(l, ((w - s) // 2, (h - s) // 2), l)
    return im
card(328, 628, 260).save('wizard_large.bmp')
card(110, 110, 100).save('wizard_small.bmp')
"@
if ($LASTEXITCODE) { throw "No se pudieron generar los iconos" }

$common = @("--noconfirm", "--windowed", "--name", "XboxBridge", "--collect-all", "vgamepad",
            "--hidden-import", "pystray._win32", "--icon", "$PSScriptRoot\icon.ico",
            "--add-data", "$PSScriptRoot\logo.png;.",
            "--workpath", "$env:TEMP\xbb_build", "--specpath", "$env:TEMP\xbb_build")

# Instalable: modo carpeta (arranca mas rapido)
python -m PyInstaller @common --onedir --distpath build xbox_bridge_gui.py
if ($LASTEXITCODE) { throw "PyInstaller (carpeta) fallo" }

# Portable: un solo .exe
New-Item -ItemType Directory -Force final | Out-Null
python -m PyInstaller @common --onefile --distpath final xbox_bridge_gui.py
if ($LASTEXITCODE) { throw "PyInstaller (portable) fallo" }

$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
          "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
          "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Falta Inno Setup 6:  winget install JRSoftware.InnoSetup" }

& $iscc /Qp installer.iss
if ($LASTEXITCODE) { throw "Inno Setup fallo" }

# Limpieza de intermedios (se regeneran en cada compilacion)
Remove-Item -Recurse -Force build, "$env:TEMP\xbb_build", icon.ico, wizard_large.bmp, wizard_small.bmp -ErrorAction SilentlyContinue
Write-Host "Listo: $PSScriptRoot\final"
