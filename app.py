import streamlit as st
import sqlite3
import datetime
import logging
import sys

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
# 1. DATABASE SETUP & CONNECTION
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
        # Ensure new columns exist if table was already created
        cursor.execute("PRAGMA table_info(users)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'gender' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT")
        if 'birth_date' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN birth_date TEXT")
        if 'account_type' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN account_type TEXT DEFAULT 'Public'")

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
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            demo_users = [
                ('saraah_robotics', 'password123', 'Saraah Robotics', 'Official Saraah Robotics Account 🚀 Autonomous Systems & AI', 18, 'Other', '2005-01-01', 'Public', ''),
                ('princehumperdinck87', 'password123', 'Prince Humperdinck', 'Exploring AI & Robotics 🤖 | Founder Noob Learning', 18, 'Male', '2005-05-15', 'Public', ''),
                ('alex_dev', 'password123', 'Alex Rivera', 'Building cool Python & AI web apps 💻', 19, 'Male', '2004-10-10', 'Private', ''),
                ('noob_coder', 'password123', 'Noob Coder', 'Learning Python step by step 🪀', 17, 'Female', '2006-12-22', 'Public', '')
            ]
            cursor.executemany("""
                INSERT OR IGNORE INTO users (username, password, full_name, bio, age, gender, birth_date, account_type, profile_pic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, demo_users)
        conn.commit()
        conn.close()

init_db()

def get_current_ist_time():
    ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(ist_offset).strftime("%Y-%m-%d %H:%M:%S")

# ==============================================================================
# USER REGISTRATION & PROFILE UPDATE LOGIC WITH FALLBACK
# ==============================================================================
def register_user(username, password, full_name, bio, profile_pic, gender, birth_date, account_type):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (username, password, full_name, bio, profile_pic, gender, birth_date, account_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, password, full_name, bio, profile_pic, gender, birth_date, account_type))
        conn.commit()
        conn.close()

def update_user_profile(username, new_full_name, new_bio, new_profile_pic, new_gender, new_birth_date, new_account_type, new_password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, bio, profile_pic, gender, birth_date, account_type, password FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            final_full_name = new_full_name if new_full_name and new_full_name.strip() else existing_user['full_name']
            final_bio = new_bio if new_bio and new_bio.strip() else existing_user['bio']
            final_profile_pic = new_profile_pic if new_profile_pic and new_profile_pic.strip() else existing_user['profile_pic']
            final_gender = new_gender if new_gender and new_gender.strip() else existing_user['gender']
            final_birth_date = new_birth_date if new_birth_date and new_birth_date.strip() else existing_user['birth_date']
            final_account_type = new_account_type if new_account_type and new_account_type.strip() else existing_user['account_type']
            final_password = new_password if new_password and new_password.strip() else existing_user['password']
            
            cursor.execute("""
                UPDATE users 
                SET full_name = ?, bio = ?, profile_pic = ?, gender = ?, birth_date = ?, account_type = ?, password = ?
                WHERE username = ?
            """, (final_full_name, final_bio, final_profile_pic, final_gender, final_birth_date, final_account_type, final_password, username))
            
            conn.commit()
        conn.close()

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
# 2. PREMIUM CUSTOM CSS THEME (Instagram Box Style Layout)
# ==============================================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        color: #ffffff;
    }
    header {visibility: hidden;}
    
    .auth-container {
        max-width: 380px;
        margin: 40px auto;
        background: rgba(22, 27, 34, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 35px 30px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
    }
    
    .auth-footer-box {
        max-width: 380px;
        margin: 15px auto 40px auto;
        background: rgba(22, 27, 34, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px 30px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    }

    div.stButton > button {
        background: linear-gradient(135deg, #00C853 0%, #009624) !important;
        color: #0e1117 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        box-shadow: 0 4px 15px rgba(0, 200, 83, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 200, 83, 0.4);
    }
    
    input, textarea, select {
        background-color: rgba(13, 17, 23, 0.7) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. PREMIUM BOX AUTHENTICATION SCREEN
# ==============================================================================
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.2, 1])
    
    with center_col:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="font-family: 'Brush Script MT', cursive, sans-serif; font-size: 3rem; font-weight: normal; margin: 0; background: linear-gradient(45deg, #ffffff, #a5d6a7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 1px;">Noob Learning</h1>
                <p style="color: #00C853; font-size: 0.7rem; letter-spacing: 2px; margin-top: 5px; font-weight: 600;">POWERED BY SARAAH ROBOTICS</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.auth_mode == "login":
            with st.form("login_form"):
                username_in = st.text_input("Phone number, username, or email", placeholder="Phone number, username, or email")
                password_in = st.text_input("Password", type="password", placeholder="Password")
                submitted = st.form_submit_button("Log In", use_container_width=True)
                
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
            
            st.markdown("""
                <div style="display: flex; align-items: center; text-align: center; margin: 20px 0; color: #8b949e; font-size: 13px;">
                    <div style="flex: 1; border-bottom: 1px solid rgba(255,255,255,0.1);"></div>
                    <div style="padding: 0 15px; font-weight: 600; font-size: 11px; letter-spacing: 1px;">OR</div>
                    <div style="flex: 1; border-bottom: 1px solid rgba(255,255,255,0.1);"></div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <div style="text-align: center; margin-top: 15px;">
                    <a href="#" style="color: #58a6ff; text-decoration: none; font-size: 13px;">Forgot password?</a>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='auth-footer-box'>", unsafe_allow_html=True)
            col_txt, col_btn = st.columns([2.5, 1])
            with col_txt:
                st.markdown("<p style='margin: 6px 0 0 0; font-size: 14px; color: #c9d1d9;'>Don't have an account?</p>", unsafe_allow_html=True)
            with col_btn:
                if st.button("Sign up", key="to_signup_btn"):
                    st.session_state.auth_mode = "signup"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align: center; font-size: 1.2rem; margin-bottom: 15px; color: #fff;'>Create a New Account</h3>", unsafe_allow_html=True)
                new_user = st.text_input("Username", placeholder="Choose username").lower()
                new_pass = st.text_input("Password", type="password", placeholder="Password")
                full_name = st.text_input("Full Name", placeholder="Full Name")
                gender_in = st.selectbox("Gender", ["Male", "Female", "Other"])
                dob_in = st.text_input("Date of Birth", placeholder="YYYY-MM-DD")
                acc_type_in = st.selectbox("Account Type", ["Public", "Private"])
                bio = st.text_area("Bio", placeholder="Short Bio")
                
                if st.form_submit_button("Sign Up", use_container_width=True):
                    if new_user and new_pass:
                        try:
                            register_user(new_user.strip(), new_pass, full_name, bio, "", gender_in, dob_in, acc_type_in)
                            st.success("Account created! Please log in.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Username already taken.")
                    else:
                        st.warning("Fill in username and password.")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='auth-footer-box'>", unsafe_allow_html=True)
            col_txt2, col_btn2 = st.columns([2.2, 1.2])
            with col_txt2:
                st.markdown("<p style='margin: 6px 0 0 0; font-size: 14px; color: #c9d1d9;'>Have an account?</p>", unsafe_allow_html=True)
            with col_btn2:
                if st.button("Log in", key="to_login_btn"):
                    st.session_state.auth_mode = "login"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.stop()

# ==============================================================================
# 4. MAIN APP DASHBOARD & TOP NAVIGATION BAR
# ==============================================================================
user = st.session_state.user
username = user['username']
first_letter = username[0].upper()

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
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Fetch all posts along with authors' account types to enforce privacy rule
            cursor.execute("""
                SELECT p.*, u.account_type 
                FROM reels_posts p 
                JOIN users u ON p.username = u.username 
                ORDER BY p.id DESC
            """)
            posts = cursor.fetchall()
            conn.close()
            
            for p in posts:
                p_dict = dict(p)
                # Privacy rule: If account is Private, only show if it's the current user's post (or if friends/followers mechanism applies, here current user or public)
                if p_dict['account_type'] == 'Private' and p_dict['username'] != username:
                    continue  # Hide private posts from non-owners
                
                st.markdown(f"""
                    <div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #30363d;">
                        <span style="background: #00C853; color: #0e1117; padding: 2px 8px; border-radius: 50%; font-weight: bold;">{p_dict['username'][0].upper()}</span>
                        <strong style="color: white; margin-left: 8px;">@{p_dict['username']}</strong>
                        <span style="color: #888; font-size: 11px; margin-left: 10px;">({p_dict['account_type']})</span>
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
            cursor.execute("""
                SELECT r.*, u.account_type 
                FROM reels_posts r 
                JOIN users u ON r.username = u.username 
                WHERE r.media_type = 'Reel' 
                ORDER BY r.id DESC
            """)
            reels = cursor.fetchall()
            conn.close()
            
            filtered_reels = [dict(r) for r in reels if r['account_type'] == 'Public' or r['username'] == username]
            
            if not filtered_reels:
                st.info("No reels available yet or accounts are private.")
            for r_dict in filtered_reels:
                st.markdown(f"""
                    <div style="background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <div style="background-color: #ff4b4b; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                                {r_dict['username'][0].upper()}
                            </div>
                            <div>
                                <strong style="color: white;">@{r_dict['username']}</strong> <span style="font-size:11px; color:#888;">({r_dict['account_type']})</span><br>
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
# TAB 3: CHAT & USER SEARCH SECTION
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
        st.markdown("### 💬 Direct Messages & User Search")
        st.markdown("<p style='color: #b0b8c1; font-size: 14px;'>Search users by User ID or pick from recent community members.</p>", unsafe_allow_html=True)
        
        search_query = st.text_input("🔍 Search User ID / Username", placeholder="Type a username to search...").strip().lower()
        
        st.markdown("<hr style='border: 0.5px solid #30363d;'>", unsafe_allow_html=True)
        
        filtered_peers = []
        for p in peers:
            p_dict = dict(p)
            uname = p_dict.get('username') or ''
            fname = p_dict.get('full_name') or ''
            if not search_query or search_query in uname.lower() or search_query in fname.lower():
                filtered_peers.append(p_dict)
        
        if search_query:
            st.markdown(f"**Search Results for '{search_query}' ({len(filtered_peers)} found):**")
        else:
            st.markdown("**🕒 Recent Community Users:**")
            
        if not filtered_peers:
            st.info("No users found matching your search.")
            
        for p_dict in filtered_peers:
            avatar_char = p_dict['username'][0].upper()
            display_name = p_dict.get('full_name') or p_dict['username']
            profile_pic = p_dict.get('profile_pic')
            acc_type = p_dict.get('account_type', 'Public')
            
            c_info, c_btn = st.columns([5, 1])
            with c_info:
                if profile_pic:
                    avatar_html = f"<img src='{profile_pic}' style='width: 42px; height: 42px; border-radius: 50%; object-fit: cover;'>"
                else:
                    avatar_html = f"<div style='background-color: #00C853; color: #0e1117; width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 18px;'>{avatar_char}</div>"

                st.markdown(f"""
                <div style="display: flex; align-items: flex-start; gap: 15px; padding: 8px 0;">
                    {avatar_html}
                    <div>
                        <span style="color: white; font-weight: bold; font-size: 15px;">{display_name}</span> 
                        <span style="color: #b0b8c1; font-size: 13px;">(@{p_dict['username']})</span>
                        <span style="background: #21262d; color: #888; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-left: 5px;">{acc_type}</span>
                        <p style="color: #aaa; font-size: 13px; margin: 4px 0 0 0;">{p_dict.get('bio') or 'No bio added.'}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with c_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Message 💬", key=f"search_chat_btn_{p_dict['username']}"):
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
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            user = dict(row)
            st.session_state.user = user
        conn.close()

    st.markdown(f"""
        <div style="background-color: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d;">
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="background-color: #00C853; color: #0e1117; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 28px;">
                    {first_letter}
                </div>
                <div>
                    <h2 style="margin: 0; color: white;">{user.get('full_name') or username} <span style="font-size: 15px; color: #888;">(@{username})</span></h2>
                    <p style="color: #00C853; font-weight: 500; margin: 2px 0;">Account Type: {user.get('account_type', 'Public')} | Gender: {user.get('gender', 'N/A')} | DOB: {user.get('birth_date', 'N/A')}</p>
                    <p style="color: #ccc; margin: 5px 0 0 0;">{user.get('bio') or 'No bio added yet.'}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("⚙️ Edit Profile Settings"):
        with st.form("edit_profile"):
            new_full = st.text_input("Full Name", value=user.get('full_name', ''))
            gender_options = ["Male", "Female", "Other"]
            current_gender = user.get('gender', 'Other')
            gender_idx = gender_options.index(current_gender) if current_gender in gender_options else 2
            new_gender = st.selectbox("Gender", gender_options, index=gender_idx)
            
            new_dob = st.text_input("Date of Birth (YYYY-MM-DD)", value=user.get('birth_date', ''))
            
            acc_options = ["Public", "Private"]
            current_acc = user.get('account_type', 'Public')
            acc_idx = acc_options.index(current_acc) if current_acc in acc_options else 0
            new_acc_type = st.selectbox("Account Type (Public = Everyone, Private = Followers/Friends only)", acc_options, index=acc_idx)
            
            new_bio = st.text_area("Bio", value=user.get('bio', ''))
            new_pic = st.text_input("Profile Picture URL (Optional)", value=user.get('profile_pic', ''))
            new_pass = st.text_input("Change Password (leave blank to keep current)", type="password", value="")
            
            if st.form_submit_button("Save Profile Settings"):
                update_user_profile(username, new_full, new_bio, new_pic, new_gender, new_dob, new_acc_type, new_pass)
                st.success("Profile updated successfully! Unchanged fields retained their previous values.")
                st.rerun()

st.markdown("<p style='text-align: center; color: #555; font-size: 0.7rem; letter-spacing: 2px; margin-top: 5rem;'>POWERED BY SARAAH ROBOTICS</p>", unsafe_allow_html=True)
