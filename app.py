import streamlit as st
import plotly.graph_objects as go
import os
import pandas as pd
import uuid
import io
from database import get_total_savings
from reporting import ReportingEngine

# --- THE CRITICAL IMPORT ---
try:
    from main import run_green_route, MODEL_MAP
    from carbon_api import get_carbon_data
except ImportError:
    st.error("❌ Project files missing. Ensure all backend files are present.")

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GreenRouting Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INITIALIZE SESSION STATE ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:12]
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'current_file' not in st.session_state:
    st.session_state.current_file = None

# --- NEXAVERSE COLOR PALETTE ---
COLORS = {
    "wine": "#4A2545",    
    "sand": "#FBBF24",    
    "blue": "#2B4162",    
    "emerald": "#0B6E4F", 
    "ink": "#031927",
    "charcoal": "#0D1B2A",
    "bg_white": "#FFFFFF"
}

# --- ATOMIC CSS ---
st.markdown(f"""
    <style>
        [data-testid="stAppViewBlockContainer"] {{
            max-width: 95% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 10.180px !important; 
            margin: 0 auto;
        }}
        [data-testid="stHeader"] {{ display: none !important; }}        
        .stApp {{ background-color: {COLORS['ink']} !important;}}

        .fixed-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 120px;
            background-color: {COLORS['wine']} !important;
            border-bottom: 4px solid {COLORS['sand']};
            z-index: 999; padding: 0px 60px; display: flex; align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}

        .mission-banner {{
            background: {COLORS['blue']}; color: white; padding: 20px; border-radius: 12px;
            border-left: 8px solid {COLORS['sand']}; margin-bottom: 15px;
        }}

        /* COMPACT FILE UPLOADER STYLING */
        [data-testid="stFileUploadDropzone"] {{
            padding: 0 !important;
            border: none !important;
            background-color: transparent !important;
            min-height: 45px !important;
        }}
        [data-testid="stFileUploadDropzone"] div {{
            display: none !important;
        }}
        [data-testid="stFileUploadDropzone"]::before {{
            content: "📎";
            font-size: 24px;
            cursor: pointer;
            visibility: visible;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 45px;
        }}
        
        .impact-box {{
            background-color: {COLORS['wine']}; color: white; border-radius: 12px; padding: 20px;
            margin-bottom: 20px; border-left: 8px solid {COLORS['sand']};
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}
        
        .metric-row {{ 
            display: flex; justify-content: space-between; margin-bottom: 10px; 
            border-bottom: 1px solid rgba(250, 159, 66, 0.3); padding-bottom: 5px; 
        }}
        
        .metric-label {{ font-size: 0.85rem; color: #FFFFFF; opacity: 0.9; font-weight: 500; }}
        .metric-value {{ font-size: 1rem; font-weight: bold; color: {COLORS['sand']}; }}

        div.stButton > button {{
            border-radius: 20px !important;
            background-color: {COLORS['sand']} !important;
            color: {COLORS['ink']} !important;
            font-weight: bold !important;
            border: none !important;
            height: 45px !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- DATA FETCHING ---
try:
    raw_intensity, _ = get_carbon_data()
    intensity = int(raw_intensity)
except: 
    intensity = 420 

# DATABASE SOURCE OF TRUTH
db_lifetime_savings = get_total_savings(session_id=st.session_state.session_id)
last_res = st.session_state.get('last_result') or {}
history = st.session_state.history

# --- METRICS CALCULATION ---
current_sci = last_res.get('sci_score', 0.0)
display_lifetime = db_lifetime_savings
total_session_cost = sum(0.06 if 'LITE' in str(e.get('model', '')).upper() else 0.90 for e in history)
total_monetary_saved = (len(history) * 0.90) - total_session_cost if len(history) > 0 else 0.0

# --- HEADER ---
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <h1 style="color: white; font-size: 38px; letter-spacing: -1px;">🌿 GreenRouting</h1>
            <p style="color: {COLORS['sand']}; font-size: 14px; text-transform: uppercase; font-weight: bold;">Agentic Decarbonization Engine</p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.write("") 
st.write("") 

# --- 1. MISSION BANNER ---
st.markdown(f"""
    <div class="mission-banner">
        <h3 style="margin:0; color:{COLORS['sand']}; font-size: 1.2rem;">The Mission</h3>
        <p style="font-size: 0.95rem; margin-top:5px; opacity:0.9;">Optimizing AI Software Carbon Intensity (SCI) through grid-aware routing.</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. PLOTLY ANALYSIS ---
with st.expander("📊 Comparative Analysis (Full Registry)", expanded=False):
    col_a, col_b = st.columns(2)
    models = ["Nova Lite", "Llama 3.2", "Claude Haiku", "Mistral Small", "Nova Pro", "Llama 3.1", "Claude 3.5", "Mistral L"]
    
    xaxis_config = dict(
        tickmode='array',
        tickvals=list(range(len(models))),
        ticktext=models,
        tickfont=dict(color='#333333', size=11, family="Arial Black"),
        tickangle=-45,
        automargin=True
    )
    
    yaxis_config = dict(tickfont=dict(color='#333333', size=10), showgrid=True, gridcolor='lightgray')

    with col_a:
        fig_cost = go.Figure(go.Bar(x=models, y=[0.06, 0.06, 0.08, 0.06, 0.90, 0.85, 0.95, 0.90], marker_color=COLORS['emerald']))
        fig_cost.update_layout(
            title=dict(text="<b>Cost per 1k Tokens ($)</b>", font=dict(color='black', size=16)), 
            height=350, margin=dict(t=60, b=120, l=50, r=20), paper_bgcolor='white', plot_bgcolor='white',
            xaxis=xaxis_config, yaxis=yaxis_config
        )
        st.plotly_chart(fig_cost, use_container_width=True, theme=None)
        
    with col_b:
        fig_lat = go.Figure(go.Bar(x=models, y=[0.4, 0.5, 0.4, 0.6, 1.8, 2.1, 1.7, 2.0], marker_color=COLORS['wine']))
        fig_lat.update_layout(
            title=dict(text="<b>Latency (Seconds)</b>", font=dict(color='black', size=16)), 
            height=350, margin=dict(t=60, b=120, l=50, r=20), paper_bgcolor='white', plot_bgcolor='white',
            xaxis=xaxis_config, yaxis=yaxis_config
        )
        st.plotly_chart(fig_lat, use_container_width=True, theme=None)

# --- DUAL COLUMN LAYOUT ---
col_left, col_right = st.columns([1, 2.3], gap="large")

with col_left:
    st.markdown(f"""
        <div class="impact-box">
            <h3 style="margin:0 0 15px 0; color:{COLORS['sand']}; border-bottom: 2px solid {COLORS['sand']}; padding-bottom:10px;">Impact Metrics</h3>
            <div class="metric-row"><span class="metric-label">Current SCI</span><span class="metric-value">{current_sci:.2f} mg</span></div>
            <div class="metric-row"><span class="metric-label">Lifetime Carbon Saved</span><span class="metric-value">{display_lifetime:.2f} mg</span></div>
            <div class="metric-row"><span class="metric-label">Total Saved</span><span class="metric-value" style="color:#00FF00;">${total_monetary_saved:.2f}</span></div>
        </div>
    """, unsafe_allow_html=True)

    if display_lifetime < 3000.0:
        next_goal, goal_name = 3000.0, "Silver"
    elif display_lifetime < 5000.0:
        next_goal, goal_name = 5000.0, "Gold"
    elif display_lifetime < 10000.0:
        next_goal, goal_name = 10000.0, "Platinum"
    else:
        next_goal, goal_name = None, "Max Tier"

    if next_goal:
        progress = min(display_lifetime / next_goal, 1.0)
        st.write(f"📈 Progress to {goal_name}: {display_lifetime:.1f} / {next_goal} mg")
        st.progress(progress)

    st.markdown(f"""
        <div class="grid-card" style="margin-top:20px;">
            <h4 style="margin:0; color:{COLORS['sand']}; text-transform: uppercase; font-size: 0.8rem;">Live Grid Intensity</h4>
            <p style="font-size: 2.2rem; font-weight: 900; margin:5px 0;">{intensity} <span style="font-size: 0.9rem;">gCO₂/kWh</span></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="registry-box"><b>🌐 Active Registry</b><br>Eco: Nova, Llama, Claude, Mistral<br>Power: Nova Pro, Llama 70B, Claude Sonnet, Mistral Large</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"<h4 style='color:white;'>📋 Compliance & Recognition</h4>", unsafe_allow_html=True)
    company_name = st.text_input("Company Name", value="IBM")
    
    reporter = ReportingEngine(company_name)
    tier = reporter.get_achievement_tier(display_lifetime)
    
    if not tier:
        st.warning(f"🔒 Milestone Locked. Save 3000.0mg to unlock.")
        st.button("🏅 Generate Achievement Cert", disabled=True, use_container_width=True)
    else:
        st.success(f"🔓 {tier['tier']} Milestone Achieved!")
        pdf_bytes = reporter.generate_pdf_certificate(display_lifetime)
        st.download_button(
            label=f"🥇 Download {tier['tier']} PDF Certificate",
            data=pdf_bytes,
            file_name=f"Nexaverse_{tier['tier']}_Certificate.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    if st.session_state.history:
        audit = reporter.generate_esg_audit(st.session_state.history)
        csv_df = pd.DataFrame([{
            "Report ID": audit['audit_header']['report_id'],
            "Carbon Mitigated (mg)": audit['metrics']['total_mitigated_mg'],
            "Status": audit['compliance']['status']
        }])
        st.download_button("📥 Download ESG Audit (CSV)", data=csv_df.to_csv(index=False), file_name=f"ESG_Audit_{company_name}.csv", use_container_width=True)

with col_right:
    st.markdown(f"<h3 style='color:{COLORS['bg_white']}; margin-top:0;'>💬 Carbon-Aware Agent</h3>", unsafe_allow_html=True)
    
    chat_container = st.container(height=550)
    
    with chat_container:
        if not st.session_state.history:
            st.markdown('<p style="color: #FFFFFF; opacity: 0.8; font-size: 0.8rem; margin-bottom: 10px;">Ready for dispatch.</p>', unsafe_allow_html=True)
        
        for entry in st.session_state.history:
            with st.chat_message("user"):
                st.markdown(entry['prompt'])
            with st.chat_message("assistant", avatar="🌿"):
                model_lbl = f"♻️ {entry['model']}" if "LITE" in entry['model'].upper() else entry['model']
                st.markdown(f"**Model Selected: `{model_lbl}`**")
                st.markdown(entry['response'])

    # --- CUSTOM COMPACT CHAT BAR ---
    st.write("")
    c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
    
    with c1:
        uploaded_file = st.file_uploader("Attach", type=["png", "jpg", "pdf"], label_visibility="collapsed", key="local_uploader")
        if uploaded_file:
            st.session_state.current_file = uploaded_file.getvalue()
            st.toast(f"📎 {uploaded_file.name} attached")

    with c2:
        user_prompt = st.text_input("Message", placeholder="Dispatch task or ask about the grid...", label_visibility="collapsed")

    with c3:
        submit = st.button("Send", use_container_width=True)

    if submit and user_prompt:
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_prompt)
            
            with st.chat_message("assistant", avatar="🌿"):
                with st.status("🌿 Analyzing SCI Factors...") as status:
                    result = run_green_route(
                        user_prompt, 
                        image_path=st.session_state.current_file, 
                        session_id=st.session_state.session_id
                    ) 
                    status.update(label=f"✅ Routed to {result['model']}", state="complete")
                
                model_lbl = f"♻️ {result['model']}" if "LITE" in result['model'].upper() else result['model']
                st.markdown(f"**Model Selected: `{model_lbl}`**")
                st.markdown(result['response'])

        st.session_state.history.append({
            "prompt": user_prompt, 
            "model": result['model'], 
            "response": result['response'], 
            "saved": result.get('carbon_saved', 0), 
            "sci_score": result.get('sci_score', 0)
        })
        st.session_state.last_result = result
        st.session_state.current_file = None 
        st.rerun()
