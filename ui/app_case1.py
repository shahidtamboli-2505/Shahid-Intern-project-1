# ui/app_case1.py
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

# -----------------------------
# Backend import (Case 1 only)
# -----------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.agent_logic_case1 import run_case1_pipeline


# -----------------------------
# Premium UI CSS (Responsive + Dark Elegant)
# -----------------------------
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        :root{
          --fs-base: clamp(15px, 1.05vw, 17px);
          --fs-small: clamp(13px, 0.90vw, 14.5px);
          --fs-medium: clamp(16px, 1.20vw, 19px);
          --fs-title: clamp(28px, 3.2vw, 46px);

          --pad-card: clamp(1rem, 2.2vw, 1.55rem);
          --radius: 22px;
        }

        html, body, [class*="css"], p, span, div, label, small, a, li {
          font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          font-size: var(--fs-base);
          color: #eaf0ff !important;
        }

        #MainMenu, footer, header { visibility: hidden; }

        .block-container{
          max-width: min(96vw, 1500px);
          padding: clamp(0.9rem, 2.6vw, 2.6rem) !important;
        }

        [data-testid="stAppViewContainer"]{
          background:
            radial-gradient(1100px 640px at 12% 12%, rgba(99,102,241,0.22), transparent 55%),
            radial-gradient(1050px 600px at 88% 18%, rgba(14,165,233,0.18), transparent 58%),
            radial-gradient(900px 520px at 52% 92%, rgba(34,197,94,0.12), transparent 56%),
            linear-gradient(180deg, #070A12 0%, #0B1220 45%, #070A12 100%);
        }

        [data-testid="stCaptionContainer"], .stCaption, .stMarkdown, .stText, .stAlert, .stToast {
          color: #eaf0ff !important;
        }

        .card{
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.12);
          border-radius: var(--radius);
          padding: var(--pad-card);
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          box-shadow: 0 22px 60px rgba(0,0,0,0.35);
        }

        .pill{
          display:inline-flex;
          align-items:center;
          gap:.55rem;
          padding:.45rem .95rem;
          border-radius:999px;
          font-size: var(--fs-small);
          font-weight: 850;
          color:#eaf0ff;
          background: rgba(99,102,241,0.12);
          border: 1px solid rgba(99,102,241,0.28);
        }

        .title{
          font-size: var(--fs-title);
          font-weight: 950;
          letter-spacing: -0.04em;
          line-height: 1.06;
          color:#f3f6ff !important;
          margin: .55rem 0 .15rem 0;
        }

        .subtitle{
          font-size: var(--fs-medium);
          font-weight: 720;
          color:#eaf0ff !important;
          opacity:.92;
          margin: 0;
        }

        .muted{
          font-size: var(--fs-small);
          font-weight: 650;
          color:#d7e2ff !important;
          opacity: .85;
        }

        .stTextInput label{
          font-size: var(--fs-medium) !important;
          font-weight: 850 !important;
          color:#eaf0ff !important;
        }

        .stTextInput input{
          border-radius: 16px !important;
          padding: clamp(0.78rem, 1.4vw, 1.02rem) !important;
          font-size: var(--fs-medium) !important;
          background: rgba(255,255,255,0.08) !important;
          color: #f3f6ff !important;
          border: 1px solid rgba(255,255,255,0.16) !important;
          box-shadow: 0 12px 26px rgba(0,0,0,0.25) !important;
        }

        .stTextInput input::placeholder{
          color: rgba(234,240,255,0.55) !important;
        }

        .stTextInput input:focus{
          border: 1px solid rgba(99,102,241,0.85) !important;
          box-shadow: 0 0 0 4px rgba(99,102,241,0.22) !important;
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button{
          border-radius: 18px;
          padding: clamp(0.85rem, 1.5vw, 1.05rem) clamp(1.05rem, 1.8vw, 1.2rem);
          font-size: var(--fs-medium);
          font-weight: 950;
          border: 1px solid rgba(255,255,255,0.14);
          background: linear-gradient(135deg, #4f46e5 0%, #0ea5e9 55%, #22c55e 140%);
          color:#fff !important;
          box-shadow: 0 20px 52px rgba(79,70,229,0.35);
          transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover{
          transform: translateY(-2px);
          filter: brightness(1.05);
          box-shadow: 0 28px 70px rgba(79,70,229,0.45);
        }

        .logline{
          display:flex;
          align-items:center;
          gap:.8rem;
          padding:.78rem .95rem;
          border-radius: 16px;
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.12);
          margin: .5rem 0;
          box-shadow: 0 16px 36px rgba(0,0,0,0.28);
        }

        .dot{
          width: 11px;
          height: 11px;
          border-radius: 50%;
          background: #4f46e5;
          box-shadow: 0 0 0 5px rgba(79,70,229,0.22);
        }

        [data-testid="stDataFrame"]{
          border-radius: 18px;
          overflow: hidden;
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(255,255,255,0.05);
          box-shadow: 0 18px 44px rgba(0,0,0,0.32);
        }

        .fade-in { animation: fadeIn 260ms ease-out; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 900px){
          .block-container{ max-width: 98vw; padding: 1rem !important; }
          .card{ padding: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _hero_section() -> None:
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.markdown(
        f"""
        <div class="card fade-in">
          <div style="display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
            <div>
              <div class="pill">🧩 pixel11 • Real Businesses</div>
              <div class="title">Data Mining Platform</div>
              <div class="subtitle">Search any category: hospitals • schools • colleges • industries • services</div>
              <div class="muted" style="margin-top:.35rem;">
                Professional output • Clean Excel export • Live results preview
              </div>
            </div>
            <div style="text-align:right; min-width: 220px;">
              <div class="muted" style="font-weight:800;">Status</div>
              <div style="font-weight:900; font-size:1.02rem;">Ready ✅</div>
              <div class="muted" style="margin-top:.25rem;">{now}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _log_card(messages: list[str]) -> None:
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🧾 Status")
    for msg in messages:
        st.markdown(
            f"""
            <div class="logline">
              <span class="dot"></span>
              <span style="font-weight:900;">{msg}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _results_card(df: pd.DataFrame, caption: str) -> None:
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 📊 Preview")
    st.caption(caption)
    st.dataframe(df, use_container_width=True, height=340)
    st.markdown("</div>", unsafe_allow_html=True)


def _download_card(excel_bytes: bytes, file_name: str) -> None:
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### ⬇️ Export")
    st.caption("Download the Excel file generated by the backend pipeline.")
    st.download_button(
        "📥 Download Excel",
        data=excel_bytes,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="Data Mining Platform — pixel11",
        page_icon="🧩",
        layout="wide",
    )

    _inject_css()
    _hero_section()
    st.write("")

    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🔎 Search")
    st.caption("Tip: Keep query short (e.g. “hospitals”, “schools”, “colleges”, “manufacturing”, “restaurants”).")

    c1, c2, c3 = st.columns([1.15, 1.15, 1.4], gap="large")
    with c1:
        st.text_input("Enter your location", placeholder="Pune, Maharashtra", key="location_input")
    with c2:
        st.text_input("Enter specific place or area", placeholder="Hinjewadi Phase 2", key="place_input")
    with c3:
        st.text_input("Enter what you want to find", placeholder="hospitals", key="query_input")

    col_btn_left, col_btn_right = st.columns([6, 2])
    with col_btn_left:
        st.markdown("<div class='muted'>Example: <b>hospitals</b> in <b>Hinjewadi</b>, <b>Pune</b></div>", unsafe_allow_html=True)
    with col_btn_right:
        generate_clicked = st.button("✨ Generate Data", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if "result_df" not in st.session_state:
        st.session_state.result_df = pd.DataFrame()
        st.session_state.caption = "Run a search to preview real results."
        st.session_state.excel_bytes = None
        st.session_state.excel_name = None

    if generate_clicked:
        location = (st.session_state.get("location_input") or "").strip()
        place = (st.session_state.get("place_input") or "").strip()
        query = (st.session_state.get("query_input") or "").strip()

        if not location:
            st.error("Please enter your location.")
            st.stop()
        if not query:
            st.error("Please enter what you want to find.")
            st.stop()

        logs = ["pixel11 query started…", "Cleaning & de-duplication…", "Excel generated…"]
        st.write("")
        _log_card(logs)

        with st.spinner("Fetching real results from pixel11…"):
            result = run_case1_pipeline(
                query=query,
                location=location,
                place=place,
                use_gpt=False,
            )

        excel_path = result.get("excel_path")
        stats = result.get("stats", {}) or {}

        if excel_path and os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
            st.session_state.result_df = df
            st.session_state.caption = (
                f"Real backend output • Raw: {stats.get('raw_count', 0)} | Clean: {stats.get('clean_count', 0)}"
            )

            with open(excel_path, "rb") as f:
                st.session_state.excel_bytes = f.read()
            st.session_state.excel_name = os.path.basename(excel_path)

            st.success("Done ✅ Data generated successfully.")
        else:
            st.error("Excel file not found. Please try again.")

    st.write("")
    left, right = st.columns([3.2, 2], gap="large")

    with left:
        if st.session_state.result_df is not None and not st.session_state.result_df.empty:
            _results_card(st.session_state.result_df, st.session_state.caption)
        else:
            st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
            st.markdown("### 📊 Preview")
            st.caption(st.session_state.caption)
            st.info("No data yet. Click **Generate Data** to fetch real results.")
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if st.session_state.excel_bytes and st.session_state.excel_name:
            _download_card(st.session_state.excel_bytes, st.session_state.excel_name)
        else:
            st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
            st.markdown("### ⬇️ Export")
            st.caption("Run the pipeline to enable Excel download.")
            st.info("Excel download will appear here after data is generated.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="card fade-in" style="margin-top:1rem;">
              <div style="font-weight:900; font-size:1.05rem; margin-bottom:.25rem;">✅ Notes</div>
              <div class="muted">• Data source: pixel11</div>
              <div class="muted">• Better queries: “hospitals”, “schools”, “colleges”, “manufacturing”</div>
              <div class="muted">• Use Place to narrow: “Hinjewadi”, “Bhosari”, “Chakan”</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="text-align:center; margin-top: 1.1rem; opacity:.8; font-size: 0.92rem; font-weight: 700;">
          Built for real-time business discovery • pixel11 only • Excel-ready output
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
