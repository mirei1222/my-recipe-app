import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client

# 1. 페이지 설정
st.set_page_config(page_title="지사 손익실적 및 수입원료/모선별 원가 분석 시스템", page_icon="📑", layout="wide")

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

st.title("📑 지사 손익실적 및 수입원료/모선별 원가 분석 (임원 보고용)")

try:
    df = load_data()
   
    # --- 사이드바 설정 ---
    st.sidebar.header("⚙️ 보고서 기준 설정")
    selected_branch = st.sidebar.selectbox("지사 선택", df['branch'].unique() if not df.empty else ["충청지사"])
    selected_year = st.sidebar.selectbox("기준 연도", ["2026", "2025"], index=0)
    selected_month = st.sidebar.slider("기준 월 (누계)", 1, 12, 8)

    tab1, tab2, tab3 = st.tabs(["나. 손익실적 (경상이익)", "다. 제조원가 및 판관비 분석 (원/kg)", "라. 수입원료 모선별 결제/환율 & 연동 시뮬레이션"])

    # ==========================================
    # TAB 1: 손익실적 (보고서 '나' 양식)
    # ==========================================
    with tab1:
        st.subheader(f"📌 손익실적 요약 ({selected_branch} {selected_month}월 누계)")
       
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위 : 백만원, %)</div>", unsafe_allow_html=True)

        pnl_data = {
            "구 분": ["판매량(톤)", "매출액", "매출원가", "매출총이익", "판매관리비", "영업이익", "영업외손익", "경상이익(공통관리비제외)"],
            "연간계획": [551090, 287060, 260732, 26328, 16066, 10262, -1291, 8971],
            "계획(A)": [364330, 189418, 172045, 17373, 11567, 5806, -729, 5077],
            "실적(B)": [342580, 168193, 155004, 13188, 9931, 3257, -801, 2456],
            "전년동기(C)": [366346, 175910, 159933, 15977, 9841, 6136, -725, 5411]
        }
       
        pnl_df = pd.DataFrame(pnl_data)
        pnl_df["증감(B-A)"] = pnl_df["실적(B)"] - pnl_df["계획(A)"]
        pnl_df["달성율(B/A)"] = (pnl_df["실적(B)"] / pnl_df["계획(A)"] * 100).round(1)
        pnl_df["증감(B-C)"] = pnl_df["실적(B)"] - pnl_df["전년동기(C)"]

        # 천단위 콤마 포맷팅 적용
        pnl_fmt = pnl_df.copy()
        num_cols = ["연간계획", "계획(A)", "실적(B)", "증감(B-A)", "전년동기(C)", "증감(B-C)"]
        for col in num_cols:
            pnl_fmt[col] = pnl_fmt[col].apply(lambda x: f"{x:,.0f}")
        pnl_fmt["달성율(B/A)"] = pnl_fmt["달성율(B/A)"].apply(lambda x: f"{x:.1f}%")

        cols_order = ["구 분", "연간계획", "계획(A)", "실적(B)", "증감(B-A)", "달성율(B/A)", "전년동기(C)", "증감(B-C)"]
        st.dataframe(pnl_fmt[cols_order], use_container_width=True, hide_index=True)

        # 엑셀 다운로드 버튼
        csv_pnl = pnl_df[cols_order].to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 손익실적 표 엑셀(CSV) 다운로드", csv_pnl, "손익실적_요약.csv", "text/csv")

        st.markdown("---")
        st.markdown("#### 🟢 월별 경상이익 추이 (공통관리비 배분 전/후)")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 억원)</div>", unsafe_allow_html=True)
       
        monthly_data = {
            "구분": ["배분 전 경상이익", "배분 후 경상이익"],
            "1월": [10.8, 3.8], "2월": [3.7, 1.2], "3월": [7.5, 4.8], "4월": [0.4, -1.2],
            "5월": [-2.8, -6.3], "6월": [4.2, 4.6], "7월": [1.7, 1.6], "8월": [-0.9, -3.6], "누계": [24.6, 4.9]
        }
        monthly_df = pd.DataFrame(monthly_data)
        monthly_fmt = monthly_df.copy()
        for col in ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "누계"]:
            monthly_fmt[col] = monthly_fmt[col].apply(lambda x: f"{x:,.1f}")
           
        st.dataframe(monthly_fmt, use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 2: 제조원가 및 판관비 분석 (상하 배치)
    # ==========================================
    with tab2:
        st.subheader("🏭 제조원가 및 판매관리비 세부 분석")
       
        # 1. 제조원가 표
        st.markdown("##### < 제 조 원 가 >")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 톤, 원/kg)</div>", unsafe_allow_html=True)
       
        mfg_df = pd.DataFrame({
            "구분(누계)": ["'26.8월", "'25.8월", "증감"],
            "생산량": [297797, 309973, -12176],
            "원료비": [392.2, 374.3, 17.9],
            "보조재료비": [6.0, 6.1, -0.1],
            "노무비": [10.7, 9.0, 1.7],
            "감가비": [2.6, 2.5, 0.1],
            "수광비": [10.4, 10.5, -0.1],
            "단위당총원가": [25.8, 24.4, 1.4]
        })
       
        mfg_fmt = mfg_df.copy()
        mfg_fmt["생산량"] = mfg_fmt["생산량"].apply(lambda x: f"{x:,.0f}")
        for col in ["원료비", "보조재료비", "노무비", "감가비", "수광비", "단위당총원가"]:
            mfg_fmt[col] = mfg_fmt[col].apply(lambda x: f"{x:,.1f}")
           
        st.dataframe(mfg_fmt, use_container_width=True, hide_index=True)

        st.markdown("---")

        # 2. 판매관리비 표
        st.markdown("##### < 판 매 관 리 비 >")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 톤, 원/kg)</div>", unsafe_allow_html=True)
       
        sgna_df = pd.DataFrame({
            "구분(누계)": ["'26.8월", "'25.8월", "증감"],
            "판매량": [342580, 366346, -23766],
            "인건비": [5.2, 4.6, 0.6],
            "지급수수료": [4.3, 4.1, 0.2],
            "판촉비": [1.3, 1.1, 0.2],
            "수송비": [11.9, 11.3, 0.6],
            "제세공과": [2.7, 2.6, 0.1],
            "단위당총판관비": [29.0, 26.9, 2.1]
        })
       
        sgna_fmt = sgna_df.copy()
        sgna_fmt["판매량"] = sgna_fmt["판매량"].apply(lambda x: f"{x:,.0f}")
        for col in ["인건비", "지급수수료", "판촉비", "수송비", "제세공과", "단위당총판관비"]:
            sgna_fmt[col] = sgna_fmt[col].apply(lambda x: f"{x:,.1f}")
           
        st.dataframe(sgna_fmt, use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 3: 수입원료 모선별 결제/환율 & 연동 시뮬레이션
    # ==========================================
    with tab3:
        st.subheader("🌾 수입원료 모선별 입고·결제 환율 관리 및 정밀 연동 시뮬레이션")
        st.caption("모선별 입력한 수입원료 결제금액이 하단 '연말 추정 경상이익'에 실시간 반영됩니다.")

        default_vessels = pd.DataFrame([
            {"품목": "옥수수", "모선명": "옥수수 10월 1호선", "결제예정월": "10월", "물량(톤)": 55000, "C&F단가($/톤)": 268.0, "적용환율(원/$)": 1375.0},
            {"품목": "옥수수", "모선명": "옥수수 11월 2호선", "결제예정월": "11월", "물량(톤)": 50000, "C&F단가($/톤)": 262.0, "적용환율(원/$)": 1385.0},
            {"품목": "소맥", "모선명": "소맥 10월선", "결제예정월": "10월", "물량(톤)": 25000, "C&F단가($/톤)": 280.0, "적용환율(원/$)": 1375.0},
            {"품목": "대두박", "모선명": "대두박 10월선", "결제예정월": "10월", "물량(톤)": 18000, "C&F단가($/톤)": 410.0, "적용환율(원/$)": 1380.0},
            {"품목": "수입채종박", "모선명": "채종박 11월선", "결제예정월": "11월", "물량(톤)": 10000, "C&F단가($/톤)": 310.0, "적용환율(원/$)": 1385.0},
            {"품목": "수입팜박", "모선명": "팜박 10월선", "결제예정월": "10월", "물량(톤)": 15000, "C&F단가($/톤)": 185.0, "적용환율(원/$)": 1370.0},
            {"품목": "수입야자박", "모선명": "야자박 12월선", "결제예정월": "12월", "물량(톤)": 12000, "C&F단가($/톤)": 205.0, "적용환율(원/$)": 1390.0},
        ])

        st.markdown("##### 1. 모선별 입고·결제 조건 기입표 (key 부여로 세션 유지)")
        st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 톤, U$/톤, 원/$)</div>", unsafe_allow_html=True)

        item_options = ["옥수수", "소맥", "대두박", "수입채종박", "수입팜박", "수입야자박"]
        month_options = ["9월", "10월", "11월", "12월", "1월"]

        # key='vessel_editor' 추가로 탭 이동시 초기화 문제 방지
        edited_df = st.data_editor(
            default_vessels,
            key="vessel_editor",
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
            st.markdown("##### 2. 모선별 원화 단가 및 결제금액 산출 결과")
            st.markdown("<div style='text-align: right; font-weight: bold; color: #555555; margin-bottom: 5px;'>(단위: 톤, U$/톤, 원/$, 원/kg, 백만원)</div>", unsafe_allow_html=True)

            res_display = calc_df.copy()
            res_display["물량(톤)"] = res_display["물량(톤)"].apply(lambda x: f"{x:,.0f}")
            res_display["C&F단가($/톤)"] = res_display["C&F단가($/톤)"].apply(lambda x: f"{x:,.1f}")
            res_display["적용환율(원/$)"] = res_display["적용환율(원/$)"].apply(lambda x: f"{x:,.1f}")
            res_display["원화단가(원/kg)"] = res_display["원화단가(원/kg)"].apply(lambda x: f"{x:,.1f}")
            res_display["원화금액(백만원)"] = res_display["원화금액(백만원)"].apply(lambda x: f"{x:,.0f}")

            st.dataframe(res_display, use_container_width=True, hide_index=True)

            # 모선 데이터 엑셀 다운로드
            csv_vessel = calc_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 모선별 원가계산서 엑셀 다운로드", csv_vessel, "모선별_수입원가_분석.csv", "text/csv")

            # 3. 실시간 P&L 연동 시뮬레이션
            st.markdown("---")
            st.markdown("##### 🎯 [실시간 연동] 모선별 원가 반영 연말 최종 경상이익 추정 및 Bridge 분석")

            # 기준 사업계획 경상이익 (백만원)
            plan_ord_profit = 8971
            tot_raw_cost = calc_df["원화금액(백만원)"].sum()
           
            # 계획 기준 수입원가 대비 차이 계산 (기준가 250달러, 환율 1350원 기준 대비)
            base_plan_raw_cost = (calc_df["물량(톤)"].sum() * 250 * 1350) / 1000000.0
            cost_impact = tot_raw_cost - base_plan_raw_cost  # +이면 원가상승 (손익 차감)

            # 4분기 추가 물량 스퍼트 영향
            sim_vol_target = st.number_input("4분기 판매 스퍼트 추가 목표 물량 (톤)", value=150000, step=5000)
            vol_impact = (sim_vol_target - 140000) * 0.025  # 톤당 25원 마진 가정 (백만원)
            expense_saving = 150  # 경비 절감 효과 (백만원)

            # 최종 연말 추정 경상이익 산출 (모선 원가 차감 연동!)
            est_final_ord = int(plan_ord_profit + vol_impact - cost_impact + expense_saving)

            c1, c2, c3 = st.columns(3)
            c1.metric("2026 사업계획 경상이익", f"{plan_ord_profit:,.0f} 백만원")
            c2.metric("수입원료 원가증감 영향", f"{-cost_impact:,.0f} 백만원", delta="원가상승 차감" if cost_impact > 0 else "원가절감 반영", delta_color="inverse")
            c3.metric("🏆 연말 최종 추정 경상이익", f"{est_final_ord:,.0f} 백만원", delta=f"달성률 {(est_final_ord/plan_ord_profit*100):.1f}%")

            # 임원 보고용 Waterfall (Bridge) 차트 생성
            fig = go.Figure(go.Waterfall(
                name="손익 변동 요인", orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=["사업계획 경상이익", "판매물량 변동효과", "수입원료/환율 변동", "경비절감 효과", "연말 추정 경상이익"],
                textposition="outside",
                text=[f"{plan_ord_profit:,.0f}", f"{vol_impact:+,.0f}", f"{-cost_impact:+,.0f}", f"{expense_saving:+,.0f}", f"{est_final_ord:,.0f}"],
                y=[plan_ord_profit, vol_impact, -cost_impact, expense_saving, 0],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#E53935"}},
                increasing={"marker": {"color": "#43A047"}},
                totals={"marker": {"color": "#1E88E5"}}
            ))
            fig.update_layout(title="📊 사업계획 대비 연말 경상이익 변동요인 (Bridge Chart)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
