"""
Configurable weights for the IntelliDC Weighted Scoring Model.

Weights are stored in a mutable dictionary so they can be updated
at runtime from the AI Configuration page without restarting the server.

All weights MUST sum to 1.0.
"""

DEFAULT_WEIGHTS = {
    "cpu":                  0.25,
    "ram":                  0.15,
    "storage":              0.10,
    "network":              0.10,
    "temperature":          0.15,
    "power":                0.10,
    "humidity":             0.05,
    "workload_criticality": 0.10,
}

# Runtime-mutable weights — initialized from defaults.
# The AI Configuration page will modify this dict directly.
active_weights = dict(DEFAULT_WEIGHTS)


def validate_weights(weights: dict) -> bool:
    """Check that all weights are non-negative and sum to 1.0 (within tolerance)."""
    if any(v < 0 for v in weights.values()):
        return False
    total = sum(weights.values())
    return abs(total - 1.0) < 1e-6


def update_weights(new_weights: dict) -> dict:
    """
    Replace active weights with new_weights after validation.
    Returns the updated weights dict.
    Raises ValueError if weights are invalid.
    """
    if not validate_weights(new_weights):
        raise ValueError(
            f"Weights must be non-negative and sum to 1.0. "
            f"Got sum={sum(new_weights.values()):.6f}"
        )
    active_weights.clear()
    active_weights.update(new_weights)
    return dict(active_weights)


def reset_weights() -> dict:
    """Reset active weights back to defaults."""
    active_weights.clear()
    active_weights.update(DEFAULT_WEIGHTS)
    return dict(active_weights)


def get_weights() -> dict:
    """Return a copy of the current active weights."""
    return dict(active_weights)
