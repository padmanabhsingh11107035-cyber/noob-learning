import streamlit as st
import sqlite3
import datetime
import logging
import sys

# ==============================================================================
# 0. LOGGING AND SYSTEM SETUP
# ==============================================================================
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("NoobLearningApp")

st.set_page_config(
    page_title="Noob Learning Hub",
    page_icon="🎓",
    layout="centered",
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
        # Create users table with all necessary columns
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
                profile_pic BLOB
            )
        """)
        
        # Create reels/posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reels_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                caption TEXT,
                media_type TEXT,
                timestamp TEXT
            )
        """)

        # Create messages table for real-time chat
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                receiver TEXT,
                message TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

init_db()

def get_current_ist_time():
    ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(ist_offset)

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "login"
if 'nav_option' not in st.session_state:
    st.session_state.nav_option = "Home"
if 'viewing_user' not in st.session_state:
    st.session_state.viewing_user = None
if 'active_chat_user' not in st.session_state:
    st.session_state.active_chat_user = None

# ==============================================================================
# 2. CUSTOM CSS STYLING (Gen Z / Instagram Aesthetics)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Billabong&family=Inter:wght@400;500;600&display=swap');

    .stApp {
        background-color: #fafafa;
    }
    header {visibility: hidden;}

    .insta-brand-title {
        font-family: 'Billabong', cursive, sans-serif;
        font-size: 3.5rem;
        text-align: center;
        color: #111;
        margin-bottom: 0rem;
        font-weight: normal;
    }

    div.stFormSubmitButton > button {
        background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        font-weight: 600;
    }
    div.stFormSubmitButton > button:hover {
        opacity: 0.9;
        color: white !important;
    }

    .chat-bubble-user {
        background: #0095f6;
        color: white;
        padding: 10px 14px;
        border-radius: 15px 15px 2px 15px;
        margin: 5px 0;
        max-width: 70%;
        float: right;
        clear: both;
    }
    .chat-bubble-peer {
        background: #efefef;
        color: black;
        padding: 10px 14px;
        border-radius: 15px 15px 15px 2px;
        margin: 5px 0;
        max-width: 70%;
        float: left;
        clear: both;
    }

    .app-footer {
        text-align: center;
        color: #8e8e8e;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        margin-top: 4rem;
        padding-bottom: 1rem;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. AUTHENTICATION & ONBOARDING SCREEN
# ==============================================================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='insta-brand-title'>Noob Learning</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666; font-size: 0.9rem; margin-bottom: 25px;'>Powered by Saraah Robotics</p>", unsafe_allow_html=True)
        
        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                username_input = st.text_input("Username", placeholder="Username or email")
                password_input = st.text_input("Password", type="password", placeholder="Password")
                submitted = st.form_submit_button("Log In", use_container_width=True)
                
                if submitted:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username_input.strip(), password_input))
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
                st.markdown("<h4 style='text-align: center; color: #444;'>Join the Community</h4>", unsafe_allow_html=True)
                new_username = st.text_input("Username", placeholder="Choose a unique username")
                new_password = st.text_input("Password", type="password", placeholder="Create a password")
                full_name = st.text_input("Full Name", placeholder="Your full name")
                bio = st.text_area("Bio", placeholder="Tell us about yourself...")
                age = st.number_input("Age", min_value=5, max_value=120, value=18)
                gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
                birth_date = st.text_input("Birth Date", placeholder="DD/MM/YYYY")
                account_type = st.selectbox("Account Type", ["Student", "Creator", "Robotics Enthusiast", "Teacher"])
                
                signup_submitted = st.form_submit_button("Sign Up", use_container_width=True)
                
                if signup_submitted:
                    if new_username and new_password:
                        conn = get_db_connection()
                        if conn:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO users (username, password, full_name, bio, age, gender, birth_date, account_type)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (new_username.strip(), new_password, full_name, bio, age, gender, birth_date, account_type))
                                conn.commit()
                                conn.close()
                                st.success("Account created successfully! Please log in.")
                                st.session_state.auth_mode = "login"
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Username already taken. Choose another.")
                                conn.close()
                    else:
                        st.warning("Please fill in username and password.")
                        
            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

        st.markdown("<p class='app-footer'>Noob Learning Hub</p>", unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 4. MAIN APP DASHBOARD
# ==============================================================================
user = st.session_state.user

st.markdown("<h2 style='text-align: center; font-family: \"Billabong\", cursive; font-size: 3rem;'>Noob Learning Hub</h2>", unsafe_allow_html=True)

# Top Bar / Log Out
col_l, col_r = st.columns([4, 1])
with col_r:
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

# Navigation Bar
nav_cols = st.columns(5)
with nav_cols[0]:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.nav_option = "Home"
        st.session_state.viewing_user = None
        st.session_state.active_chat_user = None
        st.rerun()
with nav_cols[1]:
    if st.button("🎬 Reels", use_container_width=True):
        st.session_state.nav_option = "Reels"
        st.session_state.viewing_user = None
        st.session_state.active_chat_user = None
        st.rerun()
with nav_cols[2]:
    if st.button("➕ Post", use_container_width=True):
        st.session_state.nav_option = "Post"
        st.session_state.viewing_user = None
        st.session_state.active_chat_user = None
        st.rerun()
with nav_cols[3]:
    if st.button("💬 Chat", use_container_width=True):
        st.session_state.nav_option = "Chat"
        st.session_state.viewing_user = None
        st.rerun()
with nav_cols[4]:
    if st.button("👤 Profile", use_container_width=True):
        st.session_state.nav_option = "Profile"
        st.session_state.viewing_user = user['username']
        st.session_state.active_chat_user = None
        st.rerun()

st.markdown("<hr style='margin: 10px 0 20px 0;'>", unsafe_allow_html=True)
current_tab = st.session_state.get('nav_option', 'Home')

# --- TAB 1: HOME FEED ---
if current_tab == "Home":
    st.write("### Feed")
    st.info("Welcome back! Check out what your peers are sharing in Noob Learning Hub.")
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reels_posts ORDER BY id DESC")
        posts = cursor.fetchall()
        conn.close()
        
        if not posts:
            st.write("No posts or reels yet. Be the first to share something!")
        for p in posts:
            with st.container():
                st.markdown(f"**@ {p['username']}**")
                st.write(p['caption'])
                st.markdown("<hr style='border: 0.5px solid #eee;'>", unsafe_allow_html=True)

# --- TAB 2: REELS HUB ---
elif current_tab == "Reels":
    st.write("### Reels Watcher")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reels_posts ORDER BY id DESC")
        reels = cursor.fetchall()
        conn.close()
        
        if not reels:
            st.info("No reels available right now. Create one from the Post tab!")
        for r in reels:
            st.markdown(f"🎬 **@{r['username']}**")
            st.markdown(f"> {r['caption']}")
            st.markdown("---")

# --- TAB 3: CREATE POST / REEL ---
elif current_tab == "Post":
    st.write("### Create New Post or Reel")
    with st.form("create_post_form"):
        caption = st.text_area("Write a caption or description...")
        media_type = st.selectbox("Content Type", ["Post", "Reel"])
        submitted_post = st.form_submit_button("Publish Content", use_container_width=True)
        
        if submitted_post:
            if caption.strip():
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO reels_posts (username, caption, media_type, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (user['username'], caption, media_type, str(get_current_ist_time())))
                    conn.commit()
                    conn.close()
                    st.success("Successfully published!")
                    st.rerun()
            else:
                st.warning("Please add a caption.")

# --- TAB 4: CHAT HUB ---
elif current_tab == "Chat":
    conn = get_db_connection()
    all_users = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username != ?", (user['username'],))
        all_users = cursor.fetchall()
        conn.close()

    if st.session_state.active_chat_user is None:
        st.write("### Direct Messages")
        if not all_users:
            st.info("No other users registered yet.")
        for u in all_users:
            col_c1, col_c2 = st.columns([3, 1])
            with col_c1:
                st.markdown(f"💬 **@{u['username']}** ({u['full_name'] or 'Member'})")
            with col_c2:
                if st.button("Chat", key=f"chat_with_{u['user_id']}"):
                    st.session_state.active_chat_user = u['username']
                    st.rerun()
    else:
        peer = st.session_state.active_chat_user
        if st.button("⬅ Back to Inbox"):
            st.session_state.active_chat_user = None
            st.rerun()

        st.markdown(f"### Chat with @{peer}")
        chat_box = st.container(height=350)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                ORDER BY id ASC
            """, (user['username'], peer, peer, user['username']))
            msgs = cursor.fetchall()
            conn.close()
            
            with chat_box:
                for m in msgs:
                    if m['sender'] == user['username']:
                        st.markdown(f"<div class='chat-bubble-user'>{m['message']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-bubble-peer'>{m['message']}</div>", unsafe_allow_html=True)

        user_message = st.chat_input(f"Message @{peer}...")
        if user_message:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (sender, receiver, message, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (user['username'], peer, user_message, str(get_current_ist_time())))
                conn.commit()
                conn.close()
                st.rerun()

# --- TAB 5: PROFILE & SETTINGS HUB ---
elif current_tab == "Profile":
    target_username = st.session_state.viewing_user or user['username']
    
    conn = get_db_connection()
    profile_data = None
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (target_username,))
        row = cursor.fetchone()
        if row:
            profile_data = dict(row)
        conn.close()

    if profile_data:
        is_owner = (profile_data['username'] == user['username'])
        
        col_img, col_info = st.columns([1, 2])
        with col_img:
            st.markdown("<h1>👤</h1>", unsafe_allow_html=True)
        with col_info:
            st.markdown(f"### @{profile_data['username']}")
            st.markdown(f"**{profile_data.get('full_name') or profile_data['username']}** • *{profile_data.get('account_type', 'Member')}*")
            st.markdown(f"{profile_data.get('bio') or 'No bio added.'}")

        if is_owner:
            with st.expander("⚙️ Edit Profile Settings"):
                with st.form("update_profile_form"):
                    new_full_name = st.text_input("Full Name", value=profile_data.get('full_name', ''))
                    new_bio = st.text_area("Bio", value=profile_data.get('bio', ''))
                    new_age = st.number_input("Age", min_value=5, max_value=120, value=int(profile_data.get('age') or 18))
                    
                    if st.form_submit_button("Save Changes"):
                        conn = get_db_connection()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE users SET full_name = ?, bio = ?, age = ? WHERE user_id = ?
                            """, (new_full_name, new_bio, new_age, user['user_id']))
                            conn.commit()
                            conn.close()
                            
                            user['full_name'] = new_full_name
                            user['bio'] = new_bio
                            user['age'] = new_age
                            
                            st.success("Profile updated successfully!")
                            st.rerun()

        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.write("🖼️ **User Posts & Reels**")
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reels_posts WHERE username = ? ORDER BY id DESC", (target_username,))
            user_reels = cursor.fetchall()
            conn.close()
            
            if not user_reels:
                st.info("This user has not posted anything yet.")
            for ur in user_reels:
                st.markdown(f"• {ur['caption']} *({ur['media_type']})*")

st.markdown("<p class='app-footer'>POWERED BY SARAAH ROBOTICS</p>", unsafe_allow_html=True)
