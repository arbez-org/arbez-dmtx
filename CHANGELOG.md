# Changelog

Notable changes to **arbez-dmtx**. Versioning follows [SemVer](https://semver.org/)
(pre-1.0: behaviour may change on minor bumps).

## 0.0.3 — 2026-10-16

Python 3.15, and Actions off Node 20.

- **`Requires-Python` is now `>=3.10,<3.16`.** 0.0.2 is already published with
  `<3.15`, so the cap lift is this release. The wheel stays `py3-none` (no ABI
  matrix). CPython 3.15 and free-threaded 3.15t join the build matrix and skip
  when a runner image has no such interpreter. No API change. Bundled libdmtx
  stays 0.7.8.
- **GitHub Actions moved off Node 20.** `actions/checkout` v7,
  `actions/setup-python` v7, `astral-sh/setup-uv` v10.3.0, `actions/upload-artifact`
  v7, and `actions/download-artifact` v8 run on Node 24. The PyPI publish
  composite is the v1.14.2 commit, whose `setup-python` is also Node 24.
- **Ruff 0.16's expanded default rules are clean.** `uvx ruff check` is
  unpinned in CI. The fixes are import order, f-strings, a sorted `__all__`,
  and catching `ImportError` around the optional zxing-cpp import. No behavior
  change.

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
