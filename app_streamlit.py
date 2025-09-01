import io
import tempfile
from dataclasses import replace
from pathlib import Path
import pandas as pd
import streamlit as st

from import_csv import cores_from_high_flux_csv, _parse_csv_rows
from models import Coil
from search import find_combinations


st.set_page_config(page_title="토로이드 코일 설계", layout="wide")
st.title("토로이드 코일 설계 프로그램")

# 기본 코일 데이터(내장). Docker/오프라인 동작 보장
DEFAULT_COILS = [
    {
        "name": "AWG 30 enamel",
        "awg": 30,
        "wire_diameter_m": 0.255e-3,
        "resistance_per_m_ohm": 0.345,
        "price_per_m_usd": 0.04,
        "packing_factor": 0.68,
        "base_price_usd": 0.0,
        "enamel_thickness_m": 0.010e-3,
    },
    {
        "name": "AWG 28 enamel",
        "awg": 28,
        "wire_diameter_m": 0.321e-3,
        "resistance_per_m_ohm": 0.214,
        "price_per_m_usd": 0.05,
        "packing_factor": 0.68,
        "base_price_usd": 0.0,
        "enamel_thickness_m": 0.012e-3,
    },
    {
        "name": "AWG 26 enamel",
        "awg": 26,
        "wire_diameter_m": 0.405e-3,
        "resistance_per_m_ohm": 0.135,
        "price_per_m_usd": 0.06,
        "packing_factor": 0.70,
        "base_price_usd": 0.0,
        "enamel_thickness_m": 0.015e-3,
    },
    {
        "name": "AWG 24 enamel",
        "awg": 24,
        "wire_diameter_m": 0.511e-3,
        "resistance_per_m_ohm": 0.085,
        "price_per_m_usd": 0.07,
        "packing_factor": 0.72,
        "base_price_usd": 0.0,
        "enamel_thickness_m": 0.018e-3,
    },
    {
        "name": "AWG 22 enamel",
        "awg": 22,
        "wire_diameter_m": 0.644e-3,
        "resistance_per_m_ohm": 0.0535,
        "price_per_m_usd": 0.09,
        "packing_factor": 0.73,
        "base_price_usd": 0.0,
        "enamel_thickness_m": 0.020e-3,
    },
]

with st.sidebar:
    st.header("입력 (Inputs)")
    # 고정 소스: 리포지토리 CSV (창성코어)
    repo_csv_path = Path(__file__).resolve().parent / "TalkFile_창성코어(High Flux GT Cores).xlsx - Hight Flux GT Cores.csv"
    uploaded = None
    L_uH = st.number_input("목표 인덕턴스 (µH)", min_value=0.1, value=250.0, step=10.0)
    enamel_um = st.number_input("에나멜 두께 (µm, 절연 단면 두께)", min_value=0.0, value=12.0, step=1.0)
    top_k = st.slider("상위 K", min_value=1, max_value=100, value=20)

tab1, tab2 = st.tabs(["결과 (Results)", "CSV 미리보기 (Preview)"]) 

cores = []
rows_df = None

if repo_csv_path.exists():
    cores = cores_from_high_flux_csv(str(repo_csv_path))
    rows = _parse_csv_rows(str(repo_csv_path))
    if rows:
        rows_df = pd.DataFrame([{
            "파트 번호 (part_no)": r.part_no,
            "A_L 26µ (nH/N^2)": r.al_26_nH,
            "A_L 60µ (nH/N^2)": r.al_60_nH,
            "A_L 125µ (nH/N^2)": r.al_125_nH,
            "경로 길이 (path_m)": r.path_len_m,
            "단면적 (area_m2)": r.area_m2,
            "외경 (OD_m)": r.od_after_m,
            "내경 (ID_m)": r.id_after_m,
            "높이 (HT_m)": r.ht_after_m,
        } for r in rows])

if cores:
    # Build coil list with ABSOLUTE enamel thickness (µm -> m)
    name_to_coil = {c["name"]: c for c in DEFAULT_COILS}
    coils = []
    for name in name_to_coil.keys():
        base = name_to_coil.get(name)
        if base is None:
            continue
        # Build real Coil instance so max_turns_on is available
        coils.append(
            Coil(
                name=base["name"],
                awg=base["awg"],
                wire_diameter_m=base["wire_diameter_m"],
                resistance_per_m_ohm=base["resistance_per_m_ohm"],
                price_per_m_usd=base["price_per_m_usd"],
                packing_factor=base["packing_factor"],
                base_price_usd=base["base_price_usd"],
                enamel_thickness_m=enamel_um * 1e-6,
            )
        )

    if not coils:
        st.warning("No coils selected. Please choose at least one coil.")
        opts = []
    else:
        opts = find_combinations(
            L_target_h=L_uH*1e-6,
            cores=cores,
            coils=coils,
            tolerance=0.10,
            working_current_a=None,
        )

    # Show results
    with tab1:
        st.subheader("설계 옵션 (Design Options)")
        df = pd.DataFrame([{
            "코어 (Core)": d.core.name,
            "코일 (Coil)": d.coil.name,
            "턴수 (Turns)": d.turns,
            "코어 내경(mm) (Core_ID_mm)": (getattr(d.core, "id_m", None) or 0.0) * 1e3,
            "인덕턴스(H) (L_H)": d.L_h,
            "오차(%) (Error_%)": d.rel_error*100,
            "와이어 길이(m) (Wire_m)": d.wire_length_m,
            "저항(Ω) (R_ohm)": d.resistance_ohm,
            "비용(USD) (Cost_usd)": d.cost_usd,
            "점수 (Score)": d.score,
            "유효 와이어 직경(mm) (EffWire_d_mm)": (d.coil.wire_diameter_m + 2*d.coil.enamel_thickness_m) * 1e3,
            "윈도우 면적(mm²) (WindowArea)": d.window_area_m2 * 1e6,
            "남은 면적(mm²) (Leftover)": d.leftover_window_area_m2 * 1e6,
            "필 비율(%) (FillRatio)": d.fill_ratio * 100,
        } for d in opts[:top_k]])
        st.dataframe(df, use_container_width=True)

        csv_download = df.to_csv(index=False).encode('utf-8')
        st.download_button("결과 CSV 다운로드 (Download Results CSV)", data=csv_download, file_name="toroid_options.csv", mime="text/csv")

    with tab2:
        st.subheader("CSV 미리보기 (Preview)")
        if rows_df is not None:
            st.dataframe(rows_df, use_container_width=True)
        else:
            st.info("미리보기를 위해 CSV를 업로드하세요.")
else:
    with tab1:
        st.info("리포지토리 CSV가 필요합니다. 파일을 프로젝트 루트에 두고 다시 실행하세요.")
    with tab2:
        st.info("CSV 업로드를 기다리는 중…")


