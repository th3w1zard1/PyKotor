"""Debug script to investigate MDLOps timeout issues."""

import tempfile
from pathlib import Path

from pykotor.common.misc import Game
from pykotor.extract.file import FileResource
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default


def debug_model(model_name: str, game: Game):
    """Debug a specific model."""
    paths = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game} installation found")
        return

    installation = Installation(game_paths[0])
    mdl_res = None
    mdx_res = None
    
    for res in installation:
        if res.resname() == model_name and res.restype() == ResourceType.MDL:
            mdl_res = res
        elif res.resname() == model_name and res.restype() == ResourceType.MDX:
            mdx_res = res
    
    if not mdl_res or not mdx_res:
        print(f"Model {model_name} not found")
        return
    
    with tempfile.TemporaryDirectory(prefix="mdl_debug_") as td:
        td_path = Path(td)
        test_mdl = td_path / f"{model_name}.mdl"
        test_mdx = td_path / f"{model_name}.mdx"
        
        test_mdl.write_bytes(mdl_res.data())
        test_mdx.write_bytes(mdx_res.data())
        
        print(f"Reading {model_name}...")
        mdl_obj = read_mdl(test_mdl, source_ext=test_mdx, file_format=ResourceType.MDL)
        if mdl_obj is None:
            print("Failed to read MDL")
            return
        
        print(f"Writing PyKotor output...")
        pykotor_mdl = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx = td_path / f"{model_name}-pykotor.mdx"
        
        try:
            write_mdl(mdl_obj, pykotor_mdl, ResourceType.MDL, target_ext=pykotor_mdx)
            print(f"Wrote {pykotor_mdl} ({pykotor_mdl.stat().st_size} bytes)")
            print(f"Wrote {pykotor_mdx} ({pykotor_mdx.stat().st_size} bytes)")
            
            # Compare sizes
            orig_mdl_size = test_mdl.stat().st_size
            orig_mdx_size = test_mdx.stat().st_size
            pykotor_mdl_size = pykotor_mdl.stat().st_size
            pykotor_mdx_size = pykotor_mdx.stat().st_size
            
            print(f"\nSize comparison:")
            print(f"  Original MDL: {orig_mdl_size} bytes")
            print(f"  PyKotor MDL:  {pykotor_mdl_size} bytes (diff: {pykotor_mdl_size - orig_mdl_size:+d})")
            print(f"  Original MDX: {orig_mdx_size} bytes")
            print(f"  PyKotor MDX:  {pykotor_mdx_size} bytes (diff: {pykotor_mdx_size - orig_mdx_size:+d})")
            
        except Exception as e:
            print(f"Error writing: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Debug the failing models
    print("Debugging n_darkjedim.mdl (K1)...")
    debug_model("n_darkjedim", Game.K1)
    
    print("\n" + "="*70 + "\n")
    
    print("Debugging 101perac.mdl (K2)...")
    debug_model("101perac", Game.K2)

