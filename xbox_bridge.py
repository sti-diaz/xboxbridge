"""
xbox_bridge.py - Convierte un control DirectInput (Bluetooth) en un Xbox 360 virtual (XInput).

Requisitos (Windows):
    pip install pygame vgamepad
    (vgamepad instala/pide ViGEmBus; si no, instalarlo desde github.com/nefarius/ViGEmBus)
    HidHide: ocultar el control real y agregar python.exe / pythonw.exe en "Applications".

Uso:
    python xbox_bridge.py --map    # asistente: te pide presionar cada boton (una sola vez)
    python xbox_bridge.py          # ejecuta el puente
"""
import os
import sys
import json
import time
import pathlib
import threading

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"  # sigue leyendo con GTA en primer plano

import pygame
import vgamepad as vg

# Junto al .exe si esta empaquetado con PyInstaller, si no junto al script
BASE = pathlib.Path(sys.executable if getattr(sys, "frozen", False) else __file__).parent
CFG = BASE / "mapping.json"
# Exe instalado (Program Files no es escribible): %APPDATA%\XboxBridge\mapping.json.
# Un exe portable con mapping.json al lado lo sigue usando.
if getattr(sys, "frozen", False) and not CFG.exists():
    CFG = pathlib.Path(os.environ.get("APPDATA", BASE)) / "XboxBridge" / "mapping.json"
    CFG.parent.mkdir(parents=True, exist_ok=True)
DEADZONE = 0.08
HZ = 250

B = vg.XUSB_BUTTON
BUTTONS = [  # (nombre, constante vgamepad)
    ("A", B.XUSB_GAMEPAD_A), ("B", B.XUSB_GAMEPAD_B),
    ("X", B.XUSB_GAMEPAD_X), ("Y", B.XUSB_GAMEPAD_Y),
    ("LB", B.XUSB_GAMEPAD_LEFT_SHOULDER), ("RB", B.XUSB_GAMEPAD_RIGHT_SHOULDER),
    ("BACK (View)", B.XUSB_GAMEPAD_BACK), ("START (Menu)", B.XUSB_GAMEPAD_START),
    ("GUIDE (Xbox)", B.XUSB_GAMEPAD_GUIDE),
    ("L3 (click stick izq)", B.XUSB_GAMEPAD_LEFT_THUMB),
    ("R3 (click stick der)", B.XUSB_GAMEPAD_RIGHT_THUMB),
]
DPAD = {
    (0, 1): B.XUSB_GAMEPAD_DPAD_UP, (0, -1): B.XUSB_GAMEPAD_DPAD_DOWN,
    (-1, 0): B.XUSB_GAMEPAD_DPAD_LEFT, (1, 0): B.XUSB_GAMEPAD_DPAD_RIGHT,
}


log = print                 # la GUI lo reemplaza para mostrar mensajes en pantalla
stop = threading.Event()    # la GUI lo activa para cancelar mapeo/emulacion


class Stopped(Exception):
    pass


def open_js():
    pygame.init()
    pygame.joystick.init()
    while pygame.joystick.get_count() == 0:
        if stop.is_set():
            raise Stopped
        log("Esperando control (emparejalo por Bluetooth)...")
        time.sleep(1)
        pygame.joystick.quit()
        pygame.joystick.init()
    js = pygame.joystick.Joystick(0)
    js.init()
    log(f"Control: {js.get_name()} | ejes={js.get_numaxes()} botones={js.get_numbuttons()} hats={js.get_numhats()}")
    return js


def poll():
    if stop.is_set():
        raise Stopped
    pygame.event.pump()
    time.sleep(0.01)


def wait_release_all(js):
    while any(js.get_button(i) for i in range(js.get_numbuttons())):
        poll()


def ask_button(js, label):
    log(f"  Presiona: {label}")
    wait_release_all(js)
    while True:
        poll()
        for i in range(js.get_numbuttons()):
            if js.get_button(i):
                log(f"    -> boton {i}")
                wait_release_all(js)
                return i


def ask_axis(js, label):
    log(f"  {label}")
    time.sleep(0.4)
    poll()
    rest = [js.get_axis(i) for i in range(js.get_numaxes())]
    while True:
        poll()
        for i in range(js.get_numaxes()):
            v = js.get_axis(i)
            if abs(v - rest[i]) > 0.6:
                log(f"    -> eje {i}")
                # esperar a que vuelva al reposo
                while abs(js.get_axis(i) - rest[i]) > 0.3:
                    poll()
                return i, rest[i], v


def run_mapping():
    js = open_js()
    m = {"buttons": {}, "axes": {}}
    log("\n== Botones ==")
    for name, _ in BUTTONS:
        m["buttons"][name] = ask_button(js, name)

    log("\n== Sticks (empuja hasta el tope y suelta) ==")
    for key, label in [("LX", "Stick IZQ hacia la DERECHA"), ("LY", "Stick IZQ hacia ARRIBA"),
                       ("RX", "Stick DER hacia la DERECHA"), ("RY", "Stick DER hacia ARRIBA")]:
        i, rest, act = ask_axis(js, label)
        m["axes"][key] = {"axis": i, "sign": 1 if act > rest else -1, "rest": rest}

    log("\n== Gatillos (aprieta a fondo y suelta) ==")
    for key, label in [("LT", "Gatillo IZQ (LT)"), ("RT", "Gatillo DER (RT)")]:
        m["axes"][key] = ask_trigger(js, label)

    CFG.write_text(json.dumps(m, indent=2))
    log(f"\nGuardado en {CFG}.")


def stick(js, cfg):
    v = (js.get_axis(cfg["axis"]) - cfg["rest"]) * cfg["sign"]
    v = max(-1.0, min(1.0, v))
    return 0.0 if abs(v) < DEADZONE else v


def ask_trigger(js, label):
    """Acepta gatillo como eje (analogico) o como boton (digital). El reposo se mide DESPUES de soltar,
    porque SDL reporta 0 en los gatillos hasta que se mueven por primera vez."""
    log(f"  {label}: aprietalo a fondo, mantenlo medio segundo y sueltalo")
    wait_release_all(js)
    poll()
    start = [js.get_axis(i) for i in range(js.get_numaxes())]
    while True:
        poll()
        for b in range(js.get_numbuttons()):
            if js.get_button(b):
                log(f"    -> boton {b} (digital)")
                wait_release_all(js)
                return {"type": "button", "button": b}
        for i in range(js.get_numaxes()):
            if abs(js.get_axis(i) - start[i]) > 0.6:
                samples = []
                t0 = time.time()
                while time.time() - t0 < 2.0:
                    poll()
                    samples.append(js.get_axis(i))
                rest = samples[-1]
                active = max(samples, key=lambda s: abs(s - rest))
                log(f"    -> eje {i} (reposo={rest:.2f}, a fondo={active:.2f})")
                return {"type": "axis", "axis": i, "rest": rest, "active": active}


def probe():
    """Muestra en vivo ejes/botones/hats crudos para ver como llega el control."""
    js = open_js()
    log("Mueve/aprieta cosas. Ctrl+C para salir.")
    last = None
    try:
        while True:
            poll()
            ax = [round(js.get_axis(i), 2) for i in range(js.get_numaxes())]
            bt = [i for i in range(js.get_numbuttons()) if js.get_button(i)]
            ht = [js.get_hat(i) for i in range(js.get_numhats())]
            cur = (ax, bt, ht)
            if cur != last:
                log(f"ejes={ax} botones={bt} hats={ht}")
                last = cur
    except KeyboardInterrupt:
        pass


def trigger(js, cfg):
    if cfg.get("type") == "button":
        return 1.0 if js.get_button(cfg["button"]) else 0.0
    span = cfg["active"] - cfg["rest"]
    v = (js.get_axis(cfg["axis"]) - cfg["rest"]) / span if span else 0.0
    return max(0.0, min(1.0, v))


def run_bridge():
    if not CFG.exists():
        sys.exit("No hay mapping.json. Ejecuta primero:  python xbox_bridge.py --map")
    m = json.loads(CFG.read_text())
    js = open_js()
    pad = vg.VX360Gamepad()
    consts = dict(BUTTONS)
    log("Puente activo (Xbox 360 virtual). Ctrl+C para salir.")
    try:
        while True:
            if stop.is_set():
                break
            pygame.event.pump()
            for name, idx in m["buttons"].items():
                (pad.press_button if js.get_button(idx) else pad.release_button)(button=consts[name])

            if js.get_numhats():
                hx, hy = js.get_hat(0)
                for d, c in DPAD.items():
                    (pad.press_button if (hx, hy) == d else pad.release_button)(button=c)

            a = m["axes"]
            pad.left_joystick_float(stick(js, a["LX"]), stick(js, a["LY"]))
            pad.right_joystick_float(stick(js, a["RX"]), stick(js, a["RY"]))
            pad.left_trigger_float(trigger(js, a["LT"]))
            pad.right_trigger_float(trigger(js, a["RT"]))
            pad.update()
            time.sleep(1 / HZ)
    except (KeyboardInterrupt, Stopped):
        pass
    finally:
        pad.reset()
        pad.update()


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    elif "--map" in sys.argv:
        run_mapping()
    else:
        run_bridge()
