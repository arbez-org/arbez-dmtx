#!/bin/sh
# Build + test the arbez-dmtx musllinux wheel INSIDE a pypa musllinux_1_2 image.
#
# Invoked by .github/workflows/build.yml via `docker run` on a GLIBC host (not as
# a job-level container): GitHub Actions cannot run Node JS actions such as
# actions/checkout / actions/upload-artifact inside an Alpine ARM64 container
# ("JavaScript Actions in Alpine containers are only supported on x64 Linux
# runners"). So checkout + artifact upload run on the host and only this build
# runs in the musl image — the same host-docker approach cibuildwheel uses.
#
# Expects: CWD = the repo root (mounted at /io); PLAT env = the musllinux
# platform tag (e.g. musllinux_1_2_x86_64). Writes ./dist/<wheel> for the host
# upload-artifact step.
set -e
: "${PLAT:?PLAT env (e.g. musllinux_1_2_x86_64) is required}"

# musl image is Alpine -> apk (build-base = gcc/make; autotools drive
# autogen.sh/autoreconf; curl+tar fetch the pinned source). build_libdmtx.sh is
# otherwise libc-agnostic and still sha256-verifies the pinned tarball.
apk add --no-cache build-base autoconf automake libtool curl tar >/dev/null
bash scripts/build_libdmtx.sh src/arbez_dmtx/_libdmtx

P=/opt/python/cp311-cp311/bin/python
"$P" -m pip install -q --upgrade build wheel twine
"$P" -m build --wheel --outdir dist_raw
# Retag the py3-none wheel to the musllinux platform (the bundled .so already
# matches the image's musl floor), same as the manylinux path in build.yml.
"$P" -m wheel tags --platform-tag "$PLAT" --remove dist_raw/*.whl
mkdir -p dist && rm -f dist/*.whl && mv dist_raw/*.whl dist/
echo "wheel: $(ls dist/*.whl)"
case "$(ls dist/*.whl)" in
  *linux_x86_64.whl|*linux_aarch64.whl) echo "ERROR: bare linux tag survived retag"; exit 1 ;;
esac
"$P" -m twine check dist/*.whl

# Exercise the single py3-none wheel on every interpreter the image ships within
# our supported range (>=3.10,<3.16). Absent versions (e.g. cp313t) skip cleanly;
# cp314-cp314t and cp315-cp315t exercise the free-threaded (GIL-off) path.
for PY in /opt/python/cp3*/bin/python; do
  [ -x "$PY" ] || continue
  tag=$(basename "$(dirname "$(dirname "$PY")")")   # e.g. cp310-cp310, cp314-cp314t
  case "$tag" in
    cp310-*|cp311-*|cp312-*|cp313-*|cp314-*|cp315-*) ;;
    *) echo "skip $tag (outside >=3.10,<3.16)"; continue ;;
  esac
  echo "--- musl $tag ---"
  "$PY" -m pip install -q pytest pillow dist/*.whl
  "$PY" -m pip install -q numpy || echo "numpy unavailable ($tag); ndarray test self-skips"
  "$PY" -c 'import sys, arbez_dmtx; print("  loaded", arbez_dmtx.libdmtx_version(), "| gil", getattr(sys, "_is_gil_enabled", lambda: "n/a")())'
  "$PY" -m pytest tests -q
done
