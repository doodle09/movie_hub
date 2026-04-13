# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MovieHub Desktop Application.

Build command:
    pyinstaller moviehub.spec

This produces a one-folder bundle in dist/MovieHub/ containing the
executable and all required data files (database, vector store, configs).
"""

import os
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = os.path.abspath('.')

# ── Data files to bundle alongside the exe ──────────────────────────
# Format: (source_path, destination_folder_relative_to_exe)
datas = [
    # Pre-built SQLite database
    (os.path.join(PROJECT_ROOT, 'movie_discovery.db'), '.'),
    # ChromaDB vector store
    (os.path.join(PROJECT_ROOT, 'embeddings', 'chroma_db'), os.path.join('embeddings', 'chroma_db')),
    # API keys config
    (os.path.join(PROJECT_ROOT, 'configs', 'api_keys.json'), 'configs'),
    # .env file (if present)
]

# Only include .env if it exists
env_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_path):
    datas.append((env_path, '.'))

# ── Hidden imports that PyInstaller might miss ──────────────────────
hiddenimports = [
    'chromadb',
    'chromadb.api',
    'chromadb.api.segment',
    'chromadb.config',
    'chromadb.db',
    'chromadb.db.impl',
    'chromadb.db.impl.sqlite',
    'chromadb.segment',
    'chromadb.segment.impl',
    'chromadb.telemetry',
    'chromadb.utils.embedding_functions',
    'sentence_transformers',
    'torch',
    'transformers',
    'tokenizers',
    'numpy',
    'pandas',
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_qt5agg',
    'PIL',
    'google.generativeai',
    'google.ai.generativelanguage',
    'google.api_core',
    'google.auth',
    'sqlite3',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'dotenv',
]

a = Analysis(
    ['desktop_app.py'],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',       # Not needed — we use PyQt6
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,     # one-folder mode (keeps size manageable)
    name='MovieHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,             # No terminal window — pure GUI
    icon=None,                 # Add an .ico file path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MovieHub',
)
