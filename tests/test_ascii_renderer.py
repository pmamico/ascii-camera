"""Unit tests for ASCII conversion helpers."""

import numpy as np

from ascii_cam.ascii_renderer import ASCII_CHARS, frame_to_ascii


def test_frame_to_ascii_maps_dark_and_light_pixels_bgr() -> None:
    frame = np.array(
        [
            [[0, 0, 0], [255, 255, 255]],
            [[128, 128, 128], [64, 64, 64]],
        ],
        dtype=np.uint8,
    )

    rows = frame_to_ascii(frame, max_width=2, max_height=10)

    assert len(rows) == 2
    assert rows[0][0] == ASCII_CHARS[0]
    assert rows[0][1] == ASCII_CHARS[-1]


def test_frame_to_ascii_rejects_non_bgr_input() -> None:
    frame = np.zeros((2, 2), dtype=np.uint8)

    try:
        frame_to_ascii(frame, max_width=2, max_height=2)
        raised = False
    except ValueError:
        raised = True

    assert raised
