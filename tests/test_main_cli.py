"""CLI argument parsing tests for the curses UI entry point."""

from matrix_cam.main import _parse_args


def test_parse_args_defaults() -> None:
    args = _parse_args([])
    assert args.refresh_delay == 0.03
    assert args.source == [0]
    assert args.segment_backend == "mog2"
    assert args.no_mask is False


def test_parse_args_multiple_sources() -> None:
    args = _parse_args(["--source", "0", "2", "5"])
    assert args.source == [0, 2, 5]
