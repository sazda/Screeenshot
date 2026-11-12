"""
Screenshot alat
Izradio: Aleksandar Sazdanović

Mogućnosti:
  - izbor monitora (ako je povezano više monitora) ili svih monitora zajedno
  - snimanje celog ekrana ili izabranog dela (prevlačenjem miša)
  - čuvanje u formatu PNG, JPG, JPEG ili PDF
"""

import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

try:
    import mss
    from PIL import Image, ImageTk
except ImportError as exc:  # pragma: no cover
    print("Nedostaje biblioteka:", exc)
    print("Instalirajte zavisnosti komandom:  pip install -r requirements.txt")
    sys.exit(1)

APP_NAME = "Screenshot alat"
APP_VERSION = "1.0.0"
AUTHOR = "Aleksandar Sazdanović"

FORMATS = {
    "PNG": (".png", "PNG"),
    "JPG": (".jpg", "JPEG"),
    "JPEG": (".jpeg", "JPEG"),
    "PDF": (".pdf", "PDF"),
}


def enable_dpi_awareness():
    """Na Windows-u sa skaliranjem (125%, 150%...) bez ovoga koordinate
    prozora i stvarni pikseli ekrana se ne poklapaju."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def list_monitors():
    """Vraća listu (naziv, monitor_dict). Indeks 0 u mss-u su svi monitori."""
    with mss.mss() as sct:
        mons = sct.monitors
    result = []
    for i, m in enumerate(mons[1:], start=1):
        label = f"Monitor {i}  ({m['width']}x{m['height']}, pozicija {m['left']},{m['top']})"
        if i == 1:
            label += "  [primarni]"
        result.append((label, m))
    if len(mons) > 2:
        m = mons[0]
        result.append((f"Svi monitori  ({m['width']}x{m['height']})", m))
    return result


def grab(monitor):
    with mss.mss() as sct:
        shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def save_image(img, path, fmt_key):
    _, pil_format = FORMATS[fmt_key]
    img = img.convert("RGB")
    if pil_format == "JPEG":
        img.save(path, pil_format, quality=95, optimize=True)
    elif pil_format == "PDF":
        img.save(path, pil_format, resolution=96.0)
    else:
        img.save(path, pil_format, optimize=True)


class RegionSelector(tk.Toplevel):
    """Prikazuje snimak monitora preko celog tog monitora i pušta korisnika
    da mišem označi pravougaonik. Rezultat je isečena slika ili None."""

    def __init__(self, master, image, monitor):
        super().__init__(master)
        self.image = image
        self.result = None
        self.start = None
        self.rect = None

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry(
            f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}"
        )

        self.canvas = tk.Canvas(self, cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Zatamnjena pozadina da bi označeni deo bio jasno vidljiv
        dim = Image.blend(image, Image.new("RGB", image.size, "black"), 0.35)
        self.bg = ImageTk.PhotoImage(dim)
        self.full = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self.bg, anchor="nw")
        self.canvas.create_text(
            20, 20, anchor="nw", fill="white", font=("Segoe UI", 14, "bold"),
            text="Prevucite mišem preko dela ekrana  •  Esc = otkaži",
        )
        self.crop_id = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.close())
        self.bind("<ButtonPress-3>", lambda e: self.close())

        self.after(50, self._grab_focus)

    def _grab_focus(self):
        self.lift()
        self.focus_force()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def on_press(self, e):
        self.start = (e.x, e.y)

    def on_drag(self, e):
        if not self.start:
            return
        x0, y0 = self.start
        x1, y1 = e.x, e.y
        l, t, r, b = min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
        if self.rect:
            self.canvas.delete(self.rect)
        if self.crop_id:
            self.canvas.delete(self.crop_id)
        if r - l > 0 and b - t > 0:
            # nezatamnjen prikaz označenog dela
            self._crop_photo = ImageTk.PhotoImage(self.image.crop((l, t, r, b)))
            self.crop_id = self.canvas.create_image(l, t, image=self._crop_photo, anchor="nw")
        self.rect = self.canvas.create_rectangle(l, t, r, b, outline="#00a2ff", width=2)

    def on_release(self, e):
        if not self.start:
            return
        x0, y0 = self.start
        l, t, r, b = min(x0, e.x), min(y0, e.y), max(x0, e.x), max(y0, e.y)
        w, h = self.image.size
        l, t = max(0, l), max(0, t)
        r, b = min(w, r), min(h, b)
        if r - l < 3 or b - t < 3:
            # premali izbor — verovatno slučajan klik, pokušaj ponovo
            self.start = None
            return
        self.result = self.image.crop((l, t, r, b))
        self.close()

    def close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.resizable(False, False)

        self.monitors = []
        self.monitor_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="full")
        self.format_var = tk.StringVar(value="PNG")
        self.delay_var = tk.IntVar(value=0)
        self.ask_var = tk.BooleanVar(value=True)
        self.folder_var = tk.StringVar(value=self._default_folder())

        self._build_menu()
        self._build_ui()
        self.refresh_monitors()

    @staticmethod
    def _default_folder():
        pics = os.path.join(os.path.expanduser("~"), "Pictures")
        return pics if os.path.isdir(pics) else os.path.expanduser("~")

    # ---------- UI ----------
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Snimi", accelerator="Ctrl+S", command=self.take)
        file_menu.add_separator()
        file_menu.add_command(label="Izlaz", command=self.destroy)
        menubar.add_cascade(label="Fajl", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="O programu", command=self.about)
        menubar.add_cascade(label="Pomoć", menu=help_menu)
        self.config(menu=menubar)
        self.bind("<Control-s>", lambda e: self.take())

    def _build_ui(self):
        pad = {"padx": 10, "pady": 5}
        root = ttk.Frame(self, padding=10)
        root.grid(sticky="nsew")

        # Monitor
        f_mon = ttk.LabelFrame(root, text="Ekran", padding=8)
        f_mon.grid(row=0, column=0, sticky="ew", **pad)
        self.monitor_combo = ttk.Combobox(
            f_mon, textvariable=self.monitor_var, state="readonly", width=48
        )
        self.monitor_combo.grid(row=0, column=0, sticky="ew")
        ttk.Button(f_mon, text="Osveži", command=self.refresh_monitors).grid(
            row=0, column=1, padx=(6, 0)
        )

        # Oblast
        f_mode = ttk.LabelFrame(root, text="Oblast snimanja", padding=8)
        f_mode.grid(row=1, column=0, sticky="ew", **pad)
        ttk.Radiobutton(f_mode, text="Ceo ekran", value="full",
                        variable=self.mode_var).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(f_mode, text="Deo ekrana (označi mišem)", value="region",
                        variable=self.mode_var).grid(row=0, column=1, sticky="w", padx=(20, 0))

        # Format i opcije
        f_fmt = ttk.LabelFrame(root, text="Čuvanje", padding=8)
        f_fmt.grid(row=2, column=0, sticky="ew", **pad)
        ttk.Label(f_fmt, text="Format:").grid(row=0, column=0, sticky="w")
        for i, key in enumerate(FORMATS):
            ttk.Radiobutton(f_fmt, text=key, value=key, variable=self.format_var).grid(
                row=0, column=1 + i, sticky="w", padx=(8, 0)
            )

        ttk.Label(f_fmt, text="Kašnjenje (s):").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(f_fmt, from_=0, to=30, width=5, textvariable=self.delay_var).grid(
            row=1, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 0)
        )

        ttk.Checkbutton(f_fmt, text="Pitaj gde da sačuvam", variable=self.ask_var,
                        command=self._toggle_folder).grid(
            row=2, column=0, columnspan=5, sticky="w", pady=(8, 0)
        )
        ttk.Label(f_fmt, text="Folder:").grid(row=3, column=0, sticky="w", pady=(4, 0))
        self.folder_entry = ttk.Entry(f_fmt, textvariable=self.folder_var, width=36)
        self.folder_entry.grid(row=3, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(4, 0))
        self.folder_btn = ttk.Button(f_fmt, text="...", width=3, command=self.choose_folder)
        self.folder_btn.grid(row=3, column=4, sticky="w", padx=(4, 0), pady=(4, 0))
        self._toggle_folder()

        ttk.Button(root, text="📷  Snimi ekran", command=self.take).grid(
            row=3, column=0, sticky="ew", padx=10, pady=(10, 5), ipady=6
        )
        self.status = ttk.Label(root, text="", foreground="#555")
        self.status.grid(row=4, column=0, sticky="w", padx=10)

    def _toggle_folder(self):
        state = "disabled" if self.ask_var.get() else "normal"
        self.folder_entry.configure(state=state)
        self.folder_btn.configure(state=state)

    # ---------- akcije ----------
    def refresh_monitors(self):
        try:
            self.monitors = list_monitors()
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Ne mogu da pročitam monitore:\n{exc}")
            self.monitors = []
        labels = [m[0] for m in self.monitors]
        self.monitor_combo["values"] = labels
        if labels and self.monitor_var.get() not in labels:
            self.monitor_var.set(labels[0])
        self.monitor_combo.configure(state="readonly" if len(labels) > 1 else "disabled")
        self.status.configure(text=f"Pronađeno monitora: {sum(1 for l in labels if l.startswith('Monitor'))}")

    def choose_folder(self):
        d = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~"))
        if d:
            self.folder_var.set(d)

    def _selected_monitor(self):
        label = self.monitor_var.get()
        for l, m in self.monitors:
            if l == label:
                return m
        return self.monitors[0][1] if self.monitors else None

    def take(self):
        monitor = self._selected_monitor()
        if monitor is None:
            messagebox.showerror(APP_NAME, "Nije pronađen nijedan monitor.")
            return
        try:
            delay = max(0, int(self.delay_var.get()))
        except (tk.TclError, ValueError):
            delay = 0

        # Sakrij prozor da ne bi bio na snimku
        self.withdraw()
        self.update()
        self.after(max(250, delay * 1000), lambda: self._capture(monitor))

    def _capture(self, monitor):
        try:
            img = grab(monitor)
        except Exception as exc:
            self.deiconify()
            messagebox.showerror(APP_NAME, f"Snimanje nije uspelo:\n{exc}")
            return

        if self.mode_var.get() == "region":
            selector = RegionSelector(self, img, monitor)
            self.wait_window(selector)
            img = selector.result
            if img is None:
                self.deiconify()
                self.status.configure(text="Snimanje otkazano.")
                return

        self.deiconify()
        self.lift()
        self._save(img)

    def _save(self, img):
        fmt = self.format_var.get()
        ext, _ = FORMATS[fmt]
        name = "screenshot_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ext

        if self.ask_var.get():
            path = filedialog.asksaveasfilename(
                title="Sačuvaj snimak",
                initialdir=self.folder_var.get(),
                initialfile=name,
                defaultextension=ext,
                filetypes=[(f"{fmt} fajl", "*" + ext), ("Svi fajlovi", "*.*")],
            )
            if not path:
                self.status.configure(text="Čuvanje otkazano.")
                return
            if not os.path.splitext(path)[1]:
                path += ext
            self.folder_var.set(os.path.dirname(path))
        else:
            folder = self.folder_var.get()
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, name)

        try:
            save_image(img, path, fmt)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Čuvanje nije uspelo:\n{exc}")
            return
        self.status.configure(text=f"Sačuvano: {path}  ({img.width}x{img.height})")

    def about(self):
        messagebox.showinfo(
            "O programu",
            f"{APP_NAME}  v{APP_VERSION}\n\n"
            "Program za snimanje ekrana (screenshot).\n"
            "Izbor monitora, celog ekrana ili dela ekrana,\n"
            "čuvanje u PNG, JPG, JPEG ili PDF formatu.\n\n"
            f"Izradio: {AUTHOR}",
        )


def main():
    enable_dpi_awareness()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
