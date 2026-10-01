# Prototype Windows onedir. Aucune collecte de la racine du dépôt ou de data/.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

root = Path(SPECPATH)
datas = collect_data_files('docx')
binaries = collect_dynamic_libs('pymupdf')
hiddenimports = ['docx', 'lxml.etree', 'PIL.ImageTk', 'win32com.client',
                 'pythoncom', 'pywintypes', 'openpyxl']
a = Analysis([str(root / 'scripts/windows_launcher.py')], pathex=[str(root)],
             binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             hookspath=[], runtime_hooks=[],
             excludes=['pytest', 'tests', 'unittest', 'IPython', 'matplotlib', 'numpy'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ComptaPriveeAI',
          debug=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ComptaPriveeAI')
