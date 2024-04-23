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
import os
import re

from datetime import datetime
from typing import TYPE_CHECKING

import bpy

from typing_extensions import Literal

from mdl.ascii import anim as mdlanim, node as mdlnode
from pykotor.common.geometry import Vector3
from pykotor.resource.formats.mdl.mdl_data import DummySubtype, MDLNodeFlags, ancestor_node, is_root_dummy, search_node, search_node_all

from .... import defines, glob, utils
from ....exception.malformedmdl import MalformedMdl
from ....scene import armature

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.io_mdl import _Node, _SkinmeshHeader


class Mdl:
    def __init__(self):
        self.nodeDict      = collections.OrderedDict()
        self.animDict      = dict() # No need to retain order

        self.name           = "UNNAMED"
        self.supermodel     = "NULL"
        self.animscale      = 1.0
        self.classification = defines.Classification.UNKNOWN
        self.unknownC1      = 0
        self.ignorefog      = False
        self.compress_quats = False
        self.headlink       = False
        self.lytposition    = None

        self.animations = []

    def load_ascii_node(self, ascii_block: list[list[str]]):
        if ascii_block is None:
            raise MalformedMdl("Empty Node")

        nodeType = ""
        try:
            nodeType = ascii_block[0][1].lower()
        except (IndexError, AttributeError) as e:
            raise MalformedMdl("Invalid node type") from e

        switch = {
            defines.Nodetype.DUMMY:      mdlnode.Dummy,
            defines.Nodetype.REFERENCE:  mdlnode.Reference,
            defines.Nodetype.TRIMESH:    mdlnode.Trimesh,
            defines.Nodetype.DANGLYMESH: mdlnode.Danglymesh,
            defines.Nodetype.LIGHTSABER: mdlnode.Lightsaber,
            defines.Nodetype.SKIN:       mdlnode.Skinmesh,
            defines.Nodetype.EMITTER:    mdlnode.Emitter,
            defines.Nodetype.LIGHT:      mdlnode.Light,
            defines.Nodetype.AABB:       mdlnode.Aabb
        }
        try:
            node = switch[nodeType]()
        except KeyError as e:
            raise MalformedMdl("Invalid node type") from e

        # tell the node if it is part of a walkmesh (mdl is default)
        if isinstance(self, Xwk):
            node.roottype = self.walkmesh_type

        # tell the node what model it is part of
        node.rootname = self.name

        node.load_ascii(ascii_block)
        self.add_node(node)

    def add_node(self, new_node):
        # Blender requires unique object names. Names in mdls are only
        # unique for a parent, i.e. another object with the same name but
        # with a different parent may exist.
        # We'd need to save all names starting from root to resolve
        # this, but that's too much effort.
        # ParentName + Name should be enough.
        if new_node:
            key = new_node.parentName + new_node.name
            if key in self.nodeDict:
                print(f"PyKotor: WARNING - node name conflict {key}.")
            else:
                self.nodeDict[key] = new_node

    def add_animation(self, anim):
        if anim:
            if anim.name in self.animDict:
                print("PyKotor: WARNING - animation name conflict.")
            else:
                self.animDict[anim.name] = anim

    def import_to_collection(
        self,
        collection,
        wkm: Xwk,
        position: Vector3 | None = None,
    ):
        if position is None:
            position = Vector3.from_null()

        mdl_root = None
        if (glob.importGeometry) and self.nodeDict:
            mdl_root = self._extracted_from_import_to_collection_(collection, position)

        # Import the walkmesh, it will use any placeholder dummies just imported,
        # and the walkmesh nodes will be copied during animation import
        if glob.importWalkmesh and wkm is not None and wkm.walkmesh_type != "wok":
            wkm.import_to_collection(collection)

        # Attempt to import animations
        # Search for the MDL root if not already present
        if not mdl_root:
            for obj in collection.objects:
                if is_root_dummy(obj, defines.Dummytype.MDLROOT):
                    mdl_root = obj
                    break
        # Still none ? Don't try to import anims then
        if not mdl_root:
            return

        armature_object = None
        if glob.createArmature:
            armature_object = armature.recreate_armature(mdl_root)
        else:
            # When armature creation is disabled, see if the MDL root already has an armature and use that
            skinmeshes: list[_SkinmeshHeader] = search_node_all(mdl_root, lambda o: o.kb.meshtype == defines.Meshtype.SKIN)
            for skinmesh in skinmeshes:
                for modifier in skinmesh.modifiers:
                    if modifier.type == "ARMATURE":
                        armature_object = modifier.object
                        break
                if armature_object:
                    break

        self._create_animations(mdl_root, armature_object)

    # TODO Rename this here and in `import_to_collection`
    def _extracted_from_import_to_collection_(self, collection, position: Vector3):
        it = iter(self.nodeDict.items())

        # The first node should be the rootdummy.
        # If the first node has a parent or isn't a dummy we don't
        # even try to import the mdl
        (_, node) = next(it)
        objIdx = 0
        if type(node) != mdlnode.Dummy or not (utils.is_null(node.parentName)):
            raise MalformedMdl("First node has to be a dummy without a parent.")

        obj                    = node.add_to_collection(collection)
        obj.location           = position
        obj.kb.dummytype      = defines.Dummytype.MDLROOT
        obj.kb.supermodel     = self.supermodel
        obj.kb.classification = self.classification
        obj.kb.unknownC1      = self.unknownC1
        obj.kb.ignorefog      = (self.ignorefog >= 1)
        obj.kb.compress_quats = (self.compress_quats >= 1)
        obj.kb.headlink       = (self.headlink >= 1)
        obj.kb.animscale      = self.animscale
        result = obj

        obj.kb.imporder = objIdx
        objIdx += 1
        for _, node in it:
            obj = node.add_to_collection(collection)
            obj.kb.imporder = objIdx
            objIdx += 1

            # If LYT position is specified, set it for the AABB node
            if self.lytposition and node.nodetype == "aabb":
                node.lytposition = self.lytposition
                obj.kb.lytposition = self.lytposition

            if (utils.is_null(node.parentName)):
                # Node without parent and not the mdl root.
                raise MalformedMdl(f"{node.name} has no parent.")

            if obj.parent is not None:
                print(f"WARNING: Node already parented: {obj.name}")
            elif (
                result
                and node.parentName in bpy.data.objects
                and result.name == getattr(
                    ancestor_node(
                        bpy.data.objects[node.parentName],
                        is_root_dummy,
                    ),
                    "name",
                    None,
                )
            ):
                # parent named node exists and is in our model
                obj.parent = bpy.data.objects[node.parentName]
                if node.parentName != self.name:
                    # child of non-root, preserve orientation
                    obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
            else:
                # parent node was not found in our model,
                # this should mean that a node of the same name already
                # existed in the scene,
                # perform search for parent node in our model,
                # taking into account blender .001 suffix naming scheme,
                # note: only searching 001-030
                found: bool = False
                for altname in [f"{node.parentName}.{i:03d}" for i in range(1,30)]:
                    if (
                        altname in bpy.data.objects
                        and result.name == getattr(
                            ancestor_node(
                                bpy.data.objects[altname],
                                utils.is_root_dummy,
                            ),
                            "name",
                            None,
                        )
                    ):
                        # parent node in our model exists with suffix
                        obj.parent = bpy.data.objects[altname]
                        obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
                        found = True
                        break
                # Node with invalid parent.
                if not found:
                    raise MalformedMdl(f"{node.name} has no parent {node.parentName}")

        return result

    def _create_animations(self, mdl_root, armature_object):
        # Load the 'default' animation first, so it is at the front
        anims = [a for a in self.animations if a.name == "default"]
        for a in anims:
            a.add_to_objects(mdl_root)
        # Load the rest of the anims
        anims = [a for a in self.animations if a.name != "default"]
        for a in anims:
            a.add_to_objects(mdl_root)
        if armature_object:
            armature.create_armature_animations(mdl_root, armature_object)

    def load_ascii(self, ascii_block: str):
        geom_start = ascii_block.find("node ")
        anim_start = ascii_block.find("newanim ")
        geom_end   = ascii_block.find("endmodelgeom ")

        if (anim_start > 0) and (geom_start > anim_start):
            raise MalformedMdl("Animations before geometry")
        if (geom_start < 0):
            raise MalformedMdl("Unable to find geometry")

        self.read_ascii_header(ascii_block[:geom_start-1])
        # Import Geometry
        self.read_ascii_geom(ascii_block[geom_start:geom_end])
        # Import Animations
        if glob.importAnim and (anim_start > 0):
            self.read_ascii_anims(ascii_block[anim_start:])

    def read_ascii_anims(self, ascii_block):
        """Load all animations from an ascii mdl block."""
        delim = "newanim "
        animList = [delim + b for b in ascii_block.split(delim) if b]
        self.animations = [mdlanim.Animation(ascii_data=txt) for txt in animList]
        for anim in self.animations:
            self.add_animation(anim)

    def read_ascii_geom(self, ascii_block: str):
        """Load all geometry nodes from an ascii mdl block."""
        delim = "node "
        ascii_nodes: list[str] = [delim + b for b in ascii_block.split(delim) if b]
        for ascii_node in ascii_nodes:
            ascii_lines = [_list.strip().split() for _list in ascii_node.splitlines()]
            try:  # Read node type
                ascii_lines[0][1].lower()
            except (IndexError, AttributeError) as e:
                raise MalformedMdl("Unable to read node type") from e
            try:  # Read node name
                ascii_lines[0][2].lower()
            except (IndexError, AttributeError) as e:
                raise MalformedMdl("Unable to read node name") from e
            self.load_ascii_node(ascii_lines)

    def read_ascii_header(self, ascii_block: str):
        ascii_lines: list[list[str] | str] = [
            _line.strip().split()
            for _line in ascii_block.splitlines()
        ]
        for line in ascii_lines:
            try:
                label = line[0].lower()
            except (IndexError, AttributeError):
                continue  # Probably empty line, skip it

            if label == "newmodel":
                try:
                    self.name = line[1]
                except (ValueError, IndexError):
                    print("PyKotor: WARNING - unable to read model name.")
            elif label == "setsupermodel":
                try:  # should be ['setsupermodel', modelname, supermodelname]
                    self.supermodel = line[2]
                except (ValueError, IndexError):
                    print(f"PyKotor: WARNING - unable to read supermodel. Using default value: '{self.supermodel}'")
            elif label == "classification":
                try:
                    self.classification = line[1].title()
                except (ValueError, IndexError):
                    print(f"PyKotor: WARNING - unable to read classification. Using Default value: '{self.classification}'")
                if self.classification not in defines.Classification.ALL:
                    print(f"PyKotor: WARNING - invalid classification: '{self.classification}'")
                    self.classification = defines.Classification.UNKNOWN
            elif label == "classification_unk1":
                try:
                    self.unknownC1 = int(line[1])
                except IndexError:
                    print(f"PyKotor: WARNING - unable to read classification unknown. Default value: '{self.unknownC1}'")
            elif label == "ignorefog":
                try:
                    self.ignorefog = int(line[1])
                except IndexError:
                    print(f"PyKotor: WARNING - unable to read ignorefog. Default value: '{self.ignorefog}'")
            elif label == "compress_quaternions":
                try:
                    self.compress_quats = int(line[1])
                except IndexError:
                    print(f"PyKotor: WARNING - unable to read compress_quaternions. Default value: '{self.compress_quats}'")
            elif label == "headlink":
                try:
                    self.headlink = int(line[1])
                except IndexError:
                    print(f"PyKotor: WARNING - unable to read headlink. Default value: '{self.headlink}'")
            elif label == "setanimationscale":
                try:
                    self.animscale = float(line[1])
                except (ValueError, IndexError):
                    print(f"PyKotor: WARNING - unable to read animationscale. Using default value: {self.animscale}")
            elif label == "layoutposition":
                self.lytposition = [float(x) for x in line[1:]]

    def geometry_to_ascii(
        self,
        bin_object: _Node,
        ascii_lines: list[list[str] | str],
        name_dict: dict | None = None,
        *,
        simple: bool = False,
    ):
        nodeType = utils.get_node_type(bin_object)
        switch = {"dummy":      mdlnode.Dummy,
                  "reference":  mdlnode.Reference,
                  "trimesh":    mdlnode.Trimesh,
                  "danglymesh": mdlnode.Danglymesh,
                  "skin":       mdlnode.Skinmesh,
                  "emitter":    mdlnode.Emitter,
                  "light":      mdlnode.Light,
                  "aabb":       mdlnode.Aabb}
        try:
            node = switch[nodeType]()
        except KeyError:
            raise MalformedMdl("Invalid node type")

        node.to_ascii(bin_object, ascii_lines, self.classification, name_dict=name_dict, simple=simple)

        childList = [(child.kb.imporder, child) for child in bin_object.children]
        childList.sort(key=lambda tup: tup[0])

        for (_, child) in childList:
            self.geometry_to_ascii(child, ascii_lines, name_dict=name_dict, simple=simple)

    def generate_ascii_animations(
        self,
        ascii_lines: list[list[str] | str],
        root_dummy,
        options: dict | None = None,
    ):
        if options is None:
            options = {}
        if root_dummy.kb.animList:
            for anim in root_dummy.kb.animList:
                print(f"export animation {anim.name}")
                mdlanim.Animation.generate_ascii(root_dummy, anim, ascii_lines, options)

    def generate_ascii(
        self,
        ascii_lines: list[list[str] | str],
        root_dummy,
        exports: set[str] | None = None,
    ):
        if exports is None:
            exports = {"ANIMATION", "WALKMESH"}
        self.name           = root_dummy.name
        self.classification = root_dummy.kb.classification
        self.supermodel     = root_dummy.kb.supermodel
        self.unknownC1      = root_dummy.kb.unknownC1
        self.ignorefog      = root_dummy.kb.ignorefog
        self.compress_quats = root_dummy.kb.compress_quats
        self.headlink       = root_dummy.kb.headlink
        self.animscale      = root_dummy.kb.animscale

        # feature: export of models loaded in scene multiple times
        # construct a name map that points any NAME.00n names to their base name,
        # needed for model and node names as well as parent node references
        object_name_map = {}
        all_nodes = search_node_all(root_dummy, bool)
        for node in all_nodes:
            match = re.match(r"^(.+)\.\d\d\d$", node.name)
            if match:
                remap_name = all(
                    test_node.name.lower() != match.group(1).lower()
                    for test_node in all_nodes
                )
                # if the node base name has already been remapped, don't repeat
                if match.group(1) in object_name_map.values():
                    remap_name = False
                # add the name mapping
                if remap_name:
                    object_name_map[node.name] = match.group(1)
        # change the model name if root node is in object name map
        if self.name in object_name_map:
            self.name = object_name_map[self.name]
        # set object_name_map to none if feature is unused
        if not len(object_name_map.keys()):
            object_name_map = None

        # Header
        currentTime = datetime.now()
        blendFileName = os.path.basename(bpy.data.filepath) or "unknown"
        ascii_lines.append("# Exported from blender at " + currentTime.strftime("%A, %Y-%m-%d"))
        ascii_lines.extend(
            (
                f"filedependancy {blendFileName}",
                f"newmodel {self.name}",
                f"setsupermodel {self.name} {self.supermodel}",
                f"classification {self.classification}",
                f"classification_unk1 {self.unknownC1!s}",
                f"ignorefog {int(self.ignorefog)!s}",
            )
        )
        if self.compress_quats:
            # quaternion compression does not work with the rotations we export,
            # for unknown reasons...
            # therefore, just export it as disabled for now...
            ascii_lines.append("compress_quaternions 0")
            # they actually work with mdlops now, not mdledit yet...
        if self.headlink:
            ascii_lines.append(f"headlink {int(self.headlink)!s}")
        ascii_lines.extend(
            (
                f"setanimationscale {round(self.animscale, 7)!s}",
                f"beginmodelgeom {self.name}",
            )
        )
        aabb = search_node(
            root_dummy,
            lambda x: x.kb.meshtype == MDLNodeFlags.AABB,
        )
        if (
            aabb is not None
            and aabb.kb.lytposition != (0.0, 0.0, 0.0)
        ):
            lytposition = (
                aabb.kb.lytposition[0],
                aabb.kb.lytposition[1],
                aabb.kb.lytposition[2],
            )
            if root_dummy.location.to_tuple() != (0.0, 0.0, 0.0):
                lytposition = (
                    root_dummy.location[0],
                    root_dummy.location[1],
                    root_dummy.location[2],
                )
            ascii_lines.append("  layoutposition {: .7g} {: .7g} {: .7g}".format(*lytposition))
        self.geometry_to_ascii(
            root_dummy,
            ascii_lines,
            object_name_map,
            simple=False,
        )
        ascii_lines.append(f"endmodelgeom {self.name}")
        # Animations
        if "ANIMATION" in exports:
            ascii_lines.extend(("", "# ANIM ASCII"))
            self.generate_ascii_animations(ascii_lines, root_dummy)
        ascii_lines.extend((f"donemodel {self.name}", ""))


class Xwk(Mdl):
    def __init__(self, wkm_type: Literal["pwk", "wok"] = "pwk"):
        Mdl.__init__(self)

        self.walkmesh_type: Literal["pwk", "wok"] = wkm_type

    def load_ascii_animation(self, ascii_block: str):
        pass # No animations in walkmeshes

    def load_ascii(self, ascii_lines: list[list[str] | str]):
        # Parse the walkmesh
        blockStart = -1
        for idx, line in enumerate(ascii_lines):
            try:
                label = line[0]
            except IndexError:
                # Probably empty line or whatever, just skip it
                continue
            if (label == "node"):
                blockStart = idx
            elif (label == "endnode"):
                if (blockStart >= 0):
                    self.load_ascii_node(ascii_lines[blockStart:idx+1])
                    blockStart = -1
                else:
                    # "endnode" before "node"
                    raise MalformedMdl(f"Unexpected 'endnode' at line {idx}")

    def generate_ascii(
        self,
        ascii_lines: list[list[str] | str],
        root_dummy,
        exports: set[str] | None = None,
    ):
        if exports is None:
            exports = {"ANIMATION", "WALKMESH"}
        self.name = root_dummy.name

        # Header
        currentTime = datetime.now()
        ascii_lines.append("# Exported from blender at " + currentTime.strftime("%A, %Y-%m-%d"))
        # Geometry
        for child in root_dummy.children:
            self.geometry_to_ascii(child, ascii_lines, simple=True)

    def import_to_collection(self, collection):
        if not self.nodeDict:
            return
        # Walkmeshes have no rootdummys. We need to create one ourselves
        # Unless the rootdummy is in the model already, because that happens

        # Also, kotormax puts the rootdummy into the PWK and probably DWK,
        # making this not work.
        # Even worse, it parents the use dummies to the mesh,
        # making this doubly not work.

        # Our format expectations are more like what mdlops exports,
        # which is in line with the format used in NWN.

        # Look for the node parents for the list of parents. They should
        # all have the same name
        nameList = []
        for node in self.nodeDict.values():
            if node.parentName not in nameList:
                nameList.append(node.parentName)
        self.name = nameList[0]

        if (
            self.name in collection.objects
            and bpy.data.objects[self.name].kb.dummytype != DummySubtype.MDLROOT
        ):
            node = bpy.data.objects[self.name].kb
            if self.walkmesh_type == "dwk":
                node.dummytype = defines.Dummytype.DWKROOT
            else:
                node.dummytype = defines.Dummytype.PWKROOT
            rootdummy = bpy.data.objects[self.name]

        else:
            mdl_name = self.name
            wkm_name = self.name
            if not wkm_name.lower().endswith(f"_{self.walkmesh_type}"):
                wkm_name += f"_{self.walkmesh_type}"
            if mdl_name.lower().endswith("_" + self.walkmesh_type):
                mdl_name = mdl_name[:-4]
            node = mdlnode.Dummy(wkm_name)
            if self.walkmesh_type == "dwk":
                node.dummytype = defines.Dummytype.DWKROOT
            else:
                node.dummytype = defines.Dummytype.PWKROOT
            node.name = wkm_name
            rootdummy = node.add_to_collection(collection)
            if mdl_name in bpy.data.objects:
                rootdummy.parent = bpy.data.objects[mdl_name]

        mdlroot = ancestor_node(
            rootdummy,
            lambda o: o.kb.dummytype == defines.Dummytype.MDLROOT,
        )
        if mdlroot is None and rootdummy.parent:
            mdlroot = rootdummy.parent
        if self.walkmesh_type == "dwk":
            dp_open1 = search_node(mdlroot, lambda o: "dwk_dp" in o.name.lower() and o.name.lower().endswith("open1_01"))
            dp_open2 = search_node(mdlroot, lambda o: "dwk_dp" in o.name.lower() and o.name.lower().endswith("open2_01"))
            dp_closed01 = search_node(mdlroot, lambda o: "dwk_dp" in o.name.lower() and o.name.lower().endswith("closed_01"))
            dp_closed02 = search_node(mdlroot, lambda o: "dwk_dp" in o.name.lower() and o.name.lower().endswith("closed_02"))
            wg_open1 = search_node(mdlroot, lambda o: "dwk_wg" in o.name.lower() and o.name.lower().endswith("open1"))
            wg_open2 = search_node(mdlroot, lambda o: "dwk_wg" in o.name.lower() and o.name.lower().endswith("open2"))
            wg_closed = search_node(mdlroot, lambda o: "dwk_wg" in o.name.lower() and o.name.lower().endswith("closed"))

        if self.walkmesh_type == "pwk":
            pwk_wg = search_node(mdlroot, lambda o: o.name.lower().endswith("_wg"))
            pwk_use01 = search_node(mdlroot, lambda o: o.name.lower().endswith("pwk_use01"))
            pwk_use02 = search_node(mdlroot, lambda o: o.name.lower().endswith("pwk_use02"))

        for node in self.nodeDict.values():
            # the node names may only be recorded in the MDL,
            # this means that the named dummy nodes already exist in-scene,
            # use these names to translate the WKM's special node names
            if "dp_open1_01" in node.name.lower() and dp_open1:
                node.name = dp_open1.name
            if "dp_open2_01" in node.name.lower() and dp_open2:
                node.name = dp_open2.name
            if "dp_closed_01" in node.name.lower() and dp_closed01:
                node.name = dp_closed01.name
            if "dp_closed_02" in node.name.lower() and dp_closed02:
                node.name = dp_closed02.name
            if "dwk_wg_open1" in node.name.lower() and wg_open1:
                node.name = wg_open1.name
            if "dwk_wg_open2" in node.name.lower() and wg_open2:
                node.name = wg_open2.name
            if "dwk_wg_closed" in node.name.lower() and wg_closed:
                node.name = wg_closed.name
            if node.name.lower().endswith("_wg") and pwk_wg:
                node.name = pwk_wg.name
            if node.name.lower().endswith("pwk_use01") and pwk_use01:
                node.name = pwk_use01.name
            if node.name.lower().endswith("pwk_use02") and pwk_use02:
                node.name = pwk_use02.name
            # remove pre-existing nodes that were added as part of a model
            if node.name in collection.objects:
                obj = collection.objects[node.name]
                collection.objects.unlink(obj)
                bpy.data.objects.remove(obj)
            obj = node.add_to_collection(collection)
            # Check if such an object exists
            if node.parentName.lower() in [k.lower() for k in bpy.data.objects]:
                parent_name = utils.get_real_name(node.parentName)
                obj.parent = bpy.data.objects[parent_name]
                obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
            else:
                # Node with invalid parent.
                raise MalformedMdl(node.name + " has no parent " + node.parentName)


class Wok(Xwk):
    def __init__(self, name: str = "UNNAMED", wkm_type: Literal["wok"] = "wok"):
        self.node_dict: collections.OrderedDict = collections.OrderedDict()
        self.name           = name
        self.walkmesh_type   = "wok"
        self.classification: Literal["Other", "TILE"] = "Other"

    def geometry_to_ascii(self, bObject, asciiLines, simple):
        nodeType = utils.get_node_type(bObject)
        if nodeType == "aabb":
            node = mdlnode.Aabb()
            node.roottype = "wok"
            node.nodetype = "trimesh"
            node.get_room_links(bObject.data)
            node.to_ascii(bObject, asciiLines, simple)
            return  # We'll take the first aabb object
        else:
            for child in bObject.children:
                self.geometry_to_ascii(child, asciiLines, simple)

    def generate_ascii(self, asciiLines, rootDummy, exports = {"ANIMATION", "WALKMESH"}):
        self.name = rootDummy.name

        # Header
        currentTime   = datetime.now()
        asciiLines.append("# Exported from blender at " + currentTime.strftime("%A, %Y-%m-%d"))
        # Geometry = AABB
        self.geometry_to_ascii(rootDummy, asciiLines, True)

    def import_to_collection(self, collection):
        pass
