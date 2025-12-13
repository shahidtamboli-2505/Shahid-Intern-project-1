# ui/app_case1.py

import io
import pandas as pd
import streamlit as st
import sys
import os

# Add project root to Python path so backend imports work
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

# Import backend pipeline
from run_case1 import run_case1
from backend.db import fetch_businesses_by_query


# -----------------------------
# UI styling (Blue SaaS Theme)
# -----------------------------
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width:1180px; padding-top:2rem; padding-bottom:2rem; }
        [data-testid="stAppViewContainer"] {
            background:
              radial-gradient(900px 450px at 20% 10%, rgba(14,165,233,0.14), transparent 60%),
              radial-gradient(800px 420px at 85% 15%, rgba(56,189,248,0.12), transparent 55%),
              linear-gradient(180deg,#f4f9ff 0%,#eef6ff 40%,#f6fbff 100%);
        }
        html, body, [class*="css"], p, span, div, label, small, a, li {
            color:#111 !important; font-family:"Inter","Segoe UI",system-ui;
        }
        .card {
            background:rgba(255,255,255,0.84);
            backdrop-filter:blur(10px);
            border-radius:22px;
            border:1px solid rgba(0,0,0,0.08);
            padding:1.25rem 1.3rem;
            box-shadow:0 12px 26px rgba(0,0,0,0.08);
        }
        .pill {
            display:inline-flex; gap:.45rem; padding:.35rem .8rem;
            border-radius:999px; font-size:.85rem; font-weight:600;
            background:rgba(14,165,233,.10); border:1px solid rgba(14,165,233,.25);
        }
        .title { font-size:2.25rem; font-weight:800; letter-spacing:-0.02em; margin:.5rem 0; }
        .subtitle { font-size:1.05rem; font-weight:600; margin-bottom:.35rem; }
        .stTextInput input {
            border-radius:16px !important; padding:.72rem .9rem !important;
            background:#fff !important; color:#111 !important; border:1px solid #ccc !important;
        }
        .stTextInput input:focus {
            border:1px solid rgba(14,165,233,0.85) !important;
            box-shadow:0 0 0 4px rgba(14,165,233,0.18) !important;
        }
        div[data-testid="stButton"] > button {
            border-radius:16px; padding:.8rem 1.1rem; font-weight:750;
            background:#0ea5e9; color:#fff !important; border:1px solid rgba(14,165,233,.35);
            transition:all .2s ease;
        }
        div[data-testid="stButton"] > button:hover {
            background:#0284c7; transform:translateY(-1px);
        }
        div[data-testid="stDownloadButton"] > button {
            border-radius:16px; padding:.8rem 1.1rem; font-weight:750;
            background:#0ea5e9; color:#fff !important;
        }
        .logline {
            display:flex; align-items:center; gap:.65rem;
            padding:.6rem .75rem; border-radius:14px;
            background:rgba(255,255,255,.90);
            border:1px solid rgba(0,0,0,.08);
        }
        .dot {
            width:10px; height:10px; border-radius:50%;
            background:#0ea5e9; box-shadow:0 0 0 4px rgba(14,165,233,.18);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# UI Sections
# -----------------------------
def _hero_section() -> None:
    st.markdown(
        """
        <div class="card" style="text-align:center;">
          <div class="pill">🏭 Case 1 • Data Mining Platform</div>
          <div class="title">Manufacturing Industries</div>
          <div class="subtitle">Real-time Scraping • Cleaning • Excel Export</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _log_card(messages: list[str]) -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🧾 Status Logs")
    for msg in messages:
        st.markdown(
            f"""
            <div class="logline">
              <span class="dot"></span>
              <span style="font-weight:700;">{msg}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _results_card(df: pd.DataFrame) -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📊 Results Preview")
    st.dataframe(df, use_container_width=True, height=350)
    st.markdown("</div>", unsafe_allow_html=True)


def _download_card(excel_bytes: bytes, name: str) -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⬇️ Download Excel File")
    st.download_button(
        "📥 Download Excel",
        data=excel_bytes,
        file_name=name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# MAIN APP
# -----------------------------
def main() -> None:
    st.set_page_config(
        page_title="Case 1 — Manufacturing Industries",
        page_icon="🏭",
        layout="wide",
    )

    _inject_css()
    _hero_section()
    st.write("")

    # ---------- INPUT CARD ----------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🔎 Search Manufacturing Industries")

    search_query = st.text_input(
        "Enter search query",
        placeholder="Manufacturing industries near Pune",
    )

    generate_btn = st.button("✨ Generate Data", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # First initialization
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if "excel_bytes" not in st.session_state:
        st.session_state.excel_bytes = None

    # ---------- WHEN USER CLICKS GENERATE ----------
    if generate_btn:
        try:
            with st.spinner("⏳ Scraping IndiaMART • Cleaning • Generating Excel…"):
                # Run backend pipeline
                excel_path = run_case1(search_query, use_cache=False)

                # Fetch cleaned business data from DB
                data = fetch_businesses_by_query(search_query)
                df = pd.DataFrame(data)

                # Save into session
                st.session_state.df = df

                # Convert Excel to bytes
                with open(excel_path, "rb") as f:
                    st.session_state.excel_bytes = f.read()

            logs = [
                "Connected to IndiaMART…",
                "Scraped business pages…",
                "Cleaned + categorized dataset…",
                "Saved to SQLite database…",
                "Excel sheet generated…",
            ]
            _log_card(logs)

        except Exception as e:
            st.error(f"❌ Error occurred: {e}")

    # ---------- RESULTS PREVIEW ----------
    if not st.session_state.df.empty:
        left, right = st.columns([3, 2])
        with left:
            _results_card(st.session_state.df)
        with right:
            _download_card(
                st.session_state.excel_bytes,
                "case1_manufacturing_results.xlsx",
            )

    st.markdown(
        "<div style='text-align:center; margin-top:1rem; font-size:.9rem;'>"
        "Built with 💙 Streamlit • Case 1 Backend Integrated"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
