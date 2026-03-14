import streamlit as st
import plotly.graph_objects as go
import random
import time

# Attempt to import your custom router
try:
    from router import GreenRouter
except ImportError:
    st.error("Please ensure 'router.py' is in the same directory.")
    GreenRouter = None

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GreenRouting Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR DYNAMIC THEMING ---
st.markdown("""
    <style>
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    /* Style the metrics for a cleaner look */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
    }
    /* Outline and Shadow for the Chat Input Box */
        div[data-testid="stChatInput"] {
            border: 2px solid #26A998 !important; /* Your Vibrant Teal outline */
            box-shadow: 0px 6px 15px rgba(35, 44, 82, 0.15) !important; /* Soft Navy drop shadow */
            border-radius: 12px !important; /* Smooth rounded corners */
            transition: all 0.3s ease-in-out; /* Makes the hover effect smooth */
        }

        /* Adds a subtle "glow" when the user clicks inside to type */
        div[data-testid="stChatInput"]:focus-within {
            box-shadow: 0px 8px 20px rgba(38, 169, 152, 0.25) !important; /* Teal shadow */
            border-color: #478560 !important; /* Shifts to your Forest Green */
        }
    </style>
""", unsafe_allow_html=True)

# --- MOCK API FOR CARBON INTENSITY ---
def get_current_carbon_intensity():
    """Mocks fetching data from carbon_api.py"""
    # Returns a random value between 10 (Very Green) and 95 (Very Dirty)
    return random.randint(10, 95)

# --- INITIALIZE STATE ---
if 'carbon_intensity' not in st.session_state:
    st.session_state.carbon_intensity = 0
if 'router' not in st.session_state and GreenRouter:
    # Initialize your class here. (Assuming mock AWS credentials for the UI build)
    st.session_state.router = GreenRouter() 
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_route' not in st.session_state:
    st.session_state.last_route = {"model": "None", "reason": "Awaiting input..."}

# --- HEADER & GREEN STATUS ---
col_head1, col_head2 = st.columns([3, 1]) # split the top of your screen into two invisible columns. The left column gets 75% of the space (for the title), and the right gets 25% (for the status box).
with col_head1:
    st.markdown("""
        <h1 style='
            font-size: 3.5rem; 
            font-weight: 800; 
            background: -webkit-linear-gradient(45deg, #2A9D8F, #3EB489); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            margin-bottom: 0px;
            padding-bottom: 0px;'>
            GreenRouting Intelligence
        </h1>
    """, unsafe_allow_html=True)


with col_head2:
    # Status Indicator Logic
    intensity = st.session_state.carbon_intensity
    if intensity == 0:
        status_color = "#6B7280"
        status_text = "Standby (Awaiting Input)"
    elif intensity < 40:
        status_color = "#2A9D8F" # Eco Green
        status_text = "Optimal (Clean Grid)"
    elif intensity < 80:
        status_color = "#E9A53C" # Moderate Yellow
        status_text = "Moderate"
    else:
        status_color = "#E76F51"
        status_text = "Alert (Dirty Grid)"
        
    st.markdown(f"""
        <div style="padding: 15px; border-radius: 12px; background-color: var(--secondary-background-color); text-align: center; border: 1px solid var(--faded-text-color);">
            <p style="margin: 0; font-size: 20px; color: var(--faded-text-color);">Current Grid Carbon</p>
            <h2 style="margin: 0; color: {status_color};">{intensity} gCO₂/kWh</h2>
            <p style="margin: 0; font-size: 0.8rem; font-weight: 600; color: var(--text-color);">{status_text}</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# --- PLOTLY DASHBOARD VISUALS ---
def create_dashboards(selected_model):
    col1, col2, col3 = st.columns(3)
    
    is_lite = "lite" in selected_model.lower()
    
    # Modern green/teal palette
    accent_color = '#2A9D8F'   # Teal primary
    secondary_color = '#264653'  # Inky blue‑green for contrast
    soft_green = '#A4C3B2'     # Soft desaturated green for subtle areas
    bg_fill = 'rgba(0,0,0,0)'
    
    lite_bar = accent_color if is_lite else secondary_color
    pro_bar = secondary_color if is_lite else accent_color
    
    with col1:
        # --- COST EFFICIENCY ---
        fig_cost = go.Figure(data=[
            go.Bar(x=['Nova Lite', 'Nova Pro'], y=[0.06, 0.90], 
                   marker_color=[lite_bar, pro_bar], width=0.5)
        ])
        fig_cost.update_layout(
            title=dict(text="Cost Efficiency ($)", x=0.5, xanchor='center', font=dict(color=secondary_color, size=20)),
            margin=dict(l=20, r=20, t=60, b=40),
            height=280,
            paper_bgcolor=bg_fill,
            plot_bgcolor=bg_fill,
            yaxis=dict(range=[0, 1], showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            xaxis=dict(tickfont=dict(color=secondary_color)),
            showlegend=False
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    with col2:
        # --- CO2 SAVED (GAUGE) ---
        saved_co2 = random.randint(120, 300) if is_lite else 0
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = saved_co2,
            number = {'font': {'color': secondary_color, 'size': 50}},
            gauge = {
                'axis': {'range': [None, 500], 'tickfont': {'color': secondary_color, 'size': 10}},
                'bar': {'color': accent_color},
                'bgcolor': "#E2E8F0",
                'borderwidth': 0,
            }
        ))
        fig_gauge.update_layout(
            title=dict(text="Estimated CO₂ Saved (mg)", x=0.5, xanchor='center', font=dict(color=secondary_color, size=20)),
            margin=dict(l=20, r=20, t=60, b=10), # Lower bottom margin to lift the gauge up
            height=280,
            paper_bgcolor=bg_fill
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col3:
        # --- LATENCY (HORIZONTAL BAR) ---
        fig_speed = go.Figure(go.Bar(
            x=[0.4, 1.8],
            y=['Nova Lite', 'Nova Pro'],
            orientation='h',
            marker_color=[lite_bar, pro_bar],
            width=0.5
        ))
        fig_speed.update_layout(
            title=dict(text="Latency / Reasoning Depth (sec)", x=0.5, xanchor='center', font=dict(color=secondary_color, size=20)),
            margin=dict(l=80, r=20, t=60, b=40), # Added left margin for the text labels
            height=280,
            paper_bgcolor=bg_fill,
            plot_bgcolor=bg_fill,
            xaxis=dict(range=[0, 2], title="Seconds", title_font=dict(size=12), tickfont=dict(color=secondary_color)),
            yaxis=dict(tickfont=dict(color=secondary_color))
        )
        st.plotly_chart(fig_speed, use_container_width=True)

# Render dashboards based on the last routing decision
create_dashboards(st.session_state.last_route["model"])

st.divider()
# --- ROUTING HISTORY LOG ---

st.subheader("Routing History")

# We use an expander so it doesn't clutter the clean UI
with st.expander("View Past Prompts", expanded=False):
    if len(st.session_state.history) == 0:
        st.caption("No history yet. Send a prompt to get started!")
    else:
        # Loop through the history backwards so the newest is at the top
        for entry in reversed(st.session_state.history):
            st.markdown(f"**Prompt:** {entry['prompt']}")
            st.markdown(f"↳ *Model: `{entry['model']}` | Reason: {entry['reason']}*")
            st.divider() # Adds a light gray line between entries

# --- INPUT AREA (MULTIMODAL) ---
st.subheader("Test the Router")

# 1) Attach file ABOVE the chat box
uploaded_file = st.file_uploader(
    "Attach context (Images, Documents)",
    type=["png", "jpg", "pdf", "txt", "docx","json"]
)
if uploaded_file:
    st.success(f"Attached: {uploaded_file.name} (Ready for Multimodal Routing)")

# 2) Chat Input stays below uploader
if prompt := st.chat_input("Enter your prompt to see how GreenRouting dispatches it..."):
    st.session_state.carbon_intensity = get_current_carbon_intensity()
    with st.spinner("Analyzing semantic intent & grid health..."):
        time.sleep(0.5)
        if st.session_state.router:
            try:
                model, reason = st.session_state.router.route_request(
                    prompt,
                    st.session_state.carbon_intensity
                )
            except Exception as e:
                model, reason = "Error", f"Could not route: {e}"
        else:
            model = "us.amazon.nova-lite-v1:0" if len(prompt) < 50 else "us.amazon.nova-pro-v1:0"
            reason = "Mock routing (router.py not found)"

        st.session_state.last_route = {"model": model, "reason": reason}
        st.session_state.history.append({"prompt": prompt, "model": model, "reason": reason})
        st.rerun()

# --- ROUTING RESULTS ---
if st.session_state.last_route["model"] != "None":
    st.info(f"**Selected Model:** `{st.session_state.last_route['model']}`\n\n**Router Reasoning:** {st.session_state.last_route['reason']}")

