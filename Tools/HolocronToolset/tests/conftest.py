import os
import pytest
import sys
import cProfile
import logging
import pstats
import signal
import time
from datetime import datetime
from pathlib import Path

# Normalize PYTHONPATH for cross-platform compatibility
# This ensures PYTHONPATH works on Windows (semicolons) and Unix/Linux/macOS (colons)
_pythonpath = os.environ.get("PYTHONPATH")
if _pythonpath:
    correct_sep = os.pathsep
    if ";" in _pythonpath and correct_sep == ":":
        # Windows format on Unix - convert to colons
        paths = [p.strip().strip('"').strip("'") for p in _pythonpath.split(";") if p.strip()]
        os.environ["PYTHONPATH"] = correct_sep.join(paths)
    elif ":" in _pythonpath and correct_sep == ";":
        # Unix format on Windows - convert to semicolons
        paths = [p.strip().strip('"').strip("'") for p in _pythonpath.split(":") if p.strip()]
        os.environ["PYTHONPATH"] = correct_sep.join(paths)
    else:
        # Already correct format, just normalize paths
        paths = [p.strip().strip('"').strip("'") for p in _pythonpath.split(correct_sep) if p.strip()]
    
    # Add PYTHONPATH paths to sys.path to ensure imports work
    for path_str in paths:
        if path_str:
            path_obj = Path(path_str).resolve()
            if path_obj.exists() and str(path_obj) not in sys.path:
                sys.path.insert(0, str(path_obj))

# Set Qt API to PyQt5 (default) before any Qt imports
# qtpy will use this to select the appropriate bindings
if "QT_API" not in os.environ:
    os.environ["QT_API"] = "PyQt5"

# Configure Qt for headless testing by default
# Most tests should run headless (offscreen) to avoid spawning GUI windows
# Only module designer tests (which require OpenGL) should run with a real display
# Set offscreen mode by default - module designer tests will override this
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Store original platform setting for module designer tests
_original_qt_platform = os.environ.get("QT_QPA_PLATFORM")

# Configure Qt for OpenGL testing (for module designer tests only)
# Don't force software rendering - use hardware GPU when available
# Software rendering doesn't support modern OpenGL features (shaders, etc.)
# Only CI systems without GPU should set QT_OPENGL=software explicitly

# Disable PyOpenGL error checking for tests
# Some OpenGL configurations may produce errors that don't affect actual rendering
os.environ["PYOPENGL_ERROR_CHECKING"] = "0"

def _is_module_designer_test(item: pytest.Item) -> bool:
    """Check if a test is a module designer test that requires OpenGL/real display.
    
    Module designer tests require a real display because they use OpenGL rendering.
    All other tests should run headless (offscreen) to avoid spawning GUI windows.
    
    Only tests that directly test ModuleDesigner (not just import ToolWindow) need real display.
    """
    test_path = str(item.fspath) if hasattr(item, 'fspath') else str(item.path)
    test_name = item.name if hasattr(item, 'name') else ""
    
    # Only tests that directly test ModuleDesigner need real display
    # test_module_designer_performance.py contains actual ModuleDesigner tests
    # test_ui_windows.py has test_module_designer_init which directly tests ModuleDesigner
    # Other tests that import ToolWindow but don't use ModuleDesigner should run headless
    if "test_module_designer_performance" in test_path:
        return True
    if "test_ui_windows" in test_path and "module_designer" in test_name.lower():
        return True
    
    return False

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item):
    """Setup hook that runs before each test.
    
    For module designer tests, unset QT_QPA_PLATFORM to allow real display.
    For all other tests, ensure offscreen mode is set to prevent GUI windows from appearing.
    """
    if _is_module_designer_test(item):
        # Module designer tests need real display for OpenGL rendering
        # Remove offscreen setting to allow real display
        if "QT_QPA_PLATFORM" in os.environ and os.environ["QT_QPA_PLATFORM"] == "offscreen":
            del os.environ["QT_QPA_PLATFORM"]
    else:
        # All other tests should run headless to avoid spawning GUI windows
        # This prevents tests from showing windows that require manual interaction
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Paths
REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_PATH = REPO_ROOT / "Tools"
LIBS_PATH = REPO_ROOT / "Libraries"

# Add Toolset src
TOOLSET_SRC = (TOOLS_PATH / "HolocronToolset" / "src").resolve()
if str(TOOLSET_SRC) not in sys.path:
    sys.path.insert(0, str(TOOLSET_SRC))

# Add KotorDiff src (needed for KotorDiffWindow)
KOTORDIFF_SRC = (TOOLS_PATH / "KotorDiff" / "src").resolve()
if str(KOTORDIFF_SRC) not in sys.path:
    sys.path.insert(0, str(KOTORDIFF_SRC))

# Add Libraries
PYKOTOR_PATH = (LIBS_PATH / "PyKotor" / "src").resolve()
UTILITY_PATH = (LIBS_PATH / "Utility" / "src").resolve()
PYKOTORGL_PATH = (LIBS_PATH / "PyKotorGL" / "src").resolve()

if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))
if str(UTILITY_PATH) not in sys.path:
    sys.path.insert(0, str(UTILITY_PATH))
if str(PYKOTORGL_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTORGL_PATH))

from toolset.data.installation import HTInstallation
from toolset.main_settings import setup_pre_init_settings

# Module-level set to track which installations have been pre-warmed
_prewarmed_installations = set()

@pytest.fixture(scope="session")
def k1_path():
    path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
    if not path:
        pytest.skip("K1_PATH environment variable not set")
    return path

@pytest.fixture(scope="session")
def k2_path():
    path = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")
    if not path:
        pytest.skip("K2_PATH environment variable not set")
    return path

def _prewarm_installation(installation: HTInstallation, skip_streams: bool = True, skip_2da: bool = True) -> None:
    """Pre-warm installation cache to ensure expensive operations in _setup_installation
    are only performed once per installation across all tests.
    
    Args:
    ----
        installation: The installation to pre-warm
        skip_streams: If True, skip loading stream resources (WAVES, sounds, music) which are expensive
                     and not needed for most tests. Set to False if tests need stream resources.
        skip_2da: If True, skip caching 2DA files which takes ~31 seconds. Set to False if tests need 2DA files.
                  Tests that need 2DA files can call ht_batch_cache_2da themselves.
    
    This includes:
    - Caching 2DA files (ht_batch_cache_2da is idempotent, but we pre-warm for clarity)
      (only if skip_2da=False)
    - Accessing stream resources (_streamwaves, _streamsounds, _streammusic) which triggers scanning
      (only if skip_streams=False)
    """
    # Use installation path as unique identifier to track pre-warming per installation
    installation_id = id(installation)
    if installation_id in _prewarmed_installations:
        return
    
    # Temporarily disable logging to avoid expensive flush operations during prewarm
    import logging
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_handlers = root_logger.handlers[:]
    
    # Disable all handlers temporarily to prevent flush operations
    for handler in root_logger.handlers:
        handler.setLevel(logging.ERROR)
    root_logger.setLevel(logging.ERROR)
    
    try:
        # Pre-warm 2DA caches for all editors that use _setup_installation
        # This takes ~31 seconds - skip by default for kit generation tests
        if not skip_2da:
            # DLGEditor (K1)
            installation.ht_batch_cache_2da([
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS,
            ])
            # DLGEditor (K2) and other editors
            installation.ht_batch_cache_2da([
                HTInstallation.TwoDA_EMOTIONS,
                HTInstallation.TwoDA_EXPRESSIONS,
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS,
            ])
    
        # Pre-warm stream resources by accessing them once (triggers scanning, but only once)
        # This is the expensive operation that takes ~45 seconds - skip by default
        if not skip_streams:
            _ = list(installation._streamwaves)  # noqa: SLF001
            _ = list(installation._streamsounds)  # noqa: SLF001
            _ = list(installation._streammusic)  # noqa: SLF001
    finally:
        # Restore original logging configuration
        root_logger.setLevel(original_level)
        for handler, orig_handler in zip(root_logger.handlers, original_handlers):
            if hasattr(orig_handler, 'level'):
                handler.setLevel(orig_handler.level)
    
    _prewarmed_installations.add(installation_id)

@pytest.fixture(scope="session")
def installation(k1_path):
    """Creates a shared HTInstallation instance for K1 (session-scoped singleton)."""
    inst = HTInstallation(k1_path, "Test Installation", tsl=False)
    # Skip stream loading for most tests - saves ~45 seconds
    _prewarm_installation(inst, skip_streams=True)
    return inst

@pytest.fixture(scope="session")
def tsl_installation(k2_path):
    """Creates a shared HTInstallation instance for K2/TSL (session-scoped singleton, lazy-loaded)."""
    inst = HTInstallation(k2_path, "Test TSL Installation", tsl=True)
    # Skip stream loading for most tests - saves ~45 seconds
    _prewarm_installation(inst, skip_streams=True)
    return inst

@pytest.fixture(scope="session", autouse=True)
def setup_settings():
    """Ensure settings are initialized before tests run."""
    setup_pre_init_settings()

# Global shared installation instance for unittest tests
from typing import Union
_shared_k1_installation: Union[HTInstallation, None] = None

# Profiling for conftest.py operations
_conftest_profiler: Union[cProfile.Profile, None] = None

def _rotate_prof_files(prof_dir: Path, keep_count: int = 50) -> None:
    """Rotate prof files, keeping only the most recent ones.
    
    Args:
        prof_dir: Directory containing prof files
        keep_count: Number of most recent prof files to keep (default: 50)
    """
    prof_files = sorted(prof_dir.glob("*.prof"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Remove files beyond the keep_count limit
    for old_file in prof_files[keep_count:]:
        try:
            old_file.unlink()
            print(f"Rotated (deleted) old prof file: {old_file.name}")
        except OSError:
            pass  # File might have been deleted already

def pytest_configure(config):
    """Pre-warm installation cache before any tests run.
    
    This hook runs very early in the pytest lifecycle, before test collection.
    We create and pre-warm a shared installation instance that unittest tests can use.
    """
    global _shared_k1_installation, _conftest_profiler
    
    # Configure logging to suppress 'Loading ... from installation...' messages during tests
    class InstallationLoadingFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            # Filter out messages containing "Loading" and "from installation"
            message = record.getMessage()
            if "Loading" in message and "from installation" in message:
                return False
            return True
    
    # Apply filter to root logger
    root_logger = logging.getLogger()
    installation_filter = InstallationLoadingFilter()
    root_logger.addFilter(installation_filter)
    
    # Also set root logger level to WARNING to suppress INFO messages
    # But keep the filter in case some handlers bypass the level
    root_logger.setLevel(logging.WARNING)
    
    # Start profiling conftest operations
    _conftest_profiler = cProfile.Profile()
    _conftest_profiler.enable()
    start_time = time.time()
    
    try:
        k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
        if k1_path and os.path.exists(k1_path):
            _shared_k1_installation = HTInstallation(k1_path, "Shared Test Installation", tsl=False)
            # Skip stream loading and 2DA caching for unittest tests - saves ~76 seconds total
            _prewarm_installation(_shared_k1_installation, skip_streams=True, skip_2da=True)
    finally:
        _conftest_profiler.disable()
        duration = time.time() - start_time
        
        # Only save prof file if execution took 30+ seconds
        if duration >= 30.0:
            # Create flat cProfile directory structure
            conftest_path = Path(__file__)
            tests_root = conftest_path.parents[1]  # tests/
            prof_dir = tests_root / "cProfile"
            prof_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prof_file = prof_dir / f"conftest_{timestamp}.prof"
            _conftest_profiler.dump_stats(str(prof_file))
            print(f"\nConftest profiling saved to {prof_file} (duration: {duration:.2f}s)")
            
            # Rotate old prof files (keep only last 50)
            _rotate_prof_files(prof_dir)

def get_shared_k1_installation() -> Union[HTInstallation, None]:
    """Get the shared pre-warmed K1 installation instance for unittest tests."""
    return _shared_k1_installation

@pytest.fixture(scope="session")
def test_files_dir():
    """Returns the path to the test files directory."""
    path = Path(__file__).parent / "test_files"
    if not path.exists():
        # Fallback to pykotor test files if toolset one doesn't exist or is empty
        # But prefer toolset one as it has baragwin.uti
        # Assuming the user has these files present as they attached them.
        pass
    return path

@pytest.fixture
def mock_installation(mocker):
    """Creates a mock HTInstallation for tests that don't need a real one."""
    mock = mocker.MagicMock(spec=HTInstallation)
    mock.name = "Mock Installation"
    mock.tsl = False
    mock.path.return_value = Path("/mock/path")
    return mock

# Profiling setup
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """
    Profile the test execution.
    Only creates .prof files if execution time is 30+ seconds.
    """
    profiler = cProfile.Profile()
    start_time = time.time()
    
    def signal_handler(sig, frame):
        print(f"\nCaught signal {sig}, dumping profile stats...")
        profiler.disable()
        duration = time.time() - start_time
        
        # Always save interrupted prof files regardless of duration
        # Create flat cProfile directory structure
        conftest_path = Path(__file__)
        tests_root = conftest_path.parents[1]  # tests/
        prof_dir = tests_root / "cProfile"
        prof_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats = pstats.Stats(profiler).sort_stats('cumtime')
        stats.print_stats(50)
        prof_file = prof_dir / f"{item.name}_interrupted_{timestamp}.prof"
        stats.dump_stats(str(prof_file))
        print(f"Profile saved to {prof_file} (duration: {duration:.2f}s)")
        
        # Restore original handler and re-raise or exit
        signal.signal(signal.SIGINT, original_handler)
        sys.exit(1)

    # Save original handler
    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        signal.signal(signal.SIGINT, original_handler)
        
        duration = time.time() - start_time
        
        # Only create .prof file if execution took 30+ seconds
        if duration >= 30.0:
            # Create flat cProfile directory structure
            conftest_path = Path(__file__)
            tests_root = conftest_path.parents[1]  # tests/
            prof_dir = tests_root / "cProfile"
            prof_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prof_file = prof_dir / f"{item.name}_{timestamp}.prof"
            stats = pstats.Stats(profiler).sort_stats('cumtime')
            print(f"\nProfile stats for {item.name} (duration: {duration:.2f}s):")
            stats.print_stats(20)
            stats.dump_stats(str(prof_file))
            print(f"Profile saved to {prof_file}")
            
            # Rotate old prof files (keep only last 50)
            _rotate_prof_files(prof_dir)
        # uncomment to always print cprofile stats even if within target duration.
        #else:
            # Still print stats for debugging, but don't save file
        #    stats = pstats.Stats(profiler).sort_stats('cumtime')
        #    print(f"\nProfile stats for {item.name} (duration: {duration:.2f}s, not saved - < 30s):")
        #    stats.print_stats(20)
