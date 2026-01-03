from __future__ import annotations

import math

from enum import IntFlag
from typing import TYPE_CHECKING, Any

from pykotor.common.misc import Color
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.formats.mdl.mdl_types import MDLClassification, MDLDynamicType, MDLGeometryType, MDLNodeFlags, MDLNodeType
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector2, Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_types import MDLControllerType


# Float canonicalization for equality/hash.
# Toolchains (MDLOps vs PyKotor vs game binaries) routinely differ at ~1e-6 due to formatting
# and IEEE754 round-trip; 1e-5 keeps comparisons stable while remaining strict for MDL data.
_MDL_FLOAT_DECIMALS: int = 3
_MDL_FLOAT_SCALE: float = 10**_MDL_FLOAT_DECIMALS

# Keys that should not be compared *as raw values* because they are aliases, redundant,
# or derived caches. See the ID-equivalence checks below for how node_id/parent_id are
# still validated without requiring exact integer matches.
_MDL_EQ_IGNORE_KEYS: set[str] = set()

# Node ids are semantically meaningful (they back references), but the exact integer values
# are not guaranteed to be stable across roundtrips/toolchains. We therefore:
# - ignore raw values during structural deep-compare/hash
# - separately validate they form an equivalent labeling of the same node graph
_MDL_EQ_ID_KEYS: set[str] = {"node_id", "parent_id"}

# Equality/hash hot-path context tags (avoid allocating path strings during recursion).
_CTX_NONE: int = 0
_CTX_CHILDREN: int = 1
_CTX_ANIMS: int = 2
_CTX_ROWS: int = 3
_CTX_CONTROLLERS: int = 4


def _mdl_node_position_from_controller(node: MDLNode) -> tuple[float, float, float] | None:
    """Return position delta from a POSITION controller row if present and meaningful.

    For header controllers, many toolchains treat POSITION as a delta relative to the node's
    scalar position. We apply that combination in canonicalization.
    """
    for c in node.controllers:
        if c.controller_type != 8:
            continue
        if c.is_bezier:
            continue
        rows = c.rows
        if not rows:
            continue
        data = rows[0].data
        if len(data) < 3:
            continue
        fx, fy, fz = float(data[0]), float(data[1]), float(data[2])
        qx, qy, qz = _qfloat(fx), _qfloat(fy), _qfloat(fz)
        # Treat near-zero as non-meaningful (identity delta/no-op).
        if qx == _qfloat(0.0) and qy == _qfloat(0.0) and qz == _qfloat(0.0):
            return None
        return (fx, fy, fz)
    return None


def _mdl_node_orientation_from_controller(node: MDLNode) -> tuple[float, float, float, float] | None:
    """Return orientation from an ORIENTATION controller row if present and meaningful.

    Note: Values are not guaranteed to be normalized; we normalize during canonicalization.
    """
    for c in node.controllers:
        if c.controller_type != 20:
            continue
        if c.is_bezier:
            continue
        rows = c.rows
        if not rows:
            continue
        data = rows[0].data
        if len(data) < 4:
            continue
        fx, fy, fz, fw = float(data[0]), float(data[1]), float(data[2]), float(data[3])
        # Identity quaternion (or -identity) is non-meaningful/no-op.
        qx, qy, qz, qw = _qfloat(fx), _qfloat(fy), _qfloat(fz), _qfloat(fw)
        if qx == _qfloat(0.0) and qy == _qfloat(0.0) and qz == _qfloat(0.0) and (qw == _qfloat(1.0) or qw == _qfloat(-1.0)):
            return None
        return (fx, fy, fz, fw)
    return None


def _mdl_node_canonical_position(node: MDLNode) -> tuple[int, int, int]:
    """Canonical position for equality/hash: scalar position plus optional controller delta."""
    pos: Vector3 = node.position
    bx = float(pos.x)
    by = float(pos.y)
    bz = float(pos.z)

    delta = _mdl_node_position_from_controller(node)
    if delta is not None:
        dx, dy, dz = delta
        bx += dx
        by += dy
        bz += dz

    return (_qfloat(bx), _qfloat(by), _qfloat(bz))


def _mdl_canonicalize_quaternion(x: float, y: float, z: float, w: float) -> tuple[int, int, int, int]:
    """Normalize quaternion and canonicalize sign so q and -q compare equal."""
    # Normalize (robust to unnormalized/scaled values coming from toolchains)
    mag2 = (x * x) + (y * y) + (z * z) + (w * w)
    if mag2 <= 0.0:
        return (_qfloat(0.0), _qfloat(0.0), _qfloat(0.0), _qfloat(1.0))
    inv = 1.0 / math.sqrt(mag2)
    x *= inv
    y *= inv
    z *= inv
    w *= inv

    # Canonicalize sign: ensure w >= 0 (or, if w == 0, first non-zero component positive).
    if w < 0.0:
        x, y, z, w = -x, -y, -z, -w
    elif w == 0.0:
        if x < 0.0 or (x == 0.0 and (y < 0.0 or (y == 0.0 and z < 0.0))):
            x, y, z, w = -x, -y, -z, -w

    return (_qfloat(x), _qfloat(y), _qfloat(z), _qfloat(w))


def _mdl_node_canonical_orientation(node: MDLNode) -> tuple[int, int, int, int]:
    """Canonical orientation for equality/hash: prefer meaningful controller value, else scalar field.

    Values are compared as normalized quaternions so toolchain scaling doesn't break equality.
    """
    from_ctrl = _mdl_node_orientation_from_controller(node)
    if from_ctrl is not None:
        x, y, z, w = from_ctrl
        return _mdl_canonicalize_quaternion(x, y, z, w)
    ori = node.orientation
    if ori is None:
        return (_qfloat(0.0), _qfloat(0.0), _qfloat(0.0), _qfloat(1.0))
    return _mdl_canonicalize_quaternion(float(ori.x), float(ori.y), float(ori.z), float(ori.w))


def _mdl_node_effective_controllers(node: MDLNode) -> dict[tuple[int, bool], MDLController]:
    """Return controllers canonicalized for semantic equality.

    MDLOps can emit explicit controller blocks for values that are already represented
    redundantly by scalar node fields (position/orientation) or defaults (scale/alpha).
    For equality, we treat those redundant constant controllers as optional.
    """
    out: dict[tuple[int, bool], MDLController] = {}
    ctrls = node.controllers
    if not ctrls:
        return out

    for c in ctrls:
        ctype = c.controller_type
        is_bezier = c.is_bezier
        rows = c.rows
        if not rows:
            continue

        # POSITION/ORIENTATION are handled via canonical scalar comparisons (see _mdl_node_canonical_*).
        # Do not include them as controllers to compare separately, since toolchains can represent them
        # either as scalar fields or as a controller row.
        try:
            if int(ctype) in (8, 20):
                continue
        except Exception:
            pass

        # Only drop redundant controllers for non-bezier (bezier flag changes interpretation/storage).
        if not is_bezier:
            r0 = rows[0]
            data = r0.data

            try:
                # SCALE: default 1.0 is redundant
                if int(ctype) == 36 and len(data) >= 1:
                    if _qfloat(float(data[0])) == _qfloat(1.0):
                        continue
                # ALPHA: default 1.0 is redundant
                if int(ctype) == 132 and len(data) >= 1:
                    if _qfloat(float(data[0])) == _qfloat(1.0):
                        continue
            except Exception:
                # If anything odd happens (types/lengths), don't drop the controller.
                pass

        out[(ctype, is_bezier)] = c

    return out


def _mdl_controllers_equivalent(
    a_node: MDLNode,
    b_node: MDLNode,
    *,
    ignore_keys: set[str] | None,
    _visited: set[tuple[int, int]],
) -> bool:
    a_map = _mdl_node_effective_controllers(a_node)
    b_map = _mdl_node_effective_controllers(b_node)
    if set(a_map.keys()) != set(b_map.keys()):
        return False
    for k in a_map.keys():
        ar = [] if a_map[k].rows is None else a_map[k].rows
        br = [] if b_map[k].rows is None else b_map[k].rows
        if not _mdl_deep_eq(ar, br, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_ROWS):
            return False
    return True


def _qfloat(v: float) -> int:
    """Quantize float to a stable integer for approximate equality + hashing."""
    if math.isnan(v):
        # NaN != NaN by default; normalize to a deterministic sentinel.
        return 0x7FFFFFFF
    if math.isinf(v):
        return 0x7FFFFFFE if v > 0 else -0x7FFFFFFE
    return int(round(v * _MDL_FLOAT_SCALE))


class _Vector2ListProxy:
    """List-like adapter for UV lists.

    Canonical meshes store UVs as `vertex_uv1: list[Vector2]`.
    Some legacy tooling expects `vertex_uv: list[tuple[float, float]]`.

    This proxy provides a minimal list API and normalizes tuple/list inputs into Vector2.
    """

    def __init__(self, backing: list[Vector2]):
        self._backing = backing

    def append(self, v: Vector2 | tuple[float, float] | list[float]) -> None:
        if isinstance(v, Vector2):
            self._backing.append(v)
            return
        if isinstance(v, (tuple, list)) and len(v) >= 2:
            self._backing.append(Vector2(float(v[0]), float(v[1])))
            return
        raise TypeError(f"Unsupported UV value: {v!r}")

    def __len__(self) -> int:
        return len(self._backing)

    def __iter__(self):
        return iter(self._backing)

    def __getitem__(self, idx: int) -> Vector2:
        return self._backing[idx]


def _norm_value(v: Any, *, ignore_keys: set[str] | None = None) -> Any:
    """Normalize MDL values into hashable, approx-stable representations."""
    if v is None:
        return None

    if isinstance(v, (bool, int, str)):
        return v

    if isinstance(v, IntFlag):
        return int(v)

    if isinstance(v, float):
        return ("f", _qfloat(v))

    if isinstance(v, (Vector2, Vector3, Vector4)):
        parts: list[Any] = [("f", _qfloat(float(v.x))), ("f", _qfloat(float(v.y)))]
        if isinstance(v, (Vector3, Vector4)):
            parts.append(("f", _qfloat(float(v.z))))
        if isinstance(v, Vector4):
            parts.append(("f", _qfloat(float(v.w))))
        return ("vec", tuple(parts))

    if isinstance(v, Color):
        # Explicit component access (avoid getattr/hasattr patterns).
        return (
            "color",
            (
                ("f", _qfloat(float(v.r))),
                ("f", _qfloat(float(v.g))),
                ("f", _qfloat(float(v.b))),
                ("f", _qfloat(float(v.a))),
            ),
        )

    if isinstance(v, (list, tuple)):
        return tuple(_norm_value(x, ignore_keys=ignore_keys) for x in v)

    if isinstance(v, dict):
        return tuple((k, _norm_value(val, ignore_keys=ignore_keys)) for k, val in sorted(v.items(), key=lambda kv: str(kv[0])))

    dct = v.__dict__
    if isinstance(dct, dict):
        ignore = ignore_keys or set()
        items = []
        for k in sorted(dct.keys()):
            # Ignore private/internal implementation details (caches, parent pointers, etc.)
            if str(k).startswith("_"):
                continue
            if k in ignore:
                continue
            items.append((k, _norm_value(dct[k], ignore_keys=ignore_keys)))
        return (v.__class__.__name__, tuple(items))

    return v


def _mdl_eq(a: Any, b: Any, *, ignore_keys: set[str] | None = None) -> bool:
    # NOTE: Kept for backwards-compatibility with callers that expect a direct equality check,
    # but it internally routes through the faster streaming comparator for performance reasons.
    return _mdl_deep_eq(a, b, ignore_keys=ignore_keys)


def _mdl_hash(
    v: Any,
    *,
    ignore_keys: set[str] | None = None,
) -> int:
    # NOTE: Hashing mutable objects is inherently risky; callers must not mutate after hashing.
    return _mdl_deep_hash(v, ignore_keys=ignore_keys)


def _mdl_collect_nodes(root: MDLNode) -> list[MDLNode]:
    nodes: list[MDLNode] = []
    stack: list[MDLNode] = [root]
    while stack:
        n = stack.pop()
        nodes.append(n)
        # Determinism for equivalency checks
        try:
            kids = sorted(n.children, key=lambda c: c.name)
        except Exception:
            kids = list(n.children)
        stack.extend(reversed(kids))
    return nodes


def _mdl_build_parent_name_map(root: MDLNode) -> dict[str, str | None]:
    """Map node name -> parent node name (or None for root)."""
    parent_by_name: dict[str, str | None] = {}
    stack: list[tuple[MDLNode, str | None]] = [(root, None)]
    while stack:
        node, parent_name = stack.pop()
        parent_by_name[node.name] = parent_name
        try:
            kids = sorted(node.children, key=lambda c: c.name)
        except Exception:
            kids = list(node.children)
        for child in kids:
            stack.append((child, node.name))
    return parent_by_name


def _mdl_ids_equivalent_subtree(a_root: MDLNode, b_root: MDLNode) -> bool:
    """Check node_id/parent_id equivalency for a subtree without requiring exact integer matches.

    The *semantic truth* of hierarchy is the parent/child structure keyed by node names (ASCII uses
    names; binary stores offsets + name-index + ids). We therefore:
    - Require the same set of unique node names on both sides
    - Require each side's id labeling, if present, is internally self-consistent with its hierarchy
      (parent_id points to the actual parent node_id when both are known)
    - Only enforce cross-model id mapping when both sides are fully labeled
    """
    a_nodes = _mdl_collect_nodes(a_root)
    b_nodes = _mdl_collect_nodes(b_root)

    a_by_name: dict[str, MDLNode] = {}
    b_by_name: dict[str, MDLNode] = {}
    for n in a_nodes:
        if n.name in a_by_name:
            return False
        a_by_name[n.name] = n
    for n in b_nodes:
        if n.name in b_by_name:
            return False
        b_by_name[n.name] = n
    if set(a_by_name.keys()) != set(b_by_name.keys()):
        return False

    a_parent_name = _mdl_build_parent_name_map(a_root)
    b_parent_name = _mdl_build_parent_name_map(b_root)

    # Build id<->name maps where possible.
    a_id_to_name: dict[int, str] = {}
    b_id_to_name: dict[int, str] = {}
    a_name_to_id: dict[str, int] = {}
    b_name_to_id: dict[str, int] = {}

    for name, node in a_by_name.items():
        if node.node_id >= 0:
            nid = int(node.node_id)
            if nid in a_id_to_name:
                return False
            a_id_to_name[nid] = name
            a_name_to_id[name] = nid
    for name, node in b_by_name.items():
        if node.node_id >= 0:
            nid = int(node.node_id)
            if nid in b_id_to_name:
                return False
            b_id_to_name[nid] = name
            b_name_to_id[name] = nid

    # Validate parent_id consistency *within a single model* (no cross-model coupling).
    # If ids are partially missing, we only validate the relationships that are present.
    def _validate_parent_ids_self_consistent(
        by_name: dict[str, MDLNode],
        name_to_id: dict[str, int],
        parent_name_map: dict[str, str | None],
    ) -> bool:
        for name, node in by_name.items():
            expected_parent_name = parent_name_map.get(name)
            pid = int(node.parent_id or -1)
            # Subtree root: the chosen comparison root may not be the true model root, so its
            # parent_id can legitimately point outside this subtree. Do not constrain it here.
            if expected_parent_name is None:
                continue

            # Non-root: if parent_id is present and both node+parent have ids assigned, it must match.
            if pid >= 0:
                parent_id_expected = name_to_id.get(expected_parent_name)
                if parent_id_expected is not None and pid != parent_id_expected:
                    return False
            # If pid is missing (<0), that's allowed (common in ASCII-derived structures),
            # because the true hierarchy is still represented by the children list.
        return True

    if not _validate_parent_ids_self_consistent(a_by_name, a_name_to_id, a_parent_name):
        return False
    if not _validate_parent_ids_self_consistent(b_by_name, b_name_to_id, b_parent_name):
        return False

    # Cross-validate parent edges under the induced id mapping, when both sides are fully labeled.
    a_fully_labeled = len(a_name_to_id) == len(a_by_name)
    b_fully_labeled = len(b_name_to_id) == len(b_by_name)
    if a_fully_labeled and b_fully_labeled:
        id_map: dict[int, int] = {a_name_to_id[name]: b_name_to_id[name] for name in a_by_name.keys()}
        # Ensure bijection (injective)
        if len(set(id_map.values())) != len(id_map):
            return False
        for name, a_node in a_by_name.items():
            b_node = b_by_name[name]
            a_pid = int(a_node.parent_id or -1)
            b_pid = int(b_node.parent_id or -1)
            if a_parent_name[name] is None:
                # subtree root: parent_id may point outside the subtree
                continue
            # Many pipelines (notably ASCII animation nodes) do not populate parent_id at all,
            # because parent relationships are tracked by name. Only enforce parent_id mapping
            # when *both* sides actually provide a non-negative parent_id.
            if a_pid >= 0 and b_pid >= 0:
                if id_map.get(a_pid) != b_pid:
                    return False

    return True


def _mdl_validate_ids_self_consistent(root: MDLNode) -> bool:
    """Validate node_id/parent_id are internally consistent with the hierarchy when present.

    - node_id must be unique for all nodes where node_id >= 0
    - for any node with parent_id >= 0, its parent_id must resolve to the actual parent node
      if that parent has a node_id >= 0.
    """
    nodes = _mdl_collect_nodes(root)
    by_name = {n.name: n for n in nodes}
    parent_by_name = _mdl_build_parent_name_map(root)

    id_to_name: dict[int, str] = {}
    name_to_id: dict[str, int] = {}
    for n in nodes:
        nid = int(n.node_id or -1)
        if nid < 0:
            continue
        if nid in id_to_name:
            return False
        id_to_name[nid] = n.name
        name_to_id[n.name] = nid

    for name, node in by_name.items():
        expected_parent_name = parent_by_name.get(name)
        pid = int(node.parent_id or -1)
        if expected_parent_name is None:
            # root: parent_id should be negative if present
            if pid >= 0:
                return False
            continue
        if pid < 0:
            # allowed to be missing
            continue
        expected_parent_id = name_to_id.get(expected_parent_name)
        if expected_parent_id is not None and pid != expected_parent_id:
            return False
    return True


def _mdl_quat_is_zeroish(x: float, y: float, z: float, w: float) -> bool:
    # A bunch of toolchains (and corrupted/placeholder data) can emit 0 quats. Treat as invalid.
    return _qfloat(x) == _qfloat(0.0) and _qfloat(y) == _qfloat(0.0) and _qfloat(z) == _qfloat(0.0) and _qfloat(w) == _qfloat(0.0)


def _mdl_node_parent_edges_by_name(nodes: list[MDLNode]) -> dict[str, str | None]:
    """Build parent mapping from children edges, independent of root choice."""
    parent: dict[str, str | None] = {n.name: None for n in nodes}
    by_id = {id(n): n for n in nodes}
    for p in nodes:
        for c in p.children or []:
            if id(c) in by_id:
                parent[c.name] = p.name
    return parent


def _mdl_canonical_controllers(
    node: MDLNode,
    *,
    drop_transform_controllers: bool = False,
) -> dict[tuple[int, bool], tuple[tuple[int, tuple[int, ...]], ...]]:
    """Canonicalize controllers as a mapping: (type, is_bezier) -> sorted rows.

    Each row is represented as (quantized_time, quantized_data_tuple).
    """
    out: dict[tuple[int, bool], list[tuple[int, tuple[int, ...]]]] = {}
    for c in node.controllers or []:
        try:
            ctype = int(c.controller_type)
        except Exception:
            continue
        is_bezier = bool(c.is_bezier or False)
        # MDLOps treats node header transforms (position/orientation) as authoritative for *geometry* nodes,
        # and will often omit controller types 8/20 when decompiling binaries. For MDLOps-compat equality,
        # we canonicalize by dropping those transform controllers when comparing geometry trees.
        if drop_transform_controllers and ctype in (8, 20):
            continue
        rows = c.rows or []
        if not rows:
            continue
        lst = out.setdefault((ctype, is_bezier), [])
        for r in rows:
            t = _qfloat(float(r.time or 0.0))
            data = r.data or []
            qdata = tuple(_qfloat(float(x)) for x in data)
            lst.append((t, qdata))

    # Make immutable + deterministic (sort by time then data)
    return {k: tuple(sorted(v)) for k, v in out.items()}


def _mdl_canonical_controllers_hashable(
    node: MDLNode,
    *,
    drop_transform_controllers: bool = False,
) -> tuple[tuple[tuple[int, bool], tuple[tuple[int, tuple[int, ...]], ...]], ...]:
    """Hashable form of _mdl_canonical_controllers (sorted items)."""
    d = _mdl_canonical_controllers(node, drop_transform_controllers=drop_transform_controllers)
    return tuple(sorted(d.items()))


def _mdl_node_canonical_position_from_controllers(node: MDLNode) -> tuple[int, int, int] | None:
    """Extract a canonical POSITION controller (if present) for comparison."""
    ctrls = _mdl_canonical_controllers(node)
    key = (8, False)
    rows = ctrls.get(key)
    if not rows:
        return None
    # Use the first row at time 0 if present, else first row by sort order
    t, data = rows[0]
    if len(data) < 3:
        return None
    return (data[0], data[1], data[2])


def _mdl_node_canonical_orientation_from_controllers(node: MDLNode) -> tuple[int, int, int, int] | None:
    ctrls = _mdl_canonical_controllers(node)
    key = (20, False)
    rows = ctrls.get(key)
    if not rows:
        return None
    t, data = rows[0]
    if len(data) < 4:
        return None
    # Normalize + sign-canon using float value before quantize would be better, but we only have ints here.
    # So we accept quantized normalization by re-expanding to float.
    x = data[0] / _MDL_FLOAT_SCALE
    y = data[1] / _MDL_FLOAT_SCALE
    z = data[2] / _MDL_FLOAT_SCALE
    w = data[3] / _MDL_FLOAT_SCALE
    if _mdl_quat_is_zeroish(x, y, z, w):
        return None
    return _mdl_canonicalize_quaternion(x, y, z, w)


def _mdl_node_header_position(node: MDLNode) -> tuple[int, int, int]:
    pos = node.position
    if pos is None:
        return (_qfloat(0.0), _qfloat(0.0), _qfloat(0.0))
    return (_qfloat(float(pos.x)), _qfloat(float(pos.y)), _qfloat(float(pos.z)))


def _mdl_node_header_orientation(node: MDLNode) -> tuple[int, int, int, int]:
    ori = node.orientation
    if ori is None:
        return (_qfloat(0.0), _qfloat(0.0), _qfloat(0.0), _qfloat(1.0))
    return _mdl_canonicalize_quaternion(float(ori.x), float(ori.y), float(ori.z), float(ori.w))


def _mdl_node_canonical_position_strict(node: MDLNode, *, prefer_controllers: bool = True) -> tuple[int, int, int]:
    """Canonical node position.

    - Geometry nodes: compare scalar position (what actually gets written into binary headers).
    - Animation nodes: scalar is usually null, but if a position controller exists it is the semantic payload.
      We canonicalize to controller when present, otherwise scalar.
    """
    if prefer_controllers:
        ctrl = _mdl_node_canonical_position_from_controllers(node)
        if ctrl is not None:
            return ctrl
    return _mdl_node_header_position(node)


def _mdl_node_canonical_orientation_strict(node: MDLNode, *, prefer_controllers: bool = True) -> tuple[int, int, int, int]:
    if prefer_controllers:
        ctrl = _mdl_node_canonical_orientation_from_controllers(node)
        if ctrl is not None:
            return ctrl
    return _mdl_node_header_orientation(node)


def _mdl_mesh_validate_aliases(mesh: MDLMesh) -> bool:
    """vertex_uvs is a back-compat alias for vertex_uv1; it must be consistent if populated."""
    uv1 = mesh.vertex_uv1
    uva = mesh.vertex_uvs
    if uva is None or uv1 is None:
        return True
    return uva is uv1 or uva == uv1


def _mdl_mesh_equal(a: MDLMesh, b: MDLMesh) -> bool:
    """Canonical mesh equality."""
    if not (_mdl_mesh_validate_aliases(a) and _mdl_mesh_validate_aliases(b)):
        return False

    # Common scalar fields that materially affect rendering and are present in ASCII.
    if a.texture_1 != b.texture_1:
        return False
    if a.texture_2 != b.texture_2:
        return False
    if a.transparency_hint != b.transparency_hint:
        return False
    if a.has_lightmap != b.has_lightmap:
        return False
    if a.rotate_texture != b.rotate_texture:
        return False
    if a.background_geometry != b.background_geometry:
        return False
    if a.shadow != b.shadow:
        return False
    if a.beaming != b.beaming:
        return False
    if a.render != b.render:
        return False
    if a.dirt_enabled != b.dirt_enabled:
        return False
    if a.dirt_texture != b.dirt_texture:
        return False
    if a.dirt_coordinate_space != b.dirt_coordinate_space:
        return False

    # Skin-specific data
    if isinstance(a, MDLSkin) and isinstance(b, MDLSkin):
        if not _mdl_deep_eq(a.qbones, b.qbones, ignore_keys=_MDL_EQ_IGNORE_KEYS):
            return False
        if not _mdl_deep_eq(a.tbones, b.tbones, ignore_keys=_MDL_EQ_IGNORE_KEYS):
            return False
        if not _mdl_deep_eq(a.bone_indices, b.bone_indices, ignore_keys=_MDL_EQ_IGNORE_KEYS):
            return False
        if not _mdl_deep_eq(a.vertex_bones, b.vertex_bones, ignore_keys=_MDL_EQ_IGNORE_KEYS):
            return False
    elif isinstance(a, MDLSkin) != isinstance(b, MDLSkin):
        return False

    # Colors (present in ASCII and materially affect rendering).
    if not _mdl_deep_eq(a.diffuse, b.diffuse, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if not _mdl_deep_eq(a.ambient, b.ambient, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if not _mdl_deep_eq(a.bb_min, b.bb_min, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if not _mdl_deep_eq(a.bb_max, b.bb_max, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if _qfloat(float(a.radius)) != _qfloat(float(b.radius)):
        return False
    if not _mdl_deep_eq(a.average, b.average, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if _qfloat(float(a.area)) != _qfloat(float(b.area)):
        return False

    # Geometry arrays
    if not _mdl_deep_eq(a.vertex_positions, b.vertex_positions, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False

    # Per-vertex normals
    if not _mdl_deep_eq(a.vertex_normals or [], b.vertex_normals or [], ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False

    # UVs (can be empty lists)
    if not _mdl_deep_eq(a.vertex_uv1, b.vertex_uv1, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if not _mdl_deep_eq(a.vertex_uv2, b.vertex_uv2, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False

    # Faces are authoritative (carry normals/plane/material/tvert indices/smoothgroups).
    if not _mdl_deep_eq(a.faces, b.faces, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False

    return True


def _mdl_mesh_hash(mesh: MDLMesh) -> int:
    """Hash consistent with _mdl_mesh_equal."""
    h = hash(("mesh", mesh.texture_1, mesh.texture_2))
    h ^= hash(("background_geometry", mesh.background_geometry))
    h ^= hash(("beaming", mesh.beaming))
    h ^= hash(("dirt_coordinate_space", mesh.dirt_coordinate_space))
    h ^= hash(("dirt_enabled", mesh.dirt_enabled))
    h ^= hash(("dirt_texture", mesh.dirt_texture))
    h ^= hash(("has_lightmap", mesh.has_lightmap))
    h ^= hash(("render", mesh.render))
    h ^= hash(("rotate_texture", mesh.rotate_texture))
    h ^= hash(("shadow", mesh.shadow))
    h ^= hash(("transparency_hint", mesh.transparency_hint))

    # Skin-specific data
    if isinstance(mesh, MDLSkin):
        h ^= _mdl_deep_hash(mesh.qbones, ignore_keys=_MDL_EQ_IGNORE_KEYS)
        h ^= _mdl_deep_hash(mesh.tbones, ignore_keys=_MDL_EQ_IGNORE_KEYS)
        h ^= _mdl_deep_hash(mesh.bone_indices, ignore_keys=_MDL_EQ_IGNORE_KEYS)
        h ^= _mdl_deep_hash(mesh.vertex_bones, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    h ^= _mdl_deep_hash(mesh.diffuse, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    h ^= _mdl_deep_hash(mesh.ambient, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    h ^= _mdl_deep_hash(mesh.bb_min, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    h ^= _mdl_deep_hash(mesh.bb_max, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    h ^= hash(_qfloat(float(mesh.radius)))
    h ^= _mdl_deep_hash(mesh.average, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    h ^= hash(_qfloat(float(mesh.area)))

    h ^= _mdl_deep_hash(mesh.vertex_positions, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    h ^= _mdl_deep_hash(mesh.vertex_normals or [], ignore_keys=_MDL_EQ_IGNORE_KEYS)

    h ^= _mdl_deep_hash(mesh.vertex_uv1, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    h ^= _mdl_deep_hash(mesh.vertex_uv2, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    h ^= _mdl_deep_hash(mesh.faces, ignore_keys=_MDL_EQ_IGNORE_KEYS)
    return h


def _mdl_node_validate_node_type_consistent(node: MDLNode) -> bool:
    """node.node_type should not contradict attached data if set.

    We consider node.node_type authoritative only when it matches derived type from attached components.
    """
    derived = MDLNodeType.DUMMY
    if node.light is not None:
        derived = MDLNodeType.LIGHT
    elif node.emitter is not None:
        derived = MDLNodeType.EMITTER
    elif node.reference is not None:
        derived = MDLNodeType.REFERENCE
    elif node.saber is not None:
        derived = MDLNodeType.SABER
    elif node.aabb is not None:
        derived = MDLNodeType.AABB
    elif node.skin is not None:
        # Skinned meshes are still TRIMESH nodes; "skin-ness" is carried by attached payload/flags.
        derived = MDLNodeType.TRIMESH
    elif node.dangly is not None:
        derived = MDLNodeType.DANGLYMESH
    elif node.mesh is not None:
        derived = MDLNodeType.TRIMESH

    nt = node.node_type or MDLNodeType.DUMMY
    # Allow DUMMY as "unspecified" in binary-derived models, but disallow conflicting explicit types.
    return nt == MDLNodeType.DUMMY or nt == derived


def _mdl_node_payload_equal(
    a: MDLNode,
    b: MDLNode,
    *,
    in_geometry_tree: bool,
) -> bool:
    """Compare node payload excluding hierarchy edges and raw ids."""
    if a.name != b.name:
        return False
    # Geometry nodes: MDLOps uses node header transforms and can omit pos/orient controllers.
    prefer_controllers = not in_geometry_tree
    if _mdl_node_canonical_position_strict(a, prefer_controllers=prefer_controllers) != _mdl_node_canonical_position_strict(b, prefer_controllers=prefer_controllers):
        return False
    if _mdl_node_canonical_orientation_strict(a, prefer_controllers=prefer_controllers) != _mdl_node_canonical_orientation_strict(b, prefer_controllers=prefer_controllers):
        return False

    # Presence/type of attachments
    if (a.light is None) != (b.light is None):
        return False
    if (a.emitter is None) != (b.emitter is None):
        return False
    if (a.reference is None) != (b.reference is None):
        return False
    if (a.mesh is None) != (b.mesh is None):
        return False
    if (a.skin is None) != (b.skin is None):
        return False
    if (a.dangly is None) != (b.dangly is None):
        return False
    if (a.aabb is None) != (b.aabb is None):
        return False
    if (a.saber is None) != (b.saber is None):
        return False

    # Deep-compare attachments (they already use quantized deep equality)
    if a.light is not None and not _mdl_deep_eq(a.light, b.light, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if a.emitter is not None and not _mdl_deep_eq(a.emitter, b.emitter, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if a.reference is not None and not _mdl_deep_eq(a.reference, b.reference, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False

    # Mesh-like payload can be huge; rely on deep compare but validate aliases first.
    if a.mesh is not None and b.mesh is not None:
        if not _mdl_mesh_equal(a.mesh, b.mesh):
            return False

    if a.skin is not None and not _mdl_deep_eq(a.skin, b.skin, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if a.dangly is not None and not _mdl_deep_eq(a.dangly, b.dangly, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if a.aabb is not None and not _mdl_deep_eq(a.aabb, b.aabb, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False
    if a.saber is not None and not _mdl_deep_eq(a.saber, b.saber, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False

    # Controllers: compare canonicalized (type,is_bezier)->rows map.
    # For geometry nodes, drop transform controllers (8/20) to match MDLOps binary decompilation behavior.
    if _mdl_canonical_controllers(a, drop_transform_controllers=in_geometry_tree) != _mdl_canonical_controllers(b, drop_transform_controllers=in_geometry_tree):
        return False

    # node_type consistency validation (no ignoring)
    if not (_mdl_node_validate_node_type_consistent(a) and _mdl_node_validate_node_type_consistent(b)):
        return False

    return True


def _mdl_animation_nodes_by_name(anim: MDLAnimation) -> dict[str, MDLNode]:
    nodes = anim.all_nodes()
    out: dict[str, MDLNode] = {}
    for n in nodes:
        if n.name in out:
            # Non-unique names are not representable canonically
            raise ValueError(f"Duplicate animation node name: {n.name!r}")
        out[n.name] = n
    return out


def _mdl_animation_equal(
    a: MDLAnimation,
    b: MDLAnimation,
) -> bool:
    if a.name != b.name:
        return False
    if a.root_model != b.root_model:
        return False
    if _qfloat(float(a.anim_length)) != _qfloat(float(b.anim_length)):
        return False
    if _qfloat(float(a.transition_length)) != _qfloat(float(b.transition_length)):
        return False
    if not _mdl_deep_eq(a.events, b.events, ignore_keys=_MDL_EQ_IGNORE_KEYS):
        return False

    # Compare node graph canonically by name+parent edges, independent of root selection.
    a_nodes = list(_mdl_animation_nodes_by_name(a).values())
    b_nodes = list(_mdl_animation_nodes_by_name(b).values())
    if {n.name for n in a_nodes} != {n.name for n in b_nodes}:
        return False
    a_parent = _mdl_node_parent_edges_by_name(a_nodes)
    b_parent = _mdl_node_parent_edges_by_name(b_nodes)
    if a_parent != b_parent:
        return False
    a_by = {n.name: n for n in a_nodes}
    b_by = {n.name: n for n in b_nodes}
    for name in a_by.keys():
        if not _mdl_node_payload_equal(a_by[name], b_by[name], in_geometry_tree=False):
            return False

    # Validate ids (no ignoring) as equivalency: self-consistent + equivalent labeling
    if not (_mdl_validate_ids_self_consistent(a.root) and _mdl_validate_ids_self_consistent(b.root)):
        return False
    if not _mdl_ids_equivalent_subtree(a.root, b.root):
        return False
    return True


def _mdl_float_eq(
    a: float,
    b: float,
) -> bool:
    """Approximate equality for MDL floats (1e-4 tolerance)."""
    if math.isnan(a):
        return math.isnan(b)
    if math.isinf(a):
        return math.isinf(b) and ((a > 0) == (b > 0))
    # Use 1e-4 absolute tolerance to handle toolchain formatting drift (%.7g vs raw binary).
    return math.isclose(a, b, abs_tol=1e-4, rel_tol=1e-9)


def _mdl_deep_eq(
    a: Any,
    b: Any,
    *,
    ignore_keys: set[str] | None = None,
    _visited: set[tuple[int, int]] | None = None,
    _ctx: int = _CTX_NONE,
) -> bool:
    """High-performance deep equality with float quantization and cycle protection.

    This avoids building large intermediate normalized tuples (which was expensive for meshes),
    while still enforcing the same approximate-equality semantics as hashing.
    """
    if a is b:
        return True
    if a is None or b is None:
        return a is None and b is None

    # Cycle protection for graphs (models can have back-refs/caches in some tooling contexts).
    if _visited is None:
        _visited = set()
    key = (id(a), id(b))
    if key in _visited:
        return True
    _visited.add(key)

    # Primitive fast-paths
    if isinstance(a, (bool, int, str)) or isinstance(b, (bool, int, str)):
        return a == b
    if isinstance(a, IntFlag) or isinstance(b, IntFlag):
        try:
            return int(a) == int(b)
        except Exception:
            return a == b
    if isinstance(a, float) or isinstance(b, float):
        if not (isinstance(a, float) and isinstance(b, float)):
            return False
        return _mdl_float_eq(a, b)

    # Vector-like (Vector2/3/4 etc)
    if isinstance(a, (Vector2, Vector3, Vector4)) and isinstance(b, (Vector2, Vector3, Vector4)):
        if type(a) is not type(b):
            return False
        # Compare component-wise with the same quantization used for hashing.
        if not _mdl_float_eq(float(a.x), float(b.x)):
            return False
        if not _mdl_float_eq(float(a.y), float(b.y)):
            return False
        if isinstance(a, (Vector3, Vector4)):
            if not _mdl_float_eq(float(a.z), float(b.z)):
                return False
        if isinstance(a, Vector4):
            if not _mdl_float_eq(float(a.w), float(b.w)):
                return False
        return True
    elif isinstance(a, (Vector2, Vector3, Vector4)) or isinstance(b, (Vector2, Vector3, Vector4)):
        return False

    # MDLFace: specialized canonical equality (ignoring lossy fields)
    if isinstance(a, MDLFace) and isinstance(b, MDLFace):
        if a.v1 != b.v1 or a.v2 != b.v2 or a.v3 != b.v3:
            return False
        if a.material != b.material:
            return False
        if a.smoothgroup != b.smoothgroup:
            return False
        # Canon t-verts
        at1 = a.v1 if a.t1 < 0 else a.t1
        bt1 = b.v1 if b.t1 < 0 else b.t1
        if at1 != bt1:
            return False

        at2 = a.v2 if a.t2 < 0 else a.t2
        bt2 = b.v2 if b.t2 < 0 else b.t2
        if at2 != bt2:
            return False

        at3 = a.v3 if a.t3 < 0 else a.t3
        bt3 = b.v3 if b.t3 < 0 else b.t3
        if at3 != bt3:
            return False

        return True
    elif isinstance(a, MDLFace) or isinstance(b, MDLFace):
        return False

    # Color (pykotor.common.misc.Color)
    if isinstance(a, Color) and isinstance(b, Color):
        if not _mdl_float_eq(float(a.r), float(b.r)):
            return False
        if not _mdl_float_eq(float(a.g), float(b.g)):
            return False
        if not _mdl_float_eq(float(a.b), float(b.b)):
            return False
        if not _mdl_float_eq(float(a.a), float(b.a)):
            return False
        return True
    elif isinstance(a, Color) or isinstance(b, Color):
        return False

    # Sequences
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        if not (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple))):
            return False
        if len(a) != len(b):
            return False

        # Special case: children list is semantically keyed by node name (MDL hierarchy references by name).
        if _ctx == _CTX_CHILDREN and a:
            try:
                map_a = {x.name: x for x in a}
                map_b = {x.name: x for x in b}
            except Exception:
                map_a = None
                map_b = None
            if map_a is not None and map_b is not None and len(map_a) == len(a) and len(map_b) == len(b):
                if set(map_a.keys()) != set(map_b.keys()):
                    return False
                for name in map_a.keys():
                    if not _mdl_deep_eq(map_a[name], map_b[name], ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE):
                        return False
                return True

        # Special case: animations list is semantically keyed by (name, root_model)
        if _ctx == _CTX_ANIMS and a:
            try:

                def _akey(x: Any) -> tuple[str, str]:
                    return (str(x.name), str(x.root_model))

                map_a = {_akey(x): x for x in a}
                map_b = {_akey(x): x for x in b}
            except Exception:
                map_a = None
                map_b = None
            if map_a is not None and map_b is not None and len(map_a) == len(a) and len(map_b) == len(b):
                if set(map_a.keys()) != set(map_b.keys()):
                    return False
                for k in map_a.keys():
                    if not _mdl_deep_eq(map_a[k], map_b[k], ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE):
                        return False
                return True

        # Special case: controller rows list is semantically keyed by time
        if _ctx == _CTX_ROWS and a:
            try:

                def _tkey(x: Any) -> int:
                    return _qfloat(float(x.time))

                rows_a = sorted(a, key=_tkey)
                rows_b = sorted(b, key=_tkey)
            except Exception:
                rows_a = a
                rows_b = b
            for i, (av, bv) in enumerate(zip(rows_a, rows_b)):
                if not _mdl_deep_eq(av, bv, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE):
                    return False
            return True

        # Default: ordered pairwise compare
        for i, (av, bv) in enumerate(zip(a, b)):
            if not _mdl_deep_eq(av, bv, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE):
                return False
        return True

    # Dicts
    if isinstance(a, dict) or isinstance(b, dict):
        if not (isinstance(a, dict) and isinstance(b, dict)):
            return False
        if set(a.keys()) != set(b.keys()):
            return False
        for k in a.keys():
            if not _mdl_deep_eq(a[k], b[k], ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE):
                return False
        return True

    # Object __dict__ structural compare (skip privates + ignored keys)
    da = a.__dict__
    db = b.__dict__
    if isinstance(da, dict) and isinstance(db, dict):
        ignore = ignore_keys or set()
        keys_a = {k for k in da.keys() if not k.startswith("_") and k not in ignore}
        keys_b = {k for k in db.keys() if not k.startswith("_") and k not in ignore}
        if keys_a != keys_b:
            return False
        for k in keys_a:
            next_ctx = _CTX_NONE
            if k == "children":
                next_ctx = _CTX_CHILDREN
            elif k == "anims":
                next_ctx = _CTX_ANIMS
            elif k == "rows":
                next_ctx = _CTX_ROWS
            elif k == "controllers":
                next_ctx = _CTX_CONTROLLERS

            # Special-case canonical position/orientation on MDLNode.
            if isinstance(a, MDLNode) and isinstance(b, MDLNode) and k in ("position", "orientation"):
                if k == "position":
                    if _mdl_node_canonical_position(a) != _mdl_node_canonical_position(b):
                        return False
                    continue
                if k == "orientation":
                    if _mdl_node_canonical_orientation(a) != _mdl_node_canonical_orientation(b):
                        return False
                    continue

            # Special-case controllers on MDLNode: canonicalize redundant constant controllers.
            if next_ctx == _CTX_CONTROLLERS and isinstance(a, MDLNode) and isinstance(b, MDLNode):
                if not _mdl_controllers_equivalent(a, b, ignore_keys=ignore_keys, _visited=_visited):
                    return False
                continue

            if not _mdl_deep_eq(da[k], db[k], ignore_keys=ignore_keys, _visited=_visited, _ctx=next_ctx):
                return False
        return True

    # Fallback
    return a == b


def _mdl_deep_hash(
    v: Any,
    *,
    ignore_keys: set[str] | None = None,
    _visited: set[int] | None = None,
    _ctx: int = _CTX_NONE,
) -> int:
    """High-performance deep hash that matches _mdl_deep_eq's semantics.

    Uses float quantization so approximate float equality implies equal hashes.
    """
    if v is None:
        return hash(None)

    # Cycle protection: treat _visited as the *active recursion stack*, not a global "seen" set.
    # This keeps hashing consistent with deep equality even when graphs differ only by aliasing.
    if _visited is None:
        _visited = set()
    vid = id(v)
    if vid in _visited:
        return hash(("cycle", type(v).__name__))
    _visited.add(vid)
    try:
        # Primitives
        if isinstance(v, (bool, int, str)):
            return hash(v)
        if isinstance(v, IntFlag):
            return hash(int(v))
        if isinstance(v, float):
            return hash(("f", _qfloat(v)))

        # Vector-like
        if isinstance(v, (Vector2, Vector3, Vector4)):
            vec_parts: list[int] = [_qfloat(float(v.x)), _qfloat(float(v.y))]
            if isinstance(v, (Vector3, Vector4)):
                vec_parts.append(_qfloat(float(v.z)))
            if isinstance(v, Vector4):
                vec_parts.append(_qfloat(float(v.w)))
            return hash(("vec", tuple(vec_parts)))

        # MDLFace
        if isinstance(v, MDLFace):
            return hash(("face", v.v1, v.v2, v.v3, v.material, v.smoothgroup, v.v1 if v.t1 < 0 else v.t1, v.v2 if v.t2 < 0 else v.t2, v.v3 if v.t3 < 0 else v.t3))

        # Color
        if isinstance(v, Color):
            return hash(("color", (_qfloat(float(v.r)), _qfloat(float(v.g)), _qfloat(float(v.b)), _qfloat(float(v.a)))))

        # Sequences
        if isinstance(v, (list, tuple)):
            # Special: children list order-insensitive by node name
            if _ctx == _CTX_CHILDREN and v and isinstance(v[0], MDLNode):
                try:
                    child_items = sorted(((str(x.name), x) for x in v), key=lambda kv: str(kv[0]).lower())
                    return hash(("children", tuple((n, _mdl_deep_hash(x, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE)) for n, x in child_items)))
                except Exception:
                    pass

            # Special: anim list order-insensitive by (name, root_model)
            if _ctx == _CTX_ANIMS and v and isinstance(v[0], MDLAnimation):
                try:

                    def _akey(x: Any) -> tuple[str, str]:
                        return (str(x.name), str(x.root_model))

                    anim_items = sorted(((_akey(x), x) for x in v), key=lambda kv: str(kv[0]).lower())
                    return hash(("anims", tuple((k, _mdl_deep_hash(x, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE)) for k, x in anim_items)))
                except Exception:
                    pass

            # Special: controller rows order-insensitive by time
            if _ctx == _CTX_ROWS and v and isinstance(v[0], MDLControllerRow):
                try:

                    def _tkey(x: Any) -> int:
                        return _qfloat(float(x.time))

                    row_items = sorted(v, key=_tkey)
                    return hash(("rows", tuple(_mdl_deep_hash(x, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE) for x in row_items)))
                except Exception:
                    pass

            return hash(("seq", len(v), tuple(_mdl_deep_hash(x, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE) for x in v)))

        # Dicts
        if isinstance(v, dict):
            dict_items = tuple(
                sorted(((k, _mdl_deep_hash(val, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_NONE)) for k, val in v.items()), key=lambda kv: str(kv[0]).lower())
            )
            return hash(("dict", dict_items))

        # Object __dict__
        dct = v.__dict__
        if isinstance(dct, dict):
            ignore = ignore_keys or set()
            items: list[tuple[str, int]] = []
            for k in sorted(dct.keys()):
                if str(k).startswith("_") or k in ignore:
                    continue
                next_ctx = _CTX_NONE
                if k == "children":
                    next_ctx = _CTX_CHILDREN
                elif k == "anims":
                    next_ctx = _CTX_ANIMS
                elif k == "rows":
                    next_ctx = _CTX_ROWS
                elif k == "controllers":
                    next_ctx = _CTX_CONTROLLERS

                # Special-case canonical position/orientation on MDLNode.
                if isinstance(v, MDLNode) and k in ("position", "orientation"):
                    if k == "position":
                        items.append((k, hash(("pos", _mdl_node_canonical_position(v)))))
                        continue
                    if k == "orientation":
                        items.append((k, hash(("ori", _mdl_node_canonical_orientation(v)))))
                        continue

                # Special-case controllers on MDLNode: hash canonicalized effective controllers.
                if next_ctx == _CTX_CONTROLLERS and isinstance(v, MDLNode):
                    ctrls = _mdl_node_effective_controllers(v)
                    # Order-insensitive commutative combine (no sorting).
                    acc = 0
                    for (ctype, is_bezier), ctrl in ctrls.items():
                        h_key = hash((int(ctype) if ctype is not None else None, bool(is_bezier)))
                        h_rows = _mdl_deep_hash(ctrl.rows, ignore_keys=ignore_keys, _visited=_visited, _ctx=_CTX_ROWS)
                        acc ^= hash((h_key, h_rows))
                    items.append((k, hash((len(ctrls), acc))))
                    continue

                items.append((k, _mdl_deep_hash(dct[k], ignore_keys=ignore_keys, _visited=_visited, _ctx=next_ctx)))
            return hash((v.__class__.__name__, tuple(items)))

        return hash(v)
    finally:
        _visited.discard(vid)


class MDL(ComparableMixin):
    """Represents a MDL/MDX file.

    Attributes:
    ----------
        root: The root node of the model.
        anims: The animations stored in the model.
        name: The model name.
        fog: If fog affects the model.
        supermodel: Name of another model resource to import extra data from.

    References:
    ----------
        vendor/reone/src/libs/graphics/model.cpp - Model structure and rendering
        vendor/reone/include/reone/graphics/model.h - Model header definitions
        vendor/mdlops - MDL/MDX manipulation tool
        vendor/kotorblender/io_scene_kotor/format/mdl/ - Blender MDL loader/exporter
        vendor/KotOR.js/src/odyssey/OdysseyModel.ts - TypeScript model structure
        vendor/kotor/kotor/model/nodes.py - Python model node parsing
        vendor/xoreos-tools/src/resource/mdlmdx.cpp - MDL/MDX format parser
        Note: MDL/MDX are binary formats with separate geometry (.mdx) and structure (.mdl) files
    """

    BINARY_TYPE = ResourceType.MDL
    COMPARABLE_FIELDS = (
        "name",
        "fog",
        "supermodel",
        "classification",
        "classification_unk1",
        "animation_scale",
        "bmin",
        "bmax",
        "radius",
        "headlink",
        "compress_quaternions",
        "root",
    )
    COMPARABLE_SEQUENCE_FIELDS = ("anims",)

    def __init__(
        self,
    ):
        self.root: MDLNode = MDLNode()
        self.anims: list[MDLAnimation] = []
        # Back-compat: some engine/tooling expects a geometry_type field.
        self.geometry_type: MDLGeometryType = MDLGeometryType.GEOMETRY_NORMAL
        self.name: str = ""
        self.fog: bool = False
        self.supermodel: str = ""
        # ASCII/mdlops specific header fields
        self.classification: MDLClassification = MDLClassification.OTHER
        self.classification_unk1: int = 0
        self.animation_scale: float = 0.971
        self.bmin: Vector3 = Vector3(-5, -5, -1)
        self.bmax: Vector3 = Vector3(5, 5, 10)
        self.radius: float = 7.0
        self.headlink: str = ""
        self.compress_quaternions: int = 0

    # Back-compat aliases (used by Engines/PyKotorEngine tests/tooling)
    @property
    def animations(self) -> list[MDLAnimation]:
        return self.anims

    @animations.setter
    def animations(self, v: list[MDLAnimation]) -> None:
        self.anims = v

    @property
    def root_node(self) -> MDLNode:
        return self.root

    @root_node.setter
    def root_node(self, v: MDLNode) -> None:
        self.root = v

    def __eq__(self, other):
        if not isinstance(other, MDL):
            return NotImplemented
        # Header/scalars (canonical float compare)
        if self.name != other.name:
            return False
        if self.fog != other.fog:
            return False
        if self.supermodel != other.supermodel:
            return False
        if int(self.classification) != int(other.classification):
            return False
        if int(self.classification_unk1) != int(other.classification_unk1):
            return False
        if _qfloat(float(self.animation_scale)) != _qfloat(float(other.animation_scale)):
            return False
        if _qfloat(float(self.radius)) != _qfloat(float(other.radius)):
            return False
        if (
            _qfloat(float(self.bmin.x)) != _qfloat(float(other.bmin.x))
            or _qfloat(float(self.bmin.y)) != _qfloat(float(other.bmin.y))
            or _qfloat(float(self.bmin.z)) != _qfloat(float(other.bmin.z))
        ):
            return False
        if (
            _qfloat(float(self.bmax.x)) != _qfloat(float(other.bmax.x))
            or _qfloat(float(self.bmax.y)) != _qfloat(float(other.bmax.y))
            or _qfloat(float(self.bmax.z)) != _qfloat(float(other.bmax.z))
        ):
            return False
        if self.headlink != other.headlink:
            return False
        if int(self.compress_quaternions) != int(other.compress_quaternions):
            return False

        # Geometry graph by name+parent edges, independent of root selection.
        a_nodes = self.all_nodes()
        b_nodes = other.all_nodes()
        a_by: dict[str, MDLNode] = {}
        b_by: dict[str, MDLNode] = {}
        for n in a_nodes:
            if n.name in a_by:
                return False
            a_by[n.name] = n
        for n in b_nodes:
            if n.name in b_by:
                return False
            b_by[n.name] = n
        if set(a_by.keys()) != set(b_by.keys()):
            return False
        if _mdl_node_parent_edges_by_name(list(a_by.values())) != _mdl_node_parent_edges_by_name(list(b_by.values())):
            return False
        for name in a_by.keys():
            if not _mdl_node_payload_equal(a_by[name], b_by[name], in_geometry_tree=True):
                return False

        # Validate ids (no ignoring) as equivalency.
        if not (_mdl_validate_ids_self_consistent(self.root) and _mdl_validate_ids_self_consistent(other.root)):
            return False
        if not _mdl_ids_equivalent_subtree(self.root, other.root):
            return False

        # Animations matched by (name, root_model)
        def _akey(anim: MDLAnimation) -> tuple[str, str]:
            return (anim.name, anim.root_model)

        if len(self.anims) != len(other.anims):
            return False
        a_anims = {_akey(a): a for a in self.anims}
        b_anims = {_akey(a): a for a in other.anims}
        if len(a_anims) != len(self.anims) or len(b_anims) != len(other.anims):
            return False
        if set(a_anims.keys()) != set(b_anims.keys()):
            return False
        for k in a_anims.keys():
            if not _mdl_animation_equal(a_anims[k], b_anims[k]):
                return False

        return True

    def __hash__(self):
        # WARNING: MDL objects are mutable; mutating after hashing is unsafe for set/dict keys.
        # Hash must match __eq__. Since node_id/parent_id are compared via equivalency, we hash
        # the canonical graph keyed by node name and parent-name edges, not raw ids.
        h = 0
        h ^= hash(self.name)
        h ^= hash(self.fog)
        h ^= hash(self.supermodel)
        h ^= hash(int(self.classification))
        h ^= hash(int(self.classification_unk1))
        h ^= hash(_qfloat(float(self.animation_scale)))
        h ^= hash(_qfloat(float(self.radius)))
        h ^= hash((_qfloat(float(self.bmin.x)), _qfloat(float(self.bmin.y)), _qfloat(float(self.bmin.z))))
        h ^= hash((_qfloat(float(self.bmax.x)), _qfloat(float(self.bmax.y)), _qfloat(float(self.bmax.z))))
        h ^= hash(self.headlink)
        h ^= hash(int(self.compress_quaternions))

        nodes = self.all_nodes()
        by = {n.name: n for n in nodes}
        parent = _mdl_node_parent_edges_by_name(list(by.values()))
        # stable order by name
        for name in sorted(by.keys()):
            n = by[name]
            h ^= hash(("node", name, parent.get(name)))
            h ^= hash(_mdl_node_header_position(n))
            h ^= hash(_mdl_node_header_orientation(n))
            h ^= hash(_mdl_canonical_controllers_hashable(n, drop_transform_controllers=True))
            # attachments hashed via deep hash
            if n.light is not None:
                h ^= hash(("light", _mdl_deep_hash(n.light, ignore_keys=_MDL_EQ_IGNORE_KEYS)))
            else:
                h ^= hash(("light", _mdl_deep_hash(None)))

            if n.emitter is not None:
                h ^= hash(("emitter", _mdl_deep_hash(n.emitter, ignore_keys=_MDL_EQ_IGNORE_KEYS)))
            else:
                h ^= hash(("emitter", _mdl_deep_hash(None)))

            if n.reference is not None:
                h ^= hash(("reference", _mdl_deep_hash(n.reference, ignore_keys=_MDL_EQ_IGNORE_KEYS)))
            else:
                h ^= hash(("reference", _mdl_deep_hash(None)))

            if n.mesh is not None:
                h ^= hash(("mesh", _mdl_mesh_hash(n.mesh)))
            else:
                h ^= hash(("mesh", _mdl_deep_hash(None)))

            if n.skin is not None:
                h ^= hash(("skin", _mdl_deep_hash(n.skin, ignore_keys=_MDL_EQ_IGNORE_KEYS)))
            else:
                h ^= hash(("skin", _mdl_deep_hash(None)))

            if n.dangly is not None:
                h ^= hash(("dangly", _mdl_deep_hash(n.dangly, ignore_keys=_MDL_EQ_IGNORE_KEYS)))
            else:
                h ^= hash(("dangly", _mdl_deep_hash(None)))

            if n.aabb is not None:
                h ^= hash(("aabb", _mdl_deep_hash(n.aabb, ignore_keys=_MDL_EQ_IGNORE_KEYS)))
            else:
                h ^= hash(("aabb", _mdl_deep_hash(None)))

            if n.saber is not None:
                h ^= hash(("saber", _mdl_deep_hash(n.saber, ignore_keys=_MDL_EQ_IGNORE_KEYS)))
            else:
                h ^= hash(("saber", _mdl_deep_hash(None)))

        # Animations hashed by key
        def _akey(anim: MDLAnimation) -> tuple[str, str]:
            return (anim.name, anim.root_model)

        for k in sorted((_akey(a) for a in self.anims)):
            anim = next(a for a in self.anims if _akey(a) == k)
            h ^= hash(("anim", k, _qfloat(float(anim.anim_length)), _qfloat(float(anim.transition_length))))
            h ^= hash(_mdl_deep_hash(anim.events, ignore_keys=_MDL_EQ_IGNORE_KEYS))
            # canonical node graph hash by name+parent edge + payload
            a_by = _mdl_animation_nodes_by_name(anim)
            a_parent = _mdl_node_parent_edges_by_name(list(a_by.values()))
            for name in sorted(a_by.keys()):
                n = a_by[name]
                h ^= hash(("anode", k, name, a_parent.get(name)))
                h ^= hash(_mdl_node_canonical_position_strict(n, prefer_controllers=True))
                h ^= hash(_mdl_node_canonical_orientation_strict(n, prefer_controllers=True))
                h ^= hash(_mdl_canonical_controllers_hashable(n, drop_transform_controllers=False))
        return h

    def get(
        self,
        node_name: str,
    ) -> MDLNode | None:
        """Gets a node by name from the tree.

        Args:
        ----
            node_name: The name of the node to retrieve.

        Returns:
        -------
            pick: The node with the matching name or None.
        """
        pick: MDLNode | None = None

        nodes: list[MDLNode] = [self.root]
        while nodes:
            node = nodes.pop()
            if node.name == node_name:
                pick = node
            else:
                nodes.extend(node.children)

        return pick

    def all_nodes(
        self,
    ) -> list[MDLNode]:
        """Returns a list of all nodes in the tree including the root node and children recursively.

        Args:
        ----
            self: The tree object

        Returns:
        -------
            list[MDLNode]: A list of all nodes in the tree
        """
        nodes: list[MDLNode] = []
        scan: list[MDLNode] = [self.root]
        while scan:
            node: MDLNode = scan.pop()
            nodes.append(node)
            scan.extend(node.children)
        return nodes

    def find_parent(
        self,
        child: MDLNode,
    ) -> MDLNode | None:
        """Find the parent node of the given child node.

        Args:
        ----
            child: The child node to find the parent for

        Returns:
        -------
            parent: The parent node of the given child or None if not found
        """
        all_nodes: list[MDLNode] = self.all_nodes()
        parent: MDLNode | None = None
        for node in all_nodes:
            if child in node.children:
                parent = node
        return parent

    def global_position(
        self,
        node: MDLNode,
    ) -> Vector3:
        """Returns the global position of a node by traversing up the parent chain.

        Args:
        ----
            node: The node to get the global position for.

        Returns:
        -------
            Vector3: The global position of the node
        """
        position: Vector3 = node.position
        parent: MDLNode | None = self.find_parent(node)
        while parent is not None:
            position += parent.position
            parent = self.find_parent(parent)
        return position

    def get_by_node_id(
        self,
        node_id: int,
    ) -> MDLNode:
        """Get node by node id.

        Args:
        ----
            node_id: The id of the node to retrieve

        Returns:
        -------
            MDLNode: The node with matching id
        """
        for node in self.all_nodes():
            if node.node_id == node_id:
                return node
        raise ValueError

    def all_textures(
        self,
    ) -> set[str]:
        """Returns all unique texture names used in the scene.

        Args:
        ----
            self: The scene object

        Returns:
        -------
            set[str]: A set containing all unique texture names used in meshes
        """
        return {node.mesh.texture_1 for node in self.all_nodes() if (node.mesh and node.mesh.texture_1 != "NULL" and node.mesh.texture_1)}

    def all_lightmaps(
        self,
    ) -> set[str]:
        """Returns a set of all lightmap textures used in the scene.

        Args:
        ----
            self: The scene object

        Returns:
        -------
            set[str]: A set of all lightmap texture names used in nodes
        """
        return {node.mesh.texture_2 for node in self.all_nodes() if (node.mesh and node.mesh.texture_2 != "NULL" and node.mesh.texture_2)}

    def prepare_skin_meshes(self) -> None:
        """Prepare bone lookup tables for all skinned meshes in the model.

        This method should be called after loading the model and before rendering or
        manipulating skinned meshes. It creates bone serial and node number lookup
        tables for efficient bone matrix computation during skeletal animation.

        References:
        ----------
            vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 - prepareSkinMeshes()
            Called after model loading to initialize skin mesh bone mappings

        Notes:
        -----
            This is essential for multi-part character models where body parts
            reference bones in the full skeleton hierarchy (reone:704-722).
        """
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:704-722
        nodes = self.all_nodes()
        for node in nodes:
            # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:705-707
            # Only process skin mesh nodes
            if node.mesh and isinstance(node.mesh, MDLSkin):
                # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:708-721
                # Prepare bone lookups for this skin mesh
                node.mesh.prepare_bone_lookups(nodes)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, supermodel={self.supermodel!r})"


# region Animation Data
class MDLAnimation(ComparableMixin):
    """Animation data for model animations.

    Animations in KotOR contain a full node hierarchy with controller keyframe data.
    Each animation can override positions, rotations, and other properties of nodes
    over time to create character movement, attacks, expressions, etc.

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:736-779 (animation reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:653-699 (animation loading)
        vendor/mdlops/MDLOpsM.pm:4052-4090 (animation reading from ASCII)

    Attributes:
    ----------
        name: Animation name (e.g. "c_imp_walk01", "g_dance01")
            Reference: reone:742, kotorblender:660
        root_model: Name of model this animation applies to
            Reference: reone:752, mdlops:4069
            Empty string means animation applies to same model
        anim_length: Duration of animation in seconds
            Reference: reone:751, kotorblender:662, mdlops:4065
        transition_length: Blend time when transitioning to this animation
            Reference: reone:752, kotorblender:663, mdlops:4069
        events: Animation events that trigger at specific times
            Reference: reone:760-769, kotorblender:684-698, mdlops:4078-4081
            Used for footstep sounds, attack hit timing, etc.
        root: Root node of animation node hierarchy
            Reference: reone:757, kotorblender:700-767
            Contains controller keyframe data for all animated nodes
    """

    COMPARABLE_FIELDS = ("name", "root_model", "anim_length", "transition_length", "root")
    COMPARABLE_SEQUENCE_FIELDS = ("events",)

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:742
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:660
        self.name: str = ""

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:752
        # vendor/mdlops/MDLOpsM.pm:4069 - animroot
        self.root_model: str = ""

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:751
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:662
        self.anim_length: float = 0.0

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:752
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:663
        self.transition_length: float = 0.0

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:760-769
        # vendor/mdlops/MDLOpsM.pm:4078-4081
        # Animation events (footsteps, attack hits, sounds, etc.)
        self.events: list[MDLEvent] = []

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:757
        # Animation node hierarchy with controller keyframes
        self.root: MDLNode = MDLNode()

    # Back-compat aliases (used by Engines/PyKotorEngine tests/tooling)
    @property
    def length(self) -> float:
        return float(self.anim_length)

    @length.setter
    def length(self, v: float) -> None:
        self.anim_length = float(v)

    @property
    def transition_time(self) -> float:
        return float(self.transition_length)

    @transition_time.setter
    def transition_time(self, v: float) -> None:
        self.transition_length = float(v)

    def __eq__(self, other):
        if not isinstance(other, MDLAnimation):
            return NotImplemented
        return _mdl_animation_equal(self, other)

    def __hash__(self):
        # Consistent with _mdl_animation_equal: hash canonical graph keyed by names/edges.
        h = hash((self.name, self.root_model, _qfloat(float(self.anim_length)), _qfloat(float(self.transition_length))))
        h ^= hash(_mdl_deep_hash(self.events, ignore_keys=_MDL_EQ_IGNORE_KEYS))
        by = _mdl_animation_nodes_by_name(self)
        parent = _mdl_node_parent_edges_by_name(list(by.values()))
        for name in sorted(by.keys()):
            n = by[name]
            h ^= hash(
                (
                    name,
                    parent.get(name),
                    _mdl_node_canonical_position_strict(n, prefer_controllers=True),
                    _mdl_node_canonical_orientation_strict(n, prefer_controllers=True),
                    _mdl_canonical_controllers_hashable(n, drop_transform_controllers=False),
                )
            )
        return h

    def all_nodes(
        self,
    ) -> list[MDLNode]:
        """Returns all nodes in the MDL tree including children recursively.

        Args:
        ----
            self: The MDL tree object

        Returns:
        -------
            list[MDLNode]: A list containing all nodes in the tree
        """
        nodes: list[MDLNode] = []
        scan: list[MDLNode] = [self.root]
        while scan:
            node = scan.pop()
            nodes.append(node)
            scan.extend(node.children)
        return nodes

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, root_model={self.root_model!r}, anim_length={self.anim_length!r}, transition_length={self.transition_length!r})"


class MDLEvent(ComparableMixin):
    """Animation event that triggers at a specific time during animation playback.

    Events are used to synchronize sound effects, particle effects, or gameplay logic
    with animation timing. Common uses include footstep sounds, weapon swing sounds,
    attack damage timing, and special effect triggers.

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:764-768 (event reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:686-698 (event loading)
        vendor/mdlops/MDLOpsM.pm:4078-4081 (event parsing from ASCII)

    Attributes:
    ----------
        activation_time: Time in seconds when event triggers (0.0 to anim_length)
            Reference: reone:765, kotorblender:694
        name: Event name/identifier (e.g. "snd_footstep", "snd_hit", "detonate")
            Reference: reone:766, kotorblender:695
            Game code uses event names to trigger appropriate actions

    Examples:
    --------
        footstep event at 0.5s: triggers footstep sound effect
        hit event at 1.2s: deals damage when attack animation reaches strike
        detonate event: triggers explosion for grenades/mines
    """

    COMPARABLE_FIELDS = ("activation_time", "name")

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:765
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:694
        # Time in seconds when event fires (0.0 to animation length)
        self.activation_time: float = 0.0

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:766
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:695
        # Event name used by game code to trigger actions
        self.name: str = ""

    def __eq__(self, other):
        if not isinstance(other, MDLEvent):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)


# endregion


class MDLNode(ComparableMixin):
    """A node in the MDL tree that can store additional nodes or some extra data related to the model such as geometry or lighting.

    Model nodes form a hierarchical tree structure where each node can contain geometric data
    (mesh, skin, dangly, saber, walkmesh), light sources, particle emitters, or serve as
    positioning dummies. Controller keyframes can animate node properties over time.

    References:
    ----------
        vendor/reone/include/reone/graphics/modelnode.h:31-287 - ModelNode class definition
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:182-290 - Node loading from MDL
        vendor/xoreos/src/graphics/aurora/modelnode.h:67-252 - ModelNode class
        vendor/xoreos/src/graphics/aurora/model_kotor.cpp:277-533 - KotOR node parsing
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:406-582 - Node reading
        vendor/kotorblender/io_scene_kotor/scene/model.py:103-297 - Node hierarchy building
        vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:31-464 - TypeScript node implementation
        vendor/mdlops (ASCII MDL node format specifications)
        vendor/kotor/kotor/model/nodes.py:7-51 - Python node parsing

    Attributes:
    ----------
        children: List of child nodes in hierarchy
            Reference: reone:modelnode.h:219, xoreos:modelnode.h:241, KotOR.js:37
            Child nodes inherit parent transforms and can be enumerated for rendering

        controllers: Animation controller keyframe data
            Reference: reone:modelnode.h:34, xoreos:modelnode.h:178-196, kotorblender:reader.py:498-526
            Controllers animate position, orientation, scale, color, alpha, and other properties
            See MDLControllerType enum for complete list of controllable properties

        name: Node name (ASCII string, max 32 chars)
            Reference: reone:mdlmdxreader.cpp:212, xoreos:model_kotor.cpp:311, kotorblender:reader.py:416
            Used to reference nodes by name for attachment points, bone lookups, and parenting

        node_id: Unique node number within model for quick lookups
            Reference: reone:mdlmdxreader.cpp:202-203, xoreos:model_kotor.cpp:305, kotorblender:reader.py:413
            Stored as uint16 in binary format, used for parent/child relationships and bone references

        position: Local position relative to parent (x, y, z)
            Reference: reone:modelnode.h:243, xoreos:modelnode.h:89, KotOR.js:42, kotorblender:reader.py:427
            Combined with parent transforms to compute world-space position
            Can be animated via position controller (type 8)

        orientation: Local rotation as quaternion (x, y, z, w)
            Reference: reone:modelnode.h:244, xoreos:modelnode.h:92-93, KotOR.js:43, kotorblender:reader.py:428
            Quaternion format ensures smooth interpolation for animation
            Can be animated via orientation controller (type 20)
            Compressed in animation keyframes using 32-bit packed format (KotOR.js:14-20)

        light: Light source data (color, radius, flare properties)
            Reference: reone:modelnode.h:116-127, xoreos:modelnode.h:204-211, kotorblender/light.py:33-124
            Present when node type includes LIGHT flag (0x02)
            See MDLLight class for detailed light properties

        emitter: Particle emitter data (spawn rate, velocity, textures)
            Reference: reone:modelnode.h:129-153, xoreos:modelnode.h:213-221, kotorblender/emitter.py:39-286
            Present when node type includes EMITTER flag (0x04)
            See MDLEmitter class for particle system properties

        reference: Reference node (links to external model)
            Reference: reone:modelnode.h:155-158, xoreos:modelnode.h:223-224
            Present when node type includes REFERENCE flag (0x10)
            Used for equippable items, attached weapons, etc.

        mesh: Triangle mesh geometry data (vertices, faces, materials)
            Reference: reone:modelnode.h:70-91, xoreos:modelnode.h:197-202, kotorblender/trimesh.py:44-242
            Present when node type includes MESH flag (0x20)
            Contains vertex data in companion MDX file
            See MDLMesh class for geometry details

        skin: Skinned mesh with bone weighting for character animation
            Reference: reone:modelnode.h:36-41, xoreos:modelnode.h:226-232, kotorblender/skinmesh.py:33-189
            Present when node type includes SKIN flag (0x40)
            Vertices deform based on bone transforms using weight maps
            See MDLSkin class for bone binding details

        dangly: Cloth/hair physics mesh with constraint simulation
            Reference: reone:modelnode.h:47-53, xoreos:modelnode.h:234-237, kotorblender:reader.py:451-466
            Present when node type includes DANGLY flag (0x100)
            Vertices constrained by displacement, tightness, period values
            See MDLDangly class for physics properties

        aabb: Axis-aligned bounding box tree for walkmesh collision
            Reference: reone:modelnode.h:55-68, xoreos:modelnode.h:239-240, kotorblender/reader.py:469-487
            Present when node type includes AABB flag (0x200)
            Used for pathfinding and collision detection
            See MDLWalkmesh class for collision geometry

        saber: Lightsaber blade mesh with special rendering
            Reference: reone:modelnode.h:99, xoreos:modelnode.h:202, kotorblender:reader.py:446-448
            Present when node type includes SABER flag (0x800)
            Single plane geometry rendered with additive blending
            See MDLSaber class for blade properties
    """

    COMPARABLE_FIELDS = ("name", "position", "orientation", "light", "emitter", "mesh", "skin", "dangly", "aabb", "saber")
    COMPARABLE_SEQUENCE_FIELDS = ("children", "controllers")

    def __init__(
        self,
    ):
        """Initializes a MDLNode object.

        Args:
        ----
            self: The MDLNode object being initialized
        """
        # vendor/reone/include/reone/graphics/modelnode.h:219
        # vendor/xoreos/src/graphics/aurora/modelnode.h:241
        # vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:37
        # Child nodes inherit transforms and participate in rendering hierarchy
        self.children: list[MDLNode] = []

        # vendor/reone/include/reone/graphics/modelnode.h:34
        # vendor/xoreos/src/graphics/aurora/modelnode.h:178-196
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:498-526
        # Animation keyframe data for position, orientation, scale, color, etc.
        self.controllers: list[MDLController] = []

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:212
        # vendor/xoreos/src/graphics/aurora/model_kotor.cpp:311
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:416
        # ASCII string identifier (max 32 chars in binary format)
        self.name: str = ""

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:202-203
        # vendor/xoreos/src/graphics/aurora/model_kotor.cpp:305
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:413
        # Unique node number (uint16) for quick lookups and bone references
        self.node_id: int = -1

        # vendor/reone/include/reone/graphics/modelnode.h:243
        # vendor/xoreos/src/graphics/aurora/modelnode.h:89
        # vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:42
        # Local position (x,y,z) relative to parent node
        self.position: Vector3 = Vector3.from_null()

        # vendor/reone/include/reone/graphics/modelnode.h:244
        # vendor/xoreos/src/graphics/aurora/modelnode.h:92-93
        # vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:43
        # Local rotation as quaternion (x,y,z,w) for smooth animation interpolation
        self.orientation: Vector4 = Vector4(0, 0, 0, 1)

        # vendor/reone/include/reone/graphics/modelnode.h:116-127
        # Light source with flares, shadows, dynamic properties (node type & 0x02)
        self.light: MDLLight | None = None

        # vendor/reone/include/reone/graphics/modelnode.h:129-153
        # Particle emitter for effects like smoke, sparks, fire (node type & 0x04)
        self.emitter: MDLEmitter | None = None

        # vendor/reone/include/reone/graphics/modelnode.h:155-158
        # Reference to external model for equipment/attachments (node type & 0x10)
        self.reference: MDLReference | None = None

        # vendor/reone/include/reone/graphics/modelnode.h:70-91
        # Triangle mesh geometry with materials (node type & 0x20)
        self.mesh: MDLMesh | None = None

        # vendor/reone/include/reone/graphics/modelnode.h:36-41
        # Skinned mesh with bone weights for character animation (node type & 0x40)
        self.skin: MDLSkin | None = None

        # vendor/reone/include/reone/graphics/modelnode.h:47-53
        # Cloth/hair physics mesh with constraints (node type & 0x100)
        self.dangly: MDLDangly | None = None

        # vendor/reone/include/reone/graphics/modelnode.h:55-68
        # Walkmesh AABB tree for collision/pathfinding (node type & 0x200)
        self.aabb: MDLWalkmesh | None = None

        # vendor/reone/include/reone/graphics/modelnode.h:99
        # Lightsaber blade mesh with special rendering (node type & 0x800)
        self.saber: MDLSaber | None = None

        # Node type for ASCII MDL format compatibility
        self.node_type: MDLNodeType = MDLNodeType.DUMMY

        # Parent ID for ASCII MDL format compatibility
        self.parent_id: int = -1

    def get_flags(self) -> MDLNodeFlags:
        """Get the node flags based on attached data."""
        flags = MDLNodeFlags.HEADER
        if self.light:
            flags |= MDLNodeFlags.LIGHT
        if self.emitter:
            flags |= MDLNodeFlags.EMITTER
        if self.reference:
            flags |= MDLNodeFlags.REFERENCE
        if self.mesh:
            flags |= MDLNodeFlags.MESH
        if self.skin:
            flags |= MDLNodeFlags.SKIN
        if self.dangly:
            flags |= MDLNodeFlags.DANGLY
        if self.aabb:
            flags |= MDLNodeFlags.AABB
        if self.saber:
            flags |= MDLNodeFlags.SABER
        return flags

    def __eq__(self, other):
        if not isinstance(other, MDLNode):
            return NotImplemented
        if not _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS):
            return False
        return _mdl_ids_equivalent_subtree(self, other)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)

    def descendants(
        self,
    ) -> list[MDLNode]:
        """Returns all descendants of a node including itself.

        Args:
        ----
            self: The node to find descendants for

        Returns:
        -------
            list[MDLNode]: A list containing the node and all its descendants

        Processing Logic:
        ----------------
            - Initialize an empty list to store ancestors
            - Loop through each child node of the current node
            - Append the child to the ancestors list
            - Recursively call descendants on the child to get its descendants and extend the ancestors list
            - Return the final ancestors list containing the node and all its descendants.
        """
        ancestors: list[MDLNode] = []
        for child in self.children:
            ancestors.append(child)
            ancestors.extend(child.descendants())
        return ancestors

    def child(
        self,
        name: str,
    ) -> MDLNode:
        """Find child node by name.

        Args:
        ----
            name: Name of child node to find

        Returns:
        -------
            MDLNode: Child node with matching name
        """
        for child in self.children:
            if child.name == name:
                return child
        raise KeyError

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, node_id={self.node_id!r})"


class MDLLight(ComparableMixin):
    """Light data that can be attached to a node.

    Lights in KotOR can have lens flares, shadows, dynamic properties, and various
    rendering modes. They use controller keyframes for animated properties like color,
    radius, and multiplier (intensity).

    References:
    ----------
        vendor/reone/src/libs/scene/node/light.cpp:43-86 (light scene node implementation)
        vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:33-124 (light properties)

    Attributes:
    ----------
        flare_radius: Radius around light source where lens flares are visible
            Reference: kotorblender:48,80,107
            Default 1.0, typically 0.0 to disable
        light_priority: Priority level for dynamic light rendering (0-5)
            Reference: kotorblender:41,76,103
            Higher priority lights are rendered when dynamic light limit is reached
        ambient_only: 1 = only affects ambient lighting, 0 = affects both diffuse & ambient
            Reference: kotorblender:43,74,101
            Used for fill lights and area mood lighting
        dynamic_type: Type of dynamic behavior
            Reference: kotorblender:44,78,105
            0 = static (baked), 1 = dynamic (real-time), 2 = animated
        shadow: 1 = casts shadows, 0 = no shadows
            Reference: kotorblender:38,63-66,75,102
            Shadows use contact shadow technique with radius as distance
        flare: 1 = has lens flares enabled, 0 = no lens flares
            Reference: kotorblender:47,83-84,110
            Requires flare_radius > 0 or flare_list populated
        fading_light: 1 = light fades in/out when toggled, 0 = instant on/off
            Reference: kotorblender:46,77,104, reone:52-66
            Fade speed is 2.0 units per second (reone:40)
        flare_sizes: List of flare element sizes (0.0-1.0 scale)
            Reference: kotorblender:28,90
        flare_positions: List of flare element positions along view ray (-1.0 to 1.0)
            Reference: kotorblender:29,91
            0.0 = at light source, negative = between camera and light, positive = beyond
        flare_color_shifts: List of color shift values for each flare element
            Reference: kotorblender:30,89
        flare_textures: List of texture names for each flare element
            Reference: kotorblender:27,88
            Common: "flaretex01" through "flaretex16"

    Controller Properties (animated via keyframes):
    -----------------------------------------------
        color: RGB color (Vector3) - controller type 76
            Reference: reone:44
        radius: Light falloff radius in meters - controller type 88
            Reference: reone:45, kotorblender:39,73,100
            For directional lights, radius >= 100.0 (reone:41,83-85)
            Energy = multiplier * radius^2 (kotorblender:123)
        multiplier: Intensity multiplier - controller type 140
            Reference: reone:46, kotorblender:40,72,99
            Combined with radius to calculate light power

    Notes:
    -----
        Negative color values indicate a "negative light" that subtracts illumination
        Reference: kotorblender:60,62,81,98,108,120-121
    """

    COMPARABLE_FIELDS = ("flare_radius", "light_priority", "ambient_only", "dynamic_type", "shadow", "flare", "fading_light", "multiplier")
    COMPARABLE_SEQUENCE_FIELDS = ("flare_sizes", "flare_positions", "flare_color_shifts", "flare_textures")

    def __init__(
        self,
    ):
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:48,80,107
        # Radius for lens flare visibility (0.0 = disabled, typical range 0.0-10.0)
        self.flare_radius: float = 0.0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:41,76,103
        # Light priority for dynamic light culling (0-5, higher = more important)
        self.light_priority: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:43,74,101
        # 1 = ambient-only (no diffuse), 0 = full lighting
        self.ambient_only: bool = False

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:44,78,105
        # Dynamic behavior: 0=static, 1=dynamic, 2=animated
        self.dynamic_type: MDLDynamicType = MDLDynamicType.STATIC

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:38,63-66,75,102
        # 1 = casts shadows, 0 = no shadows
        self.shadow: bool = False

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:47,83-84,110
        # 1 = lens flares enabled, 0 = disabled
        self.flare: bool = False

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:46,77,104
        # vendor/reone/src/libs/scene/node/light.cpp:40,52-66
        # 1 = fades in/out at 2.0 units/sec, 0 = instant toggle
        self.fading_light: bool = False

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:28,90
        # Lens flare element sizes (one per flare texture)
        self.flare_sizes: list[float] = []

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:29,91
        # Flare positions along view ray: 0.0=light, negative=toward camera, positive=away
        self.flare_positions: list[float] = []

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:30,89
        # Color shift values for each flare element
        self.flare_color_shifts: list[tuple[float, float, float]] = []

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:27,88
        # Texture names for lens flare elements (e.g. "flaretex01")
        self.flare_textures: list[str] = []

        # RGB color stored as Vector3 (controller type 76)
        # Reference: reone:44, docstring line 2098
        self._color: Vector3 = Vector3(1.0, 1.0, 1.0)

        # vendor/reone/src/libs/scene/node/light.cpp:46
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:40,72,99
        # Intensity multiplier (controller type 140)
        self.multiplier: float = 1.0

    @property
    def radius(self) -> float:
        return self.flare_radius

    @radius.setter
    def radius(self, value: float) -> None:
        self.flare_radius = value

    @property
    def color(self) -> Color:
        """RGB color of the light.

        Returns:
        -------
            Color instance representing the light's RGB color.
        """
        return Color.from_rgb_vector3(self._color)

    @color.setter
    def color(self, value: Color) -> None:
        """Set the RGB color of the light.

        Args:
        ----
            value: Color instance to set as the light's color.
        """
        self._color = value.rgb_vector3()

    def __repr__(self):
        return f"{self.__class__.__name__}(flare_radius={self.flare_radius!r}, light_priority={self.light_priority!r}, ambient_only={self.ambient_only!r}, dynamic_type={self.dynamic_type!r}, shadow={self.shadow!r}, flare={self.flare!r}, fading_light={self.fading_light!r})"

    def __eq__(self, other):
        if not isinstance(other, MDLLight):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)


class MDLEmitter(ComparableMixin):
    """Particle emitter data for special effects.

    Emitters generate particle effects like smoke, fire, sparks, lightning, explosions,
    and force fields. They support multiple update modes (fountain, single, explosion,
    lightning), rendering modes, and extensive particle appearance/physics properties.

    References:
    ----------
        vendor/reone/src/libs/scene/node/emitter.cpp:44-319 (emitter scene node)
        vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:27-305 (emitter properties)

    Update Modes (update field):
    ---------------------------
        "Fountain" - Continuous particle stream at birthrate
            Reference: reone:132-140, kotorblender:236
        "Single" - Single particle, respawns if loop=True
            Reference: reone:141-146, kotorblender:236
        "Explosion" - Burst of particles then stop
            Reference: kotorblender:236
        "Lightning" - Lightning bolt effects with branching
            Reference: reone:147-151, kotorblender:236

    Render Modes (render field):
    ----------------------------
        "Normal" - Standard billboard particles
        "Linked" - Particles connected by lines/trails
        "Billboard_to_Local_Z" - Billboards aligned to emitter Z axis
        "Billboard_to_World_Z" - Billboards aligned to world Z axis
        "Aligned_to_World_Z" - Particles aligned to world Z
        "Aligned_to_Particle_Dir" - Particles face movement direction
        "Motion_Blur" - Particles with motion blur trails
            Reference: kotorblender:244-259, reone:41

    Spawn Types (spawn_type field):
    -------------------------------
        0 = "Normal" - Spawn at emitter position
        1 = "Trail" - Spawn along particle path
            Reference: kotorblender:229-233

    Blend Modes (blend field):
    --------------------------
        "Normal" - Standard alpha blending
        "Punch-Through" - Binary alpha (0 or 1)
        "Lighten" - Additive blending (common for fire/energy)
            Reference: kotorblender:260-267

    Attributes:
    ----------
        dead_space: Inner radius where no particles spawn (meters)
            Reference: kotorblender:113
        blast_radius: Outer radius for explosion/blast effects (meters)
            Reference: kotorblender:114
        blast_length: Length of blast wave propagation (meters)
            Reference: kotorblender:115
        branch_count: Number of lightning branches
            Reference: kotorblender:116
        control_point_smoothing: Smoothing factor for control point paths (0.0-1.0)
            Reference: kotorblender:117
        x_grid: Texture atlas grid width (for animated textures)
            Reference: kotorblender:118
        y_grid: Texture atlas grid height (for animated textures)
            Reference: kotorblender:119
        spawn_type: Spawn location mode (0=Normal, 1=Trail)
            Reference: kotorblender:120,229-233
        update: Update mode string ("Fountain", "Single", "Explosion", "Lightning")
            Reference: kotorblender:121,234-242, reone:131-151
        render: Render mode string (see Render Modes above)
            Reference: kotorblender:122,244-259
        blend: Blend mode string ("Normal", "Punch-Through", "Lighten")
            Reference: kotorblender:123,260-267
        texture: Main particle texture name
            Reference: kotorblender:124
        chunk_name: Chunk model name for mesh-based particles
            Reference: kotorblender:125
        two_sided_texture: 1 = render both sides, 0 = single-sided
            Reference: kotorblender:126
        loop: 1 = loop/repeat emission, 0 = emit once
            Reference: kotorblender:127, reone:142
        render_order: Rendering priority/sorting order
            Reference: kotorblender:128
        frame_blender: 1 = blend between animation frames, 0 = snap
            Reference: kotorblender:129
        depth_texture: Depth texture name for soft particles
            Reference: kotorblender:130,146
        flags: Emitter behavior flags (see MDLEmitterFlags)
            Reference: kotorblender:131-143
            Flags include: p2p, p2p_sel, affected_by_wind, tinted, bounce,
                          random, inherit, inheritvel, inherit_local, splat,
                          inherit_part, depth_texture

    Controller Properties (animated via keyframes):
    -----------------------------------------------
        birthrate: Particles spawned per second
            Reference: reone:45,134,138, kotorblender:148
        lifeExp: Particle lifetime in seconds (-1 = infinite)
            Reference: reone:46,110, kotorblender:157
        xSize/ySize: Emitter spawn area dimensions (meters)
            Reference: reone:48-49, kotorblender:172-173
        frameStart/frameEnd: Texture atlas animation range
            Reference: reone:50-56, kotorblender:154-155
        fps: Texture atlas animation speed (frames/second)
            Reference: reone:58, kotorblender:153
        spread: Particle spawn cone angle (degrees)
            Reference: reone:59, kotorblender:169
        velocity: Initial particle velocity (meters/second)
            Reference: reone:60, kotorblender:171
        randVel: Random velocity variation (meters/second)
            Reference: reone:61, kotorblender:162
        mass: Particle mass (affects gravity)
            Reference: reone:62, kotorblender:158
        grav: Gravity acceleration (meters/second^2)
            Reference: reone:63, kotorblender:156
        sizeStart/sizeMid/sizeEnd: Particle size over lifetime
            Reference: reone:73-75, kotorblender:163-165
        colorStart/colorMid/colorEnd: Particle RGB color over lifetime
            Reference: reone:76-78, kotorblender:189-191
        alphaStart/alphaMid/alphaEnd: Particle opacity over lifetime (0.0-1.0)
            Reference: reone:79-81, kotorblender:145-147
        lightningDelay/Radius/Scale/SubDiv: Lightning effect parameters
            Reference: reone:64-71, kotorblender:174-178

    Notes:
    -----
        Particles transition through three lifecycle stages: Start -> Mid -> End
        The "Mid" stage occurs at 50% of particle lifetime
        Reference: reone:73-81, kotorblender:163-165
    """

    COMPARABLE_FIELDS = (
        "dead_space",
        "blast_radius",
        "blast_length",
        "branch_count",
        "control_point_smoothing",
        "x_grid",
        "y_grid",
        "spawn_type",
        "update",
        "render",
        "blend",
        "texture",
        "chunk_name",
        "two_sided_texture",
        "loop",
        "render_order",
        "frame_blender",
        "depth_texture",
        "flags",
    )

    def __init__(
        self,
    ):
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:113
        # Inner dead zone radius where no particles spawn
        self.dead_space: float = 0.0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:114
        # Outer blast/explosion radius
        self.blast_radius: float = 0.0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:115
        # Blast wave propagation length
        self.blast_length: float = 0.0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:116
        # Number of lightning branches
        self.branch_count: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:117
        # Control point path smoothing factor
        self.control_point_smoothing: float = 0.0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:118
        # Texture atlas grid width
        self.x_grid: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:119
        # Texture atlas grid height
        self.y_grid: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:120,229-233
        # Spawn location: 0=Normal (at emitter), 1=Trail (along path)
        self.spawn_type: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:121,234-242
        # vendor/reone/src/libs/scene/node/emitter.cpp:131-151
        # Update mode: "Fountain", "Single", "Explosion", "Lightning"
        self.update: str = ""

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:122,244-259
        # Render mode: "Normal", "Linked", "Billboard_to_Local_Z", etc.
        self.render: str = ""

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:123,260-267
        # Blend mode: "Normal", "Punch-Through", "Lighten"
        self.blend: str = ""

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:124
        # Main particle texture name
        self.texture: str = ""

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:125
        # Chunk model name for mesh-based particles
        self.chunk_name: str = ""

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:126
        # 1 = two-sided rendering, 0 = single-sided
        self.two_sided_texture: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:127
        # vendor/reone/src/libs/scene/node/emitter.cpp:142
        # 1 = loop emission, 0 = emit once
        self.loop: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:128
        # Rendering priority/sorting order
        self.render_order: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:129
        # 1 = blend animation frames, 0 = snap between frames
        self.frame_blender: int = 0

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:130,146
        # Depth texture for soft particle effects
        self.depth_texture: str = ""

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:131-143
        # Behavior flags (see MDLEmitterFlags)
        self.flags: int = 0

    def __eq__(self, other):
        if not isinstance(other, MDLEmitter):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)


class MDLReference(ComparableMixin):
    """Reference node data for attaching external model resources.

    Reference nodes allow models to dynamically attach other models at specific
    attachment points. This is commonly used for:
    - Equipping weapons, armor, and accessories on characters
    - Attaching placeable items to character hands
    - Mounting riders on creatures
    - Adding modular parts to placeables

    The referenced model is loaded and attached at runtime when needed, enabling
    dynamic equipment systems without requiring every equipment combination to be
    a separate model file.

    References:
    ----------
        vendor/kotorblender/io_scene_kotor/scene/modelnode/reference.py:25-57
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:545-561 (reference reading)

    Attributes:
    ----------
        model: Name of the external model resource to attach (without file extension)
            Reference: kotorblender:30, reone:552
            Example: "w_lghtsbr_001" for a lightsaber model
            The model is loaded from the game's model resources at runtime
        reattachable: Whether the reference can be dynamically replaced
            Reference: kotorblender:31, reone:553
            True = can swap models (e.g. changing equipped weapons)
            False = permanent attachment

    Common Reference Node Names:
    ---------------------------
        rhand - Right hand attachment point (weapons, tools)
        lhand - Left hand attachment point (shields, off-hand weapons)
        head - Head attachment point (helmets, masks)
        back - Back attachment point (backpacks, cloaks)
        hook - Generic attachment point (various items)

    Example Usage:
    -------------
        Character model has "rhand" reference node
        When equipped with lightsaber, game loads "w_lghtsbr_001.mdl"
        Lightsaber model is attached at rhand node's transform
        If reattachable=True, can swap to different weapon model
    """

    COMPARABLE_FIELDS = ("model", "reattachable")

    def __init__(
        self,
    ):
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/reference.py:30
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:552
        # External model resource name to attach at this node
        self.model: str = ""

        # vendor/kotorblender/io_scene_kotor/scene/modelnode/reference.py:31
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:553
        # True = can swap models dynamically, False = permanent attachment
        self.reattachable: bool = False

    def __repr__(self):
        return f"{self.__class__.__name__}(model={self.model!r}, reattachable={self.reattachable!r})"

    def __eq__(self, other):
        if not isinstance(other, MDLReference):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)


class MDLMesh(ComparableMixin):
    """Mesh geometry data including vertices, faces, textures, and rendering properties.

    Meshes are the core geometry data in MDL models. They contain vertex positions, normals,
    UV coordinates, faces/triangles, textures, and various rendering properties. KotOR supports
    several advanced mesh features including UV animation, bump mapping, and lightmaps.

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:148-487 (mesh reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:415-466 (trimesh loading)
        vendor/mdlops/MDLOpsM.pm:1600-1750 (mesh processing)

    Key Features:
    ------------
        - UV Animation: Texture scrolling for water, lava, holograms
        - Bump/Normal Mapping: Advanced lighting with tangent space
        - Lightmaps: Pre-baked lighting for static geometry
        - Transparency: Alpha blending and transparency hints
    """

    COMPARABLE_FIELDS = (
        "diffuse",
        "ambient",
        "transparency_hint",
        "texture_1",
        "texture_2",
        "saber_unknowns",
        "animate_uv",
        "uv_direction_x",
        "uv_direction_y",
        "uv_jitter",
        "uv_jitter_speed",
        "has_lightmap",
        "rotate_texture",
        "background_geometry",
        "shadow",
        "beaming",
        "render",
        "dirt_enabled",
        "dirt_texture",
        "dirt_coordinate_space",
        "hide_in_hologram",
    )
    COMPARABLE_SEQUENCE_FIELDS = (
        "faces",
        "vertex_positions",
        "vertex_normals",
        "vertex_uv1",
        "vertex_uv2",
    )

    def __init__(
        self,
    ):
        # Basic geometry
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:386-416
        # vendor/mdlops/MDLOpsM.pm:1650-1700
        self.faces: list[MDLFace] = []

        # Material properties
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:435-438
        self.diffuse: Color = Color.WHITE
        self.ambient: Color = Color.WHITE
        self.transparency_hint: int = 0

        # Textures
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:461-467
        # texture_1 is diffuse map, texture_2 is lightmap
        self.texture_1: str = ""
        self.texture_2: str = ""

        # Saber-specific unknowns (not fully documented in vendors)
        self.saber_unknowns: tuple[int, int, int, int, int, int, int, int] = (3, 0, 0, 0, 0, 0, 0, 0)

        # UV Animation for scrolling textures (water, lava, holograms, forcefields)
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:457-460
        # vendor/mdlops/MDLOpsM.pm:3204-3210
        # When animate_uv is true, texture coordinates scroll in uv_direction at runtime
        self.animate_uv: bool = False

        # Bounding geometry for culling and collision
        # vendor/mdlops/MDLOpsM.pm:1685-1695
        self.radius: float = 0.0
        self.bb_min: Vector3 = Vector3.from_null()
        self.bb_max: Vector3 = Vector3.from_null()
        self.average: Vector3 = Vector3.from_null()
        self.area: float = 0.0

        # UV Animation direction and jitter parameters
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:459
        # Direction vector for texture scrolling (units per second)
        # Used for animated water, lava flows, hologram scan lines, etc.
        self.uv_direction_x: float = 0.0
        self.uv_direction_y: float = 0.0

        # UV jitter for random texture offset variations
        # Creates shimmering/wavering effect on textures
        self.uv_jitter: float = 0.0
        self.uv_jitter_speed: float = 0.0

        # Rendering flags
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:475-478
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:439-444
        self.has_lightmap: bool = False  # Has pre-baked lighting (texture_2)
        self.rotate_texture: bool = False  # Rotate texture 90 degrees
        self.background_geometry: bool = False  # Render in background pass
        self.shadow: bool = False  # Cast shadows
        self.beaming: bool = False  # Special hologram effect
        self.render: bool = True  # Should be rendered

        # Vertex data arrays
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:381-384
        # All vertex arrays must have same length (1:1 correspondence)
        self.vertex_positions: list[Vector3] = []

        # vendor/mdlops/MDLOpsM.pm:5603-5791 (vertex normal calculation)
        # Normals can be area/angle weighted for smooth shading
        self.vertex_normals: list[Vector3] = []

        # UV texture coordinates (2D)
        # uv1 is diffuse texture coords, uv2 is lightmap coords
        self.vertex_uv1: list[Vector2] = []
        self.vertex_uv2: list[Vector2] = []

        # Back-compat alias used by older code/tests.
        # Treat as the primary UV set (same object as vertex_uv1).
        self.vertex_uvs: list[Vector2] = [] if self.vertex_uv1 is None else self.vertex_uv1

        # NOTE: Tangent space data (for bump/normal mapping) is stored separately in MDX
        # vendor/mdlops/MDLOpsM.pm:5379-5597 (tangent space calculation)
        # vendor/mdlops/MDLOpsM.pm:256 (MDX_TANGENT_SPACE = 0x00000080)
        # Each vertex with tangent space has: bitangent (3 floats) + tangent (3 floats)
        # Total 6 additional floats per vertex for bump mapping support
        # Tangent space enables advanced lighting (normal maps, parallax, etc.)

        # KotOR 2 Only - Enhanced effects
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:445-448
        self.dirt_enabled: bool = False  # Dirt/weathering overlay texture
        self.dirt_texture: str = ""  # Dirt texture name
        self.dirt_coordinate_space: int = 0  # UV space for dirt
        self.hide_in_hologram: bool = False  # Don't render in hologram effect

        # Inverted mesh sequence counter (array3) - used by MDLOps for inv_count
        # vendor/mdlops/MDLOpsM.pm:2238-2243, 4187-4188
        # Preserved for roundtrip compatibility with MDLOps
        self.inverted_counters: list[int] = []
        
        # Indices arrays - preserved for roundtrip compatibility with MDLOps
        # These arrays are typically empty but must be preserved if present in original binary
        self.indices_counts: list[int] = []
        self.indices_offsets: list[int] = []

    @property
    def vertex_uv(self) -> _Vector2ListProxy:
        """Back-compat alias for `vertex_uv1` that accepts tuple/list values."""
        return _Vector2ListProxy(self.vertex_uv1)

    def gen_normals(self): ...

    def __eq__(self, other):
        if not isinstance(other, MDLMesh):
            return NotImplemented
        # vertex_uvs is an alias; raw value can differ (None vs list) while still meaning "uv1".
        # We therefore ignore the alias field in the deep-compare, but enforce equivalence here.
        if not _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS):
            return False
        a_uv = self.vertex_uv1 or self.vertex_uvs
        b_uv = other.vertex_uv1 or other.vertex_uvs
        return _mdl_deep_eq(a_uv, b_uv, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS, _ctx=_CTX_NONE)

    def __hash__(self):
        # Hash must match __eq__: ignore alias field, hash effective uv1.
        h = _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS)
        uv = self.vertex_uv1 or self.vertex_uvs
        return hash((h, _mdl_deep_hash(uv, ignore_keys=_MDL_EQ_IGNORE_KEYS | _MDL_EQ_ID_KEYS, _ctx=_CTX_NONE)))


class MDLSkin(MDLMesh):
    """Skin data for skeletal animation (skinned mesh).

    Skinned meshes are meshes whose vertices are influenced by multiple bones in a skeleton,
    allowing for smooth deformation during character animation. Each vertex can be weighted
    to up to 4 bones, and the mesh deforms based on bone transformations.

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 (prepareSkinMeshes)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:468-485 (skin loading)
        vendor/mdlops/MDLOpsM.pm:1755-1820 (skin node processing)

    Attributes:
    ----------
        bone_indices: Fixed array of 16 bone indices that this skin references
            Reference: mdlops:1760 - bone index array
        qbones: Quaternion rotations for each bone's bind pose
            Reference: mdlops:1765 - bone orientations
        tbones: Translation vectors for each bone's bind pose
            Reference: mdlops:1768 - bone positions
        bonemap: Maps local bone indices to global skeleton bone numbers
            Reference: reone:709-720 - bone mapping preparation
            This is critical for multi-part character models where each part
            references bones in the full skeleton
        vertex_bones: Per-vertex bone weights and indices for skinning
            Reference: reone:261-268, kotorblender:478-485
            Each vertex can be influenced by up to 4 bones with normalized weights
    """

    COMPARABLE_FIELDS = (
        *MDLMesh.COMPARABLE_FIELDS,
        "bone_indices",
    )
    COMPARABLE_SEQUENCE_FIELDS = (
        *MDLMesh.COMPARABLE_SEQUENCE_FIELDS,
        "qbones",
        "tbones",
        "vertex_bones",
        "bonemap",
        "bone_serial",
        "bone_node_number",
    )

    def __init__(
        self,
    ):
        # Skins are meshes with extra bone-weighting data.
        # Reuse MDLMesh initialization so ambient/diffuse/textures/verts/faces exist.
        super().__init__()

        # vendor/mdlops/MDLOpsM.pm:1760 - Fixed 16-bone index array
        self.bone_indices: tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # vendor/mdlops/MDLOpsM.pm:1765 - Bone quaternion orientations (bind pose)
        self.qbones: list[Vector4] = []

        # vendor/mdlops/MDLOpsM.pm:1768 - Bone translation positions (bind pose)
        self.tbones: list[Vector3] = []

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:709-720
        # Maps local bone index to global skeleton bone number
        # Critical for multi-part models where each part references the full skeleton
        self.bonemap: list[int] = []

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-268
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-485
        # Per-vertex skinning data: up to 4 bone influences per vertex
        self.vertex_bones: list[MDLBoneVertex] = []

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:712-713
        # Prepared lookup tables for bone serial numbers and node numbers
        # These are computed from bonemap during skin mesh preparation
        self.bone_serial: list[int] = []  # Maps bone index to serial number in model
        self.bone_node_number: list[int] = []  # Maps bone index to node number in hierarchy

    def prepare_bone_lookups(self, nodes: list[MDLNode]) -> None:
        """Prepare bone serial and node number lookup tables from the bone map.

        This method creates lookup tables that map bone indices to their serial positions
        and node numbers in the model hierarchy. This is essential for multi-part character
        models where each part needs to reference bones in the full skeleton.

        Args:
        ----
            nodes: List of all nodes in the model, in order

        References:
        ----------
            vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 - prepareSkinMeshes()
            Algorithm: For each bone in bonemap, store its serial position and node number

        Notes:
        -----
            This should be called after loading the skin data and before rendering.
            The bonemap contains local-to-global bone index mappings (reone:709-710).
            Invalid bone indices (0xFFFF) are skipped (reone:715-717).
        """
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:708-721
        # Build a lookup of node_id -> serial index to correctly map global bone IDs.
        node_index_by_id: dict[int, int] = {}
        for serial_index, node in enumerate(nodes):
            if node.node_id >= 0 and node.node_id not in node_index_by_id:
                node_index_by_id[node.node_id] = serial_index

        for local_index, bone_idx_value in enumerate(self.bonemap):
            # Bone map values are stored as floats in binary MDL; convert to int safely.
            try:
                bone_idx = int(bone_idx_value)
            except (TypeError, ValueError):
                continue

            # Ensure lookup arrays are large enough for this bone index.
            if bone_idx >= len(self.bone_serial):
                self.bone_serial.extend([0] * (bone_idx + 1 - len(self.bone_serial)))
                self.bone_node_number.extend([0] * (bone_idx + 1 - len(self.bone_node_number)))

            # Skip invalid bone indices (0xFFFF = unused slot).
            if bone_idx == 0xFFFF or bone_idx < 0:
                continue

            # Map global bone ID to the correct node serial.
            serial_index = node_index_by_id.get(bone_idx)
            if serial_index is None:
                # Fallback: if bonemap entry is the serial itself (legacy behaviour), accept it.
                if local_index < len(nodes):
                    serial_index = local_index
                else:
                    continue

            bone_node = nodes[serial_index]
            self.bone_serial[bone_idx] = serial_index
            self.bone_node_number[bone_idx] = bone_node.node_id

    # Back-compat alias (used by tests)
    @property
    def bone_vertices(self) -> list[MDLBoneVertex]:
        return self.vertex_bones

    @bone_vertices.setter
    def bone_vertices(self, v: list[MDLBoneVertex]) -> None:
        self.vertex_bones = v


class MDLConstraint(ComparableMixin):
    """Constraint data that can be attached to a node."""

    COMPARABLE_FIELDS = ("name", "type", "target", "target_node")

    def __init__(
        self,
    ):
        self.name: str = ""
        self.type: int = 0
        self.target: int = 0
        self.target_node: int = 0

    def __eq__(self, other):
        if not isinstance(other, MDLConstraint):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS)


class MDLDangly(MDLMesh):
    """Dangly mesh physics data for cloth, hair, and soft body simulation.

    Dangly meshes are special meshes that simulate cloth or hair physics in KotOR.
    They use a simplified physics model with constraints and vertex positions that
    update based on movement and gravity. Common uses include capes, robes, and hair.

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:276-291 (dangly reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:487-497 (dangly loading)
        vendor/mdlops/MDLOpsM.pm:1823-1870 (dangly node processing)

    Attributes:
    ----------
        constraints: List of constraint data defining how vertices can move
            Reference: reone:276-291, mdlops:1835-1850
            Constraints limit vertex movement to create realistic cloth behavior
        verts: Current vertex positions (updated by physics)
            Reference: reone:283, kotorblender:491-493
            These positions change during animation as cloth physics are simulated
        verts_original: Original bind pose vertex positions
            Reference: mdlops:1860
            Used as reference for resetting or calculating displacement
    """

    COMPARABLE_FIELDS = MDLMesh.COMPARABLE_FIELDS
    COMPARABLE_SEQUENCE_FIELDS = (
        *MDLMesh.COMPARABLE_SEQUENCE_FIELDS,
        "constraints",
        "verts",
        "verts_original",
    )

    def __init__(
        self,
    ):
        # Dangly meshes still behave like meshes for rendering/export purposes.
        # Reuse MDLMesh initialization so ambient/diffuse/textures/verts/faces exist.
        super().__init__()

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:276-291
        # vendor/mdlops/MDLOpsM.pm:1835-1850
        # Constraints define how vertices can move (springs, limits, etc.)
        self.constraints: list[MDLConstraint] = []

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:283
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:491-493
        # Current positions updated by physics simulation
        self.verts: list[Vector3] = []

        # vendor/mdlops/MDLOpsM.pm:1860 - Original bind pose positions
        self.verts_original: list[Vector3] = []

    def __repr__(self):
        return f"{self.__class__.__name__}(constraints={self.constraints!r}, verts={self.verts!r}, verts_original={self.verts_original!r})"


class MDLWalkmesh(ComparableMixin):
    """Walkmesh collision data using Axis-Aligned Bounding Box (AABB) tree.

    Walkmeshes define where characters can walk in a level. They use an AABB tree
    (binary space partitioning tree) for efficient collision detection. Each node
    in the tree represents a bounding volume that can be tested for intersection.

    The AABB tree is a hierarchical structure where:
    - Leaf nodes contain actual collision faces/triangles
    - Branch nodes subdivide space and have left/right children
    - Most significant plane axis determines split direction

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:489-509 (AABB tree reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:499-520 (AABB loading)
        vendor/mdlops/MDLOpsM.pm:1873-1935 (walkmesh/AABB processing)

    Attributes:
    ----------
        aabbs: List of AABB tree nodes forming the collision hierarchy
            Reference: reone:489-509 - AABB tree structure
            Each node contains:
            - Bounding box (min/max points)
            - Face index (for leaf nodes, -1 for branch nodes)
            - Most significant plane (split axis)
            - Left/right child offsets (for branch nodes)

    Notes:
    -----
        The AABB tree enables O(log n) collision detection instead of O(n).
        Reone implements efficient tree traversal with early rejection.
        Reference: reone:490-496 for bounding box format
    """

    COMPARABLE_SEQUENCE_FIELDS = ("aabbs",)

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:489-509
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:499-520
        # Hierarchical AABB tree for efficient collision detection
        # Each node contains bounding box and either face index (leaf) or child pointers (branch)
        self.aabbs: list[MDLNode] = []

    def __eq__(self, other):
        if not isinstance(other, MDLWalkmesh):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS)


class MDLSaber(ComparableMixin):
    """Lightsaber blade mesh data.

    Lightsaber blades are special procedurally-generated meshes in KotOR that
    create the iconic glowing blade effect. The blade geometry is generated
    at runtime based on parameters like length, width, color, and type.

    Saber meshes have a fixed vertex count (176 vertices) and use a specific
    vertex layout optimized for the blade effect with transparency and glow.

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:308-378 (saber generation)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:522-540 (saber loading)
        vendor/mdlops/MDLOpsM.pm:1937-2010 (saber node processing)

    Attributes:
    ----------
        saber_type: Type of lightsaber (single, double-bladed, etc.)
            Reference: mdlops:1945
        saber_color: Blade color (red, blue, green, etc.)
            Reference: mdlops:1947, reone:319-320
        saber_length: Length of the blade in meters
            Reference: mdlops:1948, reone:312-314
        saber_width: Width/thickness of the blade
            Reference: mdlops:1949
        saber_flare_color: Color of the blade's lens flare effect
            Reference: mdlops:1950
        saber_flare_radius: Radius of the lens flare effect
            Reference: mdlops:1951

    Notes:
    -----
        Saber vertices are generated procedurally with 176 vertices total:
        - 88 vertices for each side of the blade (176 total)
        - Each segment uses 8 vertices (kNumSaberPieceVertices = 8)
        - Faces are generated from predefined indices
        Reference: reone:32-33, reone:327-449 for generation algorithm
    """

    COMPARABLE_FIELDS = (
        "saber_type",
        "saber_color",
        "saber_length",
        "saber_width",
        "saber_flare_color",
        "saber_flare_radius",
    )

    def __init__(
        self,
    ):
        # vendor/mdlops/MDLOpsM.pm:1945 - Saber type (single/double-bladed)
        self.saber_type: int = 0

        # vendor/mdlops/MDLOpsM.pm:1947 - Blade color
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:319-320
        self.saber_color: int = 0

        # vendor/mdlops/MDLOpsM.pm:1948 - Blade length in meters
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:312-314
        self.saber_length: float = 0.0

        # vendor/mdlops/MDLOpsM.pm:1949 - Blade width/thickness
        self.saber_width: float = 0.0

        # vendor/mdlops/MDLOpsM.pm:1950 - Lens flare color
        self.saber_flare_color: int = 0

        # vendor/mdlops/MDLOpsM.pm:1951 - Lens flare radius
        self.saber_flare_radius: float = 0.0

    def __eq__(self, other):
        if not isinstance(other, MDLSaber):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS)


# endregion


# region Geometry Data
class MDLBoneVertex(ComparableMixin):
    """Per-vertex skinning data for skeletal animation.

    Each vertex in a skinned mesh can be influenced by up to 4 bones with different
    weights. The weights are normalized (sum to 1.0) and determine how much each bone's
    transformation affects the vertex position during animation.

    This is the core data structure for smooth character deformation in skeletal animation.
    When a character animates, each vertex position is computed as:
        final_pos = w0*bone0*orig_pos + w1*bone1*orig_pos + w2*bone2*orig_pos + w3*bone3*orig_pos

    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-268 (vertex bone reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-485 (bone weight loading)
        vendor/mdlops/MDLOpsM.pm:1785-1800 (vertex skinning data)

    Attributes:
    ----------
        vertex_weights: Normalized weights for up to 4 bone influences (w0, w1, w2, w3)
            Reference: reone:264-266, kotorblender:481-483
            Weights should sum to 1.0 for proper blending
            Unused weights are set to 0.0
        vertex_indices: Bone indices for up to 4 bone influences (bone0, bone1, bone2, bone3)
            Reference: reone:261-263, kotorblender:478-480
            Indices reference bones in the skin's bonemap array
            Unused indices are set to -1.0 (yes, stored as float in MDX)

    Notes:
    -----
        KotOR uses up to 4 bones per vertex for smooth deformation.
        The game engine performs hardware-accelerated vertex skinning on GPU.
        Weight normalization is critical for avoiding visual artifacts.
    """

    COMPARABLE_FIELDS = ("vertex_weights", "vertex_indices")

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:264-266
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:481-483
        # Normalized blend weights (must sum to 1.0)
        self.vertex_weights: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-263
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-480
        # Bone indices into skin's bonemap (-1.0 = unused)
        self.vertex_indices: tuple[float, float, float, float] = (-1.0, -1.0, -1.0, -1.0)

    def __repr__(self):
        return f"{self.__class__.__name__}(vertex_weights={self.vertex_weights!r}, vertex_indices={self.vertex_indices!r})"

    def __eq__(self, other):
        if not isinstance(other, MDLBoneVertex):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS)


class MDLFace(ComparableMixin):
    # NOTE:
    # - Binary faces store: normal, plane coefficient, material_id, adjacent_face1/2/3, v1/v2/v3
    # - MDLOps ASCII faces store: v1 v2 v3 smoothgroup_mask t1 t2 t3 material_id
    # We keep BOTH adjacency (a1/a2/a3) and tvert indices (t1/t2/t3) so roundtrips can be lossless.
    COMPARABLE_FIELDS = (
        "v1",
        "v2",
        "v3",
        "material",
        "smoothgroup",
        "_canon_t1",
        "_canon_t2",
        "_canon_t3",
    )

    def __init__(
        self,
    ):
        self.v1: int = 0
        self.v2: int = 0
        self.v3: int = 0
        # TODO: deconstruct self.material to full comprehensive data structures.
        # Face material is a packed 32-bit value in binary MDL files.
        # Low 5 bits (0-31) store walkmesh surface material for BWM/KotOR (surfacemat.2da).
        # Upper bits encode smoothgroup ID, lightmap info, and other vendor-specific data.
        # MDLOps reuses this field for smoothgroups when exporting ASCII (vendor/mdlops/MDLOpsM.pm:1292-1298).
        # KotOR.js and reone both treat it as opaque 32-bit integer (vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:395-408,
        # vendor/KotOR.js/src/odyssey/OdysseyModel.ts:face.material).
        # We therefore store it as an integer to avoid lossy enum conversion.
        self.material: int = 0
        # MDLOps ASCII exports a per-face smoothing group mask (often powers of two like 16/32).
        # When reading binary, this may be absent/unknown; keep as 0 unless populated.
        self.smoothgroup: int = 0
        # Texture-vertex (tvert) indices for the 3 corners of the face (MDLOps ASCII: columns 5-7).
        # These reference the mesh's `tverts` section (UV list) when present.
        self.t1: int = -1
        self.t2: int = -1
        self.t3: int = -1
        self.a1: int = 0
        self.a2: int = 0
        self.a3: int = 0
        self.coefficient: int = 0
        self.normal: Vector3 = Vector3.from_null()

    @property
    def _canon_t1(self) -> int:
        return self.v1 if self.t1 < 0 else self.t1

    @property
    def _canon_t2(self) -> int:
        return self.v2 if self.t2 < 0 else self.t2

    @property
    def _canon_t3(self) -> int:
        return self.v3 if self.t3 < 0 else self.t3

    def __eq__(self, other):
        if not isinstance(other, MDLFace):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS)


def _mdl_recompute_mesh_face_payload(mesh: "MDLMesh") -> None:
    """Recompute derived per-face payload (adjacency, plane coefficient, normal) from mesh geometry.

    MDLOps-style ASCII does not carry these binary-only fields. To keep roundtrips idempotent
    without inventing new ASCII syntax, we deterministically derive them from:
    - mesh.vertex_positions
    - mesh.faces (v1/v2/v3 indices)

    This function is intentionally side-effecting and does NOT cache results.
    """
    try:
        faces = mesh.faces
        verts = mesh.vertex_positions
    except Exception:
        return

    if not faces or not verts:
        return

    # Map vertex index -> list of faces that reference it.
    nverts = len(verts)
    faces_by_vertex: list[list[int]] = [[] for _ in range(nverts)]
    for fi, f in enumerate(faces):
        try:
            faces_by_vertex[int(f.v1)].append(fi)
            faces_by_vertex[int(f.v2)].append(fi)
            faces_by_vertex[int(f.v3)].append(fi)
        except Exception:
            continue

    # Tolerant position keying inspired by MDLOps (vendor/MDLOps/MDLOpsM.pm adjacency routine):
    # it groups vertices by formatted position so overlapping geometry still links.
    verts_by_pos: dict[str, list[int]] = {}
    pos_key_of_vert: list[str] = [""] * nverts
    for vi, p in enumerate(verts):
        try:
            key = f"{float(p.x):.4g},{float(p.y):.4g},{float(p.z):.4g}"
        except Exception:
            key = "0,0,0"
        pos_key_of_vert[vi] = key
        verts_by_pos.setdefault(key, []).append(vi)

    def _vec_sub(a: Vector3, b: Vector3) -> Vector3:
        return Vector3(float(a.x) - float(b.x), float(a.y) - float(b.y), float(a.z) - float(b.z))

    def _vec_cross(a: Vector3, b: Vector3) -> Vector3:
        ax, ay, az = float(a.x), float(a.y), float(a.z)
        bx, by, bz = float(b.x), float(b.y), float(b.z)
        return Vector3(ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)

    def _vec_len(a: Vector3) -> float:
        ax, ay, az = float(a.x), float(a.y), float(a.z)
        return (ax * ax + ay * ay + az * az) ** 0.5

    def _vec_norm(a: Vector3) -> Vector3:
        l = _vec_len(a)
        if l == 0.0:
            return Vector3.from_null()
        inv = 1.0 / l
        return Vector3(float(a.x) * inv, float(a.y) * inv, float(a.z) * inv)

    # For each face, compute:
    # - normal: normalized cross((p2-p1),(p3-p1))
    # - coefficient: int(-dot(n,p1)) (deterministic; matches our binary rounding/truncation style)
    # - adjacency: for each edge, choose the smallest neighbor face index that shares that edge
    for fi, f in enumerate(faces):
        try:
            v1 = int(f.v1)
            v2 = int(f.v2)
            v3 = int(f.v3)
            if v1 < 0 or v2 < 0 or v3 < 0 or v1 >= nverts or v2 >= nverts or v3 >= nverts:
                continue
            p1 = verts[v1]
            p2 = verts[v2]
            p3 = verts[v3]
        except Exception:
            continue

        # Normal + plane coefficient
        n = _vec_norm(_vec_cross(_vec_sub(p2, p1), _vec_sub(p3, p1)))
        f.normal = n
        try:
            d = -(float(n.x) * float(p1.x) + float(n.y) * float(p1.y) + float(n.z) * float(p1.z))
        except Exception:
            d = 0.0
        f.coefficient = int(d)

        # Adjacency via "faces touching each (position-tolerant) vertex"
        corner_verts = (v1, v2, v3)
        vsets: list[set[int]] = []
        for cv in corner_verts:
            key = pos_key_of_vert[cv]
            s: set[int] = set()
            for ov in verts_by_pos.get(key, (cv,)):
                for face_idx in faces_by_vertex[ov]:
                    if face_idx != fi:
                        s.add(face_idx)
            vsets.append(s)

        # Edge (v1,v2), (v2,v3), (v3,v1) -> a1,a2,a3
        def _pick_neighbor(a: set[int], b: set[int]) -> int:
            inter = a & b
            return min(inter) if inter else 0

        f.a1 = _pick_neighbor(vsets[0], vsets[1])
        f.a2 = _pick_neighbor(vsets[1], vsets[2])
        f.a3 = _pick_neighbor(vsets[2], vsets[0])


# endregion


class MDLController(ComparableMixin):
    """Controller for animating node properties over time.

    Controllers define how node properties (position, orientation, color, etc.) change over time.
    They can use either linear interpolation (default) or bezier interpolation for smooth curves.

    References:
    ----------
        vendor/mdlops/MDLOpsM.pm:1649-1778 - Controller data structure and bezier flag detection
        vendor/mdlops/MDLOpsM.pm:1704-1710 - Bezier flag extraction from column count (bit 4)
        vendor/mdlops/MDLOpsM.pm:3764-3802 - ASCII controller reading with bezier support
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:664-690 - Binary controller reading

    Attributes:
    ----------
        controller_type: The type of controller (position, orientation, color, etc.)
        rows: List of keyframe data rows (time + values)
        is_bezier: True if using bezier interpolation, False for linear interpolation
            Reference: mdlops:1704-1710 - Detected from column_count & 16 flag

    Notes:
    -----
        Bezier controllers store 3 values per column instead of 1:
        - Value at keyframe
        - In-tangent (control point before keyframe)
        - Out-tangent (control point after keyframe)
        Reference: mdlops:1721-1723, 1749-1756
    """

    COMPARABLE_FIELDS = ("controller_type", "is_bezier")
    COMPARABLE_SEQUENCE_FIELDS = ("rows",)

    def __init__(
        self,
        controller_type: MDLControllerType,
        rows: list[MDLControllerRow],
        is_bezier: bool = False,
    ):
        # vendor/mdlops/MDLOpsM.pm:1666-1673 - Controller type and data rows
        self.controller_type: MDLControllerType = controller_type
        self.rows: list[MDLControllerRow] = rows

        # vendor/mdlops/MDLOpsM.pm:1704-1710 - Bezier flag from column count bit 4
        # vendor/mdlops/MDLOpsM.pm:3764-3770 - Bezier detection in ASCII reading
        # Some parsers historically passed None here; normalize to strict bool.
        self.is_bezier: bool = bool(is_bezier)

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(controller_type={self.controller_type!r}, rows={self.rows!r}, is_bezier={self.is_bezier!r})"

    def __eq__(self, other):
        if not isinstance(other, MDLController):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS)


class MDLControllerRow(ComparableMixin):
    COMPARABLE_FIELDS = ("time", "data")

    def __init__(
        self,
        time: float,
        data: list[float],
    ):
        self.time: float = time
        self.data: list[float] = data

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}({self.time!r}, {self.data!r})"

    def __str__(
        self,
    ):
        return f"{self.time} {self.data}".replace(",", "").replace("[", "").replace("]", "")

    def __eq__(self, other):
        if not isinstance(other, MDLControllerRow):
            return NotImplemented
        return _mdl_eq(self, other, ignore_keys=_MDL_EQ_IGNORE_KEYS)

    def __hash__(self):
        return _mdl_hash(self, ignore_keys=_MDL_EQ_IGNORE_KEYS)


# endregion
