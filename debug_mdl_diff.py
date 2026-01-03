from __future__ import annotations

import os
import sys

from pathlib import Path
from typing import NoReturn

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), "Libraries/PyKotor/src"))


def _die(msg: str) -> NoReturn:
    raise SystemExit(msg)


def debug_diff(*, resref: str = "3dgui") -> int:
    """Print a human-readable diff between binary-parsed and roundtripped MDLs."""
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.mdl import MDLAsciiReader, MDLAsciiWriter, MDLBinaryReader
    from pykotor.resource.formats.mdl.mdl_auto import read_mdl, write_mdl
    from pykotor.resource.type import ResourceType

    k1_path = os.environ.get("K1_PATH")
    if not k1_path:
        _die("Missing K1_PATH env var (set it to your KOTOR install root).")

    root = Path(k1_path)
    if not root.exists():
        _die(f"K1_PATH does not exist: {root}")

    inst = Installation(root)

    mdl_res = inst.resource(resref, ResourceType.MDL)
    mdx_res = inst.resource(resref, ResourceType.MDX)
    if mdl_res is None or mdx_res is None:
        _die(f"Could not locate {resref}.mdl/.mdx in installation: {root}")

    mdl_bytes = mdl_res.data
    mdx_bytes = mdx_res.data

    mdl_bin = MDLBinaryReader(mdl_bytes, source_ext=mdx_bytes).load()
    ascii_bytes = bytearray()
    MDLAsciiWriter(mdl_bin, target=ascii_bytes).write()
    mdl_ascii = MDLAsciiReader(source=ascii_bytes).load()

    # Reproduce the test's binary->ascii->binary roundtrip.
    out_mdl = bytearray()
    out_mdx = bytearray()
    write_mdl(mdl_ascii, out_mdl, ResourceType.MDL, target_ext=out_mdx)
    mdl_bin_round = read_mdl(
        bytes(out_mdl),
        source_ext=bytes(out_mdx) if out_mdx else None,
        file_format=ResourceType.MDL,
    )

    # 1) Field-driven compare() output is intentionally suppressed by default because it is
    # extremely verbose for large MDLs (controllers contain many float rows). Enable by setting:
    #   $Env:PYKOTOR_MDL_VERBOSE_COMPARE='1'
    if os.environ.get("PYKOTOR_MDL_VERBOSE_COMPARE") == "1":
        logs: list[str] = []
        same = mdl_bin.compare(mdl_ascii, log_func=logs.append)
        if not same and logs:
            print("\n".join(logs))

    # 2) Equality-driven pinpointing: locate the first attribute path that breaks MDL.__eq__,
    # using mdl_data.py's canonicalization rules.
    if mdl_bin != mdl_ascii:
        from pykotor.resource.formats.mdl import mdl_data as md

        # High-level MDL equality breakdown (before drilling to node-level).
        print("\n-- MDL equality breakdown --")
        try:
            a_ids_ok = md._mdl_validate_ids_self_consistent(mdl_bin.root)  # noqa: SLF001
            b_ids_ok = md._mdl_validate_ids_self_consistent(mdl_ascii.root)  # noqa: SLF001
            ids_equiv_ok = md._mdl_ids_equivalent_subtree(mdl_bin.root, mdl_ascii.root)  # noqa: SLF001
            print(f"ids_self_consistent: bin={bool(a_ids_ok)} ascii={bool(b_ids_ok)} ids_equivalent={bool(ids_equiv_ok)}")
        except Exception as e:
            print(f"ids checks: <error> {e!r}")
        try:
            def _akey(anim: md.MDLAnimation) -> tuple[str, str]:
                return (anim.name, anim.root_model)

            a_keys = [_akey(a) for a in mdl_bin.anims]
            b_keys = [_akey(a) for a in mdl_ascii.anims]
            print(f"anims: bin={len(a_keys)} ascii={len(b_keys)}")
            if set(a_keys) != set(b_keys):
                print("anim keys differ")
                print("bin keys:", sorted(a_keys))
                print("ascii keys:", sorted(b_keys))
            else:
                a_anims = {_akey(a): a for a in mdl_bin.anims}
                b_anims = {_akey(a): a for a in mdl_ascii.anims}
                for k in sorted(a_anims.keys()):
                    if not md._mdl_animation_equal(a_anims[k], b_anims[k]):  # noqa: SLF001
                        print(f"first anim mismatch at key={k!r}")
                        # Reuse the mismatch finder to get a concrete path.
                        sub = _find_first_mismatch(a_anims[k], b_anims[k], "anim")
                        if sub:
                            print("anim mismatch path:", sub)
                        break
        except Exception as e:
            print(f"anim keys: <error> {e!r}")

        def _walk_nodes(root_node: md.MDLNode) -> list[md.MDLNode]:
            out: list[md.MDLNode] = [root_node]
            out.extend(root_node.descendants())
            return out

        def _find_first_mismatch(a: object, b: object, base: str) -> str | None:
            if a is b:
                return None
            if a is None or b is None:
                return base

            if isinstance(a, (bool, int, str, bytes)) or isinstance(b, (bool, int, str, bytes)):
                return None if a == b else base

            if isinstance(a, float) and isinstance(b, float):
                return None if md._mdl_float_eq(a, b) else base  # noqa: SLF001

            if isinstance(a, (md.Vector2, md.Vector3, md.Vector4)) and isinstance(b, (md.Vector2, md.Vector3, md.Vector4)):
                return None if md._mdl_deep_eq(a, b, ignore_keys=md._MDL_EQ_IGNORE_KEYS) else base  # noqa: SLF001

            if isinstance(a, md.Color) and isinstance(b, md.Color):
                return None if md._mdl_deep_eq(a, b, ignore_keys=md._MDL_EQ_IGNORE_KEYS) else base  # noqa: SLF001

            # Collections
            if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
                if len(a) != len(b):
                    return f"{base} (len {len(a)} != {len(b)})"
                for i, (av, bv) in enumerate(zip(a, b)):
                    sub = _find_first_mismatch(av, bv, f"{base}[{i}]")
                    if sub:
                        return sub
                return None

            if isinstance(a, dict) and isinstance(b, dict):
                if set(a.keys()) != set(b.keys()):
                    return f"{base} (dict keys differ)"
                for k in sorted(a.keys(), key=lambda x: str(x)):
                    sub = _find_first_mismatch(a[k], b[k], f"{base}[{k!r}]")
                    if sub:
                        return sub
                return None

            # Objects with __dict__
            da = getattr(a, "__dict__", None)
            db = getattr(b, "__dict__", None)
            if isinstance(da, dict) and isinstance(db, dict):
                ignore = md._MDL_EQ_IGNORE_KEYS | md._MDL_EQ_ID_KEYS  # noqa: SLF001
                keys_a = {k for k in da.keys() if not str(k).startswith("_") and k not in ignore}
                keys_b = {k for k in db.keys() if not str(k).startswith("_") and k not in ignore}
                if keys_a != keys_b:
                    return f"{base} (object keys differ)"

                for k in sorted(keys_a):
                    ctx = md._CTX_NONE  # noqa: SLF001
                    if k == "children":
                        ctx = md._CTX_CHILDREN  # noqa: SLF001
                    elif k == "controllers":
                        ctx = md._CTX_CONTROLLERS  # noqa: SLF001
                    elif k == "rows":
                        ctx = md._CTX_ROWS  # noqa: SLF001
                    elif k == "anims":
                        ctx = md._CTX_ANIMS  # noqa: SLF001

                    if not md._mdl_deep_eq(da[k], db[k], ignore_keys=ignore, _ctx=ctx):  # noqa: SLF001
                        sub = _find_first_mismatch(da[k], db[k], f"{base}.{k}")
                        return sub or f"{base}.{k}"

                return None

            return None if a == b else base

        nodes_a = {n.name: n for n in _walk_nodes(mdl_bin.root)}
        nodes_b = {n.name: n for n in _walk_nodes(mdl_ascii.root)}

        # Mirror MDL.__eq__'s name+parent-edge keyed geometry comparison.
        try:
            pa = md._mdl_node_parent_edges_by_name(list(nodes_a.values()))  # noqa: SLF001
            pb = md._mdl_node_parent_edges_by_name(list(nodes_b.values()))  # noqa: SLF001
            if pa != pb:
                print("\n== MDL.__eq__ first mismatch ==\ngeometry parent edges differ")
                return 1
        except Exception:
            pass

        for name in sorted(set(nodes_a.keys()) | set(nodes_b.keys()), key=str.lower):
            na = nodes_a.get(name)
            nb = nodes_b.get(name)
            if na is None or nb is None:
                print(f"\n== MDL.__eq__ first mismatch ==\nMissing node: {name!r}")
                return 1
            if not md._mdl_node_payload_equal(na, nb, in_geometry_tree=True):  # noqa: SLF001
                where = _find_first_mismatch(na, nb, f"root.{name}")
                if name.lower() == "backcape":
                    print("\n-- BackCape attachment summary --")
                    print(f"bin: node_type={na.node_type} mesh={na.mesh is not None} skin={na.skin is not None} dangly={na.dangly is not None} aabb={na.aabb is not None} saber={na.saber is not None}")
                    print(f"ascii: node_type={nb.node_type} mesh={nb.mesh is not None} skin={nb.skin is not None} dangly={nb.dangly is not None} aabb={nb.aabb is not None} saber={nb.saber is not None}")
                    try:
                        print("\n-- BackCape canonical transform --")
                        print("bin header pos:", md._mdl_node_header_position(na))  # noqa: SLF001
                        print("asc header pos:", md._mdl_node_header_position(nb))  # noqa: SLF001
                        print("bin canon pos:", md._mdl_node_canonical_position_strict(na, prefer_controllers=False))  # noqa: SLF001
                        print("asc canon pos:", md._mdl_node_canonical_position_strict(nb, prefer_controllers=False))  # noqa: SLF001
                        print("bin header ori:", md._mdl_node_header_orientation(na))  # noqa: SLF001
                        print("asc header ori:", md._mdl_node_header_orientation(nb))  # noqa: SLF001
                        print("bin canon ori:", md._mdl_node_canonical_orientation_strict(na, prefer_controllers=False))  # noqa: SLF001
                        print("asc canon ori:", md._mdl_node_canonical_orientation_strict(nb, prefer_controllers=False))  # noqa: SLF001
                    except Exception as e:
                        print("canon transform: <error>", repr(e))
                    try:
                        print("\n-- BackCape canonical controllers (hashable) --")
                        print("bin:", md._mdl_canonical_controllers_hashable(na, drop_transform_controllers=True))  # noqa: SLF001
                        print("asc:", md._mdl_canonical_controllers_hashable(nb, drop_transform_controllers=True))  # noqa: SLF001
                    except Exception as e:
                        print("canon controllers: <error>", repr(e))
                    try:
                        if na.mesh is not None and nb.mesh is not None:
                            print("\n-- BackCape mesh_equal --")
                            print("mesh_equal:", bool(md._mdl_mesh_equal(na.mesh, nb.mesh)))  # noqa: SLF001
                            subm = _find_first_mismatch(na.mesh, nb.mesh, "BackCape.mesh")
                            if subm:
                                print("first mesh mismatch path:", subm)
                            if not md._mdl_mesh_equal(na.mesh, nb.mesh):  # noqa: SLF001
                                a = na.mesh
                                b = nb.mesh
                                print("\n-- BackCape mesh mismatch explanation (first failing check) --")
                                if not md._mdl_mesh_validate_aliases(a):  # noqa: SLF001
                                    print("alias invalid (bin): vertex_uvs vs vertex_uv1")
                                if not md._mdl_mesh_validate_aliases(b):  # noqa: SLF001
                                    print("alias invalid (ascii): vertex_uvs vs vertex_uv1")
                                for field in (
                                    "texture_1",
                                    "texture_2",
                                    "transparency_hint",
                                    "has_lightmap",
                                    "rotate_texture",
                                    "background_geometry",
                                    "shadow",
                                    "beaming",
                                    "render",
                                    "dirt_enabled",
                                    "dirt_texture",
                                    "dirt_coordinate_space",
                                ):
                                    if getattr(a, field) != getattr(b, field):
                                        print(f"{field}: bin={getattr(a, field)!r} ascii={getattr(b, field)!r}")
                                        break
                                else:
                                    # Deep fields
                                    if not md._mdl_deep_eq(a.diffuse, b.diffuse, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                        print("diffuse differs")
                                    elif not md._mdl_deep_eq(a.ambient, b.ambient, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                        print("ambient differs")
                                    elif not md._mdl_deep_eq(a.bb_min, b.bb_min, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                        print("bb_min differs", a.bb_min, b.bb_min)
                                    elif not md._mdl_deep_eq(a.bb_max, b.bb_max, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                        print("bb_max differs", a.bb_max, b.bb_max)
                                    elif md._qfloat(float(a.radius)) != md._qfloat(float(b.radius)):  # noqa: SLF001
                                        print("radius differs", a.radius, b.radius)
                                    elif not md._mdl_deep_eq(a.average, b.average, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                        print("average differs", a.average, b.average)
                                    elif md._qfloat(float(a.area)) != md._qfloat(float(b.area)):  # noqa: SLF001
                                        print("area differs", a.area, b.area)
                                    elif not md._mdl_deep_eq(a.vertex_positions, b.vertex_positions, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                        print("vertex_positions differs")
                                    else:
                                        an = a.vertex_normals or []
                                        bn = b.vertex_normals or []
                                        if an and bn and not md._mdl_deep_eq(an, bn, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                            print("vertex_normals differs")
                                        elif not md._mdl_deep_eq(a.vertex_uv1, b.vertex_uv1, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                            print("vertex_uv1 differs")
                                        elif not md._mdl_deep_eq(a.vertex_uv2, b.vertex_uv2, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                            print("vertex_uv2 differs")
                                        elif not md._mdl_deep_eq(a.faces, b.faces, ignore_keys=md._MDL_EQ_IGNORE_KEYS):  # noqa: SLF001
                                            print("faces differs")
                                        else:
                                            print("<could not identify failing check?>")
                        if na.skin is not None and nb.skin is not None:
                            print("\n-- BackCape skin_deep_eq --")
                            print("skin_equal:", bool(md._mdl_deep_eq(na.skin, nb.skin, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                            subs = _find_first_mismatch(na.skin, nb.skin, "BackCape.skin")
                            if subs:
                                print("first skin mismatch path:", subs)
                    except Exception as e:
                        print("mesh/skin diagnostics: <error>", repr(e))
                # Distinguish "payload mismatch" vs "id/parent_id consistency mismatch".
                ignore = md._MDL_EQ_IGNORE_KEYS | md._MDL_EQ_ID_KEYS  # noqa: SLF001
                deep_ok = md._mdl_eq(na, nb, ignore_keys=ignore)  # noqa: SLF001
                ids_ok = md._mdl_ids_equivalent_subtree(na, nb)  # noqa: SLF001
                if not deep_ok or not ids_ok:
                    print(f"\n-- mismatch breakdown for {name} --")
                    print(f"payload_equal={bool(deep_ok)} ids_equivalent_subtree={bool(ids_ok)}")
                # If the first mismatch is controller-related, dump a compact summary to speed iteration.
                if where and ".controllers" in where:
                    import re

                    def _resolve(obj: object, expr: str) -> object:
                        """Resolve a dotted/indexed path suffix like '.children[0].controllers'."""
                        cur: object = obj
                        for m in re.finditer(r"(?:\.([A-Za-z_][A-Za-z0-9_]*))|(?:\[(\d+)\])", expr):
                            attr = m.group(1)
                            idx = m.group(2)
                            if attr is not None:
                                cur = getattr(cur, attr)
                            elif idx is not None:
                                cur = cur[int(idx)]  # type: ignore[index]
                        return cur

                    prefix = f"root.{name}"
                    suffix = where
                    if suffix.startswith(prefix):
                        suffix = suffix[len(prefix) :]
                    suffix = suffix.split(" ", 1)[0]
                    try:
                        ta = _resolve(na, suffix)
                        tb = _resolve(nb, suffix)
                    except Exception:
                        ta = na.controllers
                        tb = nb.controllers
                    if isinstance(ta, md.MDLNode):
                        ta = ta.controllers
                    if isinstance(tb, md.MDLNode):
                        tb = tb.controllers

                    print("\n-- controller summary (bin) --")
                    for c in ta:  # type: ignore[union-attr]
                        print(f"{c.controller_type.name}: rows={len(c.rows)} bezier={bool(c.is_bezier)}")
                    print("\n-- controller summary (ascii) --")
                    for c in tb:  # type: ignore[union-attr]
                        print(f"{c.controller_type.name}: rows={len(c.rows)} bezier={bool(c.is_bezier)}")
                print(f"\n== MDL.__eq__ first mismatch ==\n{where or f'root.{name}'}")
                return 1

        print("\n== MDL.__eq__ mismatch ==\nCould not localize mismatch (unexpected).")
        return 1

    # Even if equality succeeds, verify hash alignment (pytest asserts this).
    hb = hash(mdl_bin)
    ha = hash(mdl_ascii)
    if hb != ha:
        print(f"== MDL hash mismatch ==\nbin={hb}\nascii={ha}")
        try:
            from pykotor.resource.formats.mdl import mdl_data as md

            def _hash_parts(m: md.MDL) -> dict[str, int]:
                parts: dict[str, int] = {}
                parts["name"] = hash(m.name)
                parts["fog"] = hash(m.fog)
                parts["supermodel"] = hash(m.supermodel)
                parts["classification"] = hash(int(m.classification))
                parts["classification_unk1"] = hash(int(m.classification_unk1))
                parts["animation_scale"] = hash(md._qfloat(float(m.animation_scale)))  # noqa: SLF001
                parts["radius"] = hash(md._qfloat(float(m.radius)))  # noqa: SLF001
                parts["bmin"] = hash((md._qfloat(float(m.bmin.x)), md._qfloat(float(m.bmin.y)), md._qfloat(float(m.bmin.z))))  # noqa: SLF001
                parts["bmax"] = hash((md._qfloat(float(m.bmax.x)), md._qfloat(float(m.bmax.y)), md._qfloat(float(m.bmax.z))))  # noqa: SLF001
                parts["headlink"] = hash(m.headlink)
                parts["compress_quaternions"] = hash(int(m.compress_quaternions))

                nodes = m.all_nodes()
                by = {n.name: n for n in nodes}
                parent = md._mdl_node_parent_edges_by_name(list(by.values()))  # noqa: SLF001
                for name in sorted(by.keys()):
                    n = by[name]
                    base = 0
                    base ^= hash(("node", name, parent.get(name)))
                    base ^= hash(md._mdl_node_header_position(n))  # noqa: SLF001
                    base ^= hash(md._mdl_node_header_orientation(n))  # noqa: SLF001
                    base ^= hash(md._mdl_canonical_controllers_hashable(n, drop_transform_controllers=True))  # noqa: SLF001
                    if n.light is not None:
                        base ^= hash(("light", md._mdl_deep_hash(n.light, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                    else:
                        base ^= hash(("light", md._mdl_deep_hash(None)))  # noqa: SLF001
                    if n.emitter is not None:
                        base ^= hash(("emitter", md._mdl_deep_hash(n.emitter, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                    else:
                        base ^= hash(("emitter", md._mdl_deep_hash(None)))  # noqa: SLF001
                    if n.reference is not None:
                        base ^= hash(("reference", md._mdl_deep_hash(n.reference, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                    else:
                        base ^= hash(("reference", md._mdl_deep_hash(None)))  # noqa: SLF001
                    if n.mesh is not None:
                        base ^= hash(("mesh", md._mdl_mesh_hash(n.mesh)))  # noqa: SLF001
                    else:
                        base ^= hash(("mesh", md._mdl_deep_hash(None)))  # noqa: SLF001
                    if n.skin is not None:
                        base ^= hash(("skin", md._mdl_deep_hash(n.skin, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                    else:
                        base ^= hash(("skin", md._mdl_deep_hash(None)))  # noqa: SLF001
                    if n.dangly is not None:
                        base ^= hash(("dangly", md._mdl_deep_hash(n.dangly, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                    else:
                        base ^= hash(("dangly", md._mdl_deep_hash(None)))  # noqa: SLF001
                    if n.aabb is not None:
                        base ^= hash(("aabb", md._mdl_deep_hash(n.aabb, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                    else:
                        base ^= hash(("aabb", md._mdl_deep_hash(None)))  # noqa: SLF001
                    if n.saber is not None:
                        base ^= hash(("saber", md._mdl_deep_hash(n.saber, ignore_keys=md._MDL_EQ_IGNORE_KEYS)))  # noqa: SLF001
                    else:
                        base ^= hash(("saber", md._mdl_deep_hash(None)))  # noqa: SLF001
                    parts[f"node:{name}"] = base

                # animations
                def _akey(anim: md.MDLAnimation) -> tuple[str, str]:
                    return (anim.name, anim.root_model)

                for k in sorted((_akey(a) for a in m.anims)):
                    anim = next(a for a in m.anims if _akey(a) == k)
                    parts[f"anim-meta:{k}"] = hash(("anim", k, md._qfloat(float(anim.anim_length)), md._qfloat(float(anim.transition_length))))  # noqa: SLF001
                    parts[f"anim-events:{k}"] = hash(md._mdl_deep_hash(anim.events, ignore_keys=md._MDL_EQ_IGNORE_KEYS))  # noqa: SLF001
                    a_by = md._mdl_animation_nodes_by_name(anim)  # noqa: SLF001
                    a_parent = md._mdl_node_parent_edges_by_name(list(a_by.values()))  # noqa: SLF001
                    for name in sorted(a_by.keys()):
                        n = a_by[name]
                        base = 0
                        base ^= hash(("anode", k, name, a_parent.get(name)))
                        base ^= hash(md._mdl_node_canonical_position_strict(n, prefer_controllers=True))  # noqa: SLF001
                        base ^= hash(md._mdl_node_canonical_orientation_strict(n, prefer_controllers=True))  # noqa: SLF001
                        base ^= hash(md._mdl_canonical_controllers_hashable(n, drop_transform_controllers=False))  # noqa: SLF001
                        parts[f"anode:{k}:{name}"] = base
                return parts

            pb = _hash_parts(mdl_bin)
            pa = _hash_parts(mdl_ascii)
            for k in sorted(set(pb.keys()) | set(pa.keys())):
                if pb.get(k) != pa.get(k):
                    print(f"-- first hash part mismatch: {k} --")
                    print("bin part:", pb.get(k))
                    print("asc part:", pa.get(k))
                    if k.startswith("node:"):
                        name = k.split(":", 1)[1]
                        n1 = {n.name: n for n in mdl_bin.all_nodes()}.get(name)
                        n2 = {n.name: n for n in mdl_ascii.all_nodes()}.get(name)
                        if n1 and n2:
                            parent1 = md._mdl_node_parent_edges_by_name(list({n.name: n for n in mdl_bin.all_nodes()}.values()))  # noqa: SLF001
                            parent2 = md._mdl_node_parent_edges_by_name(list({n.name: n for n in mdl_ascii.all_nodes()}.values()))  # noqa: SLF001
                            comps = []
                            comps.append(("node-edge", hash(("node", name, parent1.get(name))), hash(("node", name, parent2.get(name)))))
                            comps.append(("header-pos", hash(md._mdl_node_header_position(n1)), hash(md._mdl_node_header_position(n2))))  # noqa: SLF001
                            comps.append(("header-ori", hash(md._mdl_node_header_orientation(n1)), hash(md._mdl_node_header_orientation(n2))))  # noqa: SLF001
                            comps.append(("controllers", hash(md._mdl_canonical_controllers_hashable(n1, drop_transform_controllers=True)), hash(md._mdl_canonical_controllers_hashable(n2, drop_transform_controllers=True))))  # noqa: SLF001
                            comps.append(("mesh", hash(md._mdl_mesh_hash(n1.mesh)) if n1.mesh else 0, hash(md._mdl_mesh_hash(n2.mesh)) if n2.mesh else 0))  # noqa: SLF001
                            comps.append(("skin", hash(md._mdl_deep_hash(n1.skin, ignore_keys=md._MDL_EQ_IGNORE_KEYS)) if n1.skin else 0, hash(md._mdl_deep_hash(n2.skin, ignore_keys=md._MDL_EQ_IGNORE_KEYS)) if n2.skin else 0))  # noqa: SLF001
                            for label, a, b in comps:
                                if a != b:
                                    print(f"-- node subpart mismatch: {label} --")
                                    print("bin:", a)
                                    print("asc:", b)
                                    break
                    break
        except Exception as e:
            print(f"hash breakdown: <error> {e!r}")
        return 2

    # If binary vs ASCII matches but binary->ascii->binary does not, print that diff.
    if mdl_bin != mdl_bin_round:
        print("\n== binary->ascii->binary mismatch ==")
        logs2: list[str] = []
        _ = mdl_bin.compare(mdl_bin_round, log_func=logs2.append)
        if logs2:
            print("\n".join(logs2[:400]))
        return 3

    print("<no-diff>")
    return 0


if __name__ == "__main__":
    raise SystemExit(debug_diff())
