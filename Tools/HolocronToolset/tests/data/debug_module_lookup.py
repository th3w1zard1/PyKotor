"""Debug module lookup."""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "PyKotor" / "src"))

from pykotor.extract.installation import Installation

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)

rims_path = inst.rims_path()
modules_path = inst.module_path()

print(f"rims_path: {rims_path}")
print(f"modules_path: {modules_path}")
print(f"rims_path.exists(): {rims_path.exists() if rims_path else False}")
print(f"modules_path.exists(): {modules_path.exists() if modules_path else False}")

test_modules = ["tar_m03aa", "tar_m03ab", "end_m01aa", "danm14aa", "danm15"]
for mod_name in test_modules:
    main_rim_rims = rims_path / f"{mod_name}.rim" if rims_path.exists() else None
    main_rim_modules = modules_path / f"{mod_name}.rim" if modules_path.exists() else None
    print(f"\n{mod_name}:")
    print(f"  rims: {main_rim_rims} exists={main_rim_rims.exists() if main_rim_rims else False}")
    print(f"  modules: {main_rim_modules} exists={main_rim_modules.exists() if main_rim_modules else False}")
    # Test the exact logic from _find_module_for_kit
    main_rim = (rims_path / f"{mod_name}.rim" if rims_path.exists() else None) or (modules_path / f"{mod_name}.rim" if modules_path.exists() else None)
    print(f"  combined result: {main_rim} exists={main_rim.exists() if main_rim else False}")

