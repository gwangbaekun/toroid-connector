# physics.py
from math import sqrt
from models import Core

MU0 = 4e-7 * 3.141592653589793  # H/m

def toroid_inductance_h(core: Core, turns: int) -> float:
    # L = mu0 * mu_r * N^2 * A / l
    return MU0 * core.mu_r * (turns ** 2) * core.area_m2 / core.path_length_m

def turns_for_target(core: Core, L_target_h: float) -> float:
    # N = sqrt(L * l / (mu0 * mu_r * A))
    return sqrt(L_target_h * core.path_length_m / (MU0 * core.mu_r * core.area_m2))

def mean_turn_length_m(core: Core) -> float:
    # Conductor length per turn around mean radius (circumference at r_mean)
    return core.path_length_m

def flux_density_t(core: Core, turns: int, current_a: float) -> float:
    # B = mu0 * mu_r * N * I / l
    return (MU0 * core.mu_r * turns * current_a) / core.path_length_m