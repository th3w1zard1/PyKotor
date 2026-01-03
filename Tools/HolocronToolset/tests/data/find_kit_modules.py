"""Find the correct module name for each kit."""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "PyKotor" / "src"))

from pykotor.extract.installation import Installation

# Kit name to area name mapping (from kit JSON files)
KIT_TO_AREA = {
    "blackvulkar": "Black Vulkar",
    "dantooineestate": "Dantooine Estate",
    "davikestate": "Davik Estate",
    "enclavesurface": "Enclave Surface",
    "endarspire": "Endar Spire",
    "hiddenbek": "Hidden Bek",
    "jedienclave": "Jedi Enclave",
    "sithbase": "Sith Base",
    "tarissewers": "Taris Sewers",
}

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)

# Get all modules and their area names
module_names = inst.module_names()
modules_list = inst.modules_list()

# Build a map of module roots to area names
module_roots_to_areas = {}
for module_file, area_name in module_names.items():
    module_root = inst.get_module_root(module_file)
    if module_root and module_root not in module_roots_to_areas:
        module_roots_to_areas[module_root] = area_name

print("All modules with area names:")
print("=" * 80)
for module_root, area_name in sorted(module_roots_to_areas.items()):
    print(f"{module_root:20s} -> {area_name or 'N/A'}")
print()

print("Finding modules for each kit:")
print("=" * 80)

kit_to_module = {}

for kit_id, area_name in KIT_TO_AREA.items():
    found_module = None
    
    # Try exact area name match first
    for module_root, module_area_name in module_roots_to_areas.items():
        if module_area_name and area_name.lower() == module_area_name.lower():
            found_module = module_root
            break
    
    # Try partial area name match
    if not found_module:
        for module_root, module_area_name in module_roots_to_areas.items():
            if module_area_name:
                # Check if kit area name is in module area name or vice versa
                if area_name.lower() in module_area_name.lower() or module_area_name.lower() in area_name.lower():
                    found_module = module_root
                    break
    
    # Try keyword matching
    if not found_module:
        keywords = {
            "blackvulkar": ["vulkar", "black"],
            "dantooineestate": ["dantooine", "estate", "sandral"],
            "davikestate": ["davik", "estate"],
            "enclavesurface": ["enclave", "surface", "courtyard"],
            "endarspire": ["endar", "spire"],
            "hiddenbek": ["bek", "hidden"],
            "jedienclave": ["jedi", "enclave"],
            "sithbase": ["sith", "base", "academy"],
            "tarissewers": ["sewer", "taris"],
        }
        kit_keywords = keywords.get(kit_id, [])
        for module_root, module_area_name in module_roots_to_areas.items():
            if module_area_name:
                area_lower = module_area_name.lower()
                if any(keyword in area_lower for keyword in kit_keywords):
                    found_module = module_root
                    break
    
    kit_to_module[kit_id] = found_module
    status = f"✓ {found_module}" if found_module else "✗ NOT FOUND"
    print(f"{kit_id:20s} -> {area_name:25s} -> {status}")

print("\n" + "=" * 80)
print("\nModule mapping for tests:")
print("-" * 80)
for kit_id, module_name in sorted(kit_to_module.items()):
    if module_name:
        print(f'    "{kit_id}": "{module_name}",')
    else:
        print(f'    "{kit_id}": None,  # NOT FOUND')

