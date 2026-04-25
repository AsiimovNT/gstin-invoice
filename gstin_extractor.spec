# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — GST Invoice Extractor
"""

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    copy_metadata,   # ✅ ADDED
)

# ── Locate package paths ──────────────────────────────────────────────────────
import streamlit as _st
STREAMLIT_PATH = Path(_st.__file__).parent

import altair as _alt
ALTAIR_PATH = Path(_alt.__file__).parent

# ── Data files to bundle ──────────────────────────────────────────────────────
datas = [
    ("app.py", "."),
    ("extractor.py", "."),
    ("excel_writer.py", "."),

    (str(STREAMLIT_PATH / "static"),     "streamlit/static"),
    (str(STREAMLIT_PATH / "runtime"),    "streamlit/runtime"),
    (str(STREAMLIT_PATH / "components"), "streamlit/components"),
    (str(STREAMLIT_PATH / "web"),        "streamlit/web"),

    (str(ALTAIR_PATH / "vegalite"),  "altair/vegalite"),
    (str(ALTAIR_PATH / "utils"),     "altair/utils"),
]

# Existing data collection
datas += collect_data_files("streamlit")
datas += collect_data_files("altair")
datas += collect_data_files("pdfminer")
datas += collect_data_files("openpyxl")
datas += collect_data_files("pandas")

# ✅ ADD THIS BLOCK (CRITICAL FIX)
datas += copy_metadata("streamlit")
datas += copy_metadata("altair")
datas += copy_metadata("pandas")
datas += copy_metadata("openpyxl")

# ── Hidden imports ────────────────────────────────────────────────────────────
hiddenimports = [
    "streamlit", "streamlit.web.cli", "streamlit.web.server",
    "streamlit.web.server.server", "streamlit.runtime",
    "streamlit.runtime.scriptrunner", "streamlit.runtime.state",
    "streamlit.components.v1", "streamlit.elements",
    "altair", "altair.vegalite.v5",
    "pandas",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.tslibs.timedeltas",
    "numpy",
    "pdfplumber", "pdfminer", "pdfminer.high_level",
    "pdfminer.layout", "pdfminer.converter", "pdfminer.pdfinterp",
    "pdfminer.pdfdevice", "pdfminer.pdfpage", "pdfminer.pdfdocument",
    "openpyxl", "openpyxl.styles", "openpyxl.utils", "openpyxl.workbook",
    "PIL", "PIL.Image",
    "click", "toml", "typing_extensions",
    "importlib_metadata", "packaging", "attr",
    "jsonschema", "pyarrow", "pyarrow.lib", "tzdata",
]

hiddenimports += collect_submodules("streamlit")
hiddenimports += collect_submodules("altair")
hiddenimports += collect_submodules("pdfminer")

# ── Analysis ──────────────────────────────────────────────────────────────────
block_cipher = None

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "scipy", "sklearn", "tensorflow", "torch",
        "cv2", "tkinter", "PyQt5", "PyQt6", "wx",
        "IPython", "jupyter", "notebook",
        "test", "tests", "unittest",
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GST Invoice Extractor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GST Invoice Extractor",
)

# ── macOS bundle ──────────────────────────────────────────────────────────────
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="GST Invoice Extractor.app",
        icon=None,
        bundle_identifier="com.gopaljee.gstin-extractor",
        info_plist={
            "CFBundleName":               "GST Invoice Extractor",
            "CFBundleDisplayName":        "GST Invoice Extractor",
            "CFBundleVersion":            "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable":    True,
            "LSUIElement":                False,
            "NSRequiresAquaSystemAppearance": False,
        },
    )