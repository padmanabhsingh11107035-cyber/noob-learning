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
                timestamp TEXT
            )
        """)
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
          (
              "alex_dev",
              "password123",
              "Alex Rivera",
              "Building cool Python & AI web apps 💻",
              19,
              "Male",
              "2004-10-10",
              "Private",
              "",
          ),
          (
              "noob_coder",
              "password123",
              "Noob Coder",
              "Learning Python step by step 🪀",
              17,
              "Female",
              "2006-12-22",
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

    cursor.execute("PRAGMA table_info(users)")
    columns = [col["name"] for col in cursor.fetchall()]
    for col in [
        "gender",
        "birth_date",
        "account_type",
        "profile_pic",
        "full_name",
        "bio",
    ]:
      if col not in columns:
        try:
          cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except Exception:
          pass
    conn.commit()

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
      except sqlite3.IntegrityError as e:
        error_msg = str(e)
      except Exception as e:
        error_msg = str(e)

    conn.close()
  return success, error_msg


# --- SESSION STATE ---
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
    st.session_state.show_edit_profile = False
    st.rerun()
with header_col3:
  if st.button("🎬 Reels", use_container_width=True):
    st.session_state.nav_option = "Reels"
    st.session_state.active_chat_user = None
    st.session_state.show_edit_profile = False
    st.rerun()
with header_col4:
  if st.button("💬 Chat", use_container_width=True):
    st.session_state.nav_option = "Chat"
    st.session_state.active_chat_user = None
    st.session_state.show_edit_profile = False
    st.rerun()
with header_col5:
  if st.button("👤 Profile", use_container_width=True):
    st.session_state.nav_option = "Profile"
    st.session_state.active_chat_user = None
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
      uploaded_file = st.file_uploader(
          "Upload Image or Video (Optional)", type=["jpg", "png", "mp4"]
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
                <p style="color: #ccc; font-size: 14px;">Welcome to <b>Noob Learning</b>! Connect with peers, share robotics prototypes, upload reels, and exchange live messages with other learners.</p>
                <hr style="border: 0.5px solid #30363d;">
                <b style="color: white;">Platform Features:</b>
                <ul style="color: #aaa; font-size: 13px; padding-left: 20px; line-height: 1.6;">
                    <li>🎬 <b>Reels Hub:</b> Watch and post bite-sized learning reels.</li>
                    <li>💬 <b>Live Chat:</b> Real-time messaging with auto-sync.</li>
                    <li>👤 <b>Custom Profiles:</b> Public/Private badges & bios.</li>
                </ul>
            </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# TAB 2: REELS
# ==============================================================================
elif current_tab == "Reels":
  st.markdown("### 🎬 Reels Hub")
  st.markdown(
      "<p style='color: #888;'>Explore short educational videos and robotics"
      " clips created by the community.</p>",
      unsafe_allow_html=True,
  )

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
        st.info("No reels available yet or accounts are private.")
      for r_dict in filtered_reels:
        formatted_reel_caption = r_dict["caption"].replace("\n", "<br>")
        st.markdown(
            f"""
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
                        <p style="font-size: 15px; color: #eee; margin-top: 10px;">{formatted_reel_caption}</p>
                    </div>
                """,
            unsafe_allow_html=True,
        )

  with sub_tab_create:
    st.markdown("### Upload a New Reel")
    with st.form("create_reel_form"):
      reel_caption = st.text_area(
          "Reel Caption & Hashtags",
          placeholder=(
              "Explain your robotics build or python trick... #Robotics"
              " #Python"
          ),
      )
      reel_file = st.file_uploader(
          "Upload Video File (MP4, MOV)", type=["mp4", "mov"]
      )
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
    st.markdown(
        "<p style='color: #b0b8c1; font-size: 14px;'>Search users by User ID or"
        " username, follow peers, and chat instantly.</p>",
        unsafe_allow_html=True,
    )

    search_query = st.text_input(
        "🔍 Search User ID / Username",
        placeholder="Type a username to search...",
    ).strip().lower()

    st.markdown(
        "<hr style='border: 0.5px solid #30363d;'>", unsafe_allow_html=True
    )

    filtered_peers = []
    for p in peers:
      p_dict = dict(p)
      uname = p_dict.get("username") or ""
      fname = p_dict.get("full_name") or ""
      if (
          not search_query
          or search_query in uname.lower()
          or search_query in fname.lower()
      ):
        filtered_peers.append(p_dict)

    if search_query:
      st.markdown(
          f"**Search Results for '{search_query}' ({len(filtered_peers)}"
          " found):**"
      )
    else:
      st.markdown("**🕒 Recent Community Users:**")

    if not filtered_peers:
      st.info("No users found matching your search.")

    for p_dict in filtered_peers:
      peer_uname = p_dict["username"]
      avatar_char = peer_uname[0].upper()
      display_name = p_dict.get("full_name") or peer_uname
      profile_pic = p_dict.get("profile_pic")
      acc_type = p_dict.get("account_type", "Public")

      conn = get_db_connection()
      is_following = False
      if conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM follows WHERE follower = ? AND following = ?",
            (username, peer_uname),
        )
        if cursor.fetchone():
          is_following = True
        conn.close()

      c_info, c_follow, c_chat = st.columns([4, 1.2, 1])
      with c_info:
        if profile_pic and profile_pic.startswith("data:image"):
          avatar_html = (
              f"<img src='{profile_pic}' style='width: 42px; height: 42px;"
              " border-radius: 50%; object-fit: cover;'>"
          )
        else:
          avatar_html = (
              f"<div style='background-color: #00C853; color: #0e1117; width:"
              f" 42px; height: 42px; border-radius: 50%; display: flex;"
              f" align-items: center; justify-content: center; font-weight:"
              f" bold; font-size: 18px;'>{avatar_char}</div>"
          )

        st.markdown(
            f"""
                <div style="display: flex; align-items: flex-start; gap: 15px; padding: 8px 0;">
                    {avatar_html}
                    <div>
                        <span style="color: white; font-weight: bold; font-size: 15px;">{display_name}</span> 
                        <span style="color: #b0b8c1; font-size: 13px;">(@{peer_uname})</span>
                        <span style="background: #21262d; color: #888; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-left: 5px;">{acc_type}</span>
                        <p style="color: #aaa; font-size: 13px; margin: 4px 0 0 0;">{p_dict.get('bio') or 'No bio added.'}</p>
                    </div>
                </div>
                """,
            unsafe_allow_html=True,
        )

      with c_follow:
        st.markdown("<br>", unsafe_allow_html=True)
        if is_following:
          if st.button("Unfollow", key=f"unfollow_btn_{peer_uname}"):
            conn = get_db_connection()
            if conn:
              cursor = conn.cursor()
              cursor.execute(
                  "DELETE FROM follows WHERE follower = ? AND following = ?",
                  (username, peer_uname),
              )
              conn.commit()
              conn.close()
              st.rerun()
        else:
          if st.button("Follow", key=f"follow_btn_{peer_uname}"):
            conn = get_db_connection()
            if conn:
              cursor = conn.cursor()
              cursor.execute(
                  "INSERT OR IGNORE INTO follows (follower, following) VALUES"
                  " (?, ?)",
                  (username, peer_uname),
              )
              conn.commit()
              conn.close()
              st.rerun()

      with c_chat:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Message 💬", key=f"search_chat_btn_{peer_uname}"):
          st.session_state.active_chat_user = peer_uname
          st.rerun()

      st.markdown(
          "<hr style='border: 0.2px solid #21262d; margin: 5px 0;'>",
          unsafe_allow_html=True,
      )

  else:
    peer_name = st.session_state.active_chat_user

    # Fetch peer user details for profile icon
    conn = get_db_connection()
    peer_data = {}
    if conn:
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM users WHERE username = ?", (peer_name,))
      p_row = cursor.fetchone()
      if p_row:
        peer_data = dict(p_row)
      conn.close()

    peer_pic = peer_data.get("profile_pic", "")
    peer_first_letter = peer_name[0].upper()

    # Chat Header Controls: Back, Title, Theme Selector, Delete Chat, Refresh
    c_back, c_title, c_theme, c_del, c_refresh = st.columns(
        [0.8, 2.2, 1.8, 1.2, 1]
    )
    with c_back:
      if st.button("⬅ Back"):
        st.session_state.active_chat_user = None
        st.rerun()
    with c_title:
      st.markdown(
          f"<h3 style='margin: 0; color: #fff;'>💬 @{peer_name}</h3>",
          unsafe_allow_html=True,
      )
    with c_theme:
      themes_list = [
          "Dark Futuristic",
          "Emerald Cyber",
          "Neon Purple",
          "Sunset Glow",
          "Classic Minimal",
      ]
      current_theme_selection = st.selectbox(
          "Theme",
          themes_list,
          index=(
              themes_list.index(st.session_state.chat_theme)
              if st.session_state.chat_theme in themes_list
              else 0
          ),
          label_visibility="collapsed",
      )
      if current_theme_selection != st.session_state.chat_theme:
        st.session_state.chat_theme = current_theme_selection
        st.rerun()
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
    with c_refresh:
      if st.button("🔄 Refresh"):
        st.rerun()

    st.markdown(
        "<hr style='border: 0.5px solid #30363d; margin: 10px 0;'>",
        unsafe_allow_html=True,
    )

    # Theme Styling Dictionary (5 Options)
    theme_styles = {
        "Dark Futuristic": {
            "bg": "rgba(22, 27, 34, 0.7)",
            "sender_bg": "#1f6feb",
            "receiver_bg": "#21262d",
            "text": "#ffffff",
        },
        "Emerald Cyber": {
            "bg": "rgba(13, 27, 20, 0.8)",
            "sender_bg": "#00C853",
            "receiver_bg": "#14261c",
            "text": "#ffffff",
        },
        "Neon Purple": {
            "bg": "rgba(26, 13, 33, 0.8)",
            "sender_bg": "#9c27b0",
            "receiver_bg": "#24152a",
            "text": "#ffffff",
        },
        "Sunset Glow": {
            "bg": "rgba(33, 18, 13, 0.8)",
            "sender_bg": "#ff5722",
            "receiver_bg": "#2a1c17",
            "text": "#ffffff",
        },
        "Classic Minimal": {
            "bg": "rgba(255, 255, 255, 0.05)",
            "sender_bg": "#3b82f6",
            "receiver_bg": "#374151",
            "text": "#ffffff",
        },
    }
    selected_theme = theme_styles.get(
        st.session_state.chat_theme, theme_styles["Dark Futuristic"]
    )

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

    chat_container = st.container(height=420)
    with chat_container:
      if not messages:
        st.info(f"No messages yet with @{peer_name}. Say hello!")
      for msg in messages:
        m = dict(msg)
        t_str = m.get("timestamp", "")
        time_only = t_str.split(" ")[1][:5] if " " in t_str else t_str

        is_sender = m["sender"] == username

        # Handle Profile Icon with automatic default fallback if not set
        if is_sender:
          user_pic = user.get("profile_pic", "")
          if user_pic and user_pic.startswith("data:image"):
            avatar_html = f"<img src='{user_pic}' style='width: 35px; height: 35px; border-radius: 50%; object-fit: cover;'>"
          else:
            avatar_html = f"<div style='background-color: #00C853; color: #0e1117; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px;'>{first_letter}</div>"

          # Sender bubble layout (Right side)
          st.markdown(
              f"""
                    <div style="display: flex; justify-content: flex-end; align-items: flex-end; gap: 10px; margin-bottom: 12px;">
                        <div style="max-width: 70%; text-align: right;">
                            <div style="background-color: {selected_theme['sender_bg']}; color: {selected_theme['text']}; padding: 10px 14px; border-radius: 12px 12px 0px 12px; display: inline-block; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                                <p style="margin: 0; font-size: 14px; word-break: break-word;">{m['message']}</p>
                            </div>
                            <span style="display: block; font-size: 10px; color: #8b949e; margin-top: 2px;">{time_only} ✓✓</span>
                        </div>
                        {avatar_html}
                    </div>
                    """,
              unsafe_allow_html=True,
          )
        else:
          if peer_pic and peer_pic.startswith("data:image"):
            peer_avatar_html = f"<img src='{peer_pic}' style='width: 35px; height: 35px; border-radius: 50%; object-fit: cover;'>"
          else:
            peer_avatar_html = f"<div style='background-color: #3b82f6; color: #ffffff; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px;'>{peer_first_letter}</div>"

          # Receiver bubble layout (Left side)
          st.markdown(
              f"""
                    <div style="display: flex; justify-content: flex-start; align-items: flex-end; gap: 10px; margin-bottom: 12px;">
                        {peer_avatar_html}
                        <div style="max-width: 70%; text-align: left;">
                            <div style="background-color: {selected_theme['receiver_bg']}; color: {selected_theme['text']}; padding: 10px 14px; border-radius: 12px 12px 12px 0px; display: inline-block; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                                <p style="margin: 0; font-size: 14px; word-break: break-word;">{m['message']}</p>
                            </div>
                            <span style="display: block; font-size: 10px; color: #8b949e; margin-top: 2px;">{time_only}</span>
                        </div>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form(key="whatsapp_chat_form", clear_on_submit=True):
      c_txt, c_btn = st.columns([5, 1])
      with c_txt:
        msg_input = st.text_input(
            "Type a message",
            placeholder=f"Message @{peer_name}...",
            label_visibility="collapsed",
        )
      with c_btn:
        send_submitted = st.form_submit_button(
            "Send ➔", use_container_width=True
        )

      if send_submitted and msg_input.strip():
        conn = get_db_connection()
        if conn:
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO messages (sender, receiver, message, timestamp)
                        VALUES (?, ?, ?, ?)
                    """,
              (
                  username,
                  peer_name,
                  msg_input.strip(),
                  get_current_ist_time(),
              ),
          )
          conn.commit()
          conn.close()
          st.rerun()

    st.markdown(
        "<p style='text-align: center; color: #8b949e; font-size: 12px;"
        " margin-top: 5px;'>🔒 End-to-end encrypted</p>",
        unsafe_allow_html=True,
    )

    try:
      from streamlit_autorefresh import st_autorefresh

      st_autorefresh(interval=3000, limit=None, key="chat_live_sync")
    except ImportError:
      pass

# ==============================================================================
# TAB 4: PROFILE SECTION (WITH EDIT & DELETE ACCOUNT FEATURE)
# ==============================================================================
elif current_tab == "Profile":
  conn = get_db_connection()
  if conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [col["name"] for col in cursor.fetchall()]
    for col in ["gender", "birth_date", "account_type", "profile_pic"]:
      if col not in columns:
        try:
          cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except Exception:
          pass
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
      user = dict(row)
      st.session_state.user = user
    conn.close()

  followers_num, following_num = get_user_stats(username)

  current_pic_data = user.get("profile_pic")
  if current_pic_data and current_pic_data.startswith("data:image"):
    avatar_display_html = (
        f"<img src='{current_pic_data}' style='width: 70px; height: 70px;"
        " border-radius: 50%; object-fit: cover;'>"
    )
  else:
    avatar_display_html = (
        f"<div style='background-color: #00C853; color: #0e1117; width: 70px;"
        f" height: 70px; border-radius: 50%; display: flex; align-items:"
        f" center; justify-content: center; font-weight: bold; font-size:"
        f" 28px;'>{first_letter}</div>"
    )

  st.markdown(
      """
        <div style="background-color: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d;">
    """,
      unsafe_allow_html=True,
  )

  card_col_info, card_col_stats, card_col_settings = st.columns([5.5, 2.2, 1])

  with card_col_info:
    st.markdown(
        f"""
            <div style="display: flex; align-items: center; gap: 20px;">
                {avatar_display_html}
                <div>
                    <h2 style="margin: 0; color: white;">{user.get('full_name') or username} <span style="font-size: 15px; color: #888;">(@{username})</span></h2>
                    <p style="color: #00C853; font-weight: 600; margin: 4px 0; font-size: 14px;">
                        🆔 User ID: {user.get('user_id', 'N/A')} &nbsp;|&nbsp; 
                        🔒 Account: {user.get('account_type', 'Public')} &nbsp;|&nbsp; 
                        ⚧ Gender: {user.get('gender', 'N/A')} &nbsp;|&nbsp; 
                        📅 DOB: {user.get('birth_date', 'N/A')}
                    </p>
                    <p style="color: #ccc; margin: 8px 0 0 0; font-size: 15px;">{user.get('bio') or 'No bio added yet.'}</p>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with card_col_stats:
    st.markdown(
        f"""
            <div style="display: flex; justify-content: space-around; align-items: center; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px 10px; height: 100%; margin-top: 5px;">
                <div style="text-align: center;">
                    <span style="display: block; font-size: 18px; font-weight: bold; color: #00E676;">{followers_num}</span>
                    <span style="font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px;">Followers</span>
                </div>
                <div style="width: 1px; background: rgba(255,255,255,0.1); height: 30px;"></div>
                <div style="text-align: center;">
                    <span style="display: block; font-size: 18px; font-weight: bold; color: #00E676;">{following_num}</span>
                    <span style="font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px;">Following</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with card_col_settings:
    st.markdown(
        "<div style='display: flex; justify-content: flex-end; align-items:"
        " center; height: 100%;'>",
        unsafe_allow_html=True,
    )
    if st.button(
        "⚙️", key="profile_settings_icon_btn", help="Edit Profile Settings"
    ):
      st.session_state.show_edit_profile = (
          not st.session_state.show_edit_profile
      )
      st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

  st.markdown("</div>", unsafe_allow_html=True)
  st.markdown("<br>", unsafe_allow_html=True)

  if st.session_state.show_edit_profile:
    st.markdown(
        """
            <div style="background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #00C853; margin-bottom: 20px;">
                <h3 style="margin-top: 0; color: #00C853;">⚙️ Edit Profile Settings</h3>
                <p style='color: #8b949e; font-size: 0.9rem;'>Update your profile information and username below.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("edit_profile"):
      new_username_input = st.text_input("🏷️ Username", value=username)
      new_full = st.text_input("👤 Full Name", value=user.get("full_name", ""))

      gender_options = ["Male", "Female", "Other"]
      current_gender = user.get("gender", "Other")
      gender_idx = (
          gender_options.index(current_gender)
          if current_gender in gender_options
          else 2
      )
      new_gender = st.selectbox("⚧ Gender", gender_options, index=gender_idx)

      new_dob = st.text_input(
          "📅 Date of Birth (YYYY-MM-DD)", value=user.get("birth_date", "")
      )

      acc_options = ["Public", "Private"]
      current_acc = user.get("account_type", "Public")
      acc_idx = (
          acc_options.index(current_acc) if current_acc in acc_options else 0
      )
      new_acc_type = st.selectbox(
          "🔒 Account Type (Public = Everyone, Private = Friends only)",
          acc_options,
          index=acc_idx,
      )

      new_bio = st.text_area("📝 Bio", value=user.get("bio", ""))

      uploaded_pic_file = st.file_uploader(
          "🖼️ Upload Profile Picture (JPG, PNG)", type=["jpg", "jpeg", "png"]
      )

      new_pass = st.text_input(
          "🔑 Change Password (leave blank to keep current)",
          type="password",
          value="",
      )

      submit_profile = st.form_submit_button(
          "Save Profile Settings", use_container_width=True
      )

      if submit_profile:
        final_pic_base64 = user.get("profile_pic", "")
        if uploaded_pic_file is not None:
          bytes_data = uploaded_pic_file.getvalue()
          encoded = base64.b64encode(bytes_data).decode()
          file_extension = uploaded_pic_file.type.split("/")[-1]
          final_pic_base64 = f"data:image/{file_extension};base64,{encoded}"

        updated_ok, err_msg = update_user_profile(
            username,
            new_username_input,
            new_full,
            new_bio,
            final_pic_base64,
            new_gender,
            new_dob,
            new_acc_type,
            new_pass,
        )

        if updated_ok:
          conn = get_db_connection()
          if conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (new_username_input.strip().lower(),),
            )
            updated_row = cursor.fetchone()
            if updated_row:
              st.session_state.user = dict(updated_row)
            conn.close()

          st.session_state.show_edit_profile = False
          st.success("Profile and username updated successfully!")
          st.rerun()
        else:
          st.error(
              f"Failed to update profile: {err_msg or 'Username might already be' ' taken.'}"
          )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚠️ Danger Zone: Delete Account"):
      st.markdown(
          "<p style='color: #ff4b4b; font-size: 14px;'>Once you delete your"
          " account, all your profile data, posts, reels, and message logs will"
          " be permanently removed.</p>",
          unsafe_allow_html=True,
      )
      confirm_delete = st.text_input(
          "Type your username to confirm deletion",
          placeholder=username,
          key="confirm_delete_input",
      )

      if st.button("Permanently Delete My Account 🗑️", type="primary"):
        if confirm_delete.strip().lower() == username.lower():
          conn = get_db_connection()
          if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            cursor.execute(
                "DELETE FROM reels_posts WHERE username = ?", (username,)
            )
            cursor.execute(
                "DELETE FROM messages WHERE sender = ? OR receiver = ?",
                (username, username),
            )
            cursor.execute(
                "DELETE FROM follows WHERE follower = ? OR following = ?",
                (username, username),
            )
            conn.commit()
            conn.close()

          st.session_state.logged_in = False
          st.session_state.user = None
          st.session_state.show_edit_profile = False
          st.success("Your account has been successfully deleted.")
          st.rerun()
        else:
          st.error("Username confirmation doesn't match. Deletion aborted.")

st.markdown(
    "<p style='text-align: center; color: #555; font-size: 0.7rem;"
    " letter-spacing: 2px; margin-top: 5rem;'>POWERED BY SARAAH ROBOTICS</p>",
    unsafe_allow_html=True,
)
