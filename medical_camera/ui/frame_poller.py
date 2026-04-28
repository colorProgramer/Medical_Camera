from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from medical_camera.services.actions import ActionDispatcher


class HikvisionFramePoller(QObject):
    frame_ready = Signal(object)
    stats_ready = Signal(float, int)

    def __init__(self, dispatcher: ActionDispatcher, interval_ms: int = 10, timeout_ms: int = 10) -> None:
        super().__init__()
        self._dispatcher = dispatcher
        self._interval_ms = interval_ms
        self._timeout_ms = timeout_ms
        self._timer: QTimer | None = None
        self._frame_count = 0
        self._last_stats_time = perf_counter()
        self._running = False

    @Slot()
    def start(self) -> None:
        self._running = True
        self._frame_count = 0
        self._last_stats_time = perf_counter()
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.setInterval(self._interval_ms)
            self._timer.timeout.connect(self._poll_once)
        if not self._timer.isActive():
            self._timer.start()

    @Slot()
    def stop(self) -> None:
        self._running = False
        if self._timer is not None and self._timer.isActive():
            self._timer.stop()

    @Slot()
    def _poll_once(self) -> None:
        if not self._running:
            return

        frame = self._dispatcher.get_latest_frame(timeout_ms=self._timeout_ms)
        if frame is None:
            return

        self.frame_ready.emit(frame)
        self._frame_count += 1
        now = perf_counter()
        elapsed = now - self._last_stats_time
        if elapsed >= 1.0:
            self.stats_ready.emit(self._frame_count / elapsed, frame.frame_number)
            self._frame_count = 0
            self._last_stats_time = now
