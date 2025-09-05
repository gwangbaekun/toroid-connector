# search.py
from dataclasses import dataclass
from math import ceil, pi, floor
from typing import Iterable
from models import Core, Coil
from physics import toroid_inductance_h, turns_for_target, mean_turn_length_m, flux_density_t
from scorer import score_combo, ScoreWeights

@dataclass
class DesignOption:
    core: Core
    coil: Coil
    turns: int
    L_h: float
    rel_error: float
    wire_length_m: float
    resistance_ohm: float
    cost_usd: float
    score: float
    # Added: window usage metrics
    window_area_m2: float
    leftover_window_area_m2: float
    fill_ratio: float

def find_combinations(
    L_target_h: float,
    cores: Iterable[Core],
    coils: Iterable[Coil],
    tolerance: float = 0.1,             # ±10%
    max_results: int = 20,
    weights: ScoreWeights = ScoreWeights(),
    working_current_a: float | None = None,
) -> list[DesignOption]:
    results: list[DesignOption] = []

    for core in cores:
        N_req = turns_for_target(core, L_target_h)
        # Try integer turns around N_req for robustness
        for N in {max(1, ceil(N_req - 2)), max(1, ceil(N_req - 1)), max(1, ceil(N_req)), max(1, ceil(N_req + 1)), max(1, ceil(N_req + 2))}:
            L_actual = toroid_inductance_h(core, N)
            rel_error = abs(L_actual - L_target_h) / L_target_h
            if rel_error > tolerance:
                continue

            for coil in coils:
                if N > coil.max_turns_on(core):
                    continue

                # Optional saturation check
                if working_current_a is not None and core.b_sat_t is not None:
                    if flux_density_t(core, N, working_current_a) > core.b_sat_t:
                        continue

                # wire_length = N * mean_turn_length_m(core)
                # resistance = coil.resistance_per_m_ohm * wire_length
                # cost = core.price_usd + coil.base_price_usd + (coil.price_per_m_usd * wire_length)

                # # Window usage metrics
                # window_area = pi * ((getattr(core, "id_m", None) or 0.0) / 2) ** 2 if getattr(core, "id_m", None) else core.window_area_m2
                # effective_diameter = coil.wire_diameter_m + 2 * max(0.0, getattr(coil, "enamel_thickness_m", 0.0))
                # wire_area = pi * (effective_diameter / 2) ** 2
                # # Required total geometric area given packing factor
                # required_total_area = (N * wire_area) / max(1e-9, coil.packing_factor)
                # leftover_total_area = max(0.0, window_area - required_total_area)
                # used_fraction = 0.0 if window_area <= 0 else min(1.0, (required_total_area / window_area))
                # # Recompute score with fill penalty preference (75-85% default from weights)
                # score = score_combo(rel_error, cost, resistance, weights, fill_ratio=used_fraction)

                wire_length, layers_used, finished_id_m, finished_od_m, cap_turns = layered_wire_length(core, coil, N)
                resistance = coil.resistance_per_m_ohm * wire_length
                cost = core.price_usd + coil.base_price_usd + (coil.price_per_m_usd * wire_length)

                # Window/usage metrics from layered capacity
                window_area = pi * ((getattr(core, "id_m", None) or 0.0) / 2) ** 2 if getattr(core, "id_m", None) else core.window_area_m2
                # Prefer a usage metric aligned with layered model: fraction of capacity
                used_fraction = 0.0 if cap_turns <= 0 else min(1.0, N / cap_turns)
                leftover_total_area = window_area * max(0.0, 1.0 - used_fraction)

                # Recompute score with fill preference
                score = score_combo(rel_error, cost, resistance, weights, fill_ratio=used_fraction)

                results.append(DesignOption(
                    core=core, coil=coil, turns=N, L_h=L_actual, rel_error=rel_error,
                    wire_length_m=wire_length, resistance_ohm=resistance, cost_usd=cost, score=score,
                    window_area_m2=window_area, leftover_window_area_m2=leftover_total_area, fill_ratio=used_fraction
                ))

    results.sort(key=lambda d: (d.score, d.cost_usd, d.rel_error))
    return results[:max_results]



# Add in search.py (below imports)
def layered_wire_length(core: Core, coil: Coil, N: int) -> tuple[float, int, float, float, int]:
    """
    IWM-style wire length and capacity at overall wire pitch.
    Returns: (wire_length_m, layers_used, finished_id_m, finished_od_m, capacity_turns)
    """
    d_eff = coil.wire_diameter_m + 2 * max(0.0, getattr(coil, "enamel_thickness_m", 0.0))

    # Resolve core dimensions
    if core.id_m is not None and core.od_m is not None and core.ht_m is not None:
        ID, OD, HT = core.id_m, core.od_m, core.ht_m
    else:
        derived = core._derive_dimensions_from_fields()
        if derived is None:
            return 0.0, 0, getattr(core, "id_m", 0.0) or 0.0, getattr(core, "od_m", 0.0) or 0.0, 0
        OD, ID, HT = derived

    if d_eff <= 0 or ID <= 0 or OD <= ID or HT <= 0:
        return 0.0, 0, ID, OD, 0

    tpl = floor(HT / d_eff)               # turns per layer at wire pitch (height direction)
    layers_radial = floor(((OD - ID) / 2.0) / d_eff)
    if tpl <= 0 or layers_radial <= 0:
        return 0.0, 0, ID, OD, 0

    capacity = tpl * layers_radial
    turns_needed = int(max(0, min(N, capacity)))

    length = 0.0
    remaining = turns_needed
    layers_used = 0

    # Distribute turns across layers; layer k (1-indexed) mid diameter Dk = ID + d_eff*(2k-1)
    for k in range(1, layers_radial + 1):
        if remaining <= 0:
            break
        turns_k = min(tpl, remaining)
        Dk = ID + d_eff * (2 * k - 1)
        length += turns_k * (pi * Dk)
        remaining -= turns_k
        layers_used += 1

    finished_id = max(0.0, ID - 2.0 * d_eff * layers_used)
    finished_od = OD + 2.0 * d_eff * layers_used

    return length, layers_used, finished_id, finished_od, capacity