"""Abstract game object base classes for KotOR games.

This module provides abstract base classes for game objects that can be used
by any engine implementation. These classes define the interface and common
functionality for creatures, items, doors, placeables, and other game objects.

References:
----------
    vendor/reone/include/reone/game/object.h (Object base class)
    vendor/reone/src/libs/game/object.cpp (Object implementation)
    vendor/KotOR.js/src/engine/GameObject.ts (TypeScript game object)
    Note: Game objects are the fundamental entities in KotOR modules
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

from utility.common.geometry import Vector3  # noqa: PLC2701

if TYPE_CHECKING:
    from pykotor.common.misc import ResRef


class ObjectType(IntEnum):
    """Type enumeration for game objects."""

    INVALID = 0
    CREATURE = 1
    DOOR = 2
    ITEM = 3
    TRIGGER = 4
    PLACEABLE = 5
    WAYPOINT = 6
    ENCOUNTER = 7
    STORE = 8
    AREA = 9
    SOUND = 10
    CAMERA = 11


@dataclass
class GameObjectState:
    """State data for a game object."""

    object_id: int = 0
    tag: str = ""
    name: str = ""
    blueprint_resref: ResRef = ""
    position: Vector3 = field(default_factory=lambda: Vector3(0, 0, 0))
    facing: float = 0.0
    visible: bool = True
    plot_flag: bool = False
    commandable: bool = True
    min_one_hp: bool = False
    dead: bool = False
    open: bool = False


class GameObject(ABC):
    """Abstract base class for all game objects.

    This class defines the common interface and functionality for all game objects
    in KotOR modules, including creatures, items, doors, placeables, etc.

    References:
    ----------
        vendor/reone/include/reone/game/object.h (lines 42-305)
        vendor/reone/src/libs/game/object.cpp (Object implementation)
    """

    def __init__(self, object_type: ObjectType, state: GameObjectState | None = None) -> None:
        """Initialize a new game object.

        Args:
        ----
            object_type: The type of game object
            state: Optional initial state data
        """
        self._type = object_type
        self._state = state or GameObjectState()

    @property
    def object_id(self) -> int:
        """Get the unique object ID."""
        return self._state.object_id

    @object_id.setter
    def object_id(self, value: int) -> None:
        """Set the unique object ID."""
        self._state.object_id = value

    @property
    def tag(self) -> str:
        """Get the object tag."""
        return self._state.tag

    @tag.setter
    def tag(self, value: str) -> None:
        """Set the object tag."""
        self._state.tag = value

    @property
    def name(self) -> str:
        """Get the object name."""
        return self._state.name

    @name.setter
    def name(self, value: str) -> None:
        """Set the object name."""
        self._state.name = value

    @property
    def blueprint_resref(self) -> ResRef:
        """Get the blueprint resource reference."""
        return self._state.blueprint_resref

    @blueprint_resref.setter
    def blueprint_resref(self, value: ResRef) -> None:
        """Set the blueprint resource reference."""
        self._state.blueprint_resref = value

    @property
    def position(self) -> Vector3:
        """Get the object position."""
        return self._state.position

    @position.setter
    def position(self, value: Vector3) -> None:
        """Set the object position."""
        self._state.position = value
        self._on_position_changed()

    @property
    def facing(self) -> float:
        """Get the object facing angle (in radians)."""
        return self._state.facing

    @facing.setter
    def facing(self, value: float) -> None:
        """Set the object facing angle (in radians)."""
        self._state.facing = value
        self._on_facing_changed()

    @property
    def visible(self) -> bool:
        """Check if the object is visible."""
        return self._state.visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Set the object visibility."""
        self._state.visible = value
        self._on_visibility_changed()

    @property
    def plot_flag(self) -> bool:
        """Check if the object has plot flag set."""
        return self._state.plot_flag

    @plot_flag.setter
    def plot_flag(self, value: bool) -> None:
        """Set the plot flag."""
        self._state.plot_flag = value

    @property
    def commandable(self) -> bool:
        """Check if the object is commandable."""
        return self._state.commandable

    @commandable.setter
    def commandable(self, value: bool) -> None:
        """Set the commandable flag."""
        self._state.commandable = value

    @property
    def min_one_hp(self) -> bool:
        """Check if the object has minimum one HP flag."""
        return self._state.min_one_hp

    @min_one_hp.setter
    def min_one_hp(self, value: bool) -> None:
        """Set the minimum one HP flag."""
        self._state.min_one_hp = value

    @property
    def dead(self) -> bool:
        """Check if the object is dead."""
        return self._state.dead

    @dead.setter
    def dead(self, value: bool) -> None:
        """Set the dead flag."""
        self._state.dead = value

    @property
    def open(self) -> bool:
        """Check if the object is open (for doors, containers, etc.)."""
        return self._state.open

    @open.setter
    def open(self, value: bool) -> None:
        """Set the open state."""
        self._state.open = value

    @property
    def object_type(self) -> ObjectType:
        """Get the object type."""
        return self._type

    def get_distance_to(self, point: Vector3) -> float:
        """Calculate distance to a point.

        Args:
        ----
            point: Target point

        Returns:
        -------
            Distance to the point
        """
        dx = self.position.x - point.x
        dy = self.position.y - point.y
        dz = self.position.z - point.z
        return (dx * dx + dy * dy + dz * dz) ** 0.5

    def get_distance_to_2d(self, point: Vector3) -> float:
        """Calculate 2D distance to a point (ignoring Z).

        Args:
        ----
            point: Target point

        Returns:
        -------
            2D distance to the point
        """
        dx = self.position.x - point.x
        dy = self.position.y - point.y
        return (dx * dx + dy * dy) ** 0.5

    def get_distance_to_object(self, other: GameObject) -> float:
        """Calculate distance to another object.

        Args:
        ----
            other: Target object

        Returns:
        -------
            Distance to the other object
        """
        return self.get_distance_to(other.position)

    def get_distance_to_object_2d(self, other: GameObject) -> float:
        """Calculate 2D distance to another object (ignoring Z).

        Args:
        ----
            other: Target object

        Returns:
        -------
            2D distance to the other object
        """
        return self.get_distance_to_2d(other.position)

    def face_point(self, point: Vector3) -> None:
        """Face towards a point.

        Args:
        ----
            point: Target point to face
        """
        dx = point.x - self.position.x
        dy = point.y - self.position.y
        self.facing = __import__("math").atan2(dy, dx)

    def face_object(self, other: GameObject) -> None:
        """Face towards another object.

        Args:
        ----
            other: Target object to face
        """
        self.face_point(other.position)

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update the object (called every frame).

        Args:
        ----
            delta_time: Time since last update in seconds
        """
        ...

    @abstractmethod
    def die(self) -> None:
        """Handle object death."""
        ...

    @abstractmethod
    def is_selectable(self) -> bool:
        """Check if the object can be selected.

        Returns:
        -------
            True if the object can be selected
        """
        ...

    def _on_position_changed(self) -> None:
        """Called when position changes (override in subclasses)."""
        pass

    def _on_facing_changed(self) -> None:
        """Called when facing changes (override in subclasses)."""
        pass

    def _on_visibility_changed(self) -> None:
        """Called when visibility changes (override in subclasses)."""
        pass
