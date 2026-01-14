import streamlit as st

def render_kpi_card(title: str, value: str, icon: str, trend: str, trend_positive: bool, color_theme: str = "primary"):
    """
    Render KPI Card.
    color_theme: 'primary', 'amber', 'danger', 'success'
    """
    
    # Map theme to CSS colors
    colors = {
        "primary": {"bg": "rgba(240, 249, 255, 1)", "text": "#0ea5e9"}, # sky-50, sky-500
        "amber":   {"bg": "rgba(255, 251, 235, 1)", "text": "#f59e0b"}, # amber-50
        "danger":  {"bg": "rgba(254, 242, 242, 1)", "text": "#ef4444"}, # red-50
        "success": {"bg": "rgba(240, 253, 244, 1)", "text": "#22c55e"}, # green-50
    }
    
    c = colors.get(color_theme, colors["primary"])
    
    trend_color = "#16a34a" if trend_positive else "#dc2626"
    trend_bg = "rgba(240, 253, 244, 1)" if trend_positive else "rgba(254, 242, 242, 1)"

    st.markdown(f"""
        <div class="glass-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                <div style="width: 3rem; height: 3rem; background-color: {c['bg']}; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; color: {c['text']};">
                    <span class="material-symbols-outlined">{icon}</span>
                </div>
                <span style="color: {trend_color}; background-color: {trend_bg}; font-size: 10px; font-weight: 900; padding: 0.25rem 0.5rem; border-radius: 0.5rem; text-transform: uppercase; letter-spacing: 0.1em;">
                    {trend}
                </span>
            </div>
            <div>
                <p style="color: #94a3b8; font-size: 0.75rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; margin: 0;">{title}</p>
                <p style="font-size: 2.25rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem; line-height: 1;">{value}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)