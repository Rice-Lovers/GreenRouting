import streamlit as st
import plotly.graph_objects as go
import os

# --- THE CRITICAL IMPORT ---
try:
    from main import run_green_route, MODEL_MAP
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
    "dgreen": "#173E33",    
    "lgreen": "#63BC69",    
    "blue": "#2B4162",    
    "orange": "#FE9547 ", 
    "ink": "#0F1E25",
    "charcoal": "#0D1B2A", #didn't use
    "bg_white": "#FFFFFF"
}

# --- REFINED ATOMIC CSS ---
st.markdown(f"""
    <style>
        /* 1. MAIN CONTAINER: Creates the "Gap" between header and dashboard */
        [data-testid="stAppViewBlockContainer"] {{
            max-width: 95% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            /* INCREASED: Forces the dashboard down to show the white background separation */
            padding-top: 120px !important; 
            margin: 0 auto;
        }}
        [data-testid="stHeader"] {{
            display: none !important;
        }}        
        .stApp {{ background-color: {COLORS['ink']} !important;}}

       
        /* 2. Header Tab: */
        .fixed-header {{
            position: fixed; 
            top: 0; !important;
            left: 0; 
            width: 100%; 
            height: 120px;
            background-color: {COLORS['dgreen']} !important;
            border-bottom: 4px solid {COLORS['lgreen']};
            z-index: 999; 
            padding: 0px 60px; 
            display: flex;
            align-items: center;
            /* HIGHLIGHT: This shadow creates the physical 'separation' feel */
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}

        /* Target the vertical column containing the logo and tagline */
        .header-content {{
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        /* Remove default margins that cause misalignment */
        .header-content h1 {{
            margin: 0 !important;
            line-height: 1.1 !important;
            padding-bottom: 2px !important;
        }}

        .header-content p {{
            margin: 0 !important;
            line-height: 1 !important;
        }}
         
        

        /* 3. Analytics Dropdown: */
        .stExpander {{
            border: 2px solid {COLORS['lgreen']} !important;
            background-color: {COLORS['lgreen']} !important;
            border-radius: 12px !important;
            margin-bottom: 20px !important;
        }}
        /* Target all possible states: normal, hover, focus, and OPEN */
        [data-testid="stExpander"] details summary,
        [data-testid="stExpander"] details summary:hover,
        [data-testid="stExpander"] details summary:focus,
        [data-testid="stExpander"] details summary:active,
        [data-testid="stExpander"] details[open] summary {{
            background-color: {COLORS['lgreen']} !important;
            border-radius: 12px !important;
        }}
        /* Targets the clickable header of the dropdown specifically */
        [data-testid="stExpanderSummary"] {{
            background-color: {COLORS['lgreen']} !important;
            border-radius: 12px !important;
            height: 55px !important;
        }}
        
        /* Forces the text inside the green dropdown to be Ink (Dark Blue/Black) */
        [data-testid="stExpanderSummary"] p {{
            color: {COLORS['ink']} !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
        }}

        [data-testid="stExpanderDetails"] {{
            background-color: {COLORS['lgreen']} !important;
            border-radius: 0 0 12px 12px !important;
        }}

        /* 4. Mission Banner: */
        .mission-banner {{
            background: {COLORS['blue']};
            color: white; 
            padding: 20px; 
            border-radius: 12px;
            border-left: 8px solid {COLORS['lgreen']};
            margin-bottom: 15px;
        }}

        /* 5. Grid Card: */
        .grid-card {{
            background-color: {COLORS['orange']} !important;
            color: white;
            border-radius: 12px;
            padding: 20px;
            border-left: 8px solid {COLORS['lgreen']};
        }}

        
        /* 6. Impact Metrics Box: Changed to dgreen with improved font visibility */
        .impact-box {{
            background-color: {COLORS['dgreen']};
            color: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 8px solid {COLORS['lgreen']};
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}
        
        .metric-row {{ 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 10px; 
            border-bottom: 1px solid rgba(250, 159, 66, 0.3); 
            padding-bottom: 5px; 
        }}
        
        .metric-label {{ font-size: 0.85rem; color: #FFFFFF; opacity: 0.9; font-weight: 500; }}
        .metric-value {{ font-size: 1rem; font-weight: bold; color: {COLORS['lgreen']}; }}

        /* 7. Registry Box: */
        .registry-box {{
            background-color: {COLORS['blue']};
            color: white;
            border-radius: 12px;
            padding: 15px;
            margin-top: 20px;
            font-size: 0.85rem;
            border-left: 8px solid {COLORS['orange']};
        }}

        /* 8. Agentic Dialogue: White text visibility */
        .agent-dialogue-header {{
            color: {COLORS['bg_white']}; !important;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        /* Chat Container Styling */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div#chat_box) {{
            background-color: {COLORS['ink']} !important;
            border-radius: 12px !important;
            padding: 15px !important;
            border: 10px solid rgba(255,255,255,0.1);
        }}
        /* Force all text inside the chat container to be white */
        [data-testid="stChatMessage"] p, 
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div {{
            color: #FFFFFF !important;
            font-size: 1rem !important;
        }}

        /* Target the specific "Assistant" and "User" bubble backgrounds */
        /* This ensures the bubbles don't default to a grey that hides your text */
        [data-testid="stChatMessage"] {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 10px !important;
            padding: 10px !important;
            margin-bottom: 10px !important;
        }}

        /* 3. Fix the "Model Selected" bold text */
        [data-testid="stChatMessage"] strong {{
            color: #FE9547 !important; /* COLORS['lgreen'] for the model name */
        }}

        /* 4. Ensure code blocks or technical outputs are visible */
        [data-testid="stChatMessage"] code {{
            background-color: #2B4162 !important; /* COLORS['blue'] */
            color: #FFFFFF !important;
        }}
        /* --- 9. Bottom Chat Input Styling --- */
        
        /* 1. Keep the outer wrapper transparent so it doesn't look bulky */
        [data-testid="stChatInput"] {{
            background-color: transparent !important;
        }}
        
        /* 2. Target the actual input "pill" (the first div inside the wrapper) */
        [data-testid="stChatInput"] > div {{
            background-color: {COLORS['charcoal']} !important;
            border: 1px solid {COLORS['orange']} !important; /* Orange border here! */
            border-radius: 12px !important;
        }}
        
        /* 3. Force the grey text area inside to become completely transparent */
        .stChatInputTextArea > div {{
            background-color: transparent !important;
        }}
        
        /* 4. Make the text you type white */
        [data-testid="stChatInputTextArea"] textarea {{
            color: {COLORS['bg_white']} !important;
        }}

        /* --- 10. Browse Files Button Styling --- */
        [data-testid="stBaseButton-secondary"] {{
            background-color: {COLORS['orange']} !important;
            color: {COLORS['ink']} !important; 
            border: none !important;
            font-weight: bold !important;
        }}

        /* Forces the chart titles to be Pure Black */
        .plot-title {{
            color: #000000 !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING & LOGIC ---
try:
    raw_intensity, _ = get_carbon_data()
    intensity = int(raw_intensity)
except:
    intensity = 420 

last_res = st.session_state.get('last_result') or {}
history = st.session_state.get('history') or []

# REVISED METRICS
COST_LITE, COST_PRO = 0.06, 0.90
current_sci = last_res.get('sci_score', 0.0)
total_saved_mg = sum(e.get('saved', 0) for e in history)
session_avg_sci = sum(e.get('sci_score', 0) for e in history) / len(history) if history else 0.0

current_prompt_cost = COST_LITE if 'LITE' in str(last_res.get('model', '')).upper() else (COST_PRO if last_res else 0.00)
total_session_cost = sum(COST_LITE if 'LITE' in str(e.get('model', '')).upper() else COST_PRO for e in history)
current_monetary_saved = (COST_PRO - COST_LITE) if 'LITE' in str(last_res.get('model', '')).upper() else 0.00
total_monetary_saved = (len(history) * COST_PRO) - total_session_cost

# --- HEADER RIBBON (OPTIMIZED) ---
# Header Ribbon (Updated for height)
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <h1 style="color: white; font-size: 38px; letter-spacing: -1px;">🌿 GreenRouting</h1>
            <p style="color: {COLORS['lgreen']}; font-size: 14px; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">
                Agentic Decarbonization Engine
            </p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)

st.write("") 


# Mission Banner
st.markdown(f"""
    <div class="mission-banner">
        <h3 style="margin:0; color:{COLORS['lgreen']}; font-size: 1.2rem;">The Mission</h3>
        <p style="font-size: 0.95rem; margin-top:5px; opacity:0.9; line-height: 1.4;">
            Optimizing AI Software Carbon Intensity (SCI) through grid-aware routing.
        </p>
    </div>
""", unsafe_allow_html=True)

# 2. Analytics Dropdown (Shifted under Mission)
with st.expander("📊 Comparative Analysis (Full Registry)", expanded=False):
    col_a, col_b = st.columns(2)
    models = ["Nova Lite", "Llama 3.2", "Claude Haiku", "Mistral Small", "Nova Pro", "Llama 3.1", "Claude 3.5", "Mistral L"]
    costs = [0.06, 0.06, 0.08, 0.06, 0.90, 0.85, 0.95, 0.90]
    latency = [0.4, 0.5, 0.4, 0.6, 1.8, 2.1, 1.7, 2.0]
    
    with col_a:
        st.markdown('<p class="plot-title">Cost Comparison ($)</p>', unsafe_allow_html=True)
        fig_cost = go.Figure(go.Bar(x=models, y=costs, marker_color=COLORS['orange']))
        # Explicit width and height for a consistent look
        fig_cost.update_layout(
            width=450, 
            height=250, 
            margin=dict(t=20,b=40,l=50,r=10), 
            paper_bgcolor=COLORS['bg_white'], 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(size=10, color=COLORS['ink'])
        )
        st.plotly_chart(fig_cost, width= "stretch", theme=None) 
        
    with col_b:
        st.markdown('<p class="plot-title">Latency Comparison (s)</p>', unsafe_allow_html=True)
        fig_lat = go.Figure(go.Bar(x=models, y=latency, marker_color=COLORS['dgreen']))
        # Matching width and height
        fig_lat.update_layout(
            width=450, 
            height=250, 
            margin=dict(t=20,b=40,l=50,r=10), 
            paper_bgcolor=COLORS['bg_white'], 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(size=10, color=COLORS['ink'])
        )
        st.plotly_chart(fig_lat, width= "stretch",  theme=None) 
# --- DUAL COLUMN LAYOUT ---
col_left, col_right = st.columns([1, 2.3], gap="large")

with col_left:
    # 3. NEW: Impact Metrics Box
    # IMPACT BOX (Now dgreen)
    st.markdown(f"""
        <div class="impact-box">
            <h3 style="margin:0 0 15px 0; color:{COLORS['lgreen']}; border-bottom: 2px solid {COLORS['lgreen']}; padding-bottom:10px;">Impact Metrics</h3>
            <div class="metric-row"><span class="metric-label">Current SCI</span><span class="metric-value">{current_sci:.2f} mg</span></div>
            <div class="metric-row"><span class="metric-label">Session Avg SCI</span><span class="metric-value">{session_avg_sci:.2f} mg</span></div>
            <div class="metric-row"><span class="metric-label">Total Carbon Saved</span><span class="metric-value">{total_saved_mg:.2f} mg</span></div>
            <div class="metric-row"><span class="metric-label">Current Prompt Cost</span><span class="metric-value">${current_prompt_cost:.3f}</span></div>
            <div class="metric-row"><span class="metric-label">Session Total Cost</span><span class="metric-value">${total_session_cost:.2f}</span></div>
            <div class="metric-row"><span class="metric-label">Current Money Saved</span><span class="metric-value">${current_monetary_saved:.2f}</span></div>
            <div class="metric-row"><span class="metric-label">Total Money Saved</span><span class="metric-value" style="color:#00FF00;">${total_monetary_saved:.2f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    # Grid Card
    st.markdown(f"""
        <div class="grid-card">
            <h4 style="margin:0; color:{COLORS['dgreen']}; text-transform: uppercase; font-size: 0.8rem;">Live Grid Intensity</h4>
            <p style="font-size: 2.2rem; font-weight: 900; margin:5px 0;">{intensity} <span style="font-size: 0.9rem;">gCO₂/kWh</span></p>
        </div>
    """, unsafe_allow_html=True)

    # Registry Box
    st.markdown('<div class="registry-box"><b>🌐 Active Registry</b><br>Eco: Nova, Llama, Claude, Mistral<br>Power: Nova Pro, Llama 70B, Claude Sonnet, Mistral Large</div>', unsafe_allow_html=True)

with col_right:
    st.markdown(f"<h3 style='color:{COLORS['bg_white']}; margin-top:0;'>💬 Carbon-Aware Agent</h3>", unsafe_allow_html=True)
    chat_container = st.container(height=480)
    with chat_container:
        st.markdown('<div id="chat_box"></div>', unsafe_allow_html=True)
        if not st.session_state.history:
            st.markdown('<p style="color: #FFFFFF; opacity: 0.8; font-size: 0.8rem; margin-bottom: 10px;">Ready for dispatch.</p>', unsafe_allow_html=True)
        for entry in st.session_state.history:
            with st.chat_message("user"): st.markdown(entry['prompt'])
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(f"**Model Selected: `{entry['model']}`**")
                st.markdown(entry['response'])

    # 1. ADD THIS: The File Uploader
    uploaded_file = st.file_uploader(
        "📎 Attach context (CSV, JSON, TXT)", 
        type=['csv', 'json', 'txt'], 
        label_visibility="collapsed" # Hides the default label for a cleaner UI
    )

    if prompt := st.chat_input("Dispatch task..."):
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant", avatar="🌿"):
                with st.status("🌿 Analyzing SCI Factors...") as status:
                    result = run_green_route(prompt) 
                    status.update(label=f"✅ Routed to {result['model']}", state="complete")

        st.session_state.history.append({"prompt": prompt, "model": result['model'], "response": result['response'], "saved": result.get('carbon_saved', 0), "sci_score": result.get('sci_score', 0)})
        st.session_state.last_result = result
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
