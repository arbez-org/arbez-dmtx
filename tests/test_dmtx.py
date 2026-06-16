"""arbez-dmtx test suite.

Covers the full public API (decode/encode + all result types and vocabularies),
input types (PIL / ndarray / raw tuple), error paths, the scheme/size contracts,
the bundled-library loader, version pinning, free-threading GIL state and
thread-safety, plus a zxing-cpp cross-check.
"""
import concurrent.futures as cf
import re
import sys
import sysconfig
from pathlib import Path

import pytest
from PIL import Image

import arbez_dmtx


def _dm_image(payload: bytes, **kw) -> Image.Image:
    e = arbez_dmtx.encode(payload, **kw)
    return Image.frombytes("RGB", (e.width, e.height), e.pixels)


def _two_code_canvas() -> Image.Image:
    a, b = _dm_image(b"CODE-A"), _dm_image(b"CODE-B")
    w = a.width + b.width + 60
    h = max(a.height, b.height) + 40
    canvas = Image.new("RGB", (w, h), "white")
    canvas.paste(a, (20, 20))
    canvas.paste(b, (a.width + 40, 20))
    return canvas


# ── version / bundled library ────────────────────────────────────────────

def test_version_shape_and_consistency():
    v = arbez_dmtx.libdmtx_version()
    assert v == arbez_dmtx.dmtxVersion()
    assert re.match(r"^\d+\.\d+\.\d+", v), v


def test_bundled_version_matches_pin():
    """The bundled libdmtx must be the version pinned in the repo (guards a
    stale vendored lib slipping into the wheel). Skips if run outside the repo."""
    pin = Path(__file__).resolve().parent.parent / "LIBDMTX_VERSION"
    if not pin.is_file():
        pytest.skip("LIBDMTX_VERSION not present (installed-package run)")
    assert arbez_dmtx.libdmtx_version() == pin.read_text().strip()


def test_loader_uses_bundled_library():
    """The loaded libdmtx must come from inside the package (the wheel-bundled
    copy won, not a system install)."""
    from arbez_dmtx._libdmtx import dmtx_library, wrapper
    assert dmtx_library._plat() in {"darwin", "linux", "win32"}
    lib = getattr(wrapper, "LIBDMTX", None)
    name = getattr(lib, "_name", "") or ""
    if name:  # CDLL._name is the resolved path on the supported platforms
        assert "arbez_dmtx" in name, name


# ── decode ───────────────────────────────────────────────────────────────

def test_roundtrip():
    assert arbez_dmtx.decode(_dm_image(b"ROUNDTRIP"))[0].data == b"ROUNDTRIP"


def test_decoded_and_rect_types():
    (d,) = arbez_dmtx.decode(_dm_image(b"TYPES-OK"), max_count=1)
    assert isinstance(d, arbez_dmtx.Decoded) and d.data == b"TYPES-OK"
    assert isinstance(d.rect, arbez_dmtx.Rect)
    assert d.rect.left >= 0 and d.rect.width > 0 and d.rect.height > 0


def test_decode_blank_image_returns_empty_list():
    out = arbez_dmtx.decode(Image.new("RGB", (64, 64), "white"))
    assert out == [] and isinstance(out, list)


def test_decode_accepts_ndarray_and_bytes_tuple():
    np = pytest.importorskip("numpy")
    arr = np.asarray(_dm_image(b"NDARRAY-OK").convert("RGB"))
    assert arbez_dmtx.decode(arr)[0].data == b"NDARRAY-OK"
    h, w = arr.shape[:2]
    assert arbez_dmtx.decode((arr.tobytes(), w, h))[0].data == b"NDARRAY-OK"


def test_decode_grayscale_and_rgba_inputs():
    """The 8bpp (L) and 32bpp (RGBA) pixel paths decode, not only 24bpp RGB."""
    img = _dm_image(b"BPP")
    assert arbez_dmtx.decode(img.convert("L"))[0].data == b"BPP"
    assert arbez_dmtx.decode(img.convert("RGBA"))[0].data == b"BPP"


def test_decode_tuple_inconsistent_dimensions_raises():
    with pytest.raises(arbez_dmtx.PyLibDMTXError):
        arbez_dmtx.decode((b"\x00" * 10, 100, 100))  # 10 bytes != 100*100*bpp


def test_decode_multiple_codes_and_max_count():
    canvas = _two_code_canvas()
    assert len(arbez_dmtx.decode(canvas)) == 2
    assert len(arbez_dmtx.decode(canvas, max_count=1)) == 1


def test_decode_passthrough_tuning_params_smoke():
    """A real code still decodes with non-default tuning params set — guards the
    dmtxDecodeSetProp mapping against an enum/arg regression."""
    img = _dm_image(b"TUNE")
    out = arbez_dmtx.decode(img, timeout=5000, corrections=3, gap_size=0)
    assert out and out[0].data == b"TUNE"


def test_decode_shrink_still_decodes():
    img = _dm_image(b"SHRINKABLE-PAYLOAD")
    # upscale so shrink=2 still leaves a decodable symbol
    big = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    assert arbez_dmtx.decode(big, shrink=1)[0].data == b"SHRINKABLE-PAYLOAD"
    assert arbez_dmtx.decode(big, shrink=2)[0].data == b"SHRINKABLE-PAYLOAD"


# ── encode ───────────────────────────────────────────────────────────────

def test_encode_returns_encoded():
    enc = arbez_dmtx.encode(b"E")
    assert isinstance(enc, arbez_dmtx.Encoded)
    assert enc.width > 0 and enc.height > 0
    assert len(enc.pixels) == enc.width * enc.height * enc.bpp // 8


def test_encode_accepts_every_advertised_scheme():
    """Regression guard for the old ``scheme.capitalize()`` bug: no name in
    ENCODING_SCHEME_NAMES may be rejected as an *invalid* scheme (whether
    libdmtx can encode a given payload with it is a separate matter)."""
    for s in arbez_dmtx.ENCODING_SCHEME_NAMES:
        try:
            arbez_dmtx.encode(b"HELLO123", scheme=s)
        except arbez_dmtx.PyLibDMTXError as e:
            assert "Invalid scheme" not in str(e), f"{s} wrongly rejected: {e}"


def test_encode_scheme_case_insensitive():
    assert (arbez_dmtx.encode(b"AB", scheme="ascii").pixels
            == arbez_dmtx.encode(b"AB", scheme="Ascii").pixels
            == arbez_dmtx.encode(b"AB", scheme="ASCII").pixels)


@pytest.mark.parametrize("size", ["10x10", "36x36", "144x144", "16x48", "RectAuto"])
def test_encode_size_roundtrips(size):
    enc = arbez_dmtx.encode(b"SZ", size=size)
    assert len(enc.pixels) == enc.width * enc.height * enc.bpp // 8
    img = Image.frombytes("RGB", (enc.width, enc.height), enc.pixels)
    assert arbez_dmtx.decode(img)[0].data == b"SZ"


def test_encode_rectangular_size_is_non_square():
    enc = arbez_dmtx.encode(b"R", size="16x48")
    assert enc.width != enc.height  # guards a w/h transposition


def test_encode_too_large_data_raises():
    with pytest.raises(arbez_dmtx.PyLibDMTXError):
        arbez_dmtx.encode(b"X" * 2000, size="10x10")


def test_encode_invalid_scheme_raises():
    with pytest.raises(arbez_dmtx.PyLibDMTXError, match="should be one of"):
        arbez_dmtx.encode(b"AB", scheme="NotAScheme")


def test_encode_invalid_size_raises():
    with pytest.raises(arbez_dmtx.PyLibDMTXError, match="should be one of"):
        arbez_dmtx.encode(b"AB", size="99x99")


def test_encode_non_utf8_bytes_roundtrip():
    """Arbitrary binary round-trips via the Base256 scheme (the binary-safe one;
    the default Ascii scheme is text-oriented)."""
    payload = b"\xff\xfe\x00binary"
    enc = arbez_dmtx.encode(payload, scheme="Base256")
    img = Image.frombytes("RGB", (enc.width, enc.height), enc.pixels)
    assert arbez_dmtx.decode(img)[0].data == payload


# ── public API surface ───────────────────────────────────────────────────

def test_public_api_surface():
    for name in ("decode", "encode", "Decoded", "Rect", "Encoded",
                 "ENCODING_SCHEME_NAMES", "ENCODING_SIZE_NAMES",
                 "PyLibDMTXError", "libdmtx_version", "dmtxVersion",
                 "__version__"):
        assert hasattr(arbez_dmtx, name), name
    assert issubclass(arbez_dmtx.PyLibDMTXError, Exception)
    assert arbez_dmtx.ENCODING_SCHEME_NAMES and arbez_dmtx.ENCODING_SIZE_NAMES
    assert re.match(r"^\d+\.\d+\.\d+", arbez_dmtx.__version__)


def test_encode_rejects_str():
    """encode() requires bytes — a str must raise, not silently corrupt."""
    with pytest.raises(TypeError):
        arbez_dmtx.encode("not bytes")


def test_decode_max_count_below_one_raises():
    with pytest.raises(ValueError):
        arbez_dmtx.decode(_dm_image(b"X"), max_count=0)


def test_decode_zero_and_negative_dimensions_raise():
    with pytest.raises(arbez_dmtx.PyLibDMTXError):
        arbez_dmtx.decode((b"\x00" * 12, 0, 4))
    with pytest.raises(arbez_dmtx.PyLibDMTXError):
        arbez_dmtx.decode((b"\x00" * 12, -2, 4))


def test_decode_timeout_zero_and_corrections_zero_are_passed_through():
    """timeout=0 and corrections=0 are real values (not 'unset') and must not
    raise — they exercise the falsy-vs-None param handling."""
    img = _dm_image(b"ZERO")
    assert isinstance(arbez_dmtx.decode(img, timeout=0), list)
    assert isinstance(arbez_dmtx.decode(img, corrections=0), list)


# ── free-threading / concurrency ─────────────────────────────────────────

@pytest.mark.skipif(not sysconfig.get_config_var("Py_GIL_DISABLED"),
                    reason="not a free-threaded build")
def test_import_does_not_reenable_gil():
    """On a free-threaded (3.13t/3.14t) build, importing the pure-ctypes
    arbez_dmtx must NOT have re-enabled the GIL."""
    assert sys._is_gil_enabled() is False


def test_concurrent_decode_threadsafe():
    img = _dm_image(b"CONC-9999")

    def w(_):
        o = arbez_dmtx.decode(img)
        return bytes(o[0].data) if o else b""

    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        outs = list(ex.map(w, range(96)))
    assert all(x == b"CONC-9999" for x in outs)


def test_both_decoders_agree():
    """IF zxing-cpp is installed and reads the synthetic DataMatrix, its payload
    must match libdmtx's (consistency cross-check)."""
    payload = b"BOTH-DECODERS-OK"
    img = _dm_image(payload)
    assert arbez_dmtx.decode(img)[0].data == payload
    try:
        import zxingcpp
    except Exception:
        return
    np = pytest.importorskip("numpy")
    zx = [r for r in zxingcpp.read_barcodes(np.asarray(img))
          if r.valid and "datamatrix" in str(r.format).lower()]
    if zx:
        assert zx[0].text.encode() == payload
