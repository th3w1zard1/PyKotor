"""Check which kits are complete (have all lightmaps their MDLs reference)."""
from __future__ import annotations

import sys
sys.path.insert(0, 'Tools/HolocronToolset/src')
import os
os.chdir('Tools/HolocronToolset/src/toolset')

from pykotor.tools import model
from pykotor.common.indoorkit import Kit, load_kits

def main():
    kits = load_kits('./kits')
    print(f'Loaded {len(kits)} kits')

    for kit in kits:
        print(f'\nKit: {kit.name}')
        all_complete = True
        for comp in kit.components:
            try:
                lightmaps = list(model.iterate_lightmaps(comp.mdl))
            except Exception as e:
                print(f'  {comp.name}: ERROR reading lightmaps: {e}')
                all_complete = False
                continue
                
            for lm in lightmaps:
                # Check if lightmap exists in kit (case-insensitive)
                lm_upper = lm.upper()
                lm_lower = lm.lower()
                if lm_upper not in kit.lightmaps and lm_lower not in kit.lightmaps:
                    print(f'  {comp.name}: MISSING lightmap {lm}')
                    all_complete = False
                    break
        
        if all_complete:
            print(f'  => COMPLETE')
        else:
            print(f'  => INCOMPLETE')

if __name__ == '__main__':
    main()

