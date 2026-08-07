import base64
import datetime
import logging
import sqlite3
import sys
import streamlit as st

# ==============================================================================
# 0. LOGGING & PAGE CONFIG
# ==============================================================================
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("NoobLearningApp")

st.set_page_config(
    page_title="Noob Learning",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 1. DATABASE SETUP & CONNECTION (ROBUST MIGRATION)
# ==============================================================================


def get_db_connection():
  try:
    conn = sqlite3.connect("database.db", check_same_thread=False)
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
    cursor.execute("PRAGMA table_info(users)")
    columns = [col["name"] for col in cursor.fetchall()]

    required_columns = {
        "gender": "TEXT",
        "birth_date": "TEXT",
        "account_type": 'TEXT DEFAULT "Public"',
        "profile_pic": "TEXT",
        "full_name": "TEXT",
        "bio": "TEXT",
        "age": "INTEGER",
        "password": "TEXT",
    }

    for col_name, col_type in required_columns.items():
      if col_name not in columns:
        try:
          cursor.execute(
              f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
          )
        except Exception as ex:
          logger.warning(f"Could not add column {col_name}: {ex}")

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower TEXT,
                following TEXT,
                UNIQUE(follower, following)
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
                media_data TEXT,
                media_type TEXT,
                timestamp TEXT
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE,
                created_by TEXT,
                description TEXT,
                timestamp TEXT
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                sender TEXT,
                message TEXT,
                media_data TEXT,
                media_type TEXT,
                timestamp TEXT
            )
        """)

    for table_name in ["messages", "group_messages"]:
      cursor.execute(f"PRAGMA table_info({table_name})")
      t_cols = [col["name"] for col in cursor.fetchall()]
      if "media_data" not in t_cols:
        try:
          cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN media_data TEXT")
        except Exception:
          pass
      if "media_type" not in t_cols:
        try:
          cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN media_type TEXT")
        except Exception:
          pass

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
      demo_users = [
          (
              "saraah_robotics",
              "password123",
              "Saraah Robotics",
              (
                  "Official Saraah Robotics Account 🚀 Autonomous Systems & AI"
              ),
              18,
              "Other",
              "2005-01-01",
              "Public",
              "",
          ),
          (
              "princehumperdinck87",
              "password123",
              "Prince Humperdinck",
              "Exploring AI & Robotics 🤖 | Founder Noob Learning",
              18,
              "Male",
              "2005-05-15",
              "Public",
              "",
          ),
      ]
      cursor.executemany(
          """
                INSERT OR IGNORE INTO users (username, password, full_name, bio, age, gender, birth_date, account_type, profile_pic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
          demo_users,
      )
    conn.commit()
    conn.close()


init_db()


def get_current_ist_time():
  ist_offset = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
  return datetime.datetime.now(ist_offset).strftime("%Y-%m-%d %H:%M:%S")


def get_user_stats(username):
  conn = get_db_connection()
  followers_count = 0
  following_count = 0
  if conn:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM follows WHERE following = ?", (username,)
    )
    row = cursor.fetchone()
    if row:
      followers_count = row[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower = ?", (username,))
    row = cursor.fetchone()
    if row:
      following_count = row[0]
    conn.close()
  return followers_count, following_count


def register_user(
    username,
    password,
    full_name,
    bio,
    profile_pic,
    gender,
    birth_date,
    account_type,
):
  conn = get_db_connection()
  if conn:
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT OR REPLACE INTO users (username, password, full_name, bio, profile_pic, gender, birth_date, account_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            password,
            full_name,
            bio,
            profile_pic,
            gender,
            birth_date,
            account_type,
        ),
    )
    conn.commit()
    conn.close()


def update_user_profile(
    old_username,
    new_username,
    new_full_name,
    new_bio,
    new_profile_pic,
    new_gender,
    new_birth_date,
    new_account_type,
    new_password,
):
  conn = get_db_connection()
  success = False
  error_msg = ""
  if conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (old_username,))
    existing_user = cursor.fetchone()

    if existing_user:
      existing_dict = dict(existing_user)
      target_username = (
          new_username.strip().lower()
          if new_username and new_username.strip()
          else old_username
      )

      if target_username != old_username:
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (target_username,))
        if cursor.fetchone():
          conn.close()
          return False, "Username already taken!"

      final_full_name = (
          new_full_name
          if new_full_name and new_full_name.strip()
          else existing_dict.get("full_name", "")
      )
      final_bio = (
          new_bio
          if new_bio and new_bio.strip()
          else existing_dict.get("bio", "")
      )
      final_profile_pic = (
          new_profile_pic
          if new_profile_pic is not None and new_profile_pic != ""
          else existing_dict.get("profile_pic", "")
      )
      final_gender = (
          new_gender
          if new_gender and new_gender.strip()
          else existing_dict.get("gender", "Other")
      )
      final_birth_date = (
          new_birth_date
          if new_birth_date and new_birth_date.strip()
          else existing_dict.get("birth_date", "")
      )
      final_account_type = (
          new_account_type
          if new_account_type and new_account_type.strip()
          else existing_dict.get("account_type", "Public")
      )
      final_password = (
          new_password
          if new_password and new_password.strip()
          else existing_dict.get("password", "")
      )

      try:
        cursor.execute(
            """
                    UPDATE users 
                    SET username = ?, full_name = ?, bio = ?, profile_pic = ?, gender = ?, birth_date = ?, account_type = ?, password = ?
                    WHERE username = ?
                """,
            (
                target_username,
                final_full_name,
                final_bio,
                final_profile_pic,
                final_gender,
                final_birth_date,
                final_account_type,
                final_password,
                old_username,
            ),
        )

        if target_username != old_username:
          cursor.execute(
              "UPDATE reels_posts SET username = ? WHERE username = ?",
              (target_username, old_username),
          )
          cursor.execute(
              "UPDATE messages SET sender = ? WHERE sender = ?",
              (target_username, old_username),
          )
          cursor.execute(
              "UPDATE messages SET receiver = ? WHERE receiver = ?",
              (target_username, old_username),
          )
          cursor.execute(
              "UPDATE follows SET follower = ? WHERE follower = ?",
              (target_username, old_username),
          )
          cursor.execute(
              "UPDATE follows SET following = ? WHERE following = ?",
              (target_username, old_username),
          )

        conn.commit()
        success = True
      except Exception as e:
        error_msg = str(e)
    conn.close()
  return success, error_msg


# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "user" not in st.session_state:
  st.session_state.user = None
if "auth_mode" not in st.session_state:
  st.session_state.auth_mode = "login"
if "nav_option" not in st.session_state:
  st.session_state.nav_option = "Feed"
if "active_chat_user" not in st.session_state:
  st.session_state.active_chat_user = None
if "active_group_chat" not in st.session_state:
  st.session_state.active_group_chat = None
if "chat_sub_mode" not in st.session_state:
  st.session_state.chat_sub_mode = "Direct Messages"
if "show_edit_profile" not in st.session_state:
  st.session_state.show_edit_profile = False
if "chat_theme" not in st.session_state:
  st.session_state.chat_theme = "Dark Futuristic"

# ==============================================================================
# 2. PREMIUM CUSTOM CSS THEME
# ==============================================================================
st.markdown(
    """
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

    div.stButton > button, button[kind="secondary"], button[kind="primary"], [data-testid="baseButton-secondary"], [data-testid="baseButton-primary"] {
        background: #00E676 !important;
        background-color: #00E676 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 900 !important;
        font-size: 15px !important;
        border: 2px solid #00FF88 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 15px rgba(0, 230, 118, 0.4) !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    div.stButton > button *, button[kind="secondary"] *, button[kind="primary"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 900 !important;
    }

    div.stButton > button:hover, button[kind="secondary"]:hover, button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(0, 230, 118, 0.7) !important;
        background: #69F0AE !important;
        background-color: #69F0AE !important;
        color: #000000 !important;
    }
    
    input, textarea, select {
        background-color: rgba(13, 17, 23, 0.7) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
    }

    .stTextInput label, .stSelectbox label, .stTextArea label, .stFileUploader label {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. AUTHENTICATION SCREEN
# ==============================================================================
if not st.session_state.logged_in:
  _, center_col, _ = st.columns([1, 1.2, 1])

  with center_col:
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)

    st.markdown(
        """
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="font-family: 'Brush Script MT', cursive, sans-serif; font-size: 3rem; font-weight: normal; margin: 0; background: linear-gradient(45deg, #ffffff, #a5d6a7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 1px;">Noob Learning</h1>
                <p style="color: #00C853; font-size: 0.7rem; letter-spacing: 2px; margin-top: 5px; font-weight: 600;">POWERED BY SARAAH ROBOTICS</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.auth_mode == "login":
      with st.form("login_form"):
        username_in = st.text_input(
            "Phone number, username, or email",
            placeholder="Phone number, username, or email",
        )
        password_in = st.text_input("Password", type="password", placeholder="Password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
          conn = get_db_connection()
          if conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username_in.strip().lower(), password_in),
            )
            row = cursor.fetchone()
            conn.close()
            if row:
              st.session_state.logged_in = True
              st.session_state.user = dict(row)
              st.rerun()
            else:
              st.error("Invalid username or password.")

      st.markdown("</div>", unsafe_allow_html=True)

      st.markdown("<div class='auth-footer-box'>", unsafe_allow_html=True)
      col_txt, col_btn = st.columns([2.5, 1])
      with col_txt:
        st.markdown(
            "<p style='margin: 6px 0 0 0; font-size: 14px; color:"
            " #c9d1d9;'>Don't have an account?</p>",
            unsafe_allow_html=True,
        )
      with col_btn:
        if st.button("Sign up", key="to_signup_btn"):
          st.session_state.auth_mode = "signup"
          st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

    else:
      with st.form("signup_form"):
        st.markdown(
            "<h3 style='text-align: center; font-size: 1.2rem; margin-bottom:"
            " 15px; color: #fff;'>Create a New Account</h3>",
            unsafe_allow_html=True,
        )
        new_user = st.text_input(
            "Username", placeholder="Choose username"
        ).lower()
        new_pass = st.text_input("Password", type="password", placeholder="Password")
        full_name = st.text_input("Full Name", placeholder="Full Name")
        gender_in = st.selectbox("Gender", ["Male", "Female", "Other"])
        dob_in = st.text_input("Date of Birth", placeholder="YYYY-MM-DD")
        acc_type_in = st.selectbox("Account Type", ["Public", "Private"])
        bio = st.text_area("Bio", placeholder="Short Bio")

        if st.form_submit_button("Sign Up", use_container_width=True):
          if new_user and new_pass:
            try:
              register_user(
                  new_user.strip(),
                  new_pass,
                  full_name,
                  bio,
                  "",
                  gender_in,
                  dob_in,
                  acc_type_in,
              )
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
        st.markdown(
            "<p style='margin: 6px 0 0 0; font-size: 14px; color:"
            " #c9d1d9;'>Have an account?</p>",
            unsafe_allow_html=True,
        )
      with col_btn2:
        if st.button("Log in", key="to_login_btn"):
          st.session_state.auth_mode = "login"
          st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)

  st.stop()

# ==============================================================================
# 4. MAIN APP DASHBOARD & NAVIGATION BAR
# ==============================================================================
user = st.session_state.user
username = user["username"]
user_id = user.get("user_id", "N/A")
first_letter = username[0].upper()

header_col1, header_col2, header_col3, header_col4, header_col5, header_col_profile = (
    st.columns([2.5, 1, 1, 1, 1, 1.8])
)

with header_col1:
  st.markdown(
      """
        <div>
            <h3 style='margin:0; color:#ff4b4b; font-size: 1.5rem;'>⚡ Noob Learning</h3>
            <p style='margin:0; font-size: 0.65rem; color:#888; letter-spacing:1px;'>POWERED BY SARAAH ROBOTICS</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

with header_col2:
  if st.button("🏠 Feed", use_container_width=True):
    st.session_state.nav_option = "Feed"
    st.session_state.active_chat_user = None
    st.session_state.active_group_chat = None
    st.session_state.show_edit_profile = False
    st.rerun()
with header_col3:
  if st.button("🎬 Reels", use_container_width=True):
    st.session_state.nav_option = "Reels"
    st.session_state.active_chat_user = None
    st.session_state.active_group_chat = None
    st.session_state.show_edit_profile = False
    st.rerun()
with header_col4:
  if st.button("💬 Chat", use_container_width=True):
    st.session_state.nav_option = "Chat"
    st.session_state.active_chat_user = None
    st.session_state.active_group_chat = None
    st.session_state.show_edit_profile = False
    st.rerun()
with header_col5:
  if st.button("👤 Profile", use_container_width=True):
    st.session_state.nav_option = "Profile"
    st.session_state.active_chat_user = None
    st.session_state.active_group_chat = None
    st.session_state.show_edit_profile = False
    st.rerun()

with header_col_profile:
  prof_col_avatar, prof_col_name, prof_col_btn = st.columns([1, 2, 1.5])
  with prof_col_avatar:
    profile_pic_val = user.get("profile_pic")
    if profile_pic_val and profile_pic_val.startswith("data:image"):
      st.markdown(
          f"""
                <img src='{profile_pic_val}' style='width: 32px; height: 32px; border-radius: 50%; object-fit: cover; margin-top: 5px;'>
            """,
          unsafe_allow_html=True,
      )
    else:
      st.markdown(
          f"""
                <div style="background-color: #00C853; color: #0e1117; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-top: 5px;">
                    {first_letter}
                </div>
            """,
          unsafe_allow_html=True,
      )
  with prof_col_name:
    st.markdown(
        f"<p style='color: white; font-weight: bold; font-size: 13px; margin:"
        f" 8px 0 0 0;'>@{username}</p>",
        unsafe_allow_html=True,
    )
  with prof_col_btn:
    if st.button("Log out", key="logout_top"):
      st.session_state.logged_in = False
      st.session_state.user = None
      st.rerun()

st.markdown(
    "<hr style='border: 0.5px solid #30363d; margin-top: 10px; margin-bottom:"
    " 20px;'>",
    unsafe_allow_html=True,
)

current_tab = st.session_state.get("nav_option", "Feed")

# ==============================================================================
# TAB 1: FEED
# ==============================================================================
if current_tab == "Feed":
  main_col, side_col = st.columns([2.2, 1.2])

  with main_col:
    st.markdown("### 📝 Share a Learning Update or Post")
    with st.form("post_form"):
      caption = st.text_area(
          "What are you learning today?",
          placeholder=(
              "Share code snippets, robotics updates, or learning notes..."
          ),
      )
      if st.form_submit_button("Publish Post 🚀", use_container_width=True):
        if caption.strip():
          conn = get_db_connection()
          if conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                            INSERT INTO reels_posts (username, caption, media_type, timestamp)
                            VALUES (?, ?, ?, ?)
                        """,
                (username, caption, "Post", get_current_ist_time()),
            )
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
        if (
            p_dict["account_type"] == "Private"
            and p_dict["username"] != username
        ):
          continue
        formatted_caption = p_dict["caption"].replace("\n", "<br>")
        st.markdown(
            f"""
                    <div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #30363d;">
                        <span style="background: #00C853; color: #0e1117; padding: 2px 8px; border-radius: 50%; font-weight: bold;">{p_dict['username'][0].upper()}</span>
                        <strong style="color: white; margin-left: 8px;">@{p_dict['username']}</strong>
                        <span style="color: #888; font-size: 11px; margin-left: 10px;">({p_dict['account_type']})</span>
                        <p style="color: #888; font-size: 11px; margin-left: 36px; margin-top: -2px;">{p_dict['timestamp']}</p>
                        <p style="color: #ddd; margin-top: 10px;">{formatted_caption}</p>
                    </div>
                """,
            unsafe_allow_html=True,
        )

  with side_col:
    st.markdown(
        """
            <div style="background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d;">
                <h3 style="color: white; margin-top: 0;">🤖 Saraah Robotics Hub</h3>
                <p style="color: #ccc; font-size: 14px;">Welcome to <b>Noob Learning</b>! Connect with peers, share robotics updates, upload reels, and exchange live text, images, videos, and documents seamlessly.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# TAB 2: REELS
# ==============================================================================
elif current_tab == "Reels":
  st.markdown("### 🎬 Reels Hub")
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
      filtered_reels = [
          dict(r)
          for r in reels
          if r["account_type"] == "Public" or r["username"] == username
      ]
      if not filtered_reels:
        st.info("No reels available yet.")
      for r_dict in filtered_reels:
        formatted_reel_caption = r_dict["caption"].replace("\n", "<br>")
        st.markdown(
            f"""
                    <div style="background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px;">
                        <strong style="color: white;">@{r_dict['username']}</strong>
                        <p style="font-size: 15px; color: #eee; margin-top: 10px;">{formatted_reel_caption}</p>
                    </div>
                """,
            unsafe_allow_html=True,
        )

  with sub_tab_create:
    st.markdown("### Upload a New Reel")
    with st.form("create_reel_form"):
      reel_caption = st.text_area("Reel Caption & Hashtags")
      if st.form_submit_button("Publish Reel 🎬", use_container_width=True):
        if reel_caption.strip():
          conn = get_db_connection()
          if conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                            INSERT INTO reels_posts (username, caption, media_type, timestamp)
                            VALUES (?, ?, ?, ?)
                        """,
                (username, reel_caption, "Reel", get_current_ist_time()),
            )
            conn.commit()
            conn.close()
            st.success("Reel published successfully!")
            st.rerun()

# ==============================================================================
# TAB 3: CHAT & GROUP CHAT SECTION (LAG-FREE FRAGMENT WITH AUTO-SCROLL)
# ==============================================================================
elif current_tab == "Chat":
  chat_mode_col1, chat_mode_col2 = st.columns(2)
  with chat_mode_col1:
    if st.button("💬 Direct Messages", use_container_width=True):
      st.session_state.chat_sub_mode = "Direct Messages"
      st.session_state.active_group_chat = None
      st.rerun()
  with chat_mode_col2:
    if st.button("👥 Group Chats", use_container_width=True):
      st.session_state.chat_sub_mode = "Group Chats"
      st.session_state.active_chat_user = None
      st.rerun()

  st.markdown(
      "<hr style='border: 0.5px solid #30363d; margin: 10px 0;'>",
      unsafe_allow_html=True,
  )

  # ----------------------------------------------------
  # SUB-MODE A: DIRECT MESSAGES
  # ----------------------------------------------------
  if st.session_state.chat_sub_mode == "Direct Messages":
    conn = get_db_connection()
    peers = []
    if conn:
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM users WHERE username != ?", (username,))
      peers = cursor.fetchall()
      conn.close()

    if st.session_state.active_chat_user is None:
      st.markdown("### 💬 Direct Messages & User Search")
      search_query = st.text_input(
          "🔍 Search User ID / Username",
          placeholder="Type a username to search...",
      ).strip().lower()

      filtered_peers = [
          dict(p)
          for p in peers
          if not search_query
          or search_query in p["username"].lower()
          or search_query in p.get("full_name", "").lower()
      ]

      for p_dict in filtered_peers:
        peer_uname = p_dict["username"]
        display_name = p_dict.get("full_name") or peer_uname

        c_info, c_chat = st.columns([5, 1])
        with c_info:
          st.markdown(
              f"**{display_name}** <span style='color:#888;'>(@{peer_uname})"
              "</span>",
              unsafe_allow_html=True,
          )
        with c_chat:
          if st.button("Message 💬", key=f"dm_btn_{peer_uname}"):
            st.session_state.active_chat_user = peer_uname
            st.rerun()
        st.markdown(
            "<hr style='border: 0.2px solid #21262d; margin: 5px 0;'>",
            unsafe_allow_html=True,
        )

    else:
      peer_name = st.session_state.active_chat_user

      conn_p = get_db_connection()
      peer_pic = ""
      if conn_p:
        cur_p = conn_p.cursor()
        cur_p.execute(
            "SELECT profile_pic FROM users WHERE username = ?", (peer_name,)
        )
        p_row = cur_p.fetchone()
        if p_row and p_row["profile_pic"]:
          peer_pic = p_row["profile_pic"]
        conn_p.close()

      c_back, c_logo, c_title, c_del = st.columns([1, 0.6, 3.4, 1])
      with c_back:
        if st.button("⬅ Back"):
          st.session_state.active_chat_user = None
          st.rerun()
      with c_logo:
        if peer_pic and peer_pic.startswith("data:image"):
          st.markdown(
              f"""
                    <img src='{peer_pic}' style='width: 36px; height: 36px; border-radius: 50%; object-fit: cover; margin-top: 2px;'>
                """,
              unsafe_allow_html=True,
          )
        else:
          peer_initial = peer_name[0].upper()
          st.markdown(
              f"""
                    <div style="background-color: #00C853; color: #0e1117; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 15px; margin-top: 2px;">
                        {peer_initial}
                    </div>
                """,
              unsafe_allow_html=True,
          )
      with c_title:
        st.markdown(
            f"<h3 style='margin: 0; color: #fff; padding-top: 2px;'>@{peer_name}</h3>",
            unsafe_allow_html=True,
        )
      with c_del:
        if st.button("🗑️ Delete"):
          conn = get_db_connection()
          if conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                            DELETE FROM messages 
                            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                        """,
                (username, peer_name, peer_name, username),
            )
            conn.commit()
            conn.close()
            st.success("Chat deleted!")
            st.rerun()

      st.markdown(
          "<hr style='border: 0.5px solid #30363d; margin: 10px 0;'>",
          unsafe_allow_html=True,
      )

      @st.fragment(run_every=1.5)
      def render_dm_fragment():
        conn = get_db_connection()
        messages = []
        if conn:
          cursor = conn.cursor()
          cursor.execute(
              """
                        SELECT * FROM messages 
                        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                        ORDER BY id ASC
                    """,
              (username, peer_name, peer_name, username),
          )
          messages = cursor.fetchall()
          conn.close()

        chat_container = st.container(height=400)
        with chat_container:
          if not messages:
            st.info(f"No messages yet with @{peer_name}. Say hello!")
          for msg in messages:
            m = dict(msg)
            is_sender = m["sender"] == username
            align = "flex-end" if is_sender else "flex-start"
            bg = "#1f6feb" if is_sender else "#21262d"

            st.markdown(
                f"""
                        <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                            <div style="background-color: {bg}; color: #fff; padding: 10px 14px; border-radius: 10px; max-width: 70%; word-break: break-word;">
                                <small style="color: #aaa; display: block; font-size: 10px;">{m['sender']} • {m.get('timestamp','')}</small>
                                <p style="margin: 4px 0 0 0;">{m['message']}</p>
                            </div>
                        </div>
                    """,
                unsafe_allow_html=True,
            )
            if m.get("media_data"):
              if m.get("media_type") == "image":
                st.markdown(
                    f"<div style='display: flex; justify-content:"
                    f" {align};'><img src='{m['media_data']}'"
                    " style='max-width: 250px; border-radius: 8px; margin-bottom:"
                    " 10px;'></div>",
                    unsafe_allow_html=True,
                )
              elif m.get("media_type") == "video":
                st.markdown(
                    f"<div style='display: flex; justify-content:"
                    f" {align};'><video controls src='{m['media_data']}'"
                    " style='max-width: 250px; border-radius: 8px; margin-bottom:"
                    " 10px;'></video></div>",
                    unsafe_allow_html=True,
                )
              elif m.get("media_type") == "document":
                st.markdown(
                    f"<div style='display: flex; justify-content:"
                    f" {align};'><a href='{m['media_data']}' download='file'"
                    " target='_blank'>📥 Download Attached Document</a></div>",
                    unsafe_allow_html=True,
                )

        # Robust Auto-Scroll Fix targeting Streamlit container heights instantly
        st.markdown(
            """
                <script>
                    const doc = window.parent.document;
                    const chatContainers = doc.querySelectorAll('[data-testid="stVerticalBlock"]');
                    chatContainers.forEach(container => {
                        if (container.scrollHeight > container.clientHeight) {
                            container.scrollTop = container.scrollHeight;
                        }
                    });
                </script>
            """,
            unsafe_allow_html=True,
        )

        with st.form(key="dm_send_form", clear_on_submit=True):
          c_input, c_file, c_btn = st.columns([3, 2, 1])
          with c_input:
            msg_text = st.text_input(
                "Message",
                placeholder="Type text or use emojis 😊🚀...",
                label_visibility="collapsed",
            )
          with c_file:
            attached_file = st.file_uploader(
                "Media",
                type=["png", "jpg", "jpeg", "mp4", "mov", "pdf", "txt"],
                label_visibility="collapsed",
            )
          with c_btn:
            send_pressed = st.form_submit_button("Send ➔")

          if send_pressed and (msg_text.strip() or attached_file):
            encoded_media = None
            media_type = None
            if attached_file:
              bytes_data = attached_file.getvalue()
              b64_str = base64.b64encode(bytes_data).decode()
              ftype = attached_file.type.split("/")[0]
              if ftype == "image":
                media_type = "image"
                encoded_media = f"data:image/{attached_file.type.split('/')[-1]};base64,{b64_str}"
              elif ftype == "video":
                media_type = "video"
                encoded_media = f"data:video/{attached_file.type.split('/')[-1]};base64,{b64_str}"
              else:
                media_type = "document"
                encoded_media = f"data:application/octet-stream;base64,{b64_str}"

            conn = get_db_connection()
            if conn:
              cursor = conn.cursor()
              cursor.execute(
                  """
                            INSERT INTO messages (sender, receiver, message, media_data, media_type, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                  (
                      username,
                      peer_name,
                      msg_text.strip(),
                      encoded_media,
                      media_type,
                      get_current_ist_time(),
                  ),
              )
              conn.commit()
              conn.close()
              st.rerun()

      render_dm_fragment()

  # ----------------------------------------------------
  # SUB-MODE B: GROUP CHATS
  # ----------------------------------------------------
  else:
    if st.session_state.active_group_chat is None:
      st.markdown("### 👥 Community Group Chats")
      st.markdown(
          "<p style='color: #aaa;'>Create your own study or robotics group or"
          " join existing ones to chat live with multiple users!</p>",
          unsafe_allow_html=True,
      )

      with st.form("create_group_form"):
        st.markdown("#### Create New Group")
        g_name = st.text_input(
            "Group Name", placeholder="e.g., Robotics Innovators 🤖"
        )
        g_desc = st.text_area(
            "Group Description", placeholder="What is this group about?"
        )
        if st.form_submit_button("Create Group 🚀", use_container_width=True):
          if g_name.strip():
            conn = get_db_connection()
            if conn:
              cursor = conn.cursor()
              try:
                cursor.execute(
                    """
                                INSERT INTO chat_groups (group_name, created_by, description, timestamp)
                                VALUES (?, ?, ?, ?)
                            """,
                    (
                        g_name.strip(),
                        username,
                        g_desc.strip(),
                        get_current_ist_time(),
                    ),
                )
                conn.commit()
                st.success(f"Group '{g_name}' created successfully!")
              except sqlite3.IntegrityError:
                st.error("A group with this name already exists.")
              conn.close()
              st.rerun()
          else:
            st.warning("Please provide a group name.")

      st.markdown(
          "<hr style='border: 0.5px solid #30363d;'>", unsafe_allow_html=True
      )
      st.markdown("#### Available Groups")

      conn = get_db_connection()
      groups = []
      if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_groups ORDER BY id DESC")
        groups = cursor.fetchall()
        conn.close()

      if not groups:
        st.info("No active groups found. Create one above to get started!")

      for g in groups:
        g_dict = dict(g)
        g_title = g_dict["group_name"]
        g_creator = g_dict["created_by"]
        g_description = g_dict["description"]

        c_ginfo, c_gjoin = st.columns([4, 1])
        with c_ginfo:
          st.markdown(
              f"""
                    <div style="background-color: #161b22; padding: 12px; border-radius: 8px; border: 1px solid #30363d;">
                        <h4 style="margin: 0; color: #00E676;">{g_title}</h4>
                        <p style="margin: 4px 0; color: #ccc; font-size: 13px;">{g_description}</p>
                        <small style="color: #888;">Created by @{g_creator}</small>
                    </div>
                """,
              unsafe_allow_html=True,
          )
        with c_gjoin:
          st.markdown("<br>", unsafe_allow_html=True)
          if st.button("Join Group ➔", key=f"join_group_{g_title}"):
            st.session_state.active_group_chat = g_title
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    else:
      active_group = st.session_state.active_group_chat
      c_gback, c_gtitle = st.columns([1, 5])
      with c_gback:
        if st.button("⬅ Groups"):
          st.session_state.active_group_chat = None
          st.rerun()
      with c_gtitle:
        st.markdown(
            f"<h3 style='margin: 0; color: #00E676;'>👥 Group: {active_group}</h3>",
            unsafe_allow_html=True,
        )

      st.markdown(
          "<hr style='border: 0.5px solid #30363d; margin: 10px 0;'>",
          unsafe_allow_html=True,
      )

      @st.fragment(run_every=1.5)
      def render_group_chat_fragment():
        conn = get_db_connection()
        group_msgs = []
        if conn:
          cursor = conn.cursor()
          cursor.execute(
              """
                        SELECT * FROM group_messages 
                        WHERE group_name = ?
                        ORDER BY id ASC
                    """,
              (active_group,),
          )
          group_msgs = cursor.fetchall()
          conn.close()

        group_container = st.container(height=400)
        with group_container:
          if not group_msgs:
            st.info(
                f"Welcome to {active_group}! Be the first to send a message or"
                " media file."
            )
          for g_msg in group_msgs:
            gm = dict(g_msg)
            is_sender = gm["sender"] == username
            align = "flex-end" if is_sender else "flex-start"
            bg = "#1f6feb" if is_sender else "#21262d"

            st.markdown(
                f"""
                        <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                            <div style="background-color: {bg}; color: #fff; padding: 10px 14px; border-radius: 10px; max-width: 70%; word-break: break-word;">
                                <small style="color: #00E676; display: block; font-size: 11px; font-weight: bold;">@{gm['sender']} • {gm.get('timestamp','')}</small>
                                <p style="margin: 4px 0 0 0;">{gm['message']}</p>
                            </div>
                        </div>
                    """,
                unsafe_allow_html=True,
            )
            if gm.get("media_data"):
              if gm.get("media_type") == "image":
                st.markdown(
                    f"<div style='display: flex; justify-content:"
                    f" {align};'><img src='{gm['media_data']}'"
                    " style='max-width: 250px; border-radius: 8px; margin-bottom:"
                    " 10px;'></div>",
                    unsafe_allow_html=True,
                )
              elif gm.get("media_type") == "video":
                st.markdown(
                    f"<div style='display: flex; justify-content:"
                    f" {align};'><video controls src='{gm['media_data']}'"
                    " style='max-width: 250px; border-radius: 8px; margin-bottom:"
                    " 10px;'></video></div>",
                    unsafe_allow_html=True,
                )
              elif gm.get("media_type") == "document":
                st.markdown(
                    f"<div style='display: flex; justify-content:"
                    f" {align};'><a href='{gm['media_data']}' download='file'"
                    " target='_blank'>📥 Download Attached Document</a></div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
                <script>
                    const doc = window.parent.document;
                    const chatContainers = doc.querySelectorAll('[data-testid="stVerticalBlock"]');
                    chatContainers.forEach(container => {
                        if (container.scrollHeight > container.clientHeight) {
                            container.scrollTop = container.scrollHeight;
                        }
                    });
                </script>
            """,
            unsafe_allow_html=True,
        )

        with st.form(key="group_send_form", clear_on_submit=True):
          gc_input, gc_file, gc_btn = st.columns([3, 2, 1])
          with gc_input:
            g_msg_text = st.text_input(
                "Group Message",
                placeholder="Type message, emojis 😊🚀...",
                label_visibility="collapsed",
            )
          with gc_file:
            g_attached_file = st.file_uploader(
                "Group Media",
                type=["png", "jpg", "jpeg", "mp4", "mov", "pdf", "txt"],
                label_visibility="collapsed",
            )
          with gc_btn:
            g_send_pressed = st.form_submit_button("Send ➔")

          if g_send_pressed and (g_msg_text.strip() or g_attached_file):
            g_encoded_media = None
            g_media_type = None
            if g_attached_file:
              g_bytes = g_attached_file.getvalue()
              g_b64 = base64.b64encode(g_bytes).decode()
              g_ftype = g_attached_file.type.split("/")[0]
              if g_ftype == "image":
                g_media_type = "image"
                g_encoded_media = f"data:image/{g_attached_file.type.split('/')[-1]};base64,{g_b64}"
              elif g_ftype == "video":
                g_media_type = "video"
                g_encoded_media = f"data:video/{g_attached_file.type.split('/')[-1]};base64,{g_b64}"
              else:
                g_media_type = "document"
                g_encoded_media = f"data:application/octet-stream;base64,{g_b64}"

            conn = get_db_connection()
            if conn:
              cursor = conn.cursor()
              cursor.execute(
                  """
                            INSERT INTO group_messages (group_name, sender, message, media_data, media_type, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                  (
                      active_group,
                      username,
                      g_msg_text.strip(),
                      g_encoded_media,
                      g_media_type,
                      get_current_ist_time(),
                  ),
              )
              conn.commit()
              conn.close()
              st.rerun()

      render_group_chat_fragment()

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

  followers_num, following_num = get_user_stats(username)
  st.markdown(
      f"""
        <div style="background-color: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d;">
            <h2 style="margin: 0; color: white;">{user.get('full_name') or username} <span style="font-size: 15px; color: #888;">(@{username})</span></h2>
            <p style="color: #00C853; font-weight: 600; margin: 4px 0; font-size: 14px;">
                🆔 User ID: {user.get('user_id', 'N/A')} &nbsp;|&nbsp; 
                🔒 Account: {user.get('account_type', 'Public')} &nbsp;|&nbsp; 
                👥 Followers: {followers_num} &nbsp;|&nbsp; Following: {following_num}
            </p>
            <p style="color: #ccc; margin: 8px 0 0 0; font-size: 15px;">{user.get('bio') or 'No bio added yet.'}</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("<br>", unsafe_allow_html=True)
  if st.button("⚙️ Edit Profile Settings"):
    st.session_state.show_edit_profile = not st.session_state.show_edit_profile
    st.rerun()

  if st.session_state.show_edit_profile:
    with st.form("edit_profile"):
      new_username_input = st.text_input("🏷️ Username", value=username)
      new_full = st.text_input("👤 Full Name", value=user.get("full_name", ""))
      new_bio = st.text_area("📝 Bio", value=user.get("bio", ""))
      new_pass = st.text_input(
          "🔑 Change Password (leave blank to keep current)",
          type="password",
          value="",
      )

      if st.form_submit_button("Save Profile Settings", use_container_width=True):
        updated_ok, err_msg = update_user_profile(
            username,
            new_username_input,
            new_full,
            new_bio,
            user.get("profile_pic", ""),
            user.get("gender", "Other"),
            user.get("birth_date", ""),
            user.get("account_type", "Public"),
            new_pass,
        )
        if updated_ok:
          st.session_state.show_edit_profile = False
          st.success("Profile updated successfully!")
          st.rerun()
        else:
          st.error(f"Failed to update profile: {err_msg}")

st.markdown(
    "<p style='text-align: center; color: #555; font-size: 0.7rem;"
    " letter-spacing: 2px; margin-top: 5rem;'>POWERED BY SARAAH ROBOTICS</p>",
    unsafe_allow_html=True,
)
