"""Configuration for multi-bin sensor simulation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SensorSimulationConfig:
    """Runtime parameters for the sensor layer."""

    # Geographic / logical grouping
    zones: list[str] = field(default_factory=lambda: ["zone-A", "zone-B", "zone-C"])
    bins_per_zone: int = 3  # total bins = len(zones) * bins_per_zone (9 by default)

    # Sampling: interval between readings per bin, seconds (2–5 typical)
    interval_sec: float = 3.0

    # RNG seed for reproducible demos (None = nondeterministic)
    random_seed: int | None = 42

    # Daytime usage: local hour range where foot traffic is higher (24h clock)
    peak_hours_start: int = 8
    peak_hours_end: int = 20

    # Simulation dynamics
    fill_drift_per_tick: float = 0.8  # base expected fill increase per reading (%)

    # When True (fog --demo): some bins get high temperature with capped low fill to exercise fog alerts.
    enable_thermal_demo: bool = False
    # Bin index -> "elevated" (fire_risk band) or "probable" (≥ probable-fire °C). Default: one of each.
    thermal_bin_profiles: dict[int, str] = field(
        default_factory=lambda: {0: "probable", 6: "elevated"}
    )
