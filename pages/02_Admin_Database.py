import streamlit as st
import time
import api_client as api_service

from styles import theme
from ui import header, sidebar

# ============================================================
# 1. SETUP
# ============================================================
st.set_page_config(page_title="Database", page_icon="👥", layout="wide")
theme.apply()
sidebar.render_sidebar()
api_base = (st.session_state.get("api_base") or "http://127.0.0.1:8000").rstrip("/")

header.render_header("Database", "Add new employees and register faces.")

# ============================================================
# 2. STATE MANAGEMENT
# ============================================================
if "show_add_panel" not in st.session_state: st.session_state.show_add_panel = False

def toggle_add_panel():
    st.session_state.show_add_panel = not st.session_state.show_add_panel

# ============================================================
# 3. EMPLOYEE ADDITION AREA (CAMERA INTEGRATION)
# ============================================================
# Button to open add panel
if not st.session_state.show_add_panel:
    if st.button("➕ Add New Employee", type="primary"):
        toggle_add_panel()
        st.rerun()

if st.session_state.show_add_panel:
    with st.container(border=True):
        st.subheader("👤 Information & Face")
        
        # --- COLUMN 1: BASIC INFORMATION ---
        col_info, col_cam = st.columns([1, 1], gap="large")
        
        with col_info:
            st.info("Step 1: Enter identification information")
            new_name = st.text_input("Full name (*)", key="new_name_input")
            new_code = st.text_input("Employee ID (Optional)", key="new_code_input")
        
        # --- COLUMN 2: FACE SCANNING CAMERA ---
        with col_cam:
            st.info("Step 2: Capture face photo")
            # Camera input outside form for realtime operation
            img_buffer = st.camera_input("Capture photo", label_visibility="collapsed")

        st.divider()
        
        # --- ACTION BUTTONS ---
        c_act1, c_act2 = st.columns([1, 5])
        with c_act1:
            # Save button performs both tasks: Create Employee -> Enroll Face
            if st.button("💾 Save All", type="primary", use_container_width=True):
                if not new_name:
                    st.error("Please enter employee name!")
                else:
                    try:
                        # 1. Create employee first
                        with st.status("Processing...", expanded=True) as status:
                            st.write("📝 Creating employee profile...")
                            emp_resp = api_service.create_employee(new_name, new_code, api_base)
                            new_id = emp_resp.get("employee_id")
                            
                            # 2. If there's a photo -> Register face immediately
                            if img_buffer:
                                st.write("📸 Analyzing and registering face...")
                                api_service.enroll_face(new_id, img_buffer.getvalue(), api_base)
                                status.update(label="✅ Complete!", state="complete", expanded=False)
                                st.success(f"Added {new_name} and registered face successfully!")
                            else:
                                status.update(label="⚠️ Saved (No photo)", state="complete")
                                st.warning(f"Added {new_name} but face NOT registered.")
                        
                        time.sleep(1.5)
                        toggle_add_panel() # Close panel
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        with c_act2:
            if st.button("Cancel"):
                toggle_add_panel()
                st.rerun()

    st.write("") # Spacer

# ============================================================
# 4. EMPLOYEE LIST
# ============================================================
st.markdown("### 📋 Employee List")

# Search bar
search_query = st.text_input("Search", placeholder="Search by name or ID...", label_visibility="collapsed")

try:
    employees = api_service.list_employees(query=search_query, limit=50, api_base=api_base)
except:
    employees = []

# Table Header
st.markdown("""
<div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 1rem; padding: 0.75rem; background: rgba(241,245,249,0.8); border-radius: 8px; font-weight: 800; color: #64748b; font-size: 0.8rem; text-transform: uppercase;">
    <div>Name</div>
    <div>Emp ID</div>
    <div>Face ID</div>
    <div style="text-align: right">Actions</div>
</div>
""", unsafe_allow_html=True)

if not employees:
    st.info("No employees yet.")

for emp in employees:
    with st.container():
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        
        # C1: Avatar + Name
        with c1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; padding: 5px 0;">
                <img src="https://ui-avatars.com/api/?name={emp['name'].replace(' ', '+')}&background=random&size=32" style="border-radius: 50%; width: 32px;">
                <div style="font-weight: 600; font-size: 0.9rem; color: #0f172a;">{emp['name']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # C2: Code
        with c2:
            st.markdown(f"<div style='padding-top: 10px; font-size: 0.85rem; color: #64748b;'>{emp.get('employee_code', '---')}</div>", unsafe_allow_html=True)

        # C3: Status
        with c3:
            has_face = emp.get('has_face', False)
            if has_face:
                st.markdown(f"<span style='background:#dcfce7; color:#16a34a; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700;'>✅ Active</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='background:#f1f5f9; color:#94a3b8; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700;'>❌ None</span>", unsafe_allow_html=True)

        # C4: Delete Only (Since we already have a nice add flow)
        with c4:
            col_dummy, col_btn = st.columns([1, 1])
            with col_btn:
                if st.button("🗑️", key=f"del_{emp['employee_id']}", help="Delete employee"):
                    # Placeholder for delete logic
                    st.toast(f"Delete feature for {emp['name']} is waiting for Delete API.")

        st.markdown("<hr style='margin: 0; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)