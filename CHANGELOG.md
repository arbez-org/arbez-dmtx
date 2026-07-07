# Changelog

Notable changes to **arbez-dmtx**. Versioning follows [SemVer](https://semver.org/)
(pre-1.0: behaviour may change on minor bumps).

## 0.0.2 — 2026-07-07

Alpine / musl support.

- **Added `musllinux_1_2` wheels for x86_64 and aarch64** — `pip install
  arbez-dmtx` now works inside Alpine-based images (musl libc), not just glibc
  (manylinux). The native libdmtx is built against musl in the
  `quay.io/pypa/musllinux_1_2_*` containers and bundled the same way. Closes #1.
- No API changes; the runtime loader and public surface are unchanged.

## 0.0.1 — 2026-06-16

First release. A self-contained, modern continuation of
[pylibdmtx](https://github.com/NaturalHistoryMuseum/pylibdmtx).

- Pure-`ctypes` Data Matrix **encode/decode**, vendoring pylibdmtx's MIT wrapper
  (with the `distutils` dependency removed) over a bundled native **libdmtx 0.7.8**.
- **Native lib bundled in the wheel on every platform** — macOS arm64, Linux
  x86_64/aarch64 (manylinux_2_28), Windows. No `brew`/`apt`/system install.
- One `py3-none-<platform>` wheel per platform; works on **Python 3.10–3.14
  including free-threaded 3.13t / 3.14t** (no per-ABI matrix; never re-enables
  the GIL).
- Full pylibdmtx-compatible public API: `decode`, `encode`, `Decoded`, `Rect`,
  `Encoded`, `ENCODING_SCHEME_NAMES`, `ENCODING_SIZE_NAMES`, `PyLibDMTXError`.
- Single-source upstream pin in `LIBDMTX_VERSION`; a weekly CI watcher
  (`upstream-watch.yml`) files a tracking issue when libdmtx publishes a newer
  release.
