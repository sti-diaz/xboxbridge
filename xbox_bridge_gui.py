"""
xbox_bridge_gui.py - Interfaz grafica para xbox_bridge.py (Mapear / Emular).

Empaquetar (portable + instalador en .\final): ver build_installer.ps1
--autostart: arranca oculto en la bandeja y empieza a emular solo (lo usa el inicio de Windows).
"""
import ctypes
import json
import pathlib
import queue
import socket
import sys
import threading
import webbrowser
import winreg
import tkinter as tk
from tkinter import ttk

import pystray
from PIL import Image, ImageDraw, ImageTk

import xbox_bridge as xb

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "XboxBridge"
SETTINGS = xb.CFG.parent / "settings.json"
DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=GJP62Y73ZDBR8"
INSTANCE_PORT = 47613  # instancia unica: la segunda le pide a la primera que se muestre
RES = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).parent))
LOGO = Image.open(RES / "logo.png").convert("RGBA")

CLOSE_OPTS = {"ask": "Preguntar", "tray": "Segundo plano", "exit": "Cerrar completamente"}

# Paleta tomada del logo
BG = "#0b1710"
PANEL = "#13261a"
PANEL_HI = "#1b3523"
BORDER = "#34532f"
CREAM = "#dfe6c2"
MUTED = "#8ea883"
NEON = "#3ee05a"
NEON_DK = "#1e8a36"
RED = "#e06a55"
BLUE = "#5bb8e6"
STATE_COLOR = {"emu": NEON, "map": BLUE, None: MUTED}

F_TITLE = ("Bahnschrift SemiBold", 20)
F_SUB = ("Bahnschrift Light", 10)
F_STATUS = ("Bahnschrift SemiBold", 13)
F_PROMPT = ("Bahnschrift", 16)
F_BTN = ("Bahnschrift SemiBold", 12)
F_UI = ("Segoe UI", 10)
F_LOG = ("Consolas", 9)


def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, RUN_NAME)
            return True
    except OSError:
        return False


def set_autostart(on):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, f'"{sys.executable}" --autostart')
        else:
            try:
                winreg.DeleteValue(k, RUN_NAME)
            except FileNotFoundError:
                pass


def load_settings():
    try:
        return json.loads(SETTINGS.read_text())
    except Exception:
        return {}


def save_settings(s):
    try:
        SETTINGS.write_text(json.dumps(s, indent=2))
    except OSError:
        pass


def tray_image(mode):
    """Logo con un punto de estado abajo a la derecha (verde emulando, azul mapeando, gris detenido)."""
    im = LOGO.resize((64, 64), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.ellipse([40, 40, 63, 63], fill=BG)
    d.ellipse([44, 44, 59, 59], fill=STATE_COLOR[mode])
    return im


def dark_titlebar(win):
    """Barra de titulo oscura con el color de fondo (Windows 10 20H1+/11; si falla se ignora)."""
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute
        dwm(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)                        # modo oscuro
        r, g, b = (int(BG[i:i + 2], 16) for i in (1, 3, 5))
        dwm(hwnd, 35, ctypes.byref(ctypes.c_int(r | g << 8 | b << 16)), 4)     # color (solo Win11)
    except Exception:
        pass


def claim_instance():
    """Devuelve el socket servidor si somos la unica instancia; si ya hay otra, la muestra y retorna None."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        srv.bind(("127.0.0.1", INSTANCE_PORT))
        srv.listen(1)
        return srv
    except OSError:
        srv.close()
        try:
            with socket.create_connection(("127.0.0.1", INSTANCE_PORT), timeout=1) as c:
                c.sendall(b"show")
        except OSError:
            pass
        return None


class RoundButton(tk.Canvas):
    """Boton redondeado con hover, en la paleta del logo."""
    STYLES = {  # fondo, fondo hover, borde, texto
        "primary": (NEON_DK, "#26a843", NEON, "#f2ffe8"),
        "secondary": (PANEL_HI, "#23422c", BORDER, CREAM),
        "danger": ("#5a2a22", "#73352a", RED, "#ffe9e4"),
    }

    def __init__(self, master, text, command, width=170, height=46, style="secondary", bg=BG):
        super().__init__(master, width=width, height=height, bg=bg, highlightthickness=0, cursor="hand2")
        self.w, self.h, self.command = width, height, command
        self.text, self.style, self.enabled, self.hover = text, style, True, False
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<ButtonRelease-1>", self._click)
        self.draw()

    def set(self, text=None, style=None, enabled=None):
        if text is not None:
            self.text = text
        if style is not None:
            self.style = style
        if enabled is not None:
            self.enabled = enabled
            self.config(cursor="hand2" if enabled else "arrow")
        self.draw()

    def _hover(self, on):
        self.hover = on
        self.draw()

    def _click(self, e):
        if self.enabled and 0 <= e.x <= self.w and 0 <= e.y <= self.h:
            self.command()

    def draw(self):
        self.delete("all")
        fill, fill_hi, edge, fg = self.STYLES[self.style]
        if not self.enabled:
            fill, edge, fg = PANEL, BORDER, "#56704e"
        elif self.hover:
            fill = fill_hi
        w, h, r = self.w - 2, self.h - 2, 12
        pts = [1 + r, 1, w - r, 1, w, 1, w, 1 + r, w, h - r, w, h, w - r, h, 1 + r, h, 1, h, 1, h - r, 1, 1 + r, 1, 1]
        self.create_polygon(pts, smooth=True, fill=fill, outline=edge, width=2)
        self.create_text(self.w / 2, self.h / 2, text=self.text.upper(), fill=fg, font=F_BTN)


class App:
    def __init__(self, root, srv):
        self.root = root
        self.msgs = queue.Queue()
        self.jobs = queue.Queue()
        self.worker = threading.Thread(target=self.pygame_thread, daemon=True)
        self.worker.start()
        self.mode = None  # None | "map" | "emu"
        self.settings = load_settings()

        root.title("Xbox Bridge")
        root.geometry("520x620")
        root.minsize(460, 540)
        root.configure(bg=BG)
        self.win_icon = ImageTk.PhotoImage(LOGO.resize((64, 64), Image.LANCZOS))
        root.iconphoto(True, self.win_icon)
        dark_titlebar(root)

        # --- cabecera ---
        head = tk.Frame(root, bg=BG)
        head.pack(fill="x", padx=20, pady=(18, 10))
        self.head_logo = ImageTk.PhotoImage(LOGO.resize((76, 76), Image.LANCZOS))
        tk.Label(head, image=self.head_logo, bg=BG).pack(side="left")
        titles = tk.Frame(head, bg=BG)
        titles.pack(side="left", padx=14)
        tk.Label(titles, text="XBOX BRIDGE", font=F_TITLE, fg=CREAM, bg=BG).pack(anchor="w")
        tk.Label(titles, text="Control Bluetooth  ▸  Xbox 360 virtual", font=F_SUB, fg=MUTED, bg=BG).pack(anchor="w")
        donate = tk.Label(head, text="♥ Donar", font=F_SUB, fg=MUTED, bg=BG, cursor="hand2")
        donate.pack(side="right", anchor="n", pady=(4, 0))
        donate.bind("<Enter>", lambda e: donate.config(fg=NEON))
        donate.bind("<Leave>", lambda e: donate.config(fg=MUTED))
        donate.bind("<Button-1>", lambda e: webbrowser.open(DONATE_URL))

        # --- tarjeta de estado ---
        card = tk.Frame(root, bg=PANEL, highlightbackground=BORDER, highlightthickness=2)
        card.pack(fill="x", padx=20, pady=(4, 12))
        srow = tk.Frame(card, bg=PANEL)
        srow.pack(fill="x", padx=16, pady=(14, 2))
        self.dot = tk.Canvas(srow, width=14, height=14, bg=PANEL, highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 10))
        self.status = tk.Label(srow, font=F_STATUS, bg=PANEL, anchor="w", justify="left", wraplength=420)
        self.status.pack(side="left", fill="x")
        self.prompt = tk.Label(card, font=F_PROMPT, fg=NEON, bg=PANEL, wraplength=440, height=2)
        self.prompt.pack(fill="x", padx=16, pady=(0, 10))

        # --- botones ---
        bar = tk.Frame(root, bg=BG)
        bar.pack(pady=(2, 12))
        self.btn_map = RoundButton(bar, "Mapear", self.toggle_map)
        self.btn_map.pack(side="left", padx=8)
        self.btn_emu = RoundButton(bar, "Emular", self.toggle_emu, style="primary")
        self.btn_emu.pack(side="left", padx=8)

        # --- opciones ---
        opts = tk.Frame(root, bg=BG)
        opts.pack(fill="x", padx=22)
        self.auto = tk.BooleanVar(value=autostart_enabled())
        tk.Checkbutton(opts, text="Iniciar con Windows y emular automaticamente", variable=self.auto,
                       command=self.toggle_autostart, font=F_UI, bg=BG, fg=CREAM, selectcolor=PANEL_HI,
                       activebackground=BG, activeforeground=NEON, disabledforeground="#56704e",
                       highlightthickness=0, bd=0,
                       state="normal" if getattr(sys, "frozen", False) else "disabled").pack(anchor="w")
        row = tk.Frame(opts, bg=BG)
        row.pack(anchor="w", pady=(6, 0))
        tk.Label(row, text="Al cerrar la ventana:", font=F_UI, fg=CREAM, bg=BG).pack(side="left", padx=(4, 8))
        self.close_var = tk.StringVar(value=CLOSE_OPTS[self.settings.get("on_close", "ask")])
        om = tk.OptionMenu(row, self.close_var, *CLOSE_OPTS.values(), command=self.set_close_pref)
        om.config(font=F_UI, bg=PANEL_HI, fg=CREAM, activebackground="#23422c", activeforeground=NEON,
                  highlightthickness=1, highlightbackground=BORDER, bd=0, relief="flat", indicatoron=True,
                  cursor="hand2")
        om["menu"].config(font=F_UI, bg=PANEL, fg=CREAM, activebackground=NEON_DK, activeforeground="white", bd=0)
        om.pack(side="left")

        # --- registro ---
        tk.Label(root, text="REGISTRO", font=("Bahnschrift SemiBold", 9), fg=MUTED, bg=BG).pack(
            anchor="w", padx=22, pady=(14, 2))
        logf = tk.Frame(root, bg=BORDER, padx=2, pady=2)
        logf.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        st = ttk.Style(root)
        st.theme_use("clam")
        st.configure("Bridge.Vertical.TScrollbar", background=PANEL_HI, troughcolor="#07100a", bordercolor="#07100a",
                     arrowcolor=MUTED, lightcolor=PANEL_HI, darkcolor=PANEL_HI, gripcount=0)
        st.map("Bridge.Vertical.TScrollbar", background=[("active", NEON_DK)], arrowcolor=[("active", NEON)])
        sb = ttk.Scrollbar(logf, orient="vertical", style="Bridge.Vertical.TScrollbar")
        sb.pack(side="right", fill="y")
        self.out = tk.Text(logf, height=10, font=F_LOG, state="disabled", bg="#07100a", fg="#9fd49a",
                           insertbackground=NEON, relief="flat", bd=0, padx=8, pady=6,
                           selectbackground=NEON_DK, yscrollcommand=sb.set)
        self.out.pack(side="left", fill="both", expand=True)
        sb.config(command=self.out.yview)
        self.out.tag_config("err", foreground=RED)

        xb.log = lambda *a: self.msgs.put(("log", " ".join(str(x) for x in a)))
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tray = pystray.Icon("XboxBridge", tray_image(None), "Xbox Bridge", pystray.Menu(
            pystray.MenuItem("Abrir", lambda: self.call(self.show), default=True),
            pystray.MenuItem(lambda _: "Detener emulacion" if self.mode == "emu" else "Emular",
                             lambda: self.call(self.toggle_emu),
                             enabled=lambda _: self.mode == "emu" or (self.mode is None and self.mapped())),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Donar ♥", lambda: webbrowser.open(DONATE_URL)),
            pystray.MenuItem("Salir", lambda: self.call(self.quit)),
        ))
        self.tray.run_detached()
        threading.Thread(target=self.instance_listener, args=(srv,), daemon=True).start()

        self.refresh()
        root.after(50, self.drain)

        if "--autostart" in sys.argv:
            root.withdraw()
            if self.mapped():
                self.toggle_emu()

    def call(self, fn):
        """Ejecuta fn en el hilo de Tk (pystray y el socket corren en otros hilos)."""
        self.msgs.put(("call", fn))

    def instance_listener(self, srv):
        while True:
            try:
                conn, _ = srv.accept()
                conn.close()
                self.call(self.show)
            except OSError:
                return

    # ---------- estado ----------
    def mapped(self):
        try:
            m = json.loads(xb.CFG.read_text())
            return bool(m.get("buttons")) and bool(m.get("axes"))
        except Exception:
            return False

    def refresh(self):
        busy = self.mode is not None
        if self.mode == "map":
            text, fg = "Mapeando... sigue las instrucciones", BLUE
        elif self.mode == "emu":
            text, fg = "Emulando Xbox 360", NEON
        elif self.mapped():
            text, fg = "Control mapeado. Listo para emular.", CREAM
        else:
            text, fg = "Control sin mapear. Presiona \"Mapear\".", RED
        self.status.config(text=text, fg=fg)
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 13, 13, fill=fg, outline="")
        if not busy:
            self.prompt.config(text="")

        mapped = self.mapped()
        self.btn_map.set(text="Cancelar" if self.mode == "map" else ("Re-mapear" if mapped else "Mapear"),
                         style="danger" if self.mode == "map" else "secondary",
                         enabled=self.mode != "emu")
        self.btn_emu.set(text="Detener" if self.mode == "emu" else "Emular",
                         style="danger" if self.mode == "emu" else "primary",
                         enabled=self.mode == "emu" or (not busy and mapped))

        self.tray.icon = tray_image(self.mode)
        self.tray.title = f"Xbox Bridge - {text}"
        self.tray.update_menu()

    def drain(self):
        try:
            while True:
                kind, val = self.msgs.get_nowait()
                if kind == "log":
                    self.write(val)
                    t = val.strip()
                    if t.startswith("Presiona:"):
                        self.prompt.config(text=t)
                    elif t.startswith(("Stick", "Gatillo", "==", "Esperando")):
                        self.prompt.config(text=t.strip("= "))
                elif kind == "error":
                    self.write("ERROR: " + val, "err")
                    if self.root.state() == "withdrawn":
                        self.tray.notify(val, "Xbox Bridge")
                    else:
                        self.dialog("Error", val, [("ok", "Aceptar", "secondary")])
                elif kind == "done":
                    self.mode = None
                    self.refresh()
                elif kind == "call":
                    val()
        except queue.Empty:
            pass
        self.root.after(50, self.drain)

    def write(self, text, tag=None):
        self.out.config(state="normal")
        self.out.insert("end", text + "\n", tag)
        self.out.see("end")
        self.out.config(state="disabled")

    # ---------- acciones ----------
    def start(self, mode, target):
        xb.stop.clear()
        self.mode = mode
        self.refresh()

        def run():
            try:
                target()
            except xb.Stopped:
                self.msgs.put(("log", "Cancelado."))
            except Exception as e:
                msg = str(e) or type(e).__name__
                if mode == "emu" and "ViGEm" in type(e).__name__ + msg:
                    msg += "\n\nInstala ViGEmBus: github.com/nefarius/ViGEmBus"
                self.msgs.put(("error", msg))
            finally:
                self.msgs.put(("done", ""))

        self.jobs.put(run)

    def pygame_thread(self):
        # SDL/DirectInput queda ligado al hilo que lo inicializa: todo el uso de pygame
        # (mapeo y emulacion) debe ocurrir siempre en este mismo hilo.
        while True:
            job = self.jobs.get()
            if job is None:
                return
            job()

    def toggle_map(self):
        if self.mode == "map":
            xb.stop.set()
        elif self.mode is None:
            self.start("map", xb.run_mapping)

    def toggle_emu(self):
        if self.mode == "emu":
            xb.stop.set()
        elif self.mode is None and self.mapped():
            self.start("emu", xb.run_bridge)

    def toggle_autostart(self):
        try:
            set_autostart(self.auto.get())
        except OSError as e:
            self.auto.set(autostart_enabled())
            self.dialog("Error", f"No se pudo cambiar el inicio automatico: {e}", [("ok", "Aceptar", "secondary")])

    def set_close_pref(self, label):
        self.settings["on_close"] = next(k for k, v in CLOSE_OPTS.items() if v == label)
        save_settings(self.settings)

    # ---------- ventana / cierre ----------
    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(200, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

    def hide(self):
        self.root.withdraw()
        if not self.settings.get("tray_hint_shown"):
            self.tray.notify("Sigue funcionando aqui. Clic derecho en el icono para salir.", "Xbox Bridge")
            self.settings["tray_hint_shown"] = True
            save_settings(self.settings)

    def on_close(self):
        pref = self.settings.get("on_close", "ask")
        if pref == "ask":
            pref, remember = self.dialog(
                "Que quieres hacer?",
                "En segundo plano el control sigue emulando\ny queda en la bandeja junto al reloj.",
                [("tray", "Segundo plano", "primary"), ("exit", "Cerrar", "danger"), ("cancel", "Cancelar", "secondary")],
                remember=True)
            if remember and pref != "cancel":
                self.settings["on_close"] = pref
                save_settings(self.settings)
                self.close_var.set(CLOSE_OPTS[pref])
        if pref == "tray":
            self.hide()
        elif pref == "exit":
            self.quit()

    def dialog(self, title, text, buttons, remember=False):
        """Dialogo modal con el estilo de la app. buttons: [(clave, texto, estilo)].
        Retorna la clave elegida, o (clave, recordar) si remember=True."""
        dlg = tk.Toplevel(self.root, bg=BG, highlightbackground=BORDER, highlightthickness=2)
        dlg.title("Xbox Bridge")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dark_titlebar(dlg)
        choice = tk.StringVar(value=buttons[-1][0])
        keep = tk.BooleanVar()

        tk.Label(dlg, text=title, font=F_STATUS, fg=CREAM, bg=BG).pack(padx=24, pady=(18, 6))
        tk.Label(dlg, text=text, font=F_UI, fg=MUTED, bg=BG, justify="center", wraplength=420).pack(padx=24)
        row = tk.Frame(dlg, bg=BG)
        row.pack(padx=18, pady=16)
        for key, label, style in buttons:
            RoundButton(row, label, lambda k=key: (choice.set(k), dlg.destroy()),
                        width=140, height=40, style=style).pack(side="left", padx=5)
        if remember:
            tk.Checkbutton(dlg, text="Recordar mi eleccion", variable=keep, font=F_UI, bg=BG, fg=CREAM,
                           selectcolor=PANEL_HI, activebackground=BG, activeforeground=NEON,
                           highlightthickness=0, bd=0).pack(pady=(0, 14))

        dlg.update_idletasks()
        if self.root.state() != "withdrawn":
            x = self.root.winfo_rootx() + (self.root.winfo_width() - dlg.winfo_width()) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - dlg.winfo_height()) // 3
            dlg.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dlg.grab_set()
        self.root.wait_window(dlg)
        return (choice.get(), keep.get()) if remember else choice.get()

    def quit(self):
        xb.stop.set()
        self.jobs.put(None)
        self.worker.join(timeout=1.5)  # deja que run_bridge suelte el pad virtual
        self.tray.stop()
        self.root.destroy()


if __name__ == "__main__":
    srv = claim_instance()
    if srv is None:
        sys.exit(0)
    root = tk.Tk()
    App(root, srv)
    root.mainloop()
