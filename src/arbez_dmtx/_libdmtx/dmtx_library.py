"""arbez-dmtx libdmtx loader: prefer the libdmtx bundled in this package
(platform wheel), fall back to a system install. Pure ctypes -> free-threading
safe (no compiled extension, never re-enables the GIL)."""
import ctypes
import ctypes.util
import os
import sys

_NAMES = {
    "darwin": ["libdmtx.dylib", "libdmtx.0.dylib"],
    "linux": ["libdmtx.so", "libdmtx.so.0", "libdmtx.so.1"],
    "win32": ["libdmtx.dll", "dmtx.dll"],
}


def _plat():
    if sys.platform == "darwin":
        return "darwin"
    if os.name == "nt":
        return "win32"
    return "linux"


def load():
    here = os.path.dirname(os.path.abspath(__file__))
    names = _NAMES[_plat()]
    # 1) bundled next to this module (the platform wheel ships it here)
    for n in names:
        p = os.path.join(here, n)
        if os.path.exists(p):
            return ctypes.CDLL(p)
    # 2) system install (find_library honors DYLD/LD paths and resolves to an
    # absolute path). No bare-name CDLL fallback: loading a bare filename can
    # pick up an attacker-planted library from the process search path (e.g. the
    # CWD), and the official platform wheel always satisfies (1).
    found = ctypes.util.find_library("dmtx")
    if found:
        return ctypes.CDLL(found)
    raise ImportError(
        "arbez-dmtx: libdmtx shared library not found (no bundled copy and no "
        "system install). Use the arbez-dmtx platform wheel, or install libdmtx."
    )
