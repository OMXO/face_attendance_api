import streamlit as st

def apply():
    """
    Áp dụng giao diện React/Tailwind vào Streamlit.
    """
    # Màu sắc định nghĩa từ Tailwind config của project React
    # Primary: Sky-500 (#0ea5e9)
    # Background: #f8fbfb
    
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
        
        <style>
        /* ===== VARIABLES (Tailwind Mapping) ===== */
        :root {
            --primary: #0ea5e9;
            --primary-bg: rgba(14, 165, 233, 0.1);
            --bg-color: #f8fbfb;
            --glass-border: #e6f4f4;
            --text-dark: #0f172a;
            --text-gray: #64748b;
            --neutral-gray: #f1f5f9;
        }

        /* ===== GLOBAL RESET ===== */
        .stApp {
            background-color: var(--bg-color);
            font-family: 'Inter', sans-serif;
            color: var(--text-dark);
        }
        
        #MainMenu, header[data-testid="stHeader"], footer {
            visibility: hidden;
        }
        
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 95% !important;
        }

        /* ===== GLASS CARD ===== */
        .glass-card {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 1rem; /* rounded-2xl */
            padding: 1.5rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        .glass-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
            border-color: rgba(14, 165, 233, 0.2);
        }

        /* ===== TYPOGRAPHY ===== */
        .tracking-widest { letter-spacing: 0.1em; text-transform: uppercase; }
        .font-black { font-weight: 900; }
        .text-xs { font-size: 0.75rem; }

        /* ===== CUSTOM TABLE STYLE ===== */
        .custom-table-container {
            border: 1px solid var(--glass-border);
            border-radius: 1rem;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.4);
        }
        table.custom-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }
        table.custom-table th {
            text-align: left;
            padding: 1rem 1.5rem;
            font-size: 0.65rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.2em;
            color: #94a3b8;
            background-color: rgba(241, 245, 249, 0.5);
            border-bottom: 1px solid var(--glass-border);
        }
        table.custom-table td {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--glass-border);
            vertical-align: middle;
            color: var(--text-dark);
        }
        table.custom-table tr:hover td {
            background-color: var(--primary-bg);
        }
        
        /* ===== UTILS ===== */
        .material-symbols-outlined {
            vertical-align: middle;
            font-size: 20px;
        }
        
        /* Streamlit Input Override */
        input[type="text"] {
            background-color: var(--neutral-gray) !important;
            border: none !important;
            border-radius: 0.75rem !important;
            color: var(--text-dark) !important;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: white;
            border-right: 1px solid var(--glass-border);
        }
        </style>
    """, unsafe_allow_html=True)