"""
ui/styles.py

Global CSS styling for AI BI Assistant.
Injected once at app startup via inject_styles().
"""

GLOBAL_CSS = """
<style>

/* ── Reset & Base ─────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                 'Segoe UI', sans-serif;
}

/* ── Force light background on main area ─────────── */
[data-testid="stAppViewContainer"] {
    background-color: #F8FAFC !important;
}

section.main {
    background-color: #F8FAFC !important;
}

.main .block-container {
    background-color: #F8FAFC !important;
    padding-top: 1.5rem;
    max-width: 1100px;
}

/* ── Fix main content text visibility ────────────── */
.main h1, .main h2, .main h3 {
    color: #111827 !important;
}

.main p, .main span, .main div {
    color: #111827;
}

/* ── Sidebar ──────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #1F2937;
}

[data-testid="stSidebar"] * {
    color: #F9FAFB !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] p {
    color: #9CA3AF !important;
    font-size: 0.78rem;
}

/* ── Hide Streamlit Branding ──────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Chat Messages ────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: white !important;
    border-radius: 12px !important;
    border: 1px solid #E5E7EB !important;
    padding: 1rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: #111827 !important;
}

/* ── User message accent ──────────────────────────── */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 3px solid #2563EB !important;
    background: #EFF6FF !important;
}

/* ── KPI Cards ────────────────────────────────────── */
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    border: 1px solid #E5E7EB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #6B7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}

.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #111827;
    line-height: 1.2;
}

.kpi-sub {
    font-size: 0.75rem;
    color: #6B7280;
    margin-top: 0.2rem;
}

/* ── Status Badge ─────────────────────────────────── */
.status-badge {
    display: inline-block;
    background: #D1FAE5;
    color: #065F46 !important;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    letter-spacing: 0.05em;
}

/* ── Section Labels ───────────────────────────────── */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #6B7280 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
    margin-top: 0.5rem;
}

/* ── Sidebar Logo ─────────────────────────────────── */
.sidebar-logo {
    padding: 1rem 0 1.5rem 0;
    border-bottom: 1px solid #1F2937;
    margin-bottom: 1.5rem;
}

.sidebar-logo-text {
    font-size: 1.1rem;
    font-weight: 700;
    color: #F9FAFB !important;
    letter-spacing: -0.02em;
}

.sidebar-logo-sub {
    font-size: 0.7rem;
    color: #6B7280 !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 0.2rem;
}

/* ── Sidebar Metrics ──────────────────────────────── */
.sidebar-metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0;
    border-bottom: 1px solid #1F2937;
}

.sidebar-metric-label {
    font-size: 0.75rem;
    color: #6B7280 !important;
}

.sidebar-metric-value {
    font-size: 0.75rem;
    font-weight: 600;
    color: #F9FAFB !important;
}

/* ── Buttons ──────────────────────────────────────── */
.stButton > button {
    background-color: #2563EB !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

.stButton > button:hover {
    background-color: #1D4ED8 !important;
    color: white !important;
}

/* ── Chat Input ───────────────────────────────────── */
[data-testid="stChatInput"] textarea {
    background: white !important;
    color: #111827 !important;
    border-radius: 12px !important;
}

/* ── Expander ─────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    background: white !important;
}

/* ── Alerts ───────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* ── Dividers ─────────────────────────────────────── */
[data-testid="stSidebar"] hr {
    border-color: #1F2937 !important;
}

/* ── Plotly charts background ─────────────────────── */
.js-plotly-plot {
    border-radius: 12px;
    overflow: hidden;
}

</style>
"""


def inject_styles():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)