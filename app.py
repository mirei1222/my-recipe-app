import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client


# ============================================================
# 1. 페이지 설정
# ============================================================
st.set_page_config(
    page_title="지사 손익·원가 분석 시스템",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# 2. Supabase 연결
# ============================================================
SUPABASE_URL = "https://gpphgtdvlcsmjymhhndq.supabase.co"
SUPABASE_KEY = "여기에 기존 SUPABASE_KEY 입력"


@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()


# ============================================================
# 3. 데이터 불러오기
# ============================================================
@st.cache_data(ttl=300)
def load_data():

    response = (
        supabase
        .table("branch_pnl")
        .select(
            "id, base_ym, branch, doc_type, "
            "account_name, amount, cost_type"
        )
        .order("base_ym")
        .execute()
    )

    df = pd.DataFrame(response.data)

    if df.empty:
        return df

    # --------------------------------------------------------
    # 금액
    # Supabase 원본은 항상 원 단위로 유지
    # --------------------------------------------------------
    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # 기준월
    # --------------------------------------------------------
    df["base_ym"] = df["base_ym"].astype(str).str.strip()

    df["year"] = pd.to_numeric(
        df["base_ym"].str[:4],
        errors="coerce"
    ).astype("Int64")

    df["month"] = pd.to_numeric(
        df["base_ym"].str[5:7],
        errors="coerce"
    ).astype("Int64")

    # --------------------------------------------------------
    # 문자 데이터 정리
    # --------------------------------------------------------
    df["branch"] = df["branch"].fillna("").astype(str).str.strip()
    df["doc_type"] = df["doc_type"].fillna("").astype(str).str.strip()
    df["account_name"] = (
        df["account_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    df["cost_type"] = (
        df["cost_type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    return df


# ============================================================
# 4. 금액 표시 함수
# ============================================================
def get_unit_info(unit):

    if unit == "원":
        return 1, "원"

    elif unit == "천원":
        return 1_000, "천원"

    elif unit == "백만원":
        return 1_000_000, "백만원"

    return 1, "원"


def format_amount(value, divisor):

    if pd.isna(value):
        return "-"

    value = float(value) / divisor

    return f"{value:,.1f}"


def convert_amount_series(series, divisor):

    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0) / divisor


# ============================================================
# 5. 숫자 우측 정렬
# ============================================================
def make_right_align_config(df, text_cols):

    config = {}

    for col in df.columns:

        if col in text_cols:
            config[col] = st.column_config.Column(
                col,
                alignment="left"
            )

        else:
            config[col] = st.column_config.Column(
                col,
                alignment="right"
            )

    return config


# ============================================================
# 6. 제목
# ============================================================
st.title("🏛️ 지사 월별 손익·원가 분석 및 손익추정 시스템")


# ============================================================
# 7. 데이터 로드
# ============================================================
try:

    df = load_data()

    if df.empty:

        st.error(
            "Supabase의 branch_pnl 테이블에서 데이터를 불러오지 못했습니다."
        )

        st.stop()


except Exception as e:

    st.error(f"Supabase 데이터 조회 오류: {e}")
    st.stop()


# ============================================================
# 8. 상단 공통 조건
# ============================================================
col1, col2, col3 = st.columns([2, 2, 6])

with col1:

    display_unit = st.selectbox(
        "금액 표시 단위",
        ["원", "천원", "백만원"],
        index=2
    )


with col2:

    branches = sorted(
        [
            x for x in df["branch"].dropna().unique()
            if str(x).strip()
        ]
    )

    if branches:

        selected_branch = st.selectbox(
            "지사",
            branches
        )

    else:

        selected_branch = None


unit_divisor, unit_name = get_unit_info(display_unit)


# 선택 지사 데이터
if selected_branch:

    work_df = df[
        df["branch"] == selected_branch
    ].copy()

else:

    work_df = df.copy()


# ============================================================
# 9. 탭 구성
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 월별 손익보고서",
        "🌾 수입원재료 모선·환율",
        "🧪 제품 배합비·원료 산출",
        "📈 3개년 비교분석",
        "📅 연도별 재무제표"
    ]
)


# ============================================================
# TAB 1
# 실제 Supabase 손익계산서 + 제조원가명세서
# ============================================================
with tab1:

    st.subheader(
        "📌 실제 데이터 기반 월별 손익·제조원가 분석"
    )

    st.caption(
        "Supabase branch_pnl의 실제 account_name과 amount를 기준으로 표시합니다."
    )

    # --------------------------------------------------------
    # 1. 데이터 현황
    # --------------------------------------------------------
    st.markdown("### 1. 데이터 현황")

    c1, c2, c3, c4 = st.columns(4)

    min_year = int(work_df["year"].min())
    max_year = int(work_df["year"].max())

    c1.metric(
        "최초 데이터",
        f"{min_year}년"
    )

    c2.metric(
        "최근 데이터",
        f"{max_year}년"
    )

    c3.metric(
        "계정과목 수",
        f"{work_df['account_name'].nunique():,}개"
    )

    c4.metric(
        "데이터 건수",
        f"{len(work_df):,}건"
    )

    st.markdown("---")

    # --------------------------------------------------------
    # 2. 손익계산서
    # --------------------------------------------------------
    st.markdown("### 2. 손익계산서")

    pnl_df = work_df[
        work_df["doc_type"].str.contains(
            "손익계산",
            na=False
        )
    ].copy()

    if pnl_df.empty:

        st.warning(
            "Supabase에서 '손익계산'으로 분류된 데이터가 없습니다."
        )

    else:

        years_available = sorted(
            pnl_df["year"].dropna().unique().tolist()
        )

        if years_available:

            selected_pnl_year = st.selectbox(
                "조회 연도",
                years_available,
                index=len(years_available) - 1,
                key="pnl_year"
            )

            selected_pnl = pnl_df[
                pnl_df["year"] == selected_pnl_year
            ].copy()

            # 계정과목 × 월
            pnl_pivot = (
                selected_pnl
                .pivot_table(
                    index="account_name",
                    columns="month",
                    values="amount",
                    aggfunc="sum",
                    fill_value=0
                )
            )

            # 1~12월 순서
            for month in range(1, 13):

                if month not in pnl_pivot.columns:
                    pnl_pivot[month] = 0

            pnl_pivot = pnl_pivot[
                list(range(1, 13))
            ]

            # 연간합계
            pnl_pivot["연간합계"] = pnl_pivot.sum(axis=1)

            # 표시용
            pnl_display = pnl_pivot.copy()

            pnl_display.columns = [
                f"{int(c)}월"
                if isinstance(c, (int, np.integer))
                else c
                for c in pnl_display.columns
            ]

            for col in pnl_display.columns:

                pnl_display[col] = pnl_display[col].apply(
                    lambda x: format_amount(
                        x,
                        unit_divisor
                    )
                )

            pnl_display = pnl_display.reset_index()

            st.dataframe(
                pnl_display,
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config=make_right_align_config(
                    pnl_display,
                    ["account_name"]
                )
            )

            st.caption(
                f"※ 금액 단위: {unit_name} / 원본 amount는 Supabase에서 원 단위로 유지"
            )


    st.markdown("---")


    # --------------------------------------------------------
    # 3. 제조원가명세서
    # --------------------------------------------------------
    st.markdown("### 3. 제조원가명세서")

    mfg_df = work_df[
        work_df["doc_type"].str.contains(
            "제조원가",
            na=False
        )
    ].copy()

    if mfg_df.empty:

        st.warning(
            "Supabase에서 '제조원가'로 분류된 데이터가 없습니다."
        )

    else:

        mfg_years = sorted(
            mfg_df["year"].dropna().unique().tolist()
        )

        selected_mfg_year = st.selectbox(
            "제조원가 조회 연도",
            mfg_years,
            index=len(mfg_years) - 1,
            key="mfg_year"
        )

        selected_mfg = mfg_df[
            mfg_df["year"] == selected_mfg_year
        ].copy()

        mfg_pivot = (
            selected_mfg
            .pivot_table(
                index="account_name",
                columns="month",
                values="amount",
                aggfunc="sum",
                fill_value=0
            )
        )

        for month in range(1, 13):

            if month not in mfg_pivot.columns:
                mfg_pivot[month] = 0

        mfg_pivot = mfg_pivot[
            list(range(1, 13))
        ]

        mfg_pivot["연간합계"] = mfg_pivot.sum(axis=1)

        mfg_display = mfg_pivot.copy()

        mfg_display.columns = [
            f"{int(c)}월"
            if isinstance(c, (int, np.integer))
            else c
            for c in mfg_display.columns
        ]

        for col in mfg_display.columns:

            mfg_display[col] = mfg_display[col].apply(
                lambda x: format_amount(
                    x,
                    unit_divisor
                )
            )

        mfg_display = mfg_display.reset_index()

        st.dataframe(
            mfg_display,
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config=make_right_align_config(
                mfg_display,
                ["account_name"]
            )
        )

        st.caption(
            f"※ 금액 단위: {unit_name}"
        )


    st.markdown("---")


    # --------------------------------------------------------
    # 4. 원본 데이터 확인
    # --------------------------------------------------------
    with st.expander("🔎 Supabase 원본 데이터 확인"):

        raw_display = work_df[
            [
                "base_ym",
                "branch",
                "doc_type",
                "account_name",
                "amount",
                "cost_type"
            ]
        ].copy()

        raw_display["amount"] = raw_display["amount"].apply(
            lambda x: format_amount(
                x,
                unit_divisor
            )
        )

        st.dataframe(
            raw_display,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TAB 2
# 수입원재료 모선·환율
# ============================================================
with tab2:

    st.subheader(
        "🌾 수입원재료 모선별 입고·결제 조건"
    )

    st.caption(
        "현재 단계에서는 입력·계산용 화면으로 유지합니다."
    )

    default_vessels = pd.DataFrame(
        [
            {
                "품목": "옥수수",
                "모선명": "옥수수 10월 1호선",
                "결제예정월": "10월",
                "물량(톤)": 55000,
                "C&F단가($/톤)": 268.0,
                "적용환율(원/$)": 1375.0
            },
            {
                "품목": "옥수수",
                "모선명": "옥수수 11월 2호선",
                "결제예정월": "11월",
                "물량(톤)": 50000,
                "C&F단가($/톤)": 262.0,
                "적용환율(원/$)": 1385.0
            },
            {
                "품목": "소맥",
                "모선명": "소맥 10월선",
                "결제예정월": "10월",
                "물량(톤)": 25000,
                "C&F단가($/톤)": 280.0,
                "적용환율(원/$)": 1375.0
            },
            {
                "품목": "대두박",
                "모선명": "대두박 10월선",
                "결제예정월": "10월",
                "물량(톤)": 18000,
                "C&F단가($/톤)": 410.0,
                "적용환율(원/$)": 1380.0
            },
            {
                "품목": "수입채종박",
                "모선명": "채종박 11월선",
                "결제예정월": "11월",
                "물량(톤)": 10000,
                "C&F단가($/톤)": 310.0,
                "적용환율(원/$)": 1385.0
            },
            {
                "품목": "수입팜박",
                "모선명": "팜박 10월선",
                "결제예정월": "10월",
                "물량(톤)": 15000,
                "C&F단가($/톤)": 185.0,
                "적용환율(원/$)": 1370.0
            },
            {
                "품목": "수입야자박",
                "모선명": "야자박 12월선",
                "결제예정월": "12월",
                "물량(톤)": 12000,
                "C&F단가($/톤)": 205.0,
                "적용환율(원/$)": 1390.0
            }
        ]
    )

    item_options = [
        "옥수수",
        "소맥",
        "대두박",
        "수입채종박",
        "수입팜박",
        "수입야자박"
    ]

    month_options = [
        "9월",
        "10월",
        "11월",
        "12월"
    ]

    edited_df = st.data_editor(
        default_vessels,
        key="vessel_editor_tab2",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "품목": st.column_config.SelectboxColumn(
                "품목",
                options=item_options,
                required=True
            ),
            "모선명": st.column_config.TextColumn(
                "모선명",
                required=True
            ),
            "결제예정월": st.column_config.SelectboxColumn(
                "결제예정월",
                options=month_options,
                required=True
            ),
            "물량(톤)": st.column_config.NumberColumn(
                "물량(톤)",
                min_value=0,
                step=1000,
                format="%d"
            ),
            "C&F단가($/톤)": st.column_config.NumberColumn(
                "C&F단가($/톤)",
                min_value=0.0,
                step=1.0,
                format="%.1f"
            ),
            "적용환율(원/$)": st.column_config.NumberColumn(
                "적용환율(원/$)",
                min_value=1000.0,
                step=5.0,
                format="%.1f"
            )
        }
    )

    if not edited_df.empty:

        calc_df = edited_df.copy()

        calc_df["원화단가(원/kg)"] = (
            calc_df["C&F단가($/톤)"]
            * calc_df["적용환율(원/$)"]
        ) / 1000

        calc_df["원화금액(백만원)"] = (
            calc_df["물량(톤)"]
            * calc_df["C&F단가($/톤)"]
            * calc_df["적용환율(원/$)"]
        ) / 1_000_000

        st.markdown("### 계산 결과")

        st.dataframe(
            calc_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TAB 3
# 제품 배합비 / 원료 산출
# ============================================================
with tab3:

    st.subheader(
        "🧪 제품 배합비(BOM) 및 원료 사용량 계산"
    )

    col_left, col_right = st.columns([6, 4])

    with col_left:

        st.markdown("### 1. 제품별 배합비")

        default_bom = pd.DataFrame(
            [
                {
                    "제품명": "양돈_젖떼기01",
                    "축종": "양돈",
                    "수입옥수수(%)": 55.0,
                    "소맥(%)": 5.0,
                    "대두박(%)": 20.0,
                    "수입채종박(%)": 0.0,
                    "수입팜박(%)": 0.0,
                    "수입야자박(%)": 0.0,
                    "국산/기타(%)": 20.0
                },
                {
                    "제품명": "양돈_육성02",
                    "축종": "양돈",
                    "수입옥수수(%)": 58.0,
                    "소맥(%)": 0.0,
                    "대두박(%)": 22.0,
                    "수입채종박(%)": 2.0,
                    "수입팜박(%)": 0.0,
                    "수입야자박(%)": 0.0,
                    "국산/기타(%)": 18.0
                },
                {
                    "제품명": "양계_산란01",
                    "축종": "양계",
                    "수입옥수수(%)": 60.0,
                    "소맥(%)": 10.0,
                    "대두박(%)": 15.0,
                    "수입채종박(%)": 0.0,
                    "수입팜박(%)": 0.0,
                    "수입야자박(%)": 0.0,
                    "국산/기타(%)": 15.0
                },
                {
                    "제품명": "축우_비육01",
                    "축종": "축우",
                    "수입옥수수(%)": 35.0,
                    "소맥(%)": 5.0,
                    "대두박(%)": 10.0,
                    "수입채종박(%)": 5.0,
                    "수입팜박(%)": 10.0,
                    "수입야자박(%)": 10.0,
                    "국산/기타(%)": 25.0
                },
                {
                    "제품명": "기타_특수01",
                    "축종": "기타",
                    "수입옥수수(%)": 40.0,
                    "소맥(%)": 10.0,
                    "대두박(%)": 15.0,
                    "수입채종박(%)": 5.0,
                    "수입팜박(%)": 5.0,
                    "수입야자박(%)": 0.0,
                    "국산/기타(%)": 25.0
                }
            ]
        )

        edited_bom = st.data_editor(
            default_bom,
            key="bom_editor",
            num_rows="dynamic",
            use_container_width=True
        )

    with col_right:

        st.markdown("### 2. 제품별 판매량")

        default_sales = pd.DataFrame(
            [
                {"제품명": "양돈_젖떼기01", "판매량(톤)": 60000},
                {"제품명": "양돈_육성02", "판매량(톤)": 83700},
                {"제품명": "양계_산란01", "판매량(톤)": 97400},
                {"제품명": "축우_비육01", "판매량(톤)": 86000},
                {"제품명": "기타_특수01", "판매량(톤)": 16280}
            ]
        )

        edited_sales = st.data_editor(
            default_sales,
            key="sales_editor",
            num_rows="dynamic",
            use_container_width=True
        )

    if not edited_bom.empty and not edited_sales.empty:

        merged_bom = pd.merge(
            edited_bom,
            edited_sales,
            on="제품명",
            how="inner"
        )

        ing_cols = [
            "수입옥수수(%)",
            "소맥(%)",
            "대두박(%)",
            "수입채종박(%)",
            "수입팜박(%)",
            "수입야자박(%)",
            "국산/기타(%)"
        ]

        for col in ing_cols:

            raw_col = col.replace(
                "(%)",
                "소모량(톤)"
            )

            merged_bom[raw_col] = (
                merged_bom["판매량(톤)"]
                * pd.to_numeric(
                    merged_bom[col],
                    errors="coerce"
                )
                / 100
            )

        species_group = (
            merged_bom
            .groupby("축종")
            .sum(numeric_only=True)
            .reset_index()
        )

        import_cols = [
            c.replace("(%)", "소모량(톤)")
            for c in ing_cols[:-1]
        ]

        species_group["수입원료 소모량(톤)"] = (
            species_group[import_cols].sum(axis=1)
        )

        species_group["국산원료 소모량(톤)"] = (
            species_group["국산/기타소모량(톤)"]
        )

        species_group["총 원료사용량(톤)"] = (
            species_group["판매량(톤)"]
        )

        species_group["수입 비중(%)"] = (
            species_group["수입원료 소모량(톤)"]
            / species_group["총 원료사용량(톤)"]
            * 100
        ).round(1)

        species_group["국산 비중(%)"] = (
            species_group["국산원료 소모량(톤)"]
            / species_group["총 원료사용량(톤)"]
            * 100
        ).round(1)

        st.markdown("---")
        st.markdown("### 3. 축종별 원료 사용량")

        result = species_group[
            [
                "축종",
                "총 원료사용량(톤)",
                "수입원료 소모량(톤)",
                "수입 비중(%)",
                "국산원료 소모량(톤)",
                "국산 비중(%)"
            ]
        ].copy()

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TAB 4
# 실제 3개년 비교분석
# ============================================================
with tab4:

    st.subheader(
        "📈 실제 데이터 기반 3개년 비교 분석"
    )

    st.caption(
        "임의 입력값이 아니라 branch_pnl의 실제 계정과목별 데이터를 사용합니다."
    )

    history_df = work_df[
        work_df["doc_type"].str.contains(
            "손익계산",
            na=False
        )
    ].copy()

    if history_df.empty:

        st.warning(
            "손익계산서 데이터가 없습니다."
        )

    else:

        account_options = sorted(
            history_df["account_name"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_account = st.selectbox(
            "분석할 계정과목",
            account_options,
            key="history_account"
        )

        selected_history = history_df[
            history_df["account_name"] == selected_account
        ].copy()

        trend = (
            selected_history
            .pivot_table(
                index="month",
                columns="year",
                values="amount",
                aggfunc="sum",
                fill_value=0
            )
            .reindex(range(1, 13), fill_value=0)
        )

        trend = trend / unit_divisor

        trend.index = [
            f"{i}월"
            for i in trend.index
        ]

        trend_display = trend.copy()

        for col in trend_display.columns:

            trend_display[col] = trend_display[col].apply(
                lambda x: f"{x:,.1f}"
            )

        trend_display = trend_display.reset_index()

        st.markdown(
            f"### 「{selected_account}」 월별 추이"
        )

        st.dataframe(
            trend_display,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # 그래프
        # ----------------------------------------------------
        fig = go.Figure()

        for year in trend.columns:

            fig.add_trace(
                go.Scatter(
                    x=list(trend.index),
                    y=trend[year],
                    mode="lines+markers",
                    name=f"{int(year)}년"
                )
            )

        fig.update_layout(
            title=f"{selected_account} 3개년 월별 추이",
            xaxis_title="월",
            yaxis_title=f"금액 ({unit_name})",
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ----------------------------------------------------
        # 3개년 동월 평균
        # ----------------------------------------------------
        if len(trend.columns) >= 2:

            avg_df = trend.copy()

            avg_df["3개년 동월평균"] = (
                avg_df.mean(axis=1)
            )

            avg_display = avg_df.copy()

            for col in avg_display.columns:

                avg_display[col] = avg_display[col].apply(
                    lambda x: f"{x:,.1f}"
                )

            avg_display = avg_display.reset_index()

            st.markdown("### 3개년 동월 평균")

            st.dataframe(
                avg_display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# TAB 5
# 실제 연도별 재무제표 조회
# ============================================================
with tab5:

    st.subheader(
        "📅 실제 연도별 재무제표 조회"
    )

    statement_df = work_df.copy()

    years = sorted(
        statement_df["year"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_year = st.selectbox(
        "조회 연도",
        years,
        index=len(years) - 1,
        key="past_year"
    )

    year_df = statement_df[
        statement_df["year"] == selected_year
    ].copy()

    # --------------------------------------------------------
    # 손익계산서
    # --------------------------------------------------------
    st.markdown(
        f"### 📌 {selected_year}년 손익계산서"
    )

    year_pnl = year_df[
        year_df["doc_type"].str.contains(
            "손익계산",
            na=False
        )
    ].copy()

    if year_pnl.empty:

        st.info(
            "해당 연도의 손익계산서 데이터가 없습니다."
        )

    else:

        pnl_year_summary = (
            year_pnl
            .groupby("account_name", as_index=False)
            ["amount"]
            .sum()
        )

        pnl_year_summary["amount"] = (
            pnl_year_summary["amount"]
            / unit_divisor
        )

        pnl_year_summary = pnl_year_summary.rename(
            columns={
                "account_name": "계정과목",
                "amount": f"금액 ({unit_name})"
            }
        )

        pnl_year_summary[
            f"금액 ({unit_name})"
        ] = pnl_year_summary[
            f"금액 ({unit_name})"
        ].apply(
            lambda x: f"{x:,.1f}"
        )

        st.dataframe(
            pnl_year_summary,
            use_container_width=True,
            hide_index=True,
            height=600
        )


    st.markdown("---")


    # --------------------------------------------------------
    # 제조원가명세서
    # --------------------------------------------------------
    st.markdown(
        f"### 🏭 {selected_year}년 제조원가명세서"
    )

    year_mfg = year_df[
        year_df["doc_type"].str.contains(
            "제조원가",
            na=False
        )
    ].copy()

    if year_mfg.empty:

        st.info(
            "해당 연도의 제조원가명세서 데이터가 없습니다."
        )

    else:

        mfg_year_summary = (
            year_mfg
            .groupby("account_name", as_index=False)
            ["amount"]
            .sum()
        )

        mfg_year_summary["amount"] = (
            mfg_year_summary["amount"]
            / unit_divisor
        )

        mfg_year_summary = mfg_year_summary.rename(
            columns={
                "account_name": "계정과목",
                "amount": f"금액 ({unit_name})"
            }
        )

        mfg_year_summary[
            f"금액 ({unit_name})"
        ] = mfg_year_summary[
            f"금액 ({unit_name})"
        ].apply(
            lambda x: f"{x:,.1f}"
        )

        st.dataframe(
            mfg_year_summary,
            use_container_width=True,
            hide_index=True,
            height=600
        )


# ============================================================
# 10. 하단 안내
# ============================================================
st.markdown("---")

st.caption(
    "※ Supabase의 amount는 원 단위 원본을 유지하며, "
    "원/천원/백만원 선택은 화면 표시 단위에만 적용됩니다."
)