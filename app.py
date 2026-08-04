import streamlit as st
import streamlit.components.v1 as components
import mysql.connector
from PIL import Image
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NOOB LEARNING", 
    page_icon="🚀", 
    layout="centered"
)

# --- CHATWAY WIDGET INTEGRATION ---
chatway_code = """
<script id="chatway" async="true" src="https://cdn.chatway.app/widget.js?id=UbvqSsHWYpja"></script>
"""

# Render in the sidebar so it's always loaded
# --- CHATWAY WIDGET INTEGRATION ---
with st.sidebar:
    st.subheader("🤖 Saraah AI Assistant")
    chatway_code = """
    <iframe 
        src="https://chatway.app/widget/UbvqSsHWYpja" 
        width="100%" 
        height="500" 
        style="border:none; border-radius:10px;">
    </iframe>
    """
    components.html(chatway_code, height=520)

# --- AIVEN DATABASE CONFIG ---
DB_CONFIG = {
    "host": "mysql-22faa093-padmanabhsingh11107035-84a9.l.aivencloud.com",
    "port": 21354,
    "user": "avnadmin",
    "password": "AVNS_iN1XY9WAsRFlUWVhM6k",
    "database": "defaultdb"
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        st.error(f"Database Connection Failed: {err}")
        return None

def setup_database():
    """ Ensures all necessary tables exist in Aiven MySQL. """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                profile_pic LONGBLOB DEFAULT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                caption TEXT,
                media_url VARCHAR(1000),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT,
                receiver_id INT,
                message_text TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id)
            );
        """)
        conn.commit()
        conn.close()

# Run database setup on startup
setup_database()

# --- SESSION STATE INITIALIZATION ---
if "user" not in st.session_state:
    st.session_state.user = None

# ================= AUTHENTICATION (LOGIN / SIGNUP) =================
if not st.session_state.user:
    st.title("🚀 NOOB LEARNING")
    st.caption("Learn, Share & Connect")

    tab1, tab2 = st.tabs(["🔒 Log In", "📝 Sign Up"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", use_container_width=True):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
                account = cursor.fetchone()
                conn.close()
                if account:
                    st.session_state.user = account
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Sign Up", use_container_width=True):
            if new_user and new_pass:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_user, new_pass))
                        conn.commit()
                        st.success("Account created successfully! Please log in.")
                    except mysql.connector.IntegrityError:
                        st.error("Username is already taken.")
                    finally:
                        conn.close()
            else:
                st.warning("Please fill in both fields.")

# ================= MAIN DASHBOARD =================
else:
    user = st.session_state.user

    # Header section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 👤 @{user['username']} `(ID: #{user['user_id']})`")
    with col2:
        if st.button("Logout", type="primary"):
            st.session_state.user = None
            st.rerun()

    st.divider()

    # Navigation Tabs
    tab_feed, tab_msg, tab_users, tab_settings = st.tabs([
        "📰 Feed", 
        "💬 Messages", 
        "👥 Users", 
        "⚙️ Settings"
    ])

    # --- TAB 1: FEED ---
    with tab_feed:
        st.subheader("Create a Post")
        caption = st.text_area("Write a caption...", height=100)
        img_file = st.file_uploader("Attach Image (optional)", type=["png", "jpg", "jpeg"])
        
        if st.button("Publish Post"):
            if caption.strip():
                file_name = img_file.name if img_file else ""
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO posts (user_id, caption, media_url) VALUES (%s, %s, %s)",
                        (user['user_id'], caption, file_name)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Post published!")
                    st.rerun()
            else:
                st.warning("Please enter a caption.")

        st.divider()
        st.subheader("Community Feed")
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT posts.caption, posts.media_url, posts.created_at, users.username, users.user_id 
                FROM posts JOIN users ON posts.user_id = users.user_id 
                ORDER BY posts.created_at DESC
            """)
            posts = cursor.fetchall()
            conn.close()

            for p in posts:
                with st.container(border=True):
                    st.markdown(f"**@{p['username']}** `(# {p['user_id']})` — *{p['created_at']}*")
                    st.write(p['caption'])

    # --- TAB 2: DIRECT MESSAGES ---
    with tab_msg:
        st.subheader("💬 Direct Messages")
        target_id = st.number_input("Enter Friend User ID to chat with", min_value=1, step=1)
        
        if target_id:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT sender_id, message_text, sent_at FROM messages
                    WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
                    ORDER BY sent_at ASC
                """, (user['user_id'], target_id, target_id, user['user_id']))
                messages = cursor.fetchall()
                conn.close()

                # Render Message Chat History
                st.write("---")
                if not messages:
                    st.info("No messages exchanged yet. Say hi below!")
                for m in messages:
                    if m['sender_id'] == user['user_id']:
                        st.chat_message("user").write(m['message_text'])
                    else:
                        st.chat_message("assistant").write(m['message_text'])

            msg_input = st.text_input("Type your message...", key="chat_input")
            if st.button("Send Message"):
                if msg_input.strip():
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)",
                            (user['user_id'], target_id, msg_input)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

    # --- TAB 3: MEMBERS DIRECTORY ---
    with tab_users:
        st.subheader("👥 Registered Members")
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, username FROM users ORDER BY user_id ASC")
            all_users = cursor.fetchall()
            conn.close()

            for u in all_users:
                st.markdown(f"🆔 **#{u['user_id']}** — @{u['username']}")

    # --- TAB 4: SETTINGS ---
    with tab_settings:
        st.subheader("⚙️ Account Settings")
        
        new_uname = st.text_input("Change Username", value=user['username'])
        new_pwd = st.text_input("Change Password", value=user['password'], type="password")

        if st.button("Save Changes"):
            if new_uname.strip() and new_pwd.strip():
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            "UPDATE users SET username = %s, password = %s WHERE user_id = %s",
                            (new_uname, new_pwd, user['user_id'])
                        )
                        conn.commit()
                        st.success("Account details updated successfully! Please log in again.")
                        st.session_state.user = None
                        st.rerun()
                    except mysql.connector.IntegrityError:
                        st.error("That username is already taken.")
                    finally:
                        conn.close()
            else:
                st.warning("Fields cannot be empty.")
