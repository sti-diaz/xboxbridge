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
| [ViGEmBus](https://github.com/nefarius/ViGEmBus) (instalador del driver, incluido en vgamepad) | BSD 3-Clause (texto abajo) | https://github.com/nefarius/ViGEmBus |
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

## Licencia de ViGEmBus

Xbox Bridge redistribuye sin modificaciones el instalador `ViGEmBusSetup_x64.msi` y lo ejecuta
solo si el driver no está instalado. Su licencia exige reproducir este aviso:

```text
BSD 3-Clause License

Copyright (c) 2016-2020, Nefarius Software Solutions e.U.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Software que se instala por separado

Xbox Bridge no incluye este programa, pero lo recomienda:

- **HidHide**: https://github.com/nefarius/HidHide (licencia publicada en su repositorio)

## Marcas

Xbox y Xbox 360 son marcas registradas de Microsoft Corporation. Este proyecto no está afiliado
a Microsoft ni cuenta con su respaldo.
