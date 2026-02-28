# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

try:
    # Provided by PyInstaller when executing the .spec file.
    spec_dir = Path(SPECPATH).resolve()
except NameError:
    # Fallback for direct execution in unusual contexts.
    spec_dir = Path.cwd() / "build_tools"

project_dir = spec_dir.parent
icon_path = project_dir / "assets" / "icons" / "xsd_app_icon.ico"
entrypoint = project_dir / "main.py"

a = Analysis(
    [str(entrypoint)],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[(str(icon_path), 'assets/icons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='XSDManager',
    debug=False,
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
    icon=[str(icon_path)],
)
