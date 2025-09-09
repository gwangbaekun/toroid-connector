import io
import math
import tempfile
from dataclasses import replace
from pathlib import Path
import pandas as pd
import streamlit as st

from import_csv import cores_from_high_flux_csv, _parse_csv_rows
from models import Coil
from search import find_combinations


AWG_CSV = """AWG,직경(mm),단면적(mm²),저항(Ω/m),허용전류(A)
    4/0,11.7,107,0.000161,280~298
    3/0,10.4,85,0.000203,240~257
    2/0,9.26,67.4,0.000256,223
    1/0,8.25,53.5,0.000323,175~190
    1,7.35,42.4,0.000407,165
    2,6.54,33.6,0.000513,130~139
    4,5.19,21.1,0.000815,98~107
    6,4.11,13.3,0.0013,72~81
    8,3.26,8.36,0.00206,55~62
    10,2.59,5.26,0.00328,40~48
    12,2.05,3.31,0.00521,28~35
    14,1.63,2.08,0.00829,18~27
    16,1.29,1.31,0.0132,12~19
    18,1.02,0.823,0.021,7~16
    20,0.812,0.518,0.0333,4.5
    22,0.644,0.326,0.053,3
    24,0.511,0.205,0.0842,0.588
    26,0.405,0.129,0.134,0.378
    28,0.321,0.081,0.213,0.25
    30,0.255,0.0509,0.339,0.147
"""

@st.cache_data
def load_awg_table_static() -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(AWG_CSV))
    df.columns = [str(c).strip() for c in df.columns]
    return df

# def iwm_calc(OD_mm: float, ID_mm: float, HT_mm: float, NT: int, WG_mm: float) -> dict:
#     # JS: len = OD - ID + (2*HT)
#     len_per_turn_mm = OD_mm - ID_mm + (2.0 * HT_mm)
#     total_len_mm = len_per_turn_mm * NT
#     total_len_m = total_len_mm / 1000.0
#     total_len_ft = total_len_mm / 304.8

#     # JS: tpl = round(((ID*Math.PI)/WG)*100)/100
#     if WG_mm <= 0 or ID_mm <= 0:
#         tpl = float("inf")  # IWM의 Infinity 표시와 동일한 상황
#     else:
#         tpl = round(((ID_mm * math.pi) / WG_mm), 2)

#     # JS: nl = round((NT / tpl)*100)/100
#     if not math.isfinite(tpl) or tpl == 0:
#         nl = float("inf")
#         layers_ceil = 0
#     else:
#         nl = round((NT / tpl), 2)
#         layers_ceil = math.ceil(nl)

#     # JS: IDf = round(ID - ceil(nl)*(WG*2), 3)
#     IDf_mm = round(ID_mm - layers_ceil * (WG_mm * 2.0), 3)
#     # JS: ODf = (OD + ceil(nl)*(WG*2))
#     ODf_mm = round(OD_mm + layers_ceil * (WG_mm * 2.0), 3)
#     # JS: HTf = (HT + ceil(nl)*(WG*2))
#     HTf_mm = round(HT_mm + layers_ceil * (WG_mm * 2.0), 3)

#     return {
#         "Length per turn (mm)": round(len_per_turn_mm, 3),
#         "Total length Millimetres": round(total_len_mm, 3),
#         "Total length Meters": round(total_len_m, 6),
#         "Total length Feet": round(total_len_ft, 3),
#         "Turns per layer at wire pitch": ("Infinity" if not math.isfinite(tpl) else tpl),
#         "Number of layers": ("Infinity" if not math.isfinite(nl) else nl),
#         "Theoretical Finished Outside Diameter \"OD\"": ODf_mm,
#         "Theoretical Finished Inner Diameter \"ID\"": IDf_mm,
#         "Theoretical Finished Height \"HT\"": HTf_mm,
#     }


# st.set_page_config(page_title="토로이드 코일 설계", layout="wide")
# st.title("토로이드 코일 설계 프로그램")

# # 기본 코일 데이터(내장). Docker/오프라인 동작 보장
# DEFAULT_COILS = [
#     {
#         "name": "AWG 30 enamel",
#         "awg": 30,
#         "wire_diameter_m": 0.255e-3,
#         "resistance_per_m_ohm": 0.345,
#         "price_per_m_usd": 0.04,
#         "packing_factor": 0.68,
#         "base_price_usd": 0.0,
#         "enamel_thickness_m": 0.010e-3,
#     },
#     {
#         "name": "AWG 28 enamel",
#         "awg": 28,
#         "wire_diameter_m": 0.321e-3,
#         "resistance_per_m_ohm": 0.214,
#         "price_per_m_usd": 0.05,
#         "packing_factor": 0.68,
#         "base_price_usd": 0.0,
#         "enamel_thickness_m": 0.012e-3,
#     },
#     {
#         "name": "AWG 26 enamel",
#         "awg": 26,
#         "wire_diameter_m": 0.405e-3,
#         "resistance_per_m_ohm": 0.135,
#         "price_per_m_usd": 0.06,
#         "packing_factor": 0.70,
#         "base_price_usd": 0.0,
#         "enamel_thickness_m": 0.015e-3,
#     },
#     {
#         "name": "AWG 24 enamel",
#         "awg": 24,
#         "wire_diameter_m": 0.511e-3,
#         "resistance_per_m_ohm": 0.085,
#         "price_per_m_usd": 0.07,
#         "packing_factor": 0.72,
#         "base_price_usd": 0.0,
#         "enamel_thickness_m": 0.018e-3,
#     },
#     {
#         "name": "AWG 22 enamel",
#         "awg": 22,
#         "wire_diameter_m": 0.644e-3,
#         "resistance_per_m_ohm": 0.0535,
#         "price_per_m_usd": 0.09,
#         "packing_factor": 0.73,
#         "base_price_usd": 0.0,
#         "enamel_thickness_m": 0.020e-3,
#     },
# ]

# # 기본 코어 CSV(내장). 리포지토리 CSV가 없을 때 사용
# DEFAULT_CORE_CSV = """,,,,,,,,,,,,
# ,Part No,Nominal Inductance(nH/N²),,,Path Length (cm),Cross Section Area (cm²),Dimensions(mm),,,,,
# ,,,,,,,Before Finish Dimensions,,,After Finish Dimensions,,
# ,,,,,,,OD(mm),ID(mm),HT(mm),OD(mm),ID(mm),HT(mm)
# ,,26u,060u,125u,,,MAX,MIN,MAX,MAX,MIN,MAX
# ,CH097GT,14,32,67,2.18,0.095,9.65,4.78,3.96,10.29,4.27,4.57
# ,CH102GT,14,32,67,2.38,0.1,10.16,5.08,3.96,10.8,4.57,4.57
# ,CH112GT,11,26,54,2.69,0.091,11.18,6.35,3.96,11.9,5.89,4.72
# ,CH127GT,12,27,56,3.12,0.114,12.7,7.62,4.75,13.46,6.99,5.51
# ,CH147GT,14,32,67,3.63,0.154,14.7,8.9,5.6,15.5,8.2,6.4
# ,CH166GT,15,35,73,4.11,0.192,16.51,10.16,6.35,17.4,9.53,7.11
# ,CH172GT,19,43,90,4.14,0.232,17.27,9.65,6.35,18.03,9.02,7.11
# ,CH203GT,14,32,67,5.09,0.226,20.32,12.7,6.35,21.1,12.07,7.11
# ,CH229GT,19,43,90,5.67,0.331,22.86,13.97,7.62,23.62,13.39,8.38
# ,CH234GT,22,51,106,5.88,0.388,23.57,14.4,8.89,24.3,13.77,9.7
# ,CH252GT,27,62,130,6.1,0.504,25.2,14.6,10,26,13.9,10.8
# ,CH270GT,33,75,156,6.35,0.654,26.92,14.73,11.18,27.7,14.1,11.99
# ,CH300GT,29,68,141,7.27,0.652,30,17.4,10.9,30.8,16.7,11.8
# ,CH330GT,26,61,127,8.15,0.672,33.02,19.94,10.67,33.83,19.3,11.61
# ,CH343GT,16,38,79,8.95,0.454,34.29,23.37,8.89,35.2,22.6,9.83
# ,CH358GT,24,56,117,8.98,0.678,35.81,22.35,10.46,36.7,21.5,11.28
# ,CH378GT,30,70,145,9.4,0.867,37.8,23.2,12.5,38.7,22.3,13.4
# ,CH400GT,35,81,169,9.84,1.072,39.88,24.13,14.48,40.7,23.3,15.37
# ,CH434GT,40,92,191,10.74,1.308,43.4,26.4,16.2,44.3,25.5,17.1
# ,CH467GT,59,135,281,10.74,1.99,46.74,24.13,18.03,47.6,23.3,18.92
# ,CH468GT,37,86,179,11.63,1.34,46.74,28.7,15.24,47.6,27.9,16.13
# ,CH488GT,44,101,210,11.74,1.569,48.8,27.9,15.8,49.7,27,16.7
# ,CH508GT,32,73,152,12.73,1.25,50.8,31.75,13.46,51.7,30.9,14.35
# ,CH540GT,44,102,213,12.63,1.71,54,29,14.4,54.9,28.1,15.3
# ,CH571GT,60,138,288,12.5,2.29,57.15,26.39,15.24,58,25.6,16.1
# ,CH572GT,33,75,156,14.3,1.444,57.15,35.56,13.97,58,34.7,14.86
# ,CH596GT,54,125,260,14.33,2.371,59.6,34,19.5,60.6,33,20.5
# ,CH610GT,83,192,400,14.37,3.675,62,32.6,25,63.1,31.37,26.27
# ,CH640GT,49,113,234,16.04,2.394,64,40,21,65.1,39,22.1
# ,CH680GT,62,143,299,15.81,3.008,68,36,20,69.1,35,21.1
# ,CH740GT,89,206,429,18.39,4.788,74.1,45.3,35,75.2,44.07,36.27
# """

# with st.sidebar:
#     st.header("입력 (Inputs)")
#     # 고정 소스: 리포지토리 CSV (창성코어)
#     repo_csv_path = Path(__file__).resolve().parent / "TalkFile_창성코어(High Flux GT Cores).xlsx - Hight Flux GT Cores.csv"
#     uploaded = None
#     # app_streamlit.py (sidebar)
#     L_uH = st.number_input("목표 인덕턴스 (µH)", min_value=0.1, value=250.0, step=10.0)
#     enamel_um = st.number_input("에나멜 두께 (µm)", min_value=0.0, value=12.0, step=1.0)
#     mu_r_input = st.number_input("상대 투자율 μ_r", min_value=1.0, value=60.0, step=1.0)
#     # top_k = st.slider("상위 K", min_value=1, max_value=100, value=20)

# tab1, tab2 = st.tabs(["결과 (Results)", "CSV 미리보기 (Preview)"]) 

# cores = []
# rows_df = None

# if repo_csv_path.exists():
#     cores = cores_from_high_flux_csv(str(repo_csv_path))
#     rows = _parse_csv_rows(str(repo_csv_path))
# else:
#     # Fallback to embedded CSV
#     csv_io = io.StringIO(DEFAULT_CORE_CSV)
#     cores = cores_from_high_flux_csv(csv_io)
#     csv_io.seek(0)
#     rows = _parse_csv_rows(csv_io)
#     if rows:
#         rows_df = pd.DataFrame([{
#             "파트 번호 (part_no)": r.part_no,
#             "A_L 26µ (nH/N^2)": r.al_26_nH,
#             "A_L 60µ (nH/N^2)": r.al_60_nH,
#             "A_L 125µ (nH/N^2)": r.al_125_nH,
#             "경로 길이 (path_m)": r.path_len_m,
#             "단면적 (area_m2)": r.area_m2,
#             "외경 (OD_m)": r.od_after_m,
#             "내경 (ID_m)": r.id_after_m,
#             "높이 (HT_m)": r.ht_after_m,
#         } for r in rows])

# if cores:
#     # Build coil list with ABSOLUTE enamel thickness (µm -> m)
#     name_to_coil = {c["name"]: c for c in DEFAULT_COILS}
#     coils = []
#     for name in name_to_coil.keys():
#         base = name_to_coil.get(name)
#         if base is None:
#             continue
#         # Build real Coil instance so max_turns_on is available
#         coils.append(
#             Coil(
#                 name=base["name"],
#                 awg=base["awg"],
#                 wire_diameter_m=base["wire_diameter_m"],
#                 resistance_per_m_ohm=base["resistance_per_m_ohm"],
#                 price_per_m_usd=base["price_per_m_usd"],
#                 packing_factor=base["packing_factor"],
#                 base_price_usd=base["base_price_usd"],
#                 enamel_thickness_m=enamel_um * 1e-6,
#             )
#         )

#     if not coils:
#         st.warning("No coils selected. Please choose at least one coil.")
#         opts = []
#     else:
#         opts = find_combinations(
#             L_target_h=L_uH*1e-6,
#             cores=cores,
#             coils=coils,
#             tolerance=0.10,
#             working_current_a=None,
#         )

#     # Show results
#     with tab1:
#         st.subheader("설계 옵션 (Design Options)")
#         df = pd.DataFrame([{
#             "코어 (Core)": d.core.name,
#             "코일 (Coil)": d.coil.name,
#             "턴수 (Turns)": d.turns,
#             "윈도우 면적(mm²)": d.window_area_m2 * 1e6,
#             "남은 면적(mm²)": d.leftover_window_area_m2 * 1e6,
#             "필 비율(%)": d.fill_ratio * 100,
#         } for d in opts[:5]])
#         st.dataframe(df, use_container_width=True)

#         csv_download = df.to_csv(index=False).encode('utf-8')
#         st.download_button("결과 CSV 다운로드 (Download Results CSV)", data=csv_download, file_name="toroid_options.csv", mime="text/csv")

#         # --- IWM detail (simple view) ---
#         st.markdown("### IWM 상세 계산 (행 선택)")

#         if opts:
#             labels = [f"{i}: {d.core.name} | {d.coil.name} | N={d.turns}" for i, d in enumerate(opts)]
#             row_idx = st.selectbox("Select row", options=list(range(len(opts))), format_func=lambda i: labels[i], index=0)
#             d = opts[row_idx]

#             # After-finish core dims (mm)
#             core = d.core
#             if getattr(core, "od_m", None) and getattr(core, "id_m", None) and getattr(core, "ht_m", None):
#                 OD_mm, ID_mm, HT_mm = core.od_m*1e3, core.id_m*1e3, core.ht_m*1e3
#             else:
#                 derived = core._derive_dimensions_from_fields() or (0.0, 0.0, 0.0)
#                 od_m, id_m, ht_m = derived
#                 OD_mm, ID_mm, HT_mm = od_m*1e3, id_m*1e3, ht_m*1e3

#             # Wire Size (overall, mm)
#             wire_size_mm = (d.coil.wire_diameter_m + 2*d.coil.enamel_thickness_m) * 1e3

#             # IWM calcs (use the helper you added earlier)
#             calc = iwm_calc(OD_mm, ID_mm, HT_mm, d.turns, wire_size_mm)

#             st.markdown("#### IWM details")
#             st.write({
#                 "Core": d.core.name,
#                 "Coil": d.coil.name,
#                 "Turns": d.turns,
#                 "Wire Size (mm)": f"{wire_size_mm:.3f}",
#                 "Length per turn (mm)": calc["Length per turn (mm)"],
#                 "Total length (mm)": calc["Total length Millimetres"],
#                 "Total length (m)": calc["Total length Meters"],
#                 "Total length (ft)": calc["Total length Feet"],
#                 "Turns per layer (at pitch)": calc["Turns per layer at wire pitch"],
#                 "Number of layers": calc["Number of layers"],
#                 'Finished OD (mm)': calc['Theoretical Finished Outside Diameter "OD"'],
#                 'Finished ID (mm)': calc['Theoretical Finished Inner Diameter "ID"'],
#                 'Finished HT (mm)': calc['Theoretical Finished Height "HT"'],
#             })

#     # with tab2:
#     #     st.subheader("CSV 미리보기 (Preview)")
#     #     if rows_df is not None:
#     #         st.dataframe(rows_df, use_container_width=True)
#     #     else:
#     #         st.info("미리보기를 위해 CSV를 업로드하세요.")
# else:
#     with tab1:
#         st.info("리포지토리 CSV가 필요합니다. 파일을 프로젝트 루트에 두고 다시 실행하세요.")
#     with tab2:
#         st.info("CSV 업로드를 기다리는 중…")


import io
from dataclasses import replace
from math import pi, ceil
import pandas as pd
import streamlit as st

from import_csv import cores_from_high_flux_csv, _parse_csv_rows
from models import Coil
from search import find_combinations

st.set_page_config(page_title="토로이드 코일 설계", layout="wide")
st.title("토로이드 코일 설계 프로그램")

# Default coils (bare diameters). Enamel thickness from user input (µm) will be applied uniformly.
DEFAULT_COILS = [
    {
        "name": "AWG 30 enamel",
        "awg": 30,
        "wire_diameter_m": 0.255e-3,
        "resistance_per_m_ohm": 0.345,
        "price_per_m_usd": 0.04,
        "packing_factor": 0.68,
        "base_price_usd": 0.0,
    },
    {
        "name": "AWG 28 enamel",
        "awg": 28,
        "wire_diameter_m": 0.321e-3,
        "resistance_per_m_ohm": 0.214,
        "price_per_m_usd": 0.05,
        "packing_factor": 0.68,
        "base_price_usd": 0.0,
    },
    {
        "name": "AWG 26 enamel",
        "awg": 26,
        "wire_diameter_m": 0.405e-3,
        "resistance_per_m_ohm": 0.135,
        "price_per_m_usd": 0.06,
        "packing_factor": 0.70,
        "base_price_usd": 0.0,
    },
    {
        "name": "AWG 24 enamel",
        "awg": 24,
        "wire_diameter_m": 0.511e-3,
        "resistance_per_m_ohm": 0.085,
        "price_per_m_usd": 0.07,
        "packing_factor": 0.72,
        "base_price_usd": 0.0,
    },
    {
        "name": "AWG 22 enamel",
        "awg": 22,
        "wire_diameter_m": 0.644e-3,
        "resistance_per_m_ohm": 0.0535,
        "price_per_m_usd": 0.09,
        "packing_factor": 0.73,
        "base_price_usd": 0.0,
    },
]

# Fallback embedded core CSV (High Flux CH series) if repo file missing
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

@st.cache_data
def load_repo_cores() -> tuple[list, pd.DataFrame]:
    # Try repo CSV path; fallback to embedded CSV
    repo_csv = "TalkFile_창성코어(High Flux GT Cores).xlsx - Hight Flux GT Cores.csv"
    try:
        cores = cores_from_high_flux_csv(repo_csv)
        rows = _parse_csv_rows(repo_csv)
    except Exception:
        sio = io.StringIO(DEFAULT_CORE_CSV)
        cores = cores_from_high_flux_csv(sio)
        sio.seek(0)
        rows = _parse_csv_rows(sio)
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
    } for r in rows]) if rows else pd.DataFrame()
    return cores, rows_df

# IWM calculator (from page JS calcs())
def iwm_calcs(OD_mm: float, ID_mm: float, HT_mm: float, NT: int, WG_mm: float) -> dict:
    len_per_turn_mm = OD_mm - ID_mm + (2.0 * HT_mm)
    total_len_mm = len_per_turn_mm * NT
    total_len_m = total_len_mm / 1000.0
    total_len_ft = total_len_mm / 304.8
    if WG_mm <= 0 or ID_mm <= 0:
        tpl = float("inf")
        nl = float("inf")
        layers_ceil = 0
    else:
        tpl = round(((ID_mm * pi) / WG_mm), 2)
        nl = round((NT / tpl), 2) if tpl != 0 else float("inf")
        layers_ceil = ceil(nl if nl != float("inf") else 0)
    IDf_mm = round(ID_mm - layers_ceil * (WG_mm * 2.0), 3)
    ODf_mm = round(OD_mm + layers_ceil * (WG_mm * 2.0), 3)
    HTf_mm = round(HT_mm + layers_ceil * (WG_mm * 2.0), 3)
    return {
        "Length per turn (mm)": round(len_per_turn_mm, 3),
        "Total length Millimetres": round(total_len_mm, 3),
        "Total length Meters": round(total_len_m, 6),
        "Total length Feet": round(total_len_ft, 3),
        "Turns per layer at wire pitch": ("Infinity" if tpl == float("inf") else tpl),
        "Number of layers": ("Infinity" if nl == float("inf") else nl),
        'Theoretical Finished Outside Diameter "OD"': ODf_mm,
        'Theoretical Finished Inner Diameter "ID"': IDf_mm,
        'Theoretical Finished Height "HT"': HTf_mm,
    }

with st.sidebar:
    st.header("입력 (Inputs)")
    L_uH = st.number_input("목표 인덕턴스 (µH)", min_value=0.1, value=250.0, step=10.0)
    mu_r_input = st.number_input("상대 투자율 μ_r", min_value=1.0, value=60.0, step=1.0)

    st.header("와이어 선택")
    awg_df = load_awg_table_static()
    row_index = st.selectbox(
        "AWG 행 선택",
        options=list(range(len(awg_df))),
        format_func=lambda i: f'{awg_df["AWG"].iloc[i]} | 직경={awg_df["직경(mm)"].iloc[i]} mm',
        index=19,  # e.g., AWG 28
    )
    bare_d_mm = float(awg_df["직경(mm)"].iloc[row_index])
    wire_size_mm = bare_d_mm                   # treat as overall pitch
    enamel_thk_m = 0.0                         # no enamel column → 0
    st.caption(f"Wire Size (overall pitch): {wire_size_mm:.3f} mm (bare only)")

tab1 = st.container()

cores, rows_df = load_repo_cores()
if not cores:
    with tab1:
        st.info("리포지토리 CSV가 필요합니다. 파일을 프로젝트 루트에 두고 다시 실행하세요.")
        st.info("CSV 업로드를 기다리는 중…")
    st.stop()

# Override μr on cores from user input
cores = [replace(c, mu_r=mu_r_input) for c in cores]

# Build coils from defaults; apply absolute enamel thickness
coils = [
    Coil(
        name=f'AWG {awg_df["AWG"].iloc[row_index]} (static)',
        awg=0,
        wire_diameter_m=bare_d_mm / 1000.0,
        resistance_per_m_ohm=0.0,
        price_per_m_usd=0.0,
        packing_factor=0.68,
        base_price_usd=0.0,
        enamel_thickness_m=enamel_thk_m,
    )
]

# Compute options
opts = find_combinations(
    L_target_h=L_uH * 1e-6,
    cores=cores,
    coils=coils,
    tolerance=0.10,
    working_current_a=None,
)

# Show minimal result columns only
with tab1:
    st.subheader("설계 옵션 (Design Options)")
    if not opts:
        st.info("조건에 맞는 조합이 없습니다.")
    else:
        df = pd.DataFrame([{
            "코어 (Core)": d.core.name,
            "코일 (Coil)": d.coil.name,
            "턴수 (Turns)": d.turns,
            "윈도우 면적(mm²)": d.window_area_m2 * 1e6,
            "남은 면적(mm²)": d.leftover_window_area_m2 * 1e6,
            "필 비율(%)": d.fill_ratio * 100,
        } for d in opts[:3]])
        st.dataframe(df, use_container_width=True)

        st.markdown("### IWM 상세 계산 (행 선택)")
        labels = [f"{i}: {d.core.name} | {d.coil.name} | N={d.turns}" for i, d in enumerate(opts)]
        row_idx = st.selectbox("Select row", options=list(range(len(opts))), format_func=lambda i: labels[i], index=0)
        d = opts[int(row_idx)]

        # After-finish core dims (mm)
        core = d.core
        if getattr(core, "od_m", None) and getattr(core, "id_m", None) and getattr(core, "ht_m", None):
            OD_mm, ID_mm, HT_mm = core.od_m * 1e3, core.id_m * 1e3, core.ht_m * 1e3
        else:
            derived = core._derive_dimensions_from_fields() or (0.0, 0.0, 0.0)
            od_m, id_m, ht_m = derived
            OD_mm, ID_mm, HT_mm = od_m * 1e3, id_m * 1e3, ht_m * 1e3

        # Wire Size (overall, mm) = bare + 2*enamel
        wire_size_mm = (d.coil.wire_diameter_m + 2 * d.coil.enamel_thickness_m) * 1e3
        calc = iwm_calcs(OD_mm, ID_mm, HT_mm, d.turns, wire_size_mm)

        st.markdown("#### IWM details")
        st.write({
            "Core": d.core.name,
            "Coil": d.coil.name,
            "Turns": d.turns,
            "Wire Size (mm)": f"{wire_size_mm:.3f}",
            "Length per turn (mm)": calc["Length per turn (mm)"],
            "Total length (mm)": calc["Total length Millimetres"],
            "Total length (m)": calc["Total length Meters"],
            "Total length (ft)": calc["Total length Feet"],
            "Turns per layer (at pitch)": calc["Turns per layer at wire pitch"],
            "Number of layers": calc["Number of layers"],
            'Finished OD (mm)': calc['Theoretical Finished Outside Diameter "OD"'],
            'Finished ID (mm)': calc['Theoretical Finished Inner Diameter "ID"'],
            'Finished HT (mm)': calc['Theoretical Finished Height "HT"'],
        })

        # --- Custom core tweak (OD/ID/HT) -------------------------------
        from models import Core
        from math import ceil

        def _initial_layers(N: int, HT_mm: float, d_mm: float) -> int:
            tpl = max(1, int(HT_mm // d_mm))
            return max(1, ceil(N / tpl))

        def _bounds_from(N:int, d_mm:float, OD_mm:float, ID_mm:float, HT_mm:float, L_init:int|None=None):
            d_local = d_mm
            L_local = L_init or _initial_layers(N, HT_mm, d_local)
            HT_min_local = d_local * ceil(N / L_local)
            OD_min_local = ID_mm + 2 * L_local * d_local
            ID_min_local = 2 * (L_local + 1) * d_local
            return L_local, HT_min_local, OD_min_local, ID_min_local

        def _validate_feasible(N:int, d_mm:float, OD_mm:float, ID_mm:float, HT_mm:float, L:int) -> tuple[bool, str]:
            d_local = d_mm
            tpl_local = int(HT_mm // d_local)
            if tpl_local <= 0:
                return False, "HT too small (no turns per layer)."
            if (OD_mm - ID_mm)/2.0 < L * d_local:
                return False, "Radial thickness insufficient: increase OD or reduce ID or increase L."
            if tpl_local * L < N:
                return False, "Turns capacity too low: increase HT or L."
            return True, "OK"

        def _iwm_finished(OD_mm:float, ID_mm:float, HT_mm:float, L:int, d_mm:float) -> tuple[float,float,float]:
            return (
                round(OD_mm + 2*L*d_mm, 3),
                round(ID_mm - 2*L*d_mm, 3),
                round(HT_mm + 2*L*d_mm, 3),
            )

        def _window_fill_from_capacity(N:int, HT_mm:float, d_mm:float, L:int) -> float:
            tpl_local = max(1, int(HT_mm // d_mm))
            cap_local = tpl_local * L
            if cap_local <= 0:
                return 0.0
            return min(1.0, N / cap_local)

        with st.expander("Custom core (OD/ID/HT tweak)"):
            N_sel = int(d.turns)
            wire_size_mm_sel = wire_size_mm
            base_OD_mm, base_ID_mm, base_HT_mm = OD_mm, ID_mm, HT_mm

            L_default = _initial_layers(N_sel, base_HT_mm, wire_size_mm_sel)
            L_ui = st.number_input("Layers (L)", min_value=1, max_value=999, value=L_default, step=1)

            L_eff, HT_min, OD_min, ID_min = _bounds_from(N_sel, wire_size_mm_sel, base_OD_mm, base_ID_mm, base_HT_mm, L_ui)
            HT_ui = st.slider("HT (mm)", min_value=float(HT_min), max_value=float(HT_min + 20*wire_size_mm_sel), value=float(max(base_HT_mm, HT_min)), step=0.01)
            ID_ui = st.slider("ID (mm)", min_value=float(ID_min), max_value=float(max(ID_min + 20*wire_size_mm_sel, base_ID_mm)), value=float(max(base_ID_mm, ID_min)), step=0.01)
            OD_ui = st.slider("OD (mm)", min_value=float(OD_min), max_value=float(max(OD_min + 40*wire_size_mm_sel, base_OD_mm)), value=float(max(base_OD_mm, OD_min)), step=0.01)

            ok, msg = _validate_feasible(N_sel, wire_size_mm_sel, OD_ui, ID_ui, HT_ui, L_eff)
            st.write(f"Feasibility: {msg}")

            ODf_mm, IDf_mm, HTf_mm = _iwm_finished(OD_ui, ID_ui, HT_ui, L_eff, wire_size_mm_sel)
            st.write({
                "Wire Size (mm)": f"{wire_size_mm_sel:.3f}",
                "Turns per layer (floor(HT/d))": int(HT_ui // wire_size_mm_sel),
                "Capacity (TPL*L)": int(HT_ui // wire_size_mm_sel) * L_eff,
                "Finished OD (mm)": ODf_mm,
                "Finished ID (mm)": IDf_mm,
                "Finished HT (mm)": HTf_mm,
            })

            fill = _window_fill_from_capacity(N_sel, HT_ui, wire_size_mm_sel, L_eff)
            st.write({
                "윈도우 면적(mm²)": round((math.pi * (ID_ui/2)**2), 3),
                "남은 면적(mm²) (capacity model)": "—",
                "필 비율(%) (capacity)": round(fill * 100.0, 2),
            })

            if st.button("Preview with custom core"):
                area_m2 = ((OD_ui - ID_ui)/2/1e3) * (HT_ui/1e3)
                r_mean_m = (OD_ui + ID_ui) / 4e3
                window_area_m2 = math.pi * (ID_ui/2/1e3)**2
                custom_core = Core(
                    name=f"Custom {OD_ui:.2f}/{ID_ui:.2f}/{HT_ui:.2f} mm",
                    mu_r=core.mu_r,
                    area_m2=area_m2,
                    r_mean_m=r_mean_m,
                    window_area_m2=window_area_m2,
                    b_sat_t=core.b_sat_t,
                    price_usd=0.0,
                    od_m=OD_ui/1e3, id_m=ID_ui/1e3, ht_m=HT_ui/1e3,
                )
                preview = find_combinations(
                    L_target_h=L_uH*1e-6,
                    cores=[custom_core],
                    coils=[d.coil],
                    tolerance=0.10,
                    working_current_a=None,
                )
                if preview:
                    p = preview[0]
                    st.success(f"Preview → Core={p.core.name} | Coil={p.coil.name} | N={p.turns} | 필 비율={p.fill_ratio*100:.2f}%")
                else:
                    st.warning("No viable combination for the custom core with current inputs.")

