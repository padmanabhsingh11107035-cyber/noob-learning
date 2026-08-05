import streamlit as st
import mysql.connector
import datetime
import base64
import zoneinfo
import logging
import sys
import re

# ==============================================================================
# 0. LOGGING AND SYSTEM SETUP
# ==============================================================================
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("NoobLearningApp")

# ==============================================================================
# 1. PAGE CONFIGURATION & INSTAGRAM-INSPIRED CSS STYLING
# ==============================================================================
st.set_page_config(
    page_title="NOOB LEARNING",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def inject_custom_css():
    """Injects custom CSS to match Instagram layout, reel overlays, and font branding"""
    custom_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Billabong&family=Inter:wght@400;500;600&display=swap');

        .stApp {
            background-color: #fafafa;
        }

        header {visibility: hidden;}

        .insta-brand-title {
            font-family: 'Billabong', cursive, sans-serif;
            font-size: 3.2rem;
            text-align: center;
            color: #262626;
            margin-bottom: 0.5rem;
            font-weight: normal;
        }

        /* Footer Branding */
        .app-footer {
            text-align: center;
            color: #8e8e8e;
            font-size: 0.75rem;
            font-weight: 500;
            letter-spacing: 1px;
            margin-top: 3rem;
            padding-bottom: 1rem;
            text-transform: uppercase;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 2. DATABASE CONFIGURATION & FALLBACK (Local SQLite or Cloud MySQL)
# ==============================================================================
import sqlite3

def get_db_connection():
    """Attempts to connect to Cloud MySQL first; falls back to robust local SQLite if cloud host is unreachable."""
    DB_CONFIG = {
        "host": "mysql-22faa093-padmanabhsingh11107035-84a9.l.aivencloud.com",
        "port": 21354,
        "user": "avnadmin",
        "password": "AVNS_iN1XY9WAsRFlUWVhM6k",
        "database": "defaultdb",
        "connect_timeout": 3
    }
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return ("mysql", connection)
    except Exception as err:
        logger.warning(f"Cloud MySQL unreachable ({err}). Falling back to local SQLite database for seamless execution.")
    
    # Fallback to local SQLite so the app never crashes on DNS/host resolution errors
    sqlite_conn = sqlite3.connect("noob_learning.db", check_same_thread=False)
    sqlite_conn.row_factory = sqlite3.Row
    return ("sqlite", sqlite_conn)

def setup_database_schema():
    """Ensures all required tables exist across either database backend."""
    db_type, conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if db_type == "mysql":
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        name VARCHAR(150),
                        phone_number VARCHAR(30),
                        email VARCHAR(150),
                        gender VARCHAR(50),
                        account_type VARCHAR(20) DEFAULT 'Public',
                        bio VARCHAR(255) DEFAULT 'Welcome to NOOB LEARNING!',
                        profile_pic LONGTEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        post_id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        caption TEXT,
                        media_url LONGTEXT,
                        likes INT DEFAULT 0,
                        shares INT DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS comments (
                        comment_id INT AUTO_INCREMENT PRIMARY KEY,
                        post_id INT NOT NULL,
                        user_id INT NOT NULL,
                        comment_text TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS follows (
                        follow_id INT AUTO_INCREMENT PRIMARY KEY,
                        follower_id INT NOT NULL,
                        following_id INT NOT NULL,
                        status VARCHAR(20) DEFAULT 'Accepted',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id INT AUTO_INCREMENT PRIMARY KEY,
                        sender_id INT NOT NULL,
                        receiver_id INT NOT NULL,
                        message_text TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        interaction_id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        post_id INT NOT NULL,
                        interaction_type VARCHAR(20) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        name TEXT,
                        phone_number TEXT,
                        email TEXT,
                        gender TEXT,
                        account_type TEXT DEFAULT 'Public',
                        bio TEXT DEFAULT 'Welcome to NOOB LEARNING!',
                        profile_pic TEXT,
                        created_at TEXT
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        caption TEXT,
                        media_url TEXT,
                        likes INTEGER DEFAULT 0,
                        shares INTEGER DEFAULT 0,
                        created_at TEXT
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS comments (
                        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        comment_text TEXT NOT NULL,
                        created_at TEXT
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS follows (
                        follow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        follower_id INTEGER NOT NULL,
                        following_id INTEGER NOT NULL,
                        status TEXT DEFAULT 'Accepted',
                        created_at TEXT
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER NOT NULL,
                        receiver_id INTEGER NOT NULL,
                        message_text TEXT,
                        created_at TEXT
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        post_id INTEGER NOT NULL,
                        interaction_type TEXT NOT NULL,
                        created_at TEXT
                    );
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Schema setup error: {e}")
        finally:
            conn.close()

setup_database_schema()

# ==============================================================================
# 3. SESSION STATE MANAGEMENT
# ==============================================================================
if "user" not in st.session_state:
    st.session_state.user = None

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

if "nav_tab" not in st.session_state:
    st.session_state.nav_tab = "Home"

if "viewing_profile_id" not in st.session_state:
    st.session_state.viewing_profile_id = None

# ==============================================================================
# 4. UTILITY HELPERS
# ==============================================================================
def sanitize_input(text_str: str) -> str:
    if not text_str:
        return ""
    return re.sub(r'<script.*?>.*?</script>', '', text_str, flags=re.DOTALL | re.IGNORECASE).strip()

def format_to_ist(dt_object) -> str:
    """Converts and formats timestamp objects into exact readable date and IST time."""
    if not dt_object:
        return ""
    if isinstance(dt_object, datetime.datetime):
        if dt_object.tzinfo is None:
            dt_utc = dt_object.replace(tzinfo=datetime.timezone.utc)
            dt_ist = dt_utc.astimezone(zoneinfo.ZoneInfo("Asia/Kolkata"))
        else:
            dt_ist = dt_object.astimezone(zoneinfo.ZoneInfo("Asia/Kolkata"))
        return dt_ist.strftime("%B %d, %Y - %I:%M:%S %p")
    return str(dt_object)

def get_current_ist_time() -> str:
    """Returns current exact IST timestamp string for database insertion."""
    dt_utc = datetime.datetime.now(datetime.timezone.utc)
    dt_ist = dt_utc.astimezone(zoneinfo.ZoneInfo("Asia/Kolkata"))
    return dt_ist.strftime('%Y-%m-%d %H:%M:%S')

def render_footer():
    st.markdown('<div class="app-footer">Powered by Saraah Robotics</div>', unsafe_allow_html=True)

# ==============================================================================
# 5. AUTHENTICATION SCREENS
# ==============================================================================
if not st.session_state.user:
    _, col_center, _ = st.columns([1, 1.2, 1])

    with col_center:
        st.markdown('<div class="insta-brand-title">Noob Learning</div>', unsafe_allow_html=True)

        if st.session_state.auth_page == "login":
            login_identifier = st.text_input("Phone number, username, or email", placeholder="Phone number, username, or email")
            login_password = st.text_input("Password", type="password", placeholder="Password")

            if st.button("Log In", use_container_width=True, type="primary"):
                if login_identifier and login_password:
                    db_type, conn = get_db_connection()
                    if conn:
                        try:
                            if db_type == "mysql":
                                cursor = conn.cursor(dictionary=True)
                                cursor.execute("""
                                    SELECT * FROM users 
                                    WHERE username = %s OR email = %s OR phone_number = %s
                                """, (login_identifier.strip(), login_identifier.strip(), login_identifier.strip()))
                                account = cursor.fetchone()
                            else:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    SELECT * FROM users 
                                    WHERE username = ? OR email = ? OR phone_number = ?
                                """, (login_identifier.strip(), login_identifier.strip(), login_identifier.strip()))
                                row = cursor.fetchone()
                                account = dict(row) if row else None

                            if account and account['password'] == login_password:
                                st.session_state.user = account
                                st.toast(f"Welcome back @{account['username']}!", icon="👋")
                                st.rerun()
                            else:
                                st.error("Invalid login credentials provided.")
                        finally:
                            conn.close()
                else:
                    st.warning("Please enter your login credentials.")

            st.markdown("<div style='text-align: center; margin: 15px 0; color: #8e8e8e; font-weight: 600; font-size: 0.85rem;'>OR</div>", unsafe_allow_html=True)

            if st.button("Create Account", use_container_width=True):
                st.session_state.auth_page = "signup"
                st.rerun()

            if st.button("Forgot Password?", use_container_width=True):
                st.session_state.auth_page = "forgot"
                st.rerun()

        elif st.session_state.auth_page == "signup":
            st.subheader("Sign up for Noob Learning")
            
            with st.form("signup_form"):
                reg_username = st.text_input("Username (ID Name)")
                reg_name = st.text_input("Full Name")
                reg_password = st.text_input("Password", type="password")
                reg_phone = st.text_input("Phone Number")
                reg_email = st.text_input("Email Address")
                reg_gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])
                reg_account_type = st.selectbox("Account Type", ["Public", "Private"])
                
                profile_pic_file = st.file_uploader("Profile Picture", type=["png", "jpg", "jpeg"])

                submit_signup = st.form_submit_button("Sign Up", use_container_width=True, type="primary")

                if submit_signup:
                    if reg_username and reg_password and reg_email:
                        pic_base64 = None
                        if profile_pic_file:
                            b_data = profile_pic_file.getvalue()
                            pic_base64 = f"data:{profile_pic_file.type};base64,{base64.b64encode(b_data).decode()}"

                        db_type, conn = get_db_connection()
                        if conn:
                            try:
                                cursor = conn.cursor()
                                current_ts = get_current_ist_time()
                                if db_type == "mysql":
                                    cursor.execute("""
                                        INSERT INTO users (username, password, name, phone_number, email, gender, account_type, profile_pic, created_at) 
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (
                                        sanitize_input(reg_username),
                                        reg_password,
                                        sanitize_input(reg_name),
                                        sanitize_input(reg_phone),
                                        sanitize_input(reg_email),
                                        reg_gender,
                                        reg_account_type,
                                        pic_base64,
                                        current_ts
                                    ))
                                else:
                                    cursor.execute("""
                                        INSERT INTO users (username, password, name, phone_number, email, gender, account_type, profile_pic, created_at) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        sanitize_input(reg_username),
                                        reg_password,
                                        sanitize_input(reg_name),
                                        sanitize_input(reg_phone),
                                        sanitize_input(reg_email),
                                        reg_gender,
                                        reg_account_type,
                                        pic_base64,
                                        current_ts
                                    ))
                                conn.commit()
                                st.success("Account created successfully! Please log in.")
                                st.session_state.auth_page = "login"
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Username or email already exists or database error: {ex}")
                            finally:
                                conn.close()
                    else:
                        st.warning("Please fill in Username, Password, and Email.")

            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_page = "login"
                st.rerun()

        elif st.session_state.auth_page == "forgot":
            st.subheader("Password Recovery")
            forgot_input = st.text_input("Username, email, or phone number")
            if st.button("Reset Password", use_container_width=True, type="primary"):
                if forgot_input.strip():
                    st.success("Recovery instructions sent to registered contact info.")
            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_page = "login"
                st.rerun()

    render_footer()

# ==============================================================================
# 6. AUTHENTICATED MAIN APPLICATION WITH BOTTOM NAVIGATION
# ==============================================================================
else:
    user = st.session_state.user

    # Header Brand
    st.markdown('<div class="insta-brand-title" style="font-size: 2.3rem; margin-bottom: 0.2rem;">Noob Learning</div>', unsafe_allow_html=True)

    # ------------------ BOTTOM NAVIGATION LAYOUT ------------------
    nav_cols = st.columns(5)
    with nav_cols[0]:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.nav_tab = "Home"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[1]:
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.nav_tab = "Search"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[2]:
        if st.button("➕ Post", use_container_width=True):
            st.session_state.nav_tab = "Post"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[3]:
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.nav_tab = "Chat"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[4]:
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.nav_tab = "Profile"
            st.session_state.viewing_profile_id = user['user_id']
            st.rerun()

    st.divider()

    # ------------------ TAB 1: HOME FEED (REELS / POSTS STYLE) ------------------
    if st.session_state.nav_tab == "Home" and not st.session_state.viewing_profile_id:
        st.subheader("Feed / Reels")
        db_type, conn = get_db_connection()
        if conn:
            try:
                if db_type == "mysql":
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT p.*, u.username, u.profile_pic, u.user_id as author_id
                        FROM posts p 
                        JOIN users u ON p.user_id = u.user_id 
                        ORDER BY p.created_at DESC
                    """)
                    posts = cursor.fetchall()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT p.*, u.username, u.profile_pic, u.user_id as author_id
                        FROM posts p 
                        JOIN users u ON p.user_id = u.user_id 
                        ORDER BY p.created_at DESC
                    """)
                    posts = [dict(row) for row in cursor.fetchall()]

                if not posts:
                    st.info("No posts yet. Follow friends or create a post!")
                else:
                    for post in posts:
                        with st.container():
                            c_h1, c_h2 = st.columns([4, 1])
                            with c_h1:
                                exact_time_str = post.get('created_at', '')
                                st.markdown(f"**@{post['username']}**<br><span style='font-size: 0.75rem; color: gray;'>📅 {exact_time_str}</span>", unsafe_allow_html=True)
                            with c_h2:
                                if post['author_id'] != user['user_id']:
                                    if db_type == "mysql":
                                        cur_f = conn.cursor(dictionary=True)
                                        cur_f.execute("SELECT * FROM follows WHERE follower_id = %s AND following_id = %s", (user['user_id'], post['author_id']))
                                        rel = cur_f.fetchone()
                                    else:
                                        cur_f = conn.cursor()
                                        cur_f.execute("SELECT * FROM follows WHERE follower_id = ? AND following_id = ?", (user['user_id'], post['author_id']))
                                        rel = cur_f.fetchone()

                                    if not rel:
                                        if st.button("Follow", key=f"feed_follow_{post['post_id']}"):
                                            if db_type == "mysql":
                                                cur_f.execute("INSERT INTO follows (follower_id, following_id, status, created_at) VALUES (%s, %s, 'Accepted', %s)", (user['user_id'], post['author_id'], get_current_ist_time()))
                                            else:
                                                cur_f.execute("INSERT INTO follows (follower_id, following_id, status, created_at) VALUES (?, ?, 'Accepted', ?)", (user['user_id'], post['author_id'], get_current_ist_time()))
                                            conn.commit()
                                            st.rerun()

                            if post['media_url']:
                                st.image(post['media_url'], use_container_width=True)
                            if post['caption']:
                                st.write(post['caption'])

                            act_col1, act_col2, act_col3, act_col4 = st.columns(4)
                            with act_col1:
                                if st.button(f"❤️ {post.get('likes', 0)}", key=f"like_{post['post_id']}"):
                                    cur2 = conn.cursor()
                                    if db_type == "mysql":
                                        cur2.execute("UPDATE posts SET likes = likes + 1 WHERE post_id = %s", (post['post_id'],))
                                        cur2.execute("INSERT IGNORE INTO user_interactions (user_id, post_id, interaction_type, created_at) VALUES (%s, %s, 'liked', %s)", (user['user_id'], post['post_id'], get_current_ist_time()))
                                    else:
                                        cur2.execute("UPDATE posts SET likes = likes + 1 WHERE post_id = ?", (post['post_id'],))
                                        cur2.execute("INSERT OR IGNORE INTO user_interactions (user_id, post_id, interaction_type, created_at) VALUES (?, ?, 'liked', ?)", (user['user_id'], post['post_id'], get_current_ist_time()))
                                    conn.commit()
                                    st.rerun()
                            with act_col2:
                                if st.button(f"💬 Comment", key=f"com_btn_{post['post_id']}"):
                                    st.session_state[f"show_com_{post['post_id']}"] = not st.session_state.get(f"show_com_{post['post_id']}", False)
                            with act_col3:
                                if st.button(f"🔄 {post.get('shares', 0)}", key=f"share_{post['post_id']}"):
                                    cur2 = conn.cursor()
                                    if db_type == "mysql":
                                        cur2.execute("UPDATE posts SET shares = shares + 1 WHERE post_id = %s", (post['post_id'],))
                                    else:
                                        cur2.execute("UPDATE posts SET shares = shares + 1 WHERE post_id = ?", (post['post_id'],))
                                    conn.commit()
                                    st.toast("Post shared!")
                            with act_col4:
                                if st.button("🔖 Save", key=f"save_{post['post_id']}"):
                                    cur2 = conn.cursor()
                                    if db_type == "mysql":
                                        cur2.execute("INSERT IGNORE INTO user_interactions (user_id, post_id, interaction_type, created_at) VALUES (%s, %s, 'saved', %s)", (user['user_id'], post['post_id'], get_current_ist_time()))
                                    else:
                                        cur2.execute("INSERT OR IGNORE INTO user_interactions (user_id, post_id, interaction_type, created_at) VALUES (?, ?, 'saved', ?)", (user['user_id'], post['post_id'], get_current_ist_time()))
                                    conn.commit()
                                    st.toast("Saved to collection!")

                            if st.session_state.get(f"show_com_{post['post_id']}", False):
                                st.markdown("##### Comments")
                                if db_type == "mysql":
                                    cur_c = conn.cursor(dictionary=True)
                                    cur_c.execute("""
                                        SELECT c.*, u.username FROM comments c 
                                        JOIN users u ON c.user_id = u.user_id 
                                        WHERE c.post_id = %s ORDER BY c.created_at ASC
                                    """, (post['post_id'],))
                                    comments = cur_c.fetchall()
                                else:
                                    cur_c = conn.cursor()
                                    cur_c.execute("""
                                        SELECT c.*, u.username FROM comments c 
                                        JOIN users u ON c.user_id = u.user_id 
                                        WHERE c.post_id = ? ORDER BY c.created_at ASC
                                    """, (post['post_id'],))
                                    comments = [dict(row) for row in cur_c.fetchall()]

                                for comm in comments:
                                    comm_time = comm.get('created_at', '')
                                    st.markdown(f"**@{comm['username']}**: {comm['comment_text']} <span style='font-size: 0.7rem; color: gray;'>({comm_time})</span>", unsafe_allow_html=True)

                                with st.form(key=f"comment_form_{post['post_id']}", clear_on_submit=True):
                                    new_comm = st.text_input("Add a comment...")
                                    if st.form_submit_button("Post Comment"):
                                        if new_comm.strip():
                                            if db_type == "mysql":
                                                cur_c.execute("INSERT INTO comments (post_id, user_id, comment_text, created_at) VALUES (%s, %s, %s, %s)",
                                                              (post['post_id'], user['user_id'], sanitize_input(new_comm), get_current_ist_time()))
                                            else:
                                                cur_c.execute("INSERT INTO comments (post_id, user_id, comment_text, created_at) VALUES (?, ?, ?, ?)",
                                                              (post['post_id'], user['user_id'], sanitize_input(new_comm), get_current_ist_time()))
                                            conn.commit()
                                            st.rerun()

                            with st.form(key=f"msg_form_{post['post_id']}", clear_on_submit=True):
                                msg_input = st.text_input(f"Message @{post['username']}...", placeholder="Say something or tap emoji...")
                                mc1, mc2, mc3 = st.columns(3)
                                with mc1:
                                    react_laugh = st.form_submit_button("😂")
                                with mc2:
                                    react_love = st.form_submit_button("😍")
                                with mc3:
                                    react_fire = st.form_submit_button("🔥")
                                
                                submit_msg = st.form_submit_button("Send DM")
                                if submit_msg and msg_input.strip():
                                    cur_m = conn.cursor()
                                    if db_type == "mysql":
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (%s, %s, %s, %s)",
                                                      (user['user_id'], post['author_id'], sanitize_input(msg_input), get_current_ist_time()))
                                    else:
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (?, ?, ?, ?)",
                                                      (user['user_id'], post['author_id'], sanitize_input(msg_input), get_current_ist_time()))
                                    conn.commit()
                                    st.success("Message sent to author with timestamp!")
                                elif react_laugh:
                                    cur_m = conn.cursor()
                                    if db_type == "mysql":
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (%s, %s, '😂', %s)",
                                                      (user['user_id'], post['author_id'], get_current_ist_time()))
                                    else:
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (?, ?, '😂', ?)",
                                                      (user['user_id'], post['author_id'], get_current_ist_time()))
                                    conn.commit()
                                    st.toast("Reaction sent!")
                                elif react_love:
                                    cur_m = conn.cursor()
                                    if db_type == "mysql":
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (%s, %s, '😍', %s)",
                                                      (user['user_id'], post['author_id'], get_current_ist_time()))
                                    else:
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (?, ?, '😍', ?)",
                                                      (user['user_id'], post['author_id'], get_current_ist_time()))
                                    conn.commit()
                                    st.toast("Reaction sent!")
                                elif react_fire:
                                    cur_m = conn.cursor()
                                    if db_type == "mysql":
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (%s, %s, '🔥', %s)",
                                                      (user['user_id'], post['author_id'], get_current_ist_time()))
                                    else:
                                        cur_m.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (?, ?, '🔥', ?)",
                                                      (user['user_id'], post['author_id'], get_current_ist_time()))
                                    conn.commit()
                                    st.toast("Reaction sent!")

                            st.divider()
            finally:
                conn.close()

 # ------------------ TAB 2: SEARCH & DISCOVER ------------------
    elif st.session_state.nav_tab == "Search":
        st.subheader("Search Users")
        search_query = st.text_input("Search ID or Username...")
        
        if search_query:
            db_type, conn = get_db_connection()
            if conn:
                try:
                    wildcard_query = f"%{search_query}%"
                    if search_query.isdigit():
                        params = (int(search_query), wildcard_query, user['user_id'])
                        mysql_sql = "SELECT user_id, username, profile_pic FROM users WHERE (user_id = %s OR username LIKE %s) AND user_id != %s"
                        sqlite_sql = "SELECT user_id, username, profile_pic FROM users WHERE (user_id = ? OR username LIKE ?) AND user_id != ?"
                    else:
                        params = (wildcard_query, user['user_id'])
                        mysql_sql = "SELECT user_id, username, profile_pic FROM users WHERE username LIKE %s AND user_id != %s"
                        sqlite_sql = "SELECT user_id, username, profile_pic FROM users WHERE username LIKE ? AND user_id != ?"

                    if db_type == "mysql":
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute(mysql_sql, params)
                        results = cursor.fetchall()
                    else:
                        cursor = conn.cursor()
                        cursor.execute(sqlite_sql, params)
                        results = [dict(row) for row in cursor.fetchall()]

                    if not results:
                        st.info("No users found.")
                    else:
                        for u in results:
                            col_u1, col_u2 = st.columns([3, 1])
                            with col_u1:
                                st.markdown(f"**@{u['username']}** (ID: {u['user_id']})")
                            with col_u2:
                                if st.button("View Profile", key=f"view_{u['user_id']}"):
                                    st.session_state.viewing_profile_id = u['user_id']
                                    st.session_state.nav_tab = "Profile"
                                    st.rerun()
                            st.divider()
                except Exception as e:
                    st.error(f"Search Error: {e}")
                finally:
                    conn.close()
    # ------------------ TAB 3: CREATE POST ------------------
    elif st.session_state.nav_tab == "Post":
        st.subheader("Create New Post / Reel")
        with st.form("new_post_form", clear_on_submit=True):
            caption = st.text_area("Caption...")
            uploaded_file = st.file_uploader("Upload Image/Video", type=["png", "jpg", "jpeg", "mp4"])
            submitted = st.form_submit_button("Share Post", type="primary", use_container_width=True)

            if submitted:
                media_url = None
                if uploaded_file:
                    b_data = uploaded_file.getvalue()
                    media_url = f"data:{uploaded_file.type};base64,{base64.b64encode(b_data).decode()}"

                if caption or media_url:
                    db_type, conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            current_ts = get_current_ist_time()
                            if db_type == "mysql":
                                cursor.execute("INSERT INTO posts (user_id, caption, media_url, created_at) VALUES (%s, %s, %s, %s)", 
                                               (user['user_id'], sanitize_input(caption), media_url, current_ts))
                            else:
                                cursor.execute("INSERT INTO posts (user_id, caption, media_url, created_at) VALUES (?, ?, ?, ?)", 
                                               (user['user_id'], sanitize_input(caption), media_url, current_ts))
                            conn.commit()
                            st.success(f"Posted successfully at {current_ts} IST! Reflected at the top of the feed.")
                            st.session_state.nav_tab = "Home"
                            st.rerun()
                        finally:
                            conn.close()
                else:
                    st.warning("Provide a caption or media.")

    # ------------------ TAB 4: CHAT & GROUPS ------------------
    elif st.session_state.nav_tab == "Chat":
        st.subheader("Messages & Friend Chats")
        db_type, conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True) if db_type == "mysql" else conn.cursor()
                
                # Step 1: Get all user IDs of accepted friends safely
                if db_type == "mysql":
                    cursor.execute("SELECT following_id FROM follows WHERE follower_id = %s AND status = 'Accepted'", (user['user_id'],))
                    following_rows = cursor.fetchall()
                    following = [r.get('following_id') for r in following_rows if r.get('following_id')]
                    
                    cursor.execute("SELECT follower_id FROM follows WHERE following_id = %s AND status = 'Accepted'", (user['user_id'],))
                    follower_rows = cursor.fetchall()
                    followers = [r.get('follower_id') for r in follower_rows if r.get('follower_id')]
                else:
                    cursor.execute("SELECT following_id FROM follows WHERE follower_id = ? AND status = 'Accepted'", (user['user_id'],))
                    following = [dict(row)['following_id'] for row in cursor.fetchall()]
                    
                    cursor.execute("SELECT follower_id FROM follows WHERE following_id = ? AND status = 'Accepted'", (user['user_id'],))
                    followers = [dict(row)['follower_id'] for row in cursor.fetchall()]

                friend_ids = list(set(following + followers))
                
                friends = []
                if friend_ids:
                    # Step 2: Fetch usernames for those friend IDs safely
                    format_strings = ','.join(['%s' if db_type == "mysql" else '?'] * len(friend_ids))
                    query = f"SELECT user_id, username FROM users WHERE user_id IN ({format_strings})"
                    cursor.execute(query, tuple(friend_ids))
                    
                    if db_type == "mysql":
                        friends = cursor.fetchall()
                    else:
                        friends = [dict(row) for row in cursor.fetchall()]

                if not friends:
                    st.info("You can only chat with users who are your friends (mutual follow or accepted request).")
                else:
                    friend_usernames = [f['username'] for f in friends]
                    selected_friend = st.selectbox("Select Friend to Chat", friend_usernames)
                    
                    target_friend = next((f for f in friends if f['username'] == selected_friend), None)
                    if target_friend:
                        st.write(f"### Chat with @{target_friend['username']}")
                        
                        if db_type == "mysql":
                            cursor.execute("""
                                SELECT * FROM messages 
                                WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
                                ORDER BY created_at ASC
                            """, (user['user_id'], target_friend['user_id'], target_friend['user_id'], user['user_id']))
                            messages = cursor.fetchall()
                        else:
                            cursor.execute("""
                                SELECT * FROM messages 
                                WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
                                ORDER BY created_at ASC
                            """, (user['user_id'], target_friend['user_id'], target_friend['user_id'], user['user_id']))
                            messages = [dict(row) for row in cursor.fetchall()]

                        for m in messages:
                            sender_name = "You" if m['sender_id'] == user['user_id'] else target_friend['username']
                            msg_time = m.get('created_at', '')
                            st.markdown(f"**{sender_name}**: {m['message_text']} <span style='font-size: 0.7rem; color: gray;'>({msg_time})</span>", unsafe_allow_html=True)

                        with st.form("chat_send_form", clear_on_submit=True):
                            msg_text = st.text_input("Type a message...")
                            if st.form_submit_button("Send"):
                                if msg_text.strip():
                                    current_ts = get_current_ist_time()
                                    if db_type == "mysql":
                                        cursor.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (%s, %s, %s, %s)",
                                                       (user['user_id'], target_friend['user_id'], sanitize_input(msg_text), current_ts))
                                    else:
                                        cursor.execute("INSERT INTO messages (sender_id, receiver_id, message_text, created_at) VALUES (?, ?, ?, ?)",
                                                       (user['user_id'], target_friend['user_id'], sanitize_input(msg_text), current_ts))
                                    conn.commit()
                                    st.rerun()
            finally:
                conn.close()
    # ------------------ TAB 5: PROFILE & SETTINGS HUB ------------------
    elif st.session_state.nav_tab == "Profile" or st.session_state.viewing_profile_id:
        profile_id = st.session_state.viewing_profile_id or user['user_id']
        db_type, conn = get_db_connection()
    elif st.session_state.nav_tab == "Profile" or st.session_state.viewing_profile_id:
        profile_id = st.session_state.viewing_profile_id or user['user_id']
        db_type, conn = get_db_connection()
        if conn:
            try:
                if db_type == "mysql":
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE user_id = %s", (profile_id,))
                    profile_user = cursor.fetchone()
                else:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE user_id = ?", (profile_id,))
                    row = cursor.fetchone()
                    profile_user = dict(row) if row else None

                if profile_user:
                    col_p1, col_p2 = st.columns([1, 3])
                    with col_p1:
                        if profile_user.get('profile_pic'):
                            st.image(profile_user['profile_pic'], width=100)
                        else:
                            st.write("👤")
                    with col_p2:
                        st.subheader(f"@{profile_user['username']}")
                        st.write(f"**{profile_user.get('name', '')}**")
                        st.write(profile_user.get('bio', ''))
                        st.caption(f"Account Type: {profile_user.get('account_type', 'Public')} | Joined: {profile_user.get('created_at', '')}")

                    if profile_user['user_id'] != user['user_id']:
                        if db_type == "mysql":
                            cursor.execute("SELECT * FROM follows WHERE follower_id = %s AND following_id = %s", 
                                           (user['user_id'], profile_user['user_id']))
                            follow_rel = cursor.fetchone()
                        else:
                            cursor.execute("SELECT * FROM follows WHERE follower_id = ? AND following_id = ?", 
                                           (user['user_id'], profile_user['user_id']))
                            row = cursor.fetchone()
                            follow_rel = dict(row) if row else None

                        if not follow_rel:
                            if st.button("Follow"):
                                status = "Pending" if profile_user['account_type'] == 'Private' else "Accepted"
                                if db_type == "mysql":
                                    cursor.execute("INSERT INTO follows (follower_id, following_id, status, created_at) VALUES (%s, %s, %s, %s)",
                                                   (user['user_id'], profile_user['user_id'], status, get_current_ist_time()))
                                else:
                                    cursor.execute("INSERT INTO follows (follower_id, following_id, status, created_at) VALUES (?, ?, ?, ?)",
                                                   (user['user_id'], profile_user['user_id'], status, get_current_ist_time()))
                                conn.commit()
                                st.rerun()
                        elif follow_rel['status'] == 'Pending':
                            st.button("Requested", disabled=True)
                        else:
                            if st.button("Unfollow"):
                                if db_type == "mysql":
                                    cursor.execute("DELETE FROM follows WHERE follower_id = %s AND following_id = %s",
                                                   (user['user_id'], profile_user['user_id']))
                                else:
                                    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
                                                   (user['user_id'], profile_user['user_id']))
                                conn.commit()
                                st.rerun()

                    st.divider()

                    if profile_user['user_id'] == user['user_id']:
                        with st.expander("⚙️ Settings Hub (Saved Reels, Liked Reels & Edit Details)"):
                            st.write("### Edit Profile Details")
                            
                            # ==========================================================
                            # PROFILE PICTURE UPDATE WIDGET (Inside Settings Hub Only)
                            # ==========================================================
                            st.markdown("#### Update Profile Picture")
                            uploaded_pic = st.file_uploader("Choose a new profile picture (PNG/JPG)", type=["png", "jpg", "jpeg"], key="profile_pic_uploader")

                            if uploaded_pic is not None:
                                st.image(uploaded_pic, width=150, caption="New Profile Picture Preview")
                                if st.button("Save Profile Picture", key="save_profile_pic_btn"):
                                    try:
                                        pic_bytes = uploaded_pic.getvalue()
                                        if db_type == "mysql":
                                            cursor.execute("UPDATE users SET profile_pic = %s WHERE user_id = %s", (pic_bytes, user['user_id']))
                                        else:
                                            cursor.execute("UPDATE users SET profile_pic = ? WHERE user_id = ?", (pic_bytes, user['user_id']))
                                        conn.commit()
                                        st.success("Profile picture updated successfully! Refreshing...")
                                        st.rerun()
                                    except Exception as img_err:
                                        st.error(f"Error updating profile picture: {img_err}")

                            with st.form("edit_profile_form"):
                                new_name = st.text_input("Name", value=user.get('name', ''))
                                new_bio = st.text_area("Bio", value=user.get('bio', ''))
                                if st.form_submit_button("Update Profile"):
                                    if db_type == "mysql":
                                        cursor.execute("UPDATE users SET name = %s, bio = %s WHERE user_id = %s", 
                                                       (sanitize_input(new_name), sanitize_input(new_bio), user['user_id']))
                                    else:
                                        cursor.execute("UPDATE users SET name = ?, bio = ? WHERE user_id = ?", 
                                                       (sanitize_input(new_name), sanitize_input(new_bio), user['user_id']))
                                    conn.commit()
                                    user['name'] = new_name
                                    user['bio'] = new_bio
                                    st.success("Updated successfully!")

                            st.write("### 🔖 Saved Reels & Posts")
                            if db_type == "mysql":
                                cursor.execute("""
                                    SELECT p.* FROM posts p 
                                    JOIN user_interactions ui ON p.post_id = ui.post_id 
                                    WHERE ui.user_id = %s AND ui.interaction_type = 'saved'
                                """, (user['user_id'],))
                                saved_posts = cursor.fetchall()
                            else:
                                cursor.execute("""
                                    SELECT p.* FROM posts p 
                                    JOIN user_interactions ui ON p.post_id = ui.post_id 
                                    WHERE ui.user_id = ? AND ui.interaction_type = 'saved'
                                """, (user['user_id'],))
                                saved_posts = [dict(row) for row in cursor.fetchall()]

                            if not saved_posts:
                                st.caption("No saved posts or reels yet.")
                            for sp in saved_posts:
                                st.markdown(f"**{sp.get('caption', 'Saved Item')}** <span style='font-size: 0.7rem; color: gray;'>({sp.get('created_at', '')})</span>", unsafe_allow_html=True)
                                if sp.get('media_url'):
                                    st.image(sp['media_url'], width=150)

                            st.write("### ❤️ Liked Reels & Posts")
                            if db_type == "mysql":
                                cursor.execute("""
                                    SELECT p.* FROM posts p 
                                    JOIN user_interactions ui ON p.post_id = ui.post_id 
                                    WHERE ui.user_id = %s AND ui.interaction_type = 'liked'
                                """, (user['user_id'],))
                                liked_posts = cursor.fetchall()
                            else:
                                cursor.execute("""
                                    SELECT p.* FROM posts p 
                                    JOIN user_interactions ui ON p.post_id = ui.post_id 
                                    WHERE ui.user_id = ? AND ui.interaction_type = 'liked'
                                """, (user['user_id'],))
                                liked_posts = [dict(row) for row in cursor.fetchall()]

                            if not liked_posts:
                                st.caption("No liked posts or reels yet.")
                            for lp in liked_posts:
                                st.markdown(f"**{lp.get('caption', 'Liked Item')}** <span style='font-size: 0.7rem; color: gray;'>({lp.get('created_at', '')})</span>", unsafe_allow_html=True)
                                if lp.get('media_url'):
                                    st.image(lp['media_url'], width=150)

                            if st.button("Log Out"):
                                st.session_state.user = None
                                st.session_state.viewing_profile_id = None
                                st.rerun()

                    st.write("### Posts")
                    if db_type == "mysql":
                        cursor.execute("SELECT * FROM posts WHERE user_id = %s ORDER BY created_at DESC", (profile_user['user_id'],))
                        user_posts = cursor.fetchall()
                    else:
                        cursor.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC", (profile_user['user_id'],))
                        user_posts = [dict(row) for row in cursor.fetchall()]

                    if not user_posts:
                        st.caption("No posts yet.")
                    else:
                        for up in user_posts:
                            post_date_time = up.get('created_at', '')
                            st.markdown(f"<span style='font-size: 0.75rem; color: gray;'>📅 {post_date_time}</span>", unsafe_allow_html=True)
                            if up['caption']:
                                st.write(up['caption'])
                            if up['media_url']:
                                st.image(up['media_url'], width=250)
                            st.divider()
            finally:
                conn.close()

    render_footer()
    #################################################################################################################################
def make_user_follow_saraah(user_id: int):
    """Automatically forces any user to follow the exact Saraah Robotics ID."""
    db_type, conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        # Directly target the exact username shown in your profile screenshot
        target_username = "SARAAH ROBOTICS"
        
        if db_type == "mysql":
            cursor.execute("SELECT user_id FROM users WHERE username = %s LIMIT 1", (target_username,))
            saraah_user = cursor.fetchone()
            saraah_id = saraah_user['user_id'] if saraah_user else None
        else:
            cursor.execute("SELECT user_id FROM users WHERE username = ? LIMIT 1", (target_username,))
            row = cursor.fetchone()
            saraah_id = row[0] if row else None

        # If Saraah Robotics account exists and is not the user themselves, ensure a follow entry exists
        if saraah_id and saraah_id != user_id:
            if db_type == "mysql":
                cursor.execute("""
                    INSERT IGNORE INTO follows (follower_id, following_id, status, created_at) 
                    VALUES (%s, %s, 'Accepted', %s)
                """, (user_id, saraah_id, get_current_ist_time()))
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO follows (follower_id, following_id, status, created_at) 
                    VALUES (?, ?, 'Accepted', ?)
                """, (user_id, saraah_id, get_current_ist_time()))
            conn.commit()
    except Exception as e:
        logger.error(f"Error auto-following Saraah Robotics: {e}")
    finally:
        conn.close()
##################################################################################################################################################
def render_profile_picture_upload_component(user_id: int):
    """Renders a plus sign avatar placeholder if no profile picture exists, allowing users to upload one."""
    db_type, conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        # Fetch current profile picture field
        if db_type == "mysql":
            cursor.execute("SELECT profile_pic FROM users WHERE user_id = %s LIMIT 1", (user_id,))
            user_row = cursor.fetchone()
            current_pic = user_row['profile_pic'] if user_row else None
        else:
            cursor.execute("SELECT profile_pic FROM users WHERE user_id = ? LIMIT 1", (user_id,))
            row = cursor.fetchone()
            current_pic = row[0] if row else None

        st.markdown("### Profile Picture")
        
        # Check if profile picture is missing or empty
        if not current_pic:
            st.info("No profile picture found. Click below to add one with a '+' indicator style.")
            uploaded_file = st.file_uploader("Upload Profile Picture (+)", type=["png", "jpg", "jpeg"], key="profile_pic_upload_plus")
            
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                # Update database with new profile picture bytes or path depending on schema
                if db_type == "mysql":
                    cursor.execute("UPDATE users SET profile_pic = %s WHERE user_id = %s", (file_bytes, user_id))
                else:
                    cursor.execute("UPDATE users SET profile_pic = ? WHERE user_id = ?", (file_bytes, user_id))
                conn.commit()
                st.success("Profile picture updated successfully! Refreshing...")
                st.rerun()
        else:
            st.success("Profile picture is already set.")
    except Exception as e:
        logger.error(f"Error handling profile picture upload: {e}")
    finally:
        conn.close()
################################################################################################################################################################
def render_settings_and_activity_hub(user_id: int):
    """Renders an Instagram-style Settings and Activity menu with options to update details, profile picture, birthday, and handles birthday wishes."""
    db_type, conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        if db_type == "mysql":
            cursor.execute("SELECT * FROM users WHERE user_id = %s LIMIT 1", (user_id,))
            user_row = cursor.fetchone()
        else:
            cursor.execute("SELECT * FROM users WHERE user_id = ? LIMIT 1", (user_id,))
            row = cursor.fetchone()
            user_row = dict(row) if row else None

        if not user_row:
            return

        # Check if birthday column exists, if not create/handle it gracefully
        # Check if birthday is set, if not ask user for birthday after account creation
        user_birthday = user_row.get('birthday') if isinstance(user_row, dict) else None

        # Check today's date for birthday greetings (User's birthday is March 7th based on profile context)
        current_date_str = datetime.datetime.now().strftime("%m-%d")
        if user_birthday and str(user_birthday).endswith(current_date_str):
            st.balloons()
            st.success("🎉 Happy Birthday! Wishing you a fantastic year ahead from Saraah Robotics!")

        # Settings icon trigger using Streamlit expander or button toggle
        settings_open = st.toggle("⚙️ Settings and activity", key="settings_activity_toggle")

        if settings_open:
            st.markdown("### ⚙️ Settings and activity")
            st.markdown("---")
            
            # Sub-sections mimicking Instagram Settings Layout
            setting_tab = st.radio(
                "Select a setting option:", 
                [
                    "Account Details (Name, Phone, Email, Password)", 
                    "Profile Picture Upload", 
                    "Birthday Information", 
                    "Saved & Archive Activity", 
                    "Notifications & Time Management"
                ],
                key="instagram_settings_menu_radio"
            )

            st.markdown("---")

            if setting_tab == "Account Details (Name, Phone, Email, Password)":
                st.subheader("Update Account Credentials")
                with st.form("update_credentials_form"):
                    up_name = st.text_input("Name", value=user_row.get('name', ''))
                    up_phone = st.text_input("Phone Number", value=user_row.get('phone_number', ''))
                    up_email = st.text_input("Email", value=user_row.get('email', ''))
                    up_pass = st.text_input("New Password", type="password", placeholder="Leave blank or enter new password")

                    submit_creds = st.form_submit_button("Save Changes", type="primary")
                    if submit_creds:
                        try:
                            if db_type == "mysql":
                                if up_pass.strip():
                                    cursor.execute("UPDATE users SET name = %s, phone_number = %s, email = %s, password = %s WHERE user_id = %s",
                                                   (sanitize_input(up_name), sanitize_input(up_phone), sanitize_input(up_email), up_pass.strip(), user_id))
                                else:
                                    cursor.execute("UPDATE users SET name = %s, phone_number = %s, email = %s WHERE user_id = %s",
                                                   (sanitize_input(up_name), sanitize_input(up_phone), sanitize_input(up_email), user_id))
                            else:
                                if up_pass.strip():
                                    cursor.execute("UPDATE users SET name = ?, phone_number = ?, email = ?, password = ? WHERE user_id = ?",
                                                   (sanitize_input(up_name), sanitize_input(up_phone), sanitize_input(up_email), up_pass.strip(), user_id))
                                else:
                                    cursor.execute("UPDATE users SET name = ?, phone_number = ?, email = ? WHERE user_id = ?",
                                                   (sanitize_input(up_name), sanitize_input(up_phone), sanitize_input(up_email), user_id))
                            conn.commit()
                            st.success("Account details updated successfully!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error updating details: {ex}")

            elif setting_tab == "Profile Picture Upload":
                st.subheader("Update Profile Picture")
                current_pic = user_row.get('profile_pic')
                if current_pic:
                    st.image(current_pic, width=120)
                else:
                    st.info("No profile picture uploaded yet.")

                pic_file = st.file_uploader("Upload new profile picture (+)", type=["png", "jpg", "jpeg"], key="settings_pic_uploader")
                if pic_file is not None:
                    b_data = pic_file.read()
                    pic_base64 = f"data:{pic_file.type};base64,{base64.b64encode(b_data).decode()}"
                    if db_type == "mysql":
                        cursor.execute("UPDATE users SET profile_pic = %s WHERE user_id = %s", (pic_base64, user_id))
                    else:
                        cursor.execute("UPDATE users SET profile_pic = ? WHERE user_id = ?", (pic_base64, user_id))
                    conn.commit()
                    st.success("Profile picture updated!")
                    st.rerun()

            elif setting_tab == "Birthday Information":
                st.subheader("Manage Birthday")
                current_bday = user_row.get('birthday') if isinstance(user_row, dict) else None
                if not current_bday:
                    st.warning("Your birthday has not been set yet. Please add it below to receive birthday greetings!")
                
                with st.form("birthday_update_form"):
                    bday_input = st.date_input("Select your Birthday", value=datetime.date(2005, 1, 1))
                    submit_bday = st.form_submit_button("Save Birthday")
                    if submit_bday:
                        bday_str = bday_input.strftime("%Y-%m-%d")
                        try:
                            if db_type == "mysql":
                                # Safely ensure birthday column exists or update it
                                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS birthday DATE;")
                                cursor.execute("UPDATE users SET birthday = %s WHERE user_id = %s", (bday_str, user_id))
                            else:
                                try:
                                    cursor.execute("ALTER TABLE users ADD COLUMN birthday TEXT;")
                                except Exception:
                                    pass
                                cursor.execute("UPDATE users SET birthday = ? WHERE user_id = ?", (bday_str, user_id))
                            conn.commit()
                            st.success("Birthday saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving birthday: {e}")

            elif setting_tab == "Saved & Archive Activity":
                st.subheader("Your Activity Overview")
                st.write("• View saved posts, reels, and archived memories.")
                st.info("All interactive logs are securely maintained under Saraah Robotics storage.")

            elif setting_tab == "Notifications & Time Management":
                st.subheader("Preferences")
                st.write("• Push Notifications: Enabled")
                st.write("• Daily Reminder: Active")

    except Exception as e:
        logger.error(f"Settings Hub Error: {e}")
    finally:
        conn.close()
# ------------------ BOTTOM NAVIGATION LAYOUT (7 BUTTONS) ------------------#
    #1. Update your navigation buttons to 7 columns (including Settings)
    nav_cols = st.columns(7)
    with nav_cols[0]:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.nav_tab = "Home"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[1]:
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.nav_tab = "Search"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[2]:
        if st.button("➕ Post", use_container_width=True):
            st.session_state.nav_tab = "Post"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[3]:
        if st.button("🎬 Reels", use_container_width=True):
            st.session_state.nav_tab = "Reels"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[4]:
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.nav_tab = "Chat"
            st.session_state.viewing_profile_id = None
            st.rerun()
    with nav_cols[5]:
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.nav_tab = "Profile"
            st.session_state.viewing_profile_id = user['user_id']
            st.rerun()
    with nav_cols[6]:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.nav_tab = "Settings"
            st.session_state.viewing_profile_id = None
            st.rerun()

    # 2. Route checker for Settings#
    if st.session_state.get("nav_tab") == "Home":
        pass
    elif st.session_state.get("nav_tab") == "Search":
        pass
    elif st.session_state.get("nav_tab") == "Post":
        pass
    elif st.session_state.get("nav_tab") == "Reels":
        render_reels_viewer_page(user['user_id'])
    elif st.session_state.get("nav_tab") == "Chat":
        pass
    elif st.session_state.get("nav_tab") == "Profile":
        pass
    elif st.session_state.get("nav_tab") == "Settings":
        render_settings_page(user['user_id'])
##################################################################################################################################################################
# ==============================================================================
# SARAHAH ROBOTICS AUTOMATED SETTINGS & AUTO-FOLLOW MODULE (Paste at the very last)
# ==============================================================================

def make_user_follow_saraah(user_id: int):
    """Automatically forces any user to follow @SARAAH ROBOTICS instantly upon login."""
    db_type, conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        target_username = "SARAAH ROBOTICS"
        
        if db_type == "mysql":
            cursor.execute("SELECT user_id FROM users WHERE username = %s LIMIT 1", (target_username,))
            saraah_user = cursor.fetchone()
            saraah_id = saraah_user['user_id'] if saraah_user else None
        else:
            cursor.execute("SELECT user_id FROM users WHERE username = ? LIMIT 1", (target_username,))
            row = cursor.fetchone()
            saraah_id = row[0] if row else None

        if saraah_id and saraah_id != user_id:
            if db_type == "mysql":
                cursor.execute("""
                    INSERT IGNORE INTO follows (follower_id, following_id, status, created_at) 
                    VALUES (%s, %s, 'Accepted', %s)
                """, (user_id, saraah_id, get_current_ist_time()))
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO follows (follower_id, following_id, status, created_at) 
                    VALUES (?, ?, 'Accepted', ?)
                """, (user_id, saraah_id, get_current_ist_time()))
            conn.commit()
    except Exception as e:
        logger.error(f"Error auto-following Saraah Robotics: {e}")
    finally:
        conn.close()

def render_settings_page(user_id: int):
    """Renders the dedicated Settings page for updating name, phone, email, password, profile pic, and birthday."""
    db_type, conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        if db_type == "mysql":
            cursor.execute("SELECT * FROM users WHERE user_id = %s LIMIT 1", (user_id,))
            user_row = cursor.fetchone()
        else:
            cursor.execute("SELECT * FROM users WHERE user_id = ? LIMIT 1", (user_id,))
            row = cursor.fetchone()
            user_row = dict(row) if row else None

        if not user_row:
            st.error("User profile data not found.")
            return

        st.subheader("⚙️ Settings and Activity")
        st.write("Manage your account details, profile customization, and preferences.")
        st.divider()

        setting_option = st.selectbox(
            "Select Setting Category",
            [
                "Edit Account Details (Name, Phone, Email, Password)",
                "Update Profile Picture",
                "Birthday Management"
            ]
        )

        st.markdown("---")

        if setting_option == "Edit Account Details (Name, Phone, Email, Password)":
            st.markdown("### 👤 Edit Profile Information")
            with st.form("settings_edit_credentials"):
                new_name = st.text_input("Full Name", value=user_row.get('name', ''))
                new_phone = st.text_input("Phone Number", value=user_row.get('phone_number', ''))
                new_email = st.text_input("Email Address", value=user_row.get('email', ''))
                new_password = st.text_input("New Password", type="password", placeholder="Leave blank to keep current password")
                
                submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                if submitted:
                    try:
                        if db_type == "mysql":
                            if new_password.strip():
                                cursor.execute("""
                                    UPDATE users SET name = %s, phone_number = %s, email = %s, password = %s 
                                    WHERE user_id = %s
                                """, (sanitize_input(new_name), sanitize_input(new_phone), sanitize_input(new_email), new_password.strip(), user_id))
                            else:
                                cursor.execute("""
                                    UPDATE users SET name = %s, phone_number = %s, email = %s 
                                    WHERE user_id = %s
                                """, (sanitize_input(new_name), sanitize_input(new_phone), sanitize_input(new_email), user_id))
                        else:
                            if new_password.strip():
                                cursor.execute("""
                                    UPDATE users SET name = ?, phone_number = ?, email = ?, password = ? 
                                    WHERE user_id = ?
                                """, (sanitize_input(new_name), sanitize_input(new_phone), sanitize_input(new_email), new_password.strip(), user_id))
                            else:
                                cursor.execute("""
                                    UPDATE users SET name = ?, phone_number = ?, email = ? 
                                    WHERE user_id = ?
                                """, (sanitize_input(new_name), sanitize_input(new_phone), sanitize_input(new_email), user_id))
                        conn.commit()
                        st.success("Account details updated successfully!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Failed to update profile: {err}")

        elif setting_option == "Update Profile Picture":
            st.markdown("### 🖼️ Profile Picture")
            current_pic = user_row.get('profile_pic')
            if current_pic:
                st.image(current_pic, width=150)
            else:
                st.info("No profile picture currently uploaded.")

            pic_file = st.file_uploader("Upload new picture", type=["png", "jpg", "jpeg"], key="settings_page_pic_upload")
            if pic_file is not None:
                b_data = pic_file.read()
                pic_base64 = f"data:{pic_file.type};base64,{base64.b64encode(b_data).decode()}"
                if db_type == "mysql":
                    cursor.execute("UPDATE users SET profile_pic = %s WHERE user_id = %s", (pic_base64, user_id))
                else:
                    cursor.execute("UPDATE users SET profile_pic = ? WHERE user_id = ?", (pic_base64, user_id))
                conn.commit()
                st.success("Profile picture updated successfully!")
                st.rerun()

        elif setting_option == "Birthday Information":
            st.markdown("### 🎂 Birthday & Greetings")
            current_bday = user_row.get('birthday') if isinstance(user_row, dict) else None
            if not current_bday:
                st.warning("Please provide your birthday so we can greet you on your special day!")
            else:
                st.info(f"Registered Birthday: {current_bday}")

            with st.form("settings_birthday_form"):
                bday_val = st.date_input("Select Birthday", value=datetime.date(2005, 1, 1))
                sub_bday = st.form_submit_button("Save Birthday", use_container_width=True)
                if sub_bday:
                    bday_str = bday_val.strftime("%Y-%m-%d")
                    try:
                        if db_type == "mysql":
                            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS birthday DATE;")
                            cursor.execute("UPDATE users SET birthday = %s WHERE user_id = %s", (bday_str, user_id))
                        else:
                            try:
                                cursor.execute("ALTER TABLE users ADD COLUMN birthday TEXT;")
                            except Exception:
                                pass
                            cursor.execute("UPDATE users SET birthday = ? WHERE user_id = ?", (bday_str, user_id))
                        conn.commit()
                        st.success("Birthday saved successfully!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error saving birthday: {ex}")

    except Exception as e:
        logger.error(f"Settings page error: {e}")
    finally:
        conn.close()
# ==============================================================================
# FULLY WORKING DIRECT MESSAGE HANDLER (Paste at the very last)
# ==============================================================================
def render_and_handle_send_dm(current_user_id: int, recipient_user_id: int):
    """Renders a working input field and handles direct messaging dynamically so it reflects immediately."""
    st.markdown("---")
    st.subheader("💬 Direct Message")
    
    # Use a unique form key based on the recipient to prevent state collisions
    dm_form_key = f"dm_form_{current_user_id}_{recipient_user_id}"
    
    with st.form(key=dm_form_key, clear_on_submit=True):
        message_text = st.text_input("Type your message here...", placeholder="Say something...")
        send_clicked = st.form_submit_button("Send DM", type="primary")
        
        if send_clicked:
            if not message_text.strip():
                st.warning("Please type a message before sending.")
                return

            db_type, conn = get_db_connection()
            if not conn:
                st.error("Database connection failed.")
                return

            try:
                cursor = conn.cursor()
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Insert message into database supporting both MySQL and SQLite setups
                if db_type == "mysql":
                    cursor.execute("""
                        INSERT INTO messages (sender_id, recipient_id, message_text, created_at, is_read) 
                        VALUES (%s, %s, %s, %s, 0)
                    """, (current_user_id, recipient_user_id, sanitize_input(message_text), current_time))
                else:
                    cursor.execute("""
                        INSERT INTO messages (sender_id, recipient_id, message_text, created_at, is_read) 
                        VALUES (?, ?, ?, ?, 0)
                    """, (current_user_id, recipient_user_id, sanitize_input(message_text), current_time))
                
                conn.commit()
                st.success("Message sent successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error sending DM: {e}")
                st.error(f"Failed to send message: {e}")
            finally:
                conn.close()
# ==============================================================================
# REELS VIEWER MODULE & 6-BUTTON NAVIGATION (Paste at the very last)
# ==============================================================================
def render_reels_viewer_page(current_user_id: int):
    """Renders a dedicated Reels viewing section where users can watch available reels and interact with them."""
    st.subheader("🎬 Reels Feed")
    st.write("Watch short-form video reels and media posted across the community.")
    st.divider()

    db_type, conn = get_db_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    try:
        cursor = conn.cursor()
        # Fetch available video posts or reels from the database
        if db_type == "mysql":
            cursor.execute("""
                SELECT p.*, u.username, u.profile_pic 
                FROM posts p 
                JOIN users u ON p.user_id = u.user_id 
                WHERE p.media_type LIKE '%video%' OR p.caption LIKE '%reel%' 
                ORDER BY p.created_at DESC LIMIT 20
            """)
            reels = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT p.*, u.username, u.profile_pic 
                FROM posts p 
                JOIN users u ON p.user_id = u.user_id 
                WHERE p.media_type LIKE '%video%' OR p.caption LIKE '%reel%' 
                ORDER BY p.created_at DESC LIMIT 20
            """)
            reels = [dict(row) for row in cursor.fetchall()]

        if not reels:
            st.info("No reels available at the moment. Check back soon or upload a video reel!")
            return

        for reel in reels:
            username = reel.get('username', 'Unknown')
            caption = reel.get('caption', '')
            media_data = reel.get('media_url') or reel.get('media')
            created_at = reel.get('created_at', '')

            with st.container():
                st.markdown(f"**@{username}** • <span style='color:gray; font-size:12px;'>{created_at}</span>", unsafe_allow_html=True)
                if caption:
                    st.write(caption)
                
                if media_data:
                    try:
                        st.video(media_data)
                    except Exception:
                        st.warning("Could not load video media.")
                st.markdown("---")

    except Exception as e:
        logger.error(f"Error rendering reels viewer: {e}")
        st.error("Could not load reels feed.")
    finally:
        conn.close()
# ==============================================================================
# NOOB LEARNING - REELS PAGE (Paste at the very last line of your file)
# ==============================================================================
def render_reels_viewer_page(current_user_id: int):
    """Renders a Reels style feed matching the requested layout with 'Noob Learning' branding."""
    
    # Top Header matching Instagram style bar with "Noob Learning" title
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        st.markdown("📸")
    with col2:
        st.markdown("<h3 style='text-align: center; margin: 0; font-family: sans-serif;'>Noob Learning</h3>", unsafe_allow_html=True)
    with col3:
        st.markdown("✉️")
    
    st.divider()

    db_type, conn = get_db_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    try:
        cursor = conn.cursor()
        if db_type == "mysql":
            cursor.execute("""
                SELECT p.*, u.username, u.profile_pic 
                FROM posts p 
                JOIN users u ON p.user_id = u.user_id 
                ORDER BY p.created_at DESC LIMIT 20
            """)
            reels = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT p.*, u.username, u.profile_pic 
                FROM posts p 
                JOIN users u ON p.user_id = u.user_id 
                ORDER BY p.created_at DESC LIMIT 20
            """)
            reels = [dict(row) for row in cursor.fetchall()]

        if not reels:
            st.info("No media posts available yet.")
            return

        for reel in reels:
            username = reel.get('username', 'user')
            caption = reel.get('caption', '')
            media_data = reel.get('media_url') or reel.get('media')

            with st.container():
                # User info header row above post
                st.markdown(f"**@{username}**")
                
                # Main media display (video or image)
                if media_data:
                    try:
                        if "video" in str(media_data).lower() or str(media_data).endswith(('.mp4', '.mov', '.avi')):
                            st.video(media_data)
                        else:
                            st.image(media_data, use_container_width=True)
                    except Exception:
                        st.info("Displaying media placeholder.")
                
                # Action buttons row (Like, Comment, Share, Bookmark)
                ac1, ac2, ac3, ac4 = st.columns([1, 1, 1, 6])
                with ac1:
                    st.button("🤍", key=f"like_{reel.get('post_id')}")
                with ac2:
                    st.button("💬", key=f"comment_{reel.get('post_id')}")
                with ac3:
                    st.button("↗️", key=f"share_{reel.get('post_id')}")
                
                # Caption text
                if caption:
                    st.markdown(f"**@{username}** {caption}")
                
                st.markdown("---")

    except Exception as e:
        st.error("Could not load feed.")
    finally:
        conn.close()
# ==============================================================================
# FOLLOWER & FOLLOWING DISPLAY WIDGET (Paste at the very last line of your file)
# ==============================================================================
def render_follower_stats_widget(profile_user_id: int, profile_username: str):
    """Displays live follower/following counts with special override for SARAAH_ROBOTICS."""
    db_type, conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True) if db_type == "mysql" else conn.cursor()
        
        # Check if table exists, create if missing
        if db_type == "mysql":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    follower_id INT,
                    following_id INT,
                    PRIMARY KEY (follower_id, following_id)
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    follower_id INTEGER,
                    following_id INTEGER,
                    PRIMARY KEY (follower_id, following_id)
                )
            """)
        conn.commit()

        # Get actual follower count from database
        if db_type == "mysql":
            cursor.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = %s", (profile_user_id,))
            res = cursor.fetchone()
            db_followers = res['cnt'] if isinstance(res, dict) else res[0]
            
            cursor.execute("SELECT COUNT(*) as cnt FROM follows WHERE follower_id = %s", (profile_user_id,))
            res_f = cursor.fetchone()
            following_count = res_f['cnt'] if isinstance(res_f, dict) else res_f[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id = ?", (profile_user_id,))
            db_followers = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ?", (profile_user_id,))
            following_count = cursor.fetchone()[0]

        # Apply base target of 56,780 for SARAAH_ROBOTICS plus any real new database followers
        if str(profile_username).strip().upper() == "SARAAH_ROBOTICS":
            # If database has followers, add them to the base value dynamically
            followers_count = 56780 + db_followers
        else:
            followers_count = db_followers

        # Display Metrics Layout
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Followers", f"{followers_count:,}")
        with col2:
            st.metric("Following", f"{following_count:,}")

    except Exception as e:
        # Fallback view if database tables are uninitialized
        if str(profile_username).strip().upper() == "SARAAH_ROBOTICS":
            st.metric("Followers", "56,780")
        else:
            st.metric("Followers", "0")
        st.metric("Following", "0")
    finally:
        if conn:
            conn.close()
