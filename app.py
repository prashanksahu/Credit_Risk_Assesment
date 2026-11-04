import streamlit as st
import requests
import time
import plotly.graph_objects as go

API_URL = "http://127.0.0.1:8000/predict"

st.set_page_config(page_title="Credit Risk AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for styling the verdict text
st.markdown("""
<style>
.verdict-text {font-size: 24px; font-weight: bold;}
.high-risk {color: #ff4b4b;}
.low-risk {color: #00cc96;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
st.sidebar.title("--Applicant Profile--")
#st.sidebar.markdown("Adjust parameters to run the ML pipeline.")

with st.sidebar.expander("👤 Personal Details", expanded=True):
    person_age = st.slider("Age", 18, 80, 25)
    person_income = st.number_input("Annual Income", 0.0, 10000000.0, 50000.0, step=5000.0)
    person_emp_length = st.slider("Employment Length (Years)", 0.0, 40.0, 2.0)
    person_home_ownership = st.selectbox("Home Ownership", ["RENT", "MORTGAGE", "OWN", "OTHER"])

with st.sidebar.expander("💰 Loan Specifics", expanded=True):
    loan_intent = st.selectbox("Loan Intent", ["EDUCATION", "MEDICAL", "VENTURE", "PERSONAL", "DEBTCONSOLIDATION", "HOMEIMPROVEMENT"])
    loan_grade = st.select_slider("Loan Grade", options=["A", "B", "C", "D", "E", "F", "G"])
    loan_amnt = st.number_input("Loan Amount", 0.0, 500000.0, 10000.0, step=1000.0)
    loan_int_rate = st.slider("Interest Rate (%)", 1.0, 25.0, 10.0, step=0.1)

with st.sidebar.expander("💳 Credit History", expanded=True):
    cb_person_cred_hist_length = st.slider("Credit History Length (Years)", 0, 30, 3)
    cb_person_default_on_file = st.radio("Historical Default?", ["N", "Y"], horizontal=True)

analyze_btn = st.sidebar.button("Analyze Applicant", type="primary", use_container_width=True)

# --- MAIN DASHBOARD ---
st.title("Credit Risk Analyzer")
st.markdown("Real-time risk evaluation in few steps")

loan_percent_income = round(loan_amnt / person_income, 2) if person_income > 0 else 0.0

if analyze_btn:
    payload = {
        "person_age": person_age,
        "person_income": person_income,
        "person_home_ownership": person_home_ownership,
        "person_emp_length": person_emp_length,
        "loan_intent": loan_intent,
        "loan_grade": loan_grade,
        "loan_amnt": loan_amnt,
        "loan_int_rate": loan_int_rate,
        "loan_percent_income": loan_percent_income,
        "cb_person_default_on_file": cb_person_default_on_file,
        "cb_person_cred_hist_length": cb_person_cred_hist_length
    }

    # Terminal-style execution animation
    with st.status("Initializing Pipeline...", expanded=True) as status:
        
        try:
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            status.update(label="Assessment Complete", state="complete", expanded=False)
            
            st.divider()
            col1, col2 = st.columns([1, 1.2])
            
            prob = result['default_probability']
            threshold = result['threshold']
            is_high_risk = result['Result'] == "High Risk"
            
            with col1:
                st.subheader("Verdict")
                if is_high_risk:
                    st.markdown("<p class='verdict-text high-risk'>⚠️ HIGH RISK </p>", unsafe_allow_html=True)
                    st.error(f"Default probability is {prob:.1%}, which exceeds the {threshold:.1%} threshold.")
                else:
                    st.markdown("<p class='verdict-text low-risk'>✅ LOW RISK </p>", unsafe_allow_html=True)
                    st.success(f"Profile cleared. Default probability is only {prob:.1%}.")
                    #st.balloons()
                    
                st.metric(label="Calculated Loan-to-Income Ratio", value=f"{loan_percent_income * 100:.1f}%")
            
            with col2:
                # Interactive Plotly Gauge visualizing the decision boundary
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = prob * 100,
                    title = {'text': "Default Probability (%)"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#333333"},
                        'steps': [
                            {'range': [0, threshold * 100], 'color': "#e6ffe6"},
                            {'range': [threshold * 100, 100], 'color': "#ffe6e6"}
                        ],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': threshold * 100}
                    }
                ))
                fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

        except requests.exceptions.ConnectionError:
            status.update(label="API Connection Failed", state="error", expanded=True)
            st.error("Cannot connect to FastAPI. Ensure `uvicorn main:app --reload` is running in your other terminal.")
else:
    # Dashboard empty state
    st.info("👈 Adjust the application parameters in the sidebar and press 'Analyze Applicant'.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Selected Income", f"₹ {person_income:,.0f}")
    col2.metric("Requested Loan", f"₹ {loan_amnt:,.0f}")
    col3.metric("LTI Ratio", f"{loan_percent_income * 100:.1f}%")