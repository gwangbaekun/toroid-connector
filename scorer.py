# scorer.py
from dataclasses import dataclass

@dataclass
class ScoreWeights:
    w_error: float = 1.0
    w_cost: float = 0.1
    w_resistance: float = 0.02
    # New: weight and preferred range for fill ratio
    w_fill: float = 0.5
    fill_min: float = 0.75
    fill_max: float = 0.85

def _fill_penalty(fill_ratio: float | None, fill_min: float, fill_max: float) -> float:
    if fill_ratio is None:
        return 0.0
    fr = max(0.0, min(1.0, fill_ratio))
    if fill_min <= fr <= fill_max:
        return 0.0
    if fr < fill_min:
        return fill_min - fr
    return fr - fill_max

def score_combo(
    rel_error: float,
    total_cost_usd: float,
    resistance_ohm: float,
    w: ScoreWeights,
    *,
    fill_ratio: float | None = None,
) -> float:
    # Lower is better
    base = w.w_error * rel_error + w.w_cost * total_cost_usd + w.w_resistance * resistance_ohm
    fill_pen = _fill_penalty(fill_ratio, w.fill_min, w.fill_max)
    return base + w.w_fill * fill_pen