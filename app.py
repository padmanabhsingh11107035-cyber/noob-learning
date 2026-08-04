import base64
from datetime import datetime
import os
import pytz
import mysql.connector
from PIL import Image
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Noob Learning Portal", page_icon="🚀", layout="wide"
)

# --- DATABASE CONNECTION CONFIG ---
def get_db_connection():
  return mysql.connector.connect(
      host=st.secrets["mysql"]["host"],
      port=st.secrets["mysql"]["port"],
      user=st.secrets["mysql"]["user"],
      password=st.secrets["mysql"]["password"],
      database=st.secrets["mysql"]["database"],
  )

# --- INITIALIZE DATABASE TABLES ---
def init_db():
  try:
    mydb = get_db_connection()
    mycursor = mydb.cursor()

    mycursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                bio TEXT,
                profile_pic LONGTEXT
            )
        """)

    mycursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                timestamp VARCHAR(100) NOT NULL
            )
        """)

    mycursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender VARCHAR(255) NOT NULL,
                receiver VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                timestamp VARCHAR(100) NOT NULL
            )
        """)

    mydb.commit()
    mycursor.close()
    mydb.close()
  except Exception as e:
    st.error(f"Database Initialization Error: {e}")

init_db()

# --- TIMEZONE CONFIGURATION (IST) ---
IST = pytz.timezone("Asia/Kolkata")

def get_current_time():
  return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "username" not in st.session_state:
  st.session_state.username = ""

# --- CUSTOM CSS STYLING ---
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-text {
        font-size: 1.1rem;
        color: #A0A0A0;
        margin-bottom: 20px;
    }
    .card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #333333;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- AUTHENTICATION & LOGIN UI ---
if not st.session_state.logged_in:
  st.markdown(
      '<p class="main-header">🚀 Noob Learning Portal</p>', unsafe_allow_html=True
  )
  st.markdown(
      '<p class="sub-text">Please log in or register to access your platform'
      " dashboard.</p>",
      unsafe_allow_html=True,
  )

  tab1, tab2 = st.tabs(["🔑 Log In", "📝 Register"])

  with tab1:
    st.subheader("User Login")
    login_user = st.text_input("Username", key="login_username")
    login_pass = st.text_input(
        "Password", type="password", key="login_password"
    )

    if st.button("Log In", key="login_btn"):
      if login_user and login_pass:
        try:
          mydb = get_db_connection()
          mycursor = mydb.cursor(dictionary=True)
          mycursor.execute(
              "SELECT * FROM users WHERE username = %s AND password = %s",
              (login_user, login_pass),
          )
          user = mycursor.fetchone()
          mycursor.close()
          mydb.close()

          if user:
            st.session_state.logged_in = True
            st.session_state.username = login_user
            st.success("Login successful! Redirecting...")
            st.rerun()
          else:
            st.error("Invalid username or password.")
        except Exception as e:
          st.error(f"Database Connection Error: {e}")
      else:
        st.warning("Please fill in all fields.")

  with tab2:
    st.subheader("Create a New Account")
    reg_user = st.text_input("Choose a Username", key="reg_username")
    reg_pass = st.text_input(
        "Choose a Password", type="password", key="reg_password"
    )

    if st.button("Register", key="register_btn"):
      if reg_user and reg_pass:
        try:
          mydb = get_db_connection()
          mycursor = mydb.cursor()
          mycursor.execute(
              "INSERT INTO users (username, password, bio) VALUES (%s, %s,"
              " %s)",
              (reg_user, reg_pass, "Hello! I am new to Noob Learning Portal."),
          )
          mydb.commit()
          mycursor.close()
          mydb.close()
          st.success(
              "Account created successfully! Please switch to the Log In tab."
          )
        except mysql.connector.Error as err:
          st.error(f"Registration Error (Username might already exist): {err}")
      else:
        st.warning("Please fill in all fields.")

else:
  st.sidebar.markdown(f"### Welcome, **{st.session_state.username}**!")
  menu = st.sidebar.selectbox(
      "Navigation",
      [
          "🏠 Home / Feed",
          "👤 Profile & Bio",
          "💬 Direct Messages",
          "📚 Learning Center",
      ],
  )

  if st.sidebar.button("Log Out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

  # --- HOME / ACTIVITY FEED ---
  if menu == "🏠 Home / Feed":
    st.markdown(
        '<p class="main-header">🏠 Community Feed</p>', unsafe_allow_html=True
    )
    st.write("Share your thoughts, robotics notes, or code snippets below!")

    with st.form("post_form", clear_on_submit=True):
      new_post_content = st.text_area("What's on your mind?")
      submitted = st.form_submit_button("Post")
      if submitted and new_post_content.strip():
        try:
          mydb = get_db_connection()
          mycursor = mydb.cursor()
          mycursor.execute(
              "INSERT INTO posts (username, content, timestamp) VALUES (%s,"
              " %s, %s)",
              (
                  st.session_state.username,
                  new_post_content,
                  get_current_time(),
              ),
          )
          mydb.commit()
          mycursor.close()
          mydb.close()
          st.success("Post published successfully!")
          st.rerun()
        except Exception as e:
          st.error(f"Error publishing post: {e}")

    st.divider()
    st.subheader("Recent Activity")

    try:
      mydb = get_db_connection()
      mycursor = mydb.cursor(dictionary=True)
      mycursor.execute("SELECT * FROM posts ORDER BY id DESC")
      posts = mycursor.fetchall()
      mycursor.close()
      mydb.close()

      if posts:
        for p in posts:
          st.markdown(
              f"""
                    <div class="card">
                        <h4>@{p['username']}</h4>
                        <p>{p['content']}</p>
                        <small style="color: #888;">Posted on: {p['timestamp']}</small>
                    </div>
                    """,
              unsafe_allow_html=True,
          )
      else:
        st.info("No posts yet. Be the first to share something!")
    except Exception as e:
      st.error(f"Could not load feed: {e}")

  # --- PROFILE & BIO ---
  elif menu == "👤 Profile & Bio":
    st.markdown(
        '<p class="main-header">👤 User Profile</p>', unsafe_allow_html=True
    )

    try:
      mydb = get_db_connection()
      mycursor = mydb.cursor(dictionary=True)
      mycursor.execute(
          "SELECT * FROM users WHERE username = %s", (st.session_state.username,)
      )
      user_data = mycursor.fetchone()
      mycursor.close()
      mydb.close()

      if user_data:
        col1, col2 = st.columns([1, 2])
        with col1:
          st.image(
              "https://api.dicebear.com/7.x/bottts/svg?seed="
              + st.session_state.username,
              width=150,
          )
        with col2:
          st.subheader(f"@{user_data['username']}")
          current_bio = user_data["bio"] if user_data["bio"] else ""

          new_bio = st.text_area("Edit Your Bio", value=current_bio)
          if st.button("Update Bio"):
            mydb = get_db_connection()
            mycursor = mydb.cursor()
            mycursor.execute(
                "UPDATE users SET bio = %s WHERE username = %s",
                (new_bio, st.session_state.username),
            )
            mydb.commit()
            mycursor.close()
            mydb.close()
            st.success("Bio updated successfully!")
            st.rerun()
    except Exception as e:
      st.error(f"Error loading profile: {e}")

  # --- DIRECT MESSAGES ---
  elif menu == "💬 Direct Messages":
    st.markdown(
        '<p class="main-header">💬 Direct Messages</p>', unsafe_allow_html=True
    )

    try:
      mydb = get_db_connection()
      mycursor = mydb.cursor(dictionary=True)
      mycursor.execute(
          "SELECT username FROM users WHERE username != %s",
          (st.session_state.username,),
      )
      all_users = [row["username"] for row in mycursor.fetchall()]
      mycursor.close()
      mydb.close()

      if all_users:
        selected_recipient = st.selectbox("Select User to Message", all_users)

        with st.form("dm_form", clear_on_submit=True):
          msg_text = st.text_input("Type your message here...")
          send_msg = st.form_submit_button("Send Message")
          if send_msg and msg_text.strip():
            mydb = get_db_connection()
            mycursor = mydb.cursor()
            mycursor.execute(
                "INSERT INTO messages (sender, receiver, message, timestamp)"
                " VALUES (%s, %s, %s, %s)",
                (
                    st.session_state.username,
                    selected_recipient,
                    msg_text,
                    get_current_time(),
                ),
            )
            mydb.commit()
            mycursor.close()
            mydb.close()
            st.success("Message sent!")
            st.rerun()

        st.divider()
        st.subheader(f"Chat History with @{selected_recipient}")

        mydb = get_db_connection()
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute(
            """
                    SELECT * FROM messages 
                    WHERE (sender = %s AND receiver = %s) 
                       OR (sender = %s AND receiver = %s)
                    ORDER BY id ASC
                """,
            (
                st.session_state.username,
                selected_recipient,
                selected_recipient,
                st.session_state.username,
            ),
        )
        messages = mycursor.fetchall()
        mycursor.close()
        mydb.close()

        if messages:
          for m in messages:
            if m["sender"] == st.session_state.username:
              st.markdown(
                  f"<div style='text-align: right; background-color:"
                  f" #2b313e; padding: 10px; border-radius: 8px; margin:"
                  f" 5px;'><b>You:</b> {m['message']}<br><small"
                  f" style='font-size:10px; color:#aaa;'>{m['timestamp']}</small></div>",
                  unsafe_allow_html=True,
              )
            else:
              st.markdown(
                  f"<div style='text-align: left; background-color:"
                  f" #1e2129; padding: 10px; border-radius: 8px; margin:"
                  f" 5px;'><b>@{m['sender']}:</b> {m['message']}<br><small"
                  f" style='font-size:10px; color:#aaa;'>{m['timestamp']}</small></div>",
                  unsafe_allow_html=True,
              )
        else:
          st.info("No messages yet. Start the conversation below!")
      else:
        st.info("No other users registered yet.")
    except Exception as e:
      st.error(f"Error loading messaging system: {e}")

  # --- LEARNING CENTER ---
  elif menu == "📚 Learning Center":
    st.markdown(
        '<p class="main-header">📚 Learning Center</p>', unsafe_allow_html=True
    )
    st.write(
        "Welcome to your study hub! Here you can check your programming and"
        " robotics modules."
    )

    col1, col2 = st.columns(2)
    with col1:
      st.markdown(
          """
                <div class="card">
                    <h3>🐍 Python & Streamlit</h3>
                    <p>Learn how to build interactive web applications, handle session states, and connect databases.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )
    with col2:
      st.markdown(
          """
                <div class="card">
                    <h3>🤖 Robotics & Microcontrollers</h3>
                    <p>Explore projects featuring NodeMCU ESP8266, L298 motor drivers, and automated sensor systems.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )
