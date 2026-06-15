# -*- coding: utf-8 -*-
"""
Created on Mon May 11 17:13:57 2026

@author: Admin
"""


import streamlit as st
import pickle
import numpy as np
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_option_menu import option_menu
from geopy.geocoders import Nominatim
from fpdf import FPDF
from google import genai

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)
# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="MediPredict", layout="wide")


# css

st.markdown("""
<style>

/* Main app background */
.main {
    background-color: #f8fafc;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #1e3a8a;
}

/* Sidebar text */
section[data-testid="stSidebar"] * {
    color: white;
}

/* Titles */
.title {
    color: #1e3a8a;
    font-weight: bold;
}

/* HERO SECTION */
.hero-section {
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
    padding: 45px;
    border-radius: 20px;
    text-align: center;
    color: white;
    margin-bottom: 30px;
}

/* Hero Title */
.hero-title {
    font-size: 55px;
    font-weight: bold;
    margin-bottom: 10px;
}

/* Hero Subtitle */
.hero-subtitle {
    font-size: 22px;
    opacity: 0.9;
}

/* Feature Cards */
.info-card {
    background-color: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    text-align: center;
    height: 200px;
}

/* Stats Cards */
.stat-card {
    background-color: #eff6ff;
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    border-left: 5px solid #3b82f6;
}

.stat-card h2 {
    font-size: 40px;
    color: #1e3a8a;
}

.stat-card p {
    color: #475569;
    font-size: 18px;
}

/* LOGIN PAGE CARD */
.card {
    background: white;
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    border-left: 5px solid #3b82f6;
    margin-bottom: 25px;
}

/* INPUT FIELDS */
.stTextInput input{
    border-radius:12px;
    border:2px solid #dbeafe;
    padding:12px;
    background:#f8fafc;
}

/* BUTTONS */
.stButton>button{
    background:linear-gradient(90deg,#1e3a8a,#3b82f6);
    color:white;
    border:none;
    border-radius:12px;
    height:3em;
    font-size:18px;
    font-weight:bold;
    transition:0.3s;
}

/* BUTTON HOVER */
.stButton>button:hover{
    transform:scale(1.02);
    background:linear-gradient(90deg,#2563eb,#60a5fa);
    color:white;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE
# =====================================================

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    '''
)

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        disease TEXT,
        result TEXT,
        date TEXT
    )
    '''
)

conn.commit()

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS appointments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        patient_name TEXT,

        doctor TEXT,

        appointment_date TEXT,

        appointment_time TEXT
    )
    '''
)

conn.commit()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS doctors (

        name TEXT
    )
    """
)

conn.commit()

appointment_doctors = pd.read_sql_query(
    """
    SELECT * FROM doctors
    WHERE TRIM(name) != ''
    """,
    conn
)
cursor.execute(
    "SELECT * FROM doctors"
)

existing_doctors = cursor.fetchall()

if len(existing_doctors) == 0:

    default_doctors = [
        ("Dr Raj Sharma",),
        ("Dr Priya Nair",),
        ("Dr Arun Kumar",),
        ("Dr Meera Joshi",),
        ("Dr Kavya Reddy",)
    ]

    cursor.executemany(
        """
        INSERT INTO doctors (name)
        VALUES (?)
        """,

        default_doctors
    )

    conn.commit()

appointment_doctors = pd.read_sql_query(
    """
    SELECT * FROM doctors
    WHERE TRIM(name) != ''
    """,
    conn
)

# =====================================================
# PASSWORD HASHING
# =====================================================


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =====================================================
# SESSION
# =====================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


# ===================================================== 
# AUTH FUNCTIONS
# =====================================================

def register_user(username, password):

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )

        conn.commit()
        return True

    except:
        return False


def login_user(username, password):

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )

    return cursor.fetchone()
def auth_page():
    
    # CUSTOM CSS
    st.markdown("""
    <style>
    .stButton > button {
        height: 45px;
        font-size: 16px;
        border-radius: 10px;
    }

    .stTextInput input {
        height: 45px;
    }
    </style>
    """, unsafe_allow_html=True)

    # HEADER
    st.markdown("""
    <div style='
        background: linear-gradient(90deg,#1e3a8a,#3b82f6);
        padding:12px;
        border-radius:14px;
        text-align:center;
        color:white;
        margin-bottom:20px;
        width:45%;
        margin-left:auto;
        margin-right:auto;
        box-shadow:0 4px 12px rgba(0,0,0,0.12);
    '>
    
    <h1 style='
        font-size:26px;
        margin-bottom:5px;
        color:white;
    '>
    ☤ MediPredict
    </h1>
    
    <p style='
        font-size:14px;
        margin:0;
        color:white;
    '>
    AI Powered Multiple Disease Prediction System
    </p>
    
    </div>
    """, unsafe_allow_html=True)
    
    

    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # =====================================================
    # LOGIN
    # =====================================================
    with tab1:
        
            st.markdown("""
            <h1 style="
                text-align:center;
                color:#1e3a8a;
                font-size:42px;
                margin-top:10px;
                margin-bottom:0px;
            ">
                Welcome Back
            </h1>
            
            <p style="
                text-align:center;
                color:gray;
                font-size:18px;
                margin-bottom:30px;
            ">
                Login to continue
            </p>
            """, unsafe_allow_html=True)
        
            col1, col2, col3 = st.columns([1.5,2,1.5])
        
            with col2:
        
                username = st.text_input("👤 Username")
                password = st.text_input("🔒 Password", type="password")
        
                if st.button("Login", use_container_width=True):
        
                    user = login_user(username, password)
        
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("Login Successful")
                        st.rerun()
        
                    else:
                        st.error("Invalid Username or Password")
    # =====================================================
    # REGISTER
    # =====================================================
    with tab2:
    
        col1, col2, col3 = st.columns([1.5,2,1.5])
    
        with col2:

            st.markdown("""
            <h1 style='
                text-align:center;
                color:#1e3a8a;
                font-size:42px;
                margin-top:10px;
                margin-bottom:0px;
            '>
            Create Account
            </h1>
            
            <p style='
                text-align:center;
                color:gray;
                font-size:18px;
                margin-bottom:30px;
            '>
            Register to get started
            </p>
            """, unsafe_allow_html=True)

            new_user = st.text_input("👤 Create Username")
        
            new_password = st.text_input(
                "🔒 Create Password",
                type="password"
            )
    
    
            st.markdown("<br>", unsafe_allow_html=True)
    
            if st.button("Register", use_container_width=True):
    
                if new_user == "" or new_password == "":
                    st.warning("Please fill all fields")
    
                else:
                    success = register_user(new_user, new_password)
    
                    if success:
                        st.success("Account Created Successfully")
    
                    else:
                        st.error("Username already exists")
# =====================================================
# SHOW LOGIN PAGE FIRST
# =====================================================

if not st.session_state.logged_in:
    auth_page()
    st.stop()  
    
st.title("Multiple Disease Prediction System")
# =====================================================
# LOAD MODELS
# =====================================================

@st.cache_resource

def load_models():

    diabetes_model = pickle.load(open("saved_model/diabetes_model.sav","rb"))
    diabetes_scaler = pickle.load(open("saved_model/diabetes_scaler.sav","rb"))
    
    heart_model = pickle.load(open("saved_model/heart_model.sav","rb"))
    heart_scaler = pickle.load(open("saved_model/heart_scaler.sav","rb"))

    parkinsons_model = pickle.load(open("saved_model/parkinsons_model.sav","rb"))
    parkinsons_scaler = pickle.load(open("saved_model/parkinsons_scaler.sav","rb"))
    

    return (
        diabetes_model,
        diabetes_scaler,
        heart_model,
        heart_scaler,
        parkinsons_model,
        parkinsons_scaler
    )

(
    diabetes_model,
    diabetes_scaler,
    heart_model,
    heart_scaler,
    parkinsons_model,
    parkinsons_scaler
) = load_models()

# load doctor database
doctor_df = pd.read_csv("doctors.csv")
def show_doctors(specialization):

    st.subheader("👨‍⚕ Recommended Doctors")

    filtered_doctors = doctor_df[
        doctor_df["specialization"] == specialization
    ]

    if filtered_doctors.empty:
        st.warning("No doctors found")
    else:
        for index, row in filtered_doctors.iterrows():

            st.markdown(f"""
            ### 🩺 {row['name']}

            🏥 Hospital: {row['hospital']}

            ⭐ Rating: {row['rating']}

            📍 City: {row['city']}

            💼 Experience: {row['experience']}
            """)



def show_hospitals(query):

    try:
        geolocator = Nominatim(
            user_agent="multiple_disease_prediction_app"
        )

        locations = geolocator.geocode(
            query,
            exactly_one=False,
            limit=5
        )

        if not locations:
            st.warning("No hospitals found")
            return

        st.subheader("Nearby Hospitals")

        for place in locations:

            st.success(place.address)
        
            maps_url = f"https://www.google.com/maps?q={place.latitude},{place.longitude}"
        
            st.markdown(f"[📍 Open in Google Maps]({maps_url})")
        
            st.write("---")

    except Exception as e:
        st.error(f"Error: {e}")
        

def generate_pdf_report(disease, result,risk, specialist):
    pdf = FPDF()

    pdf.add_page()
    
    pdf.set_font("Arial", "B", 18)
    pdf.cell(190, 10, "MEDIPREDICT", ln=True, align="C")
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, "AI Powered Disease Prediction System", ln=True, align="C")
    
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "Medical Prediction Report", ln=True)
    
    pdf.ln(3)
    
    pdf.set_font("Arial", "", 12)
    
    pdf.cell(190, 8, f"Username : {st.session_state.username}", ln=True)
    pdf.cell(190, 8, f"Disease : {disease}", ln=True)
    pdf.cell(190, 8, f"Prediction Result : {result}", ln=True)
    pdf.cell(190, 8, f"Risk Score : {risk}%", ln=True)
    pdf.cell(190, 8, f"Recommended Specialist : {specialist}", ln=True)
    
    pdf.ln(5)
    
    pdf.cell(190, 8, f"Generated On : {datetime.now().strftime('%d-%m-%Y %I:%M %p')}", ln=True)

    pdf.ln(3)
    
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    
    pdf.ln(2)
    
    pdf.cell(190, 8, "Generated by MediPredict", ln=True, align="C")
    
    pdf.output("report.pdf")
       
        
   
def save_appointment(
    patient_name,
    doctor,
    appointment_date,
    appointment_time
):

    cursor.execute(
        """
        INSERT INTO appointments
        (
            username,
            patient_name,
            doctor,
            appointment_date,
            appointment_time
        )

        VALUES (?, ?, ?, ?, ?)
        """,

        (
            st.session_state.username,
            patient_name,
            doctor,
            str(appointment_date),
            appointment_time
        )
    )

    conn.commit()   
    
# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    
    st.success(f"Logged in as {st.session_state.username}")
    
    menu_options = [
        "Home",
        "Diabetes Prediction",
        "Heart Disease Prediction",
        "Parkinsons Prediction",
        "Appointment Booking",
        "My Appointments",
        "Prediction History",
        "AI Health Assistant"
    ]
    
    if st.session_state.username == "admin":
        menu_options.append("Admin Panel")
        
    selected = option_menu(
    "MediPredict",
    menu_options,
    icons=[
        'house',
        'activity',
        'heart',
        'person',
        'calendar-check',
        'calendar2-check',
        'clock-history',
        'robot'
    ],
    default_index=0,

    styles={
        "container": {
            "padding": "5!important",
            "background-color": "#ffffff"
        },

        "icon": {
            "color": "#1e293b",
            "font-size": "18px"
        },

        "nav-link": {
            "font-size": "18px",
            "text-align": "left",
            "margin": "5px",
            "color": "#1e293b",
            "--hover-color": "#e5e7eb",
        },

        "nav-link-selected": {
            "background-color": "#9ca3af",
            "color": "white",
        },
    }
)
# Logout Button
    st.markdown("<br><br>", unsafe_allow_html=True)

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()   


# =========================================================
# HOME PAGE
# =========================================================

if selected == "Home":

    # HERO SECTION
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">
    <span style="color:white; font-size:65px;">⚕</span> MediPredict
</h1>
        <p class="hero-subtitle">
              Predict.  Prevent.  Stay Healthy
        </p>
    </div>
    """, unsafe_allow_html=True)

    # FEATURE CARDS
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h3>Diabetes</h3>
            <p>Predict diabetes risk using intelligent AI analysis.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h3>Heart Disease</h3>
            <p>Analyze heart health and cardiovascular risks.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-card">
            <h3>Parkinson's</h3>
            <p>Early Parkinson's detection using machine learning.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # STATS SECTION
    s1, s2, s3 = st.columns(3)

    with s1:
        st.markdown("""
        <div class="stat-card">
            <h2>3+</h2>
            <p>Diseases Supported</p>
        </div>
        """, unsafe_allow_html=True)

    with s2:
        st.markdown("""
        <div class="stat-card">
            <h2>95%</h2>
            <p>Prediction Accuracy</p>
        </div>
        """, unsafe_allow_html=True)

    with s3:
        st.markdown("""
        <div class="stat-card">
            <h2>24/7</h2>
            <p>System Status</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    

# =====================================================
# SAVE HISTORY
# =====================================================


def save_history(disease, result):

    cursor.execute(
        "INSERT INTO history (username, disease, result, date) VALUES (?, ?, ?, ?)",
        (
            st.session_state.username,
            disease,
            result,
            str(datetime.now())
        )
    )

    conn.commit()

# =====================================================
# DIABETES
# =====================================================

if selected == 'Diabetes Prediction':

    st.header('Diabetes Prediction')

    col1, col2 = st.columns(2)

    with col1:
        pregnancies = st.number_input('Pregnancies', min_value=0.0)
        glucose = st.number_input('Glucose Level')
        bloodpressure = st.number_input('Blood Pressure')
        skinthickness = st.number_input('Skin Thickness')

    with col2:
        insulin = st.number_input('Insulin Level')
        bmi = st.number_input('BMI Value')
        diabetespedigreefunction = st.number_input('Diabetes Pedigree Function')
        age = st.number_input('Age')
        
    if st.button('Predict Diabetes'):
        if (pregnancies == 0 and glucose == 0 and bloodpressure == 0 and
        skinthickness == 0 and insulin == 0 and bmi == 0 and
        diabetespedigreefunction == 0 and age == 0):

            st.warning("Please enter patient details first")

        else:
            input_data = np.array([[pregnancies, glucose, bloodpressure,
                                    skinthickness, insulin, bmi,
                                    diabetespedigreefunction, age]])
    
            input_data = diabetes_scaler.transform(input_data)
    
            prediction = diabetes_model.predict(input_data)
            probability = diabetes_model.predict_proba(input_data)
    
            risk = round(probability[0][1] * 100, 2)
            
            st.progress(int(risk))
            st.info(f"Diabetes Risk Score: {risk}%")
    
            if prediction[0] == 1:
                result = "High Risk of Diabetes"
                st.error(result)
            
                show_doctors("Endocrinologist")
            
                show_hospitals("diabetes hospitals in Bangalore")
            
            else:
            
                result = "Low Risk of Diabetes"
            
                st.success(result)
                
            save_history("Diabetes", result)
            
            generate_pdf_report("Diabetes",result, risk,"Endocrinologist")
                    
            with open("report.pdf", "rb") as file:
                    
                st.download_button(
                            label="📄 Download Report",
                            data=file,
                            file_name="Diabetes_Report.pdf",
                            mime="application/pdf"
                )
                
            chart = pd.DataFrame({
                'Category': ['Risk', 'Safe'],
                'Value': [risk, 100-risk]
            })
    
            fig = px.pie(chart, names='Category', values='Value', title='Diabetes Risk Analysis')
            st.plotly_chart(fig, width= 'stretch')
            

# =====================================================
# HEART DISEASE
# =====================================================
elif selected == 'Heart Disease Prediction':

    st.header('Heart Disease Prediction')

    col1, col2, col3 = st.columns(3)

    with col1:
        age = st.number_input('Age')
        trestbps = st.number_input('Resting Blood Pressure')
        restecg = st.number_input('Resting ECG')
        oldpeak = st.number_input('Oldpeak')
        thal = st.number_input('Thal')

    with col2:
        sex = st.number_input('Sex')
        chol = st.number_input('Serum Cholesterol')
        thalach = st.number_input('Maximum Heart Rate')
        slope = st.number_input('Slope')

    with col3:
        cp = st.number_input('Chest Pain Type')
        fbs = st.number_input('Fasting Blood Sugar')
        exang = st.number_input('Exercise Induced Angina')
        ca = st.number_input('Major Vessels')

    st.markdown("<br>", unsafe_allow_html=True)
    

    if st.button('Predict Heart Disease'):
        
        if (age == 0 and sex == 0 and cp == 0 and trestbps == 0 and
            chol == 0 and fbs == 0 and restecg == 0 and
            thalach == 0 and exang == 0 and oldpeak == 0 and
            slope == 0 and ca == 0 and thal == 0):
    
            st.warning("Please enter patient details first")

        else:


            input_data = np.array([[age, sex, cp, trestbps,
                                    chol, fbs, restecg,
                                    thalach, exang, oldpeak,
                                    slope, ca, thal]])
    
            input_data = heart_scaler.transform(input_data)
    
            prediction = heart_model.predict(input_data)
            probability = heart_model.predict_proba(input_data)
    
            risk = round(probability[0][1] * 100, 2)
    
            st.progress(int(risk))
            st.info(f"Heart Disease Risk Score: {risk}%")
    
            if prediction[0] == 1:
                result = 'High Risk of Heart Disease'
                st.error(result)
                
                show_doctors("Cardiologist")
                
                show_hospitals("heart hospitals in Bangalore")
               
            else:
                result = 'Low Risk of Heart Disease'
                st.success(result)
    
            save_history("Heart Disease", result)
            
            generate_pdf_report("Heart Disease", result, risk, "Cardiologist")

            with open("report.pdf", "rb") as file:
            
                st.download_button(
                    label="📄 Download Heart Report",
                    data=file,
                    file_name="Heart_Disease_Report.pdf",
                    mime="application/pdf"
                )
            
            chart = pd.DataFrame({
                'Category': ['Risk', 'Safe'],
                'Value': [risk, 100-risk]
            })
    
            fig = px.pie(
                chart,
                names='Category',
                values='Value',
                title='Heart Disease Risk Analysis'
            )
    
            st.plotly_chart(fig, width='stretch')
            
# =====================================================
# PARKINSONS
# =====================================================

elif selected == 'Parkinsons Prediction':

    st.header("Parkinson's Prediction")

    col1, col2, col3 = st.columns(3)

    with col1:
        fo = st.number_input('MDVP:Fo(Hz)')
        fhi = st.number_input('MDVP:Fhi(Hz)')
        flo = st.number_input('MDVP:Flo(Hz)')
        jitter_percent = st.number_input('MDVP:Jitter(%)')
        jitter_abs = st.number_input('MDVP:Jitter(Abs)')
        rap = st.number_input('MDVP:RAP')
        ppq = st.number_input('MDVP:PPQ')
        ddp = st.number_input('Jitter:DDP')

    with col2:
        shimmer = st.number_input('MDVP:Shimmer')
        shimmer_db = st.number_input('MDVP:Shimmer(dB)')
        apq3 = st.number_input('Shimmer:APQ3')
        apq5 = st.number_input('Shimmer:APQ5')
        apq = st.number_input('MDVP:APQ')
        dda = st.number_input('Shimmer:DDA')
        nhr = st.number_input('NHR')
        hnr = st.number_input('HNR')

    with col3:
        rpde = st.number_input('RPDE')
        dfa = st.number_input('DFA')
        spread1 = st.number_input('spread1')
        spread2 = st.number_input('spread2')
        d2 = st.number_input('D2')
        ppe = st.number_input('PPE')
        

    if st.button('Predict Parkinsons Disease'):
        
        if all(v == 0 for v in [
            fo, fhi, flo, jitter_percent, jitter_abs,
            rap, ppq, ddp, shimmer, shimmer_db,
            apq3, apq5, apq, dda, nhr, hnr,
            rpde, dfa, spread1, spread2, d2, ppe
        ]):
            st.warning("Please enter patient details first")
        else:
            input_data = np.array([[fo, fhi, flo,
                                    jitter_percent, jitter_abs,
                                    rap, ppq, ddp,
                                    shimmer, shimmer_db, apq3,
                                    apq5, apq, dda,
                                    nhr, hnr, rpde,
                                    dfa, spread1, spread2,
                                    d2, ppe]])
    
            input_data = parkinsons_scaler.transform(input_data)
    
            prediction = parkinsons_model.predict(input_data)

            probability = parkinsons_model.predict_proba(input_data)
    
            risk = round(probability[0][1] * 100, 2)
    
            st.progress(int(risk))
            st.info(f"Parkinson's Risk Score: {risk}%")
    
            if prediction[0] == 1:
                result = 'High Risk of Parkinsons Disease'
                st.error(result)
                
                show_doctors("Neurologist")
                
                show_hospitals("neurology hospitals in Bangalore")
                                
            else:
                result = 'Low Risk of Parkinsons Disease'
                st.success(result)
    
            save_history("Parkinsons", result)
            
            generate_pdf_report("Parkinsons",result, risk, "Neurologist")

            with open("report.pdf", "rb") as file:
            
                st.download_button(
                    label="📄 Download Parkinsons Report",
                    data=file,
                    file_name="Parkinsons_Report.pdf",
                    mime="application/pdf"
                )
                
                
            chart = pd.DataFrame({
                'Category': ['Risk', 'Safe'],
                'Value': [risk, 100-risk]
            })
            
            fig = px.pie(
                chart,
                names='Category',
                values='Value',
                title='Predict Parkinsons Disease'
            )
            
            st.plotly_chart(fig, width='stretch')
            
# =====================================================
# APPOINTMENT BOOKING
# =====================================================

elif selected == "Appointment Booking":

    st.title("📅 Appointment Booking")

    doctor = st.selectbox(
        "Select Doctor",
        appointment_doctors['name']
    )
    
    appointment_date = st.date_input(
        "Select Appointment Date"
    )

    all_slots = [
        "10:00 AM",
        "11:00 AM",
        "12:00 PM",
        "2:00 PM",
        "4:00 PM"
    ]
    
    booked_slots = pd.read_sql_query(
        """
        SELECT appointment_time
        FROM appointments
    
        WHERE doctor=?
        AND appointment_date=?
        """,
    
        conn,
    
        params=(
            doctor,
            str(appointment_date)
        )
    )
    
    booked_slots_list = booked_slots[
        'appointment_time'
    ].tolist()
    
    available_slots = [
        slot for slot in all_slots
        if slot not in booked_slots_list
    ]
    
    appointment_time = st.selectbox(
        "Select Appointment Time",
        available_slots
    )

    patient_name = st.text_input(
        "Enter Patient Name"
    )

    if st.button("Book Appointment"):

        existing = pd.read_sql_query(
            """
            SELECT * FROM appointments
        
            WHERE doctor=?
            AND appointment_date=?
            AND appointment_time=?
            """,
        
            conn,
        
            params=(
                doctor,
                str(appointment_date),
                appointment_time
            )
        )
        daily_count = pd.read_sql_query(
            """
            SELECT * FROM appointments
        
            WHERE doctor=?
            AND appointment_date=?
            """,
        
            conn,
        
            params=(
                doctor,
                str(appointment_date)
            )
        )
        if len(daily_count) >= 5:

            st.error(
                "Doctor Fully Booked For This Date"
            )
            
        elif existing.empty:
        
            save_appointment(
                patient_name,
                doctor,
                appointment_date,
                appointment_time
            )
        
            st.success(f"""
    ✅ Appointment Booked Successfully
        
    👤 Patient: {patient_name}
        
    👨‍⚕️ Doctor: {doctor}
        
    📅 Date: {appointment_date}
        
    ⏰ Time: {appointment_time}
    """)
        
        else:
        
            st.error(
                "This time slot is already booked"
            )
# =====================================================
# MY APPOINTMENTS
# =====================================================

elif selected == "My Appointments":

    st.title("📅 My Appointments")

    appointment_df = pd.read_sql_query(
        """
        SELECT

        patient_name,
        doctor,
        appointment_date,
        appointment_time

        FROM appointments

        WHERE username=?
        """,

        conn,

        params=(st.session_state.username,)
    )

    if appointment_df.empty:

        st.warning("No appointments found")

    else:

        st.dataframe(
            appointment_df,
            width='stretch'
        ) 
        
        for index, row in appointment_df.iterrows():
        
            if st.button(
                f"Cancel Appointment {index}"
            ):
        
                cursor.execute(
                    """
                    DELETE FROM appointments
        
                    WHERE patient_name=?
                    AND doctor=?
                    AND appointment_date=?
                    AND appointment_time=?
                    """,
        
                    (
                        row['patient_name'],
                        row['doctor'],
                        row['appointment_date'],
                        row['appointment_time']
                    )
                )
        
                conn.commit()
        
                st.success(
                    "Appointment Cancelled Successfully"
                )
        
                st.rerun()
                
# =====================================================
# ADMIN PANEL
# =====================================================    
elif selected == "Admin Panel":

    if st.session_state.username != "admin":

        st.error("Access Denied")
        st.stop()

    
    st.markdown("""
    <h1 style='color:#1E3A8A;'> Admin Dashboard</h1>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
    
        st.subheader("+Add Doctor")
    
        new_doctor = st.text_input(
            "Enter Doctor Name"
        )
    
        if st.button("Add Doctor"):
            
            if new_doctor.strip() == "":
                st.warning("Please enter doctor name")
    
            else:
                cursor.execute(
                    """
                    INSERT INTO doctors (name)
                    VALUES (?)
                    """,
                    (new_doctor.strip(),)
                )
    
                conn.commit()
                st.success("Doctor Added Successfully")
                st.rerun()

    with col2:
    
        st.subheader("-Remove Doctor")
    
        doctor_to_delete = st.selectbox(
            "Select Doctor To Remove",
            appointment_doctors['name']
        )
    
        if st.button("Delete Doctor"):
    
            cursor.execute(
                """
                DELETE FROM doctors
                WHERE name=?
                """,
                (doctor_to_delete,)
            )
    
            conn.commit()
    
            st.success("Doctor Deleted Successfully")
            st.rerun()
        
    total_appointments = pd.read_sql_query(
            """
            SELECT COUNT(*) as total
            FROM appointments
            """,
        
            conn
        )
        
    total_doctors = pd.read_sql_query(
            """
            SELECT COUNT(*) as total
            FROM doctors
            """,
        
            conn
        )
        
    col1, col2 = st.columns(2)
        
    with col1:
        
            st.metric(
                "Total Appointments",
                total_appointments['total'][0]
            )
        
    with col2:
        
            st.metric(
                "Total Doctors",
                total_doctors['total'][0]
            )
    
    admin_df = pd.read_sql_query(
            """
            SELECT * FROM appointments
            """,
    
            conn
        )
    
    if admin_df.empty:
    
            st.warning(
                "No Appointments Found"
            )
    
    else:
            st.divider()

            st.subheader("Appointment Records")

            st.dataframe(
                admin_df,
                width='stretch'
            )
            doctor_chart = admin_df['doctor'].value_counts().reset_index()
    
            doctor_chart.columns = [
                'Doctor',
                'Bookings'
            ]
            
            fig = px.bar(
                doctor_chart,
                x='Doctor',
                y='Bookings',
                title='Doctor Booking Analytics',
                text='Bookings'
            )
            
            fig.update_traces(
                width=0.2
            )
            fig.update_layout(
                height=400
            )
            st.plotly_chart(
                fig,
                width='stretch'
            )
    
            for index, row in admin_df.iterrows():
    
                if st.button(
                    f"Delete {row['patient_name']} Appointment",
                    key=f"delete_{index}"
                ):
                    
                    cursor.execute(
                        """
                        DELETE FROM appointments
    
                        WHERE patient_name=?
                        AND doctor=?
                        AND appointment_date=?
                        AND appointment_time=?
                        """,
    
                        (
                            row['patient_name'],
                            row['doctor'],
                            row['appointment_date'],
                            row['appointment_time']
                        )
                    )
    
                    conn.commit()
    
                    st.success(
                        "Appointment Deleted"
                    )
    
                    st.rerun()
            

# =====================================================
# HISTORY
# =====================================================

elif selected == "Prediction History":

    st.header("Prediction History")

    query = pd.read_sql_query(
    "SELECT * FROM history WHERE username=?",
    conn,
    params=(st.session_state.username,)
)

    if query.empty:
        st.warning("No prediction history found")

    else:
        st.dataframe(query)
        
# ai assit        
elif selected == "AI Health Assistant":

    st.title("🤖 AI Health Assistant")

    st.info(
        "Ask health-related questions about diseases, symptoms, doctors and healthcare."
    )
    
    st.markdown(
        "<small>This AI assistant provides general health information only and should not replace professional medical advice, diagnosis, or treatment.</small>",
        unsafe_allow_html=True
    )
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "username" not in st.session_state:
       st.session_state.username = st.session_state.get("logged_in_user", "User")

    for i, message in enumerate(st.session_state.messages):

        if message["role"] == "user":

            col1, col2 = st.columns([70,1], vertical_alignment="center")

            with col2:
            
                with st.popover("⋮"):
            
                    if st.button("Delete",key=f"delete_{i}",use_container_width=False):
            
                        if i + 1 < len(st.session_state.messages):
            
                            if st.session_state.messages[i + 1]["role"] == "assistant":
            
                                st.session_state.messages.pop(i + 1)
            
                        st.session_state.messages.pop(i)
            
                        st.rerun()
            
        
            with col1:
                
                st.markdown(
                    f"""
                    <div style="text-align:right;">
                        <small>
                            👤 {st.session_state.username} • {message.get('time','')}
                        </small>
                    </div>
            
                    <div style="
                        background:#2563EB;
                        color:white;
                        padding:14px;
                        border-radius:18px;
                        margin-left:45%;
                        margin-bottom:20px;
                    ">
                        {message["content"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
             
    
        else:
            st.markdown(
                f"""
                <div style="color:#666;">
                🤖 Health Assistant • {message.get('time','')}
                </div>
                """,
                unsafe_allow_html=True
            )
        
            st.markdown(message["content"])
            
    
    st.markdown("##### 💡 Try asking:")

    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("🩺 What is Diabetes?", use_container_width=True):
            st.session_state.suggested_prompt = "What is Diabetes?"
    
        if st.button("🧠 Explain Parkinson's Disease", use_container_width=True):
            st.session_state.suggested_prompt = "Explain Parkinson's Disease"
    
    with c2:
        if st.button("❤️ What are Heart Disease Symptoms?", use_container_width=True):
            st.session_state.suggested_prompt = "What are the symptoms of heart disease?"
    
        if st.button("🥗 What foods should diabetics eat?", use_container_width=True):
            st.session_state.suggested_prompt = "What foods should a diabetic patient eat?"
    
    prompt = st.chat_input("Ask a health question...")
    
    if "suggested_prompt" in st.session_state:
        prompt = st.session_state.suggested_prompt
        del st.session_state.suggested_prompt    

    if prompt:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
                "time": datetime.now().strftime("%I:%M %p")
            }
        )
        
        conversation = ""
        for msg in st.session_state.messages[-10:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation += f"{role}: {msg['content']}\n"
            
        try:
           response = client.models.generate_content(
               model="gemini-2.5-flash",
               contents=f"""
               You are a professional healthcare assistant.
           
               Answer only health-related questions.
           
               If the question is unrelated to healthcare,
               politely refuse.
           
               Continue the conversation naturally and remember previous messages.
           
               Previous Conversation:
               {conversation}
           
               Latest User Question:
               {prompt}
               """
           )
            
           answer = response.text  

        except Exception:
            answer = """
        ⚠️ AI Assistant is temporarily unavailable.
        
        You may have reached the free Gemini API limit.
        Please try again later.
        """

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "time": datetime.now().strftime("%I:%M %p")
            }
        )
        st.rerun()


