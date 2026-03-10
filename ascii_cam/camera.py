"""Camera access helpers using OpenCV."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional
import time

import cv2
import numpy as np


class CameraError(RuntimeError):
    """Raised when the camera cannot be accessed or read."""


@dataclass
class CameraConfig:
    index: int = 0
    width: Optional[int] = 640
    height: Optional[int] = 480
    fps: Optional[int] = 30
    warmup_frames: int = 10
    warmup_delay: float = 0.05


class CameraStream(AbstractContextManager["CameraStream"]):
    """Thin wrapper around ``cv2.VideoCapture`` returning BGR frames."""

    def __init__(self, config: Optional[CameraConfig] = None) -> None:
        self.config = config or CameraConfig()
        self._capture: Optional[cv2.VideoCapture] = None

    def __enter__(self) -> "CameraStream":
        self.open()
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:  # type: ignore[override]
        self.close()

    def open(self) -> None:
        capture = cv2.VideoCapture(self.config.index)

        if not capture.isOpened():
            raise CameraError("Unable to open camera. Ensure permissions are granted.")

        if self.config.width:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        if self.config.height:
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        if self.config.fps:
            capture.set(cv2.CAP_PROP_FPS, self.config.fps)

        self._capture = capture
        self._warm_up()

    def close(self) -> None:
        if self._capture:
            self._capture.release()
            self._capture = None

    def read_frame(self) -> np.ndarray:
        if not self._capture:
            raise CameraError("Camera is not opened. Call open() first.")

        success, frame = self._capture.read()
        if not success or frame is None:
            raise CameraError("Failed to read frame from camera.")

        return frame

    def _warm_up(self) -> None:
        if not self._capture or self.config.warmup_frames <= 0:
            return

        for _ in range(self.config.warmup_frames):
            success, _frame = self._capture.read()
            if not success:
                break
            if self.config.warmup_delay > 0:
                time.sleep(self.config.warmup_delay)
