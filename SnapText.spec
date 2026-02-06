# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('LocalOCR/resources', 'resources')]
datas += collect_data_files('rapidocr_onnxruntime')


a = Analysis(
    ['LocalOCR/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['rapidocr_onnxruntime', 'onnxruntime', 'PIL', 'flask', 'werkzeug', 'rumps', 'AppKit', 'Foundation', 'webview', 'webview.platforms.cocoa', 'ApplicationServices'],
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
    [],
    exclude_binaries=True,
    name='SnapText',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['LocalOCR/resources/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SnapText',
)
app = BUNDLE(
    coll,
    name='SnapText.app',
    icon='LocalOCR/resources/icon.icns',
    bundle_identifier='com.snaptext.ocr',
    info_plist={
        'LSUIElement': '1',
        'CFBundleName': 'SnapText',
        'CFBundleDisplayName': 'SnapText',
        'CFBundleGetInfoString': "SnapText OCR Tool",
        'CFBundleIdentifier': "com.snaptext.ocr",
        'CFBundleVersion': "1.0.2",
        'CFBundleShortVersionString': "1.0.2",
        'NSHighResolutionCapable': True,
    },
)
