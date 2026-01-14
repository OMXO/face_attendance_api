import streamlit as st

def render_header(title: str, subtitle: str):
    """
    Render Header giống design React: Title bên trái, User Profile bên phải.
    Đã sửa lỗi indentation để tránh hiển thị raw HTML.
    """
    html_code = f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem;">
        <div>
            <h2 style="font-size: 1.875rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -0.025em; line-height: 1.2;">{title}</h2>
            <p style="color: #64748b; font-size: 0.875rem; margin-top: 0.25rem; margin-bottom: 0;">{subtitle}</p>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 2.5rem; height: 2.5rem; border-radius: 0.75rem; background: #f1f5f9; display: flex; align-items: center; justify-content: center; position: relative;">
                <span class="material-symbols-outlined" style="color: #64748b; font-size: 24px;">notifications</span>
                <span style="position: absolute; top: 10px; right: 10px; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; border: 1px solid white;"></span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; border-radius: 99px; border: 1px solid #e6f4f4; background: white; padding-right: 1.25rem;">
                <img src="https://ui-avatars.com/api/?name=Admin&background=0ea5e9&color=fff" style="width: 2rem; height: 2rem; border-radius: 50%; display: block;">
                <div>
                    <p style="font-size: 0.75rem; font-weight: 700; margin: 0; color: #0f172a; line-height: 1.2;">Marcus Chen</p>
                    <p style="font-size: 0.65rem; color: #94a3b8; font-weight: 700; margin: 0; line-height: 1.2;">ADMIN</p>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)