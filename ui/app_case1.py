# ui/app_case1.py
import io

import pandas as pd
import streamlit as st


# -----------------------------
# Demo data + demo excel helpers
# -----------------------------
def load_demo_data() -> pd.DataFrame:
    """Return a small sample DataFrame as a placeholder before backend integration."""
    data = [
        {
            "Industry Name": "Shree Ganesh Precision Works",
            "Category": "Manufacturing",
            "Address": "MIDC Bhosari, Pune, Maharashtra",
            "City": "Pune",
            "Contact Number": "+91 98765 43210",
            "Website": "https://example.com/ganesh-precision",
        },
        {
            "Industry Name": "Apex Industrial Fabricators",
            "Category": "Manufacturing",
            "Address": "Chakan Industrial Area, Pune, Maharashtra",
            "City": "Pune",
            "Contact Number": "+91 91234 56789",
            "Website": "https://example.com/apex-fabricators",
        },
        {
            "Industry Name": "BlueLine Plastics Pvt. Ltd.",
            "Category": "Manufacturing",
            "Address": "Hinjewadi Phase 2, Pune, Maharashtra",
            "City": "Pune",
            "Contact Number": "+91 99887 77665",
            "Website": "https://example.com/blueline-plastics",
        },
        {
            "Industry Name": "Kuber Metal Components",
            "Category": "Manufacturing",
            "Address": "Talegaon MIDC, Pune, Maharashtra",
            "City": "Pune",
            "Contact Number": "+91 90000 11223",
            "Website": "https://example.com/kuber-metals",
        },
        {
            "Industry Name": "Nova Packaging Solutions",
            "Category": "Manufacturing",
            "Address": "Pimpri-Chinchwad, Pune, Maharashtra",
            "City": "Pune",
            "Contact Number": "+91 95555 44332",
            "Website": "https://example.com/nova-packaging",
        },
    ]
    return pd.DataFrame(data)


def create_demo_excel(df: pd.DataFrame) -> bytes:
    """Generate a dummy Excel file and return bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Demo_Results")
    return output.getvalue()


# -----------------------------
# UI styling (Blue SaaS Theme)
# -----------------------------
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* Global layout */
        .block-container {
            max-width: 1180px;
            padding-top: 2.4rem;
            padding-bottom: 2.4rem;
        }

        /* Pastel light-blue SaaS background (NO purple) */
        [data-testid="stAppViewContainer"] {
            background:
              radial-gradient(900px 450px at 20% 10%, rgba(14, 165, 233, 0.14), transparent 60%),
              radial-gradient(800px 420px at 85% 15%, rgba(56, 189, 248, 0.12), transparent 55%),
              linear-gradient(180deg, #f4f9ff 0%, #eef6ff 40%, #f6fbff 100%);
        }

        /* Force readable text colors everywhere */
        html, body, [class*="css"], p, span, div, label, small, a, li {
            color: #111 !important;
            font-family: "Inter", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont;
        }

        /* Remove default Streamlit faded label styling */
        [data-testid="stCaptionContainer"] { color: #111 !important; opacity: 1 !important; }
        .stCaption, .stMarkdown, .stText, .stAlert, .stToast { color: #111 !important; }

        /* Card (glass, readable) */
        .card {
            background: rgba(255, 255, 255, 0.84);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 22px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            padding: 1.25rem 1.3rem;
            box-shadow:
              0 16px 34px rgba(0, 0, 0, 0.08),
              inset 0 1px 0 rgba(255, 255, 255, 0.65);
        }

        /* Pill */
        .pill {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .35rem .8rem;
            border-radius: 999px;
            font-size: .85rem;
            font-weight: 600;
            background: rgba(14, 165, 233, 0.10);
            color: #111;
            border: 1px solid rgba(14, 165, 233, 0.25);
        }

        /* Title & subtitle */
        .title {
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0.5rem 0 0.25rem 0;
            color: #111;
        }

        .subtitle {
            font-size: 1.05rem;
            font-weight: 600;
            color: #111;
            margin: 0 0 .35rem 0;
        }

        .muted {
            color: #111;
            font-size: .95rem;
            font-weight: 500;
        }

        /* Section headings inside cards */
        h1, h2, h3, h4, h5, h6 { color: #111 !important; }
        .stMarkdown h3 { margin-bottom: 0.4rem; }

        /* Inputs: white bg, black text, soft gray border, blue focus */
        .stTextInput input {
            border-radius: 16px !important;
            padding: 0.72rem 0.9rem !important;
            background: #fff !important;
            color: #111 !important;
            border: 1px solid #ccc !important;
            box-shadow: none !important;
        }
        .stTextInput input:focus {
            border: 1px solid rgba(14,165,233,0.85) !important;
            box-shadow: 0 0 0 4px rgba(14,165,233,0.18) !important;
        }

        /* Buttons: modern blue */
        div[data-testid="stButton"] > button {
            border-radius: 16px;
            padding: 0.78rem 1.05rem;
            font-weight: 750;
            border: 1px solid rgba(14,165,233,0.35);
            background: #0ea5e9;
            color: #fff !important;
            box-shadow: 0 14px 26px rgba(14, 165, 233, 0.22);
            transition: all 0.22s ease;
        }
        div[data-testid="stButton"] > button:hover {
            background: #0284c7; /* darker on hover */
            border-color: rgba(2,132,199,0.6);
            transform: translateY(-1px);
            box-shadow: 0 18px 34px rgba(14, 165, 233, 0.28);
        }

        /* Download button styling */
        div[data-testid="stDownloadButton"] > button {
            border-radius: 16px;
            padding: 0.78rem 1.05rem;
            font-weight: 750;
            border: 1px solid rgba(14,165,233,0.35);
            background: #0ea5e9;
            color: #fff !important;
            box-shadow: 0 14px 26px rgba(14, 165, 233, 0.22);
            transition: all 0.22s ease;
        }
        div[data-testid="stDownloadButton"] > button:hover {
            background: #0284c7;
            border-color: rgba(2,132,199,0.6);
            transform: translateY(-1px);
            box-shadow: 0 18px 34px rgba(14, 165, 233, 0.28);
        }

        /* Logs: high contrast */
        .logline {
            display: flex;
            align-items: center;
            gap: .65rem;
            padding: .6rem .75rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid rgba(0, 0, 0, 0.08);
            margin: .4rem 0;
        }
        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #0ea5e9;
            box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.18);
        }

        /* Dataframe container */
        [data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(255,255,255,0.95);
        }

        /* Captions: keep readable (not faded) */
        .stCaption, [data-testid="stCaptionContainer"] {
            opacity: 1 !important;
            color: #111 !important;
            font-weight: 600 !important;
        }

        /* Subtle fade-in */
        .fade-in { animation: fadeIn 260ms ease-out; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# UI sections
# -----------------------------
def _hero_section() -> None:
    st.markdown(
        """
        <div class="card fade-in" style="text-align:center;">
          <div class="pill">🏭 Case 1 • Data Mining Platform</div>
          <div class="title">Manufacturing Industries</div>
          <div class="subtitle">Case 1 – Manufacturing Industries Data Mining Platform</div>
          <div class="muted" style="max-width: 780px; margin: 0.45rem auto 0 auto;">
            A clean, modern SaaS-style dashboard UI to discover, preview, and export manufacturing industry data.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _log_card(messages: list[str]) -> None:
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🧾 Status Logs")
    st.caption("Placeholder logs (demo) — backend integration will replace these later.")
    for msg in messages:
        st.markdown(
            f"""
            <div class="logline">
              <span class="dot"></span>
              <span style="font-weight:800; color:#111;">{msg}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _results_card(df: pd.DataFrame) -> None:
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 📊 Preview Table")
    st.caption("Demo data preview (placeholder).")
    st.dataframe(df, use_container_width=True, height=300)
    st.markdown("</div>", unsafe_allow_html=True)


def _download_card(excel_bytes: bytes) -> None:
    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### ⬇️ Export")
    st.caption("Download a demo Excel file now. Later this will export the real dataset.")
    st.download_button(
        "📥 Download Excel",
        data=excel_bytes,
        file_name="case1_demo_manufacturing_industries.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Main UI
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

    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🔎 Search")
    st.caption("Enter a query like: Manufacturing industries near Pune")

    # NEW INPUTS: vertical order (location -> place/area -> query)
    location = st.text_input(
        "Enter your location",
        placeholder="Pune, Maharashtra",
        key="location_input",
    )
    place = st.text_input(
        "Enter specific place or area",
        placeholder="Hinjewadi Phase 2",
        key="place_input",
    )
    query = st.text_input(
        "Enter your search query (e.g., Manufacturing industries near Pune)",
        placeholder="Manufacturing industries near Pune",
        key="query_input",
    )

    col_btn_left, col_btn_right = st.columns([5, 2])
    with col_btn_left:
        st.markdown("<div style='height: 0.15rem;'></div>", unsafe_allow_html=True)
    with col_btn_right:
        st.markdown("<div style='height: 0.15rem;'></div>", unsafe_allow_html=True)
        generate_clicked = st.button("✨ Generate Data", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if "demo_df" not in st.session_state:
        st.session_state.demo_df = load_demo_data()
    if "excel_bytes" not in st.session_state:
        st.session_state.excel_bytes = create_demo_excel(st.session_state.demo_df)

    if generate_clicked:
        # Read inputs from session_state (for future backend integration)
        location = st.session_state.get("location_input")
        place = st.session_state.get("place_input")
        query = st.session_state.get("query_input")

        # TODO: use location, place, query for backend scraping

        logs = ["Scraping started…", "Mining data…", "Excel generated…"]
        st.session_state.demo_df = load_demo_data()
        st.session_state.excel_bytes = create_demo_excel(st.session_state.demo_df)
        st.write("")
        _log_card(logs)

    st.write("")
    left, right = st.columns([3, 2], gap="large")
    with left:
        _results_card(st.session_state.demo_df)
    with right:
        _download_card(st.session_state.excel_bytes)

    st.markdown(
        """
        <div style="text-align:center; margin-top: 1rem; color: #111; font-size: 0.92rem; font-weight: 650;">
          ✅ Clean SaaS Blue Theme • Case 1 only • Backend integration next
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
