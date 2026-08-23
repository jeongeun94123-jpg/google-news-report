from __future__ import annotations

import html
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from agent import run_once
from report_docx import build_report_docx

# 배포 환경에서는 Streamlit Secrets의 키를 환경변수로 연결합니다.
# 로컬에서는 기존 .env 파일을 그대로 사용합니다.
if not os.getenv("OPENAI_API_KEY"):
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
        if secret_key:
            os.environ["OPENAI_API_KEY"] = str(secret_key)
    except FileNotFoundError:
        pass

st.set_page_config(page_title="News Pulse", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root { --purple:#7446e8; --ink:#292b38; --muted:#76798c; color-scheme:light; }
html, body, [class*="css"] { font-family:'Noto Sans KR','Malgun Gothic',sans-serif; }
[data-testid="stAppViewContainer"] { background:linear-gradient(145deg,#f5f4fd 0%,#eceefa 55%,#f7f5ff 100%); color:var(--ink); }
[data-testid="stSidebar"] { background:#f7f6fc; border-right:1px solid rgba(116,70,232,.10); color:var(--ink); }
[data-testid="stSidebar"] > div { padding-top:1.7rem; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] { color:var(--ink) !important; opacity:1 !important; }
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] input { background:#fff !important; color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important; border:1px solid #e1ddee !important; caret-color:var(--purple) !important; }
[data-testid="stSidebar"] textarea::placeholder,
[data-testid="stSidebar"] input::placeholder { color:#9a9cad !important; -webkit-text-fill-color:#9a9cad !important; }
[data-testid="stSidebar"] button { color:var(--ink); }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-size:14px !important; font-weight:700 !important; letter-spacing:-.02em; margin-bottom:6px !important; }
[data-testid="stSidebar"] [data-baseweb="textarea"] { border:1px solid #e6e2f0 !important; outline:0 !important; border-radius:14px !important; overflow:hidden; background:#fff !important; box-shadow:0 4px 14px rgba(66,50,112,.06) !important; transition:box-shadow .2s ease, border-color .2s ease; }
[data-testid="stSidebar"] [data-baseweb="textarea"] > div { border:0 !important; outline:0 !important; background:#fff !important; box-shadow:none !important; }
[data-testid="stSidebar"] [data-baseweb="textarea"]:focus-within { transform:translateY(-1px); box-shadow:0 0 0 3px rgba(116,70,232,.14),0 10px 24px rgba(66,50,112,.11); }
[data-testid="stSidebar"] textarea { border:0 !important; outline:0 !important; border-radius:14px !important; padding:14px 15px !important; font-size:14px !important; font-weight:600 !important; line-height:1.55 !important; box-shadow:none !important; resize:none !important; }
[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"] { border:1px solid #e1ddee !important; border-radius:16px !important; overflow:hidden; background:#fff !important; box-shadow:0 5px 16px rgba(66,50,112,.07); min-height:50px; }
[data-testid="stSidebar"] [data-testid="stNumberInput"] input { border:0 !important; padding-left:16px !important; font-size:15px !important; font-weight:700 !important; }
[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"] button { width:34px !important; height:34px !important; min-width:34px !important; margin:7px 5px 7px 0 !important; padding:0 !important; border:0 !important; border-radius:10px !important; background:#f0ecff !important; color:var(--purple) !important; box-shadow:none !important; transition:background .18s ease, color .18s ease !important; }
[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"] button:hover { background:var(--purple) !important; color:#fff !important; }
[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"] button svg { fill:currentColor !important; stroke:currentColor !important; width:14px !important; height:14px !important; }
.block-container { max-width:1440px; padding:2rem 2.4rem 4rem; }
#MainMenu, footer { visibility:hidden; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button { background:white; border:1px solid rgba(116,70,232,.16); box-shadow:0 8px 22px rgba(75,55,135,.14); color:var(--purple); }
.hero { position:relative; overflow:hidden; padding:34px 38px; border-radius:28px; background:linear-gradient(120deg,#6d43db,#9b5cf3); color:white; box-shadow:0 20px 50px rgba(103,70,195,.25); margin-bottom:20px; }
.hero:after { content:''; position:absolute; width:260px; height:260px; border-radius:50%; right:-70px; top:-130px; background:rgba(255,255,255,.14); }
.eyebrow { font-size:12px; letter-spacing:.16em; font-weight:800; opacity:.78; }
.hero h1 { margin:8px 0; font-size:clamp(30px,4vw,50px); letter-spacing:-.045em; line-height:1.13; }
.hero p { margin:0; font-size:15px; opacity:.88; }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:8px 0 20px; }
.metric-card { background:rgba(255,255,255,.88); padding:18px 20px; border-radius:20px; border:1px solid rgba(116,70,232,.09); box-shadow:0 12px 30px rgba(67,58,105,.07); transition:.22s; cursor:help; }
.metric-card:hover { transform:translateY(-6px) scale(1.01); box-shadow:0 20px 38px rgba(87,60,160,.16); border-color:rgba(116,70,232,.35); }
.metric-label { font-size:12px; color:var(--muted); font-weight:700; }
.metric-value { font-size:27px; font-weight:800; margin-top:3px; }
.report-wrap { background:rgba(255,255,255,.9); padding:28px 32px; border-radius:24px; border:1px solid rgba(116,70,232,.09); box-shadow:0 16px 40px rgba(55,45,95,.08); }
.report-major { margin:22px 0 9px; padding:13px 16px; border-left:5px solid var(--purple); background:linear-gradient(90deg,#f1ecff,rgba(255,255,255,.3)); border-radius:4px 14px 14px 4px; font-size:18px; font-weight:800; letter-spacing:-.02em; }
.report-minor { margin:8px 0 4px 18px; color:#393b48; font-size:14px; font-weight:600; line-height:1.65; }
.report-detail { margin:3px 0 7px 44px; color:#77798a; font-size:13px; line-height:1.65; }
.sidebar-brand { color:var(--ink) !important; font-size:22px; font-weight:800; letter-spacing:-.04em; margin-bottom:4px; }
.sidebar-caption { color:#85889a !important; font-size:12px; margin-bottom:18px; }
div.stButton > button, div.stDownloadButton > button { border:0; border-radius:14px; min-height:48px; font-weight:800; transition:.2s ease; }
div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"] { color:white !important; background:linear-gradient(100deg,#8d4ff0,#6442d7) !important; box-shadow:0 10px 22px rgba(107,67,214,.24); }
[data-testid="stSidebar"] div.stButton > button,
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] { color:white !important; background:linear-gradient(105deg,#9858f4,#6542dc) !important; border:0 !important; border-radius:16px !important; min-height:52px !important; font-size:15px !important; font-weight:800 !important; letter-spacing:-.02em; box-shadow:0 10px 24px rgba(107,67,214,.25) !important; }
[data-testid="stSidebar"] div.stButton > button p,
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] p { color:white !important; font-weight:800 !important; }

/* Sidebar text fields: deliberately simple and neutral. */
[data-testid="stSidebar"] [data-baseweb="textarea"],
[data-testid="stSidebar"] [data-baseweb="textarea"] > div,
[data-testid="stSidebar"] [data-baseweb="textarea"]:focus-within {
  background:#fff !important;
  border:1px solid #dfe1e7 !important;
  border-radius:10px !important;
  box-shadow:none !important;
  outline:none !important;
  transform:none !important;
}
[data-testid="stSidebar"] [data-baseweb="textarea"] > div {
  border:0 !important;
}
[data-testid="stSidebar"] [data-baseweb="textarea"]:focus-within {
  border-color:#8b68e8 !important;
}
[data-testid="stSidebar"] textarea {
  background:#fff !important;
  color:#30313d !important;
  border:0 !important;
  border-radius:10px !important;
  box-shadow:none !important;
  outline:none !important;
  padding:13px 14px !important;
  font-size:14px !important;
  font-weight:500 !important;
  line-height:1.5 !important;
  resize:none !important;
}
div.stButton > button:hover, div.stDownloadButton > button:hover { transform:translateY(-3px); box-shadow:0 16px 28px rgba(107,67,214,.28); border-color:#7446e8; }
[data-testid="stExpander"] { background:rgba(255,255,255,.82); border-radius:16px; border-color:rgba(116,70,232,.12); transition:.2s ease; }
[data-testid="stExpander"]:hover { transform:translateY(-2px); box-shadow:0 10px 22px rgba(70,55,120,.10); }
div[data-baseweb="textarea"] textarea, div[data-baseweb="input"] input { border-radius:14px !important; }
@media(max-width:900px){ .metric-grid{grid-template-columns:repeat(2,1fr)} .block-container{padding:1.2rem} .hero{padding:26px 24px} }
</style>
""", unsafe_allow_html=True)


def render_report(report: str) -> None:
    parts = ['<div class="report-wrap">']
    for raw in report.splitlines():
        line = raw.strip()
        if not line:
            continue
        safe = html.escape(line[1:].strip() if line[0] in "□-·" else line)
        cls = "report-major" if line.startswith("□") else "report-minor" if line.startswith("-") else "report-detail"
        marker = "□" if cls == "report-major" else "-" if cls == "report-minor" else "·"
        parts.append(f'<div class="{cls}">{marker}&nbsp;&nbsp;{safe}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


config_path = Path("config.yaml")
config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

with st.sidebar:
    st.markdown('<div class="sidebar-brand">✦ News Pulse</div><div class="sidebar-caption">Google 뉴스 AI 모니터링</div>', unsafe_allow_html=True)
    st.subheader("모니터링 설정")
    keywords = st.text_area("키워드", "\n".join(config["keywords"]), help="한 줄에 키워드 하나씩 입력하세요.", height=118)
    excludes = st.text_area("제외어", "\n".join(config.get("exclude_words", [])), help="제목이나 설명에 이 단어가 있으면 제외합니다.", height=92)
    hours = st.number_input("수집 범위", min_value=1, max_value=720, value=int(config.get("lookback_hours", 24)), help="현재 시각 기준 최근 몇 시간의 기사를 볼지 설정합니다.")
    focus = st.text_area("보고서 관점", config.get("report_focus", ""), help="AI가 특히 주목할 분석 기준입니다.", height=118)
    run = st.button("리포트 새로 만들기  →", type="primary", use_container_width=True, help="뉴스 수집 후 OpenAI 분석과 Word 문서 생성을 실행합니다.")

st.markdown("""
<section class="hero"><div class="eyebrow">REAL-TIME NEWS INTELLIGENCE</div>
<h1>뉴스에서 신호를 찾고,<br>보고서로 바로 완성하세요.</h1>
<p>Google 뉴스 수집부터 AI 분석, Word 다운로드까지 한 화면에서 처리합니다.</p></section>
""", unsafe_allow_html=True)

if run:
    config["keywords"] = [x.strip() for x in keywords.splitlines() if x.strip()]
    config["exclude_words"] = [x.strip() for x in excludes.splitlines() if x.strip()]
    config["lookback_hours"] = int(hours)
    config["report_focus"] = focus.strip()
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    try:
        with st.status("뉴스 수집과 AI 분석을 시작합니다.", expanded=True) as status:
            st.write("Google 뉴스 RSS에서 최신 기사를 수집하고 있습니다.")
            report, items, md_path, json_path = run_once(str(config_path))
            st.write("보고서 계층을 정리하고 Word 문서를 생성하고 있습니다.")
            docx_bytes = build_report_docx(report, config["keywords"], len(items), int(hours), datetime.now())
            status.update(label=f"완료 — {len(items)}건을 분석했습니다.", state="complete", expanded=False)
        st.session_state.update(report=report, items=items, md_name=md_path.name, json_path=str(json_path), docx=docx_bytes)
    except Exception as exc:
        st.error(f"실행 중 문제가 발생했습니다: {exc}")

if "report" not in st.session_state:
    st.info("왼쪽에서 키워드를 설정한 뒤 ‘리포트 새로 만들기’를 눌러주세요.", icon="💡")
else:
    items = st.session_state["items"]
    publishers = Counter(x.source for x in items)
    metrics = [("분석 기사", f"{len(items)}건", "중복 제거 후 보고서에 반영한 기사 수"),
               ("언론사", f"{len(publishers)}곳", "수집 결과에 포함된 서로 다른 발행처 수"),
               ("모니터링", f"{len(config['keywords'])}개", "현재 등록된 검색 키워드 수"),
               ("수집 범위", f"{config['lookback_hours']}시간", "현재 시각 기준으로 조회한 과거 범위")]
    cards = "".join(f'<div class="metric-card" title="{html.escape(tip)}"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>' for label, value, tip in metrics)
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)

    report_tab, news_tab, download_tab = st.tabs(["◫  완성 보고서", "◎  수집 기사", "⇩  다운로드"])
    with report_tab:
        render_report(st.session_state["report"])
    with news_tab:
        st.caption("기사 제목을 클릭하면 상세 정보와 원문 링크가 펼쳐집니다.")
        for item in items:
            with st.expander(f"{item.title}  ·  {item.source}"):
                st.write(item.description or "제공된 요약문이 없습니다.")
                st.caption(f"키워드: {item.keyword}  |  게시: {item.published_at or '미상'}")
                st.link_button("원문 기사 열기 ↗", item.link)
    with download_tab:
        st.subheader("보고서 내보내기")
        st.write("Word 문서는 `□ → - → ·` 계층과 출처를 포함한 업무용 양식으로 생성됩니다.")
        left, right = st.columns(2)
        with left:
            st.download_button("Word 보고서 다운로드", st.session_state["docx"], file_name=f"news_pulse_report_{datetime.now():%Y%m%d}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary", use_container_width=True)
        with right:
            st.download_button("텍스트 보고서 다운로드", st.session_state["report"], file_name=st.session_state["md_name"], mime="text/markdown", use_container_width=True)
        st.caption(f"원본 수집 데이터: {st.session_state['json_path']}")
