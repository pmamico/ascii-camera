"""Application entry point for the curses-based ASCII camera."""

from __future__ import annotations

import curses

from .ui import run_ui


def run() -> None:
    curses.wrapper(run_ui)


if __name__ == "__main__":
    run()
