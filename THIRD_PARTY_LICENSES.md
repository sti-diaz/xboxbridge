# Licencias de terceros

El código de Xbox Bridge se distribuye bajo la licencia [MIT](LICENSE).
Los ejecutables (`XboxBridge.exe` y `XboxBridge_Setup.exe`) incluyen además los siguientes
componentes de terceros, cada uno bajo su propia licencia. La licencia MIT de este proyecto
**no** se aplica a ellos.

| Componente | Licencia | Código fuente |
|---|---|---|
| [pygame](https://www.pygame.org/) | GNU LGPL 2.1 | https://github.com/pygame/pygame |
| [SDL2](https://www.libsdl.org/) (incluido en pygame) | zlib | https://github.com/libsdl-org/SDL |
| [pystray](https://github.com/moses-palmer/pystray) | GNU LGPL 3.0 | https://github.com/moses-palmer/pystray |
| [vgamepad](https://github.com/yannbouteiller/vgamepad) | MIT | https://github.com/yannbouteiller/vgamepad |
| [ViGEmClient](https://github.com/nefarius/ViGEmClient) (incluido en vgamepad) | MIT | https://github.com/nefarius/ViGEmClient |
| [Pillow](https://python-pillow.org/) | MIT-CMU (HPND) | https://github.com/python-pillow/Pillow |
| [Python](https://www.python.org/) | PSF License | https://github.com/python/cpython |
| Tcl/Tk (tkinter) | Licencia tipo BSD de Tcl/Tk | https://www.tcl-lang.org/ |
| [PyInstaller](https://pyinstaller.org/) (cargador del .exe) | GNU GPL 2.0 con excepción para el bootloader | https://github.com/pyinstaller/pyinstaller |
| [Inno Setup](https://jrsoftware.org/isinfo.php) (instalador) | Licencia de Inno Setup | https://github.com/jrsoftware/issrc |

## Sobre las bibliotecas LGPL (pygame, pystray)

Se usan sin modificaciones, como bibliotecas separadas. Su código fuente está disponible en los
enlaces de arriba. Puedes reemplazarlas por otra versión compatible ejecutando Xbox Bridge desde
el código (`pip install -r requirements.txt` y `python xbox_bridge_gui.py`) o recompilando con
`build_installer.ps1`.

## Software que se instala por separado

Xbox Bridge no incluye estos programas, pero los necesita o los recomienda:

- **ViGEmBus** (driver): https://github.com/nefarius/ViGEmBus
- **HidHide**: https://github.com/nefarius/HidHide

Cada uno tiene su propia licencia, publicada en su repositorio.

## Marcas

Xbox y Xbox 360 son marcas registradas de Microsoft Corporation. Este proyecto no está afiliado
a Microsoft ni cuenta con su respaldo.
