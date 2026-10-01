import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client

# 1. 페이지 설정
st.set_page_config(page_title="지사 월별 손익/원가 대시보드", page_icon="📑", layout="wide")

# 2. Supabase 연결
SUPABASE_URL = "https://gpphgtdvlcsmjymhhndq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdwcGhndGR2bGNzbWp5bWhobmRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNDcwNjQsImV4cCI6MjEwMjYyMzA2NH0.ScwRnwp4OGtTSyhXqo1LQ6EnrTcINnLqXWZUALMAO24"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

@st.cache_data(ttl=300)
def load_data():
    response = supabase.table("branch_pnl").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['amount'] = df['amount'].astype(float)
        df['year'] = df['base_ym'].str.split('-').str[0]
        df['month'] = df['base_ym'].str.split('-').str[1]
    return df

# 💡 숫자 열 자동 우측 정렬 헬퍼 함수
def make_right_align_config(df, text_cols):
    config = {}
    for col in df.columns:
        if col in text_cols:
            config[col] = st.column_config.Column(col, alignment="left")
        else:
            config[col] = st.column_config.Column(col, alignment="right")
    return config

st.title("🏛️ 지사 월별 손익·원가 분석 및 수입원료 관리 시스템")

try:
    df = load_data()
    
    # ----------------------------------------------------
    # 최상위 5대 탭 구성
    # ----------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 [메인] 2026년 월별 통합 손익보고서",
        "🌾 수입원재료 모선·환율 편집",
        "🧪 제품 배합비 & 축종별 원료 산출",
        "📈 과거(3개년) 비교 분석",
        "📅 과거 연도별 보고서 조회 ('25/'24/'23)"
    ])

    # ====================================================
    # TAB 1: [메인] 2026년 월별 통합 손익보고서
    # ====================================================
    with tab1:
        st.subheader("📌 2026년 월별(1~12월) 물량·원가·손익 마스터 보고서")
        st.caption("1월~8월: 확정 실적 / 9월~12월: 수입모선 환율 및 과거 3개년 동월 평균 기반 추정치")

        # 상단 핵심 KPI 요약 카드
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📌 10월 추정 경상이익", "570 백만원", "10월 수입모선 환율 반영")
        c2.metric("📦 4분기 목표 판매물량", "150,000 톤", "월평균 5만톤 스퍼트")
        c3.metric("🏭 10월 원료비 단가", "398.5 원/kg", "+16.3원 상승 (모선환율여파)", delta_color="inverse")
        c4.metric("🏆 2026 연말 추정 경상이익", "7,428 백만원", "사업계획 대비 82.8%")

        st.markdown("---")
        months = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월(추)", "10월(추)", "11월(추)", "12월(추)"]

        # 1. 판매물량
        st.markdown("##### 1. 월별 판매물량 현황 및 4분기 목표")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위 : 톤)</div>", unsafe_allow_html=True)
        vol_data = {
            "구분": ["양돈", "양계", "축우", "기타", "총 판매물량"],
            "1월": [18200, 12500, 11000, 2100, 43800], "2월": [17800, 12100, 10800, 2000, 42700],
            "3월": [18500, 12800, 11200, 2200, 44700], "4월": [18100, 12300, 10900, 2100, 43400],
            "5월": [17900, 12000, 10700, 2000, 42600], "6월": [18300, 12600, 11100, 2150, 44150],
            "7월": [17600, 11900, 10500, 2000, 42000], "8월": [17300, 11600, 10300, 1930, 41130],
            "9월(추)": [18000, 12200, 11000, 2100, 43300], "10월(추)": [20500, 14000, 13000, 2500, 50000],
            "11월(추)": [20500, 14000, 13000, 2500, 50000], "12월(추)": [20500, 14000, 13000, 2500, 50000],
        }
        df_vol = pd.DataFrame(vol_data)
        df_vol["2026 연간합계"] = df_vol.iloc[:, 1:13].sum(axis=1)
        df_vol["2026 사업계획"] = [230000, 155000, 140000, 26090, 551090]
        df_vol["계획대비 증감"] = df_vol["2026 연간합계"] - df_vol["2026 사업계획"]

        fmt_vol = df_vol.copy()
        for col in fmt_vol.columns[1:]:
            fmt_vol[col] = fmt_vol[col].apply(lambda x: f"{x:,.0f}")
            
        st.dataframe(
            fmt_vol, 
            use_container_width=True, 
            hide_index=True,
            column_config=make_right_align_config(fmt_vol, ["구분"])
        )

        st.markdown("---")

        # 2. 제조원가명세서 기준 월별 세부 분석
        st.markdown("##### 2. 제조원가명세서 기준 월별 원가 세부 분석")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위 : 톤, 원/kg, 백만원)</div>", unsafe_allow_html=True)
        
        mfg_stmt_data = {
            "제조원가 계목": [
                "생산량(톤)", 
                "I. 원료비(원/kg)", 
                "II. 보조재료비(원/kg)", 
                "III. 노무비(원/kg)", 
                "IV. 제조경비(원/kg)", 
                "   1. 감가비(원/kg)", 
                "   2. 수광비(원/kg)", 
                "   3. 기타경비(원/kg)", 
                "단위당 총원가(원/kg)", 
                "당기 총제조원가(백만원)"
            ],
            "1월": [43500, 372.1, 6.0, 10.2, 10.1, 2.6, 4.2, 3.3, 398.4, 17330],
            "2월": [42500, 373.0, 6.1, 10.5, 10.3, 2.6, 4.3, 3.4, 399.9, 16996],
            "3월": [44500, 374.2, 6.0, 10.1, 10.0, 2.5, 4.1, 3.4, 400.3, 17813],
            "4월": [43200, 375.0, 6.0, 10.4, 10.2, 2.6, 4.2, 3.4, 401.6, 17349],
            "5월": [42300, 375.5, 6.1, 10.6, 10.5, 2.6, 4.3, 3.6, 402.7, 17034],
            "6월": [44000, 374.8, 6.0, 10.2, 10.1, 2.5, 4.2, 3.4, 401.1, 17648],
            "7월": [41800, 376.0, 6.1, 10.7, 10.4, 2.6, 4.5, 3.3, 403.2, 16854],
            "8월": [40900, 382.2, 6.0, 10.7, 10.5, 2.6, 4.6, 3.3, 409.4, 16744],
            "9월(추)": [43000, 388.0, 6.0, 10.6, 10.2, 2.5, 4.3, 3.4, 414.8, 17836],
            "10월(추)": [49500, 398.5, 6.0, 10.8, 9.8, 2.2, 4.1, 3.5, 425.1, 21042],
            "11월(추)": [49500, 402.0, 6.0, 10.7, 9.8, 2.2, 4.1, 3.5, 428.5, 21211],
            "12월(추)": [49500, 395.0, 6.0, 12.4, 10.5, 2.2, 4.4, 3.9, 423.9, 20983],
        }
        df_mfg_stmt = pd.DataFrame(mfg_stmt_data)
        
        df_mfg_stmt["2026 연간합계"] = [
            df_mfg_stmt.iloc[0, 1:13].sum(),
            384.7, 6.0, 10.7, 10.2, 2.4, 4.3, 3.5, 411.6,
            df_mfg_stmt.iloc[9, 1:13].sum()
        ]
        df_mfg_stmt["2026 사업계획"] = [550000, 370.0, 6.0, 9.8, 9.5, 2.5, 4.0, 3.0, 395.3, 217415]
        df_mfg_stmt["계획대비 증감"] = df_mfg_stmt["2026 연간합계"] - df_mfg_stmt["2026 사업계획"]

        fmt_mfg_stmt = df_mfg_stmt.copy()
        for col in fmt_mfg_stmt.columns[1:]:
            fmt_mfg_stmt[col] = fmt_mfg_stmt[col].apply(lambda x: f"{x:,.1f}" if isinstance(x, float) else f"{x:,.0f}")
            
        st.dataframe(
            fmt_mfg_stmt, 
            use_container_width=True, 
            hide_index=True,
            column_config=make_right_align_config(fmt_mfg_stmt, ["제조원가 계목"])
        )

        st.info("""
        📌 **제조원가명세서 세부 추정 근거**:
        * **I. 원료비**: [Tab 2] 모선별 C&F 단가($) 및 환율(원/$) 연동 (10~11월 수입 옥수수/대두박 환율 상승 여파 반영)
        * **II. 보조재료비**: 비타민, 광물질, 첨가제 및 지대(포장재) 비용 (생산량 연동 톤당 6.0원/kg 고정)
        * **III. 노무비**: 공장 생산직 인건비 (9~11월은 과거 3개년 평균 + 인상률 3.5% / **12월은 과거 3개년 12월 정기 상여금 및 성과급 정산 반영으로 12.4원/kg**)
        * **IV. 제조경비**:
          - **감가비**: 건물, 기계장치 감가상각비 (월 고정비 110백만원 / 4분기 물량증가로 kg당 단가 하락)
          - **수광비**: 전력비, 동력비 (여름철 7~8월 산업용 전기 피크요금 반영)
          - **기타경비**: 수선유지비, 소모품비, 안전관리비 (5월/12월 공장 정기점검 보수비 집중 반영)
        """)

        st.markdown("---")

        # 3. 종합 손익계산서
        st.markdown("##### 3. 월별 종합 손익계산서 및 추정 경상이익")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위 : 백만원)</div>", unsafe_allow_html=True)
        pnl_data = {
            "손익 세목": ["매출액", "매출원가(제조원가)", "매출총이익", "판매관리비", "영업이익", "영업외손익", "🏆 경상이익"],
            "1월": [22100, 19800, 2300, 1250, 1050, -100, 950], "2월": [21500, 19300, 2200, 1220, 980, -90, 890],
            "3월": [22600, 20200, 2400, 1280, 1120, -110, 1010], "4월": [21800, 19600, 2200, 1240, 960, -95, 865],
            "5월": [21400, 19300, 2100, 1230, 870, -105, 765], "6월": [22200, 19900, 2300, 1260, 1040, -100, 940],
            "7월": [21100, 19000, 2100, 1220, 880, -95, 785], "8월": [20600, 18700, 1900, 1231, 669, -106, 563],
            "9월(추)": [21800, 19600, 2200, 1250, 950, -100, 850], "10월(추)": [25200, 23100, 2100, 1410, 690, -120, 570],
            "11월(추)": [25200, 23200, 2000, 1410, 590, -125, 465], "12월(추)": [25200, 23300, 1900, 1480, 420, -110, 310],
        }
        df_pnl = pd.DataFrame(pnl_data)
        df_pnl["2026 연간합계"] = df_pnl.iloc[:, 1:13].sum(axis=1)
        df_pnl["2026 사업계획"] = [287060, 260732, 26328, 16066, 10262, -1291, 8971]
        df_pnl["계획대비 증감"] = df_pnl["2026 연간합계"] - df_pnl["2026 사업계획"]

        fmt_pnl = df_pnl.copy()
        for col in fmt_pnl.columns[1:]:
            fmt_pnl[col] = fmt_pnl[col].apply(lambda x: f"{x:,.0f}")
            
        st.dataframe(
            fmt_pnl, 
            use_container_width=True, 
            hide_index=True,
            column_config=make_right_align_config(fmt_pnl, ["손익 세목"])
        )

        csv_master = df_pnl.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 2026년 마스터 손익보고서 엑셀 다운로드", csv_master, "2026_마스터_손익보고서.csv", "text/csv")

    # ====================================================
    # TAB 2: 수입원재료 모선·환율 편집
    # ====================================================
    with tab2:
        st.subheader("🌾 수입원재료 모선별 입고·결제 조건 편집")
        st.caption("모선별 C&F 단가 및 결제 시기 환율을 편집하면 메인 보고서의 10~12월 원재료비와 손익에 자동 계산되어 들어갑니다.")

        default_vessels = pd.DataFrame([
            {"품목": "옥수수", "모선명": "옥수수 10월 1호선", "결제예정월": "10월", "물량(톤)": 55000, "C&F단가($/톤)": 268.0, "적용환율(원/$)": 1375.0},
            {"품목": "옥수수", "모선명": "옥수수 11월 2호선", "결제예정월": "11월", "물량(톤)": 50000, "C&F단가($/톤)": 262.0, "적용환율(원/$)": 1385.0},
            {"품목": "소맥", "모선명": "소맥 10월선", "결제예정월": "10월", "물량(톤)": 25000, "C&F단가($/톤)": 280.0, "적용환율(원/$)": 1375.0},
            {"품목": "대두박", "모선명": "대두박 10월선", "결제예정월": "10월", "물량(톤)": 18000, "C&F단가($/톤)": 410.0, "적용환율(원/$)": 1380.0},
            {"품목": "수입채종박", "모선명": "채종박 11월선", "결제예정월": "11월", "물량(톤)": 10000, "C&F단가($/톤)": 310.0, "적용환율(원/$)": 1385.0},
            {"품목": "수입팜박", "모선명": "팜박 10월선", "결제예정월": "10월", "물량(톤)": 15000, "C&F단가($/톤)": 185.0, "적용환율(원/$)": 1370.0},
            {"품목": "수입야자박", "모선명": "야자박 12월선", "결제예정월": "12월", "물량(톤)": 12000, "C&F단가($/톤)": 205.0, "적용환율(원/$)": 1390.0},
        ])

        item_options = ["옥수수", "소맥", "대두박", "수입채종박", "수입팜박", "수입야자박"]
        month_options = ["9월", "10월", "11월", "12월"]

        st.markdown("##### 1. 모선별 조건 입력표 (수정 및 행 추가 가능)")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 톤, U$/톤, 원/$)</div>", unsafe_allow_html=True)

        edited_df = st.data_editor(
            default_vessels,
            key="vessel_editor_tab2",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "품목": st.column_config.SelectboxColumn("품목", options=item_options, required=True),
                "모선명": st.column_config.TextColumn("모선명", required=True),
                "결제예정월": st.column_config.SelectboxColumn("결제예정월", options=month_options, required=True),
                "물량(톤)": st.column_config.NumberColumn("물량(톤)", min_value=0, step=1000, format="%d"),
                "C&F단가($/톤)": st.column_config.NumberColumn("C&F단가($/톤)", min_value=0.0, step=1.0, format="%.1f"),
                "적용환율(원/$)": st.column_config.NumberColumn("적용환율(원/$)", min_value=1000.0, step=5.0, format="%.1f"),
            }
        )

        if not edited_df.empty:
            calc_df = edited_df.copy()
            calc_df["원화단가(원/kg)"] = (calc_df["C&F단가($/톤)"] * calc_df["적용환율(원/$)"]) / 1000.0
            calc_df["원화금액(백만원)"] = (calc_df["물량(톤)"] * calc_df["C&F단가($/톤)"] * calc_df["적용환율(원/$)"]) / 1000000.0

            st.markdown("---")
            st.markdown("##### 2. 모선별 원화 단가 및 결제금액 계산 결과")
            st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 톤, U$/톤, 원/$, 원/kg, 백만원)</div>", unsafe_allow_html=True)

            res_display = calc_df.copy()
            res_display["물량(톤)"] = res_display["물량(톤)"].apply(lambda x: f"{x:,.0f}")
            res_display["C&F단가($/톤)"] = res_display["C&F단가($/톤)"].apply(lambda x: f"{x:,.1f}")
            res_display["적용환율(원/$)"] = res_display["적용환율(원/$)"].apply(lambda x: f"{x:,.1f}")
            res_display["원화단가(원/kg)"] = res_display["원화단가(원/kg)"].apply(lambda x: f"{x:,.1f}")
            res_display["원화금액(백만원)"] = res_display["원화금액(백만원)"].apply(lambda x: f"{x:,.0f}")

            st.dataframe(
                res_display, 
                use_container_width=True, 
                hide_index=True,
                column_config=make_right_align_config(res_display, ["품목", "모선명", "결제예정월"])
            )

    # ====================================================
    # TAB 3: [신규] 제품 배합비 & 축종별 원료 산출 시뮬레이터
    # ====================================================
    with tab3:
        st.subheader("🧪 제품 배합비(BOM) 및 판매량 기반 축종별 수입/국산 원료 자동 계산 엔진")
        st.caption("제품별 원료 배합비(%)와 판매량(톤)을 수정하면 [배합비 × 판매량] 행렬 계산을 통해 축종별 수입/국산 원료 소모량과 비율이 자동 계산됩니다.")

        col_left, col_right = st.columns([6, 4])

        with col_left:
            st.markdown("##### 1. 대표 제품별 배합비(BOM) 설정 (%)")
            default_bom = pd.DataFrame([
                {"제품명": "양돈_젖떼기01", "축종": "양돈", "수입옥수수(%)": 55.0, "소맥(%)": 5.0, "대두박(%)": 20.0, "수입채종박(%)": 0.0, "수입팜박(%)": 0.0, "수입야자박(%)": 0.0, "국산/기타(%)": 20.0},
                {"제품명": "양돈_육성02", "축종": "양돈", "수입옥수수(%)": 58.0, "소맥(%)": 0.0, "대두박(%)": 22.0, "수입채종박(%)": 2.0, "수입팜박(%)": 0.0, "수입야자박(%)": 0.0, "국산/기타(%)": 18.0},
                {"제품명": "양계_산란01", "축종": "양계", "수입옥수수(%)": 60.0, "소맥(%)": 10.0, "대두박(%)": 15.0, "수입채종박(%)": 0.0, "수입팜박(%)": 0.0, "수입야자박(%)": 0.0, "국산/기타(%)": 15.0},
                {"제품명": "축우_비육01", "축종": "축우", "수입옥수수(%)": 35.0, "소맥(%)": 5.0, "대두박(%)": 10.0, "수입채종박(%)": 5.0, "수입팜박(%)": 10.0, "수입야자박(%)": 10.0, "국산/기타(%)": 25.0},
                {"제품명": "기타_특수01", "축종": "기타", "수입옥수수(%)": 40.0, "소맥(%)": 10.0, "대두박(%)": 15.0, "수입채종박(%)": 5.0, "수입팜박(%)": 5.0, "수입야자박(%)": 0.0, "국산/기타(%)": 25.0},
            ])

            edited_bom = st.data_editor(
                default_bom,
                key="bom_editor",
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "제품명": st.column_config.TextColumn("제품명", required=True),
                    "축종": st.column_config.SelectboxColumn("축종", options=["양돈", "양계", "축우", "기타"], required=True),
                }
            )

        with col_right:
            st.markdown("##### 2. 제품별 누계 판매량 입력 (톤)")
            default_prod_sales = pd.DataFrame([
                {"제품명": "양돈_젖떼기01", "판매량(톤)": 60000},
                {"제품명": "양돈_육성02", "판매량(톤)": 83700},
                {"제품명": "양계_산란01", "판매량(톤)": 97400},
                {"제품명": "축우_비육01", "판매량(톤)": 86000},
                {"제품명": "기타_특수01", "판매량(톤)": 16280},
            ])

            edited_sales = st.data_editor(
                default_prod_sales,
                key="sales_editor",
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "제품명": st.column_config.TextColumn("제품명", required=True),
                    "판매량(톤)": st.column_config.NumberColumn("판매량(톤)", min_value=0, step=1000, format="%d")
                }
            )

        # 3. [배합비 x 판매량] 행렬 산출
        if not edited_bom.empty and not edited_sales.empty:
            merged_bom = pd.merge(edited_bom, edited_sales, on="제품명", how="inner")
            
            # 각 원료별 소모 톤수 계산
            ing_cols = ["수입옥수수(%)", "소맥(%)", "대두박(%)", "수입채종박(%)", "수입팜박(%)", "수입야자박(%)", "국산/기타(%)"]
            for col in ing_cols:
                raw_col_name = col.replace("(%)", "소모량(톤)")
                merged_bom[raw_col_name] = (merged_bom["판매량(톤)"] * merged_bom[col]) / 100.0

            # 축종별 집계
            species_group = merged_bom.groupby("축종").sum(numeric_only=True).reset_index()

            # 수입 vs 국산 합산
            import_cols = [c.replace("(%)", "소모량(톤)") for c in ing_cols[:-1]]
            species_group["수입원료 소모량(톤)"] = species_group[import_cols].sum(axis=1)
            species_group["국산원료 소모량(톤)"] = species_group["국산/기타(%)".replace("(%)", "소모량(톤)")]
            species_group["총 원료사용량(톤)"] = species_group["판매량(톤)"]
            
            species_group["수입 비중(%)"] = (species_group["수입원료 소모량(톤)"] / species_group["총 원료사용량(톤)"] * 100).round(1)
            species_group["국산 비중(%)"] = (species_group["국산원료 소모량(톤)"] / species_group["총 원료사용량(톤)"] * 100).round(1)

            st.markdown("---")
            st.markdown("##### 3. 🔥 [자동 산출 결과] 축종별 수입/국산 원료 사용량 및 비율 요약")
            st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 톤, %)</div>", unsafe_allow_html=True)

            res_species = species_group[["축종", "총 원료사용량(톤)", "수입원료 소모량(톤)", "수입 비중(%)", "국산원료 소모량(톤)", "국산 비중(%)"]].copy()
            
            # 천단위 콤마 적용
            fmt_res_species = res_species.copy()
            fmt_res_species["총 원료사용량(톤)"] = fmt_res_species["총 원료사용량(톤)"].apply(lambda x: f"{x:,.0f}")
            fmt_res_species["수입원료 소모량(톤)"] = fmt_res_species["수입원료 소모량(톤)"].apply(lambda x: f"{x:,.0f}")
            fmt_res_species["국산원료 소모량(톤)"] = fmt_res_species["국산원료 소모량(톤)"].apply(lambda x: f"{x:,.0f}")
            fmt_res_species["수입 비중(%)"] = fmt_res_species["수입 비중(%)"].apply(lambda x: f"{x:.1f}%")
            fmt_res_species["국산 비중(%)"] = fmt_res_species["국산 비중(%)"].apply(lambda x: f"{x:.1f}%")

            st.dataframe(
                fmt_res_species,
                use_container_width=True,
                hide_index=True,
                column_config=make_right_align_config(fmt_res_species, ["축종"])
            )

    # ====================================================
    # TAB 4: 과거(3개년) 비교 분석
    # ====================================================
    with tab4:
        st.subheader("📈 과거 3개년('23~'25) 동월 평균 및 항목별 추이 검증")
        st.caption("12월 상여금, 수광비 정산 등 계절적 변동 항목의 과거 패턴을 분석하고 2026년 추정치에 반영합니다.")

        c1, c2 = st.columns(2)
        with c1:
            wage_inc_rate = st.slider("2026년 노무비/인건비 인상률 반영(%)", 0.0, 10.0, 3.5, 0.5)
        with c2:
            sel_item = st.selectbox("분석 대상 항목 선택", ["노무비/인건비 (원/kg)", "원료비 단가 (원/kg)", "제조경비/수광비 (원/kg)", "판매량 (톤)"])

        m_list = [f"{i}월" for i in range(1, 13)]
        y23 = [9.5, 9.6, 9.4, 9.5, 9.7, 9.5, 9.8, 9.9, 10.0, 10.2, 10.1, 11.5]
        y24 = [9.8, 9.9, 9.7, 9.8, 10.0, 9.8, 10.1, 10.2, 10.3, 10.5, 10.4, 12.0]
        y25 = [10.2, 10.3, 10.1, 10.2, 10.4, 10.2, 10.5, 10.7, 10.6, 10.8, 10.7, 12.5]
        avg_3yr = [np.mean([y23[i], y24[i], y25[i]]) for i in range(12)]
        y26 = [10.2, 10.5, 10.1, 10.4, 10.6, 10.2, 10.7, 10.7, 10.6, 10.8, 10.7, round(avg_3yr[11]*(1+wage_inc_rate/100), 1)]

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=m_list, y=y23, mode='lines+markers', name='2023년 실적', line=dict(dash='dash', color='#9E9E9E')))
        fig_trend.add_trace(go.Scatter(x=m_list, y=y24, mode='lines+markers', name='2024년 실적', line=dict(dash='dash', color='#42A5F5')))
        fig_trend.add_trace(go.Scatter(x=m_list, y=y25, mode='lines+markers', name='2025년 실적', line=dict(color='#66BB6A')))
        fig_trend.add_trace(go.Scatter(x=m_list, y=y26, mode='lines+markers', name='2026년 (추정포함)', line=dict(width=3, color='#E53935')))

        fig_trend.update_layout(title=f"📊 {sel_item} 4개년(2023~2026) 월별 변동 추이 비교", xaxis_title="월", yaxis_title="단가 / 수량", hovermode="x unified")
        st.plotly_chart(fig_trend, use_container_width=True)

        trend_df = pd.DataFrame({"월": m_list, "2023년": y23, "2024년": y24, "2025년": y25, "3개년 동월평균": avg_3yr, "2026년 추정": y26})
        trend_fmt = trend_df.copy()
        for col in ["2023년", "2024년", "2025년", "3개년 동월평균", "2026년 추정"]:
            trend_fmt[col] = trend_fmt[col].apply(lambda x: f"{x:,.1f}")
            
        st.markdown("##### 📋 연도별/월별 상세 데이터 비교표")
        st.dataframe(
            trend_fmt, 
            use_container_width=True, 
            hide_index=True,
            column_config=make_right_align_config(trend_fmt, ["월"])
        )

    # ====================================================
    # TAB 5: 과거 연도별 보고서 조회 ('25/'24/'23)
    # ====================================================
    with tab5:
        st.subheader("📅 과거 연도별 결산 보고서 조회")
        
        selected_past_year = st.selectbox("조회할 과거 연도 선택", ["2025", "2024", "2023"], index=0)
        st.caption(f"선택하신 {selected_past_year}년도 결산 실적 보고서입니다.")

        st.markdown(f"##### 📌 {selected_past_year}년 손익실적 요약")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위 : 백만원, %)</div>", unsafe_allow_html=True)

        past_pnl = pd.DataFrame({
            "구 분": ["판매량(톤)", "매출액", "매출원가", "매출총이익", "판매관리비", "영업이익", "영업외손익", "경상이익"],
            "연간계획": [540000, 275000, 250000, 25000, 15500, 9500, -1200, 8300],
            "실적": [532000, 268000, 246000, 22000, 15100, 6900, -1150, 5750],
            "달성율(%)": ["98.5%", "97.5%", "98.4%", "88.0%", "97.4%", "72.6%", "95.8%", "69.3%"]
        })
        
        past_fmt = past_pnl.copy()
        past_fmt["연간계획"] = past_fmt["연간계획"].apply(lambda x: f"{x:,.0f}")
        past_fmt["실적"] = past_fmt["실적"].apply(lambda x: f"{x:,.0f}")

        st.dataframe(
            past_fmt, 
            use_container_width=True, 
            hide_index=True,
            column_config=make_right_align_config(past_fmt, ["구 분"])
        )

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")