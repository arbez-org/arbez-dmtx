#!/usr/bin/env bash
# Build libdmtx from source and stage the shared lib into the package so the
# wheel bundles it. Used by CI (Linux/macOS). BSD-2 licensed (vendored notice).
set -euo pipefail
# The pinned upstream version lives in ONE place: the repo-root LIBDMTX_VERSION
# file (single line). The build script reads it, the upstream-watch workflow
# reads it, and a bump is a one-line diff to that file. Override per-invocation
# with the LIBDMTX_VERSION env var.
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VER="${LIBDMTX_VERSION:-$(cat "$_here/../LIBDMTX_VERSION")}"
VER="$(printf '%s' "$VER" | tr -d '[:space:]')"
PKGLIB="${1:?usage: build_libdmtx.sh <dest dir for the .so/.dylib>}"
# Absolutize BEFORE we cd into the temp build dir — otherwise the relative dest
# would resolve against $work and the lib gets staged into the wrong directory.
mkdir -p "$PKGLIB"; PKGLIB="$(cd "$PKGLIB" && pwd)"
work="$(mktemp -d)"; cd "$work"
curl -fsSL "https://github.com/dmtx/libdmtx/archive/refs/tags/v${VER}.tar.gz" -o libdmtx.tgz
# Supply-chain: verify the source tarball against the pinned SHA256 (repo-root
# LIBDMTX_SHA256, alongside LIBDMTX_VERSION) before building. A moved tag /
# regenerated archive / MITM fails the build instead of baking foreign C into
# every wheel. Bumping LIBDMTX_VERSION MUST update LIBDMTX_SHA256 in the same diff.
expected_sha="$(printf '%s' "$(cat "$_here/../LIBDMTX_SHA256")" | tr -d '[:space:]')"
if command -v sha256sum >/dev/null 2>&1; then
  actual_sha="$(sha256sum libdmtx.tgz | awk '{print $1}')"
else
  actual_sha="$(shasum -a 256 libdmtx.tgz | awk '{print $1}')"
fi
if [ "$actual_sha" != "$expected_sha" ]; then
  echo "ERROR: libdmtx v${VER} tarball sha256 mismatch" >&2
  echo "  expected: $expected_sha" >&2
  echo "  actual:   $actual_sha" >&2
  echo "  (if upstream legitimately changed, update LIBDMTX_SHA256)" >&2
  exit 1
fi
echo "verified libdmtx v${VER} tarball sha256: $actual_sha"
tar xzf libdmtx.tgz && cd "libdmtx-${VER}"
# libdmtx uses autotools; regenerate then build a shared lib
if [ -x ./autogen.sh ]; then ./autogen.sh; else autoreconf -fi; fi
./configure --prefix="$work/inst" --disable-static --enable-shared
make -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
make install
mkdir -p "$PKGLIB"
# Stage REAL files (cp -L resolves the libtool symlinks). setuptools package_data
# does NOT pack symlinks, which is why the first CI wheel shipped without the lib.
if [ -e "$work"/inst/lib/libdmtx.dylib ]; then          # macOS
  cp -L "$work"/inst/lib/libdmtx.dylib "$PKGLIB/libdmtx.dylib"
  cp -L "$work"/inst/lib/libdmtx.dylib "$PKGLIB/libdmtx.0.dylib"
fi
if [ -e "$work"/inst/lib/libdmtx.so ]; then              # Linux (glibc/musl)
  cp -L "$work"/inst/lib/libdmtx.so "$PKGLIB/libdmtx.so"
  cp -L "$work"/inst/lib/libdmtx.so "$PKGLIB/libdmtx.so.0"
fi
# BSD-2 requires shipping libdmtx's copyright + disclaimer. We are inside the
# extracted source tree (cd'd above), so ./LICENSE is libdmtx's license. Fail
# loudly (no `|| true`) if it's absent so a non-compliant wheel can't ship.
cp -v ./LICENSE "$PKGLIB/THIRD_PARTY_LICENSES_libdmtx.txt"
echo "staged libdmtx ${VER} into $PKGLIB:"; ls -la "$PKGLIB"
