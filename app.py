import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# 1. 페이지 설정
st.set_page_config(page_title="지사 손익실적 및 제조/판관비 분석 시스템", page_icon="📑", layout="wide")

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
        df['amount'] = df['amount'].astype(int)
        df['year'] = df['base_ym'].str.split('-').str[0]
        df['month'] = df['base_ym'].str.split('-').str[1]
    return df

st.title("📑 지사 손익실적 및 제조원가/판관비 분석 (임원 보고용)")

try:
    df = load_data()
   
    # --- 사이드바 설정 ---
    st.sidebar.header("⚙️ 보고서 기준 설정")
    selected_branch = st.sidebar.selectbox("지사 선택", df['branch'].unique() if not df.empty else ["충청지사"])
    selected_year = st.sidebar.selectbox("기준 연도", ["2026", "2025"], index=0)
    selected_month = st.sidebar.slider("기준 월 (누계)", 1, 12, 8)

    tab1, tab2, tab3 = st.tabs(["나. 손익실적 (경상이익)", "다. 제조원가 및 판관비 분석 (원/kg)", "라. 주원료 가격추이 & 4분기 시뮬레이션"])

    # ==========================================
    # TAB 1: 손익실적 (보고서 '나' 양식)
    # ==========================================
    with tab1:
        st.subheader(f"📌 손익실적 요약 ({selected_branch} {selected_month}월 누계)")
        st.caption("단위 : 백만원, %, 톤")

        # 양식 기반 샘플/DB 결합 데이터셋 (백만원 단위)
        pnl_data = {
            "구 분": ["판매량(톤)", "매출액", "매출원가", "매출총이익", "판매관리비", "영업이익", "영업외손익", "경상이익(배분전)"],
            "연간계획": [551090, 287060, 260732, 26328, 16066, 10262, -1291, 8971],
            "계획(A)": [364330, 189418, 172045, 17373, 11567, 5806, -729, 5077],
            "실적(B)": [342580, 168193, 155004, 13188, 9931, 3257, -801, 2456],
            "전년동기(C)": [366346, 175910, 159933, 15977, 9841, 6136, -725, 5411]
        }
       
        pnl_df = pd.DataFrame(pnl_data)
        pnl_df["증감(B-A)"] = pnl_df["실적(B)"] - pnl_df["계획(A)"]
        pnl_df["달성율(B/A)"] = (pnl_df["실적(B)"] / pnl_df["계획(A)"] * 100).round(1).astype(str) + "%"
        pnl_df["증감(B-C)"] = pnl_df["실적(B)"] - pnl_df["전년동기(C)"]

        # 열 순서 양식과 동일하게 배치
        cols_order = ["구 분", "연간계획", "계획(A)", "실적(B)", "증감(B-A)", "달성율(B/A)", "전년동기(C)", "증감(B-C)"]
        st.dataframe(pnl_df[cols_order], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🟢 월별 경상이익 추이 (공통관리비 배분 전/후)")
        monthly_ord = pd.DataFrame({
            "구분": ["배분 전 경상이익", "배분 후 경상이익"],
            "1월": [10.8, 3.8], "2월": [3.7, 1.2], "3월": [7.5, 4.8], "4월": [0.4, -1.2],
            "5월": [-2.8, -6.3], "6월": [4.2, 4.6], "7월": [1.7, 1.6], "8월": [-0.9, -3.6], "누계": [24.6, 4.9]
        })
        st.dataframe(monthly_ord, use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 2: 제조원가 및 판관비 분석 (보고서 '다' 양식)
    # ==========================================
    with tab2:
        st.subheader("🏭 제조원가 및 판매관리비 세부 분석")
       
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("##### 1. 제조원가 현황 (단위: 톤, 원/kg)")
            mfg_df = pd.DataFrame({
                "구분(누계)": ["'26.8월", "'25.8월", "증감"],
                "생산량": [297797, 309973, -12176],
                "원료비": [392.2, 374.3, 17.9],
                "보조재료비": [6.0, 6.1, -0.1],
                "노무비": [10.7, 9.0, 1.7],
                "감가비": [2.6, 2.5, 0.1],
                "제조경비(수광비)": [10.4, 10.5, -0.1],
                "단위당총원가": [25.8, 24.4, 1.4]
            })
            st.dataframe(mfg_df, use_container_width=True, hide_index=True)

        with col_m2:
            st.markdown("##### 2. 판매관리비 현황 (단위: 톤, 원/kg)")
            sgna_df = pd.DataFrame({
                "구분(누계)": ["'26.8월", "'25.8월", "증감"],
                "판매량": [342580, 366346, -23766],
                "인건비": [5.2, 4.6, 0.6],
                "지급수수료": [4.3, 4.1, 0.2],
                "판촉비": [1.3, 1.1, 0.2],
                "수송비(사료운송)": [11.9, 11.3, 0.6],
                "상공비/제세": [2.7, 2.6, 0.1],
                "단위당총판관비": [29.0, 26.9, 2.1]
            })
            st.dataframe(sgna_df, use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 3: 주원료 가격추이 & 시뮬레이션
    # ==========================================
    with tab3:
        st.subheader("🌾 주원료 가격추이 및 4분기 연말 추정 시뮬레이션")
       
        st.markdown("##### 🌽 주요 수입 곡물 가격 추이 (단위: U$/톤)")
        raw_materials = pd.DataFrame({
            "품목": ["옥수수", "소맥", "대두박"],
            "전년평균": [231, 348, 370],
            "1분기": [236, 264, 350],
            "2분기": [249, 258, 351],
            "'26.7월": [245, 257, 340],
            "'26.8월": [260, 276, 357],
            "'26.9월(추정)": [274, 296, 389],
            "'26.10월(예상)": [268, 280, 410]
        })
        st.dataframe(raw_materials, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("##### 🎯 4분기 환율 및 판매물량 목표 입력 시 연말 경상이익 시뮬레이션")
       
        sim_col1, sim_col2 = st.columns(2)
        with sim_col1:
            sim_fx = st.slider("4분기 예상 원/달러 환율", 1300, 1450, 1380, 10)
        with sim_col2:
            sim_vol_target = st.number_input("4분기 추가 스퍼트 목표 물량 (톤)", value=150000, step=5000)

        # 간단 계산 로직
        base_ord = 2456 # 백만원
        est_final_ord = int(base_ord + (sim_vol_target * 0.02) - ((sim_fx - 1350) * 1.5))
       
        st.success(f"💡 예상 연말 최종 경상이익 추정치: **{est_final_ord:,} 백만원** (사업계획 대비 달성률 {(est_final_ord/8971*100):.1f}%)")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")

