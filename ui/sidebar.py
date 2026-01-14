import streamlit as st

def render_sidebar():
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e6f4f4; }
        .nav-section { font-size: 0.75rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin: 1.5rem 0 0.5rem 0.5rem; letter-spacing: 0.1em; }
        .stPageLink a { display: flex; align-items: center; gap: 0.75rem; padding: 0.625rem 0.75rem; border-radius: 0.75rem; color: #64748b; text-decoration: none; font-weight: 500; transition: all 0.2s; }
        .stPageLink a:hover { background-color: #f1f5f9; color: #0f172a; }
        .stPageLink a[aria-current="page"] { background-color: rgba(14, 165, 233, 0.1); color: #0ea5e9; font-weight: 700; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # Logo
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; margin-bottom: 1rem;">
                <div style="width: 2.5rem; height: 2.5rem; background-color: #0ea5e9; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; color: white;">
                    <span class="material-symbols-outlined">face</span>
                </div>
                <div>
                    <h1 style="font-size: 1rem; font-weight: 800; margin: 0;">FaceLog</h1>
                    <p style="font-size: 0.65rem; color: #0ea5e9; font-weight: 800; text-transform: uppercase; margin: 0;">Access Control</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Menu
        st.markdown('<div class="nav-section">Timekeeper</div>', unsafe_allow_html=True)
        st.page_link("01_Timekeeping.py", label="Face Scan", icon="📷")

        st.markdown('<div class="nav-section">Admin Portal</div>', unsafe_allow_html=True)
        st.page_link("pages/02_Admin_Database.py", label="Employee DB", icon="👥")
        st.page_link("pages/03_Admin_Logs.py", label="Access Logs", icon="🕒")