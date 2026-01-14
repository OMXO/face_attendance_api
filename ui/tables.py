import streamlit as st

def render_logs_table(logs: list):
    """
    Render bảng Logs với HTML tùy chỉnh.
    """
    # Header Control của bảng
    st.markdown("""
    <div class="glass-card" style="padding: 0; overflow: hidden; border: 1px solid #e6f4f4; margin-top: 1rem;">
        <div style="padding: 1.5rem; border-bottom: 1px solid #e6f4f4; display: flex; justify-content: space-between; align-items: center;">
            <h3 style="font-weight: 700; font-size: 1.125rem; color: #1e293b; margin: 0;">Recent Activity</h3>
            <div style="display: flex; gap: 0.5rem;">
                <button style="border:none; background:#f1f5f9; padding:0.5rem 1rem; border-radius:0.75rem; color:#64748b; font-size:0.75rem; font-weight:800; letter-spacing:0.05em;">FILTER</button>
            </div>
        </div>
        <div style="overflow-x: auto;">
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Department</th>
                        <th>Time</th>
                        <th>Device</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    """, unsafe_allow_html=True)

    if not logs:
        st.markdown('<tr><td colspan="5" style="text-align:center; padding:2rem; color:#94a3b8;">No records found</td></tr>', unsafe_allow_html=True)
    
    for log in logs:
        # Data preparation
        name = log.get("name") or "Unknown"
        is_recog = bool(log.get("recognized", False))
        time_str = log.get("event_time") or "--:--"
        cam = log.get("camera_label") or log.get("camera_id") or "Cam-01"
        
        # Avatar logic
        avatar = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random&color=fff&size=64"
        
        # Status styling
        if is_recog:
            status_html = '<span style="background:rgba(240,253,244,1); color:#16a34a; padding:0.25rem 0.5rem; border-radius:0.5rem; font-size:0.65rem; font-weight:800; text-transform:uppercase;">Check-in</span>'
        else:
            status_html = '<span style="background:rgba(254,242,242,1); color:#ef4444; padding:0.25rem 0.5rem; border-radius:0.5rem; font-size:0.65rem; font-weight:800; text-transform:uppercase;">Denied</span>'

        st.markdown(f"""
        <tr style="border-bottom: 1px solid #e6f4f4;">
            <td>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <img src="{avatar}" style="width: 2.5rem; height: 2.5rem; border-radius: 99px; object-fit: cover;">
                    <span style="font-weight: 700; font-size: 0.875rem;">{name}</span>
                </div>
            </td>
            <td><span style="background:#f1f5f9; color:#64748b; padding:0.25rem 0.5rem; border-radius:0.5rem; font-size:0.75rem; font-weight:700;">Engineering</span></td>
            <td style="font-weight: 600; font-size: 0.875rem; color: #475569;">{time_str}</td>
            <td style="font-size: 0.875rem; font-weight: 700; color: #0f172a;">{cam}</td>
            <td>{status_html}</td>
        </tr>
        """, unsafe_allow_html=True)

    st.markdown("</tbody></table></div></div>", unsafe_allow_html=True)

def render_employee_table(employees: list):
    """
    Render bảng Employees giống Employees.tsx
    """
    st.markdown("""
    <div class="glass-card" style="padding: 0; overflow: hidden; border: 1px solid #e6f4f4; margin-top: 1rem;">
        <div style="overflow-x: auto;">
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Full Name</th>
                        <th>Code / ID</th>
                        <th>Registration</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    """, unsafe_allow_html=True)

    if not employees:
         st.markdown('<tr><td colspan="4" style="text-align:center; padding:2rem; color:#94a3b8;">No employees found</td></tr>', unsafe_allow_html=True)

    for emp in employees:
        name = emp.get("name")
        code = emp.get("employee_code") or "—"
        has_face = emp.get("has_face")
        avatar = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random&size=64"

        # Badge Logic
        if has_face:
            badge = '<span style="background:rgba(240,253,244,1); color:#16a34a; padding:0.25rem 0.5rem; border-radius:0.5rem; font-size:0.65rem; font-weight:800; text-transform:uppercase;">Active</span>'
        else:
            badge = '<span style="background:rgba(241,245,249,1); color:#94a3b8; padding:0.25rem 0.5rem; border-radius:0.5rem; font-size:0.65rem; font-weight:800; text-transform:uppercase;">No Data</span>'

        st.markdown(f"""
        <tr>
            <td>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <img src="{avatar}" style="width: 2.5rem; height: 2.5rem; border-radius: 0.75rem; object-fit: cover;">
                    <div>
                        <div style="font-weight: 800; font-size: 0.875rem;">{name}</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">user@company.com</div>
                    </div>
                </div>
            </td>
            <td style="font-weight: 600; font-size: 0.875rem; color: #475569;">{code}</td>
            <td>{badge}</td>
            <td style="text-align: right; color: #cbd5e1;">● ● ●</td>
        </tr>
        """, unsafe_allow_html=True)

    st.markdown("</tbody></table></div></div>", unsafe_allow_html=True)