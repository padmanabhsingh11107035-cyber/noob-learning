import streamlit as st
import hashlib
from config.database import get_db_connection

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def render_auth_view():
    st.subheader("Welcome to Noob Learning")
    
    menu = ["Login", "SignUp"]
    choice = st.selectbox("Choose Action", menu)

    if choice == "Login":
        st.subheader("Login Section")

        username = st.text_input("User Name")
        password = st.text_input("Password", type='password')
        
        if st.button("Login"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()

                if user and check_hashes(password, user['password_hash']):
                    st.success(f"Logged In as {username}")
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['user_id'] = user['user_id']
                    st.rerun()
                else:
                    st.error("Incorrect Username or Password")

    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')

        if st.button("Signup"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    hashed_pwd = make_hashes(new_password)
                    cursor.execute("INSERT INTO users(username, password_hash) VALUES (%s,%s)", (new_user, hashed_pwd))
                    conn.commit()
                    st.success("You have successfully created an account! Go to Login.")
                except Exception as e:
                    st.error(f"Username already exists or error occurred: {e}")
                finally:
                    cursor.close()
                    conn.close()
