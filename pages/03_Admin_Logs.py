import streamlit as st
import pandas as pd
import api_client as api_service

from styles import theme
from ui import header, sidebar, tables

st.set_page_config(page_title="History", page_icon="🕒", layout="wide")
theme.apply()
sidebar.render_sidebar()
api_base = (st.session_state.get("api_base") or "http://127.0.0.1:8000").rstrip("/")

header.render_header("Access Logs", "Monitor system access history.")

# --- FILTER SECTION ---
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        limit = st.selectbox("Number of rows", [20, 50, 100], index=1)
    with c2:
        status_filter = st.selectbox("Status", ["All", "Success", "Failed"])
    with c3:
        # If you want to filter by date, need to update API to accept date param
        date_filter = st.date_input("Date", value=None)

# --- DATA FETCHING ---
try:
    logs = api_service.fetch_logs(limit=limit, api_base=api_base)
    
    # Client-side filtering (Temporary client-side filter if API doesn't support filter yet)
    if status_filter == "Success":
        logs = [l for l in logs if l.get("recognized")]
    elif status_filter == "Failed":
        logs = [l for l in logs if not l.get("recognized")]
        
except Exception as e:
    st.error(f"Data loading error: {e}")
    logs = []

# --- DISPLAY TABLE ---
# Reuse beautiful HTML table from ui/tables.py
tables.render_logs_table(logs)