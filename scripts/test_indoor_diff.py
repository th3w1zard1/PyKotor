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


def run_all_tests(installation: HTInstallation, kits_path: str = "./kits", verbose: bool = False) -> int:
    """Run all tests and return exit code."""
    results = []
    
    results.append(("ModuleKitManager", test_module_kit_manager(installation, verbose)))
    results.append(("Lazy Loading", test_module_kit_lazy_loading(installation, verbose)))
    results.append(("Component Structure", test_component_structure(installation, verbose)))
    results.append(("BWM Preview", test_bwm_preview_generation(installation, verbose)))
    results.append(("Kit vs Module", compare_kit_module_structures(installation, kits_path, verbose)))
    
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
