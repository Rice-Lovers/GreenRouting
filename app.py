import streamlit as st
import plotly.graph_objects as go
import os

# --- THE CRITICAL IMPORT ---
try:
    from main import run_green_route
    from carbon_api import get_carbon_data
except ImportError:
    st.error("❌ Project files missing. Ensure main.py and carbon_api.py are present.")

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GreenRouting Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INITIALIZE SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

# --- NEXAVERSE COLOR PALETTE ---
COLORS = {
    "wine": "#721817",    
    "sand": "#FA9F42",    
    "blue": "#2B4162",    
    "emerald": "#0B6E4F", 
    "ink": "#031927",
    "charcoal": "#0D1B2A",
    "bg_white": "#FFFFFF"
}

# --- ATOMIC CSS: PINNED MISSION & EXPANDED BASE ---
st.markdown(f"""
    <style>
        .stApp {{ background-color: {COLORS['bg_white']} !important; }}
        
        .fixed-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 85px;
            background: {COLORS['wine']}; border-bottom: 4px solid {COLORS['sand']};
            z-index: 999999; padding: 10px 40px; display: flex;
            justify-content: space-between; align-items: center;
        }}

        .main-content-wrapper {{ 
            margin-top: 85px !important; 
            padding: 0px !important;
        }}

        /* THE CHARCOAL WORKSPACE (TAB 1) - EXPANDED DOWNWARD */
        .charcoal-workspace {{
            background-color: {COLORS['charcoal']};
            border-radius: 15px 15px 0 0; /* Rounded top only for edge-to-edge bottom feel */
            padding: 0px;
            width: 100%;
            min-height: 150vh; /* Expands to cover the green arrow area */
            display: flex;
            flex-direction: column;
            justify-content: flex-start; 
            box-shadow: 0 -4px 32px rgba(0,0,0,0.3);
        }}

        /* MISSION BANNER - SHIFTED UP */
        .mission-banner {{
            background: {COLORS['blue']};
            color: white; 
            padding: 15px 25px; 
            border-radius: 10px;
            border-left: 8px solid {COLORS['sand']};
            /* ENSURE THIS IS 0: This pulls it to the top edge */
            margin-top: 0px !important; 
            margin-bottom: 20px;
        }}

        /* EFFICIENCY ANALYTICS (TAB 2) */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div#analytics_box) {{
            background-color: {COLORS['sand']} !important;
            border-radius: 12px !important;
            padding: 5px !important;
            border: none !important;
        }}

        /* AGENT DIALOGUE (TAB 3) */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div#chat_box) {{
            background-color: {COLORS['ink']} !important;
            border-radius: 12px !important;
            padding: 10px !important;
            height: 500px !important; /* Optimized for the expanded view */
            overflow-y: auto !important;
            color: white !important;
            border: 2px solid {COLORS['sand']};
        }}

        .grid-card {{
            background: {COLORS['emerald']};
            color: white; border-radius: 10px;
            padding: 45px; margin-top: 15px;
            border-left: 5px solid {COLORS['sand']};
        }}

        .plot-title {{ color: {COLORS['ink']}; font-weight: bold; font-size: 1.0rem; text-align: center; }}
        [data-testid="stHeader"] {{ background: transparent !important; }}
        [data-testid="stVerticalBlockBorderWrapper"] {{ background-color: transparent !important; }}
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING ---
try:
    raw_intensity, _ = get_carbon_data()
    intensity = int(raw_intensity)
except:
    intensity = 0

# --- HEADER RIBBON ---
last_res = st.session_state.get('last_result') or {}
history = st.session_state.get('history') or []

current_prompt_cost = 0.06 if 'lite' in str(last_res.get('model', '')).lower() else (0.90 if last_res else 0.00)
total_session_cost = sum(0.06 if 'lite' in str(e.get('model', '')).lower() else 0.90 for e in history)
current_savings = last_res.get('carbon_saved', 0)
total_session_savings = sum(e.get('saved', 0) for e in history)

st.markdown(f"""
    <div class="fixed-header">
        <div style="display: flex; flex-direction: column;">
            <h1 style="margin: 0; color: white; font-size: 24px;">🌿 GreenRouting</h1>
            <span style="color: {COLORS['sand']}; font-size: 10px; font-weight: bold;">NEXAVERSE OPTIMIZATION ENGINE</span>
        </div>
        <div style="display: flex; gap: 40px; text-align: right; color: white;">
            <div><p style="margin:0; font-size:10px; opacity:0.8;">Cost of Prompt</p><b style="font-size:18px;">${current_prompt_cost:.2f}</b></div>
            <div><p style="margin:0; font-size:10px; opacity:0.8;">Conversation Cost</p><b style="font-size:18px;">${total_session_cost:.2f}</b></div>
            <div><p style="margin:0; font-size:10px; opacity:0.8;">Carbon Savings</p><b style="font-size:18px; color: {COLORS['sand']};">{current_savings}mg</b></div>
            <div><p style="margin:0; font-size:10px; opacity:0.8;">Total Savings</p><b style="font-size:18px; color: {COLORS['sand']};">{total_session_savings}mg</b></div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)


# MISSION BANNER (Pinned to the top of the charcoal area)
st.markdown(f"""
    <div class="mission-banner">
        <h4 style="margin:0; color:{COLORS['sand']};">Our Mission</h4>
        <p style="font-size: 0.95rem; margin-top:5px; opacity:0.9;">
            Decarbonizing AI through grid-aware agentic routing. We optimize computational tasks 
            by selecting the most eco-efficient model based on real-time grid carbon intensity.
        </p>
    </div>
""", unsafe_allow_html=True)

# --- DUAL COLUMN CONTENT ---
col_left, col_right = st.columns([1, 2.5], gap="medium")

with col_left:
    # EFFICIENCY ANALYTICS
    with st.container(border=True):
        st.markdown('<div id="analytics_box"></div>', unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:{COLORS['ink']}; margin-top:0; text-align:left;'>Efficiency Analytics</h3>", unsafe_allow_html=True)
        
        if st.session_state.last_result:
            res = st.session_state.last_result
            is_lite = "lite" in str(res['model']).lower()
            
            st.markdown('<div class="plot-title">Cost Analysis ($)</div>', unsafe_allow_html=True)
            fig_cost = go.Figure(data=[
                go.Bar(name='Actual', x=['Nova Lite' if is_lite else 'Nova Pro'], y=[0.06 if is_lite else 0.90], marker_color=COLORS['emerald']),
                go.Bar(name='Bypassed', x=['Nova Pro' if is_lite else 'Nova Lite'], y=[0.90 if is_lite else 0.06], marker_color=COLORS['wine'])
            ])
            fig_cost.update_layout(height=160, margin=dict(t=5,b=5,l=5,r=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORS['ink']))
            st.plotly_chart(fig_cost, use_container_width=True)

            st.markdown('<div class="plot-title">Latency Profile (s)</div>', unsafe_allow_html=True)
            fig_lat = go.Figure(go.Scatter(x=['Nova Lite', 'Nova Pro'], y=[0.4, 1.8], mode='lines+markers', line=dict(color=COLORS['ink'], width=3)))
            fig_lat.update_layout(height=160, margin=dict(t=5,b=5,l=5,r=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=COLORS['ink']))
            st.plotly_chart(fig_lat, use_container_width=True)
        else:
            st.info("Awaiting sequence...")

    # Create a high-contrast physical divider
    st.markdown(f"""
        <div style="
            border-top: 2px dashed {COLORS['sand']}; 
            margin: 40px 0 20px 0; 
            opacity: 0.3;">
        </div>
    """, unsafe_allow_html=True)

    # GRID CONTEXT
    st.markdown(f"""
        <div class="grid-card">
            <h4 style="margin:0; color:{COLORS['sand']};">Grid Context</h4>
            <p style="font-size: 1.8rem; font-weight: bold; margin:2px;">{intensity} gCO₂</p>
            <p style="font-size: 0.8rem; opacity:0.9;">Real-time intensity: US-MIDA-PJM.</p>
        </div>
    """, unsafe_allow_html=True)

# --- CHARCOAL WORKSPACE START ---
st.markdown('<div class="charcoal-workspace">', unsafe_allow_html=True)

with col_right:
    # AGENT DIALOGUE (TAB 3)
    with st.container(border=True):
        st.markdown('<div id="chat_box"></div>', unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:{COLORS['sand']}; margin-top:0;'>💬 Agent Dialogue</h3>", unsafe_allow_html=True)
        
        for entry in st.session_state.history:
            with st.chat_message("user"):
                st.write(entry['prompt'])
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(f"**Optimization Protocol: `{entry['model']}`**")
                st.write(entry['response'])

    if prompt := st.chat_input("Dispatch task..."):
        try:
            result = run_green_route(prompt, None)
            st.session_state.history.append({
                "prompt": prompt, "model": result['model'], 
                "response": result['response'], "saved": result.get('carbon_saved', 0)
            })
            st.session_state.last_result = result
            st.rerun()
        except Exception as e:
            st.error(f"Routing Error: {e}")

# --- CLOSING CHARCOAL WORKSPACE ---
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
