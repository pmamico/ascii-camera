"""Curses-based full screen UI for the ASCII camera."""

from __future__ import annotations

import curses
import time
from dataclasses import dataclass
from typing import Any, Optional

from .ascii_renderer import frame_to_ascii
from .camera import CameraError, CameraStream

STATUS_BAR_HEIGHT = 1
MIN_WIDTH = 40
MIN_HEIGHT = 12


@dataclass
class UIOptions:
    refresh_delay: float = 0.03  # Seconds between frames (~33 fps)


def run_ui(stdscr: Any, options: Optional[UIOptions] = None) -> None:
    opts = options or UIOptions()
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    green_attr = _init_green_pair()

    message: Optional[str] = None
    ascii_rows: Optional[list[str]] = None

    with CameraStream() as camera:
        while True:
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                break

            height, width = stdscr.getmaxyx()
            usable_height = height - STATUS_BAR_HEIGHT

            if width < MIN_WIDTH or usable_height < MIN_HEIGHT:
                _draw_too_small(stdscr, width, height)
                stdscr.refresh()
                time.sleep(opts.refresh_delay)
                continue

            try:
                frame = camera.read_frame()
                ascii_rows = frame_to_ascii(frame, width, usable_height)
                message = None
            except CameraError as err:
                message = str(err)
                ascii_rows = None

            stdscr.erase()
            _render_ascii(stdscr, ascii_rows, width, green_attr)
            _draw_status_bar(stdscr, width, height, message)
            stdscr.refresh()
            time.sleep(opts.refresh_delay)


def _render_ascii(
    stdscr: Any,
    ascii_rows: Optional[list[str]],
    width: int,
    attr: int,
) -> None:
    if not ascii_rows:
        return

    for row_idx, row in enumerate(ascii_rows):
        if row_idx >= stdscr.getmaxyx()[0] - STATUS_BAR_HEIGHT:
            break
        try:
            stdscr.addstr(row_idx, 0, row[:width], attr)
        except curses.error:
            continue


def _draw_status_bar(
    stdscr: Any, width: int, height: int, message: Optional[str]
) -> None:
    status_text = message or "Press q to quit"
    info = f" | {width}x{height}"
    full_status = (status_text + info)[: max(0, width - 1)]
    status_line = full_status.ljust(width - 1)
    try:
        stdscr.addstr(height - 1, 0, status_line, curses.A_REVERSE)
    except curses.error:
        pass


def _draw_too_small(stdscr: Any, width: int, height: int) -> None:
    stdscr.erase()
    msg = "Increase terminal size to display ASCII camera"
    y = max(0, height // 2)
    x = max(0, (width - len(msg)) // 2)
    try:
        stdscr.addstr(y, x, msg)
    except curses.error:
        pass
    _draw_status_bar(stdscr, width, height, "Window too small")


def _init_green_pair() -> int:
    if not curses.has_colors():
        return curses.A_NORMAL

    curses.start_color()
    try:
        curses.use_default_colors()
        background = -1
    except curses.error:
        background = curses.COLOR_BLACK

    try:
        curses.init_pair(1, curses.COLOR_GREEN, background)
        return curses.color_pair(1) | curses.A_BOLD
    except curses.error:
        return curses.A_NORMAL
