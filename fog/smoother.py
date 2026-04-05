"""Simple moving-average smoothing per bin for noisy telemetry."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from shared.constants import SMOOTHING_WINDOW
from shared.models import BinReading


@dataclass
class SmoothedReading:
    """Smoothed scalar snapshot for one bin after one new raw sample."""

    bin_id: str
    zone: str
    fill_level: float
    weight_kg: float
    temperature_c: float
    usage_count: float  # smoothed event count (float for moving average)
    timestamp: float


class PerBinMovingAverage:
    """Maintains deques of the last N samples and exposes running averages."""

    def __init__(self, window: int = SMOOTHING_WINDOW) -> None:
        self._window = max(1, window)
        self._fill: deque[float] = deque(maxlen=self._window)
        self._weight: deque[float] = deque(maxlen=self._window)
        self._temp: deque[float] = deque(maxlen=self._window)
        self._usage: deque[float] = deque(maxlen=self._window)

    def update(self, r: BinReading) -> SmoothedReading:
        self._fill.append(r.fill_level)
        self._weight.append(r.weight_kg)
        self._temp.append(r.temperature_c)
        self._usage.append(float(r.usage_count))

        def avg(q: deque[float]) -> float:
            return sum(q) / len(q)

        return SmoothedReading(
            bin_id=r.bin_id,
            zone=r.zone,
            fill_level=avg(self._fill),
            weight_kg=avg(self._weight),
            temperature_c=avg(self._temp),
            usage_count=avg(self._usage),
            timestamp=r.timestamp,
        )


class SmoothingRegistry:
    """One moving-average filter per bin_id."""

    def __init__(self, window: int = SMOOTHING_WINDOW) -> None:
        self._window = window
        self._per_bin: dict[str, PerBinMovingAverage] = {}

    def smooth(self, r: BinReading) -> SmoothedReading:
        if r.bin_id not in self._per_bin:
            self._per_bin[r.bin_id] = PerBinMovingAverage(self._window)
        return self._per_bin[r.bin_id].update(r)
