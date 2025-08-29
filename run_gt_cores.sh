#!/bin/zsh
set -euo pipefail

DIR=$(cd -- "$(dirname -- "$0")" && pwd)

usage() {
  cat <<USAGE
Usage:
  $0 summary <csv_path>
  $0 part <csv_path> <PART_NO>
  $0 combos <csv_path> <L_uH> [tolerance_percent=10] [I_amp]

Examples:
  $0 summary "TalkFile_창성코어(High Flux GT Cores).xlsx - Hight Flux GT Cores.csv"
  $0 part    "TalkFile_창성코어(High Flux GT Cores).xlsx - Hight Flux GT Cores.csv" CH540GT
  $0 combos  "TalkFile_창성코어(High Flux GT Cores).xlsx - Hight Flux GT Cores.csv" 250 10 0.5
USAGE
}

if [[ $# -lt 2 ]]; then
  usage
  exit 1
fi

cmd=$1
shift

case "$cmd" in
  summary)
    csv_path=$1
    python3 - "$csv_path" <<'PY'
import sys
from pathlib import Path
repo = Path(__file__).resolve().parent
sys.path.insert(0, str(repo))
from import_csv import summarize_csv
print(summarize_csv(sys.argv[1]))
PY
    ;;
  part)
    if [[ $# -lt 2 ]]; then
      echo "part requires: <csv_path> <PART_NO>" >&2
      exit 1
    fi
    csv_path=$1
    part_no=$2
    python3 - "$csv_path" "$part_no" <<'PY'
import sys
from pathlib import Path
repo = Path(__file__).resolve().parent
sys.path.insert(0, str(repo))
from import_csv import _parse_csv_rows

csv_path, part_no = sys.argv[1], sys.argv[2]
rows = _parse_csv_rows(csv_path)
for r in rows:
    if r.part_no == part_no:
        print(r)
        break
else:
    print(f"Part not found: {part_no}")
PY
    ;;
  combos)
    if [[ $# -lt 2 ]]; then
      echo "combos requires: <csv_path> <L_uH> [tolerance_percent=10] [I_amp]" >&2
      exit 1
    fi
    csv_path=$1
    L_uH=$2
    tol_pc=${3:-10}
    I_amp=${4:-}
    python3 - "$csv_path" "$L_uH" "$tol_pc" "$I_amp" <<'PY'
import sys
from pathlib import Path
repo = Path(__file__).resolve().parent
sys.path.insert(0, str(repo))
from import_csv import cores_from_high_flux_csv
from data import COILS
from search import find_combinations

csv_path = sys.argv[1]
L_uH = float(sys.argv[2])
tol = float(sys.argv[3]) / 100.0
I_amp = sys.argv[4]
I = float(I_amp) if I_amp else None

cores = cores_from_high_flux_csv(csv_path)
opts = find_combinations(L_target_h=L_uH*1e-6, cores=cores, coils=COILS, tolerance=tol, working_current_a=I)
for i, d in enumerate(opts, 1):
    print(f"{i:2d}. Core={d.core.name} | Coil={d.coil.name} | N={d.turns}")
    print(f"    L={d.L_h:.6g} H (err={d.rel_error*100:.2f}%) | R={d.resistance_ohm:.4f} Ω")
    print(f"    Wire length={d.wire_length_m:.3f} m | Cost=${d.cost_usd:.2f} | Score={d.score:.4f}")
PY
    ;;
  *)
    usage
    exit 1
    ;;
esac



