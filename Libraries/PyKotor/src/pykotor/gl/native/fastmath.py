from __future__ import annotations

from typing import Iterable, Sequence

try:
    import cffi
except ImportError:  # pragma: no cover
    cffi = None  # type: ignore[assignment]

_ffi = None
_lib = None

if cffi is not None:  # pragma: no branch
    _ffi = cffi.FFI()
    _ffi.cdef(
        """
        void transform_bounds(
            const float* vertices,
            int vertex_count,
            int stride_bytes,
            int position_offset,
            const float* matrix,
            float out_min[3],
            float out_max[3]
        );
        """
    )
    _C_SRC = r"""
    #include <math.h>

    void transform_bounds(
        const float* vertices,
        int vertex_count,
        int stride_bytes,
        int position_offset,
        const float* matrix,
        float out_min[3],
        float out_max[3]
    )
    {
        if (!vertices || vertex_count <= 0) {
            out_min[0] = out_min[1] = out_min[2] = 0.0f;
            out_max[0] = out_max[1] = out_max[2] = 0.0f;
            return;
        }

        const float* vptr = vertices;
        const char* base = (const char*)vertices;

        const float m00 = matrix[0];  const float m01 = matrix[4];
        const float m02 = matrix[8];  const float m03 = matrix[12];
        const float m10 = matrix[1];  const float m11 = matrix[5];
        const float m12 = matrix[9];  const float m13 = matrix[13];
        const float m20 = matrix[2];  const float m21 = matrix[6];
        const float m22 = matrix[10]; const float m23 = matrix[14];

        float minx = 0.0f, maxx = 0.0f;
        float miny = 0.0f, maxy = 0.0f;
        float minz = 0.0f, maxz = 0.0f;

        for (int i = 0; i < vertex_count; ++i) {
            const float* pos = (const float*)(base + i * stride_bytes + position_offset);
            const float x = pos[0];
            const float y = pos[1];
            const float z = pos[2];

            const float tx = m00 * x + m01 * y + m02 * z + m03;
            const float ty = m10 * x + m11 * y + m12 * z + m13;
            const float tz = m20 * x + m21 * y + m22 * z + m23;

            if (i == 0) {
                minx = maxx = tx;
                miny = maxy = ty;
                minz = maxz = tz;
            } else {
                if (tx < minx) minx = tx;
                if (tx > maxx) maxx = tx;
                if (ty < miny) miny = ty;
                if (ty > maxy) maxy = ty;
                if (tz < minz) minz = tz;
                if (tz > maxz) maxz = tz;
            }
        }

        out_min[0] = minx; out_min[1] = miny; out_min[2] = minz;
        out_max[0] = maxx; out_max[1] = maxy; out_max[2] = maxz;
    }
    """
    try:
        _lib = _ffi.verify(_C_SRC)
    except Exception:  # pragma: no cover
        _ffi = None
        _lib = None


def available() -> bool:
    return _lib is not None


def transform_bounds(
    vertex_blob: memoryview,
    vertex_count: int,
    stride_bytes: int,
    position_offset: int,
    matrix: Sequence[float],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if _lib is None or _ffi is None:
        raise RuntimeError("fastmath backend unavailable")

    if len(matrix) != 16:
        raise ValueError("matrix must contain 16 elements")

    buf = _ffi.from_buffer("const float *", vertex_blob)
    mat = _ffi.new("float[16]", matrix)
    out_min = _ffi.new("float[3]")
    out_max = _ffi.new("float[3]")
    _lib.transform_bounds(buf, int(vertex_count), int(stride_bytes), int(position_offset), mat, out_min, out_max)
    return (
        (out_min[0], out_min[1], out_min[2]),
        (out_max[0], out_max[1], out_max[2]),
    )

