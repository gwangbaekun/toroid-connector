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

# 기본 코어 CSV(내장). 리포지토리 CSV가 없을 때 사용
DEFAULT_CORE_CSV = """,,,,,,,,,,,,
,Part No,Nominal Inductance(nH/N²),,,Path Length (cm),Cross Section Area (cm²),Dimensions(mm),,,,,
,,,,,,,Before Finish Dimensions,,,After Finish Dimensions,,
,,,,,,,OD(mm),ID(mm),HT(mm),OD(mm),ID(mm),HT(mm)
,,26u,060u,125u,,,MAX,MIN,MAX,MAX,MIN,MAX
,CH097GT,14,32,67,2.18,0.095,9.65,4.78,3.96,10.29,4.27,4.57
,CH102GT,14,32,67,2.38,0.1,10.16,5.08,3.96,10.8,4.57,4.57
,CH112GT,11,26,54,2.69,0.091,11.18,6.35,3.96,11.9,5.89,4.72
,CH127GT,12,27,56,3.12,0.114,12.7,7.62,4.75,13.46,6.99,5.51
,CH147GT,14,32,67,3.63,0.154,14.7,8.9,5.6,15.5,8.2,6.4
,CH166GT,15,35,73,4.11,0.192,16.51,10.16,6.35,17.4,9.53,7.11
,CH172GT,19,43,90,4.14,0.232,17.27,9.65,6.35,18.03,9.02,7.11
,CH203GT,14,32,67,5.09,0.226,20.32,12.7,6.35,21.1,12.07,7.11
,CH229GT,19,43,90,5.67,0.331,22.86,13.97,7.62,23.62,13.39,8.38
,CH234GT,22,51,106,5.88,0.388,23.57,14.4,8.89,24.3,13.77,9.7
,CH252GT,27,62,130,6.1,0.504,25.2,14.6,10,26,13.9,10.8
,CH270GT,33,75,156,6.35,0.654,26.92,14.73,11.18,27.7,14.1,11.99
,CH300GT,29,68,141,7.27,0.652,30,17.4,10.9,30.8,16.7,11.8
,CH330GT,26,61,127,8.15,0.672,33.02,19.94,10.67,33.83,19.3,11.61
,CH343GT,16,38,79,8.95,0.454,34.29,23.37,8.89,35.2,22.6,9.83
,CH358GT,24,56,117,8.98,0.678,35.81,22.35,10.46,36.7,21.5,11.28
,CH378GT,30,70,145,9.4,0.867,37.8,23.2,12.5,38.7,22.3,13.4
,CH400GT,35,81,169,9.84,1.072,39.88,24.13,14.48,40.7,23.3,15.37
,CH434GT,40,92,191,10.74,1.308,43.4,26.4,16.2,44.3,25.5,17.1
,CH467GT,59,135,281,10.74,1.99,46.74,24.13,18.03,47.6,23.3,18.92
,CH468GT,37,86,179,11.63,1.34,46.74,28.7,15.24,47.6,27.9,16.13
,CH488GT,44,101,210,11.74,1.569,48.8,27.9,15.8,49.7,27,16.7
,CH508GT,32,73,152,12.73,1.25,50.8,31.75,13.46,51.7,30.9,14.35
,CH540GT,44,102,213,12.63,1.71,54,29,14.4,54.9,28.1,15.3
,CH571GT,60,138,288,12.5,2.29,57.15,26.39,15.24,58,25.6,16.1
,CH572GT,33,75,156,14.3,1.444,57.15,35.56,13.97,58,34.7,14.86
,CH596GT,54,125,260,14.33,2.371,59.6,34,19.5,60.6,33,20.5
,CH610GT,83,192,400,14.37,3.675,62,32.6,25,63.1,31.37,26.27
,CH640GT,49,113,234,16.04,2.394,64,40,21,65.1,39,22.1
,CH680GT,62,143,299,15.81,3.008,68,36,20,69.1,35,21.1
,CH740GT,89,206,429,18.39,4.788,74.1,45.3,35,75.2,44.07,36.27
"""

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
else:
    # Fallback to embedded CSV
    csv_io = io.StringIO(DEFAULT_CORE_CSV)
    cores = cores_from_high_flux_csv(csv_io)
    csv_io.seek(0)
    rows = _parse_csv_rows(csv_io)
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


