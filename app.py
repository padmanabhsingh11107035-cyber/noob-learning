import streamlit as st
import sqlite3
import datetime
import logging
import sys
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# ==============================================================================
# 0. LOGGING & PAGE CONFIG
# ==============================================================================
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("NoobLearningApp")

st.set_page_config(
    page_title="Noob Learning",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 1. DATABASE SETUP
# ==============================================================================
def get_db_connection():
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                bio TEXT,
                age INTEGER,
                gender TEXT,
                birth_date TEXT,
                account_type TEXT,
                profile_pic TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reels_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                caption TEXT,
                media_type TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                receiver TEXT,
                message TEXT,
                timestamp TEXT
            )
        """)
        # Insert default demo accounts if not exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            demo_users = [
                ('saraah_robotics', 'password123', 'Saraah Robotics', 'Official Saraah Robotics Account 🚀 Autonomous Systems & AI', 18, 'Other', '01/01/2005', 'Creator'),
                ('princehumperdinck87', 'password123', 'Prince Humperdinck', 'Exploring AI & Robotics 🤖 | Founder Noob Learning', 18, 'Male', '15/05/2005', 'Student'),
                ('alex_dev', 'password123', 'Alex Rivera', 'Building cool Python & AI web apps 💻', 19, 'Male', '10/10/2004', 'Student'),
                ('noob_coder', 'password123', 'Noob Coder', 'Learning Python step by step 🪀', 17, 'Female', '22/12/2006', 'Student')
            ]
            cursor.executemany("""
                INSERT OR IGNORE INTO users (username, password, full_name, bio, age, gender, birth_date, account_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, demo_users)
        conn.commit()
        conn.close()

init_db()

def get_current_ist_time():
    ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(ist_offset).strftime("%Y-%m-%d %H:%M:%S")

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "login"
if 'nav_option' not in st.session_state:
    st.session_state.nav_option = "Feed"
if 'active_chat_user' not in st.session_state:
    st.session_state.active_chat_user = None

# ==============================================================================
# 2. CUSTOM CSS THEME (Exact Dark Aesthetics & Layout)
# ==============================================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    header {visibility: hidden;}
    
    /* Buttons */
    div.stButton > button {
        background-color: #00C853 !important;
        color: #0e1117 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    div.stButton > button:hover {
        opacity: 0.85;
    }
    
    /* Input Fields */
    input, textarea {
        background-color: #161b22 !important;
        color: white !important;
        border: 1px solid #30363d !important;
    }
    
    /* Card containers */
    .element-container {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. AUTHENTICATION SCREEN
# ==============================================================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='color: #ff4b4b; font-family: sans-serif; text-align: center;'>⚡ Noob Learning</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888; font-size: 0.85rem; letter-spacing: 1px;'>POWERED BY SARAAH ROBOTICS</p>", unsafe_allow_html=True)
        
        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                username_in = st.text_input("Username or mobile number", placeholder="username")
                password_in = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Log in", use_container_width=True)
                
                if submitted:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username_in.strip().lower(), password_in))
                        row = cursor.fetchone()
                        conn.close()
                        if row:
                            st.session_state.logged_in = True
                            st.session_state.user = dict(row)
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")
                            
            if st.button("Create new account", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()
        else:
            with st.form("signup_form"):
                st.markdown("### Create an Account")
                new_user = st.text_input("Username", placeholder="choose username").lower()
                new_pass = st.text_input("Password", type="password")
                full_name = st.text_input("Full Name")
                bio = st.text_area("Bio")
                
                if st.form_submit_button("Sign Up", use_container_width=True):
                    if new_user and new_pass:
                        conn = get_db_connection()
                        if conn:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO users (username, password, full_name, bio, account_type)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (new_user.strip(), new_pass, full_name, bio, 'Student'))
                                conn.commit()
                                conn.close()
                                st.success("Account created! Please log in.")
                                st.session_state.auth_mode = "login"
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Username already taken.")
                                conn.close()
                    else:
                        st.warning("Fill in username and password.")
            
            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
                
    st.stop()

# ==============================================================================
# 4. MAIN APP DASHBOARD & TOP NAVIGATION BAR
# ==============================================================================
user = st.session_state.user
username = user['username']
first_letter = username[0].upper()

# Top Header Layout (Brand + Nav Tabs + Profile Widget matching Images 3 & 4)
header_col1, header_col2, header_col3, header_col4, header_col5, header_col_profile = st.columns([2.5, 1, 1, 1, 1, 1.8])

with header_col1:
    st.markdown("""
        <div>
            <h3 style='margin:0; color:#ff4b4b; font-size: 1.5rem;'>⚡ Noob Learning</h3>
            <p style='margin:0; font-size: 0.65rem; color:#888; letter-spacing:1px;'>POWERED BY SARAAH ROBOTICS</p>
        </div>
    """, unsafe_allow_html=True)

with header_col2:
    if st.button("🏠 Feed", use_container_width=True):
        st.session_state.nav_option = "Feed"
        st.session_state.active_chat_user = None
        st.rerun()
with header_col3:
    if st.button("🎬 Reels", use_container_width=True):
        st.session_state.nav_option = "Reels"
        st.session_state.active_chat_user = None
        st.rerun()
with header_col4:
    if st.button("💬 Chat", use_container_width=True):
        st.session_state.nav_option = "Chat"
        st.rerun()
with header_col5:
    if st.button("👤 Profile", use_container_width=True):
        st.session_state.nav_option = "Profile"
        st.session_state.active_chat_user = None
        st.rerun()

with header_col_profile:
    prof_col_avatar, prof_col_name, prof_col_btn = st.columns([1, 2, 1.5])
    with prof_col_avatar:
        st.markdown(f"""
            <div style="background-color: #00C853; color: #0e1117; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-top: 5px;">
                {first_letter}
            </div>
        """, unsafe_allow_html=True)
    with prof_col_name:
        st.markdown(f"<p style='color: white; font-weight: bold; font-size: 13px; margin: 8px 0 0 0;'>@{username}</p>", unsafe_allow_html=True)
    with prof_col_btn:
        if st.button("Log out", key="logout_top"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

st.markdown("<hr style='border: 0.5px solid #30363d; margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

current_tab = st.session_state.get('nav_option', 'Feed')

# ==============================================================================
# TAB 1: FEED
# ==============================================================================
if current_tab == "Feed":
    main_col, side_col = st.columns([2.2, 1.2])
    
    with main_col:
        st.markdown("### 📝 Share a Learning Update or Post")
        with st.form("post_form"):
            caption = st.text_area("What are you learning today?", placeholder="Share code snippets, robotics updates, or learning notes...")
            uploaded_file = st.file_uploader("Upload Image or Video (Optional)", type=['jpg', 'png', 'mp4'])
            if st.form_submit_button("Publish Post 🚀", use_container_width=True):
                if caption.strip():
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO reels_posts (username, caption, media_type, timestamp)
                            VALUES (?, ?, ?, ?)
                        """, (username, caption, "Post", get_current_ist_time()))
                        conn.commit()
                        conn.close()
                        st.success("Published successfully!")
                        st.rerun()
                else:
                    st.warning("Please add some text.")

        st.markdown("---")
        
        # Display Feed Posts
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reels_posts ORDER BY id DESC")
            posts = cursor.fetchall()
            conn.close()
            
            for p in posts:
                p_dict = dict(p)
                st.markdown(f"""
                    <div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #30363d;">
                        <span style="background: #00C853; color: #0e1117; padding: 2px 8px; border-radius: 50%; font-weight: bold;">{p_dict['username'][0].upper()}</span>
                        <strong style="color: white; margin-left: 8px;">@{p_dict['username']}</strong>
                        <p style="color: #888; font-size: 11px; margin-left: 36px; margin-top: -2px;">{p_dict['timestamp']}</p>
                        <p style="color: #ddd; margin-top: 10px;">{p_dict['caption']}</p>
                    </div>
                """, unsafe_allow_html=True)

    with side_col:
        st.markdown("""
            <div style="background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d;">
                <h3 style="color: white; margin-top: 0;">🤖 Saraah Robotics Hub</h3>
                <p style="color: #ccc; font-size: 14px;">Welcome to <b>Noob Learning</b>! Connect with peers, share robotics prototypes, upload reels, and exchange live messages with other learners.</p>
                <hr style="border: 0.5px solid #30363d;">
                <b style="color: white;">Platform Features:</b>
                <ul style="color: #aaa; font-size: 13px; padding-left: 20px; line-height: 1.6;">
                    <li>🎬 <b>Reels Hub:</b> Watch and post bite-sized learning reels.</li>
                    <li>💬 <b>Live Chat:</b> Direct messaging with zero lag.</li>
                    <li>👤 <b>Custom Profiles:</b> Public/Private badges & bios.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# TAB 2: REELS SECTION
# ==============================================================================
elif current_tab == "Reels":
    st.markdown("### 🎬 Reels Hub")
    st.markdown("<p style='color: #888;'>Explore short educational videos and robotics clips created by the community.</p>", unsafe_allow_html=True)
    
    sub_tab_watch, sub_tab_create = st.tabs(["🎥 Watch Reels", "➕ Create Reel"])
    
    with sub_tab_watch:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reels_posts WHERE media_type = 'Reel' ORDER BY id DESC")
            reels = cursor.fetchall()
            conn.close()
            
            if not reels:
                st.info("No reels available yet. Be the first creator to post one!")
            for r in reels:
                r_dict = dict(r)
                st.markdown(f"""
                    <div style="background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <div style="background-color: #ff4b4b; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                                {r_dict['username'][0].upper()}
                            </div>
                            <div>
                                <strong style="color: white;">@{r_dict['username']}</strong><br>
                                <span style="color: #888; font-size: 11px;">{r_dict['timestamp']}</span>
                            </div>
                        </div>
                        <p style="font-size: 15px; color: #eee; margin-top: 10px;">{r_dict['caption']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
    with sub_tab_create:
        st.markdown("### Upload a New Reel")
        with st.form("create_reel_form"):
            reel_caption = st.text_area("Reel Caption & Hashtags", placeholder="Explain your robotics build or python trick... #Robotics #Python")
            reel_file = st.file_uploader("Upload Video File (MP4, MOV)", type=['mp4', 'mov'])
            if st.form_submit_button("Publish Reel 🎬", use_container_width=True):
                if reel_caption.strip():
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO reels_posts (username, caption, media_type, timestamp)
                            VALUES (?, ?, ?, ?)
                        """, (username, reel_caption, "Reel", get_current_ist_time()))
                        conn.commit()
                        conn.close()
                        st.success("Reel published successfully!")
                        st.rerun()
                else:
                    st.warning("Please add a caption for your reel.")

# ==============================================================================
# TAB 3: CHAT SECTION (Exact match to Image 3)
# ==============================================================================
elif current_tab == "Chat":
    conn = get_db_connection()
    peers = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username != ?", (username,))
        peers = cursor.fetchall()
        conn.close()

    if st.session_state.active_chat_user is None:
        st.markdown("### 💬 Direct Messages")
        st.markdown("<p style='color: #888; font-size: 14px;'>Select a peer or mentor to start chatting instantly.</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 0.5px solid #30363d;'>", unsafe_allow_html=True)

        for p in peers:
            p_dict = dict(p)
            avatar_char = p_dict['username'][0].upper()
            
            c_info, c_btn = st.columns([5, 1])
            with c_info:
                st.markdown(f"""
                <div style="display: flex; align-items: flex-start; gap: 15px; padding: 8px 0;">
                    <div style="background-color: #00C853; color: #0e1117; width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px; flex-shrink: 0;">
                        {avatar_char}
                    </div>
                    <div>
                        <span style="color: white; font-weight: bold; font-size: 15px;">{p_dict.get('full_name') or p_dict['username']}</span> 
                        <span style="color: #888; font-size: 13px;">(@{p_dict['username']})</span>
                        <p style="color: #aaa; font-size: 13px; margin: 4px 0 0 0;">{p_dict.get('bio') or 'No bio added.'}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Message 💬", key=f"chat_btn_{p_dict['username']}"):
                    st.session_state.active_chat_user = p_dict['username']
                    st.rerun()
            st.markdown("<hr style='border: 0.2px solid #21262d; margin: 5px 0;'>", unsafe_allow_html=True)
            
    else:
        peer_name = st.session_state.active_chat_user
        if st.button("⬅ Back to Inbox"):
            st.session_state.active_chat_user = None
            st.rerun()

        st.markdown(f"### Chat with @{peer_name}")
        chat_container = st.container(height=400)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                ORDER BY id ASC
            """, (username, peer_name, peer_name, username))
            messages = cursor.fetchall()
            conn.close()
            
            with chat_container:
                for msg in messages:
                    m = dict(msg)
                    if m['sender'] == username:
                        st.markdown(f"<div style='text-align: right;'><span style='background: #00C853; color: #0e1117; padding: 8px 14px; border-radius: 12px; display: inline-block; margin: 4px 0; text-align: left;'>{m['message']}</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align: left;'><span style='background: #21262d; color: white; padding: 8px 14px; border-radius: 12px; display: inline-block; margin: 4px 0;'>{m['message']}</span></div>", unsafe_allow_html=True)

        new_msg = st.chat_input(f"Message @{peer_name}...")
        if new_msg:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (sender, receiver, message, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (username, peer_name, new_msg, get_current_ist_time()))
                conn.commit()
                conn.close()
                st.rerun()

# ==============================================================================
# TAB 4: PROFILE SECTION
# ==============================================================================
elif current_tab == "Profile":
    st.markdown(f"""
        <div style="background-color: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d;">
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="background-color: #00C853; color: #0e1117; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 28px;">
                    {first_letter}
                </div>
                <div>
                    <h2 style="margin: 0; color: white;">{user.get('full_name') or username} <span style="font-size: 15px; color: #888;">(@{username})</span></h2>
                    <p style="color: #00C853; font-weight: 500; margin: 2px 0;">Account Type: {user.get('account_type', 'Student')}</p>
                    <p style="color: #ccc; margin: 5px 0 0 0;">{user.get('bio') or 'No bio added yet.'}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("⚙️ Edit Profile Settings"):
        with st.form("edit_profile"):
            new_full = st.text_input("Full Name", value=user.get('full_name', ''))
            new_bio = st.text_area("Bio", value=user.get('bio', ''))
            if st.form_submit_button("Save Profile Settings"):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET full_name = ?, bio = ? WHERE username = ?", (new_full, new_bio, username))
                    conn.commit()
                    conn.close()
                    user['full_name'] = new_full
                    user['bio'] = new_bio
                    st.success("Updated successfully!")
                    st.rerun()

st.markdown("<p style='text-align: center; color: #555; font-size: 0.7rem; letter-spacing: 2px; margin-top: 5rem;'>POWERED BY SARAAH ROBOTICS</p>", unsafe_allow_html=True)
