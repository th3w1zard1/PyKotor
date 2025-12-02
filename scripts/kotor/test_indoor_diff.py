#!/usr/bin/env python3
"""
Test script for Indoor Map Builder module functionality.

This script validates the Indoor Map Builder's module integration by:
1. Testing ModuleKitManager functionality
2. Testing ModuleKit lazy loading
3. Testing component extraction from modules
4. Comparing kit-based and module-based component structures

Usage:
    python scripts/test_indoor_diff.py [--installation PATH] [--verbose]

Arguments:
    --installation PATH    Path to a KotOR installation directory
    --verbose              Enable verbose output
    --help                 Show this help message

Example:
    python scripts/test_indoor_diff.py --installation "C:/Games/KOTOR" --verbose
"""
from __future__ import annotations

import argparse
import sys

from pathlib import Path
from typing import TYPE_CHECKING

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "PyKotor" / "src"))
sys.path.insert(0, str(REPO_ROOT / "Tools" / "HolocronToolset" / "src"))
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "Utility" / "src"))

if TYPE_CHECKING:
    from toolset.data.installation import HTInstallation


def setup_installation(path: str | None) -> HTInstallation | None:
    """Set up HTInstallation from path or environment variable."""
    import os

    from toolset.data.installation import HTInstallation
    
    if path:
        if not Path(path).exists():
            print(f"Error: Installation path does not exist: {path}")
            return None
        return HTInstallation(path, "Test Installation")
    
    # Try environment variables
    for env_var in ["K1_PATH", "K2_PATH", "KOTOR_PATH"]:
        env_path = os.environ.get(env_var)
        if env_path and Path(env_path).exists():
            return HTInstallation(env_path, f"Installation from {env_var}")
    
    print("No installation path provided. Use --installation PATH or set K1_PATH/K2_PATH environment variable.")
    return None


def test_module_kit_manager(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test ModuleKitManager functionality."""
    from toolset.data.indoorkit import ModuleKitManager
    
    print("\n=== Testing ModuleKitManager ===")
    
    try:
        manager = ModuleKitManager(installation)
        
        # Test get_module_names
        names = manager.get_module_names()
        print(f"  Found {len(names)} module files")
        if verbose and names:
            for filename, display in list(names.items())[:5]:
                print(f"    - {filename}: {display}")
            if len(names) > 5:
                print(f"    ... and {len(names) - 5} more")
        
        # Test get_module_roots
        roots = manager.get_module_roots()
        print(f"  Found {len(roots)} unique module roots")
        if verbose and roots:
            for root in roots[:5]:
                display = manager.get_module_display_name(root)
                print(f"    - {root}: {display}")
            if len(roots) > 5:
                print(f"    ... and {len(roots) - 5} more")
        
        # Test caching
        if roots:
            kit1 = manager.get_module_kit(roots[0])
            kit2 = manager.get_module_kit(roots[0])
            assert kit1 is kit2, "Caching failed: different kit instances returned"
            print("  Caching: PASSED")
        
        print("ModuleKitManager: PASSED")
        return True
        
    except Exception as e:
        print(f"ModuleKitManager: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_module_kit_lazy_loading(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test ModuleKit lazy loading."""
    from toolset.data.indoorkit import ModuleKitManager
    
    print("\n=== Testing ModuleKit Lazy Loading ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if not roots:
            print("  No modules available for testing")
            return True
        
        # Pick first few modules for testing
        test_roots = roots[:3]
        
        for root in test_roots:
            kit = manager.get_module_kit(root)
            
            # Should not be loaded initially
            assert kit._loaded is False, f"Kit {root} should not be loaded initially"
            
            # Load components
            loaded = kit.ensure_loaded()
            
            # Should be loaded now
            assert kit._loaded is True, f"Kit {root} should be loaded after ensure_loaded"
            
            print(f"  Module '{root}':")
            print(f"    - Loaded: {loaded}")
            print(f"    - Components: {len(kit.components)}")
            
            if verbose and kit.components:
                for comp in kit.components[:3]:
                    print(f"      - {comp.name}")
                if len(kit.components) > 3:
                    print(f"      ... and {len(kit.components) - 3} more")
        
        print("ModuleKit Lazy Loading: PASSED")
        return True
        
    except Exception as e:
        print(f"ModuleKit Lazy Loading: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_component_structure(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test that module components have correct structure."""
    from toolset.data.indoorkit import KitComponent, ModuleKitManager
    
    print("\n=== Testing Component Structure ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if not roots:
            print("  No modules available for testing")
            return True
        
        # Test first module with components
        for root in roots:
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            
            if not kit.components:
                continue
            
            # Check component structure
            comp = kit.components[0]
            
            # Verify required attributes
            required_attrs = ['kit', 'name', 'image', 'bwm', 'mdl', 'mdx', 'hooks']
            missing = [attr for attr in required_attrs if not hasattr(comp, attr)]
            
            if missing:
                print(f"  Component missing attributes: {missing}")
                return False
            
            print(f"  Testing component '{comp.name}' from '{root}':")
            print(f"    - Has kit reference: {comp.kit is not None}")
            print(f"    - Has image: {comp.image is not None}")
            print(f"    - Has BWM: {comp.bwm is not None}")
            print(f"    - MDL size: {len(comp.mdl)} bytes")
            print(f"    - MDX size: {len(comp.mdx)} bytes")
            print(f"    - Hooks: {len(comp.hooks)}")
            
            # Verify component is valid KitComponent
            assert isinstance(comp, KitComponent), "Component is not a KitComponent instance"
            
            print("Component Structure: PASSED")
            return True
        
        print("  No modules with components found")
        return True
        
    except Exception as e:
        print(f"Component Structure: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_bwm_preview_generation(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test BWM preview image generation."""
    from qtpy.QtGui import QImage

    from toolset.data.indoorkit import ModuleKitManager
    
    print("\n=== Testing BWM Preview Generation ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if not roots:
            print("  No modules available for testing")
            return True
        
        # Find a module with components
        for root in roots:
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            
            if not kit.components:
                continue
            
            comp = kit.components[0]
            
            # Check image
            assert comp.image is not None, "Component has no image"
            assert isinstance(comp.image, QImage), "Component image is not QImage"
            assert comp.image.width() > 0, "Image has zero width"
            assert comp.image.height() > 0, "Image has zero height"
            
            print(f"  Image for '{comp.name}':")
            print(f"    - Size: {comp.image.width()}x{comp.image.height()}")
            print(f"    - Format: {comp.image.format()}")
            
            print("BWM Preview Generation: PASSED")
            return True
        
        print("  No components with images found")
        return True
        
    except Exception as e:
        print(f"BWM Preview Generation: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def compare_kit_module_structures(installation: HTInstallation, kits_path: str, verbose: bool = False) -> bool:
    """Compare structure of regular kits vs module-derived kits."""
    from toolset.data.indoorkit import ModuleKitManager, load_kits
    
    print("\n=== Comparing Kit vs Module Structures ===")
    
    try:
        # Load regular kits if available
        kits, missing = load_kits(kits_path)
        
        # Load module kits
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        print(f"  Regular kits found: {len(kits)}")
        print(f"  Module roots found: {len(roots)}")
        
        # Compare attributes
        if kits and roots:
            regular_kit = kits[0]
            module_kit = manager.get_module_kit(roots[0])
            module_kit.ensure_loaded()
            
            kit_attrs = set(dir(regular_kit))
            mod_attrs = set(dir(module_kit))
            
            common = kit_attrs & mod_attrs
            only_regular = kit_attrs - mod_attrs
            only_module = mod_attrs - kit_attrs
            
            if verbose:
                print(f"\n  Common attributes: {len(common)}")
                print(f"  Only in regular kits: {len(only_regular)}")
                if only_regular:
                    for attr in sorted(only_regular)[:5]:
                        if not attr.startswith('_'):
                            print(f"    - {attr}")
                print(f"  Only in module kits: {len(only_module)}")
                if only_module:
                    for attr in sorted(only_module)[:5]:
                        if not attr.startswith('_'):
                            print(f"    - {attr}")
        
        print("Kit vs Module Comparison: PASSED")
        return True
        
    except Exception as e:
        print(f"Kit vs Module Comparison: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_room_creation_from_module(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test creating IndoorMapRoom from module component."""
    from pykotor.data.indoormap import IndoorMapRoom
    from toolset.data.indoorkit import ModuleKitManager
    from utility.common.geometry import Vector3
    
    print("\n=== Testing Room Creation from Module ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if not roots:
            print("  No modules available for testing")
            return True
        
        # Find a module with components
        for root in roots:
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            
            if not kit.components:
                continue
            
            comp = kit.components[0]
            
            # Create room from module component
            room = IndoorMapRoom(
                comp,
                Vector3(10, 20, 0),
                45.0,
                flip_x=False,
                flip_y=True,
            )
            
            # Verify room properties
            assert room.component is comp, "Room component mismatch"
            assert abs(room.position.x - 10) < 0.001, "Room position X mismatch"
            assert abs(room.position.y - 20) < 0.001, "Room position Y mismatch"
            assert abs(room.rotation - 45.0) < 0.001, "Room rotation mismatch"
            assert room.flip_x is False, "Room flip_x mismatch"
            assert room.flip_y is True, "Room flip_y mismatch"
            
            print(f"  Created room from '{comp.name}':")
            print(f"    - Position: ({room.position.x}, {room.position.y})")
            print(f"    - Rotation: {room.rotation}")
            print(f"    - Flip: X={room.flip_x}, Y={room.flip_y}")
            
            # Verify component is from module kit
            assert getattr(kit, 'is_module_kit', False) is True, "Kit should be a module kit"
            
            print("Room Creation: PASSED")
            return True
        
        print("  No modules with components found")
        return True
        
    except Exception as e:
        print(f"Room Creation: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_indoor_map_operations(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test IndoorMap operations with module-derived rooms."""
    from pykotor.data.indoormap import IndoorMap, IndoorMapRoom
    from toolset.data.indoorkit import ModuleKitManager
    from utility.common.geometry import Vector3
    
    print("\n=== Testing IndoorMap Operations ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if not roots:
            print("  No modules available for testing")
            return True
        
        # Find a module with components
        for root in roots:
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            
            if not kit.components:
                continue
            
            # Create IndoorMap
            indoor_map = IndoorMap()
            
            # Add multiple rooms
            comp = kit.components[0]
            
            room1 = IndoorMapRoom(comp, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
            room2 = IndoorMapRoom(comp, Vector3(20, 0, 0), 90.0, flip_x=True, flip_y=False)
            room3 = IndoorMapRoom(comp, Vector3(40, 0, 0), 180.0, flip_x=False, flip_y=True)
            
            indoor_map.rooms.append(room1)
            indoor_map.rooms.append(room2)
            indoor_map.rooms.append(room3)
            
            assert len(indoor_map.rooms) == 3, "Should have 3 rooms"
            
            # Test remove
            indoor_map.rooms.remove(room2)
            assert len(indoor_map.rooms) == 2, "Should have 2 rooms after removal"
            assert room2 not in indoor_map.rooms, "Room2 should be removed"
            
            # Test clear
            indoor_map.rooms.clear()
            assert len(indoor_map.rooms) == 0, "Should have 0 rooms after clear"
            
            print(f"  Operations with component '{comp.name}':")
            print("    - Add rooms: OK")
            print("    - Remove room: OK")
            print("    - Clear rooms: OK")
            
            print("IndoorMap Operations: PASSED")
            return True
        
        print("  No modules with components found")
        return True
        
    except Exception as e:
        print(f"IndoorMap Operations: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_module_doors_and_hooks(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test module kit doors and hooks."""
    from toolset.data.indoorkit import ModuleKitManager
    
    print("\n=== Testing Module Doors and Hooks ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if not roots:
            print("  No modules available for testing")
            return True
        
        doors_found = 0
        hooks_found = 0
        
        for root in roots[:5]:  # Check first 5 modules
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            
            if not kit.components:
                continue
            
            # Check doors
            if kit.doors:
                doors_found += len(kit.doors)
                if verbose:
                    print(f"  Module '{root}' has {len(kit.doors)} doors")
                    for door in kit.doors[:2]:
                        print(f"    - Door: width={door.width}, height={door.height}")
            
            # Check hooks in components
            for comp in kit.components:
                if comp.hooks:
                    hooks_found += len(comp.hooks)
                    if verbose:
                        print(f"    Component '{comp.name}' has {len(comp.hooks)} hooks")
        
        print(f"  Total doors found: {doors_found}")
        print(f"  Total hooks found: {hooks_found}")
        
        print("Doors and Hooks: PASSED")
        return True
        
    except Exception as e:
        print(f"Doors and Hooks: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_module_bwm_geometry(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test BWM geometry from module components."""
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from toolset.data.indoorkit import ModuleKitManager
    
    print("\n=== Testing BWM Geometry ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if not roots:
            print("  No modules available for testing")
            return True
        
        for root in roots[:5]:
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            
            if not kit.components:
                continue
            
            comp = kit.components[0]
            bwm = comp.bwm
            
            assert isinstance(bwm, BWM), "BWM should be BWM instance"
            assert len(bwm.faces) > 0, "BWM should have faces"
            
            # Compute bounds
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for face in bwm.faces:
                for v in [face.v1, face.v2, face.v3]:
                    min_x = min(min_x, v.x)
                    min_y = min(min_y, v.y)
                    max_x = max(max_x, v.x)
                    max_y = max(max_y, v.y)
            
            width = max_x - min_x
            height = max_y - min_y
            
            print(f"  Component '{comp.name}':")
            print(f"    - Faces: {len(bwm.faces)}")
            print(f"    - Bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
            print(f"    - Size: {width:.1f} x {height:.1f}")
            
            # Check face structure
            face = bwm.faces[0]
            assert hasattr(face, 'v1'), "Face should have v1"
            assert hasattr(face, 'v2'), "Face should have v2"
            assert hasattr(face, 'v3'), "Face should have v3"
            assert hasattr(face, 'material'), "Face should have material"
            
            print("BWM Geometry: PASSED")
            return True
        
        print("  No modules with components found")
        return True
        
    except Exception as e:
        print(f"BWM Geometry: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_multiple_module_loading(installation: HTInstallation, verbose: bool = False) -> bool:
    """Test loading multiple modules simultaneously."""
    from toolset.data.indoorkit import ModuleKitManager
    
    print("\n=== Testing Multiple Module Loading ===")
    
    try:
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        if len(roots) < 3:
            print("  Need at least 3 modules for this test")
            return True
        
        # Load multiple modules
        loaded_kits = []
        for root in roots[:5]:
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            loaded_kits.append((root, kit))
            
            if verbose:
                print(f"  Loaded '{root}': {len(kit.components)} components")
        
        # Verify they're distinct
        for i, (root1, kit1) in enumerate(loaded_kits):
            for j, (root2, kit2) in enumerate(loaded_kits):
                if i != j:
                    assert kit1 is not kit2, f"Kits {root1} and {root2} should be distinct"
        
        # Verify caching
        for root, kit in loaded_kits:
            cached = manager.get_module_kit(root)
            assert cached is kit, f"Kit {root} should be cached"
        
        print(f"  Loaded {len(loaded_kits)} modules successfully")
        print("  All kits are distinct and cached correctly")
        
        print("Multiple Module Loading: PASSED")
        return True
        
    except Exception as e:
        print(f"Multiple Module Loading: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def test_component_equivalence(installation: HTInstallation, kits_path: str, verbose: bool = False) -> bool:
    """Test that module components can be used interchangeably with kit components."""
    from pykotor.data.indoormap import IndoorMap, IndoorMapRoom
    from toolset.data.indoorkit import KitComponent, ModuleKitManager, load_kits
    from utility.common.geometry import Vector3
    
    print("\n=== Testing Component Equivalence ===")
    
    try:
        # Load both regular kits and module kits
        regular_kits, _ = load_kits(kits_path)
        manager = ModuleKitManager(installation)
        roots = manager.get_module_roots()
        
        # Create indoor map
        indoor_map = IndoorMap()
        
        # Add room from regular kit if available
        regular_room = None
        if regular_kits:
            for kit in regular_kits:
                if kit.components:
                    comp = kit.components[0]
                    regular_room = IndoorMapRoom(comp, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
                    indoor_map.rooms.append(regular_room)
                    print(f"  Added room from regular kit: {comp.name}")
                    break
        
        # Add room from module kit
        module_room = None
        for root in roots:
            kit = manager.get_module_kit(root)
            kit.ensure_loaded()
            
            if kit.components:
                comp = kit.components[0]
                module_room = IndoorMapRoom(comp, Vector3(20, 0, 0), 0.0, flip_x=False, flip_y=False)
                indoor_map.rooms.append(module_room)
                print(f"  Added room from module kit: {comp.name}")
                break
        
        # Verify both rooms work
        for room in indoor_map.rooms:
            assert isinstance(room.component, KitComponent), "Room component should be KitComponent"
            assert room.component.bwm is not None, "Component should have BWM"
            assert room.component.image is not None, "Component should have image"
        
        print(f"  Total rooms in map: {len(indoor_map.rooms)}")
        print("  All rooms work with KitComponent interface")
        
        print("Component Equivalence: PASSED")
        return True
        
    except Exception as e:
        print(f"Component Equivalence: FAILED - {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False


def run_all_tests(installation: HTInstallation, kits_path: str = "./kits", verbose: bool = False) -> int:
    """Run all tests and return exit code."""
    results = []
    
    # Core module functionality tests
    results.append(("ModuleKitManager", test_module_kit_manager(installation, verbose)))
    results.append(("Lazy Loading", test_module_kit_lazy_loading(installation, verbose)))
    results.append(("Component Structure", test_component_structure(installation, verbose)))
    results.append(("BWM Preview", test_bwm_preview_generation(installation, verbose)))
    results.append(("Kit vs Module", compare_kit_module_structures(installation, kits_path, verbose)))
    
    # Room creation and operations tests
    results.append(("Room Creation", test_room_creation_from_module(installation, verbose)))
    results.append(("IndoorMap Operations", test_indoor_map_operations(installation, verbose)))
    
    # Hooks, doors, and geometry tests
    results.append(("Doors and Hooks", test_module_doors_and_hooks(installation, verbose)))
    results.append(("BWM Geometry", test_module_bwm_geometry(installation, verbose)))
    
    # Multi-module and equivalence tests
    results.append(("Multiple Modules", test_multiple_module_loading(installation, verbose)))
    results.append(("Component Equivalence", test_component_equivalence(installation, kits_path, verbose)))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return 0 if failed == 0 else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Indoor Map Builder module functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--installation", "-i",
        help="Path to KotOR installation directory"
    )
    parser.add_argument(
        "--kits", "-k",
        default="./kits",
        help="Path to kits directory (default: ./kits)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize Qt application for QImage support
    try:
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
    except Exception as e:
        print(f"Warning: Could not initialize Qt application: {e}")
    
    # Setup installation
    installation = setup_installation(args.installation)
    if installation is None:
        return 1
    
    print(f"Using installation: {installation.path}")
    print(f"Game: {installation.game().name}")
    
    # Run tests
    return run_all_tests(installation, args.kits, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
