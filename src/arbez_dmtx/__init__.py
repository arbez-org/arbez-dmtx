"""arbez-dmtx — self-contained DataMatrix encode/decode (vendored libdmtx).

A modern, self-contained successor to ``pylibdmtx``: a distutils-free ctypes
binding to libdmtx (BSD-2) with the native shared library **bundled in the
platform wheel on every OS** — no ``brew install libdmtx`` / ``apt-get install
libdmtx0a`` required (the gap pylibdmtx left off Windows). Pure ctypes, so it is
free-threading (3.13t/3.14t) safe: importing it does NOT re-enable the GIL, and
``CDLL`` releases the GIL around each decode.

Full pylibdmtx-compatible public API:

    from arbez_dmtx import decode, encode, Decoded, Rect, Encoded
    from PIL import Image

    encoded = encode(b"hello")
    img = Image.frombytes("RGB", (encoded.width, encoded.height), encoded.pixels)
    decode(img)            # -> [Decoded(data=b'hello', rect=Rect(...))]

``decode`` accepts ``PIL.Image``, ``numpy.ndarray`` (e.g. from OpenCV), or a
``(pixels, width, height)`` tuple, and the full set of libdmtx tuning params
(``timeout``, ``gap_size``, ``shrink``, ``shape``, ``deviation``, ``threshold``,
``min_edge``, ``max_edge``, ``corrections``, ``max_count``). ``encode`` takes
``scheme`` / ``size`` from ``ENCODING_SCHEME_NAMES`` / ``ENCODING_SIZE_NAMES``.
"""
from ._libdmtx.pylibdmtx import (  # noqa: F401
    ENCODING_SCHEME_NAMES,
    ENCODING_SIZE_NAMES,
    Decoded,
    Encoded,
    Rect,
    decode,
    encode,
)
from ._libdmtx.pylibdmtx_error import PyLibDMTXError  # noqa: F401
from ._libdmtx.wrapper import dmtxVersion  # noqa: F401

__all__ = [
    # core API
    "decode",
    "encode",
    # result / value types
    "Decoded",
    "Rect",
    "Encoded",
    # encode option vocabularies
    "ENCODING_SCHEME_NAMES",
    "ENCODING_SIZE_NAMES",
    # errors
    "PyLibDMTXError",
    # bundled-library introspection
    "dmtxVersion",
    "libdmtx_version",
    "__version__",
]
__version__ = "0.0.2"


def libdmtx_version():
    """Version string of the bundled/loaded libdmtx C library (e.g. ``'0.7.8'``)."""
    return dmtxVersion()
