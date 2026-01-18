import streamlit as st
import api_client as api_service
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import cv2
import time
import os
from ui import design_system, header, sidebar, overlays

# 1. PAGE CONFIG
st.set_page_config(page_title="Live Terminal | FaceLog", page_icon="📷", layout="wide")
design_system.apply()
sidebar.render_sidebar()

# 2. HEADER
header.render_header("Biometric Scan Terminal", "Security checkpoint active. Real-time identification enabled.")

# 3. UI LAYOUT
col_cam, col_info = st.columns([2, 1], gap="large")

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.latest_bgr = None
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.latest_bgr = img
        return frame

with col_cam:
    st.markdown("""
    <div style="position: relative; border-radius: 24px; overflow: hidden; border: 2px solid rgba(59, 130, 246, 0.3); box-shadow: 0 0 40px rgba(59, 130, 246, 0.2);">
        <div style="position: absolute; top: 20px; left: 20px; z-index: 10; display: flex; align-items: center; gap: 8px;">
            <div style="width: 10px; height: 10px; background: #ef4444; border-radius: 50%; box-shadow: 0 0 10px #ef4444; animation: pulse 1.5s infinite;"></div>
            <span style="color: white; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">Live Stream</span>
        </div>
        <div style="position: absolute; bottom: 20px; right: 20px; z-index: 10;">
            <span style="color: rgba(255,255,255,0.7); font-family: monospace; font-size: 0.7rem;">TERMINAL ID: CAM-04-X</span>
        </div>
    """, unsafe_allow_html=True)
    
    ctx = webrtc_streamer(
        key="recognition",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_info:
    st.markdown("<h3 style='margin-bottom: 1rem;'>Intelligence Sidebar</h3>", unsafe_allow_html=True)
    
    # Processing Status
    status_placeholder = st.empty()
    result_placeholder = st.empty()

    if ctx.video_processor:
        if "last_scan_ts" not in st.session_state:
            st.session_state.last_scan_ts = 0

        now = time.time()
        # Scan every 1.5 seconds for higher responsiveness
        if now - st.session_state.last_scan_ts > 1.5:
            frame = ctx.video_processor.latest_bgr
            if frame is not None:
                status_placeholder.markdown("""
                <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); padding: 12px; border-radius: 12px; display: flex; align-items: center; gap: 10px;">
                    <div class="stSpinner" style="width:16px; height:16px;"></div>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #3b82f6;">Analyzing Biometric Data...</span>
                </div>
                """, unsafe_allow_html=True)
                
                _, img_encoded = cv2.imencode(".jpg", frame)
                try:
                    res = api_service.recognize(
                        image_bytes=img_encoded.tobytes(),
                        event_type="check-in",
                        camera_id="CAM-01"
                    )
                    st.session_state.last_scan_result = res
                    st.session_state.last_scan_ts = now
                    status_placeholder.empty()
                except Exception as e:
                    st.error(f"Analysis Failed: {e}")
            else:
                status_placeholder.info("Waiting for video stream initialization...")
    else:
        status_placeholder.warning("Please enable camera access to begin scanning.")

    # Render Persistent Results
    res = st.session_state.get("last_scan_result")
    if res:
        if res.get("recognized"):
            with result_placeholder.container():
                overlays.render_success_message(
                    name=res.get("name", "Authorized User"),
                    code=res.get("employee_code", "N/A"),
                    score=res.get("similarity")
                )
                st.toast(f"Welcome back, {res.get('name')}!", icon="✅")
        else:
            result_placeholder.markdown("""
            <div class="glass-card" style="border: 2px solid rgba(248, 113, 113, 0.3); background: rgba(248, 113, 113, 0.05);">
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🕵️</div>
                    <h4 style="color: #f87171; margin: 0;">Identity Unknown</h4>
                    <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 8px;">No biometric match found in secure database. Please adjust lighting or contact admin.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
