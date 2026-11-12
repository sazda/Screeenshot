"""
Pravljenje Windows MSI instalera (cx_Freeze).

Pokretanje (samo na Windows-u):
    pip install -r requirements-build.txt
    python setup.py bdist_msi

Gotov instaler se nalazi u folderu dist/.
"""

import re
import sys
from pathlib import Path

from cx_Freeze import Executable, setup

HERE = Path(__file__).parent
SOURCE = (HERE / "screenshot.py").read_text(encoding="utf-8")


def _const(name):
    return re.search(rf'^{name}\s*=\s*"([^"]+)"', SOURCE, re.M).group(1)


APP_NAME = _const("APP_NAME")
VERSION = _const("APP_VERSION")  # jedino mesto gde se menja verzija
AUTHOR = _const("AUTHOR")

# NE MENJATI! Po ovom kodu Windows prepoznaje da je nova verzija
# nadogradnja postojeće i automatski uklanja staru pri instalaciji.
UPGRADE_CODE = "{45C465BA-D486-47AA-ABF5-D123401B200A}"

build_exe_options = {
    "packages": ["mss", "PIL", "tkinter"],
    "excludes": ["unittest", "pydoc_data", "test"],
    "include_msvcr": True,
    "include_files": [("LICENSE", "LICENSE.txt"), ("assets", "assets")],
}

bdist_msi_options = {
    "upgrade_code": UPGRADE_CODE,
    "add_to_path": False,
    "install_icon": "assets/icon.ico",  # ikonica u „Programs and Features“
    "all_users": True,
    "initial_target_dir": rf"[ProgramFiles64Folder]\{APP_NAME}",
    "summary_data": {
        "author": AUTHOR,
        "comments": "Program za snimanje ekrana",
    },
}

executables = [
    Executable(
        "screenshot.py",
        base="gui" if sys.platform == "win32" else None,
        target_name="ScreenshotAlat",
        icon="assets/icon.ico",
        shortcut_name=APP_NAME,
        shortcut_dir="ProgramMenuFolder",
        copyright=f"© {AUTHOR}",
    )
]

setup(
    name=APP_NAME,
    version=VERSION,
    author=AUTHOR,
    description="Program za snimanje ekrana",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
