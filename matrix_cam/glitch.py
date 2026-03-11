"""Matrix-style glitch engine for ASCII frames."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, List, MutableSequence, Optional, Sequence, Tuple

from .ascii_renderer import AsciiFrame

GLITCH_TEXT_FLASHES: tuple[str, ...] = (
    "wake up",
    "signal lost",
    "glitch detected",
    "trace active",
    "ghost packet",
    "unknown process",
)

SYSTEM_OVERLAYS: tuple[str, ...] = (
    "[SYS] scanning subject",
    "[SYS] identity unresolved",
    "[SYS] signal degraded",
)

GLITCH_CHARSET: tuple[str, ...] = tuple("01|![]{}<>/\\")

MASK_OFF_FOREGROUND_SWAP_CHANCE = 0.4


def _block_pattern(width: int) -> str:
    return "█" * max(0, width)


def _repeat_pattern(text: str, width: int) -> str:
    if width <= 0:
        return ""
    repeats = (width // len(text)) + 2
    tiled = (text * repeats)[:width]
    return tiled


def _center_pattern(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) >= width:
        return text[:width]
    padding = width - len(text)
    left = padding // 2
    right = padding - left
    return (" " * left) + text + (" " * right)


CORRUPTED_LINE_PATTERNS: tuple[Callable[[int], str], ...] = (
    _block_pattern,
    lambda width: _center_pattern("--- DATA STREAM ERROR ---", width),
    lambda width: _repeat_pattern("01001010 00101101 01100011 ", width),
)


@dataclass(frozen=True)
class GlitchConfig:
    text_flash_chance: float = 0.005
    overlay_chance: float = 0.008
    corrupted_line_chance: float = 0.004
    charset_glitch_chance: float = 0.003


@dataclass
class ActiveGlitch:
    kind: str
    ttl: int
    payload: dict[str, Any]


class GlitchEngine:
    """Injects short-lived glitch artifacts into ASCII frames."""

    def __init__(
        self,
        config: Optional[GlitchConfig] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        self._config = config or GlitchConfig()
        self._rng = rng or random.Random()
        self._active: List[ActiveGlitch] = []
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._active.clear()

    def apply(self, frame: Optional[AsciiFrame]) -> Optional[AsciiFrame]:
        if frame is None or not self._enabled:
            if not self._enabled:
                self._active.clear()
            return frame

        if frame.height <= 0 or frame.width <= 0:
            return frame

        self._schedule_glitches(frame)

        mutable_rows: List[str] = list(frame.rows)
        mutated = False
        remaining: List[ActiveGlitch] = []
        for glitch in self._active:
            if self._apply_glitch(mutable_rows, glitch):
                mutated = True
            glitch.ttl -= 1
            if glitch.ttl > 0:
                remaining.append(glitch)
        self._active = remaining

        if not mutated:
            return frame

        return AsciiFrame(
            rows=mutable_rows,
            mask=frame.mask,
            width=frame.width,
            height=frame.height,
            foreground_ratio=frame.foreground_ratio,
        )

    def _schedule_glitches(self, frame: AsciiFrame) -> None:
        if frame.height == 0 or frame.width == 0:
            return

        if self._rng.random() < self._config.text_flash_chance:
            glitch = self._build_text_flash(frame)
            if glitch:
                self._active.append(glitch)

        if self._rng.random() < self._config.overlay_chance:
            glitch = self._build_overlay(frame)
            if glitch:
                self._active.append(glitch)

        if self._rng.random() < self._config.corrupted_line_chance:
            glitch = self._build_corrupted_line(frame)
            if glitch:
                self._active.append(glitch)

        if self._rng.random() < self._config.charset_glitch_chance:
            glitch = self._build_charset_glitch()
            if glitch:
                self._active.append(glitch)

    def _build_text_flash(self, frame: AsciiFrame) -> Optional[ActiveGlitch]:
        if frame.height == 0 or frame.width == 0:
            return None
        text = self._rng.choice(GLITCH_TEXT_FLASHES)
        target = self._select_flash_target(frame, text)
        if target is None:
            return None
        row, col = target
        return ActiveGlitch(
            kind="text",
            ttl=self._random_duration(),
            payload={"row": row, "col": col, "text": text},
        )

    def _build_overlay(self, frame: AsciiFrame) -> Optional[ActiveGlitch]:
        if frame.height == 0 or frame.width == 0:
            return None
        text = self._rng.choice(SYSTEM_OVERLAYS)
        top_rows = min(3, frame.height)
        if frame.mask is not None:
            target = self._find_span(frame.rows[:top_rows], len(text), True)
            if target is None:
                return None
            row, col = target
        else:
            row = self._rng.randint(0, top_rows - 1)
            col = self._random_column(text, frame.width)
        return ActiveGlitch(
            kind="overlay",
            ttl=self._random_duration(),
            payload={"row": row, "col": col, "text": text},
        )

    def _build_corrupted_line(self, frame: AsciiFrame) -> Optional[ActiveGlitch]:
        if frame.height == 0:
            return None
        row = self._rng.randint(0, frame.height - 1)
        pattern = self._rng.choice(CORRUPTED_LINE_PATTERNS)
        return ActiveGlitch(
            kind="line",
            ttl=1,
            payload={"row": row, "pattern": pattern},
        )

    def _build_charset_glitch(self) -> Optional[ActiveGlitch]:
        intensity = 0.35 + self._rng.random() * 0.35
        return ActiveGlitch(
            kind="charset",
            ttl=1,
            payload={"intensity": intensity},
        )

    def _apply_glitch(self, rows: MutableSequence[str], glitch: ActiveGlitch) -> bool:
        if glitch.kind in {"text", "overlay"}:
            return self._apply_text(rows, glitch.payload)
        if glitch.kind == "line":
            return self._apply_corrupted_line(rows, glitch.payload)
        if glitch.kind == "charset":
            return self._apply_charset_glitch(rows, glitch.payload)
        return False

    def _apply_text(self, rows: MutableSequence[str], payload: dict[str, Any]) -> bool:
        row_idx = payload["row"]
        if row_idx < 0 or row_idx >= len(rows):
            return False
        row_chars = list(rows[row_idx])
        width = len(row_chars)
        if width == 0:
            return False
        max_start = max(0, width - len(payload["text"]))
        col = min(max(payload["col"], 0), max_start)
        text: str = payload["text"]
        mutated = False
        for offset, char in enumerate(text):
            pos = col + offset
            if pos >= width:
                break
            if row_chars[pos] != char:
                mutated = True
            row_chars[pos] = char
        rows[row_idx] = "".join(row_chars)
        return mutated

    def _apply_corrupted_line(self, rows: MutableSequence[str], payload: dict[str, Any]) -> bool:
        row_idx = payload["row"]
        if row_idx < 0 or row_idx >= len(rows):
            return False
        width = len(rows[row_idx])
        pattern: Callable[[int], str] = payload["pattern"]
        rows[row_idx] = pattern(width)
        return True

    def _apply_charset_glitch(self, rows: MutableSequence[str], payload: dict[str, Any]) -> bool:
        intensity = payload["intensity"]
        mutated = False
        for idx, row in enumerate(rows):
            if not row:
                continue
            chars = list(row)
            for col, char in enumerate(chars):
                if char == " ":
                    continue
                if self._rng.random() < intensity:
                    replacement = self._rng.choice(GLITCH_CHARSET)
                    if replacement != char:
                        mutated = True
                    chars[col] = replacement
            rows[idx] = "".join(chars)
        return mutated

    def _random_column(self, text: str, width: int) -> int:
        text_width = len(text)
        if width <= text_width:
            return 0
        return self._rng.randint(0, width - text_width)

    def _random_duration(self) -> int:
        return self._rng.randint(8, 10)

    def _select_flash_target(self, frame: AsciiFrame, text: str) -> Optional[Tuple[int, int]]:
        if frame.height == 0 or frame.width == 0:
            return None
        if frame.mask is not None:
            return self._find_span(frame.rows, len(text), True)
        if self._rng.random() < MASK_OFF_FOREGROUND_SWAP_CHANCE:
            span = self._find_span(frame.rows, len(text), False)
            if span is not None:
                return span
        row = self._rng.randint(0, frame.height - 1)
        col = self._random_column(text, frame.width)
        return row, col

    def _find_span(
        self,
        rows: Sequence[str],
        text_length: int,
        match_spaces: bool,
        row_offset: int = 0,
    ) -> Optional[Tuple[int, int]]:
        if text_length <= 0:
            return None
        spans: List[Tuple[int, int, int]] = []
        for relative_row, row in enumerate(rows):
            col = 0
            while col < len(row):
                is_space = row[col] == " "
                if is_space != match_spaces:
                    col += 1
                    continue
                span_start = col
                while col < len(row) and (row[col] == " ") == match_spaces:
                    col += 1
                span_length = col - span_start
                if span_length >= text_length:
                    spans.append((row_offset + relative_row, span_start, span_length))
        if not spans:
            return None
        row_idx, span_start, span_length = self._rng.choice(spans)
        max_col = span_start + span_length - text_length
        col_idx = self._rng.randint(span_start, max_col)
        return row_idx, col_idx
