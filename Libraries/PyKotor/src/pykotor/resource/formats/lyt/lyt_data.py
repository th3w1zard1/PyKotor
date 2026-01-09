"""This module handles classes relating to editing LYT files.

LYT (Layout) files define the spatial structure of game areas/modules. They specify
the positions of room models, door hook points, swoop track elements, and obstacles.
LYT files are ASCII text files that describe how area geometry is assembled from
individual room models (MDL files) and where interactive elements like doors are placed.

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:18-100
        ASCII Format:
        ------------
        beginlayout
        roomcount <number>
        <model_name> <x> <y> <z>
        ...
        trackcount <number>
        <model_name> <x> <y> <z>
        ...
        obstaclecount <number>
        <model_name> <x> <y> <z>
        ...
        doorhookcount <number>
        <room_name> <door_name> <x> <y> <z> <qx> <qy> <qz> <qw>
        ...
        donelayout
        Format Rules:
        - Lines starting with '#' are comments
        - Room/track/obstacle entries: model name + 3D position (x, y, z)
        - Door hook entries: room name + door name + position + quaternion (7 values)
        - Room names are case-insensitive (stored lowercase)
        - Model names are ResRefs (max 16 chars, no spaces)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from utility.common.geometry import Vector3, Vector4


class LYT(ComparableMixin):
    """Represents a LYT (Layout) file defining area spatial structure.
    
    LYT files specify how area geometry is assembled from room models and where
    interactive elements (doors, tracks, obstacles) are positioned. The game engine
    uses LYT files to load and position room models (MDL files) and determine
    door placement points for area transitions.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:19-22 (arrays)


        
    Attributes:
    ----------
        rooms: List of room definitions (area model positions)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:19 (rooms array)
            Each room specifies a model name (ResRef) and 3D position
            Room models are MDL files that make up the area geometry
            Used by game engine to load and position area room models
            
        tracks: List of swoop track booster positions
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:21 (tracks array)
            Used in swoop racing mini-games (KotOR II)
            Each track entry specifies model name and position
            Currently not fully implemented in all vendor sources
            
        obstacles: List of swoop track obstacle positions
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:22 (obstacles array)
            Used in swoop racing mini-games (KotOR II)
            Each obstacle entry specifies model name and position
            Currently not fully implemented in all vendor sources
            
        doorhooks: List of door hook points (door placement positions)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:20 (doorhooks array)
            Each door hook specifies room name, door name, position, and orientation
            Door hooks define where doors can be placed in rooms
            Orientation stored as quaternion (qx, qy, qz, qw) for door rotation
    """

    BINARY_TYPE = ResourceType.LYT
    COMPARABLE_SEQUENCE_FIELDS = ("rooms", "tracks", "obstacles", "doorhooks")

    def __init__(self):
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:19
        
        # List of room definitions (model name + 3D position)
        self.rooms: list[LYTRoom] = []
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:21
        
        # List of swoop track booster positions
        self.tracks: list[LYTTrack] = []
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:22
        
        # List of swoop track obstacle positions
        self.obstacles: list[LYTObstacle] = []
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:20
        
        # List of door hook points (door placement positions)
        self.doorhooks: list[LYTDoorHook] = []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LYT):
            return NotImplemented
        return (
            self.rooms == other.rooms
            and self.tracks == other.tracks
            and self.obstacles == other.obstacles
            and self.doorhooks == other.doorhooks
        )

    def __hash__(self) -> int:
        return hash(
            (
                tuple(self.rooms),
                tuple(self.tracks),
                tuple(self.obstacles),
                tuple(self.doorhooks),
            ),
        )

    def iter_resource_identifiers(self) -> Generator[ResourceIdentifier, Any, None]:
        """Generate resources that utilise this LYT."""
        for room in self.rooms:
            yield ResourceIdentifier(room.model, ResourceType.MDL)
            yield ResourceIdentifier(room.model, ResourceType.MDX)
            yield ResourceIdentifier(room.model, ResourceType.WOK)

    def all_room_models(self) -> Generator[str, Any, None]:
        """Return all models used by this LYT."""
        for room in self.rooms:
            parsed_model: str = room.model.strip()
            assert parsed_model == room.model, "room model names cannot contain spaces."
            assert ResRef.is_valid(parsed_model), (
                f"invalid room model: '{room.model}' at room {self.rooms.index(room)}, "
                "must conform to resref restrictions."
            )
            yield parsed_model.lower()

    def find_room_by_model(self, model: str) -> LYTRoom | None:
        """Find a room in the LYT by its model name."""
        return next((room for room in self.rooms if room.model.lower() == model.lower()), None)

    def find_nearest_room(self, position: Vector3) -> LYTRoom | None:
        """Find the nearest room to a given position."""
        if not self.rooms:
            return None
        return min(self.rooms, key=lambda room: (room.position - position).magnitude())

    def _dfs_rooms(self, room: LYTRoom, visited: set[LYTRoom]) -> None:
        """Depth-first search to find connected rooms."""
        visited.add(room)
        for connected_room in room.connections:
            if connected_room not in visited:
                self._dfs_rooms(connected_room, visited)

    def update_connections(self, room1: LYTRoom, room2: LYTRoom, new_room: LYTRoom) -> None:
        """Update connections after merging rooms."""
        for room in self.rooms:
            if room1 in room.connections:
                room.connections.remove(room1)
                room.connections.add(new_room)
            if room2 in room.connections:
                room.connections.remove(room2)
                room.connections.add(new_room)

    def serialize(self) -> dict[str, Any]:
        """Serialize a complete LYT to JSON-compatible dict.

        Returns:
        -------
            Dictionary representation
        """
        return {
            "rooms": [r.serialize() for r in self.rooms],
            "doorhooks": [d.serialize() for d in self.doorhooks],
            "tracks": [t.serialize() for t in self.tracks],
            "obstacles": [o.serialize() for o in self.obstacles],
        }


class LYTRoom(ComparableMixin):
    """Represents a single room (area model) in a LYT layout.
    
    Rooms are the basic building blocks of area geometry. Each room references
    an MDL model file that contains the 3D geometry for a portion of the area.
    Rooms are positioned in 3D space and can be connected to other rooms for
    area transitions and pathfinding.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/interface/resource/ILayoutRoom.ts:13-16


        
    Attributes:
    ----------
        model: ResRef name of the room model (MDL file)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:69 (name: params[0])
            Stored as lowercase for case-insensitive comparison
            Must be valid ResRef (max 16 chars, no spaces)
            Corresponds to MDL/MDX/WOK files (e.g., "room001")
            
        position: 3D position of the room in world space (x, y, z)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:70 (position Vector3)
            Defines where the room model is placed in the area
            Used by game engine to position room geometry
            
        connections: Set of other rooms this room connects to
            PyKotor-specific field for tracking room connectivity
            Used for pathfinding and area transition logic
            Not present in binary/ASCII format (derived from door hooks)
    """

    COMPARABLE_FIELDS = ("model", "position")

    def __init__(self, model: str, position: Vector3):
        
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:69
        
        # ResRef name of room model (MDL file)
        self.model: str = model
        
        
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:70
        
        # 3D position in world space (x, y, z)
        self.position: Vector3 = position
        
        # PyKotor-specific: Set of connected rooms (for pathfinding)
        self.connections: set[LYTRoom] = set()

    def __add__(self, other: LYTRoom) -> LYTRoom:
        """Merge this room with another room using the + operator."""
        new_position = (self.position + other.position) * 0.5
        new_room = LYTRoom(f"{self.model}_{other.model}", new_position)
        new_room.connections = self.connections.union(other.connections)
        return new_room

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTRoom):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))

    def add_connection(self, room: LYTRoom) -> None:
        """Add a connection to another room."""
        if room not in self.connections:
            self.connections.add(room)

    def remove_connection(self, room: LYTRoom) -> None:
        """Remove a connection to another room."""
        if room in self.connections:
            self.connections.discard(room)

    def serialize(self) -> dict[str, Any]:
        """Serialize an LYTRoom to JSON-compatible dict."""
        return {
            "model": self.model,
            "position": self.position.serialize(),
        }


class LYTTrack(ComparableMixin):
    """Represents a swoop track booster element in a LYT layout.
    
    Tracks are used in swoop racing mini-games (primarily KotOR II). Each track
    entry defines a booster element that can be placed along a racing track.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:73-77 (track parsing)


        
    Attributes:
    ----------
        model: ResRef name of the track model (MDL file)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:75 (name: params[0])
            Model file for the track booster element
            Must be valid ResRef (max 16 chars)
            
        position: 3D position of the track element (x, y, z)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:76 (position Vector3)
            Defines where the track booster is placed
            Used in swoop racing mini-games
    """

    COMPARABLE_FIELDS = ("model", "position")

    def __init__(self, model: str, position: Vector3):
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:75
        # ResRef name of track model
        self.model: str = model
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:76
        # 3D position in world space
        self.position: Vector3 = position

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTTrack):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))

    def serialize(self) -> dict[str, Any]:
        """Serialize an LYTTrack to JSON-compatible dict."""
        return {
            "model": self.model,
            "position": self.position.serialize(),
        }


class LYTObstacle(ComparableMixin):
    """Represents a swoop track obstacle element in a LYT layout.
    
    Obstacles are used in swoop racing mini-games (primarily KotOR II). Each
    obstacle entry defines a hazard element that can be placed along a racing track.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:79-83 (obstacle parsing)


        
    Attributes:
    ----------
        model: ResRef name of the obstacle model (MDL file)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:81 (name: params[0])
            Model file for the track obstacle element
            Must be valid ResRef (max 16 chars)
            
        position: 3D position of the obstacle element (x, y, z)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:82 (position Vector3)
            Defines where the track obstacle is placed
            Used in swoop racing mini-games
    """

    COMPARABLE_FIELDS = ("model", "position")

    def __init__(self, model: str, position: Vector3):
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:81
        # ResRef name of obstacle model
        self.model: str = model
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:82
        # 3D position in world space
        self.position: Vector3 = position

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTObstacle):
            return NotImplemented
        return self.model.lower() == other.model.lower() and self.position == other.position

    def __hash__(self) -> int:
        return hash((self.model.lower(), self.position))

    def serialize(self) -> dict[str, Any]:
        """Serialize an LYTObstacle to JSON-compatible dict."""
        return {
            "model": self.model,
            "position": self.position.serialize(),
        }


class LYTDoorHook(ComparableMixin):
    """Represents a door hook point in a LYT layout.
    
    Door hooks define positions where doors can be placed in rooms. Each door hook
    specifies the room it belongs to, a door name, position, and orientation. Doors
    are placed at these hook points to create area transitions and room connections.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/interface/resource/ILayoutDoorHook.ts:13-18
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:85-91 (doorhook parsing)
        ASCII Format (10 tokens):
        -----------------------
        <room_name> <door_name> <x> <y> <z> <qx> <qy> <qz> <qw> [unk1] [unk2] [unk3] [unk4] [unk5]
        Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:86-90 (7-8 values parsed)
        Note: xoreos parses 10 tokens (includes 5 unknown floats), KotOR.js parses 7-8
        
    Attributes:
    ----------
        room: Name of the room this door hook belongs to
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:87 (room: params[0])
            Room name is case-insensitive (stored lowercase)
            Must match a room name in the rooms list
            
        door: Name/identifier for this door hook
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:88 (name: params[1])
            Used to identify specific door hooks within a room
            Case-insensitive (stored lowercase)
            
        position: 3D position of the door hook (x, y, z)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:89 (position Vector3)
            Defines where the door is placed in world space
            
        orientation: Rotation quaternion for door orientation (qx, qy, qz, qw)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/LYTObject.ts:90 (quaternion Quaternion)
            Defines door rotation/orientation in world space
            Quaternion format: (x, y, z, w) components
            Note: xoreos stores 5 unknown floats (may include quaternion + extras)
    """

    COMPARABLE_FIELDS = ("room", "door", "position", "orientation")

    def __init__(self, room: str, door: str, position: Vector3, orientation: Vector4):
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:87
        # Room name this door hook belongs to (case-insensitive)
        self.room: str = room
        
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:88
        # Door hook name/identifier (case-insensitive)
        self.door: str = door
        
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:89
        # 3D position in world space
        self.position: Vector3 = position
        
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/LYTObject.ts:90
        
        # Rotation quaternion (qx, qy, qz, qw)
        self.orientation: Vector4 = orientation

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LYTDoorHook):
            return NotImplemented
        return (
            self.room == other.room
            and self.door == other.door
            and self.position == other.position
            and self.orientation == other.orientation
        )

    def __hash__(self) -> int:
        return hash((self.room, self.door, self.position, self.orientation))

    def serialize(self) -> dict[str, Any]:
        """Serialize an LYTDoorHook to JSON-compatible dict."""
        return {
            "room": self.room,
            "door": self.door,
            "position": self.position.serialize(),
            "orientation": self.orientation.serialize(),
        }
