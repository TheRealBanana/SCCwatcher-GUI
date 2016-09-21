# -*- mode: python -*-
from os import getcwd
_CURDIR = getcwd()

a = Analysis(['sccwatcher.pyw'],
             pathex=[_CURDIR],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='sccwatcher_gui.exe',
          debug=False,
          strip=None,
          upx=False,
          console=False,
          icon='../ui_files/icons/logo.ico')
