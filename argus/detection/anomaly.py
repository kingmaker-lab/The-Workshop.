from collections import defaultdict
from math import sqrt


class OnlineBaseline:
    """Welford baseline for numeric measurements, ready for later anomaly rules."""

    def __init__(self, minimum_samples: int = 5) -> None:
        if minimum_samples < 5:
            raise ValueError("minimum_samples must be at least 5")
        self.minimum_samples = minimum_samples
        self._count: dict[tuple[str, str], int] = defaultdict(int)
        self._mean: dict[str, float] = defaultdict(float)
        self._sum_squared_delta: dict[str, float] = defaultdict(float)

    def observe(self, key: tuple[str, str], value: float) -> float | None:
        count = self._count[key]
        if count < self.minimum_samples:
            self._update(key, value)
            return None
        variance = self._sum_squared_delta[key] / max(count - 1, 1)
        standard_deviation = sqrt(variance)
        difference = abs(value - self._mean[key])
        score = (0.0 if difference == 0 else float("inf")) if standard_deviation == 0 else difference / standard_deviation
        self._update(key, value)
        return score

    def _update(self, key: tuple[str, str], value: float) -> None:
        self._count[key] += 1
        delta = value - self._mean[key]
        self._mean[key] += delta / self._count[key]
        self._sum_squared_delta[key] += delta * (value - self._mean[key])