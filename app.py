import streamlit as st
import plotly.graph_objects as go
import random
import time
import os

# --- THE CRITICAL IMPORT ---
try:
    from main import run_green_route
    from carbon_api import get_carbon_data # Import this to fix the 0 issue
except ImportError:
    st.error("❌ Project files missing. Ensure main.py and carbon_api.py are present.")

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GreenRouting Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .stApp { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
        div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 600; }
        div[data-testid="stChatInput"] {
            border: 2px solid #26A998 !important;
            box-shadow: 0px 6px 15px rgba(35, 44, 82, 0.15) !important;
            border-radius: 12px !important;
        }
        .response-container {
            padding: 20px;
            border-radius: 15px;
            background-color: #1e2630;
            border-left: 5px solid #2A9D8F;
            margin-top: 20px;
            color: #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZE STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

# --- HEADER & STATUS ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("<h1 style='color: #2A9D8F;'>GreenRouting Intelligence</h1>", unsafe_allow_html=True)

with col_head2:
    # --- FIX: Fetch real data if session is empty ---
    if st.session_state.last_result:
        raw_intensity = st.session_state.last_result['intensity']
    else:
        try:
            # Fetch fresh data from your API on page load
            _, raw_intensity = get_carbon_data()
        except:
            raw_intensity = 0

    try:
        intensity = int(raw_intensity)
    except:
        intensity = 0
        
    status_color = "#2A9D8F" if intensity < 40 else "#E76F51"
    status_text = "Optimal (Clean Grid)" if intensity < 40 else "Alert (Dirty Grid)"
    
    st.markdown(f"""
        <div style="padding: 15px; border-radius: 12px; background-color: #1a1c24; text-align: center; border: 1px solid #333;">
            <p style="margin: 0; font-size: 18px; color: #888;">Current Grid Carbon</p>
            <h2 style="margin: 0; color: {status_color};">{intensity} gCO₂/kWh</h2>
            <p style="margin: 0; font-size: 0.8rem; font-weight: 600;">{status_text}</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# --- DASHBOARD VISUALS ---
def create_dashboards(model_name):
    col1, col2, col3 = st.columns(3)
    is_lite = "lite" in str(model_name).lower()
    accent = '#2A9D8F'
    muted = '#264653'
    
    with col1:
        fig = go.Figure(go.Bar(x=['Nova Lite', 'Nova Pro'], y=[0.06, 0.90], 
                               marker_color=[accent if is_lite else muted, muted if is_lite else accent]))
        fig.update_layout(title="Cost Efficiency ($)", height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#888"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        saved = 182 if is_lite else 0
        fig = go.Figure(go.Indicator(mode="gauge+number", value=saved, gauge={'bar': {'color': accent}, 'axis': {'range': [0, 500]}, 'bgcolor': "#333"}))
        fig.update_layout(title="Estimated CO₂ Saved (mg)", height=280, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#888"))
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = go.Figure(go.Bar(x=[0.4, 1.8], y=['Nova Lite', 'Nova Pro'], orientation='h', 
                               marker_color=[accent if is_lite else muted, muted if is_lite else accent]))
        fig.update_layout(title="Latency (sec)", height=280, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#888"))
        st.plotly_chart(fig, use_container_width=True)

if st.session_state.last_result:
    create_dashboards(st.session_state.last_result['model'])

# --- ROUTING HISTORY ---
st.subheader("Routing History")
with st.expander("View Past Prompts"):
    for entry in reversed(st.session_state.history):
        st.markdown(f"**Prompt:** {entry['prompt']}  \n↳ *Model: `{entry['model']}`*")

# --- INPUT AREA ---
st.subheader("Test the Router")
uploaded_file = st.file_uploader("Attach Context", type=["png", "jpg", "jpeg"])

if prompt := st.chat_input("Enter your prompt..."):
    image_path = None
    if uploaded_file:
        image_path = f"temp_{uploaded_file.name}"
        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    with st.spinner("Routing..."):
        try:
            # 2. RUN: This triggers your updated main.py return logic
            result = run_green_route(prompt, image_path)
            
            st.session_state.last_result = result
            st.session_state.history.append({"prompt": prompt, "model": result['model']})
            
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- DISPLAY AI RESPONSE ---
if st.session_state.last_result:
    res = st.session_state.last_result
    st.markdown(f"### 🤖 Response from `{res['model']}`")
    st.markdown(f'<div class="response-container">{res["response"]}</div>', unsafe_allow_html=True)
    if res['carbon_saved'] > 0:
        st.toast(f"🌱 Carbon Saved: {res['carbon_saved']}mg", icon="✅")
