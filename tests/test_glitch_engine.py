"""Unit tests for the glitch overlay system."""

import random

import numpy as np

from matrix_cam.ascii_renderer import AsciiFrame
from matrix_cam.glitch import GlitchConfig, GlitchEngine


class StubRandom(random.Random):
    def __init__(
        self,
        random_values: list[float] | None = None,
        int_values: list[int] | None = None,
        default_random: float = 1.0,
    ) -> None:
        self._random_values = list(random_values or [])
        self._int_values = list(int_values or [])
        self._default_random = default_random

    def random(self) -> float:
        if self._random_values:
            return self._random_values.pop(0)
        return self._default_random

    def randint(self, a: int, b: int) -> int:
        if self._int_values:
            value = self._int_values.pop(0)
        else:
            value = a
        return max(a, min(value, b))

    def choice(self, seq):  # type: ignore[override]
        return seq[0]


def _frame(width: int = 24, height: int = 6) -> AsciiFrame:
    rows = ["." * width for _ in range(height)]
    return AsciiFrame(rows=rows, mask=None, width=width, height=height, foreground_ratio=0.0)


def test_glitch_engine_injects_text_flash() -> None:
    rng = StubRandom(random_values=[0.0, 1.0, 1.0, 1.0], int_values=[0, 1, 0])
    engine = GlitchEngine(
        GlitchConfig(text_flash_chance=1.0, overlay_chance=0.0, corrupted_line_chance=0.0, charset_glitch_chance=0.0),
        rng=rng,
    )
    frame = _frame()

    glitched = engine.apply(frame)
    assert glitched is not None

    assert glitched is not frame
    assert "wake up" in glitched.rows[0]


def test_glitch_engine_replaces_row_with_corruption() -> None:
    rng = StubRandom(random_values=[1.0, 1.0, 0.0, 1.0], int_values=[0])
    engine = GlitchEngine(
        GlitchConfig(text_flash_chance=0.0, overlay_chance=0.0, corrupted_line_chance=1.0, charset_glitch_chance=0.0),
        rng=rng,
    )
    frame = _frame(width=10, height=2)

    glitched = engine.apply(frame)
    assert glitched is not None

    assert set(glitched.rows[0]) == {"█"}


def test_glitch_engine_switches_charset_single_frame() -> None:
    rng = StubRandom(
        random_values=[1.0, 1.0, 1.0, 0.0, 0.0],
        default_random=0.0,
    )
    engine = GlitchEngine(
        GlitchConfig(text_flash_chance=0.0, overlay_chance=0.0, corrupted_line_chance=0.0, charset_glitch_chance=1.0),
        rng=rng,
    )
    frame = _frame(width=5, height=1)

    glitched = engine.apply(frame)
    assert glitched is not None

    assert glitched.rows[0] == "0" * 5


def test_disabling_glitch_engine_restores_clean_output() -> None:
    rng = StubRandom(random_values=[0.0, 1.0, 1.0, 1.0], int_values=[0, 1, 0])
    engine = GlitchEngine(
        GlitchConfig(text_flash_chance=1.0, overlay_chance=0.0, corrupted_line_chance=0.0, charset_glitch_chance=0.0),
        rng=rng,
    )
    frame = _frame(width=12, height=2)

    glitched = engine.apply(frame)
    assert glitched is not None
    engine.set_enabled(False)
    clean = engine.apply(frame)

    assert "wake up" in glitched.rows[0]
    assert clean is frame


def test_text_glitch_targets_blank_mask_regions() -> None:
    rng = StubRandom(random_values=[0.0, 1.0, 1.0, 1.0], int_values=[0, 8])
    engine = GlitchEngine(
        GlitchConfig(text_flash_chance=1.0, overlay_chance=0.0, corrupted_line_chance=0.0, charset_glitch_chance=0.0),
        rng=rng,
    )
    rows = ["abcdefghij", " " * 12]
    mask = np.ones((2, 12), dtype=bool)
    frame = AsciiFrame(rows=rows, mask=mask, width=12, height=2, foreground_ratio=0.0)

    glitched = engine.apply(frame)
    assert glitched is not None

    assert glitched.rows[0] == rows[0]
    assert "wake up" in glitched.rows[1]


def test_text_glitch_can_replace_foreground_when_mask_disabled() -> None:
    rng = StubRandom(random_values=[0.0, 0.0, 1.0, 1.0, 1.0], int_values=[0, 8])
    engine = GlitchEngine(
        GlitchConfig(text_flash_chance=1.0, overlay_chance=0.0, corrupted_line_chance=0.0, charset_glitch_chance=0.0),
        rng=rng,
    )
    rows = ["abcdefghij", "klmnopqrst"]
    frame = AsciiFrame(rows=rows, mask=None, width=10, height=2, foreground_ratio=0.0)

    glitched = engine.apply(frame)
    assert glitched is not None

    assert glitched.rows[0].startswith("wake up")
    assert glitched.rows[1] == rows[1]
