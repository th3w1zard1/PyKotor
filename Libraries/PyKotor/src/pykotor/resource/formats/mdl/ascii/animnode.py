# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
from __future__ import annotations

import collections
import re

from contextlib import suppress
from typing import Any, Callable, ClassVar

import bpy

from typing_extensions import Literal

from mdl.ascii import parse
from pykotor.resource.formats.mdl.mdl_data import CONST_MDL_ANIMATION_FPS, MDLAnimation, get_action, str2identifier
from utility.misc import is_int


class Keys:
    def __init__(self):
        self.position       = []
        self.orientation    = []
        self.scale          = []
        self.selfillumcolor = []
        self.alpha          = []
        # Lights
        self.color  = []
        self.radius = []
        # Emitters
        self.alphastart = []
        self.alphamid = []
        self.alphaend = []
        self.birthrate = []
        self.m_frandombirthrate = []
        self.bounce_co = []
        self.combinetime = []
        self.drag = []
        self.fps = []
        self.frameend = []
        self.framestart = []
        self.grav = []
        self.lifeexp = []
        self.mass = []
        self.p2p_bezier2 = []
        self.p2p_bezier3 = []
        self.particlerot = []
        self.randvel = []
        self.sizestart = []
        self.sizemid = []
        self.sizeend = []
        self.sizestart_y = []
        self.sizemid_y = []
        self.sizeend_y = []
        self.spread = []
        self.threshold = []
        self.velocity = []
        self.xsize = []
        self.ysize = []
        self.blurlength = []
        self.lightningdelay = []
        self.lightningradius = []
        self.lightningsubdiv = []
        self.lightningscale = []
        self.lightningzigzag = []
        self.percentstart = []
        self.percentmid = []
        self.percentend = []
        self.targetsize = []
        self.numcontrolpts = []
        self.controlptradius = []
        self.controlptdelay = []
        self.tangentspread = []
        self.tangentlength = []
        self.colorstart = []
        self.colormid = []
        self.colorend = []
        # Unknown. Import as text
        self.rawascii: str = ""

    def has_alpha(self) -> bool:
        return len(self.alpha) > 0


class Node:
    KEY_TYPE: ClassVar[dict[str, dict[str, Any]]] = {
        "position": {
            "values": 3,
            "axes": 3,
            "objdata": "location",
        },
        "orientation": {
            "values": 4,
            "axes": 4,
            "objdata": "rotation_quaternion",
        },
        "scale": {
            "values": 1,
            "axes": 3,
            "objdata": "scale",
        },
        "alpha": {
            "values": 1,
            "axes": 1,
            "objdata": "kb.alpha",
        },
        "selfillumcolor": {
            "values": 3,
            "axes": 3,
            "objdata": "kb.selfillumcolor",
        },
        "color": {
            "values": 3,
            "axes": 3,
            "objdata": "color",
        },
        "radius": {
            "values": 1,
            "axes": 1,
            "objdata": "distance",
        },
    }
    EMITTER_KEY_TYPE: ClassVar[dict[str, dict[str, Any]]] = {
        "alphaStart": {
            "values": 1,
            "axes": 1,
        },
        "alphaMid": {
            "values": 1,
            "axes": 1,
        },
        "alphaEnd": {
            "values": 1,
            "axes": 1,
        },
        "birthrate": {
            "values": 1,
            "axes": 1,
            "conversion": float,
        },
        "m_fRandomBirthRate": {
            "values": 1,
            "axes": 1,
            "conversion": float,
        },
        "bounce_co": {
            "values": 1,
            "axes": 1,
        },
        "combinetime": {
            "values": 1,
            "axes": 1,
        },
        "drag": {
            "values": 1,
            "axes": 1,
        },
        "fps": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "frameEnd": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "frameStart": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "grav": {
            "values": 1,
            "axes": 1,
        },
        "lifeExp": {
            "values": 1,
            "axes": 1,
        },
        "mass": {
            "values": 1,
            "axes": 1,
        },
        "p2p_bezier2": {
            "values": 1,
            "axes": 1,
        },
        "p2p_bezier3": {
            "values": 1,
            "axes": 1,
        },
        "particleRot": {
            "values": 1,
            "axes": 1,
        },
        "randvel": {
            "values": 1,
            "axes": 1,
        },
        "sizeStart": {
            "values": 1,
            "axes": 1,
        },
        "sizeMid": {
            "values": 1,
            "axes": 1,
        },
        "sizeEnd": {
            "values": 1,
            "axes": 1,
        },
        "sizeStart_y": {
            "values": 1,
            "axes": 1,
        },
        "sizeMid_y": {
            "values": 1,
            "axes": 1,
        },
        "sizeEnd_y": {
            "values": 1,
            "axes": 1,
        },
        "spread": {
            "values": 1,
            "axes": 1,
        },
        "threshold": {
            "values": 1,
            "axes": 1,
        },
        "velocity": {
            "values": 1,
            "axes": 1,
        },
        "xsize": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "ysize": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "blurlength": {
            "values": 1,
            "axes": 1,
        },
        "lightningDelay": {
            "values": 1,
            "axes": 1,
        },
        "lightningRadius": {
            "values": 1,
            "axes": 1,
        },
        "lightningSubDiv": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "lightningScale": {
            "values": 1,
            "axes": 1,
        },
        "lightningzigzag": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "percentStart": {
            "values": 1,
            "axes": 1,
        },
        "percentMid": {
            "values": 1,
            "axes": 1,
        },
        "percentEnd": {
            "values": 1,
            "axes": 1,
        },
        "targetsize": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "numcontrolpts": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "controlptradius": {
            "values": 1,
            "axes": 1,
        },
        "controlptdelay": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "tangentspread": {
            "values": 1,
            "axes": 1,
            "conversion": int,
        },
        "tangentlength": {
            "values": 1,
            "axes": 1,
        },
        "colorStart": {
            "values": 3,
            "axes": 3,
        },
        "colorMid": {
            "values": 3,
            "axes": 3,
        },
        "colorEnd": {
            "values": 3,
            "axes": 3,
        },
    }

    def __init__(self, name = "UNNAMED"):
        self.name       = name
        self.nodetype   = "dummy"
        self.parentName = "NULL"

        # Keyed
        self.keys = Keys()

        self.isEmpty = True

    def __bool__(self):
        """Return false if the node is empty, i.e. it has no anims attached."""
        return not self.isEmpty

    def requires_unique_data(self):
        return self.keys.has_alpha()

    def parse_keys_9f(self, ascii_block: str, key_list: list):
        """Parse animation keys containing 9 floats (not counting the time value)."""
        parse._f(ascii_block, key_list, 10)
        self.isEmpty = False

    def parse_keys_3f(self, ascii_block: str, key_list: list):
        """Parse animation keys containing 3 floats (not counting the time value)."""
        parse.f4(ascii_block, key_list)
        self.isEmpty = False

    def parse_keys_4f(self, ascii_block: str, key_list: str):
        """Parse animation keys containing 4 floats (not counting the time value)."""
        parse.f5(ascii_block, key_list)
        self.isEmpty = False

    def parse_keys_1f(self, ascii_block: str, key_list: list):
        """Parse animation keys containing 1 float (not counting the time value)."""
        parse.f2(ascii_block, key_list)
        self.isEmpty = False

    def parse_keys_incompat(self, ascii_block: str):
        """Parse animation keys incompatible with blender. They will be saved
        as plain text.
        """
        for line in ascii_block:
            self.keys.rawascii = self.keys.rawascii + "\n" + " ".join(line)
        self.isEmpty = False

    @staticmethod
    def find_end(asciiBlock):
        """We don't know when a list of keys of keys will end. We'll have to
        search for the first non-numeric value.
        """
        return next(
            (i for i, v in enumerate(asciiBlock) if len(v) and not is_int(v[0])),
            -1,
        )

    def load_ascii(self, ascii_block: str):
        for idx, line in enumerate(ascii_block):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if label == "node":
                self.nodeType = line[1].lower()
                self.name = line[2]
            elif label == "endnode":
                return
            elif label == "endlist":
                # Can't rely on that being here. We have our own way to get
                # the end of a key list
                pass
            elif label == "parent":
                self.parentName = line[1]
            elif (
                label in self.KEY_TYPE
                or label in (f"{attr}key" for attr in self.KEY_TYPE)
                or label in (f"{attr}bezierkey" for attr in self.KEY_TYPE)
            ):
                # Parse all controllers: unkeyed, keyed, or bezierkeyed
                attrname = next(attr for attr in self.KEY_TYPE if label.startswith(attr))
                attr_type = self.KEY_TYPE[attrname]
                key_type = ""
                key_type = "key" if label.endswith("key") else key_type
                key_type = "bezierkey" if label.endswith("bezierkey") else key_type
                numVals = attr_type["values"]
                if key_type:
                    if key_type == "bezierkey":
                        numVals *= 3
                    numKeys = type(self).find_end(ascii_block[idx+1:])
                    subblock = ascii_block[idx+1:idx+numKeys+1]
                else:
                    numKeys = 1
                    subblock = [[0.0] + line[1:]]
                # parse numvals plus one for time
                parse._f(subblock, getattr(self.keys, attrname), numVals + 1)
                self.isEmpty = False
            elif (
                label in (attr.lower() for attr in self.EMITTER_KEY_TYPE)
                or label in (f"{attr.lower()}key" for attr in self.EMITTER_KEY_TYPE)
                or label in (f"{attr.lower()}bezierkey" for attr in self.EMITTER_KEY_TYPE)
            ):
                # Parse all controllers: unkeyed, keyed, or bezierkeyed
                attrname = next(attr for attr in self.EMITTER_KEY_TYPE if attr.lower() in label)
                propname = attrname.lower()
                attr_type = self.EMITTER_KEY_TYPE[attrname]
                key_type = ""
                key_type = "key" if label.endswith("key") else key_type
                key_type = "bezierkey" if label.endswith("bezierkey") else key_type
                numVals = attr_type["values"]
                if key_type:
                    if key_type == "bezierkey":
                        numVals *= 3
                    numKeys = type(self).find_end(ascii_block[idx+1:])
                    subblock = ascii_block[idx+1:idx+numKeys+1]
                else:
                    numKeys = 1
                    subblock = [[0.0] + line[1:]]
                # parse numvals plus one for time
                if "conversion" in attr_type and attr_type["conversion"] is int:
                    parse._i(subblock, getattr(self.keys, propname), numVals + 1)
                else:
                    parse._f(subblock, getattr(self.keys, propname), numVals + 1)
                self.isEmpty = False
            elif not is_int(line[0]):
                numKeys = type(self).find_end(ascii_block[idx+1:])
                if numKeys:
                    self.parse_keys_incompat(ascii_block[idx:idx+numKeys+1])
                    self.isEmpty = False

    @staticmethod
    def get_keys_from_action(
        anim: MDLAnimation,
        action,
        key_dict: dict[str, Any],
    ):
        for fcurve in action.fcurves:
            # Get the sub dict for this particlar type of fcurve
            axis     = fcurve.array_index
            dataPath = fcurve.data_path
            name     = ""
            for keyname in Node.KEY_TYPE:
                ktype = Node.KEY_TYPE[keyname]
                if ktype["objdata"] is not None and \
                   dataPath == ktype["objdata"]:
                    name = keyname + "key"
                    break
            for keyname in Node.EMITTER_KEY_TYPE:
                if dataPath == "kb." + keyname.lower():
                    ktype = Node.EMITTER_KEY_TYPE[keyname]
                    name = keyname + "key"
                    break

            # does this fcurve have points in this animation?
            # if not, skip it
            if not len([
                kfp for kfp in fcurve.keyframe_points \
                if kfp.co[0] >= anim.frameStart and kfp.co[0] <= anim.frameEnd
            ]):
                continue

            for kfp in fcurve.keyframe_points:
                if name.startswith("orientation"):
                    # bezier keyed orientation animation currently unsupported
                    break
                if kfp.interpolation == "BEZIER":
                    name = re.sub(r"^(.+)key$", r"\1bezierkey", name)
                    break

            for kfkey, kfp in enumerate(fcurve.keyframe_points):
                frame = int(round(kfp.co[0]))
                if frame < anim.frameStart or frame > anim.frameEnd:
                    continue
                if name not in key_dict:
                    key_dict[name] = collections.OrderedDict()
                keys  = key_dict[name]
                values = keys.get(frame, [0.0, 0.0, 0.0, 0.0])
                values[axis] = values[axis] + kfp.co[1]
                if name.endswith("bezierkey"):
                    if kfp.interpolation == "BEZIER":
                        values[ktype["axes"] + (axis * 2) : (ktype["axes"] + 1) + (axis * 2)] = [
                            kfp.handle_left[1] - kfp.co[1],
                            kfp.handle_right[1] - kfp.co[1],
                        ]
                    elif kfp.interpolation == "LINEAR":
                        # do the linear emulation,
                        # distance between keyframes / 3 point on linear interpolation @ frame
                        # y = y0 + ((x - x0) * ((y1 - y0)/(x1 - x0)))
                        # right handle is on the segment controlled by this keyframe
                        if kfkey < len(fcurve.keyframe_points) - 1:
                            next_kfp = fcurve.keyframe_points[kfkey + 1]
                            next_frame = int(round((next_kfp.co[0] - kfp.co[0]) / 3.0))
                            right_handle = kfp.co[1] + (
                                (next_frame - frame)
                                * ((next_kfp.co[1] - kfp.co[1]) / (next_kfp.co[0] - kfp.co[0]))
                            )
                            # make exported right handle value relative to keyframe value:
                            right_handle = right_handle - kfp.co[1]
                        else:
                            right_handle = 0.0
                        # left handle is on the segment controlled by the previous keyframe
                        if kfkey > 0 and fcurve.keyframe_points[kfkey - 1].interpolation == "LINEAR":
                            prev_kfp = fcurve.keyframe_points[kfkey - 1]
                            prev_frame = int(round((kfp.co[0] - prev_kfp.co[0]) / 3.0))
                            left_handle = prev_kfp.co[1] + (
                                (prev_frame - prev_kfp.co[0])
                                * ((kfp.co[1] - prev_kfp.co[1]) / (kfp.co[0] - prev_kfp.co[0]))
                            )
                            # make exported left handle value relative to keyframe value:
                            left_handle = left_handle - kfp.co[1]
                        elif kfkey > 0 and kfp.handle_left and kfp.handle_left[1]:
                            left_handle = kfp.handle_left[1] - kfp.co[1]
                        else:
                            left_handle = 0.0
                        values[ktype["axes"] + (axis * 2) : (ktype["axes"] + 1) + (axis * 2)] = [
                            left_handle,
                            right_handle,
                        ]
                    else:
                        # somebody mixed an unknown keyframe type ...
                        # give them some bad data
                        values[ktype["axes"] + (axis * 2):(ktype["axes"] + 1) + (axis * 2)] = [ 0.0, 0.0 ]
                keys[frame] = values

    def add_keys_to_ascii_incompat(
        self,
        obj,
        ascii_lines: list[list[str] | str],
    ):
        return Node.generate_ascii_keys_incompat(obj, ascii_lines)

    @staticmethod
    def generate_ascii_keys_incompat(
        obj,
        ascii_lines: list[list[str] | str],
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        if obj.kb.rawascii not in bpy.data.texts:
            return
        txt      = bpy.data.texts[obj.kb.rawascii]
        txtLines = [l.split() for l in txt.as_string().split("\n")]
        for line in txtLines:
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if label not in ("node", "endnode", "parent", "position") and label[0] != "#":
                if is_int(label):
                    ascii_lines.append("      " + " ".join(line))
                else:
                    ascii_lines.append("    " + " ".join(line))

    @staticmethod
    def generate_ascii_keys(
        anim_obj,
        anim: MDLAnimation,
        ascii_lines: list[list[str] | str],
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        keyDict: dict[str, list[int, str]] = {}

        # Object Data
        if anim_obj.animation_data:
            action = anim_obj.animation_data.action
            if action:
                Node.get_keys_from_action(anim, action, keyDict)

        # Light Data
        if anim_obj.data and anim_obj.data.animation_data:
            action = anim_obj.data.animation_data.action
            if action:
                Node.get_keys_from_action(anim, action, keyDict)

        for attrname in Node.KEY_TYPE:
            bez_name = f"{attrname}bezierkey"
            key_name = f"{attrname}key"
            if not keyDict.get(bez_name) and not keyDict.get(key_name):
                continue

            ktype = Node.KEY_TYPE[attrname]
            # using a bezierkey
            if bez_name in keyDict and len(keyDict[bez_name]):
                key_name = bez_name
            ascii_lines.append(f"    {key_name} {len(keyDict[key_name])!s}")

            for frame, key in keyDict[key_name].items():
                parsed_key = key
                # convert raw frame number to animation-relative time
                time = round(round((frame - anim.frameStart) / CONST_MDL_ANIMATION_FPS, 7), 5)
                # orientation value conversion
                if key_name.startswith("orientation"):
                    parsed_key = utils.quat2nwangle(parsed_key[:4])
                # export title and
                line = "      {: .7g}" + (" {: .7g}" * ktype["values"])
                s = line.format(time, *parsed_key[:ktype["values"]])
                # export bezierkey control points
                if key_name == bez_name:
                    # left control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*parsed_key[ktype["axes"]::2])
                    # right control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*parsed_key[ktype["axes"] + 1::2])
                ascii_lines.append(s)

        for attrname in Node.EMITTER_KEY_TYPE:
            bez_name = f"{attrname}bezierkey"
            key_name = f"{attrname}key"
            if not keyDict.get(bez_name) and not keyDict.get(key_name):
                continue

            ktype = Node.EMITTER_KEY_TYPE[attrname]
            # using a bezierkey
            if bez_name in keyDict and len(keyDict[bez_name]):
                key_name = bez_name
            ascii_lines.append(f"    {key_name} {len(keyDict[key_name])!s}")
            for frame, key in keyDict[key_name].items():
                # convert raw frame number to animation-relative time
                time = round(round((frame - anim.frameStart) / CONST_MDL_ANIMATION_FPS, 7), 5)
                # orientation value conversion
                # export title and
                value_str = " {: .7g}"
                if "conversion" in ktype and ktype["conversion"] is int:
                    value_str = " {: d}"
                    key[:ktype["values"]] = [int(k) for k in key[:ktype["values"]]]
                line = "      {: .7g}" + (value_str * ktype["values"])
                s = line.format(time, *key[:ktype["values"]])
                # export bezierkey control points
                if key_name == bez_name:
                    # left control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*key[ktype["axes"]::2])
                    # right control point(s)
                    s += (" {: .7g}" * ktype["values"]).format(*key[ktype["axes"] + 1::2])
                ascii_lines.append(s)

    @staticmethod
    def get_original_name(node_name: str, anim_name: str) -> str:
        """A bit messy due to compatibility concerns."""
        if node_name.endswith(anim_name):
            orig = node_name[:len(node_name)-len(anim_name)]
            if orig.endswith("."):
                orig = orig[:-1]
            return orig

        # Try to separate the name by the first '.'
        # This is unsafe, but we have no choice if we want to maintain some
        # flexibility. It will be up to the user to name the object properly
        orig = node_name.partition(".")[0]
        return orig or node_name

    @staticmethod
    def export_needed(anim_obj, anim: MDLAnimation) -> bool:
        """Test whether this node should be included in exported ASCII model."""
        # this is the root node, must be included
        if anim_obj.parent is None:
            return True

        # test for object controllers, loc/rot/scale/selfillum
        objects: list = [anim_obj]
        with suppress(Exception):
            # this is for light controllers, radius/color:
            if anim_obj.data:
                objects.append(anim_obj.data)
            # this is for secondary obj controller, alpha:
            if anim_obj.active_material:
                objects.append(anim_obj.active_material)

        # test the found objects for animation controllers
        for obj in objects:
            if (
                obj.animation_data
                and obj.animation_data.action
                and obj.animation_data.action.fcurves
                and MDLAnimation.has_keyframes_in_range(
                    obj.animation_data.action.fcurves.keyframe_points,
                    anim.frameStart,
                    anim.frameEnd,
                )
            ):
                # this node has animation controllers, include it
                # FIXME: match actual controllers sometime
                # (current will match ANY animation)
                return True

        # if any children of this node will be included, this node must be
        for child in anim_obj.children:
            if Node.export_needed(child, anim):
                print(f"export_needed as parent for {anim_obj.name}")
                return True

        # no reason to include this node
        return False

    def to_ascii(
        self,
        anim_obj,
        ascii_lines: list[str | list[str]],
        anim_name: str,
    ):
        original_name: str = Node.get_original_name(anim_obj.name, anim_name)
        original_obj  = bpy.data.objects[original_name]

        # test whether this node should be exported,
        # previous behavior was to export all nodes for all animations
        if not Node.export_needed(anim_obj):  # FIXME: needs MDLAnimation argument?
            return

        originalParent = "NULL"
        if anim_obj.parent:
            originalParent = Node.get_original_name(anim_obj.parent.name, anim_name)

        if original_obj.kb.meshtype == "emitter":
            ascii_lines.append(f"  node emitter {original_name}")
        else:
            ascii_lines.append(f"  node dummy {original_name}")
        ascii_lines.append(f"    parent {originalParent}")
        self.add_keys_to_ascii(anim_obj, original_obj, ascii_lines)
        self.add_keys_to_ascii_incompat(anim_obj, ascii_lines)
        ascii_lines.append("  endnode")


class Animnode:
    def __init__(self, name: str = "UNNAMED"):
        self.nodeidx: int = -1
        self.nodetype: Literal["dummy", "emitter"] = "dummy"
        self.name: str = name
        self.parent: str = "NULL"

        self.emitter_data: dict = {}
        self.object_data: dict[str, tuple[list[list[float]], str, int]] = {}

    def __bool__(self):
        """Return false if the node is empty, i.e. no anims attached."""
        return bool(self.object_data or self.emitter_data)

    @staticmethod
    def insert_kfp(
        frames: list,
        values: list | list[list],
        action,
        dp: str,
        dp_dim: int,
        action_group: str | None = None,
    ):
        if not frames or not values:
            return

        fcu = []
        kfp_list = []
        for i in range(dp_dim):
            sm = MDLAnimation.get_fcurve(action, dp, i, action_group)
            fcu.append(sm)
            kfp_list.append(sm.keyframe_points)

        kfp_cnt = []
        for x in kfp_list:
            kfp_cnt.append(len(x))
            x.add(len(values))

        for i, (frm, val) in enumerate(zip(frames, values)):
            for d in range(dp_dim):
                p = kfp_list[d][kfp_cnt[d]+i]
                p.co = frm, val[d]
                p.interpolation = "LINEAR"
                # could do len == dp_dim * 3...
                if len(val) <= dp_dim:
                    continue

                p.interpolation = "BEZIER"
                p.handle_left_type = "FREE"
                p.handle_right_type = "FREE"
                # initialize left and right handle x positions
                h_left_frame = frm - CONST_MDL_ANIMATION_FPS
                h_right_frame = frm + CONST_MDL_ANIMATION_FPS
                # adjust handle x positions based on previous/next keyframes
                if i > 0:
                    p_left = frames[i - 1]
                    print(f" left {p_left} frm {frm}")
                    # place 1/3 into the distance from current keyframe
                    # to previous keyframe
                    h_left_frame = frm - ((frm - p_left) / 3.0)
                if i < len(values) - 1:
                    p_right = frames[i + 1]
                    print(f"right {p_right} frm {frm}")
                    # place 1/3 into the distance from current keyframe
                    # to next keyframe
                    h_right_frame = frm + ((p_right - frm) / 3.0)

                # set bezier handle positions,
                # y values are relative, so added to initial value
                p.handle_left[:] = [
                    h_left_frame,
                    val[d + dp_dim] + val[d]
                ]
                p.handle_right[:] = [
                    h_right_frame,
                    val[d + (2 * dp_dim)] + val[d]
                ]

        for c in fcu:
            c.update()

    def load_ascii(
        self,
        ascii_lines: list[list[str] | str],
        nodeidx: int = -1,
    ):
        self.nodeidx = nodeidx
        key_data = {}
        for i, line in enumerate(ascii_lines):
            try:
                label = line[0].lower()
            except (IndexError, AttributeError):  # noqa: S112
                continue  # Probably empty line, skip it
            else:
                if is_int(label):
                    continue

            if label == "node":
                self.nodetype = line[1].lower()
                self.name = str2identifier(line[2])
            elif label == "endnode":
                return
            elif label == "parent":
                self.parentName = str2identifier(line[1])
            else:
                # Check for keys
                key_name: str = label
                key_type: Literal["key", "bezierkey", ""] = ""
                if key_name.endswith("key"):
                    key_name = key_name[:-3]
                    key_type = "key"
                if key_name.endswith("bezier"):
                    key_name = key_name[:-6]
                    key_type = "bezierkey"

                if (
                    key_name in Node.KEY_TYPE
                    or key_name in [
                        k.lower()
                        for k in Node.EMITTER_KEY_TYPE
                    ]
                ):
                    attr_name = key_name
                    key_data = self.object_data
                    test = key_data["test"]
                    attr_type = None
                    if attr_name not in Node.KEY_TYPE:
                        # emitter property
                        attr_name = next(
                            attr
                            for attr in Node.EMITTER_KEY_TYPE
                            if attr.lower() in label
                        )
                        key_data = self.emitter_data
                        attr_type = Node.EMITTER_KEY_TYPE[attr_name]
                    else:
                        # object property
                        attr_type = Node.KEY_TYPE[attr_name]

                    numVals = attr_type["values"]
                    numKeys = 0
                    if key_type:
                        if key_type == "bezierkey":
                            numVals *= 3
                        numKeys = Node.find_end(ascii_lines[i+1:])
                        subblock = ascii_lines[i + 1:i + numKeys + 1]
                    else:
                        numKeys = 1
                        subblock = [[0.0] + line[1:]]

                    converter: type[float] | Callable[[str], float | int] = attr_type.get("converter", float)
                    for key_name in key_data:
                        # Transform each subblock entry: time followed by values
                        transformed_subblock: list[list[float]] = []
                        for v in subblock:
                            time_value = float(v[0])  # Convert the first element to float for time
                            converted_values: list[float] = [
                                converter(value)
                                for value in v[1 : numVals + 1]
                            ]  # Convert subsequent values
                            transformed_subblock.append([time_value, *converted_values])  # Combine them into one list

                        # Additional attributes and the number of values
                        additional_attr = attr_type.get("objdata", "")
                        key_data[key_name] = (transformed_subblock, additional_attr, numVals)

    def create_data_object(
        self,
        obj,
        anim: MDLAnimation,
        options: dict[str, Any] | None = None,
    ):
        """Creates animations in object actions."""
        if options is None:
            options = {}

        fps = CONST_MDL_ANIMATION_FPS
        frame_start = anim.frameStart

        # Insert keyframes of each type
        for label, (data, data_path, data_dim) in self.object_data.items():
            parsed_data_dim = data_dim

            frames = [fps * d[0] + frame_start for d in data]

            if obj.type == "LIGHT" and label in ("radius", "color"):
                # For light radius and color, target the object data
                use_action = get_action(obj.data, options["mdlname"] + "." + obj.name)
            else:
                # Otherwise, target the object
                use_action = get_action(obj, options["mdlname"] + "." + obj.name)

            if label == "position":
                values = [d[1:4] for d in data]
                parsed_data_dim = 3 # TODO(ndix UR): add support for Bezier keys
            elif label == "orientation":
                quats = [utils.nwangle2quat(d[1:5]) for d in data]
                values = [quat[:4] for quat in quats]
                parsed_data_dim = 4
            elif label == "scale":
                values = [[d[1]]*3 for d in data]
                parsed_data_dim = 3
            else:
                values = [d[1:data_dim+1] for d in data]

            Animnode.insert_kfp(frames, values, use_action, data_path, parsed_data_dim)

    def create_data_emitter(
        self,
        obj,
        anim: MDLAnimation,
        options: dict | None = None,
    ):
        """Creates animations in emitter actions."""
        if options is None:
            options = {}

        fps = CONST_MDL_ANIMATION_FPS
        frame_start = anim.frameStart
        action = get_action(obj, options["mdlname"] + "." + obj.name)
        for label, (data, _, data_dim) in self.emitter_data.items():
            frames = [fps * d[0] + frame_start for d in data]
            values = [d[1:data_dim+1] for d in data]
            dp = f"kb.{label}"
            dp_dim = data_dim
            Animnode.insert_kfp(frames, values, action, dp, dp_dim, "Odyssey Emitter")

    @staticmethod
    def create_restpose(obj, frame: int = 1):
        def insert_kfp(
            fcurves: list,
            frame: int,
            val: str | list,
            dim: int,
        ):
            # dim = len(val)
            for j in range(dim):
                kf = fcurves[j].keyframe_points.insert(frame, val[j], options={"FAST"})
                kf.interpolation = "LINEAR"
        # Get animation data
        animData = obj.animation_data
        if not animData:
            return  # No data = no animation = no need for rest pose
        # Get action
        action = animData.action
        if not action:
            return  # No action = no animation = no need for rest pose
        fcu = [action.fcurves.find("rotation_quaternion", index=i) for i in range(4)]
        if fcu.count(None) < 1:
            q = Quaternion(obj.kb.restrot)
            insert_kfp(fcu, frame, [q.w, q.x, q.y, q.z], 4)
        fcu = [action.fcurves.find("location", index=i) for i in range(3)]
        if fcu.count(None) < 1:
            insert_kfp(fcu, frame, obj.kb.restloc, 3)
        fcu = [action.fcurves.find("scale", index=i) for i in range(3)]
        if fcu.count(None) < 1:
            insert_kfp(fcu, frame, [obj.kb.restscl] * 3, 3)

    def add_object_keyframes(
        self,
        obj,
        anim: MDLAnimation,
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        if self.object_data:
            self.create_data_object(obj, anim, options)
        if self.emitter_data:
            self.create_data_emitter(obj, anim, options)

    @staticmethod
    def generate_ascii(
        obj,
        anim: MDLAnimation,
        ascii_lines: list[list[str] | str],
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        if not obj or not Node.export_needed(obj, anim):
            return

        # Type + Name
        node_type: Literal["emitter", "dummy"] = "emitter" if obj.kb.meshtype == "emitter" else "dummy"
        node_name = Node.get_original_name(obj.name, anim.name)
        ascii_lines.append(f"  node {node_type} {node_name}")

        # Parent
        parent_name = Node.get_original_name(obj.parent.name, anim.name) if obj.parent else "NULL"
        ascii_lines.append(f"    parent {parent_name}")
        Node.generate_ascii_keys(obj, anim, ascii_lines, options)
        ascii_lines.append("  endnode")
