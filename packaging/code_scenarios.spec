# PyInstaller spec — lean runtime bundle (no tests, plans, or dev scripts).
# Build: pyinstaller packaging/code_scenarios.spec --noconfirm

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

root = Path(SPECPATH).resolve().parent
launcher = root / "packaging" / "launcher_gui.py"

scenario_ids = ("resource_wars", "boss_fight", "energy_stations")

datas = [
    (str(root / "configs"), "configs"),
    (str(root / "student_bots"), "student_bots"),
    (str(root / "ui" / "assets"), "ui/assets"),
]
for scenario_id in scenario_ids:
    toml = root / "scenarios" / scenario_id / "scenario.toml"
    datas.append((str(toml), f"scenarios/{scenario_id}"))

ruff_exe = Path(sys.executable).with_name("ruff.exe")
if ruff_exe.is_file():
    datas.append((str(ruff_exe), "."))

radon_datas, radon_binaries, radon_hiddenimports = collect_all("radon")

hiddenimports = (
    collect_submodules("engine")
    + collect_submodules("scenarios")
    + collect_submodules("ui")
    + collect_submodules("ai")
    + radon_hiddenimports
)

datas += radon_datas
binaries = radon_binaries

a = Analysis(
    [str(launcher)],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "rich",
        "tests",
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
    exclude_binaries=True,
    name="CodeScenarios",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CodeScenarios",
)
