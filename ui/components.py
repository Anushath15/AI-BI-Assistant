import streamlit as st


# ==========================================================
# APP HEADER
# ==========================================================

def render_app_header(dataset_name: str = ""):
    st.markdown(
        f"""
        <div style="
            background:#FFFFFF;
            border:1px solid #E5E7EB;
            border-radius:18px;
            padding:24px 30px;
            margin-bottom:24px;
        ">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">

                <div>
                    <h1 style="
                        margin:0;
                        font-size:34px;
                        font-weight:800;
                        color:#111827;
                    ">
                        📊 AI BI Assistant
                    </h1>

                    <p style="
                        margin:8px 0 0 0;
                        color:#6B7280;
                        font-size:15px;
                    ">
                        {dataset_name if dataset_name else "Upload a dataset to begin analysis"}
                    </p>
                </div>

                <div style="
                    background:#DCFCE7;
                    color:#166534;
                    padding:8px 18px;
                    border-radius:999px;
                    font-weight:600;
                    font-size:14px;
                ">
                    ● Connected
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# SECTION LABEL
# ==========================================================

def render_section_label(
    title: str,
    icon: str = "",
    margin_top: str = "0rem",
):
    st.markdown(
        f"""
        <div style="
            margin-top:{margin_top};
            margin-bottom:12px;
        ">
            <h3 style="
                margin:0;
                color:#1F2937;
                font-weight:700;
                display:flex;
                align-items:center;
                gap:8px;
            ">
                <span>{icon}</span>
                <span>{title}</span>
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# KPI CARD
# ==========================================================

def render_kpi_card(
    title: str,
    value,
    icon: str = "📊",
    color: str = "#2563EB",
):
    st.markdown(
        f"""
        <div style="
            background:#FFFFFF;
            border:1px solid #E5E7EB;
            border-radius:16px;
            padding:20px;
            box-shadow:0 2px 8px rgba(0,0,0,.05);
            height:140px;
        ">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:flex-start;
            ">

                <div>

                    <div style="
                        color:#6B7280;
                        font-size:12px;
                        font-weight:700;
                        text-transform:uppercase;
                    ">
                        {title}
                    </div>

                    <div style="
                        margin-top:12px;
                        color:#111827;
                        font-size:30px;
                        font-weight:800;
                    ">
                        {value}
                    </div>

                </div>

                <div style="
                    width:52px;
                    height:52px;
                    border-radius:14px;
                    background:{color}20;
                    display:flex;
                    justify-content:center;
                    align-items:center;
                    font-size:24px;
                ">
                    {icon}
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# SIDEBAR METRIC
# ==========================================================

def render_sidebar_metric(label: str, value):
    st.sidebar.markdown(
        f"""
        <div style="
            background:#1E293B;
            border-radius:12px;
            padding:12px;
            margin-bottom:10px;
        ">

            <div style="
                color:#CBD5E1;
                font-size:12px;
            ">
                {label}
            </div>

            <div style="
                margin-top:4px;
                color:white;
                font-size:22px;
                font-weight:700;
            ">
                {value}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# INSIGHT CARD
# ==========================================================

def render_insight_card(text: str):
    st.success(text)


# ==========================================================
# EMPTY STATE
# ==========================================================

def render_empty_state(
    message: str = "Upload a dataset to begin analysis."
):
    st.markdown(
        f"""
        <div style="
            border:2px dashed #CBD5E1;
            border-radius:18px;
            background:white;
            padding:60px;
            text-align:center;
            color:#64748B;
            font-size:18px;
        ">

            📂

            <br><br>

            {message}

        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# ERROR
# ==========================================================

def render_planning_error(message: str):
    st.error(message)