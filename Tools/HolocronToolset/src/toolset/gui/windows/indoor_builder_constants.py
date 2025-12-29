"""Constants and configuration for the Indoor Map Builder.

This module centralizes all magic numbers, thresholds, and configuration values
used throughout the indoor map builder to improve maintainability and consistency.
"""
from __future__ import annotations

from enum import Enum
from typing import Final

# =============================================================================
# Renderer Constants
# =============================================================================

# Render loop timing
RENDER_FPS: Final[int] = 60
RENDER_INTERVAL_MS: Final[int] = 16  # 1000ms / 60fps ≈ 16ms

# Camera defaults
DEFAULT_CAMERA_POSITION_X: Final[float] = 0.0
DEFAULT_CAMERA_POSITION_Y: Final[float] = 0.0
DEFAULT_CAMERA_ROTATION: Final[float] = 0.0
DEFAULT_CAMERA_ZOOM: Final[float] = 1.0
MIN_CAMERA_ZOOM: Final[float] = 0.1
MAX_CAMERA_ZOOM: Final[float] = 50.0  # Increased to allow much closer zoom

# Zoom controls
# Use multiplicative factor for linear visual zoom (each step changes by the same percentage)
ZOOM_STEP_FACTOR: Final[float] = 1.15  # 15% zoom change per keyboard step (linear visual change)
ZOOM_WHEEL_SENSITIVITY: Final[float] = 0.03  # Percentage change per wheel click (3% per click for finer control)

# =============================================================================
# Snapping Constants
# =============================================================================

# Grid snapping
DEFAULT_GRID_SIZE: Final[float] = 1.0
MIN_GRID_SIZE: Final[float] = 0.5
MAX_GRID_SIZE: Final[float] = 10.0
GRID_SIZE_STEP: Final[float] = 0.5

# Hook snapping
HOOK_SNAP_BASE_THRESHOLD: Final[float] = 1.0
HOOK_SNAP_SCALE_FACTOR: Final[float] = 2.0
HOOK_CONNECTION_THRESHOLD: Final[float] = 1.5  # Distance for auto-connecting hooks
HOOK_SNAP_DISCONNECT_BASE_THRESHOLD: Final[float] = 1.0
HOOK_SNAP_DISCONNECT_SCALE_FACTOR: Final[float] = 0.8

# Rotation snapping
DEFAULT_ROTATION_SNAP: Final[int] = 15
MIN_ROTATION_SNAP: Final[int] = 1
MAX_ROTATION_SNAP: Final[int] = 90

# =============================================================================
# Interaction Thresholds
# =============================================================================

# Position change thresholds (for undo/redo)
POSITION_CHANGE_EPSILON: Final[float] = 0.001
ROTATION_CHANGE_EPSILON: Final[float] = 0.001

# Hook interaction
HOOK_HOVER_RADIUS: Final[float] = 0.6
HOOK_DISPLAY_RADIUS: Final[float] = 0.4
HOOK_SELECTED_RADIUS: Final[float] = 0.8

# Warp point
WARP_POINT_RADIUS: Final[float] = 1.0
WARP_POINT_ACTIVE_SCALE: Final[float] = 1.3
WARP_POINT_CROSSHAIR_SCALE: Final[float] = 1.2

# Marquee selection
MARQUEE_MOVE_THRESHOLD_PIXELS: Final[float] = 5.0

# =============================================================================
# Visual Constants
# =============================================================================

# Hook colors (RGBA)
HOOK_COLOR_UNCONNECTED: Final[tuple[int, int, int, int]] = (255, 80, 80, 255)  # Red
HOOK_COLOR_CONNECTED: Final[tuple[int, int, int, int]] = (80, 200, 80, 255)  # Green
HOOK_COLOR_SELECTED: Final[tuple[int, int, int, int]] = (80, 160, 255, 255)  # Blue
HOOK_PEN_COLOR_UNCONNECTED: Final[tuple[int, int, int, int]] = (255, 200, 200, 255)
HOOK_PEN_COLOR_CONNECTED: Final[tuple[int, int, int, int]] = (180, 255, 180, 255)
HOOK_PEN_COLOR_SELECTED: Final[tuple[int, int, int, int]] = (180, 220, 255, 255)

# Snap indicator
SNAP_INDICATOR_COLOR: Final[tuple[int, int, int, int]] = (0, 255, 255, 255)  # Cyan
SNAP_INDICATOR_ALPHA: Final[int] = 100
SNAP_INDICATOR_RADIUS: Final[float] = 0.8
SNAP_INDICATOR_PEN_WIDTH: Final[float] = 0.3

# Grid
GRID_COLOR: Final[tuple[int, int, int, int]] = (50, 50, 50, 255)
GRID_PEN_WIDTH: Final[float] = 0.05

# Warp point
WARP_POINT_COLOR: Final[tuple[int, int, int, int]] = (0, 255, 0, 255)  # Green
WARP_POINT_ALPHA_NORMAL: Final[int] = 127
WARP_POINT_ALPHA_ACTIVE: Final[int] = 180
WARP_POINT_PEN_WIDTH_NORMAL: Final[float] = 0.4
WARP_POINT_PEN_WIDTH_ACTIVE: Final[float] = 0.6

# Room highlights
ROOM_HOVER_ALPHA: Final[int] = 40
ROOM_SELECTED_ALPHA: Final[int] = 80
ROOM_HOVER_COLOR: Final[tuple[int, int, int, int]] = (100, 150, 255, 255)
ROOM_SELECTED_COLOR: Final[tuple[int, int, int, int]] = (255, 200, 100, 255)

# Cursor preview
CURSOR_PREVIEW_ALPHA: Final[int] = 150
CURSOR_HOOK_ALPHA: Final[int] = 180

# Background
BACKGROUND_COLOR: Final[tuple[int, int, int, int]] = (20, 20, 25, 255)

# Connection lines
CONNECTION_LINE_COLOR: Final[tuple[int, int, int, int]] = (80, 255, 80, 255)
CONNECTION_LINE_WIDTH_SCALE: Final[float] = 2.0

# Marquee selection
MARQUEE_FILL_COLOR: Final[tuple[int, int, int, int]] = (100, 150, 255, 50)
MARQUEE_BORDER_COLOR: Final[tuple[int, int, int, int]] = (100, 150, 255, 255)

# =============================================================================
# Placement Constants
# =============================================================================

# Default placement offset for duplication
DUPLICATE_OFFSET_X: Final[float] = 2.0
DUPLICATE_OFFSET_Y: Final[float] = 2.0
DUPLICATE_OFFSET_Z: Final[float] = 0.0

# Component preview scaling
COMPONENT_PREVIEW_SCALE: Final[float] = 0.1  # Divide by 10

# =============================================================================
# Drag Mode Enum
# =============================================================================


class DragMode(Enum):
    """Enumeration of drag operation modes."""

    NONE = ""
    ROOMS = "rooms"
    WARP = "warp"
    MARQUEE = "marquee"
    HOOK = "hook"

