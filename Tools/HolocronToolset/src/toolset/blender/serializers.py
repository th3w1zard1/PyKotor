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
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
    from pykotor.resource.generics.git import (
        GIT,
        GITCamera,
        GITCreature,
        GITDoor,
        GITEncounter,
        GITInstance,
        GITPlaceable,
        GITSound,
        GITStore,
        GITTrigger,
        GITWaypoint,
    )
    from utility.common.geometry import Vector3, Vector4


def serialize_vector3(v: Vector3) -> dict[str, float]:
    """Serialize a Vector3 to JSON-compatible dict."""
    return {"x": float(v.x), "y": float(v.y), "z": float(v.z)}


def serialize_vector4(v: Vector4) -> dict[str, float]:
    """Serialize a Vector4 (quaternion) to JSON-compatible dict."""
    return {"x": float(v.x), "y": float(v.y), "z": float(v.z), "w": float(v.w)}


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
    """
    from pykotor.resource.generics.git import (
        GITCamera,
        GITCreature,
        GITDoor,
        GITEncounter,
        GITPlaceable,
        GITSound,
        GITStore,
        GITTrigger,
        GITWaypoint,
    )

    # Base data common to all instances
    data: dict[str, Any] = {
        "type": instance.__class__.__name__,
        "position": serialize_vector3(instance.position),
        "runtime_id": id(instance),
    }

    if isinstance(instance, GITCamera):
        data.update(_serialize_camera(instance))
    elif isinstance(instance, GITCreature):
        data.update(_serialize_creature(instance))
    elif isinstance(instance, GITDoor):
        data.update(_serialize_door(instance))
    elif isinstance(instance, GITEncounter):
        data.update(_serialize_encounter(instance))
    elif isinstance(instance, GITPlaceable):
        data.update(_serialize_placeable(instance))
    elif isinstance(instance, GITSound):
        data.update(_serialize_sound(instance))
    elif isinstance(instance, GITStore):
        data.update(_serialize_store(instance))
    elif isinstance(instance, GITTrigger):
        data.update(_serialize_trigger(instance))
    elif isinstance(instance, GITWaypoint):
        data.update(_serialize_waypoint(instance))

    return data


def _serialize_camera(camera: GITCamera) -> dict[str, Any]:
    """Serialize GITCamera-specific data."""
    return {
        "camera_id": camera.camera_id,
        "orientation": serialize_vector4(camera.orientation),
        "fov": camera.fov,
        "height": camera.height,
        "mic_range": camera.mic_range,
        "pitch": camera.pitch,
    }


def _serialize_creature(creature: GITCreature) -> dict[str, Any]:
    """Serialize GITCreature-specific data."""
    return {
        "resref": str(creature.resref),
        "bearing": creature.bearing,
    }


def _serialize_door(door: GITDoor) -> dict[str, Any]:
    """Serialize GITDoor-specific data."""
    # transition_destination is a LocalizedString, not Vector3
    transition_locstring = door.transition_destination
    transition_stringref = transition_locstring.stringref if hasattr(transition_locstring, 'stringref') else -1

    return {
        "resref": str(door.resref),
        "bearing": door.bearing,
        "tag": door.tag,
        "linked_to_module": str(door.linked_to_module),
        "linked_to": door.linked_to,
        "linked_to_flags": door.linked_to_flags.value if hasattr(door.linked_to_flags, 'value') else int(door.linked_to_flags),
        "transition_destination_stringref": transition_stringref,
    }


def _serialize_encounter(encounter: GITEncounter) -> dict[str, Any]:
    """Serialize GITEncounter-specific data."""

    geometry = [serialize_vector3(v) for v in encounter.geometry]
    spawn_points = [
        {
            "position": {"x": sp.x, "y": sp.y, "z": sp.z},
            "orientation": sp.orientation,
        }
        for sp in encounter.spawn_points
    ]

    return {
        "resref": str(encounter.resref),
        "geometry": geometry,
        "spawn_points": spawn_points,
    }


def _serialize_placeable(placeable: GITPlaceable) -> dict[str, Any]:
    """Serialize GITPlaceable-specific data."""
    return {
        "resref": str(placeable.resref),
        "bearing": placeable.bearing,
        "tweak_color": placeable.tweak_color.bgr_integer() if placeable.tweak_color else None,
    }


def _serialize_sound(sound: GITSound) -> dict[str, Any]:
    """Serialize GITSound-specific data."""
    return {
        "resref": str(sound.resref),
    }


def _serialize_store(store: GITStore) -> dict[str, Any]:
    """Serialize GITStore-specific data."""
    return {
        "resref": str(store.resref),
        "bearing": store.bearing,
    }


def _serialize_trigger(trigger: GITTrigger) -> dict[str, Any]:
    """Serialize GITTrigger-specific data."""
    geometry = [serialize_vector3(v) for v in trigger.geometry]

    # transition_destination is a LocalizedString
    transition_locstring = trigger.transition_destination
    transition_stringref = transition_locstring.stringref if hasattr(transition_locstring, 'stringref') else -1

    return {
        "resref": str(trigger.resref),
        "tag": trigger.tag,
        "geometry": geometry,
        "linked_to_module": str(trigger.linked_to_module),
        "linked_to": trigger.linked_to,
        "linked_to_flags": trigger.linked_to_flags.value if hasattr(trigger.linked_to_flags, 'value') else int(trigger.linked_to_flags),
        "transition_destination_stringref": transition_stringref,
    }


def _serialize_waypoint(waypoint: GITWaypoint) -> dict[str, Any]:
    """Serialize GITWaypoint-specific data."""
    return {
        "resref": str(waypoint.resref),
        "bearing": waypoint.bearing,
        "tag": waypoint.tag,
        "name_stringref": waypoint.name.stringref,
        "map_note_enabled": waypoint.map_note_enabled,
        "has_map_note": waypoint.has_map_note,
    }


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
    """
    return {
        "creatures": [serialize_git_instance(c) for c in git.creatures],
        "doors": [serialize_git_instance(d) for d in git.doors],
        "placeables": [serialize_git_instance(p) for p in git.placeables],
        "waypoints": [serialize_git_instance(w) for w in git.waypoints],
        "triggers": [serialize_git_instance(t) for t in git.triggers],
        "encounters": [serialize_git_instance(e) for e in git.encounters],
        "sounds": [serialize_git_instance(s) for s in git.sounds],
        "stores": [serialize_git_instance(s) for s in git.stores],
        "cameras": [serialize_git_instance(c) for c in git.cameras],
    }


# =============================================================================
# LYT Serialization
# =============================================================================


def serialize_lyt_room(room: LYTRoom) -> dict[str, Any]:
    """Serialize an LYTRoom to JSON-compatible dict."""
    return {
        "model": room.model,
        "position": serialize_vector3(room.position),
    }


def serialize_lyt_doorhook(doorhook: LYTDoorHook) -> dict[str, Any]:
    """Serialize an LYTDoorHook to JSON-compatible dict."""
    return {
        "room": doorhook.room,
        "door": doorhook.door,
        "position": serialize_vector3(doorhook.position),
        "orientation": serialize_vector4(doorhook.orientation),
    }


def serialize_lyt_track(track: LYTTrack) -> dict[str, Any]:
    """Serialize an LYTTrack to JSON-compatible dict."""
    return {
        "model": track.model,
        "position": serialize_vector3(track.position),
    }


def serialize_lyt_obstacle(obstacle: LYTObstacle) -> dict[str, Any]:
    """Serialize an LYTObstacle to JSON-compatible dict."""
    return {
        "model": obstacle.model,
        "position": serialize_vector3(obstacle.position),
    }


def serialize_lyt(lyt: LYT) -> dict[str, Any]:
    """Serialize a complete LYT to JSON-compatible dict.

    Args:
        lyt: LYT resource

    Returns:
        Dictionary representation
    """
    return {
        "rooms": [serialize_lyt_room(r) for r in lyt.rooms],
        "doorhooks": [serialize_lyt_doorhook(d) for d in lyt.doorhooks],
        "tracks": [serialize_lyt_track(t) for t in lyt.tracks],
        "obstacles": [serialize_lyt_obstacle(o) for o in lyt.obstacles],
    }


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
        "tracks": [{"model": t.get("model", ""), "position": deserialize_vector3(t.get("position", {}))} for t in data.get("tracks", [])],
        "obstacles": [{"model": o.get("model", ""), "position": deserialize_vector3(o.get("position", {}))} for o in data.get("obstacles", [])],
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
    """
    vertices = [serialize_vector3(v) for v in bwm.vertices()]

    faces = []
    for face in bwm.faces:
        faces.append({
            "v1": {"x": face.v1.x, "y": face.v1.y, "z": face.v1.z},
            "v2": {"x": face.v2.x, "y": face.v2.y, "z": face.v2.z},
            "v3": {"x": face.v3.x, "y": face.v3.y, "z": face.v3.z},
            "material": face.material.value if hasattr(face.material, "value") else int(face.material),
            "trans1": face.trans1,
            "trans2": face.trans2,
            "trans3": face.trans3,
        })

    return {
        "walkmesh_type": bwm.walkmesh_type.value if hasattr(bwm.walkmesh_type, "value") else int(bwm.walkmesh_type),
        "vertices": vertices,
        "faces": faces,
    }


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
        "lyt": serialize_lyt(lyt),
        "git": serialize_git(git),
        "walkmeshes": [serialize_bwm(w) for w in walkmeshes],
    }

