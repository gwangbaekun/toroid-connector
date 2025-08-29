# cli_demo.py
import argparse
from data import CORES, COILS
from search import find_combinations

def main():
    parser = argparse.ArgumentParser(description="Toroid inductance selector")
    parser.add_argument("--L", type=float, required=True, help="Target inductance in Henry (e.g., 0.002 for 2 mH)")
    parser.add_argument("--tol", type=float, default=0.1, help="Relative tolerance (e.g., 0.05 = 5%)")
    parser.add_argument("--imax", type=float, default=None, help="Optional working current in A for Bsat check")
    parser.add_argument("--k", type=int, default=10, help="Max results to show")
    args = parser.parse_args()

    options = find_combinations(
        L_target_h=args.L,
        cores=CORES,
        coils=COILS,
        tolerance=args.tol,
        max_results=args.k,
        working_current_a=args.imax,
    )

    if not options:
        print("No viable combinations found with given parameters.")
        return

    for i, d in enumerate(options, 1):
        print(f"{i:2d}. Core={d.core.name} | Coil={d.coil.name} | N={d.turns} turns")
        print(f"    L={d.L_h:.6g} H (err={d.rel_error*100:.2f}%) | R={d.resistance_ohm:.4f} Ω")
        print(f"    Wire length={d.wire_length_m:.3f} m | Cost=${d.cost_usd:.2f} | Score={d.score:.4f}")

if __name__ == "__main__":
    main()