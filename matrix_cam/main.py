"""Application entry point for the curses-based ASCII camera."""

from __future__ import annotations

import argparse
import curses
from typing import Sequence

from .segmentation import ForegroundSegmenter
from .ui import UIOptions, run_ui


def run(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    options = UIOptions(
        refresh_delay=args.refresh_delay,
        start_segmentation=not args.no_mask,
        segmentation_backend=args.segment_backend,
        camera_sources=tuple(args.source),
    )
    curses.wrapper(run_ui, options)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Real-time ASCII camera viewer. "
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--refresh-delay",
        type=float,
        default=0.03,
        help="Seconds between frame renders (lower is faster, higher uses less CPU)",
    )
    parser.add_argument(
        "--no-mask",
        action="store_true",
        help="Start with the foreground mask disabled",
    )
    parser.add_argument(
        "--segment-backend",
        choices=ForegroundSegmenter.available_backends(),
        default="mog2",
        help="Select the segmentation backend",
    )
    parser.add_argument(
        "--source",
        type=int,
        nargs="+",
        metavar="INDEX",
        default=[0],
        help="Camera source to use",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    run()
