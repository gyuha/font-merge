# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# 프로젝트 루트 디렉토리 (spec 파일의 현재 디렉토리)
project_root = Path(os.getcwd()).absolute()

# 아이콘 파일 경로
icon_path = project_root / 'icon.icns'

a = Analysis(
    ['src/font_merge/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src/font_merge', 'font_merge'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'fontTools',
        'fontTools.ttLib',
        'fontTools.subset',
        'fontTools.merge',
        'fontTools.feaLib',
        'fontTools.otlLib',
        'fontTools.varLib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FontMerge',
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
    icon=str(icon_path) if icon_path.exists() else None,
)

app = BUNDLE(
    exe,
    name='FontMerge.app',
    icon=str(icon_path) if icon_path.exists() else None,
    bundle_identifier='com.fontmerge.app',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'Font Merge',
        'CFBundleDisplayName': 'Font Merge',
        'CFBundleIdentifier': 'com.fontmerge.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'FMRG',
        'CFBundleExecutable': 'FontMerge',
        'CFBundleIconFile': 'icon.icns',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'TrueType Font',
                'CFBundleTypeExtensions': ['ttf'],
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['public.truetype-ttf-font']
            },
            {
                'CFBundleTypeName': 'OpenType Font',
                'CFBundleTypeExtensions': ['otf'],
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['public.opentype-font']
            }
        ]
    },
)