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

# --- REFINED ATOMIC CSS ---
st.markdown(f"""
    <style>
        /* Main Container: Tighten side margins and remove top white space */
        [data-testid="stAppViewBlockContainer"] {{
            max-width: 95% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 8rem !important;
            margin: 0 auto;
        }}
        
        .stApp {{ background-color: {COLORS['bg_white']} !important; }}
        
        /* Fixed Header */
        .fixed-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 90px;
            background: {COLORS['wine']}; border-bottom: 4px solid {COLORS['sand']};
            z-index: 999; padding: 10px 60px; display: flex;
            justify-content: space-between; align-items: center;
        }}

        .main-content-wrapper {{ 
            margin-top: 20px !important; /* Offset for header + small gap */
            padding: 0px !important;
            background-color: {COLORS['bg_white']} !important;
        }}

       

        /* Unified Dashboard Box */
        .main-workspace {{
            background-color: {COLORS['charcoal']};
            border-radius: 15px;
            padding: 25px;
            width: 100%;
            min-height: auto;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            margin-bottom: 50px;
        }}

        /* Mission Banner */
        .mission-banner {{
            background: {COLORS['blue']};
            color: white; 
            padding: 20px 20px; 
            border-radius: 12px;
            border-left: 8px solid {COLORS['sand']};
            margin-bottom: 25px;
        }}

        /* Side Card Styles */
        .analytics_box {{
            background-color: {COLORS['sand']} !important;
            color: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

         /* 1. Target the main Expander container */
        .stExpander {{
            border: none !important;
            background-color: {COLORS['sand']} !important;
            border-radius: 12px !important;
        }}

        /* 2. Target the Header/Summary specifically */
        [data-testid="stExpanderSummary"] {{
            background-color: {COLORS['sand']} !important;
            color: {COLORS['ink']} !important; /* Force text to dark ink */
            border-radius: 12px !important;
            border: none !important;
        }}

        /* 3. Change the hover effect so it stays Sand */
        [data-testid="stExpanderSummary"] svg {{
        fill: {COLORS['ink']} !important;
        color: {COLORS['ink']} !important;
        }}

        /* 4. Remove the hover effect that turns it grey */
        [data-testid="stExpanderSummary"]:hover {{
        background-color: {COLORS['sand']} !important;
        border-radius: 12px !important;
        }}

        /* 5. The Body (Details) - Ensure it stays sand when open */
        [data-testid="stExpanderDetails"] {{
        background-color: {COLORS['sand']} !important;
        color: {COLORS['ink']} !important;
        border-radius: 0 0 12px 12px !important;
        padding: 15px !important;
        }}

        .grid-card {{
            background-color: {COLORS['emerald']} !important;
            color: white;
            border-radius: 12px;
            padding: 25px;
            border-left: 8px solid {COLORS['sand']};
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

        /* Chat Styling */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div#chat_box) {{
            background-color: {COLORS['ink']} !important;
            border-radius: 12px !important;
            padding: 15px !important;
            border-left: 5px solid {COLORS['sand']};
            box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
        }}

        [data-testid="stHeader"] {{ background: transparent !important; }}
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING ---
try:
    raw_intensity = get_carbon_data()
    intensity = int(raw_intensity)
except:
    intensity = 420 # Placeholder for PJM average

# --- HEADER LOGIC & UI ---
last_res = st.session_state.get('last_result') or {}
history = st.session_state.get('history') or []

current_prompt_cost = 0.06 if 'lite' in str(last_res.get('model', '')).lower() else (0.90 if last_res else 0.00)
total_session_cost = sum(0.06 if 'lite' in str(e.get('model', '')).lower() else 0.90 for e in history)
current_savings = last_res.get('carbon_saved', 0)
total_session_savings = sum(e.get('saved', 0) for e in history)

st.markdown(f"""
    <div class="fixed-header">
        <div style="display: flex; flex-direction: column;">
            <h1 style="margin: 0; color: white; font-size: 32px; letter-spacing: -1px;">🌿 GreenRouting</h1>
            <span style="color: {COLORS['sand']}; font-size: 14px; text-transform: uppercase;">Agentic Decarbonization Engine</span>
        </div>
        <div style="display: flex; gap: 50px; text-align: right; color: white;">
            <div><p style="margin:0; font-size:12px; opacity:0.7;">PROMPT COST</p><b style="font-size:22px;">${current_prompt_cost:.2f}</b></div>
            <div><p style="margin:0; font-size:12px; opacity:0.7;">SESSION TOTAL</p><b style="font-size:22px;">${total_session_cost:.2f}</b></div>
            <div><p style="margin:0; font-size:12px; opacity:0.7;">SAVED</p><b style="font-size:22px; color: {COLORS['sand']};">{current_savings}mg</b></div>
            <div><p style="margin:0; font-size:12px; opacity:0.7; font-weight: bold;">TOTAL IMPACT</p><b style="font-size:22px; color: {COLORS['sand']};">{total_session_savings}mg</b></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- PAGE CONTENT ---
st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

# Dashboard Mission
st.markdown(f"""
    <div class="mission-banner">
        <h3 style="margin:0; color:{COLORS['sand']}; font-size: 1.4rem;">The Mission</h3>
        <p style="font-size: 1.05rem; margin-top:8px; opacity:0.95; line-height: 1.5;">
            Reducing the carbon footprint of Generative AI. Our engine analyzes real-time grid intensity 
            to route complex reasoning to high-capacity models only when the grid is clean, 
            defaulting to eco-efficient models during high-carbon periods.
        </p>
    </div>
""", unsafe_allow_html=True)

# Layout Columns
col_left, col_right = st.columns([1, 2.3], gap="large")

with col_left:
    # Analytics Card
    with st.expander("Comparative Analysis", expanded=False):
        if st.session_state.last_result:
            res = st.session_state.last_result
            is_lite = "lite" in str(res['model']).lower()
            
            # Cost Analysis Plot
            st.markdown('<div class="plot-title">Cost Analysis ($)</div>', unsafe_allow_html=True)
            fig_cost = go.Figure(data=[
                go.Bar(name='Used', x=['Current'], y=[0.06 if is_lite else 0.90], marker_color=COLORS['emerald']),
                go.Bar(name='Avoided', x=['Pro Fallback'], y=[0.90 if is_lite else 0.00], marker_color=COLORS['wine'])
            ])
            fig_cost.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_cost, use_container_width=True)
            
            # UPDATED: Added Latency Profile plot as a second comparative metric
            st.markdown('<div class="plot-title">Latency Profile (s)</div>', unsafe_allow_html=True)
            fig_lat = go.Figure(go.Scatter(
                x=['Nova Lite', 'Nova Pro'], 
                y=[0.4, 1.8], 
                mode='lines+markers', 
                line=dict(color=COLORS['ink'], width=3)
            ))
            fig_lat.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_lat, use_container_width=True)
        else:
            st.markdown(f"<p style='color:{COLORS['ink']}; opacity:0.8;'>Dispatch a task to see metrics.</p>", unsafe_allow_html=True)

    # Grid Card
    st.markdown(f"""
        <div class="grid-card">
            <h4 style="margin:0; color:{COLORS['sand']}; text-transform: uppercase; font-size: 0.8rem;">Live Grid Intensity</h4>
            <p style="font-size: 2.8rem; font-weight: 900; margin:5px 0;">{intensity} <span style="font-size: 1rem;">gCO₂/kWh</span></p>
            <p style="font-size: 0.9rem; opacity:0.8;">Region: <b>US-PJM (Virginia)</b></p>
        </div>
    """, unsafe_allow_html=True)

with col_right:
    # Main Workspace
    
    st.markdown(f"<h3 style='color:{COLORS['bg_white']}; margin-top:0;'>💬 Carbon-Aware Agent</h3>", unsafe_allow_html=True)
    
    chat_container = st.container(height=480)
    with chat_container:
        st.markdown('<div id="chat_box"></div>', unsafe_allow_html=True)
        if not st.session_state.history:
            st.caption("Ready for dispatch.")
            
        for entry in st.session_state.history:
            with st.chat_message("user"):
                st.markdown(entry['prompt'])
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(f"**Model Selected: `{entry['model']}`**")
                st.markdown(entry['response'])

    if prompt := st.chat_input("Dispatch task to the Green Engine..."):
        # 1. Immediately display the user message in the UI
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        try:
            # 2. Create the loading state
            with chat_container:
                with st.chat_message("assistant", avatar="🌿"):
                    # Use st.status for a professional 'Thinking' look
                    with st.status("🌿 Agent is analyzing...", expanded=True) as status:
                        st.write("Checking real-time grid intensity...")
                        # Small delay to let the user see the status (optional)
                        
                        st.write("Determining optimal routing complexity...")
                        result = run_green_route(prompt) 
                        
                        status.update(label="✅ Optimization Complete", state="complete", expanded=False)

            # 3. Save to history and update UI
            st.session_state.history.append({
                "prompt": prompt, 
                "model": result['model'], 
                "response": result['response'], 
                "saved": result.get('carbon_saved', 0)
            })
            st.session_state.last_result = result
            st.rerun()
            
        except Exception as e:
            st.error(f"Routing Error: {e}")
      
st.markdown('</div>', unsafe_allow_html=True)
