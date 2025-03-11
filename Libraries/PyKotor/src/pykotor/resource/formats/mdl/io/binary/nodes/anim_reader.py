"""Binary reader for MDL animation nodes and data."""

from __future__ import annotations

from math import sqrt
from typing import TYPE_CHECKING, Dict, List, Optional

from pykotor.resource.formats.mdl.data.constants import (
    CTRL_FLAG_BEZIER,
    MDL_OFFSET,
    MODEL_FN_PTR_1_K1_XBOX,
    MODEL_FN_PTR_1_K2_XBOX,
    ControllerType,
)
from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.anim import MDLAnimation, MDLAnimationEvent, MDLNodeAnimation, MDLPositionKeyframe, MDLRotationKeyframe, MDLScaleKeyframe
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader
from utility.common.geometry import Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
    from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import ArrayDefinition


class ControllerKey:
    """Key data for an animation controller."""

    def __init__(
        self,
        ctrl_type: int,
        num_rows: int,
        timekeys_start: int,
        values_start: int,
        num_columns: int,
    ):
        self.ctrl_type: int = ctrl_type
        self.num_rows: int = num_rows
        self.timekeys_start: int = timekeys_start
        self.values_start: int = values_start
        self.num_columns: int = num_columns


class MDLBinaryAnimationReader(MDLBinaryNodeReader):
    """Reader for binary MDL animation nodes and data."""

    def __init__(
        self,
        mdl_reader: BinaryReader,
        mdx_reader: BinaryReader,
        names: List[str],
        node_by_number: dict[int, MDLNode],
    ):
        """Initialize the animation reader."""
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)
        self.xbox: bool = False

    def read_node(self, parent: Optional[MDLNodeAnimation] = None) -> MDLNodeAnimation:
        """Read an animation node from the file."""
        try:
            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create animation node
            name = self._names[name_index]
            node = MDLNodeAnimation(name=name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Skip function pointers
            self._reader.skip(8)

            # Read controller arrays
            controller_arr = self._read_array_definition()
            controller_data_arr = self._read_array_definition()

            # Read controllers
            if controller_arr.count > 0:
                controllers = self._load_controllers(controller_arr, controller_data_arr)
                self._process_controllers(node, controllers)

            # Read child nodes
            self.read_children(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading animation node: {str(e)}")

    def _process_controllers(self, node: MDLNodeAnimation, controllers: Dict[int, List[List[float]]]) -> None:
        """Process and convert controller data to node keyframes."""
        # Position keyframes
        if ControllerType.POSITION in controllers:
            for frame in controllers[ControllerType.POSITION]:
                node.position_keyframes.append(
                    MDLPositionKeyframe(frame[0], Vector3(frame[1], frame[2], frame[3]))
                )

        # Orientation keyframes
        if ControllerType.ORIENTATION in controllers:
            for frame in controllers[ControllerType.ORIENTATION]:
                node.rotation_keyframes.append(
                    MDLRotationKeyframe(frame[0], self._orientation_controller_to_quaternion(frame[1:]))
                )

        # Scale keyframes
        if ControllerType.SCALE in controllers:
            for frame in controllers[ControllerType.SCALE]:
                node.scale_keyframes.append(
                    MDLScaleKeyframe(frame[0], Vector3(frame[1], frame[1], frame[1]))  # Uniform scale
                )

    def read_animation(self) -> MDLAnimation:
        """Read animation data from the file."""
        try:
            # Read function pointers to detect format
            fn_ptr1 = self._reader.read_uint32()
            if fn_ptr1 in [MODEL_FN_PTR_1_K1_XBOX, MODEL_FN_PTR_1_K2_XBOX]:
                self.xbox = True
            self._reader.skip(4)  # fn_ptr2

            # Read animation header
            name = self._reader.read_terminated_string("\0", 32)
            root_offset = self._reader.read_uint32()
            node_count = self._reader.read_uint32()
            self._reader.skip(24)  # runtime arrays
            ref_count = self._reader.read_uint32()
            model_type = self._reader.read_uint8()
            self._reader.skip(3)  # padding

            # Create animation
            anim = MDLAnimation(
                name=name,
                length=self._reader.read_single(),
                transtime=self._reader.read_single(),
                animroot=self._reader.read_terminated_string("\0", 32)
            )

            # Read events array
            events_arr = self._read_array_definition()
            self._reader.skip(4)  # padding

            # Read events
            if events_arr.count > 0:
                self._reader.seek(MDL_OFFSET + events_arr.offset)
                for _ in range(events_arr.count):
                    time = self._reader.read_single()
                    event_name = self._reader.read_terminated_string("\0", 32)
                    anim.events.append(MDLAnimationEvent(time=time, name=event_name))

            # Read animation nodes
            if node_count > 0:
                root_node = self.read_node()
                if isinstance(root_node, MDLNodeAnimation):
                    anim.root_node = root_node

            return anim

        except Exception as e:
            raise MDLReadError(f"Error reading animation data: {str(e)}")

    def _load_controllers(self, controller_arr: ArrayDefinition, controller_data_arr: ArrayDefinition) -> Dict[int, List[List[float]]]:
        """Load animation controllers from binary data."""
        self._reader.seek(MDL_OFFSET + controller_arr.offset)
        keys: List[ControllerKey] = []

        # Read controller keys
        for _ in range(controller_arr.count):
            ctrl_type = self._reader.read_uint32()
            self._reader.skip(2)  # unknown
            num_rows = self._reader.read_uint16()
            timekeys_start = self._reader.read_uint16()
            values_start = self._reader.read_uint16()
            num_columns = self._reader.read_uint8()
            self._reader.skip(3)  # padding

            keys.append(
                ControllerKey(
                    ctrl_type,
                    num_rows,
                    timekeys_start,
                    values_start,
                    num_columns,
                )
            )

        controllers: Dict[int, List[List[float]]] = {}
        for key in keys:
            # Read time keys
            self._reader.seek(MDL_OFFSET + controller_data_arr.offset + 4 * key.timekeys_start)
            timekeys = [self._reader.read_single() for _ in range(key.num_rows)]

            # Read value data
            self._reader.seek(MDL_OFFSET + controller_data_arr.offset + 4 * key.values_start)

            # Handle special case for compressed orientation
            if key.ctrl_type == ControllerType.ORIENTATION and key.num_columns == 2:
                integral = True
                num_columns = 1
            else:
                integral = False
                num_columns = key.num_columns & 0xF
                bezier = bool(key.num_columns & CTRL_FLAG_BEZIER)
                if bezier:
                    num_columns *= 3

            # Read values
            values: List[float] = []
            for _ in range(num_columns * key.num_rows):
                values.append(float(self._reader.read_uint32()) if integral else self._reader.read_single())

            # Combine time and values into keyframes
            controllers[key.ctrl_type] = [
                [timekeys[i]] + values[i * num_columns : (i + 1) * num_columns]
                for i in range(key.num_rows)
            ]

        return controllers

    def _orientation_controller_to_quaternion(self, values: List[float]) -> Vector4:
        """Convert orientation controller values to quaternion."""
        num_columns = len(values)
        if num_columns == 4:
            return Vector4(*values)  # type: ignore
        elif num_columns == 1:
            # Decompress packed quaternion using reone's algorithm
            comp = int(values[0])
            x = ((comp & 0x7FF) / 1023.0) - 1.0
            y = (((comp >> 11) & 0x7FF) / 1023.0) - 1.0
            z = ((comp >> 22) / 511.0) - 1.0
            mag2 = x * x + y * y + z * z

            if mag2 >= 1.0:
                mag = sqrt(mag2)
                x /= mag
                y /= mag
                z /= mag
                w = 0.0
            else:
                w = -sqrt(1.0 - mag2)

            return Vector4(x, y, z, w)
        else:
            raise RuntimeError(f"Invalid number of orientation columns: {num_columns}")
