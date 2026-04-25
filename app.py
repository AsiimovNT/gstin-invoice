"""
GST Invoice Extractor — Local Streamlit App
Run: streamlit run app.py
"""

import tempfile
import altair as alt
import pandas as pd
import streamlit as st
from pathlib import Path
from extractor import extract_from_multiple_pdfs
from excel_writer import write_excel


# ── Indian number formatter ───────────────────────────────────────────────────
def fmt_inr(amount: float) -> str:
    amount = int(round(amount))
    s = str(abs(amount))
    if len(s) <= 3:
        result = s
    else:
        last3 = s[-3:]
        rest   = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        result = ",".join(reversed(groups)) + "," + last3
    return f"₹{'-' if amount < 0 else ''}{result}"


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GST Invoice Extractor",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
if "dark_mode" not in st.session_state: st.session_state.dark_mode = False
if "records"   not in st.session_state: st.session_state.records   = []
if "files_key" not in st.session_state: st.session_state.files_key = ""

# ── STEP 1: Handle theme toggle BEFORE T dict is built ───────────────────────
# Placing the button here means dark_mode is updated in the same rerun —
# no st.rerun() needed, so file uploader state is never disturbed.
with st.sidebar:
    toggle_label = "☀️  Light Mode" if st.session_state.dark_mode else "🌙  Dark Mode"
    if st.button(toggle_label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
    st.markdown("---")

# ── STEP 2: Build theme token dict from the (possibly just-updated) state ────
dark = st.session_state.dark_mode

if dark:
    T = {
        "app_bg":         "#0E1117",
        "card_bg":        "#1C2333",
        "card_border":    "#4A7FD4",
        "card_val":       "#93C8FF",
        "card_label":     "#8A9BB5",
        "header_grad":    "linear-gradient(135deg, #0D1B3E 0%, #1A3A72 100%)",
        "header_sub":     "#7AAEE0",
        "sidebar_grad":   "linear-gradient(160deg, #0A1628 0%, #152B55 100%)",
        "sidebar_txt":    "#C8D8F0",
        "sidebar_border": "#2A4070",
        "section_hdr":    "#93C8FF",
        "body_txt":       "#D0DCF0",
        "footer_bg":      "#141C2E",
        "footer_txt":     "#6A85B0",
        "footer_brand":   "#7AAEE0",
        "btn_bg":         "#1A3A72",
        "btn_hover":      "#4A7FD4",
        "divider":        "#2A3A55",
        "chart_color":    "#4A7FD4",
        "shadow":         "0 2px 12px rgba(0,0,0,0.4)",
    }
else:
    T = {
        "app_bg":         "#F0F4FF",
        "card_bg":        "#FFFFFF",
        "card_border":    "#2E5EA8",
        "card_val":       "#1F3864",
        "card_label":     "#7F8C8D",
        "header_grad":    "linear-gradient(135deg, #1F3864 0%, #2E5EA8 100%)",
        "header_sub":     "#BDD7EE",
        "sidebar_grad":   "linear-gradient(160deg, #1F3864 0%, #2E5EA8 100%)",
        "sidebar_txt":    "#FFFFFF",
        "sidebar_border": "#3A6DBF",
        "section_hdr":    "#1F3864",
        "body_txt":       "#2C3E50",
        "footer_bg":      "#E8EEF8",
        "footer_txt":     "#7F8C8D",
        "footer_brand":   "#1F3864",
        "btn_bg":         "#1F3864",
        "btn_hover":      "#2E5EA8",
        "divider":        "#D0DCEF",
        "chart_color":    "#2E5EA8",
        "shadow":         "0 2px 8px rgba(0,0,0,0.08)",
    }

# ── STEP 3: Inject CSS (now correctly themed) ─────────────────────────────────
st.markdown(f"""
<style>
    .stApp {{ background-color: {T['app_bg']} !important; }}

    /* ── Kill Streamlit's default bottom padding & built-in footer ── */
    footer {{ display: none !important; }}
    #MainMenu {{ display: none !important; }}
    [data-testid="stAppViewContainer"] > .main {{
        padding-bottom: 0 !important;
    }}
    [data-testid="stBottomBlockContainer"] {{
        display: none !important;
    }}
    .block-container {{
        padding-bottom: 0 !important;
        margin-bottom: 0 !important;
    }}

    section[data-testid="stSidebar"] {{
        background: {T['sidebar_grad']} !important;
        border-right: 1px solid {T['sidebar_border']};
    }}
    section[data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {{
        color: {T['sidebar_txt']} !important;
    }}
    section[data-testid="stSidebar"] .stCheckbox span {{
        color: {T['sidebar_txt']} !important;
    }}

    .header-card {{
        background: {T['header_grad']};
        border-radius: 12px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }}
    .header-card h1,
    .header-card h1 span,
    .header-card h1 a {{
        color: #FFFFFF !important;
        margin: 0;
        font-size: 2rem;
        text-shadow: 0 1px 4px rgba(0,0,0,0.5);
    }}
    .header-card p {{ color: {T['header_sub']}; margin: 4px 0 0; font-size: 1rem; }}

    .metric-card, .welcome-card {{
        background: {T['card_bg']};
        border-radius: 10px;
        padding: 18px 22px;
        text-align: center;
        box-shadow: {T['shadow']};
        border-top: 4px solid {T['card_border']};
    }}
    .metric-card .metric-val,
    .welcome-card .metric-val {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {T['card_val']};
    }}
    .metric-card .metric-label,
    .welcome-card .metric-label {{
        font-size: 0.82rem;
        color: {T['card_label']};
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 2px;
    }}

    h3 {{ color: {T['section_hdr']} !important; }}
    p, li, span, label {{ color: {T['body_txt']}; }}
    .stDataFrame {{ border-radius: 10px; overflow: hidden; }}

    .stDownloadButton button {{
        background: {T['btn_bg']} !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
    }}
    .stDownloadButton button:hover {{ background: {T['btn_hover']} !important; }}

    /* Full-bleed footer */
    .footer-wrap {{
        position: relative;
        left: 50%;
        margin-left: -50vw;
        width: 100vw;
        background: {T['footer_bg']};
        border-top: 2px solid {T['divider']};
        padding: 20px 40px;
        text-align: center;
        margin-top: 48px;
        box-sizing: border-box;
    }}
    .footer-wrap .footer-brand {{
        font-size: 1rem;
        font-weight: 700;
        color: {T['footer_brand']} !important;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }}
    .footer-wrap .footer-sub {{
        font-size: 0.78rem;
        color: {T['footer_txt']} !important;
        margin-top: 4px;
    }}

    div[data-testid="stButton"] button {{
        border-radius: 20px !important;
        border: 1px solid {T['card_border']} !important;
        font-size: 0.82rem !important;
        padding: 4px 14px !important;
    }}
</style>
""", unsafe_allow_html=True)


# ── STEP 4: Rest of sidebar (file upload + options) ───────────────────────────
with st.sidebar:
    st.markdown("## 📂 Upload Invoices")
    st.markdown("Supports single or multiple PDF files. Each invoice page is extracted automatically.")
    st.markdown("---")

    uploaded_files = st.file_uploader(
        "Drop PDF files here",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Options")
    show_source = st.checkbox("Show Source File column", value=True)
    show_page   = st.checkbox("Show Page Number column", value=False)
    st.markdown("---")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1>🧾 GST Invoice Extractor</h1>
    <p>Upload GST Tax Invoice PDFs → Extract key fields → Export to Excel instantly</p>
</div>
""", unsafe_allow_html=True)


# ── Main content ──────────────────────────────────────────────────────────────
if not uploaded_files:
    # Only clear cached data when files are explicitly removed
    if st.session_state.files_key != "":
        st.session_state.records   = []
        st.session_state.files_key = ""

    c1, c2, c3 = st.columns(3)
    for col, icon, label in zip(
        [c1, c2, c3],
        ["📄", "⚡", "📊"],
        ["Upload PDFs from sidebar", "Auto-extract in seconds", "Download as Excel"],
    ):
        with col:
            st.markdown(f"""<div class="welcome-card">
                <div class="metric-val">{icon}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈  Upload one or more GST Invoice PDFs using the sidebar to get started.")

else:
    # ── Extract (only when files actually change) ─────────────────────────────
    current_key = "|".join(f"{uf.name}:{uf.size}" for uf in uploaded_files)

    if current_key != st.session_state.files_key:
        with st.spinner("🔍 Extracting invoice data..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_paths = []
                for uf in uploaded_files:
                    tmp_path = Path(tmpdir) / uf.name
                    tmp_path.write_bytes(uf.read())
                    tmp_paths.append(str(tmp_path))
                st.session_state.records   = extract_from_multiple_pdfs(tmp_paths)
                st.session_state.files_key = current_key

    records = st.session_state.records

    if not records:
        st.error("❌ No valid GST invoices found. Please check the PDFs and try again.")
        st.stop()

    df          = pd.DataFrame(records)
    display_cols = ["Supplier Name", "Supplier GSTIN", "Invoice No.", "Date", "Total Amount (₹)"]
    if show_source: display_cols.append("Source File")
    if show_page:   display_cols.append("Page")

    df_display = df[[c for c in display_cols if c in df.columns]].copy()
    df_display.index = range(1, len(df_display) + 1)
    df_display.index.name = "S.No."

    amount_vals = []
    for v in df["Total Amount (₹)"]:
        try:   amount_vals.append(float(str(v).replace(",", "")))
        except: pass

    total_amt   = sum(amount_vals)
    avg_amt     = total_amt / len(amount_vals) if amount_vals else 0
    n_suppliers = df["Supplier Name"].nunique()

    # ── Metric cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in zip(
        [c1, c2, c3, c4],
        [str(len(records)), fmt_inr(total_amt), fmt_inr(avg_amt), str(n_suppliers)],
        ["Invoices Extracted", "Total Amount", "Avg. Invoice Value", "Unique Suppliers"],
    ):
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-val">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Data table ────────────────────────────────────────────────────────────
    st.markdown("### 📋 Extracted Invoice Data")
    styled_df = df_display.style.map(
        lambda v: "color: #E74C3C; font-style: italic;" if v == "—" else ""
    )
    st.dataframe(styled_df, use_container_width=True, height=400)

    missing_count = sum(1 for rec in records for v in rec.values() if v == "—")
    if missing_count == 0:
        st.success("✅ All fields extracted successfully — no missing values detected.")
    else:
        st.warning(f"⚠️ {missing_count} field(s) could not be extracted (shown as —). "
                   "This may occur with scanned/image-based PDFs.")

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💾 Export to Excel")
    col_dl, col_info = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="⬇️  Download Excel Report",
            data=write_excel(records),
            file_name="gst_invoices_extracted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col_info:
        st.markdown("""
        **The Excel file includes:**
        - 📄 **Invoice Data** sheet — all extracted fields with professional formatting
        - 📊 **Summary** sheet — totals, averages, highest/lowest invoice stats
        - Grand total row at the bottom · Alternating row colours for easy reading
        """)

    # ── Invoice Breakdown chart ───────────────────────────────────────────────
    if len(records) > 1 and amount_vals:
        st.markdown("---")
        st.markdown("### 📈 Invoice Breakdown")

        chart_data = pd.DataFrame({
            "Invoice":    df["Invoice No."].tolist(),
            "Amount":     amount_vals,
            "Amount (₹)": [fmt_inr(v) for v in amount_vals],
        })

        chart = (
            alt.Chart(chart_data)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=T["chart_color"])
            .encode(
                x=alt.X("Invoice:N", sort=None,
                        axis=alt.Axis(labelColor=T["body_txt"], titleColor=T["body_txt"],
                                      labelAngle=-30, title="Invoice No.")),
                y=alt.Y("Amount:Q",
                        axis=alt.Axis(labelColor=T["body_txt"], titleColor=T["body_txt"],
                                      title="Amount (₹)", format=",")),
                tooltip=[
                    alt.Tooltip("Invoice:N",    title="Invoice No."),
                    alt.Tooltip("Amount (₹):N", title="Total Amount"),
                ],
            )
            .properties(height=340, background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(gridColor=T["divider"], domainColor=T["divider"])
        )
        st.altair_chart(chart, use_container_width=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer-wrap">
    <div class="footer-brand">Gopal Jee &amp; Associates &trade;</div>
    <div class="footer-sub">GST Invoice Extractor &nbsp;·&nbsp; Powered by AI extraction</div>
</div>
""", unsafe_allow_html=True)
