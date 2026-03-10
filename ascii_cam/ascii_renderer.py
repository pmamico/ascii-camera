"""Utilities for turning camera frames into Matrix-style ASCII art."""

from __future__ import annotations

from typing import Iterable, List, Sequence

import cv2
import numpy as np

ASCII_CHARS: Sequence[str] = tuple(chr(code) for code in range(32, 127))
CHAR_ASPECT_RATIO = 0.45  # Character cells are taller than they are wide.


def frame_to_ascii(
    bgr_frame: np.ndarray,
    max_width: int,
    max_height: int,
    charset: Sequence[str] = ASCII_CHARS,
) -> List[str]:
    if bgr_frame.ndim != 3 or bgr_frame.shape[2] != 3:
        raise ValueError("Input frame must be a BGR image")
    if max_width <= 0 or max_height <= 0:
        raise ValueError("max_width and max_height must be positive")

    frame_height, frame_width = bgr_frame.shape[:2]
    target_width = max(1, min(max_width, frame_width))
    adjusted_height = int(max_height * CHAR_ASPECT_RATIO)
    target_height = max(1, min(adjusted_height, frame_height))

    interpolation = _choose_interpolation(bgr_frame, target_width, target_height)

    gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    gray_resized = cv2.resize(
        gray_frame,
        (target_width, target_height),
        interpolation=interpolation,
    )

    normalized = gray_resized.astype(np.float32) / 255.0
    scaled = np.clip((normalized * (len(charset) - 1)).astype(np.int32), 0, len(charset) - 1)
    charset_array = np.array(charset, dtype="<U1")
    ascii_rows = ["".join(charset_array[row].tolist()) for row in scaled]
    padded_rows = [row.ljust(max_width)[:max_width] for row in ascii_rows]
    return padded_rows


def ascii_preview(rows: Iterable[str], colored: bool = True) -> str:
    text = "\n".join(rows)
    if colored:
        return f"\033[32m{text}\033[0m"
    return text


def _choose_interpolation(frame: np.ndarray, target_width: int, target_height: int) -> int:
    shrinking = target_width < frame.shape[1] or target_height < frame.shape[0]
    very_small_target = target_width <= 2 or target_height <= 2

    if shrinking and not very_small_target:
        return cv2.INTER_AREA
    return cv2.INTER_NEAREST
