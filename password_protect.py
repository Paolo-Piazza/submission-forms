import streamlit as st
import json
import time
from datetime import datetime

# Session timeout (10 minutes)
SESSION_TIMEOUT = 600

# Load user data from an external file (users.json)
def load_users():
    with open("TOM/users.json", "r") as file:
        return json.load(file)

# Function to check if the email and password match
def validate_login(email, password):
    users = load_users()
    for user in users:
        if user["email"] == email and user["password"] == password:
            return True
    return False

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
st.title("Login with Email and Password")

if not st.session_state.authenticated:
    email = st.text_input("Enter your email")
    password = st.text_input("Enter your password", type="password")

    if email and password and st.button("Login"):
        if validate_login(email, password):
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.last_active = time.time()
            log_user_activity(email)
            st.success("Login successful!")
            st.switch_page("pages/compareProteinPanels.py")  # Redirect to the main app
        else:
            st.error("Invalid email or password. Please try again.")

if st.session_state.authenticated:
    st.write(f"Welcome, {st.session_state.user_email}!")

    # Logout button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()


