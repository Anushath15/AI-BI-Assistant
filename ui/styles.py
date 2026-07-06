import streamlit as st

def apply_global_styles():

    st.markdown("""

<style>

html, body, [class*="css"]{

background:#F8FAFC;

font-family:'Inter',sans-serif;

color:#111827;

}

.block-container{

padding-top:2rem;

padding-bottom:2rem;

max-width:1400px;

}

div[data-testid="stSidebar"]{

background:#111827;

}

h1,h2,h3,h4{

color:#111827;

font-weight:700;

}

.stButton>button{

border-radius:12px;

background:#2563EB;

color:white;

border:none;

padding:10px 20px;

font-weight:600;

transition:.3s;

}

.stButton>button:hover{

background:#1D4ED8;

}

.metric-card{

background:white;

padding:20px;

border-radius:18px;

box-shadow:0 10px 25px rgba(0,0,0,.08);

border:1px solid #ECECEC;

}

.chat-card{

background:white;

border-radius:18px;

padding:18px;

box-shadow:0 8px 24px rgba(0,0,0,.08);

margin-bottom:15px;

}

</style>

""",unsafe_allow_html=True)