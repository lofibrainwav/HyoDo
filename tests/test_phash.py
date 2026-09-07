"""TDD for Stage 2 package 2-D image decoding + perceptual hashing.

Spec: docs/superpowers/specs/2026-09-06-hyodo-agent-os-stage2-design.md,
Package 2-D.
"""

from __future__ import annotations

import struct
import zlib

import pytest

from hyodo.phash import (
    UnsupportedImageError,
    decode_image_grayscale,
    decode_pnm_grayscale,
    phash_dct64,
    phash_distance,
)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _make_png(width: int, height: int, pixels_rgb, *, color_type: int = 2) -> bytes:
    """Build a minimal, valid 8-bit non-interlaced RGB PNG for tests."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    raw = b""
    for row in pixels_rgb:
        raw += b"\x00" + bytes(value for pixel in row for value in pixel)
    idat = zlib.compress(raw)
    return sig + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


def _checkerboard(size: int = 8):
    return [
        [(255, 255, 255) if (x + y) % 2 == 0 else (0, 0, 0) for x in range(size)]
        for y in range(size)
    ]


def test_png_roundtrip_decodes_to_grayscale(tmp_path):
    pixels = _checkerboard(4)
    data = _make_png(4, 4, pixels)
    path = tmp_path / "tiny.png"
    path.write_bytes(data)
    gray = decode_image_grayscale(path)
    assert len(gray) == 4
    assert len(gray[0]) == 4
    assert gray[0][0] == 255  # white corner
    assert gray[0][1] == 0  # black neighbor


def test_png_decode_is_deterministic(tmp_path):
    pixels = _checkerboard(8)
    data = _make_png(8, 8, pixels)
    path = tmp_path / "a.png"
    path.write_bytes(data)
    first = decode_image_grayscale(path)
    second = decode_image_grayscale(path)
    assert first == second


def test_pgm_binary_decodes_grayscale():
    header = b"P5\n4 2\n255\n"
    pixels = bytes([0, 64, 128, 255, 10, 20, 30, 40])
    gray = decode_pnm_grayscale(header + pixels)
    assert gray == [[0, 64, 128, 255], [10, 20, 30, 40]]


def test_ppm_binary_decodes_grayscale():
    header = b"P6\n2 1\n255\n"
    pixels = bytes([255, 255, 255, 0, 0, 0])
    gray = decode_pnm_grayscale(header + pixels)
    assert gray[0][0] == 255
    assert gray[0][1] == 0


def test_unsupported_format_raises():
    with pytest.raises(UnsupportedImageError):
        decode_pnm_grayscale(b"not an image at all")


def test_unsupported_png_interlace_raises(tmp_path):
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 1)  # interlace=1
    idat = zlib.compress(b"\x00" + bytes([0, 0, 0, 0, 0, 0]) + b"\x00" + bytes([0, 0, 0, 0, 0, 0]))
    data = sig + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")
    path = tmp_path / "interlaced.png"
    path.write_bytes(data)
    with pytest.raises(UnsupportedImageError):
        decode_image_grayscale(path)


def test_unrecognized_bytes_raise(tmp_path):
    path = tmp_path / "not-an-image.bin"
    path.write_bytes(b"\x01\x02\x03\x04garbage")
    with pytest.raises(UnsupportedImageError):
        decode_image_grayscale(path)


# --- phash --------------------------------------------------------------


def _gray_from_png_bytes(data: bytes, tmp_path, name="x.png"):
    path = tmp_path / name
    path.write_bytes(data)
    return decode_image_grayscale(path)


def test_phash_is_16_lowercase_hex_chars(tmp_path):
    gray = _gray_from_png_bytes(_make_png(32, 32, _checkerboard(32)), tmp_path)
    result = phash_dct64(gray)
    assert len(result) == 16
    assert result == result.lower()
    int(result, 16)  # does not raise


def test_phash_deterministic_for_identical_bytes(tmp_path):
    data = _make_png(16, 16, _checkerboard(16))
    gray1 = _gray_from_png_bytes(data, tmp_path, "a.png")
    gray2 = _gray_from_png_bytes(data, tmp_path, "b.png")
    assert phash_dct64(gray1) == phash_dct64(gray2)


def test_phash_distance_zero_for_identical_hash(tmp_path):
    gray = _gray_from_png_bytes(_make_png(16, 16, _checkerboard(16)), tmp_path, "z.png")
    h = phash_dct64(gray)
    assert phash_distance(h, h) == 0


def test_phash_distance_symmetric(tmp_path):
    checker = _gray_from_png_bytes(_make_png(16, 16, _checkerboard(16)), tmp_path, "c.png")
    solid = _gray_from_png_bytes(
        _make_png(16, 16, [[(10, 10, 10)] * 16 for _ in range(16)]), tmp_path, "s.png"
    )
    a = phash_dct64(checker)
    b = phash_dct64(solid)
    assert phash_distance(a, b) == phash_distance(b, a)


def test_phash_distance_within_64_bits():
    a = "0" * 16
    b = "f" * 16
    assert phash_distance(a, b) == 64


def test_different_images_tend_to_differ(tmp_path):
    checker = _gray_from_png_bytes(_make_png(32, 32, _checkerboard(32)), tmp_path, "c2.png")
    solid = _gray_from_png_bytes(
        _make_png(32, 32, [[(200, 30, 30)] * 32 for _ in range(32)]), tmp_path, "s2.png"
    )
    a = phash_dct64(checker)
    b = phash_dct64(solid)
    assert a != b
