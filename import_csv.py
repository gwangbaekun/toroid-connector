# import_csv.py
# Utility to parse High Flux GT Cores CSV and convert into Core models

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from math import pi
from pathlib import Path
from typing import Iterable, Union, TextIO, Any

from models import Core
from physics import MU0


@dataclass
class ParsedRow:
    part_no: str
    al_26_nH: float | None
    al_60_nH: float | None
    al_125_nH: float | None
    path_len_m: float
    area_m2: float
    od_after_m: float
    id_after_m: float
    ht_after_m: float


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    v = value.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _parse_csv_rows(source: Union[str, Path, TextIO, bytes, bytearray]) -> list[ParsedRow]:
    rows: list[ParsedRow] = []
    # Normalize source to a file-like reader
    close_after = False
    if isinstance(source, (str, Path)):
        f: TextIO = open(source, newline="", encoding="utf-8")
        close_after = True
    elif hasattr(source, "read"):
        f = source  # type: ignore[assignment]
    else:
        if isinstance(source, (bytes, bytearray)):
            f = io.StringIO(source.decode("utf-8"))
        else:
            f = io.StringIO(str(source))
        close_after = True

    try:
        reader = csv.reader(f)
        for raw in reader:
            if not raw:
                continue
            if len(raw) < 13:
                continue
            part = (raw[1] or "").strip()
            if not part or part.startswith("Part No") or part.startswith("Nominal"):
                continue
            if not part.upper().startswith("CH"):
                continue

            al26 = _to_float(raw[2])
            al60 = _to_float(raw[3])
            al125 = _to_float(raw[4])
            path_cm = _to_float(raw[5]) or 0.0
            area_cm2 = _to_float(raw[6]) or 0.0
            od_a_mm = _to_float(raw[10]) or 0.0
            id_a_mm = _to_float(raw[11]) or 0.0
            ht_a_mm = _to_float(raw[12]) or 0.0

            rows.append(
                ParsedRow(
                    part_no=part,
                    al_26_nH=al26,
                    al_60_nH=al60,
                    al_125_nH=al125,
                    path_len_m=path_cm * 1e-2,
                    area_m2=area_cm2 * 1e-4,
                    od_after_m=od_a_mm * 1e-3,
                    id_after_m=id_a_mm * 1e-3,
                    ht_after_m=ht_a_mm * 1e-3,
                )
            )
    finally:
        if close_after:
            try:
                f.close()
            except Exception:
                pass
    return rows


def _mu_r_from_al(al_nH_per_N2: float, area_m2: float, path_m: float) -> float:
    # AL [H/N^2] = µ0 µr A / l  => µr = AL * l / (µ0 * A)
    al_H = al_nH_per_N2 * 1e-9
    if area_m2 <= 0 or path_m <= 0:
        return 1.0
    return max(1.0, (al_H * path_m) / (MU0 * area_m2))


def cores_from_high_flux_csv(source: Union[str, Path, TextIO, bytes, bytearray]) -> list[Core]:
    parsed = _parse_csv_rows(source)
    cores: list[Core] = []
    for r in parsed:
        # Compute r_mean from given path length, independent of OD/ID
        if r.path_len_m > 0:
            r_mean_m = r.path_len_m / (2 * pi)
        else:
            r_mean_m = (r.od_after_m + r.id_after_m) / 4

        window_area_m2 = pi * (r.id_after_m / 2) ** 2 if r.id_after_m > 0 else 0.0

        def make_core(mu_r: float, grade: str) -> Core:
            return Core(
                name=f"{r.part_no} HighFlux {grade}",
                mu_r=mu_r,
                area_m2=r.area_m2,
                r_mean_m=r_mean_m,
                window_area_m2=window_area_m2,
                b_sat_t=None,
                price_usd=0.0,
                od_m=r.od_after_m or None,
                id_m=r.id_after_m or None,
                ht_m=r.ht_after_m or None,
            )

        if r.al_26_nH is not None:
            cores.append(make_core(_mu_r_from_al(r.al_26_nH, r.area_m2, r.path_len_m), "26u"))
        if r.al_60_nH is not None:
            cores.append(make_core(_mu_r_from_al(r.al_60_nH, r.area_m2, r.path_len_m), "60u"))
        if r.al_125_nH is not None:
            cores.append(make_core(_mu_r_from_al(r.al_125_nH, r.area_m2, r.path_len_m), "125u"))

    return cores


def summarize_csv(source: Union[str, Path, TextIO, bytes, bytearray]) -> str:
    rows = _parse_csv_rows(source)
    total = len(rows)
    if total == 0:
        return "No rows parsed. Check CSV formatting."
    first = rows[0]
    return (
        f"Rows={total}; example {first.part_no}: AL26={first.al_26_nH} nH/N^2, "
        f"path={first.path_len_m:.4f} m, area={first.area_m2:.6f} m^2, "
        f"OD/ID/HT(after)={first.od_after_m:.3f}/{first.id_after_m:.3f}/{first.ht_after_m:.3f} m"
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Parse High Flux GT Cores CSV and print summary")
    p.add_argument("csv_path", help="Path to the CSV file")
    args = p.parse_args()
    print(summarize_csv(args.csv_path))


