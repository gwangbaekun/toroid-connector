import io
import tempfile
from dataclasses import replace
import pandas as pd
import streamlit as st

from import_csv import cores_from_high_flux_csv, _parse_csv_rows
from data import COILS, CORES
from search import find_combinations


st.set_page_config(page_title="토로이드 코일 설계", layout="wide")
st.title("토로이드 코일 설계 프로그램")

with st.sidebar:
    st.header("입력 (Inputs)")
    data_source = st.radio("데이터 소스 (Data Source)", ["내장 데이터 (data.py)", "CSV 업로드 (Upload CSV)"], index=0)
    uploaded = None
    if data_source == "CSV 업로드 (Upload CSV)":
        uploaded = st.file_uploader("High Flux GT Cores CSV 업로드", type=["csv"]) 
    L_uH = st.number_input("목표 인덕턴스 (Target Inductance, µH)", min_value=0.1, value=250.0, step=10.0)
    tol_pc = st.slider("허용오차 (Tolerance, ±%)", min_value=1, max_value=50, value=10)
    I_amp = st.number_input("동작 전류 (Working Current, A)", min_value=0.0, value=0.5, step=0.1)
    top_k = st.slider("상위 K 결과 (Top K results)", min_value=1, max_value=100, value=20)

    st.header("코어 필터 (Core Filters)")
    min_id_mm = st.number_input("코어 내경 최소 (Min ID, mm)", min_value=0.0, value=0.0, step=1.0)
    max_id_mm = st.number_input("코어 내경 최대 (Max ID, mm)", min_value=0.0, value=999.0, step=1.0)
    require_id = st.checkbox("내경 값 없는 코어 제외 (Require ID present)", value=False)

    st.header("코일 옵션 (Coil Options)")
    coil_names = [c.name for c in COILS]
    selected_coils = st.multiselect("코일 선택 (Select coils)", coil_names, default=coil_names)
    enamel_scale = st.number_input("에나멜 두께 배율 (Enamel thickness scale)", min_value=0.0, value=1.0, step=0.1)

tab1, tab2 = st.tabs(["결과 (Results)", "CSV 미리보기 (Preview)"]) 

cores = []
rows_df = None

if data_source == "내장 데이터 (data.py)":
    cores = CORES
    # Simple preview of built-in cores
    rows_df = pd.DataFrame([{
        "코어 이름 (name)": c.name,
        "상대 투자율 (mu_r)": c.mu_r,
        "유효 단면적 (area_m2)": c.area_m2,
        "평균 반경 (r_mean_m)": c.r_mean_m,
        "외경 (OD_m)": getattr(c, "od_m", None),
        "내경 (ID_m)": getattr(c, "id_m", None),
        "높이 (HT_m)": getattr(c, "ht_m", None),
    } for c in cores])
else:
    if uploaded is not None:
        content = uploaded.read()
        with tempfile.NamedTemporaryFile(delete=True, suffix=".csv") as tmp:
            tmp.write(content)
            tmp.flush()
            # Preview rows
            rows = _parse_csv_rows(tmp.name)
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
            # Build cores for computation
            cores = cores_from_high_flux_csv(tmp.name)

if cores:
    # Apply core ID filters
    def core_passes_filters(c):
        id_m = getattr(c, "id_m", None)
        if id_m is None:
            return not require_id
        id_mm = id_m * 1e3
        return (id_mm >= min_id_mm) and (id_mm <= max_id_mm)

    cores = [c for c in cores if core_passes_filters(c)]

    # Build coil list with enamel scale applied
    name_to_coil = {c.name: c for c in COILS}
    coils = []
    for name in selected_coils:
        base = name_to_coil.get(name)
        if base is None:
            continue
        coils.append(replace(base, enamel_thickness_m=base.enamel_thickness_m * enamel_scale))

    if not coils:
        st.warning("No coils selected. Please choose at least one coil.")
        opts = []
    else:
        opts = find_combinations(
            L_target_h=L_uH*1e-6,
            cores=cores,
            coils=coils,
            tolerance=tol_pc/100.0,
            working_current_a=I_amp,
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
        st.info("사이드바에서 CSV를 업로드하거나 내장 데이터를 사용해 계산하세요.")
    with tab2:
        st.info("CSV 업로드를 기다리는 중…")


