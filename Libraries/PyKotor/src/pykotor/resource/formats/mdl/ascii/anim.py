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

from collections import OrderedDict
from typing import TYPE_CHECKING

from mdl.ascii import animnode
from pykotor.resource.formats.mdl.mdl_data import CONST_MDL_ANIMATION_FPS, search_node
from utility.misc import is_int

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.resource.formats.mdl.io_mdl import _Node
    from pykotor.resource.formats.mdl.mdl_data import MDLAnimation


class Animation:
    def __init__(
        self,
        name: Literal["UNNAMED"] = "UNNAMED",
        ascii_data: str | None = None,
    ):
        self.name: str = name
        self.length: float = 1.0
        self.transtime: float = 1.0
        self.animroot: str = "NULL"
        self.event_list: list = []
        self.node_list: OrderedDict = OrderedDict()

        self.nodes: list = []
        self.events: list = []

        if ascii_data:
            self.load_ascii(ascii_data)

    def add_to_objects(self, mdl_root):
        list_anim = self._create_list_anim(mdl_root)
        self._add_events_to_list_anim(list_anim)
        obj_by_node = self._associate_node_to_object(mdl_root)

        # Add object keyframes
        for node in self.nodes:
            if node.name.lower() in obj_by_node:
                obj = obj_by_node[node.name.lower()]
                node.add_object_keyframes(obj, list_anim, {"mdlname":mdl_root.name})
                self._create_rest_pose(obj, list_anim.frameStart-5)

    def _create_list_anim(self, mdl_root):
        result = utils.create_anim_list_item(mdl_root)
        result.name = self.name
        result.transtime = CONST_MDL_ANIMATION_FPS * self.transtime
        result.root = result.root_obj = self._get_anim_target(mdl_root).name
        result.frameEnd = utils.nwtime2frame(self.length) + result.frameStart
        return result

    def _get_anim_target(self, mdl_root):
        result = search_node(mdl_root, lambda o, name=self.animroot: o.name.lower() == name.lower())
        if not result:
            result = mdl_root
            print(f"PyKotor: animation retargeted from {self.animroot} to {mdl_root.name}")
        return result

    def _add_events_to_list_anim(self, list_anim):
        for time, name in self.events:
            event = list_anim.event_list.add()
            event.name = name
            event.frame = utils.nwtime2frame(time) + list_anim.frameStart

    def _associate_node_to_object(self, mdl_root):
        result = dict()
        for node in self.nodes:
            obj = utils.search_node(mdl_root, lambda o, name=node.name: o.name.lower() == name.lower())
            if obj:
                result[node.name.lower()] = obj
        return result

    def _create_rest_pose(self, obj, frame: int = 1):
        animnode.Animnode.create_restpose(obj, frame)

    def add_ascii_node(self, ascii_block: str):
        node = animnode.Node()
        node.load_ascii(ascii_block)
        key  = node.parentName + node.name

        #TODO: Should probably raise an exception
        if key not in self.node_list:
            self.node_list[key] = node

    def add_event(self, event):
        self.event_list.append(event)

    def get_anim_from_ascii(self, ascii_block: str):
        # sourcery skip: remove-redundant-if
        blockStart = -1
        for idx, line in enumerate(ascii_block):
            try:
                label = line[0].lower()
            except IndexError:
                # Probably empty line or whatever, skip it
                continue
            if (label == "newanim"):
                self.name = line[1]
            elif (label == "length"):
                self.length = float(line[1])
            elif (label == "transtime"):
                self.transtime = float(line[1])
            elif (label == "animroot"):
                try:
                    self.animroot = line[1]
                except:
                    self.animroot = "undefined"
            elif (label == "event"):
                self.add_event((float(line[1]), line[2]))
            elif (label == "eventlist"):
                numEvents = next((i for i, v in enumerate(ascii_block[idx+1:]) if not is_int(v[0])), -1)
                list(map(self.add_event, ((float(v[0]), v[1]) for v in ascii_block[idx+1:idx+1+numEvents])))
            elif (label == "node"):
                blockStart = idx
            elif (label == "endnode"):
                if (blockStart > 0):
                    self.add_ascii_node(ascii_block[blockStart:idx+1])
                    blockStart = -1
                elif (label == "node"):  # FIXME: is this perhaps trying to parse the next label? 'node' is already parsed above.
                    raise MalformedMdl("Unexpected 'endnode'")

    def load_ascii(self, ascii_data):
        """Load an animation from a block from an ascii mdl file."""
        self.get_anim_from_ascii([_line.strip().split() for _line in ascii_data.splitlines()])
        animNodesStart = ascii_data.find("node ")
        if (animNodesStart > -1):
            self.load_ascii_anim_header(ascii_data[:animNodesStart-1])
            self.load_ascii_anim_nodes(ascii_data[animNodesStart:])
        else:
            print("NeverBlender - WARNING: Failed to load an animation.")

    def load_ascii_anim_header(self, ascii_data: str):
        ascii_lines = [_line.strip().split() for _line in ascii_data.splitlines()]
        for line in ascii_lines:
            try:
                label = line[0].lower()
            except (IndexError, AttributeError):
                continue  # Probably empty line, skip it

            if (label == "newanim"):
                self.name = utils.str2identifier(line[1])
            elif (label == "length"):
                self.length = float(line[1])
            elif (label == "transtime"):
                self.transtime = float(line[1])
            elif (label == "animroot"):
                try:
                    self.animroot = line[1].lower()
                except (ValueError, IndexError):
                    self.animroot = ""
            elif (label == "event"):
                self.events.append((float(line[1]), line[2]))

    def load_ascii_anim_nodes(self, ascii_data: str):
        dlm = "node "
        node_list: list[str] = [dlm + s for s in ascii_data.split(dlm) if s]
        for idx, ascii_node in enumerate(node_list):
            ascii_lines = [_line.strip().split() for _line in ascii_node.splitlines()]
            node = animnode.Animnode()
            node.load_ascii(ascii_lines, idx)
            self.nodes.append(node)

    def anim_node_to_ascii(
        self,
        binary_obj: _Node,
        ascii_lines: list[list[str] | str],
    ):
        node = animnode.Node()
        node.to_ascii(binary_obj, ascii_lines, self.name)

        childList: list[tuple] = [
            (child.kb.imporder, child)
            for child in binary_obj.children
        ]
        childList.sort(key=lambda tup: tup[0])

        for (_, child) in childList:
            self.anim_node_to_ascii(child, ascii_lines)

    @staticmethod
    def generate_ascii_nodes(obj, anim, ascii_lines, options):
        animnode.Animnode.generate_ascii(obj, anim, ascii_lines, options)

        # Sort children to restore original order before import
        # (important for supermodels/animations to work)
        children = list(obj.children)
        children.sort(key=lambda c: c.name)
        children.sort(key=lambda c: c.kb.imporder)
        for c in children:
            Animation.generate_ascii_nodes(c, anim, ascii_lines, options)

    @staticmethod
    def generate_ascii(
        anim_root_dummy,
        anim: MDLAnimation,
        ascii_lines: list[list[str] | str],
        options: dict | None = None,
    ):
        ascii_lines.extend(
            (
                f"newanim {anim.name} {anim_root_dummy.name}",
                f"  length {round((anim.frameEnd - anim.frameStart) / CONST_MDL_ANIMATION_FPS, 5)}",
                f"  transtime {round(anim.ttime, 3)}",
                f"  animroot {anim.root}",
            )
        )
        # Get animation events
        for event in anim.event_list:
            event_time = (event.frame - anim.frameStart) / CONST_MDL_ANIMATION_FPS
            ascii_lines.append(
                f"  event {round(event_time, 3)} {event.name}"
            )

        Animation.generate_ascii_nodes(anim_root_dummy, anim, ascii_lines, options)

        ascii_lines.extend((f"doneanim {anim.name} {anim_root_dummy.name}", ""))

    def to_ascii(
        self,
        anim_scene: _Node,
        anim_root_dummy,
        ascii_lines: list[list[str] | str],
        mdl_name: str = "",
    ):
        self.name      = anim_root_dummy.kb.animname
        self.length    = utils.frame2nwtime(anim_scene.frame_end, anim_scene.render.fps)
        self.transtime = anim_root_dummy.kb.transtime
        self.animroot  = anim_root_dummy.kb.animroot

        ascii_lines.extend(
            (
                f"newanim {self.name} {mdl_name}",
                f"  length {round(self.length, 5)!s}",
                f"  transtime {round(self.transtime, 3)!s}",
                f"  animroot {self.root}",
            )
        )
        for event in anim_root_dummy.kb.event_list:
            eventTime = utils.frame2nwtime(event.frame, anim_scene.render.fps)
            ascii_lines.append(f"  event {round(eventTime, 5)!s} {event.name}")

        self.anim_node_to_ascii(anim_root_dummy, ascii_lines)
        ascii_lines.extend(
            (
                f"doneanim {self.name} {mdl_name}",
                "",
            )
        )
