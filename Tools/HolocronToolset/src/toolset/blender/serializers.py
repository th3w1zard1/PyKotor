"""Serializers for converting PyKotor data structures to JSON for IPC.

This module handles serialization of:
- GIT instances (creatures, placeables, doors, etc.)
- LYT layout data (rooms, doorhooks, tracks, obstacles)
- Module data
- Walkmesh data
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.generics.git import (  # pyright: ignore[reportMissingImports]
        GIT,
        GITInstance,
    )
    from utility.common.geometry import Vector3, Vector4
    from pykotor.common.indoormap import IndoorMap, IndoorMapRoom


def serialize_vector3(v: Vector3) -> dict[str, float]:
    """Serialize a Vector3 to JSON-compatible dict.
    
    Deprecated: Use v.serialize() instead.
    """
    return v.serialize()


def serialize_vector4(v: Vector4) -> dict[str, float]:
    """Serialize a Vector4 (quaternion) to JSON-compatible dict.
    
    Deprecated: Use v.serialize() instead.
    """
    return v.serialize()


def deserialize_vector3(data: dict[str, float]) -> tuple[float, float, float]:
    """Deserialize a Vector3 from JSON dict."""
    return (data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))


def deserialize_vector4(data: dict[str, float]) -> tuple[float, float, float, float]:
    """Deserialize a Vector4 from JSON dict."""
    return (data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0), data.get("w", 1.0))


# =============================================================================
# GIT Instance Serialization
# =============================================================================


def serialize_git_instance(instance: GITInstance) -> dict[str, Any]:
    """Serialize a GITInstance to JSON-compatible dict.

    Args:
        instance: Any GITInstance subclass

    Returns:
        Dictionary representation suitable for JSON serialization
    
    Deprecated: Use instance.serialize() instead.
    """
    return instance.serialize()


def deserialize_git_instance(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize GIT instance data from JSON.

    This returns a dictionary that can be used to update a GITInstance.
    The actual instance creation/update is handled by the caller.

    Args:
        data: Serialized instance data

    Returns:
        Dictionary with instance properties
    """
    result: dict[str, Any] = {
        "type": data.get("type", ""),
        "position": deserialize_vector3(data.get("position", {})),
    }

    instance_type = data.get("type", "")

    if instance_type == "GITCamera":
        result.update({
            "camera_id": data.get("camera_id", 0),
            "orientation": deserialize_vector4(data.get("orientation", {})),
            "fov": data.get("fov", 55.0),
            "height": data.get("height", 0.0),
            "mic_range": data.get("mic_range", 0.0),
            "pitch": data.get("pitch", 0.0),
        })
    elif instance_type in ("GITCreature", "GITPlaceable", "GITStore"):
        result.update({
            "resref": data.get("resref", ""),
            "bearing": data.get("bearing", 0.0),
        })
        if instance_type == "GITPlaceable":
            result["tweak_color"] = data.get("tweak_color")
    elif instance_type == "GITDoor":
        result.update({
            "resref": data.get("resref", ""),
            "bearing": data.get("bearing", 0.0),
            "tag": data.get("tag", ""),
            "linked_to_module": data.get("linked_to_module", ""),
            "linked_to": data.get("linked_to", ""),
            "linked_to_flags": data.get("linked_to_flags", 0),
            "transition_destination_stringref": data.get("transition_destination_stringref", -1),
        })
    elif instance_type == "GITSound":
        result["resref"] = data.get("resref", "")
    elif instance_type in ("GITEncounter", "GITTrigger"):
        result.update({
            "resref": data.get("resref", ""),
            "geometry": [deserialize_vector3(g) for g in data.get("geometry", [])],
        })
        if instance_type == "GITTrigger":
            result.update({
                "tag": data.get("tag", ""),
                "linked_to_module": data.get("linked_to_module", ""),
                "linked_to": data.get("linked_to", ""),
                "linked_to_flags": data.get("linked_to_flags", 0),
                "transition_destination_stringref": data.get("transition_destination_stringref", -1),
            })
        else:
            result["spawn_points"] = data.get("spawn_points", [])
    elif instance_type == "GITWaypoint":
        result.update({
            "resref": data.get("resref", ""),
            "bearing": data.get("bearing", 0.0),
            "tag": data.get("tag", ""),
            "name_stringref": data.get("name_stringref", -1),
            "map_note_enabled": data.get("map_note_enabled", False),
            "has_map_note": data.get("has_map_note", False),
        })

    return result


# =============================================================================
# GIT Serialization
# =============================================================================


def serialize_git(git: GIT) -> dict[str, Any]:
    """Serialize a complete GIT to JSON-compatible dict.

    Args:
        git: GIT resource

    Returns:
        Dictionary representation
    
    Deprecated: Use git.serialize() instead.
    """
    return git.serialize()


# =============================================================================
# LYT Serialization
# =============================================================================


def serialize_lyt_room(room: LYTRoom) -> dict[str, Any]:
    """Serialize an LYTRoom to JSON-compatible dict.
    
    Deprecated: Use room.serialize() instead.
    """
    return room.serialize()


def serialize_lyt_doorhook(doorhook: LYTDoorHook) -> dict[str, Any]:
    """Serialize an LYTDoorHook to JSON-compatible dict.
    
    Deprecated: Use doorhook.serialize() instead.
    """
    return doorhook.serialize()


def serialize_lyt_track(track: LYTTrack) -> dict[str, Any]:
    """Serialize an LYTTrack to JSON-compatible dict.
    
    Deprecated: Use track.serialize() instead.
    """
    return track.serialize()


def serialize_lyt_obstacle(obstacle: LYTObstacle) -> dict[str, Any]:
    """Serialize an LYTObstacle to JSON-compatible dict.
    
    Deprecated: Use obstacle.serialize() instead.
    """
    return obstacle.serialize()


def serialize_lyt(lyt: LYT) -> dict[str, Any]:
    """Serialize a complete LYT to JSON-compatible dict.

    Args:
        lyt: LYT resource

    Returns:
        Dictionary representation
    
    Deprecated: Use lyt.serialize() instead.
    """
    return lyt.serialize()


def deserialize_lyt_room(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize LYTRoom data."""
    return {
        "model": data.get("model", ""),
        "position": deserialize_vector3(data.get("position", {})),
    }


def deserialize_lyt_doorhook(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize LYTDoorHook data."""
    return {
        "room": data.get("room", ""),
        "door": data.get("door", ""),
        "position": deserialize_vector3(data.get("position", {})),
        "orientation": deserialize_vector4(data.get("orientation", {})),
    }


def deserialize_lyt(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize LYT data from JSON."""
    return {
        "rooms": [deserialize_lyt_room(r) for r in data.get("rooms", [])],
        "doorhooks": [deserialize_lyt_doorhook(d) for d in data.get("doorhooks", [])],
        "tracks": [deserialize_track(t) for t in data.get("tracks", [])],
        "obstacles": [deserialize_obstacle(o) for o in data.get("obstacles", [])],
    }


def deserialize_track(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize LYTTrack data."""
    return {
        "model": data.get("model", ""),
        "position": deserialize_vector3(data.get("position", {})),
    }


def deserialize_obstacle(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize LYTObstacle data."""
    return {
        "model": data.get("model", ""),
        "position": deserialize_vector3(data.get("position", {})),
    }


# =============================================================================
# Walkmesh Serialization
# =============================================================================


def serialize_bwm(bwm: BWM) -> dict[str, Any]:
    """Serialize a BWM walkmesh to JSON-compatible dict.

    Args:
        bwm: BWM walkmesh resource

    Returns:
        Dictionary representation
    
    Deprecated: Use bwm.serialize() instead.
    """
    return bwm.serialize()


# =============================================================================
# Module Data Serialization
# =============================================================================


def serialize_module_data(
    lyt: LYT,
    git: GIT,
    walkmeshes: list[BWM],
    module_root: str,
    installation_path: str,
) -> dict[str, Any]:
    """Serialize complete module data for Blender.

    Args:
        lyt: Layout resource
        git: GIT resource
        walkmeshes: List of walkmesh resources
        module_root: Module root name
        installation_path: Path to KotOR installation

    Returns:
        Complete module data dictionary
    """
    return {
        "module_root": module_root,
        "installation_path": installation_path,
        "lyt": lyt.serialize(),
        "git": git.serialize(),
        "walkmeshes": [w.serialize() for w in walkmeshes],
    }


# =============================================================================
# Indoor Map Serialization
# =============================================================================


def serialize_indoor_map_room(room: IndoorMapRoom) -> dict[str, Any]:
    """Serialize an IndoorMapRoom to JSON-compatible dict.
    
    Args:
        room: IndoorMapRoom instance
        
    Returns:
        Dictionary representation
    
    Deprecated: Use room.serialize() instead.
    """
    return room.serialize()


def serialize_indoor_map(indoor_map: IndoorMap) -> dict[str, Any]:
    """Serialize an IndoorMap to JSON-compatible dict.
    
    Args:
        indoor_map: IndoorMap instance
        
    Returns:
        Dictionary representation
    
    Deprecated: Use indoor_map.serialize() instead.
    """
    return indoor_map.serialize()
