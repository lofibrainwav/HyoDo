"""Pure-stdlib image decoding and perceptual hashing for ``hyodo eye``.

No new runtime dependency: PNG decoding uses only :mod:`zlib` (stdlib) and a
hand-rolled filter reconstruction; PGM/PPM decoding is a plain binary
reader. Everything here operates on already-read bytes or an already-open
path — it never talks to the network and it never reaches the ledger with
pixel data, only the 16-hex-character hash this module returns.

Supported formats:

- PNG, 8-bit depth, non-interlaced, colour types 0 (greyscale), 2 (RGB),
  4 (greyscale + alpha), 6 (RGBA).
- Binary PGM (``P5``) and PPM (``P6``), maxval 255.

Anything else raises :class:`UnsupportedImageError`, which callers map to
the ``eye_image_unsupported`` outcome.
"""

from __future__ import annotations

import math
import zlib
from pathlib import Path

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_CHANNELS_BY_COLOR_TYPE = {0: 1, 2: 3, 4: 2, 6: 4}


class UnsupportedImageError(ValueError):
    """Raised when image bytes are not a supported PNG or binary PGM/PPM."""


def _paeth_predictor(a: int, b: int, c: int) -> int:
    """PNG Paeth filter predictor (see the PNG spec, section 9.4)."""
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter_scanline(line: bytearray, prev: bytes, filter_type: int, bpp: int) -> None:
    """Reverse one PNG scanline filter in place (spec section 9.2-9.4)."""
    length = len(line)
    if filter_type == 0:  # None
        return
    if filter_type == 1:  # Sub
        for i in range(bpp, length):
            line[i] = (line[i] + line[i - bpp]) & 0xFF
    elif filter_type == 2:  # Up
        for i in range(length):
            line[i] = (line[i] + prev[i]) & 0xFF
    elif filter_type == 3:  # Average
        for i in range(length):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            line[i] = (line[i] + ((a + b) // 2)) & 0xFF
    elif filter_type == 4:  # Paeth
        for i in range(length):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + _paeth_predictor(a, b, c)) & 0xFF
    else:
        raise UnsupportedImageError(f"unknown PNG filter type {filter_type}")


def _iter_png_chunks(data: bytes):
    pos = 8
    while pos + 8 <= len(data):
        length = int.from_bytes(data[pos : pos + 4], "big")
        pos += 4
        chunk_type = data[pos : pos + 4]
        pos += 4
        chunk_data = data[pos : pos + length]
        pos += length + 4  # skip CRC
        yield chunk_type, chunk_data
        if chunk_type == b"IEND":
            return


def _rgb_to_gray(r: int, g: int, b: int) -> int:
    """ITU-R BT.601 luma weights, rounded to the nearest 8-bit level."""
    return round(0.299 * r + 0.587 * g + 0.114 * b)


def decode_png_grayscale(data: bytes) -> list[list[int]]:
    """Decode PNG *data* to a row-major greyscale pixel grid.

    Only 8-bit, non-interlaced PNGs with colour type 0/2/4/6 are supported.
    Alpha is ignored (composited over nothing — this reads the colour
    channels only); that is a deliberate simplification documented here,
    not a bug: ``hyodo eye`` only needs a perceptual hash, not a faithful
    render.
    """
    if data[:8] != _PNG_SIGNATURE:
        raise UnsupportedImageError("not a PNG file")
    ihdr: bytes | None = None
    idat = bytearray()
    for chunk_type, chunk_data in _iter_png_chunks(data):
        if chunk_type == b"IHDR":
            ihdr = chunk_data
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
    if ihdr is None or len(ihdr) < 13:
        raise UnsupportedImageError("PNG missing IHDR")
    width = int.from_bytes(ihdr[0:4], "big")
    height = int.from_bytes(ihdr[4:8], "big")
    bit_depth = ihdr[8]
    color_type = ihdr[9]
    interlace = ihdr[12]
    if width <= 0 or height <= 0:
        raise UnsupportedImageError("PNG has zero-sized dimensions")
    if bit_depth != 8 or interlace != 0 or color_type not in _PNG_CHANNELS_BY_COLOR_TYPE:
        raise UnsupportedImageError(
            f"unsupported PNG shape: bit_depth={bit_depth} color_type={color_type} "
            f"interlace={interlace}"
        )
    channels = _PNG_CHANNELS_BY_COLOR_TYPE[color_type]
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise UnsupportedImageError(f"PNG IDAT did not inflate: {exc}") from exc

    stride = width * channels
    prev = bytes(stride)
    pos = 0
    gray: list[list[int]] = []
    for _row in range(height):
        if pos >= len(raw):
            raise UnsupportedImageError("PNG pixel data truncated")
        filter_type = raw[pos]
        pos += 1
        line = bytearray(raw[pos : pos + stride])
        if len(line) != stride:
            raise UnsupportedImageError("PNG scanline truncated")
        pos += stride
        _unfilter_scanline(line, prev, filter_type, channels)
        row_out: list[int] = []
        for i in range(width):
            off = i * channels
            if channels == 1:
                row_out.append(line[off])
            elif channels == 2:
                row_out.append(line[off])  # grey channel; alpha ignored
            else:  # 3 (RGB) or 4 (RGBA)
                row_out.append(_rgb_to_gray(line[off], line[off + 1], line[off + 2]))
        gray.append(row_out)
        prev = bytes(line)
    return gray


def _skip_pnm_whitespace_and_comments(data: bytes, pos: int) -> int:
    while pos < len(data):
        ch = data[pos : pos + 1]
        if ch in b" \t\r\n":
            pos += 1
            continue
        if ch == b"#":
            while pos < len(data) and data[pos : pos + 1] != b"\n":
                pos += 1
            continue
        break
    return pos


def decode_pnm_grayscale(data: bytes) -> list[list[int]]:
    """Decode binary PGM (``P5``) or PPM (``P6``) *data*, maxval 255 only."""
    magic = data[:2]
    if magic not in (b"P5", b"P6"):
        raise UnsupportedImageError("not a binary PGM/PPM file")
    pos = 2
    values: list[int] = []
    for _ in range(3):
        pos = _skip_pnm_whitespace_and_comments(data, pos)
        start = pos
        while pos < len(data) and data[pos : pos + 1] not in b" \t\r\n":
            pos += 1
        token = data[start:pos]
        if not token.isdigit():
            raise UnsupportedImageError("malformed PGM/PPM header")
        values.append(int(token))
    pos += 1  # exactly one whitespace byte separates maxval from pixel data
    width, height, maxval = values
    if maxval != 255 or width <= 0 or height <= 0:
        raise UnsupportedImageError("unsupported PGM/PPM maxval or dimensions")
    channels = 1 if magic == b"P5" else 3
    expected = width * height * channels
    pixels = data[pos : pos + expected]
    if len(pixels) != expected:
        raise UnsupportedImageError("PGM/PPM pixel data truncated")
    gray: list[list[int]] = []
    idx = 0
    for _y in range(height):
        row: list[int] = []
        for _x in range(width):
            if channels == 1:
                row.append(pixels[idx])
                idx += 1
            else:
                row.append(_rgb_to_gray(pixels[idx], pixels[idx + 1], pixels[idx + 2]))
                idx += 3
        gray.append(row)
    return gray


def decode_image_grayscale(path: Path) -> list[list[int]]:
    """Read the image at *path* and return a row-major greyscale pixel grid.

    Dispatches on magic bytes; raises :class:`UnsupportedImageError` for any
    format other than the supported PNG/PGM/PPM subset (including a
    corrupted file of a supported format).
    """
    data = path.read_bytes()
    if data[:8] == _PNG_SIGNATURE:
        return decode_png_grayscale(data)
    if data[:2] in (b"P5", b"P6"):
        return decode_pnm_grayscale(data)
    raise UnsupportedImageError("unrecognized image format")


def _resize_area_average(gray: list[list[int]], out_h: int, out_w: int) -> list[list[float]]:
    """Downsample *gray* to ``out_h`` x ``out_w`` by averaging each source block.

    A simple, deterministic box filter: each output cell averages the
    (possibly ragged) rectangle of source pixels it maps to, unweighted by
    partial pixel coverage. That is a documented approximation of "area
    averaging", not a filtered resampler — good enough for a perceptual
    hash, which only needs coarse low-frequency structure.
    """
    height = len(gray)
    width = len(gray[0]) if height else 0
    if height == 0 or width == 0:
        raise UnsupportedImageError("image has no pixels to resize")
    result: list[list[float]] = [[0.0] * out_w for _ in range(out_h)]
    for oy in range(out_h):
        y0 = oy * height // out_h
        y1 = max(y0 + 1, (oy + 1) * height // out_h)
        for ox in range(out_w):
            x0 = ox * width // out_w
            x1 = max(x0 + 1, (ox + 1) * width // out_w)
            total = 0
            count = 0
            for y in range(y0, y1):
                row = gray[y]
                for x in range(x0, x1):
                    total += row[x]
                    count += 1
            result[oy][ox] = total / count
    return result


def _dct_1d(vec: list[float]) -> list[float]:
    """Un-normalized 1-D DCT-II. A positive constant scale factor does not
    change which coefficients land above or below their median, which is
    all :func:`phash_dct64` needs."""
    n = len(vec)
    out = [0.0] * n
    for k in range(n):
        total = 0.0
        for i in range(n):
            total += vec[i] * math.cos((math.pi / n) * (i + 0.5) * k)
        out[k] = total
    return out


def _dct_2d(matrix: list[list[float]]) -> list[list[float]]:
    """Separable 2-D DCT-II: 1-D DCT over rows, then over the resulting columns."""
    rows_transformed = [_dct_1d(row) for row in matrix]
    n = len(rows_transformed)
    width = len(rows_transformed[0]) if rows_transformed else 0
    out = [[0.0] * width for _ in range(n)]
    for col in range(width):
        column = [rows_transformed[row][col] for row in range(n)]
        transformed_column = _dct_1d(column)
        for row in range(n):
            out[row][col] = transformed_column[row]
    return out


def phash_dct64(gray: list[list[int]]) -> str:
    """Compute a 64-bit DCT-based perceptual hash, returned as 16 lowercase hex chars.

    Algorithm (``phash_algo = "dct64"``):

    1. Downsample *gray* to 32x32 by area-averaging (:func:`_resize_area_average`).
    2. Run a separable 2-D DCT-II over the 32x32 grid.
    3. Take the top-left 8x8 block of coefficients (low frequencies),
       **including** the DC term at ``[0][0]``.
    4. Compute the median of all 64 coefficients in that block.
    5. Set bit ``i`` (row-major over the 8x8 block) when coefficient ``i``
       is strictly greater than the median; clear it otherwise.
    6. Pack the 64 bits, most-significant first, into 16 hex characters.

    This implementation deliberately includes the DC coefficient in the
    median computation (unlike some ``pHash`` implementations, which
    exclude it before thresholding). That is one documented, fixed choice
    — not a tunable — so two callers computing this hash from identical
    bytes always agree. Determinism follows directly from steps 1-6 being
    pure arithmetic over the input pixels: no randomness, no floating-point
    resampling as a JPEG/PNG library would decide it, no system state.
    """
    resized = _resize_area_average(gray, 32, 32)
    dct = _dct_2d(resized)
    block = [row[:8] for row in dct[:8]]
    flat = [value for row in block for value in row]
    ordered = sorted(flat)
    median = (ordered[31] + ordered[32]) / 2
    bits = "".join("1" if value > median else "0" for value in flat)
    return f"{int(bits, 2):016x}"


def phash_distance(a: str, b: str) -> int:
    """Return the Hamming distance (0-64) between two ``dct64`` hex hashes."""
    return bin(int(a, 16) ^ int(b, 16)).count("1")
