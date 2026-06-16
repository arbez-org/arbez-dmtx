# Changelog

Notable changes to **arbez-dmtx**. Versioning follows [SemVer](https://semver.org/)
(pre-1.0: behaviour may change on minor bumps).

## 0.0.1 — unreleased

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
