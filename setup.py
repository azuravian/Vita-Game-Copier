from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
includefiles = ['cat512_54h_icon.ico', 'README.md']

build_options = {'packages': [], 'excludes': [], 'include_files':includefiles}

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('I:\\dev\\Vita\\VitaGameCopier\\vitagamecopier.py', base=base, target_name = 'vgc.exe', icon = 'cat512_54h_icon.ico')
]

setup(name='Vita Game Copier',
      version = '1.0 Beta',
      description = 'Simplify copying Vita games from PC to SD2Vita',
      options = {'build_exe': build_options},
      executables = executables)
