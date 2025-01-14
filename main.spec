# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Projects\\hc_electron_eel\\.venv\\Lib\\site-packages\\eel\\eel.js', 'eel'), ('web', 'web'), ('web', 'electron/resources/app/web'), ('electron', 'electron'), ('main.js', 'electron/resources/app'),  ('preload.js', 'electron/resources/app'), ('package.json', 'electron/resources/app')],
    hiddenimports=['bottle_websocket', 'bottle_websocket'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('v', None, 'OPTION')],
    name='ulendohc_tool',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
