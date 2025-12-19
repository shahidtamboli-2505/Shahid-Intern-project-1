# ui/app_case1.py
import os
import sys
import base64
from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------
# Backend import (Case 1)
# -----------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.agent_logic_case1 import run_case1_pipeline


# -----------------------------
<<<<<<< HEAD
# Helpers
# -----------------------------
def _b64_image(path: str) -> str:
    """Return base64 for image; empty string if missing."""
    try:
        if not path or not os.path.exists(path):
            return ""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def _read_bytes(path: str) -> Optional[bytes]:
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    except Exception:
        return None
    return None


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        s = str(x).strip()
        if not s:
            return default
        return int(float(s))
    except Exception:
        return default


# -----------------------------
# Pixel11-style UI CSS
=======
# Premium UI CSS (Responsive + Dark Elegant)
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
# -----------------------------
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        :root{
          --bg: #050507;
          --panel: rgba(18, 12, 28, 0.55);
          --stroke: rgba(255,255,255,0.08);

          --text: #f4f4f7;
          --muted: rgba(244,244,247,0.72);

          --purple: #7c3aed;
          --purple2:#a855f7;

          --radius: 22px;
          --pad: clamp(1rem, 2.2vw, 1.55rem);

          --fs-base: clamp(15px, 1.05vw, 17px);
          --fs-small: clamp(13px, 0.90vw, 14.5px);
          --fs-medium: clamp(16px, 1.20vw, 19px);
          --fs-title: clamp(34px, 4.1vw, 56px);
        }

        html, body, [class*="css"], p, span, div, label, small, a, li {
          font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          font-size: var(--fs-base);
          color: var(--text) !important;
        }

        #MainMenu, footer, header { visibility: hidden; }

        .block-container{
          max-width: min(96vw, 1300px);
          padding: clamp(0.9rem, 2.2vw, 2.2rem) !important;
          padding-top: clamp(6.3rem, 7vw, 7.0rem) !important;
          position: relative;
          z-index: 3;
        }

        [data-testid="stAppViewContainer"]{
          background:
            radial-gradient(900px 520px at 52% 16%, rgba(124,58,237,0.52), rgba(0,0,0,0) 62%),
            radial-gradient(760px 520px at 22% 90%, rgba(168,85,247,0.14), rgba(0,0,0,0) 60%),
            radial-gradient(720px 520px at 86% 92%, rgba(124,58,237,0.10), rgba(0,0,0,0) 62%),
            linear-gradient(180deg, #050507 0%, #050507 100%);
        }

<<<<<<< HEAD
        [data-testid="stAppViewContainer"]::before{
          content:"";
          position: fixed;
          inset: 0;
          pointer-events: none;
          background-image:
            radial-gradient(circle, rgba(168,85,247,0.35) 1px, transparent 1.8px),
            radial-gradient(circle, rgba(124,58,237,0.22) 1px, transparent 1.8px);
          background-size: 120px 120px, 180px 180px;
          background-position: 0 0, 40px 60px;
          opacity: 0.35;
          animation: drift 18s linear infinite;
          z-index: 0;
        }
        @keyframes drift {
          from { transform: translateY(0px); }
          to   { transform: translateY(-80px); }
        }

        .px-nav{
          position: fixed;
          top: 0; left: 0; right: 0;
          z-index: 9999;
          padding: 14px 22px;
          background: rgba(5,5,7,0.55);
          backdrop-filter: blur(14px);
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .px-nav-inner{
          max-width: min(96vw, 1300px);
          margin: 0 auto;
          display:flex;
          align-items:center;
          justify-content:center;
        }
        .px-brand{
          display:flex;
          align-items:center;
          gap: 14px;
        }
        .px-brand img{
          height: 66px;
          width: auto;
          display:block;
          filter: drop-shadow(0 18px 44px rgba(124,58,237,0.26));
        }
        .px-brand-title{
          font-size: 28px;
          font-weight: 950;
          letter-spacing: -0.03em;
          color: rgba(244,244,247,0.95);
          text-shadow: 0 18px 44px rgba(124,58,237,0.18);
        }

        .bg-bubbles{
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 1;
          overflow: hidden;
        }
        .bg-bubble{
          position: absolute;
          width: 44px; height: 44px;
          border-radius: 999px;
          background: rgba(124,58,237,0.34);
          border: 1px solid rgba(255,255,255,0.10);
          box-shadow: 0 22px 80px rgba(124,58,237,0.22);
          display:flex;
          align-items:center;
          justify-content:center;
          color: rgba(255,255,255,0.86);
          font-weight: 900;
          opacity: 0.92;
          animation: floaty 6.2s ease-in-out infinite;
        }
        .bg-bubble.big{
          width: 56px; height: 56px;
          background: rgba(168,85,247,0.26);
        }
        @keyframes floaty{
          0%,100% { transform: translateY(0px); }
          50%     { transform: translateY(-18px); }
        }
        .bb1{ top: 14%; left: 10%; animation-delay: .1s; }
        .bb2{ top: 16%; left: 88%; animation-delay: .7s; }
        .bb3{ top: 52%; left: 94%; animation-delay: 1.1s; }
        .bb4{ top: 74%; left: 12%; animation-delay: 1.6s; }
        .bb5{ top: 86%; left: 86%; animation-delay: 2.0s; }
        .bb6{ top: 44%; left: 6%;  animation-delay: 2.4s; }
        .bb7{ top: 90%; left: 52%; animation-delay: 2.9s; }
        .bb8{ top: 28%; left: 72%; animation-delay: 3.2s; }

=======
        [data-testid="stCaptionContainer"], .stCaption, .stMarkdown, .stText, .stAlert, .stToast {
          color: #eaf0ff !important;
        }

>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
        .card{
          background: var(--panel);
          border: 1px solid var(--stroke);
          border-radius: var(--radius);
          padding: var(--pad);
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          box-shadow: 0 22px 70px rgba(0,0,0,0.55);
          position: relative;
          z-index: 3;
        }

<<<<<<< HEAD
        .px-hero{
          position: relative;
          overflow: hidden;
          padding: clamp(2.2rem, 5vw, 3.4rem) clamp(1.2rem, 3vw, 2.2rem);
          text-align: center;
          background: rgba(10, 7, 14, 0.35);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: var(--radius);
          z-index: 3;
=======
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
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
        }
        .px-hero::before{
          content:"";
          position:absolute;
          inset:-40px;
          background: radial-gradient(520px 300px at 50% 18%, rgba(124,58,237,0.50), transparent 65%);
          opacity: 0.9;
          pointer-events:none;
        }
        .px-title{
          font-size: var(--fs-title);
          font-weight: 950;
          letter-spacing: -0.045em;
          line-height: 1.05;
          margin: .6rem 0 .45rem 0;
          position: relative;
          z-index: 2;
        }
        .px-subtitle{
          font-size: var(--fs-medium);
          font-weight: 720;
          color: rgba(244,244,247,0.74) !important;
          margin: 0;
          position: relative;
          z-index: 2;
        }
        .px-meta{
          margin-top: .75rem;
          font-size: var(--fs-small);
          font-weight: 750;
          color: rgba(244,244,247,0.70) !important;
          position: relative;
          z-index: 2;
        }

<<<<<<< HEAD
        .wave-wrap{
          margin-top: 14px;
          border-radius: 18px;
          overflow: hidden;
          opacity: .95;
          filter: drop-shadow(0 18px 60px rgba(124,58,237,0.14));
        }

        .stTextInput label, .stNumberInput label{
=======
        .stTextInput label{
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
          font-size: var(--fs-medium) !important;
          font-weight: 850 !important;
          color: rgba(244,244,247,0.92) !important;
        }
        .stTextInput input, .stNumberInput input{
          border-radius: 16px !important;
          padding: clamp(0.78rem, 1.4vw, 1.02rem) !important;
          font-size: var(--fs-medium) !important;
          background: rgba(255,255,255,0.06) !important;
          color: rgba(244,244,247,0.94) !important;
          border: 1px solid rgba(255,255,255,0.10) !important;
          box-shadow: 0 16px 45px rgba(0,0,0,0.45) !important;
        }

<<<<<<< HEAD
=======
        .stTextInput input::placeholder{
          color: rgba(234,240,255,0.55) !important;
        }

        .stTextInput input:focus{
          border: 1px solid rgba(99,102,241,0.85) !important;
          box-shadow: 0 0 0 4px rgba(99,102,241,0.22) !important;
        }

>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button{
          border-radius: 999px;
          padding: clamp(0.85rem, 1.5vw, 1.05rem) clamp(1.2rem, 2.0vw, 1.35rem);
          font-size: var(--fs-medium);
          font-weight: 950;
          border: 1px solid rgba(255,255,255,0.10);
          background: linear-gradient(135deg, rgba(124,58,237,0.95) 0%, rgba(168,85,247,0.65) 70%);
          color:#fff !important;
          box-shadow: 0 26px 90px rgba(124,58,237,0.30);
          transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover{
          transform: translateY(-2px);
          filter: brightness(1.04);
          box-shadow: 0 34px 120px rgba(124,58,237,0.40);
        }

        .logline{
          display:flex;
          align-items:center;
          gap:.8rem;
          padding:.78rem .95rem;
          border-radius: 16px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          margin: .5rem 0;
          box-shadow: 0 16px 50px rgba(0,0,0,0.45);
        }
        .dot{
          width: 11px;
          height: 11px;
          border-radius: 50%;
          background: rgba(124,58,237,0.95);
          box-shadow: 0 0 0 6px rgba(124,58,237,0.22);
        }

        [data-testid="stDataFrame"]{
          border-radius: 18px;
          overflow: hidden;
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(255,255,255,0.03);
          box-shadow: 0 22px 70px rgba(0,0,0,0.55);
        }

        .anchor{ position: relative; top: -92px; }
        .fade-in { animation: fadeIn 260ms ease-out; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }

<<<<<<< HEAD
=======
        .fade-in { animation: fadeIn 260ms ease-out; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }

>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
        @media (max-width: 900px){
          .block-container{ max-width: 98vw; padding: 1rem !important; padding-top: 6.8rem !important; }
          .px-brand img{ height: 56px; }
          .px-brand-title{ font-size: 24px; }
          .anchor{ top: -96px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


<<<<<<< HEAD
def _navbar() -> None:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    logo_path = os.path.join(base_dir, "assets", "pixel11_logo.jpeg")
    logo_b64 = _b64_image(logo_path)

    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Pixel11 Logo" />'
    else:
        logo_html = (
            '<div style="width:66px;height:66px;border-radius:16px;'
            'background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.10);'
            'display:flex;align-items:center;justify-content:center;font-weight:950;">P</div>'
        )

=======
def _hero_section() -> None:
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
    st.markdown(
        f"""
        <div class="px-nav">
          <div class="px-nav-inner">
            <div class="px-brand">
              {logo_html}
              <div class="px-brand-title">Pixel11</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _background_bubbles() -> None:
    st.markdown(
        """
        <div class="bg-bubbles">
          <div class="bg-bubble bb1">✦</div>
          <div class="bg-bubble big bb2">▶</div>
          <div class="bg-bubble bb3">⚙</div>
          <div class="bg-bubble big bb4">⌁</div>
          <div class="bg-bubble bb5">⦿</div>
          <div class="bg-bubble bb6">+</div>
          <div class="bg-bubble big bb7">∞</div>
          <div class="bg-bubble bb8">⧉</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _wave_divider() -> None:
    html = """
    <div class="wave-wrap fade-in">
      <svg viewBox="0 0 1440 180" preserveAspectRatio="none" width="100%" height="180"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="g1" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stop-color="rgba(124,58,237,0.55)"/>
            <stop offset="60%" stop-color="rgba(168,85,247,0.30)"/>
            <stop offset="100%" stop-color="rgba(124,58,237,0.10)"/>
          </linearGradient>
        </defs>

        <rect width="1440" height="180" fill="rgba(0,0,0,0)"/>
        <path d="M0,120 C160,95 260,140 380,115 C520,85 620,150 770,118
                 C930,84 1040,150 1180,110 C1300,78 1380,115 1440,95
                 L1440,180 L0,180 Z"
              fill="url(#g1)"/>

        <path d="M0,140 C190,115 300,160 430,135 C560,110 680,165 820,138
                 C980,108 1090,168 1220,130 C1340,95 1400,130 1440,110
                 L1440,180 L0,180 Z"
              fill="rgba(124,58,237,0.10)"/>
      </svg>
    </div>
    """
    components.html(html, height=190)


def _log_card(messages: list) -> None:
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


<<<<<<< HEAD
def _stats_card(stats: Dict[str, Any]) -> None:
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 📌 Summary")

    raw_count = _safe_int(stats.get("raw_count", 0), 0)
    clean_count = _safe_int(stats.get("clean_count", 0), 0)
    with_web = _safe_int(stats.get("with_website", 0), 0)
    no_web = _safe_int(stats.get("no_website", 0), 0)
    with_rating = _safe_int(stats.get("with_rating", 0), 0)

    # Case-2 stats (safe)
    case2_enabled = bool(stats.get("case2_enabled", False))
    case2_secondary = bool(stats.get("case2_secondary_search_enabled", False))
    case2_ran = _safe_int(stats.get("case2_ran", 0), 0)
    case2_err = _safe_int(stats.get("case2_errors", 0), 0)

    case2_line = "OFF"
    if case2_enabled and case2_secondary:
        case2_line = f"ON • Processed: {case2_ran} • Errors: {case2_err}"

    st.markdown(
        f"""
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: .75rem;">
          <div class="logline"><span class="dot"></span><span style="font-weight:900;">Raw: {raw_count}</span></div>
          <div class="logline"><span class="dot"></span><span style="font-weight:900;">Clean: {clean_count}</span></div>
          <div class="logline"><span class="dot"></span><span style="font-weight:900;">Has Website: {with_web}</span></div>
          <div class="logline"><span class="dot"></span><span style="font-weight:900;">No Website: {no_web}</span></div>
          <div class="logline" style="grid-column: 1 / -1;"><span class="dot"></span><span style="font-weight:900;">With Google Rating: {with_rating}</span></div>
          <div class="logline" style="grid-column: 1 / -1;"><span class="dot"></span><span style="font-weight:900;">Case-2 (Management): {case2_line}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


=======
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67
def main() -> None:
    st.set_page_config(
        page_title="Data Mining Platform — Pixel11 Theme",
        page_icon="🧩",
        layout="wide",
    )

    _inject_css()
    _background_bubbles()
    _navbar()

    # Session state
    if "started" not in st.session_state:
        st.session_state.started = False
    if "just_started" not in st.session_state:
        st.session_state.just_started = False

    # Output state
    if "result_df" not in st.session_state:
        st.session_state.result_df = pd.DataFrame()
        st.session_state.caption = "Run a search to preview real results."
        st.session_state.excel_bytes = None
        st.session_state.excel_name = None
<<<<<<< HEAD
        st.session_state.stats = {}

    # HERO
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.markdown(
        f"""
        <div class="px-hero fade-in">
          <div class="px-title">Grow fast, Build faster</div>
          <div class="px-subtitle">Search nearby organizations and export clean Excel — real output preview.</div>
          <div class="px-meta">Status: <b>Ready ✅</b> • {now}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _wave_divider()
    st.write("")

    # First screen CTA
    if not st.session_state.started:
        cta = st.button("🚀 Let’s get started", use_container_width=True)
        if cta:
            st.session_state.started = True
            st.session_state.just_started = True
            st.rerun()
        return

    # Anchor target
    st.markdown('<div id="search" class="anchor"></div>', unsafe_allow_html=True)

    # Smooth scroll after Get Started
    if st.session_state.just_started:
        st.markdown(
            """
            <script>
              setTimeout(() => {
                const el = document.getElementById("search");
                if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
              }, 250);
            </script>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.just_started = False

    # Search card
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🔎 Search")
    st.caption("Case 1 (Google Places): results + website + rating columns. Case 2 can be enabled for management scraping.")

    c1, c2, c3 = st.columns([1.15, 1.15, 1.4], gap="large")
    with c1:
        st.text_input("Enter your location", placeholder="Pune, Maharashtra", key="location_input")
    with c2:
        st.text_input("Enter specific place or area", placeholder="Bhosari / Chakan / Hinjewadi", key="place_input")
    with c3:
        st.text_input("Enter what you want to find", placeholder="manufacturing / hospitals / colleges", key="query_input")

    a1, a2, a3 = st.columns([1.15, 1.35, 1.5], gap="large")
    with a1:
        st.number_input(
            "How many results (max 100)",
            min_value=1,
            max_value=100,
            value=20,
            step=1,
            key="top_n_input",
        )
    with a2:
        st.toggle(
            "Verbose terminal logs",
            value=False,
            key="debug_toggle",
            help="Turn ON only if you want to see page-by-page logs in terminal.",
        )
    with a3:
        # ✅ NOW CONNECTED TO BACKEND (env vars)
        st.toggle(
            "Enable Case 2 (top-level management)",
            value=False,
            key="case2_toggle",
            help="If ON, backend will scrape website team/leadership pages (public info only).",
        )

    generate_clicked = st.button("✨ Generate Data", use_container_width=True)

    st.markdown(
        "<div style='color: rgba(244,244,247,0.70); font-weight:800; margin-top:.65rem;'>"
        "Example: <b>hospitals</b> in <b>Hinjewadi</b>, <b>Pune</b></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
=======
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67

    if generate_clicked:
        location = (st.session_state.get("location_input") or "").strip()
        place = (st.session_state.get("place_input") or "").strip()
        query = (st.session_state.get("query_input") or "").strip()
        top_n = int(st.session_state.get("top_n_input") or 20)
        top_n = max(1, min(top_n, 100))
        debug = bool(st.session_state.get("debug_toggle", False))
        case2_on = bool(st.session_state.get("case2_toggle", False))

        # ✅ Set runtime env vars for backend config
        # (backend reads env in config.py)
        os.environ["CASE2_ENABLED"] = "true" if case2_on else "false"
        os.environ["CASE2_ENABLE_SECONDARY_SEARCH"] = "true" if case2_on else "false"

        if not location:
            st.error("Please enter your location.")
            st.stop()
        if not query:
            st.error("Please enter what you want to find.")
            st.stop()

        logs = [
            f"Case 1 started… (Top N = {top_n})",
            "Fetching Google Places…",
            "Cleaning & de-duplication…",
        ]
        if case2_on:
            logs.append("Case 2 enabled: scraping management from websites…")
        logs.append("Generating Excel…")

        _log_card(logs)

        try:
            with st.spinner("Fetching real results…"):
                result = run_case1_pipeline(
                    query=query,
                    location=location,
                    place=place,
                    top_n=top_n,
                    use_gpt=False,
                    debug=debug,
                )
        except Exception as e:
            msg = str(e)
            if "GOOGLE_PLACES_API_KEY" in msg:
                st.error("❌ GOOGLE_PLACES_API_KEY missing. Set it in PowerShell or .env and rerun.")
                st.info('PowerShell:  $env:GOOGLE_PLACES_API_KEY="YOUR_KEY"')
            else:
                st.error(f"❌ Error: {e}")
            st.stop()

        stats = result.get("stats", {}) or {}
<<<<<<< HEAD
        cleaned_rows = result.get("cleaned_rows") or []
        excel_bytes = result.get("excel_bytes")
        excel_path = result.get("excel_path")
=======
>>>>>>> e8cf0b1e8531f550d9e18b0c52f50c0b433d8c67

        df = pd.DataFrame(cleaned_rows) if cleaned_rows else pd.DataFrame()
        if (not excel_bytes) and excel_path:
            excel_bytes = _read_bytes(excel_path)

        raw_count = _safe_int(stats.get("raw_count", 0), 0)
        clean_count = _safe_int(stats.get("clean_count", 0), len(df))

        if not df.empty and excel_bytes:
            st.session_state.result_df = df
            st.session_state.stats = stats
            st.session_state.caption = (
                f"Real backend output • Raw: {raw_count} | Clean: {clean_count} | Showing: {min(len(df), top_n)}"
            )
            st.session_state.excel_bytes = excel_bytes
            st.session_state.excel_name = os.path.basename(excel_path) if excel_path else (
                f"case1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            st.success("Done ✅ Data generated successfully.")
        else:
            st.session_state.result_df = pd.DataFrame()
            st.session_state.stats = {}
            st.session_state.excel_bytes = None
            st.session_state.excel_name = None

            if df.empty:
                st.error("No results found. Try changing query/place or increase area (location).")
            else:
                st.error("Excel output missing. Check terminal logs.")

    # Output layout
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
        if st.session_state.stats:
            _stats_card(st.session_state.stats)

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
              <div style="font-weight:950; font-size:1.05rem; margin-bottom:.25rem;">✅ Notes</div>
              <div style="color: rgba(244,244,247,0.70); font-weight:800;">• Case 1: nearby organizations + website + rating</div>
              <div style="color: rgba(244,244,247,0.70); font-weight:800;">• Case 2: top-level management (public website scraping)</div>
              <div style="color: rgba(244,244,247,0.70); font-weight:800;">• Try queries: “hospitals”, “colleges”, “manufacturing”, “schools”</div>
              <div style="color: rgba(244,244,247,0.70); font-weight:800;">• Use Place to narrow: “Hinjewadi”, “Bhosari”, “Chakan”</div>
              <div style="color: rgba(244,244,247,0.70); font-weight:800;">• Top N is capped at 100 (UI + backend)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="text-align:center; margin-top: 1.2rem; opacity:.78; font-size: 0.92rem; font-weight: 750;">
          Built for real-time business discovery • Excel-ready output
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
