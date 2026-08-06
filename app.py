import streamlit as st
import sqlite3
import base64
import io
from PIL import Image
from datetime import datetime
import time

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Noob Learning | Powered by Saraah Robotics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# DATABASE INITIALIZATION & CONNECTIVITY
# -----------------------------------------------------------------------------
DB_PATH = "noob_learning.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        bio TEXT,
        age INTEGER,
        gender TEXT,
        birth_date TEXT,
        account_type TEXT DEFAULT 'Public',
        profile_pic BLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Reels & Posts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reels_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        caption TEXT,
        media_data BLOB,
        media_type TEXT,
        media_url TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        likes INTEGER DEFAULT 0
    )
    """)
    
    # Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Likes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        post_id INTEGER NOT NULL,
        UNIQUE(username, post_id)
    )
    """)
    
    # Seed default sample users if empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()['count'] == 0:
        default_users = [
            ("princehumperdinck87", "princehumperdinck87", "password123", "Prince Humperdinck", "Exploring AI & Robotics 🤖 | Founder Noob Learning", 21, "Male", "15/08/2003", "Public", None),
            ("saraah_robotics", "saraah_robotics", "password123", "Saraah Robotics", "Official Saraah Robotics Account 🚀 Autonomous Systems & AI", 22, "Prefer not to say", "01/01/2002", "Public", None),
            ("alex_dev", "alex_dev", "password123", "Alex Rivera", "Building cool Python & AI web apps 💻", 19, "Other", "12/04/2005", "Public", None),
            ("noob_coder", "noob_coder", "password123", "Noob Coder", "Learning Python step by step 🐍", 18, "Female", "05/11/2006", "Public", None),
        ]
        cursor.executemany("""
        INSERT INTO users (user_id, username, password, full_name, bio, age, gender, birth_date, account_type, profile_pic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_users)
        
        # Seed sample feed posts & reels
        sample_posts = [
            ("saraah_robotics", "🚀 Exciting milestone! Our new robotic arm prototype passed all AI visual testing! What should we build next? #SaraahRobotics #AI", None, "image", "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&q=80", 12),
            ("princehumperdinck87", "Building the ultimate social learning platform for Gen Z developers with Python & Streamlit! 🔥 What do you think of Noob Learning?", None, "image", "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&q=80", 28),
            ("alex_dev", "Late night debugging session paid off! 💡 Never give up on your code.", None, "image", "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80", 9),
        ]
        cursor.executemany("""
        INSERT INTO reels_posts (username, caption, media_data, media_type, media_url, likes)
        VALUES (?, ?, ?, ?, ?, ?)
        """, sample_posts)
        
        # Seed sample chat history matching Image 2
        sample_chats = [
            ("princehumperdinck87", "saraah_robotics", "Hello, I heard you're pretty and you must marry me. NOW.", "2026-08-06 17:13:00"),
            ("saraah_robotics", "princehumperdinck87", "I refuse your request.", "2026-08-06 17:13:15"),
            ("princehumperdinck87", "saraah_robotics", "You must or you die a painful death.", "2026-08-06 17:13:30"),
            ("saraah_robotics", "princehumperdinck87", "Fine, but I will never love you.", "2026-08-06 17:13:45"),
            ("princehumperdinck87", "saraah_robotics", "Deal.", "2026-08-06 17:14:00"),
        ]
        cursor.executemany("""
        INSERT INTO messages (sender, receiver, message, timestamp)
        VALUES (?, ?, ?, ?)
        """, sample_chats)
        
    conn.commit()
    conn.close()

# Initialize DB on script load
init_db()

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def get_user(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def authenticate_user(username_or_id, password):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE (username = ? OR user_id = ?) AND password = ?",
        (username_or_id, username_or_id, password)
    ).fetchone()
    conn.close()
    return user

def create_user_account(user_id, username, password, full_name, bio, age, gender, birth_date, account_type, profile_pic_bytes):
    conn = get_db_connection()
    try:
        conn.execute("""
        INSERT INTO users (user_id, username, password, full_name, bio, age, gender, birth_date, account_type, profile_pic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, password, full_name, bio, age, gender, birth_date, account_type, profile_pic_bytes))
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        conn.close()
        if "UNIQUE" in str(e).upper():
            return False, "Username or User ID already exists. Please choose another."
        return False, f"Error creating account: {e}"

def get_image_b64(blob):
    if not blob:
        return None
    try:
        return base64.b64encode(blob).decode("utf-8")
    except Exception:
        return None

def render_avatar(username, profile_pic_blob=None, size=40):
    b64 = get_image_b64(profile_pic_blob)
    if b64:
        return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px; height:{size}px; border-radius:50%; object-fit:cover; display:inline-block; vertical-align:middle;" />'
    else:
        initial = username[0].upper() if username else 'U'
        colors = ['#3b82f6', '#ec4899', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']
        color = colors[len(username) % len(colors)] if username else '#3b82f6'
        return f'<div style="width:{size}px; height:{size}px; border-radius:50%; background:{color}; color:white; display:inline-flex; align-items:center; justify-content:center; font-weight:700; font-size:{int(size*0.45)}px; vertical-align:middle; text-transform:uppercase;">{initial}</div>'

# -----------------------------------------------------------------------------
# GLOBAL STYLING (SLEEK INTERFACE DESIGN THEME)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Hide Streamlit default headers & footers */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main layout font & background - Sleek Dark Aesthetic */
    .stApp {
        background-color: #050505 !important;
        color: #ffffff !important;
        font-family: 'Helvetica Neue', Arial, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Sleek typography defaults */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #ffffff;
    }

    /* Instagram Gradient Helper */
    .ig-gradient-text {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Custom Login Card (Sleek Glassmorphic Interface) */
    .login-container {
        max-width: 420px;
        margin: 50px auto 20px auto;
        text-align: center;
    }
    .login-title {
        font-size: 42px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 24px;
        letter-spacing: -1px;
    }
    .login-box {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 32px 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .login-footer-text {
        color: rgba(255, 255, 255, 0.4);
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 2.5px;
        margin-top: 36px;
        text-align: center;
    }
    
    /* Primary Action Buttons (Green or Instagram Accent) */
    div.stButton > button[kind="primary"], .green-btn button {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 10px 18px !important;
        width: 100% !important;
        box-shadow: 0 4px 14px rgba(34, 197, 94, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4) !important;
    }
    
    /* Secondary Outline Button */
    div.stButton > button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: rgba(255, 255, 255, 0.3) !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
    }

    /* Sleek Input Fields */
    div.stTextInput > div > div > input,
    div.stTextArea > div > div > textarea,
    div.stSelectbox > div > div {
        border-radius: 12px !important;
        background-color: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        padding: 12px 14px !important;
        font-size: 14px !important;
        color: #ffffff !important;
    }
    div.stTextInput > div > div > input:focus,
    div.stTextArea > div > div > textarea:focus {
        border-color: #22c55e !important;
        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.3) !important;
    }

    /* Top Navigation Header */
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        padding: 14px 28px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 24px;
        border-radius: 0 0 20px 20px;
    }
    .brand-logo {
        font-size: 24px;
        font-weight: 800;
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .brand-sub {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.5);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    /* Chat Styling (Sleek Dark Theme - Image 2 Replica) */
    .chat-header-bar {
        display: flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 14px 18px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px 16px 0 0;
    }
    .chat-user-title {
        font-weight: 700;
        font-size: 16px;
        color: #ffffff;
        margin-left: 12px;
        line-height: 1.2;
    }
    .chat-active-status {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .active-dot {
        width: 8px;
        height: 8px;
        background-color: #22c55e;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
    }

    /* Chat Bubble Received (Left) - Glass dark bubble */
    .chat-row-left {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 16px;
        justify-content: flex-start;
    }
    .bubble-received {
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        border-top-left-radius: 4px;
        padding: 12px 18px;
        max-width: 75%;
        color: #ffffff;
        font-size: 14px;
        line-height: 1.5;
        backdrop-filter: blur(8px);
    }

    /* Chat Bubble Sent (Right) - Sleek Blue Accent */
    .chat-row-right {
        display: flex;
        align-items: flex-end;
        gap: 10px;
        margin-bottom: 16px;
        justify-content: flex-end;
    }
    .bubble-sent {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border-radius: 20px;
        border-top-right-radius: 4px;
        padding: 12px 18px;
        max-width: 75%;
        color: #ffffff;
        font-size: 14px;
        line-height: 1.5;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    .seen-indicator {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
        text-align: right;
        margin-top: 4px;
    }

    /* Post / Reel Cards - Glassmorphism Card Style */
    .feed-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
    }
    .card-username {
        font-weight: 700;
        font-size: 15px;
        color: #ffffff;
    }
    .card-time {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(0,0,0,0.2);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.15);
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # 'login' or 'signup'
if "current_page" not in st.session_state:
    st.session_state.current_page = "feed"  # 'feed', 'reels', 'chat', 'profile'
if "active_chat_user" not in st.session_state:
    st.session_state.active_chat_user = None
if "signup_msg" not in st.session_state:
    st.session_state.signup_msg = None

# =============================================================================
# AUTHENTICATION FLOW (LOGIN & SIGN UP)
# =============================================================================
if not st.session_state.logged_in:
    
    # -------------------------------------------------------------------------
    # LOGIN VIEW (Replicating Image 1)
    # -------------------------------------------------------------------------
    if st.session_state.auth_mode == "login":
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Noob Learning</div>', unsafe_allow_html=True)
        
        if st.session_state.signup_msg:
            st.success(st.session_state.signup_msg)
            st.session_state.signup_msg = None
            
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            
            login_user_input = st.text_input(
                "Username or mobile number",
                placeholder="Username or mobile number",
                key="login_user_input",
                label_visibility="collapsed"
            )
            
            login_pass_input = st.text_input(
                "Password",
                type="password",
                placeholder="Password",
                key="login_pass_input",
                label_visibility="collapsed"
            )
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            if st.button("Log in", type="primary", key="btn_login_submit"):
                if login_user_input and login_pass_input:
                    user = authenticate_user(login_user_input, login_pass_input)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user["username"]
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.warning("Please enter your credentials.")
                    
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        
        if st.button("Create new account", type="secondary", key="btn_go_signup"):
            st.session_state.auth_mode = "signup"
            st.rerun()
            
        st.markdown('<div class="login-footer-text">SARAAH ROBOTICS</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SIGN UP VIEW (Instagram-style Detailed Onboarding)
    # -------------------------------------------------------------------------
    elif st.session_state.auth_mode == "signup":
        st.markdown('<div class="login-container" style="max-width: 480px;">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Join Noob Learning</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#64748b; font-size:14px; margin-top:-16px; margin-bottom:24px;">Powered by Saraah Robotics</p>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="login-box" style="text-align: left;">', unsafe_allow_html=True)
            
            st.markdown("##### 1. Account Security")
            s_fullname = st.text_input("Full Name", placeholder="e.g. John Doe", key="su_fullname")
            s_username = st.text_input("User ID / Username", placeholder="e.g. noob_master", key="su_username")
            s_password = st.text_input("Password", type="password", placeholder="Choose a strong password", key="su_password")
            
            st.markdown("##### 2. Profile Details")
            col1, col2 = st.columns(2)
            with col1:
                s_age = st.number_input("Age", min_value=10, max_value=120, value=18, key="su_age")
            with col2:
                s_gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], key="su_gender")
                
            s_birthdate = st.text_input("Birth Date (DD/MM/YYYY)", placeholder="e.g. 15/08/2004", key="su_birthdate")
            s_account_type = st.radio("Account Privacy", ["Public", "Private"], horizontal=True, key="su_acct_type")
            s_bio = st.text_area("Bio / About You", placeholder="Share your learning interests & goals...", key="su_bio")
            
            s_pic_file = st.file_uploader("Profile Picture Upload (Optional)", type=["jpg", "jpeg", "png"], key="su_pic")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            if st.button("Create Account", type="primary", key="btn_create_acct"):
                if s_username and s_password and s_fullname:
                    pic_bytes = s_pic_file.read() if s_pic_file else None
                    success, msg = create_user_account(
                        user_id=s_username,
                        username=s_username,
                        password=s_password,
                        full_name=s_fullname,
                        bio=s_bio,
                        age=s_age,
                        gender=s_gender,
                        birth_date=s_birthdate,
                        account_type=s_account_type,
                        profile_pic_bytes=pic_bytes
                    )
                    if success:
                        st.session_state.signup_msg = "Account created successfully! Please log in."
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill in all required fields (Full Name, Username, Password).")
                    
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Already have an account? Log in", type="secondary", key="btn_back_login"):
            st.session_state.auth_mode = "login"
            st.rerun()
            
        st.markdown('<div class="login-footer-text">SARAAH ROBOTICS</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# LOGGED IN DASHBOARD
# =============================================================================
else:
    current_user = get_user(st.session_state.username)
    
    # -------------------------------------------------------------------------
    # TOP NAVIGATION BAR
    # -------------------------------------------------------------------------
    nav_col1, nav_col2, nav_col3 = st.columns([3, 6, 2])
    
    with nav_col1:
        st.markdown('''
        <div>
            <span class="brand-logo">⚡ Noob Learning</span><br>
            <span class="brand-sub">Powered by Saraah Robotics</span>
        </div>
        ''', unsafe_allow_html=True)
        
    with nav_col2:
        btn_c1, btn_c2, btn_c3, btn_c4 = st.columns(4)
        with btn_c1:
            if st.button("🏠 Feed", use_container_width=True, type="primary" if st.session_state.current_page == "feed" else "secondary"):
                st.session_state.current_page = "feed"
                st.rerun()
        with btn_c2:
            if st.button("🎬 Reels", use_container_width=True, type="primary" if st.session_state.current_page == "reels" else "secondary"):
                st.session_state.current_page = "reels"
                st.rerun()
        with btn_c3:
            if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state.current_page == "chat" else "secondary"):
                st.session_state.current_page = "chat"
                st.rerun()
        with btn_c4:
            if st.button("👤 Profile", use_container_width=True, type="primary" if st.session_state.current_page == "profile" else "secondary"):
                st.session_state.current_page = "profile"
                st.rerun()
                
    with nav_col3:
        user_avatar_html = render_avatar(st.session_state.username, current_user["profile_pic"] if current_user else None, size=32)
        st.markdown(f'<div style="display:flex; align-items:center; gap:8px; justify-content:flex-end;">{user_avatar_html} <b>@{st.session_state.username}</b></div>', unsafe_allow_html=True)
        if st.button("Log out", key="btn_logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
            
    st.markdown("<hr style='margin-top:8px; margin-bottom:20px; border:none; border-top:1px solid rgba(255, 255, 255, 0.1);'>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # PAGE 1: HOME / FEED HUB
    # -------------------------------------------------------------------------
    if st.session_state.current_page == "feed":
        col_main, col_side = st.columns([7, 3])
        
        with col_main:
            # Create Post Box
            with st.container():
                st.markdown('<div class="feed-card">', unsafe_allow_html=True)
                st.markdown("##### 📝 Share a Learning Update or Post")
                post_caption = st.text_area("What are you learning today?", placeholder="Share code snippets, robotics updates, or learning notes...", key="post_text_input", height=80)
                uploaded_file = st.file_uploader("Upload Image or Video (Optional)", type=["jpg", "jpeg", "png", "mp4"], key="post_file_input")
                
                if st.button("Publish Post 🚀", type="primary", key="btn_publish_post"):
                    if post_caption or uploaded_file:
                        conn = get_db_connection()
                        media_bytes = uploaded_file.read() if uploaded_file else None
                        m_type = "image"
                        if uploaded_file and uploaded_file.name.lower().endswith(".mp4"):
                            m_type = "video"
                            
                        conn.execute("""
                        INSERT INTO reels_posts (username, caption, media_data, media_type)
                        VALUES (?, ?, ?, ?)
                        """, (st.session_state.username, post_caption, media_bytes, m_type))
                        conn.commit()
                        conn.close()
                        st.success("Post published!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.warning("Please add a caption or media.")
                st.markdown('</div>', unsafe_allow_html=True)
                
            # Feed List
            conn = get_db_connection()
            posts = conn.execute("SELECT * FROM reels_posts ORDER BY timestamp DESC").fetchall()
            conn.close()
            
            for post in posts:
                post_author = get_user(post["username"])
                author_avatar = render_avatar(post["username"], post_author["profile_pic"] if post_author else None, size=38)
                
                st.markdown('<div class="feed-card">', unsafe_allow_html=True)
                st.markdown(f'''
                <div class="card-header">
                    {author_avatar}
                    <div>
                        <div class="card-username">@{post["username"]}</div>
                        <div class="card-time">{post["timestamp"]}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                if post["caption"]:
                    st.markdown(f'<p style="font-size:15px; color:#ffffff; margin-bottom:12px;">{post["caption"]}</p>', unsafe_allow_html=True)
                    
                if post["media_data"]:
                    if post["media_type"] == "video":
                        st.video(post["media_data"])
                    else:
                        st.image(post["media_data"], use_container_width=True)
                elif post["media_url"]:
                    st.image(post["media_url"], use_container_width=True)
                    
                col_l, col_c, col_s = st.columns([2, 2, 6])
                with col_l:
                    if st.button(f"❤️ {post['likes']}", key=f"like_{post['id']}"):
                        conn = get_db_connection()
                        conn.execute("UPDATE reels_posts SET likes = likes + 1 WHERE id = ?", (post['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with col_side:
            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            st.markdown("### 🤖 Saraah Robotics Hub")
            st.markdown("""
            Welcome to **Noob Learning**! Connect with peers, share robotics prototypes, upload reels, and exchange live messages with other learners.
            
            **Platform Features:**
            - 🎥 **Reels Hub:** Watch and post bite-sized learning reels.
            - 💬 **Live Chat:** Direct messaging with zero lag.
            - 👤 **Custom Profiles:** Public/Private badges & bios.
            """)
            st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # PAGE 2: REELS HUB
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == "reels":
        reels_tab1, reels_tab2 = st.tabs(["🎬 Watch Reels", "➕ Create Reel"])
        
        with reels_tab1:
            conn = get_db_connection()
            reels = conn.execute("SELECT * FROM reels_posts ORDER BY id DESC").fetchall()
            conn.close()
            
            if reels:
                for reel in reels:
                    reel_author = get_user(reel["username"])
                    author_av = render_avatar(reel["username"], reel_author["profile_pic"] if reel_author else None, size=40)
                    
                    st.markdown('<div class="feed-card" style="max-width:540px; margin:0 auto 24px auto;">', unsafe_allow_html=True)
                    st.markdown(f'''
                    <div class="card-header">
                        {author_av}
                        <div>
                            <div class="card-username">@{reel["username"]}</div>
                            <div class="card-time">{reel["timestamp"]}</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    if reel["media_data"]:
                        if reel["media_type"] == "video":
                            st.video(reel["media_data"])
                        else:
                            st.image(reel["media_data"], use_container_width=True)
                    elif reel["media_url"]:
                        st.image(reel["media_url"], use_container_width=True)
                    else:
                        st.info("Text Reel: " + (reel["caption"] or ""))
                        
                    if reel["caption"]:
                        st.markdown(f'<p style="font-size:15px; margin-top:10px; color:#ffffff;"><b>@{reel["username"]}</b> {reel["caption"]}</p>', unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([2, 8])
                    with c1:
                        if st.button(f"❤️ {reel['likes']}", key=f"reel_like_{reel['id']}"):
                            conn = get_db_connection()
                            conn.execute("UPDATE reels_posts SET likes = likes + 1 WHERE id = ?", (reel['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No reels available yet. Create the first one!")

        with reels_tab2:
            st.markdown('<div class="feed-card" style="max-width:600px; margin:0 auto;">', unsafe_allow_html=True)
            st.markdown("### 🎥 Create New Reel")
            reel_cap = st.text_input("Reel Caption / Title", placeholder="Write a catchy caption...", key="reel_cap_in")
            reel_file = st.file_uploader("Upload Video (MP4) or Image (JPG/PNG)", type=["mp4", "jpg", "jpeg", "png"], key="reel_file_in")
            
            if st.button("Publish Reel 🎬", type="primary", key="btn_publish_reel"):
                if reel_file:
                    file_bytes = reel_file.read()
                    m_type = "video" if reel_file.name.lower().endswith(".mp4") else "image"
                    
                    conn = get_db_connection()
                    conn.execute("""
                    INSERT INTO reels_posts (username, caption, media_data, media_type)
                    VALUES (?, ?, ?, ?)
                    """, (st.session_state.username, reel_cap, file_bytes, m_type))
                    conn.commit()
                    conn.close()
                    
                    st.success("Reel published successfully!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("Please upload a media file for your reel.")
            st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # PAGE 3: LIVE CHAT HUB (Exact Image 2 Specification)
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == "chat":
        
        # VIEW A: INBOX / SELECT CONTACT (when no active_chat_user selected)
        if st.session_state.active_chat_user is None:
            st.markdown("### 💬 Direct Messages")
            st.markdown("<p style='color:rgba(255,255,255,0.6); font-size:14px;'>Select a peer or mentor to start chatting instantly.</p>", unsafe_allow_html=True)
            
            conn = get_db_connection()
            all_users = conn.execute("SELECT * FROM users WHERE username != ?", (st.session_state.username,)).fetchall()
            conn.close()
            
            for user_item in all_users:
                u_avatar = render_avatar(user_item["username"], user_item["profile_pic"], size=44)
                
                col_u1, col_u2, col_u3 = st.columns([1, 6, 3])
                with col_u1:
                    st.markdown(u_avatar, unsafe_allow_html=True)
                with col_u2:
                    st.markdown(f"**{user_item['full_name']}** (@{user_item['username']})")
                    st.markdown(f"<span style='font-size:12px; color:rgba(255,255,255,0.6);'>{user_item['bio'] or 'No bio provided'}</span>", unsafe_allow_html=True)
                with col_u3:
                    if st.button(f"Message 💬", key=f"chat_with_{user_item['username']}", type="primary"):
                        st.session_state.active_chat_user = user_item["username"]
                        st.rerun()
                st.markdown("<hr style='margin:10px 0; border:none; border-top:1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # VIEW B: ACTIVE CHAT ROOM (Strict Image 2 Design match)
        else:
            target_username = st.session_state.active_chat_user
            target_user = get_user(target_username)
            target_avatar = render_avatar(target_username, target_user["profile_pic"] if target_user else None, size=36)
            
            # Top Header Bar for Chat with Back Arrow
            c_back, c_title = st.columns([1, 11])
            with c_back:
                if st.button("←", key="btn_chat_back", help="Back to Inbox"):
                    st.session_state.active_chat_user = None
                    st.rerun()
            with c_title:
                st.markdown(f'''
                <div style="display:flex; align-items:center; gap:10px;">
                    {target_avatar}
                    <div>
                        <div style="font-weight:700; font-size:16px; color:#ffffff;">{target_username}</div>
                        <div style="font-size:12px; color:rgba(255,255,255,0.6); display:flex; align-items:center; gap:4px;">
                            <span style="width:7px; height:7px; background:#22c55e; border-radius:50%; display:inline-block; box-shadow:0 0 8px rgba(34,197,94,0.6);"></span> Active Now
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
            st.markdown("<hr style='margin:12px 0 20px 0; border:none; border-top:1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            
            # Timestamp Divider
            st.markdown('<div style="text-align:center; color:rgba(255,255,255,0.4); font-size:12px; margin-bottom:16px;">Today 5:13 PM</div>', unsafe_allow_html=True)
            
            # Fetch Conversation Messages
            conn = get_db_connection()
            chat_messages = conn.execute("""
            SELECT * FROM messages 
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
            ORDER BY timestamp ASC
            """, (st.session_state.username, target_username, target_username, st.session_state.username)).fetchall()
            conn.close()
            
            # Render Messages Container
            chat_container = st.container()
            with chat_container:
                for msg in chat_messages:
                    if msg["sender"] == target_username:
                        # Received Message (Left)
                        st.markdown(f'''
                        <div class="chat-row-left">
                            {target_avatar}
                            <div class="bubble-received">
                                {msg["message"]}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        # Sent Message (Right)
                        st.markdown(f'''
                        <div class="chat-row-right">
                            <div>
                                <div class="bubble-sent">
                                    {msg["message"]}
                                </div>
                                <div class="seen-indicator">Seen</div>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)

            # Bottom Chat Input Area (matching Image 2)
            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            
            with st.form("chat_form", clear_on_submit=True):
                col_act, col_input, col_send = st.columns([1.5, 8, 2.5])
                with col_act:
                    st.markdown("<div style='font-size:22px; padding-top:6px; text-align:center;'>📷 😀 🖼️</div>", unsafe_allow_html=True)
                with col_input:
                    new_msg = st.text_input("Message...", placeholder="Message...", label_visibility="collapsed", key="chat_msg_input")
                with col_send:
                    send_submitted = st.form_submit_button("Send 🚀", type="primary", use_container_width=True)
                    
                if send_submitted and new_msg.strip():
                    conn = get_db_connection()
                    conn.execute("""
                    INSERT INTO messages (sender, receiver, message)
                    VALUES (?, ?, ?)
                    """, (st.session_state.username, target_username, new_msg.strip()))
                    conn.commit()
                    conn.close()
                    st.rerun()

    # -------------------------------------------------------------------------
    # PAGE 4: PROFILE & SETTINGS HUB
    # -------------------------------------------------------------------------
    elif st.session_state.current_page == "profile":
        user_info = get_user(st.session_state.username)
        
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        col_p1, col_p2 = st.columns([2, 8])
        with col_p1:
            st.markdown(render_avatar(user_info["username"], user_info["profile_pic"], size=96), unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"### {user_info['full_name']} (@{user_info['username']})")
            st.markdown(f"<p style='color:rgba(255,255,255,0.6); margin-top:-10px;'><b>Account Type:</b> <span style='background:rgba(34,197,94,0.15); color:#4ade80; border:1px solid rgba(34,197,94,0.3); padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600;'>{user_info['account_type']}</span></p>", unsafe_allow_html=True)
            st.markdown(f"**Bio:** {user_info['bio'] or 'No bio provided yet.'}")
            
            c_stat1, c_stat2, c_stat3 = st.columns(3)
            c_stat1.metric("Posts / Reels", "12")
            c_stat2.metric("Followers", "342")
            c_stat3.metric("Following", "189")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Expandable Settings Panel
        with st.expander("⚙️ Edit Profile Settings"):
            with st.form("update_profile_form"):
                new_fullname = st.text_input("Full Name", value=user_info["full_name"])
                new_bio = st.text_area("Bio", value=user_info["bio"] or "")
                new_age = st.number_input("Age", value=user_info["age"] or 18, min_value=10, max_value=120)
                new_gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], index=["Male", "Female", "Other", "Prefer not to say"].index(user_info["gender"]) if user_info["gender"] in ["Male", "Female", "Other", "Prefer not to say"] else 0)
                new_birthdate = st.text_input("Birth Date", value=user_info["birth_date"] or "")
                new_acct_type = st.radio("Account Privacy", ["Public", "Private"], index=0 if user_info["account_type"] == "Public" else 1)
                new_pic_file = st.file_uploader("Change Profile Picture", type=["jpg", "jpeg", "png"])
                
                if st.form_submit_button("Save Profile Settings 💾", type="primary"):
                    conn = get_db_connection()
                    if new_pic_file:
                        pic_bytes = new_pic_file.read()
                        conn.execute("""
                        UPDATE users SET full_name = ?, bio = ?, age = ?, gender = ?, birth_date = ?, account_type = ?, profile_pic = ?
                        WHERE username = ?
                        """, (new_fullname, new_bio, new_age, new_gender, new_birthdate, new_acct_type, pic_bytes, st.session_state.username))
                    else:
                        conn.execute("""
                        UPDATE users SET full_name = ?, bio = ?, age = ?, gender = ?, birth_date = ?, account_type = ?
                        WHERE username = ?
                        """, (new_fullname, new_bio, new_age, new_gender, new_birthdate, new_acct_type, st.session_state.username))
                    conn.commit()
                    conn.close()
                    st.success("Profile updated successfully!")
                    time.sleep(0.5)
                    st.rerun()
