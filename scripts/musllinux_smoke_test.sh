#!/bin/sh
# Smoke-test the PUBLISHED arbez-dmtx wheel FROM PyPI inside a pypa musllinux_1_2
# image. Invoked by .github/workflows/pypi-smoke.yml via `docker run` on a GLIBC
# host (NOT a job-level container): GitHub Actions cannot run Node actions
# (actions/checkout, setup-uv) inside an Alpine ARM64 container ("JavaScript
# Actions in Alpine containers are only supported on x64 Linux runners"). So
# checkout runs on the host and this from-PyPI smoke runs in the musl image
# against the host-mounted tests/. From-PyPI sibling of musllinux_build_test.sh
# (which tests the LOCALLY built wheel); mirrors the manylinux container smoke.
#
# Expects: CWD = repo root (mounted at /io, has tests/); SPEC env = the pip spec
# (e.g. "arbez-dmtx==0.0.2", or "arbez-dmtx" for latest). Installs --only-binary
# so a missing musl wheel fails loudly instead of silently source-building.
set -e
: "${SPEC:?SPEC env (e.g. arbez-dmtx==0.0.2) is required}"

# The musllinux_1_2 image ships most cpXY[t] interpreters under /opt/python but
# not all (e.g. cp313t is absent). Prefer /opt/python; for any version it lacks,
# provision it with uv so the matrix is complete. The single py3-none-<plat> wheel
# is identical across Pythons, so this exercises the same published wheel.
/opt/python/cp312-cp312/bin/pip install -q --upgrade uv
UV=/opt/python/cp312-cp312/bin/uv
for V in 3.10 3.11 3.12 3.13 3.14 3.13t 3.14t; do
  echo "::group::Python $V"
  base=$(echo "$V" | tr -d '.t')          # 3.13 -> 313 ; 3.13t -> 313  (POSIX; no bash ${//})
  case "$V" in
    *t) P="/opt/python/cp${base}-cp${base}t/bin/python" ;;   # -> cp313-cp313t
    *)  P="/opt/python/cp${base}-cp${base}/bin/python" ;;     # -> cp313-cp313
  esac
  if [ -x "$P" ]; then
    PY="$P"
    "$PY" -m pip install -q --upgrade pip
    "$PY" -m pip install --only-binary=:all: pytest pillow "$SPEC"
    "$PY" -m pip install numpy || echo "numpy unavailable on $V (ndarray test self-skips)"
  else
    echo "  /opt/python lacks $V -> provisioning via uv"
    "$UV" venv ".t$V" --python "$V" || { echo "skip $V (uv cannot provide)"; echo "::endgroup::"; continue; }
    PY=".t$V/bin/python"
    "$UV" pip install --python "$PY" --only-binary=:all: pytest pillow "$SPEC"
    "$UV" pip install --python "$PY" numpy || echo "numpy unavailable on $V (ndarray test self-skips)"
  fi
  "$PY" -c 'import sys, arbez_dmtx; print("  from-PyPI", arbez_dmtx.__version__, "libdmtx", arbez_dmtx.libdmtx_version(), "| gil", getattr(sys, "_is_gil_enabled", lambda: "n/a")()); print("  at", arbez_dmtx.__file__)'
  "$PY" -m pytest tests -q
  echo "::endgroup::"
done
