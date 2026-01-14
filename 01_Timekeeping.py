from __future__ import annotations
import os
import time
import cv2
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import api_client as api_service
from styles import theme
from ui import header, overlays, sidebar
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


# Setup
st.set_page_config(page_title="Timekeeping", page_icon="📷", layout="wide")
theme.apply()
sidebar.render_sidebar()
api_base = (st.session_state.get("api_base") or API_BASE).rstrip("/")

# UI
header.render_header("Timekeeping Area", "Please place your face in the frame.")

col_cam, col_info = st.columns([2, 1])

# Image processing logic
class VideoProcessor(VideoProcessorBase):
    def __init__(self): self.latest_bgr = None
    def recv(self, frame):
        self.latest_bgr = frame.to_ndarray(format="bgr24")
        return frame

# --- LEFT COLUMN: CAMERA ---
with col_cam:
    st.markdown('<div class="viewfinder-container"><div class="corner tl"></div><div class="corner tr"></div><div class="corner bl"></div><div class="corner br"></div><div class="scanline"></div>', unsafe_allow_html=True)
    ctx = webrtc_streamer(
        key="timekeeping", mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": {"width": 1280, "height": 720}, "audio": False},
        async_processing=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- RIGHT COLUMN: RESULTS ---
with col_info:
    res = st.session_state.get("last_scan_result")
    
    if res:
        if res.get("recognized"):
            overlays.render_success_message(res.get("name"), res.get("employee_code"), res.get("similarity"))
        else:
            overlays.render_denied_message()
    else:
        st.info("Waiting for scan...")

# --- BACKGROUND PROCESS ---
if ctx.state.playing and ctx.video_processor:
    if time.time() - st.session_state.get("last_scan_ts", 0) > 1.5: # Scan every 1.5s
        frame = ctx.video_processor.latest_bgr
        if frame is not None:
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                try:
                    # Default is CHECK_IN, Camera Default
                    resp = api_service.recognize(buf.tobytes(), "CHECK_IN", "CAM_MAIN", api_base)
                    st.session_state.last_scan_result = resp
                    st.session_state.last_scan_ts = time.time()
                    st.rerun()
                except: pass