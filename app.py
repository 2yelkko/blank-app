"""12주차 직접 쓰기 앱: 배포할 수 있는 대시보드를 처음부터 씁니다.

쓰는 법
1. 칸마다 주석의 할 일을 읽고 '# 여기에 씁니다' 아래에 코드를 씁니다. 번호(# 1-3 등)는 강의 PDF 제목의 번호입니다.
2. 내 컴퓨터에서 python -m streamlit run app.py 로 확인하고, 다 쓰면 python 배포_전_점검.py 로 [고침]이 0인지 봅니다.
3. requirements.txt도 직접 채웁니다(1-4). 먼저 배포_예제/를 보지 않고 써 봅니다. 막히면 PDF의 같은 번호 쪽을 봅니다.
4. 개인 프로젝트: sales.csv를 출처가 분명한 공개 데이터로 바꾸고 질문, 위젯, 차트를 내 데이터에 맞춰 고칩니다.
   차트 3개 이상과 위젯에 따라 바뀌는 숫자·차트가 프로젝트 최소 요건입니다.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

COLORS = {"A": "#0072B2", "B": "#D55E00"}
st.set_page_config(page_title="지점 실적 탐색", layout="wide")
st.title("어느 지점의 실적이 더 좋은가")
st.caption("출처: 수업용 가상 데이터(sales.csv) · 2026년 1~12월 지점별 월 실적 · 금액 단위: 백만원")

# 1-3 데이터 경로: app.py가 있는 폴더(HERE)를 기준으로 sales.csv를 읽는 load_data를 만듭니다(@st.cache_data).
#     C:\Users\... 같은 내 컴퓨터 경로는 서버에 없습니다. 파일이 없으면 st.error로 안내하고 st.stop()으로 멈춥니다.
#     읽은 표는 data에 담습니다. 열은 month, branch, sales, profit입니다.
HERE = Path(__file__).parent   # app.py가 있는 폴더


@st.cache_data
def load_data():
    return pd.read_csv(HERE / "sales.csv")


try:
    data = load_data()
except FileNotFoundError:
    st.error("app.py와 같은 폴더에 sales.csv를 올려 주세요.")
    st.stop()

# 2-2 위젯 세 개(11주차): 사이드바에 지점(A, B 여러 개 고르기), 월 범위(1~12), 표시 지표(매출, 영업이익).
#     고른 지표 이름을 열 이름(sales, profit)으로 바꿔 metric에 담습니다.
st.sidebar.header("조회 조건")
branches = st.sidebar.multiselect("지점", ["A", "B"], default=["A", "B"])
months = st.sidebar.slider("월 범위", 1, 12, (1, 12))
metric_label = st.sidebar.selectbox("표시 지표", ["매출", "영업이익"])
metric = {"매출": "sales", "영업이익": "profit"}[metric_label]

# 빈 선택(11주차 2-3): 고른 지점과 월 범위의 행만 view에 담고, view가 비면 st.warning으로 안내한 뒤 st.stop()으로 멈춥니다.
#     아래의 숫자, 차트, 표는 모두 view를 씁니다.
view = data.loc[data["branch"].isin(branches)
                & data["month"].between(months[0], months[1])].copy()
if view.empty:
    st.warning("표시할 데이터가 없습니다. 지점을 하나 이상 선택하세요.")
    st.stop()

# 3-1 지표 카드: 기간 합계와 표시 관측 수(행 수)를 카드 두 개로 보입니다.
st.subheader(f"{months[0]}~{months[1]}월 {metric_label} · {', '.join(branches)}지점")
c1, c2 = st.columns(2)
c1.metric(f"기간 {metric_label} 합계", f"{view[metric].sum():,.0f} 백만원")
c2.metric("표시 관측 수", f"{len(view)} 행")
st.caption("한 행은 한 달·한 지점입니다.")

# 2-9 한글 확인과 차트 세 개: 서버에는 한글 글꼴이 없을 수 있어 세 차트 모두 Plotly로 그립니다(브라우저가 글자를 그림).
#     차트 1 월별 추이(선), 차트 2 지점별 기간 합계(막대), 차트 3 지점별 기간 영업이익률(막대, 이익 합계 ÷ 매출 합계 × 100).
#     화면을 세 열로 나눠 차례로 넣습니다.
# 차트 1: 월별 추이(선)
trend = px.line(view.sort_values(["branch", "month"]), x="month", y=metric, color="branch",
                markers=True, color_discrete_map=COLORS, title="월별 추이",
                labels={"month": "월", metric: f"{metric_label} (백만원)", "branch": "지점"})
trend.update_xaxes(dtick=1)
trend.update_yaxes(rangemode="tozero")

# 차트 2: 지점별 기간 합계(막대)
totals = view.groupby("branch", as_index=False)[metric].sum()
total_fig = px.bar(totals, x="branch", y=metric, color="branch", color_discrete_map=COLORS,
                   text_auto=",.0f", title=f"지점별 기간 {metric_label} 합계",
                   labels={"branch": "지점", metric: f"{metric_label} (백만원)"})
total_fig.update_layout(showlegend=False)
total_fig.update_yaxes(rangemode="tozero")

# 차트 3: 지점별 기간 영업이익률(막대) = 기간 이익 합계 ÷ 기간 매출 합계 × 100 (달마다 비율의 평균이 아님)
period = view.groupby("branch", as_index=False)[["sales", "profit"]].sum()
period["margin"] = period["profit"] / period["sales"] * 100
margin_fig = px.bar(period, x="branch", y="margin", color="branch", color_discrete_map=COLORS,
                    text_auto=".1f", title="기간 영업이익률",
                    labels={"branch": "지점", "margin": "영업이익률 (%)"})
margin_fig.update_layout(showlegend=False)
margin_fig.update_yaxes(rangemode="tozero")

left, middle, right = st.columns(3)
with left:
    st.plotly_chart(trend, width="stretch")
with middle:
    st.plotly_chart(total_fig, width="stretch")
with right:
    st.plotly_chart(margin_fig, width="stretch")

# 4-1 표와 CSV 저장(11주차): view를 표로 보이고, 지금 고른 데이터를 CSV로 내려받는 단추를 둡니다.
st.subheader("현재 선택한 데이터")
st.dataframe(view, hide_index=True, width="stretch")
st.download_button("현재 선택 CSV 저장", data=view.to_csv(index=False).encode("utf-8-sig"),
                   file_name="selected_sales.csv", mime="text/csv")
st.caption("이 자료만으로 실적 변화의 원인을 단정하지 않습니다.")
