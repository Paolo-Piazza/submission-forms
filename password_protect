import streamlit as st
import random
import smtplib
import time
from email.mime.text import MIMEText
from datetime import datetime
import os

# Session timeout (10 minutes)
SESSION_TIMEOUT = 600

# Secure email credentials
if "email" in st.secrets:
    EMAIL_SENDER = st.secrets["email"]["sender"]
    EMAIL_PASSWORD = st.secrets["email"]["password"]
else:
    from dotenv import load_dotenv

    load_dotenv()
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Store OTPs and active sessions
OTP_STORAGE = {}


# Function to send OTP via email
def send_otp(email):
    otp = str(random.randint(100000, 999999))  # Generate 6-digit OTP
    OTP_STORAGE[email] = {"otp": otp, "timestamp": time.time()}  # Store OTP with timestamp

    # Email message
    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Your One-Time Password (OTP)"
    msg["From"] = EMAIL_SENDER
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send OTP: {e}")
        return False


# Function to verify OTP
def verify_otp(email, otp):
    if email in OTP_STORAGE:
        stored_otp = OTP_STORAGE[email]["otp"]
        timestamp = OTP_STORAGE[email]["timestamp"]

        if time.time() - timestamp > 300:  # OTP expires in 5 minutes
            del OTP_STORAGE[email]
            return False, "OTP expired. Request a new one."

        if otp == stored_otp:
            del OTP_STORAGE[email]  # Remove OTP after use
            return True, "Login successful!"

    return False, "Invalid OTP. Try again."


# Function to log user activity
def log_user_activity(email):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("user_log.csv", "a") as f:
        f.write(f"{timestamp}, {email}\n")


# Function to check session timeout
def check_session_timeout():
    if "last_active" in st.session_state:
        if time.time() - st.session_state.last_active > SESSION_TIMEOUT:
            st.session_state.authenticated = False
            st.warning("Session expired due to inactivity. Please log in again.")


# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    check_session_timeout()

# Streamlit UI
st.title("Secure OTP Login")

if not st.session_state.authenticated:
    email = st.text_input("Enter your email")

    if email and st.button("Send OTP"):
        if send_otp(email):
            st.success("OTP sent! Check your email.")

    otp = st.text_input("Enter OTP", type="password")

    if st.button("Verify OTP"):
        success, message = verify_otp(email, otp)
        if success:
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.last_active = time.time()
            log_user_activity(email)
            st.success(message)
        else:
            st.error(message)

if st.session_state.authenticated:
    st.write(f"Welcome, {st.session_state.user_email}!")

    # Logout button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()
