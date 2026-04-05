"""
Per-bin state machine producing realistic fill, weight, temperature, and usage.

Patterns:
- Higher `usage_count` during daytime hours (configurable peak window).
- Fill level tends upward with noise; occasional simulated "collection" drops fill.
- Weight correlates with fill; temperature follows ambient + small heat from compaction.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Literal

from shared.models import BinReading

from sensors.config import SensorSimulationConfig

ThermalProfile = Literal["none", "elevated", "probable"]


@dataclass
class _BinState:
    """Internal evolving state for one bin."""

    fill_level: float
    last_collection_tick: int = 0


class SingleBinSimulator:
    """Generates one time series for a single smart bin."""

    def __init__(
        self,
        bin_id: str,
        zone: str,
        config: SensorSimulationConfig,
        rng: random.Random,
        *,
        thermal_profile: ThermalProfile = "none",
    ) -> None:
        self.bin_id = bin_id
        self.zone = zone
        self._cfg = config
        self._rng = rng
        self._thermal_profile = thermal_profile
        self._tick = 0
        # Start fills spread out so bins do not sync perfectly
        thermal = thermal_profile != "none"
        low = 12.0 if thermal else 15.0
        high = 35.0 if thermal else 55.0
        self._state = _BinState(fill_level=rng.uniform(low, high))

    def _daytime_factor(self, hour: float) -> float:
        """Return ~1.0 in peak hours, lower at night."""
        s, e = self._cfg.peak_hours_start, self._cfg.peak_hours_end
        if s <= hour < e:
            return 1.0
        # Smooth shoulder: lower usage overnight
        return 0.25 + 0.15 * math.sin((hour / 24.0) * math.pi)

    def _maybe_collect(self) -> None:
        """Randomly empty the bin to simulate collection routes."""
        # About once every ~200 ticks per bin on average
        if self._rng.random() < 0.005:
            self._state.fill_level = self._rng.uniform(5.0, 18.0)
            self._state.last_collection_tick = self._tick

    def next_reading(self) -> BinReading:
        self._tick += 1
        self._maybe_collect()

        hour = (time.localtime().tm_hour + time.localtime().tm_min / 60.0) % 24.0
        day_factor = self._daytime_factor(hour)

        # Usage: event count higher during busy hours (Poisson-like via Gaussian clamp)
        lam = 1.5 + 5.5 * day_factor
        noise = max(0.0, self._rng.gauss(lam, math.sqrt(lam + 0.5)))
        usage_count = max(0, int(noise + self._rng.randint(0, 2)))

        drift = self._cfg.fill_drift_per_tick * (0.3 + 0.7 * day_factor)
        noise = self._rng.gauss(0, 0.35)
        self._state.fill_level = max(
            0.0,
            min(100.0, self._state.fill_level + drift + noise + usage_count * 0.08),
        )

        if self._thermal_profile != "none":
            # Hot surface / smoldering: keep fill low while temp is forced high below
            self._state.fill_level = min(self._state.fill_level, 38.0)

        # Weight scales with fill (max ~120 kg nominal when full)
        nominal_max_kg = 120.0
        weight_kg = max(
            2.0,
            (self._state.fill_level / 100.0) * nominal_max_kg
            + self._rng.gauss(0, 1.2),
        )

        # Ambient + weak correlation with fill (decomposition / heat)
        ambient = 18.0 + 6.0 * math.sin((hour - 6) / 24 * 2 * math.pi)
        temperature_c = ambient + 0.04 * self._state.fill_level + self._rng.gauss(0, 0.6)

        if self._thermal_profile == "probable":
            temperature_c = 61.5 + self._rng.gauss(0, 1.5)
            temperature_c = min(66.0, max(60.0, temperature_c))
        elif self._thermal_profile == "elevated":
            temperature_c = 46.5 + self._rng.gauss(0, 1.8)
            temperature_c = min(55.0, max(45.5, temperature_c))

        ts = time.time()
        return BinReading(
            bin_id=self.bin_id,
            zone=self.zone,
            fill_level=round(self._state.fill_level, 2),
            weight_kg=round(weight_kg, 2),
            temperature_c=round(temperature_c, 2),
            usage_count=usage_count,
            timestamp=ts,
        )


class MultiBinOrchestrator:
    """Runs 5–10 bins across configured zones in round-robin or parallel schedule."""

    def __init__(self, config: SensorSimulationConfig | None = None) -> None:
        self.config = config or SensorSimulationConfig()
        seed = self.config.random_seed
        self._rng = random.Random(seed)
        self._bins: list[SingleBinSimulator] = []
        idx = 0
        bin_index = 0
        for zone in self.config.zones:
            for _ in range(self.config.bins_per_zone):
                idx += 1
                bin_id = f"BIN-{zone}-{idx:02d}"
                prof: ThermalProfile = "none"
                if self.config.enable_thermal_demo:
                    raw = self.config.thermal_bin_profiles.get(bin_index)
                    if raw == "probable":
                        prof = "probable"
                    elif raw == "elevated":
                        prof = "elevated"
                self._bins.append(
                    SingleBinSimulator(
                        bin_id=bin_id,
                        zone=zone,
                        config=self.config,
                        rng=random.Random(seed + idx * 9973 if seed is not None else None),
                        thermal_profile=prof,
                    )
                )
                bin_index += 1

    @property
    def bins(self) -> list[SingleBinSimulator]:
        return self._bins

    def all_readings_tick(self) -> list[BinReading]:
        """One simulation step: every bin emits one reading (stagger optional)."""
        return [b.next_reading() for b in self._bins]
