# scorer.py
from dataclasses import dataclass

@dataclass
class ScoreWeights:
    w_error: float = 1.0
    w_cost: float = 0.1
    w_resistance: float = 0.02

def score_combo(rel_error: float, total_cost_usd: float, resistance_ohm: float, w: ScoreWeights) -> float:
    # Lower is better
    return w.w_error * rel_error + w.w_cost * total_cost_usd + w.w_resistance * resistance_ohm