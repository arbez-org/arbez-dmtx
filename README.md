# arbez-dmtx

[![PyPI](https://img.shields.io/pypi/v/arbez-dmtx)](https://pypi.org/project/arbez-dmtx/)
[![CI](https://github.com/arbez-org/arbez-dmtx/actions/workflows/wheels.yml/badge.svg)](https://github.com/arbez-org/arbez-dmtx/actions/workflows/wheels.yml)
[![Python 3.10–3.15](https://img.shields.io/badge/python-3.10--3.15-blue.svg)](https://pypi.org/project/arbez-dmtx/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)


**Read and write Data Matrix barcodes from Python — with the native
[libdmtx](https://github.com/dmtx/libdmtx) library bundled in the wheel on every
platform.** No `brew install` / `apt-get install`, no compiler. Pure `ctypes`,
so one small wheel per platform works on **all of Python 3.10–3.15, including
free-threaded 3.13t / 3.14t / 3.15t**.

```python
from arbez_dmtx import decode, encode
from PIL import Image

decode(Image.open("code.png"))
# [Decoded(data=b'Stegosaurus', rect=Rect(left=5, top=6, width=96, height=95))]

enc = encode(b"hello")
Image.frombytes("RGB", (enc.width, enc.height), enc.pixels).save("dmtx.png")
```

## Install

```sh
pip install arbez-dmtx
```

That's it — the libdmtx shared library is inside the wheel. No system packages.

**Supported platforms** (wheels are published for these; there is no sdist, so
`pip install` requires a matching wheel):

| OS | Arch | Wheel |
|---|---|---|
| macOS | arm64 (Apple Silicon) | ✅ |
| Linux | x86_64, aarch64 (glibc / manylinux_2_28) | ✅ |
| Linux | x86_64, aarch64 (musl / musllinux_1_2, e.g. Alpine) | ✅ |
| Windows | x86_64 | ✅ |

Not yet built: macOS x86_64 (Intel), Windows arm64. If you need one, open an issue.

## Relationship to pylibdmtx

arbez-dmtx is a friendly, modernised continuation of
**[pylibdmtx](https://github.com/NaturalHistoryMuseum/pylibdmtx)** by Lawrence
Hudson / the Natural History Museum (MIT). It **vendors pylibdmtx's excellent
ctypes wrapper** and keeps the **same public API**, but closes the gaps that made
pylibdmtx awkward to depend on in 2026:

| | pylibdmtx | **arbez-dmtx** |
|---|---|---|
| Native libdmtx bundled | Windows only | **every OS** (macOS arm64, Linux x86_64/aarch64, Windows) |
| Off-Windows install | `brew`/`apt` the system lib yourself | nothing — it's in the wheel |
| Python support | 2.7, 3.5–3.10 | **3.10–3.15** incl. free-threaded **3.13t/3.14t/3.15t** |
| Bundled libdmtx | 0.7.x (older) | **tracks upstream** (currently 0.7.8) via a CI watcher |
| `distutils` | required (broken on 3.12+) | removed |
| PyPI freshness | stale | maintained |

**Migrating is a one-line import swap** — the function/return signatures match:

```python
# before
from pylibdmtx.pylibdmtx import decode, encode
# after
from arbez_dmtx import decode, encode
```

If you only need this library on Windows, pylibdmtx already works great; the
value here is everywhere *else* (and on the new free-threaded interpreters).

## API

The full pylibdmtx surface is re-exported at the top level:

```python
from arbez_dmtx import (
    decode, encode,                       # the two operations
    Decoded, Rect, Encoded,               # result types
    ENCODING_SCHEME_NAMES, ENCODING_SIZE_NAMES,  # encode() vocabularies
    PyLibDMTXError,                       # error type
    libdmtx_version,                      # bundled libdmtx version string
)
```

- **`decode(image, ...)`** accepts a `PIL.Image`, a `numpy.ndarray` (e.g. from
  OpenCV), or a `(pixels, width, height)` tuple, and the full libdmtx tuning
  surface: `timeout`, `gap_size`, `shrink`, `shape`, `deviation`, `threshold`,
  `min_edge`, `max_edge`, `corrections`, `max_count`. Returns a list of
  `Decoded(data: bytes, rect: Rect)`.
- **`encode(data, scheme=None, size=None)`** → `Encoded(width, height, bpp,
  pixels)`; `scheme`/`size` come from `ENCODING_SCHEME_NAMES` /
  `ENCODING_SIZE_NAMES`.

## Why pure ctypes?

No compiled extension means (a) **one `py3-none-<platform>` wheel covers every
Python version** — including the free-threaded builds, with no per-ABI matrix —
and (b) importing it **never re-enables the GIL**; `ctypes` releases the GIL
around each native call, so concurrent decode is safe on 3.13t/3.14t/3.15t.

## License & attribution

Apache-2.0 (this wrapper). Bundles **libdmtx** (BSD-2-Clause, © Mike Laughton,
Vadim A. Misbakh-Soloviov and others) and vendors the **pylibdmtx** ctypes
wrapper (MIT, © Lawrence Hudson). Full notices in [`NOTICE`](NOTICE); the libdmtx
license also ships inside each wheel as `THIRD_PARTY_LICENSES_libdmtx.txt`.

Not affiliated with or endorsed by the pylibdmtx authors — just standing on their
shoulders, gratefully.
