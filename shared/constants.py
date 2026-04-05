"""Thresholds and tuning knobs shared across fog logic."""

# Fill level alerts (%)
FILL_WARNING_PCT = 80.0
FILL_CRITICAL_PCT = 95.0

# Fire-risk heuristic: bin interior temperature (°C)
FIRE_TEMP_THRESHOLD_C = 45.0
# Above this, fog treats the bin as probable fire (escalation above fire_risk).
PROBABLE_FIRE_TEMP_THRESHOLD_C = 60.0

# Normalization for priority formula (sensor ranges)
USAGE_COUNT_CAP = 30  # at or above => usage_norm = 100
TEMP_MIN_C = 5.0
TEMP_MAX_C = 55.0

# Priority weights (must match assignment spec)
WEIGHT_FILL = 0.6
WEIGHT_USAGE = 0.3
WEIGHT_TEMP = 0.1

# Moving-average window (number of raw readings per bin)
SMOOTHING_WINDOW = 5
