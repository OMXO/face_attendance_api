import streamlit as st
import time

def render_viewfinder():
    """
    Hiển thị khung quét Camera với hiệu ứng Scanline (giống Viewfinder.tsx).
    Lưu ý: CSS này sẽ đè lên khung video webrtc.
    """
    st.markdown("""
        <style>
        @keyframes scan-move {
            0% { top: 0%; opacity: 0; }
            50% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
        }
        
        .viewfinder-container {
            position: relative;
            width: 100%;
            border-radius: 1.5rem; /* rounded-3xl */
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }

        /* Scanline Effect */
        .scanline {
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(to right, transparent, #0ea5e9, transparent);
            box-shadow: 0 0 15px rgba(14, 165, 233, 0.8);
            animation: scan-move 2s linear infinite;
            z-index: 10;
            pointer-events: none;
        }

        /* Corner Brackets */
        .corner {
            position: absolute;
            width: 3rem;
            height: 3rem;
            border: 4px solid rgba(14, 165, 233, 0.8);
            z-index: 5;
        }
        .tl { top: 1rem; left: 1rem; border-right: none; border-bottom: none; border-top-left-radius: 1rem; }
        .tr { top: 1rem; right: 1rem; border-left: none; border-bottom: none; border-top-right-radius: 1rem; }
        .bl { bottom: 1rem; left: 1rem; border-right: none; border-top: none; border-bottom-left-radius: 1rem; }
        .br { bottom: 1rem; right: 1rem; border-left: none; border-top: none; border-bottom-right-radius: 1rem; }
        </style>
        
        """, unsafe_allow_html=True)

def render_success_message(name: str, code: str, similarity: float):
    """
    Hiển thị thông báo thành công (giống SuccessOverlay.tsx).
    """
    st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #22c55e; animation: fadeIn 0.5s;">
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div style="width: 3rem; height: 3rem; background: #dcfce7; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #16a34a;">
                    <span class="material-symbols-outlined">check_circle</span>
                </div>
                <div>
                    <p style="font-size: 0.65rem; font-weight: 900; color: #16a34a; text-transform: uppercase; letter-spacing: 0.1em; margin:0;">Access Granted</p>
                    <h3 style="font-size: 1.25rem; font-weight: 900; color: #0f172a; margin: 0;">{name}</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 0;">{code} • Match: {int(similarity * 100)}%</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_denied_message():
    st.markdown("""
        <div class="glass-card" style="border-left: 4px solid #ef4444; animation: fadeIn 0.5s;">
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div style="width: 3rem; height: 3rem; background: #fee2e2; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ef4444;">
                    <span class="material-symbols-outlined">block</span>
                </div>
                <div>
                    <p style="font-size: 0.65rem; font-weight: 900; color: #ef4444; text-transform: uppercase; letter-spacing: 0.1em; margin:0;">Access Denied</p>
                    <h3 style="font-size: 1.25rem; font-weight: 900; color: #0f172a; margin: 0;">Unknown Person</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 0;">Please register at HR.</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)