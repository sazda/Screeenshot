"""
Windows deo programa Screenshot:
  - pronalaženje prozora ispod kursora (izbor prozora mišem)
  - dodavanje snimka kao priloga u Outlook poruku (klasični Outlook, COM)
  - kopiranje snimka u clipboard kao fajla (Ctrl+V u poruci = prilog)

Na drugim sistemima is_supported() vraća False i program ove opcije ne nudi.
"""

import os
import struct
import sys

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:  # pragma: no cover - izvršava se samo na Windows-u
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    dwmapi = ctypes.WinDLL("dwmapi")

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    dwmapi.DwmGetWindowAttribute.argtypes = [
        wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]

CF_HDROP = 15
GMEM_MOVEABLE = 0x0002
DROPEFFECT_COPY = 1
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
DWMWA_EXTENDED_FRAME_BOUNDS = 9
DWMWA_CLOAKED = 14


class OutlookError(Exception):
    """Greška sa porukom spremnom za prikaz korisniku."""


def is_supported():
    return IS_WINDOWS


# ---------------------------------------------------------------- prozori

def _window_rect(hwnd):
    """Vidljive ivice prozora (bez nevidljive senke koju Windows 10/11 dodaje)."""
    rect = wintypes.RECT()
    if dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS,
                                    ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def _is_cloaked(hwnd):
    # „Skriveni“ prozori (npr. aplikacije na drugoj virtuelnoj radnoj površini)
    cloaked = wintypes.DWORD()
    dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked),
                                 ctypes.sizeof(cloaked))
    return cloaked.value != 0


def window_title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def process_name(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value)
        return ""
    finally:
        kernel32.CloseHandle(h)


def window_at(x, y):
    """Najviši vidljivi prozor (drugog programa) koji sadrži tačku (x, y).
    Vraća (hwnd, (left, top, right, bottom)) ili (None, None).
    Prozori ovog programa se preskaču, pa sloj za izbor ne smeta."""
    own_pid = os.getpid()
    found = []

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == own_pid or _is_cloaked(hwnd):
            return True
        l, t, r, b = _window_rect(hwnd)
        if r - l < 2 or b - t < 2:
            return True
        if l <= x < r and t <= y < b:
            found.append((hwnd, (l, t, r, b)))
            return False  # EnumWindows ide od najvišeg ka najnižem – prvi pogodak je pravi
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return found[0] if found else (None, None)


# ---------------------------------------------------------------- Outlook

def _com_hwnd(obj):
    """Windows identifikator prozora Outlook Inspector/Explorer objekta."""
    try:
        import pythoncom

        ole = obj._oleobj_.QueryInterface(pythoncom.IID_IOleWindow)
        return int(ole.GetWindow())
    except Exception:
        return None


def _matches(obj, hwnd, title):
    h = _com_hwnd(obj)
    if h is not None:
        return h == hwnd
    try:  # rezervno: poređenje naslova prozora
        return bool(title) and obj.Caption == title
    except Exception:
        return False


def _get_outlook():
    try:
        import win32com.client
    except ImportError as exc:
        raise OutlookError("Nedostaje biblioteka pywin32.") from exc
    try:
        # Samo već pokrenut Outlook – program ga nikad sam ne pokreće
        return win32com.client.GetActiveObject("Outlook.Application")
    except Exception as exc:
        raise OutlookError(
            "Ne mogu da se povežem sa Outlook-om.\n"
            "Proverite da li je klasični Outlook otvoren. Ako je pokrenut kao "
            "administrator, pokrenite ga normalno.") from exc


def _is_received(item):
    try:
        return bool(item.Sent)
    except Exception:
        return False


def _attach(item, path):
    try:
        item.Attachments.Add(os.path.abspath(path))
    except Exception as exc:
        raise OutlookError(f"Outlook nije dozvolio dodavanje priloga:\n{exc}") from exc
    try:
        return item.Subject or "(bez naslova)"
    except Exception:
        return "(bez naslova)"


NOT_REPLY_MSG = ("Ovo je primljena poruka.\n"
                 "Prvo kliknite „Odgovori“ ili „Odgovori svima“, "
                 "pa ponovo izaberite prozor.")


def attach_to_window(hwnd, path, app=None, title=None):
    """Dodaje fajl kao prilog u Outlook poruku iz prozora hwnd.
    Vraća naslov poruke; u slučaju problema baca OutlookError."""
    if app is None:
        if IS_WINDOWS and process_name(hwnd).lower() != "outlook.exe":
            raise OutlookError("Izabrani prozor nije Outlook.\n"
                               "Kliknite na prozor sa započetim odgovorom.")
        app = _get_outlook()
    if title is None and IS_WINDOWS:
        title = window_title(hwnd)

    # 1) Poruka u posebnom prozoru
    for i in range(1, app.Inspectors.Count + 1):
        insp = app.Inspectors.Item(i)
        if _matches(insp, hwnd, title):
            item = insp.CurrentItem
            if _is_received(item):
                raise OutlookError(NOT_REPLY_MSG)
            subject = _attach(item, path)
            _activate(insp)
            return subject

    # 2) Glavni Outlook prozor – odgovor započet u oknu za čitanje
    for i in range(1, app.Explorers.Count + 1):
        exp = app.Explorers.Item(i)
        if _matches(exp, hwnd, title):
            try:
                item = exp.ActiveInlineResponse
            except Exception:
                item = None
            if item is None:
                raise OutlookError(
                    "U glavnom Outlook prozoru nema započetog odgovora.\n"
                    "Kliknite „Odgovori“ ili „Odgovori svima“, pa ponovo izaberite prozor.")
            subject = _attach(item, path)
            _activate(exp)
            return subject

    raise OutlookError("Ne mogu da pronađem Outlook poruku u izabranom prozoru.\n"
                       "Kliknite na prozor sa započetim odgovorom.")


def _activate(obj):
    try:
        obj.Activate()
    except Exception:
        pass


# ---------------------------------------------------------------- clipboard

def build_dropfiles(paths):
    """Sadržaj CF_HDROP formata: DROPFILES zaglavlje + putanje (UTF-16),
    svaka završena nulom, a lista dodatnom nulom."""
    header = struct.pack("<IiiII", 20, 0, 0, 0, 1)  # pFiles=20, pt=(0,0), fNC=0, fWide=1
    body = "".join(os.path.abspath(p) + "\0" for p in paths) + "\0"
    return header + body.encode("utf-16-le")


def _set_clipboard_bytes(fmt, data):
    h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not h:
        raise OSError("GlobalAlloc nije uspeo")
    ptr = kernel32.GlobalLock(h)
    ctypes.memmove(ptr, data, len(data))
    kernel32.GlobalUnlock(h)
    if not user32.SetClipboardData(fmt, h):
        kernel32.GlobalFree(h)  # clipboard nije preuzeo memoriju
        raise OSError("SetClipboardData nije uspeo")


def copy_file_to_clipboard(path):
    """Stavlja fajl u clipboard kao „kopirani fajl“ (kao Ctrl+C u Explorer-u).
    Ctrl+V u Outlook poruci ga dodaje kao prilog."""
    if not IS_WINDOWS:
        raise OSError("Dostupno samo na Windows-u.")
    for _ in range(10):  # clipboard je možda trenutno zauzet drugim programom
        if user32.OpenClipboard(None):
            break
        kernel32.Sleep(50)
    else:
        raise OSError("Clipboard je zauzet. Pokušajte ponovo.")
    try:
        user32.EmptyClipboard()
        _set_clipboard_bytes(CF_HDROP, build_dropfiles([path]))
        effect = user32.RegisterClipboardFormatW("Preferred DropEffect")
        _set_clipboard_bytes(effect, struct.pack("<I", DROPEFFECT_COPY))
    finally:
        user32.CloseClipboard()
