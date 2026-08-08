import base64
import io
from PIL import Image, ImageDraw, ImageOps
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
# 1. DATABASE SETUP & CONNECTION (ROBUST MIGRATION WITH GROUP ROLES & UNSEEN TRACKING)
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

    # Performance PRAGMAs - big impact on write/read speed for sqlite under Streamlit reruns
    try:
      cursor.execute("PRAGMA journal_mode=WAL")
      cursor.execute("PRAGMA synchronous=NORMAL")
      cursor.execute("PRAGMA temp_store=MEMORY")
    except Exception as ex:
      logger.warning(f"Could not set performance PRAGMAs: {ex}")

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
                timestamp TEXT,
                is_read INTEGER DEFAULT 0
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
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                username TEXT,
                role TEXT,
                UNIQUE(group_name, username)
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

    # Check columns for messages table
    cursor.execute("PRAGMA table_info(messages)")
    m_cols = [col["name"] for col in cursor.fetchall()]
    if "is_read" not in m_cols:
      try:
        cursor.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
      except Exception:
        pass
    if "media_data" not in m_cols:
      try:
        cursor.execute("ALTER TABLE messages ADD COLUMN media_data TEXT")
      except Exception:
        pass
    if "media_type" not in m_cols:
      try:
        cursor.execute("ALTER TABLE messages ADD COLUMN media_type TEXT")
      except Exception:
        pass

    # Indexes - these are the biggest lag fix. Without them every chat/follow/unread
    # lookup does a full table scan, which gets slower and slower as messages grow.
    try:
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_messages_sender_receiver ON messages(sender, receiver)"
      )
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_messages_receiver_read ON messages(receiver, is_read)"
      )
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower)"
      )
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following)"
      )
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_group_messages_group ON group_messages(group_name)"
      )
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_name)"
      )
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(username)"
      )
      cursor.execute(
          "CREATE INDEX IF NOT EXISTS idx_reels_posts_username ON reels_posts(username)"
      )
    except Exception as ex:
      logger.warning(f"Could not create indexes: {ex}")

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
          cursor.execute(
              "UPDATE chat_groups SET created_by = ? WHERE created_by = ?",
              (target_username, old_username),
          )
          cursor.execute(
              "UPDATE group_members SET username = ? WHERE username = ?",
              (target_username, old_username),
          )
          cursor.execute(
              "UPDATE group_messages SET sender = ? WHERE sender = ?",
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
if "app_theme" not in st.session_state:
  st.session_state.app_theme = "Dark"
if "selected_reel_user" not in st.session_state:
  st.session_state.selected_reel_user = None

# ==============================================================================
# 2. DYNAMIC THEME & CSS ENGINE (RESTORED THEME OPTION & STABLE BUTTON FIXES)
# ==============================================================================
is_dark = st.session_state.app_theme == "Dark"
bg_gradient = (
    "linear-gradient(135deg, #0d1117 0%, #161b22 100%)"
    if is_dark
    else "linear-gradient(135deg, #f4f6f8 0%, #e9ecef 100%)"
)
card_bg = "rgba(22, 27, 34, 0.85)" if is_dark else "rgba(255, 255, 255, 0.95)"
text_color = "#ffffff" if is_dark else "#1f2428"
sub_text_color = "#8b949e" if is_dark else "#586069"
border_color = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.1)"
input_bg = "rgba(13, 17, 23, 0.7)" if is_dark else "#ffffff"

st.markdown(
    f"""
<style>
    .stApp {{
        background: {bg_gradient};
        color: {text_color};
    }}
    header {{visibility: hidden;}}
    
    .auth-container {{
        max-width: 380px;
        margin: 40px auto;
        background: {card_bg};
        backdrop-filter: blur(12px);
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 35px 30px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
    }}
    
    .auth-footer-box {{
        max-width: 380px;
        margin: 15px auto 40px auto;
        background: {card_bg};
        backdrop-filter: blur(12px);
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 20px 30px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    }}

    /* Robust Button Styling to Ensure 100% Clickability */
    div.stButton > button, button[kind="secondary"], button[kind="primary"], [data-testid="baseButton-secondary"], [data-testid="baseButton-primary"] {{
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
        cursor: pointer !important;
    }}
    
    div.stButton > button *, button[kind="secondary"] *, button[kind="primary"] * {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: 900 !important;
    }}

    div.stButton > button:hover, button[kind="secondary"]:hover, button[kind="primary"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(0, 230, 118, 0.7) !important;
        background: #69F0AE !important;
        background-color: #69F0AE !important;
        color: #000000 !important;
    }}
    
    input, textarea, select {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}

    .stTextInput label, .stSelectbox label, .stTextArea label, .stFileUploader label {{
        color: {text_color} !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }}

    .unread-badge {{
        background-color: #00C853;
        color: #000;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 12px;
        font-weight: 900;
        float: right;
        display: inline-block;
        min-width: 22px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 200, 83, 0.5);
    }}
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
                <h1 style="font-family: 'Brush Script MT', cursive, sans-serif; font-size: 3rem; font-weight: normal; margin: 0; background: linear-gradient(45deg, #00E676, #00C853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 1px;">Noob Learning</h1>
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
            "<p style='margin: 6px 0 0 0; font-size: 14px;'>Don't have an"
            " account?</p>",
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
            " 15px;'>Create a New Account</h3>",
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
            "<p style='margin: 6px 0 0 0; font-size: 14px;'>Have an"
            " account?</p>",
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
first_letter = username[0].upper() if username else "U"


def _make_avatar_bytes(profile_value, letter, size=56, rainbow=False):
  """Create a reliable PNG avatar without embedding data: URLs in HTML."""
  try:
    if profile_value and isinstance(profile_value, str) and profile_value.startswith("data:image"):
      encoded = profile_value.split(",", 1)[1]
      image = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGBA")
      image = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
    else:
      image = Image.new("RGBA", (size, size), (0, 200, 83, 255))
      draw = ImageDraw.Draw(image)
      text = (letter or "U")[:1].upper()
      bbox = draw.textbbox((0, 0), text)
      tw = bbox[2] - bbox[0]
      th = bbox[3] - bbox[1]
      draw.text(((size - tw) / 2, (size - th) / 2 - bbox[1]), text, fill=(14, 17, 23, 255))

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    image.putalpha(mask)

    if rainbow:
      canvas = Image.new("RGBA", (size + 8, size + 8), (0, 0, 0, 0))
      ring = ImageDraw.Draw(canvas)
      colors = [
          (255, 0, 76, 255),
          (255, 122, 0, 255),
          (255, 214, 0, 255),
          (0, 230, 118, 255),
          (0, 176, 255, 255),
          (124, 77, 255, 255),
          (255, 0, 168, 255),
      ]
      box = (1, 1, size + 6, size + 6)
      step = 360 / len(colors)
      for index, color in enumerate(colors):
        ring.arc(box, index * step, (index + 1) * step, fill=color, width=4)
      canvas.alpha_composite(image, (4, 4))
      return canvas

    return image
  except Exception:
    fallback = Image.new("RGBA", (size, size), (0, 200, 83, 255))
    draw = ImageDraw.Draw(fallback)
    draw.ellipse((0, 0, size - 1, size - 1), fill=(0, 200, 83, 255))
    return fallback


# The navigation header is hidden while a conversation is open. This gives the
# direct-chat screen the clean, separate-page feel requested by the user.
show_main_nav = (
    st.session_state.active_chat_user is None
    and st.session_state.active_group_chat is None
)

if show_main_nav:
  (
      header_col1,
      header_col2,
      header_col3,
      header_col4,
      header_col5,
      header_col_theme,
      header_col_profile,
  ) = st.columns([2.2, 0.9, 0.9, 0.9, 0.9, 1.1, 1.6])

  with header_col1:
    st.markdown(
        """
          <div>
              <h3 style='margin:0; color:#00E676; font-size: 1.4rem;'>⚡ Noob Learning</h3>
              <p style='margin:0; font-size: 0.65rem; color:#888; letter-spacing:1px;'>POWERED BY SARAAH ROBOTICS</p>
          </div>
      """,
        unsafe_allow_html=True,
    )

  with header_col2:
    if st.button("🏠 Feed", use_container_width=True, key="nav_feed"):
      st.session_state.nav_option = "Feed"
      st.session_state.active_chat_user = None
      st.session_state.active_group_chat = None
      st.session_state.show_edit_profile = False
      st.rerun()

  with header_col3:
    if st.button("🎬 Reels", use_container_width=True, key="nav_reels"):
      st.session_state.nav_option = "Reels"
      st.session_state.active_chat_user = None
      st.session_state.active_group_chat = None
      st.session_state.show_edit_profile = False
      st.rerun()

  with header_col4:
    if st.button("💬 Chat", use_container_width=True, key="nav_chat"):
      st.session_state.nav_option = "Chat"
      st.session_state.active_chat_user = None
      st.session_state.active_group_chat = None
      st.session_state.show_edit_profile = False
      st.rerun()

  with header_col5:
    if st.button("👤 Profile", use_container_width=True, key="nav_profile"):
      st.session_state.nav_option = "Profile"
      st.session_state.active_chat_user = None
      st.session_state.active_group_chat = None
      st.session_state.show_edit_profile = False
      st.rerun()

  with header_col_theme:
    new_theme = st.selectbox(
        "Theme",
        ["Dark", "Light"],
        index=0 if st.session_state.app_theme == "Dark" else 1,
        label_visibility="collapsed",
        key="top_theme_selector",
    )
    if new_theme != st.session_state.app_theme:
      st.session_state.app_theme = new_theme
      st.rerun()

  with header_col_profile:
    prof_col_avatar, prof_col_name, prof_col_btn = st.columns([1, 2, 1.5])
    with prof_col_avatar:
      st.image(
          _make_avatar_bytes(user.get("profile_pic", ""), first_letter, 32, False),
          width=32,
      )
    with prof_col_name:
      st.markdown(
          f"<p style='font-weight: bold; font-size: 13px; margin: 8px 0 0 0;'>@{username}</p>",
          unsafe_allow_html=True,
      )
    with prof_col_btn:
      if st.button("Log out", key="logout_top"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.active_chat_user = None
        st.session_state.active_group_chat = None
        st.rerun()

  st.markdown(
      f"<hr style='border: 0.5px solid {border_color}; margin-top: 10px; margin-bottom: 20px;'>",
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
                    <div style="background-color: {card_bg}; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid {border_color};">
                        <span style="background: #00C853; color: #0e1117; padding: 2px 8px; border-radius: 50%; font-weight: bold;">{p_dict['username'][0].upper()}</span>
                        <strong style="margin-left: 8px;">@{p_dict['username']}</strong>
                        <span style="color: #888; font-size: 11px; margin-left: 10px;">({p_dict['account_type']})</span>
                        <p style="color: #888; font-size: 11px; margin-left: 36px; margin-top: -2px;">{p_dict['timestamp']}</p>
                        <p style="margin-top: 10px;">{formatted_caption}</p>
                    </div>
                """,
            unsafe_allow_html=True,
        )

  with side_col:
    st.markdown(
        f"""
            <div style="background-color: {card_bg}; padding: 20px; border-radius: 12px; border: 1px solid {border_color};">
                <h3 style="margin-top: 0;">🤖 Saraah Robotics Hub</h3>
                <p style="font-size: 14px;">Welcome to <b>Noob Learning</b>! Connect with peers, share robotics updates, upload reels, and exchange live text, images, videos, and documents seamlessly.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# TAB 2: REELS
# ==============================================================================
elif current_tab == "Reels":
  st.markdown("### 🎬 Reels Hub")

  # ---------------------------------------------------------------------------
  # TOP REEL / STORY STRIP
  # ---------------------------------------------------------------------------
  conn_story = get_db_connection()
  story_users = []
  if conn_story:
    cur_story = conn_story.cursor()
    cur_story.execute(
        """
        SELECT r.username, MAX(r.id) AS latest_id, u.profile_pic, u.user_id
        FROM reels_posts r
        JOIN users u ON r.username = u.username
        WHERE r.media_type = 'Reel'
        GROUP BY r.username
        ORDER BY latest_id DESC
        """
    )
    story_users = cur_story.fetchall()
    conn_story.close()

  if story_users:
    st.markdown("#### 🌈 Latest Reels")
    story_cols = st.columns(min(len(story_users), 6))
    for index, story in enumerate(story_users[:6]):
      story_dict = dict(story)
      story_user = story_dict["username"]
      with story_cols[index]:
        st.image(
            _make_avatar_bytes(
                story_dict.get("profile_pic", ""),
                story_user[:1],
                58,
                True,
            ),
            width=58,
        )
        if st.button(
            f"@{story_user}",
            key=f"story_reel_{story_user}",
            use_container_width=True,
        ):
          st.session_state.selected_reel_user = story_user
          st.rerun()

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
          if (r["account_type"] == "Public" or r["username"] == username)
          and (
              st.session_state.selected_reel_user is None
              or r["username"] == st.session_state.selected_reel_user
          )
      ]
      if st.session_state.selected_reel_user is not None:
        if st.button("← Show all reels", key="clear_reel_filter"):
          st.session_state.selected_reel_user = None
          st.rerun()
      if not filtered_reels:
        st.info("No reels available yet.")
      for r_dict in filtered_reels:
        formatted_reel_caption = r_dict["caption"].replace("\n", "<br>")
        st.markdown(
            f"""
                    <div style="background-color: {card_bg}; padding: 20px; border-radius: 12px; border: 1px solid {border_color}; margin-bottom: 20px;">
                        <strong>@{r_dict['username']}</strong>
                        <p style="font-size: 15px; margin-top: 10px;">{formatted_reel_caption}</p>
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
# TAB 3: CHAT & PRIVATE GROUP SECTION WITH ADMIN CONTROLS
# ==============================================================================
elif current_tab == "Chat":
  if st.session_state.active_chat_user is None and st.session_state.active_group_chat is None:
    chat_mode_col1, chat_mode_col2 = st.columns(2)
    with chat_mode_col1:
      if st.button("💬 Direct Messages", use_container_width=True, key="chat_mode_direct"):
        st.session_state.chat_sub_mode = "Direct Messages"
        st.session_state.active_group_chat = None
        st.rerun()
    with chat_mode_col2:
      if st.button("👥 Group Chats", use_container_width=True, key="chat_mode_groups"):
        st.session_state.chat_sub_mode = "Group Chats"
        st.session_state.active_chat_user = None
        st.rerun()

    st.markdown(
        f"<hr style='border: 0.5px solid {border_color}; margin: 10px 0;'>",
        unsafe_allow_html=True,
    )


  def get_user_avatar_html(uname, avatar_cache=None):
    # PERF FIX: previously this opened a brand new sqlite connection and ran a
    # query for EVERY single chat bubble on EVERY rerun (N+1 queries), which is
    # the main cause of chat lag as message history grows. Now it reads from a
    # small dict that's fetched once per render via a single batched query.
    u_pic = ""
    if avatar_cache is not None:
      u_pic = avatar_cache.get(uname, "") or ""
    else:
      conn_u = get_db_connection()
      if conn_u:
        cur_u = conn_u.cursor()
        cur_u.execute("SELECT profile_pic FROM users WHERE username = ?", (uname,))
        res = cur_u.fetchone()
        if res and res["profile_pic"]:
          u_pic = res["profile_pic"]
        conn_u.close()

    if u_pic and u_pic.startswith("data:image"):
      return f"<img src='{u_pic}' style='width: 28px; height: 28px; border-radius: 50%; object-fit: cover; vertical-align: middle; margin-right: 6px;'>"
    else:
      initial = uname[0].upper() if uname else "U"
      return f"<span style='display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background-color: #00C853; color: #0e1117; border-radius: 50%; font-weight: bold; font-size: 12px; vertical-align: middle; margin-right: 6px;'>{initial}</span>"


  # ----------------------------------------------------
  # SUB-MODE A: DIRECT MESSAGES
  # ----------------------------------------------------
  if st.session_state.chat_sub_mode == "Direct Messages":
    conn = get_db_connection()
    peers = []
    if conn:
      cursor = conn.cursor()
      cursor.execute(
          """
          SELECT user_id, username, full_name, profile_pic, account_type
          FROM users
          WHERE username != ?
          ORDER BY username COLLATE NOCASE ASC
          """,
          (username,),
      )
      peers = cursor.fetchall()
      conn.close()

    # -------------------------------------------------------------------------
    # OPEN CONVERSATION
    # -------------------------------------------------------------------------
    if st.session_state.active_chat_user is not None:
      peer_name = st.session_state.active_chat_user

      conn_peer = get_db_connection()
      peer_data = None
      if conn_peer:
        cur_peer = conn_peer.cursor()
        cur_peer.execute(
            """
            SELECT user_id, username, full_name, profile_pic, account_type
            FROM users
            WHERE username = ?
            """,
            (peer_name,),
        )
        peer_data = cur_peer.fetchone()
        conn_peer.close()

      if peer_data is None:
        st.session_state.active_chat_user = None
        st.rerun()

      peer_dict = dict(peer_data)
      peer_user_id = peer_dict.get("user_id", "N/A")
      peer_pic = peer_dict.get("profile_pic", "") or ""

      # Optional one-second refresh. If the package is not installed, the chat
      # remains fully functional and refreshes whenever the user interacts.
      try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(
            interval=1000,
            limit=None,
            key=f"live_dm_{username}_{peer_name}",
        )
      except ImportError:
        pass

      # Mark incoming messages as read in one query.
      conn_mark = get_db_connection()
      if conn_mark:
        cur_mark = conn_mark.cursor()
        cur_mark.execute(
            """
            UPDATE messages
            SET is_read = 1
            WHERE sender = ? AND receiver = ? AND (is_read = 0 OR is_read IS NULL)
            """,
            (peer_name, username),
        )
        conn_mark.commit()
        conn_mark.close()

      # -----------------------------------------------------------------------
      # CHAT-ONLY HEADER
      # -----------------------------------------------------------------------
      back_col, avatar_col, title_col, delete_col = st.columns([0.65, 0.75, 4.4, 0.9])

      with back_col:
        if st.button("⬅", key="dm_back_button", help="Back to chats"):
          st.session_state.active_chat_user = None
          st.rerun()

      with avatar_col:
        st.image(
            _make_avatar_bytes(peer_pic, peer_name[:1], 42, True),
            width=42,
        )

      with title_col:
        st.markdown(
            f"""
            <div style="padding-top:2px;">
                <div style="font-size:18px;font-weight:800;">ID: {peer_user_id}</div>
                <div style="color:#888;font-size:11px;">@{peer_name}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

      with delete_col:
        if st.button("🗑️", key="delete_direct_chat", help="Delete this chat"):
          conn_delete = get_db_connection()
          if conn_delete:
            cur_delete = conn_delete.cursor()
            cur_delete.execute(
                """
                DELETE FROM messages
                WHERE (sender = ? AND receiver = ?)
                   OR (sender = ? AND receiver = ?)
                """,
                (username, peer_name, peer_name, username),
            )
            conn_delete.commit()
            conn_delete.close()
          st.success("Chat deleted!")
          st.rerun()

      st.markdown(
          f"<hr style='border:0.5px solid {border_color};margin:8px 0 10px 0;'>",
          unsafe_allow_html=True,
      )

      # -----------------------------------------------------------------------
      # LOAD ONLY THE ACTIVE CONVERSATION
      # -----------------------------------------------------------------------
      conn = get_db_connection()
      messages = []
      if conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, sender, receiver, message, media_data, media_type, timestamp
            FROM messages
            WHERE (sender = ? AND receiver = ?)
               OR (sender = ? AND receiver = ?)
            ORDER BY id ASC
            """,
            (username, peer_name, peer_name, username),
        )
        messages = cursor.fetchall()
        conn.close()

      avatar_cache = {
          username: user.get("profile_pic", "") or "",
          peer_name: peer_pic,
      }

      chat_container = st.container(height=500)
      with chat_container:
        if not messages:
          st.info(f"No messages yet with @{peer_name}. Say hello!")

        for msg in messages:
          m = dict(msg)
          is_sender = m["sender"] == username
          align = "flex-end" if is_sender else "flex-start"
          bubble_bg = "#1f6feb" if is_sender else "#21262d"
          sender_record = user if is_sender else peer_dict
          sender_id = sender_record.get("user_id", "N/A")

          bubble_cols = st.columns([1, 8, 1])
          target = bubble_cols[2] if is_sender else bubble_cols[0]
          with target:
            st.image(
                _make_avatar_bytes(
                    avatar_cache.get(m["sender"], ""),
                    m["sender"][:1],
                    30,
                    False,
                ),
                width=30,
            )

          st.markdown(
              f"""
              <div style="display:flex;justify-content:{align};margin:0 0 6px 0;">
                <div style="background:{bubble_bg};color:#fff;padding:9px 13px;border-radius:12px;max-width:72%;word-break:break-word;">
                  <div style="font-size:10px;color:#b8c0cc;margin-bottom:3px;">
                    ID: {sender_id} · @{m['sender']} · {m.get('timestamp','')}
                  </div>
                  <div style="font-size:14px;line-height:1.35;">{m.get('message','')}</div>
                </div>
              </div>
              """,
              unsafe_allow_html=True,
          )

          if m.get("media_data"):
            if m.get("media_type") == "image":
              try:
                media_bytes = base64.b64decode(m["media_data"].split(",", 1)[1])
                st.image(media_bytes, width=260)
              except Exception:
                pass
            elif m.get("media_type") == "video":
              try:
                media_bytes = base64.b64decode(m["media_data"].split(",", 1)[1])
                st.video(media_bytes)
              except Exception:
                pass
            elif m.get("media_type") == "document":
              st.download_button(
                  "📥 Download attachment",
                  data=base64.b64decode(m["media_data"].split(",", 1)[1]),
                  file_name="attachment",
                  key=f"dm_download_{m['id']}",
              )

      # -----------------------------------------------------------------------
      # MESSAGE COMPOSER
      # -----------------------------------------------------------------------
      with st.form(key="dm_send_form", clear_on_submit=True):
        c_input, c_file, c_btn = st.columns([3.5, 2, 1])

        with c_input:
          msg_text = st.text_input(
              "Message",
              placeholder="Type a message or use emojis 😊🚀...",
              label_visibility="collapsed",
          )

        with c_file:
          attached_file = st.file_uploader(
              "Media",
              type=["png", "jpg", "jpeg", "mp4", "mov", "pdf", "txt"],
              label_visibility="collapsed",
              key="dm_media_uploader",
          )

        with c_btn:
          send_pressed = st.form_submit_button("Send ➔", use_container_width=True)

        if send_pressed and (msg_text.strip() or attached_file):
          encoded_media = None
          media_type = None

          if attached_file:
            bytes_data = attached_file.getvalue()
            b64_str = base64.b64encode(bytes_data).decode()
            file_type = attached_file.type or "application/octet-stream"
            main_type = file_type.split("/")[0]
            if main_type == "image":
              media_type = "image"
            elif main_type == "video":
              media_type = "video"
            else:
              media_type = "document"
            encoded_media = f"data:{file_type};base64,{b64_str}"

          conn_send = get_db_connection()
          if conn_send:
            cur_send = conn_send.cursor()
            cur_send.execute(
                """
                INSERT INTO messages
                (sender, receiver, message, media_data, media_type, timestamp, is_read)
                VALUES (?, ?, ?, ?, ?, ?, 0)
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
            conn_send.commit()
            conn_send.close()
            st.rerun()

    # -------------------------------------------------------------------------
    # CHAT LIST
    # -------------------------------------------------------------------------
    else:
      st.markdown("### 💬 Direct Messages")

      # Top reel/story strip: only users who currently have at least one Reel.
      conn_story = get_db_connection()
      story_users = []
      if conn_story:
        cur_story = conn_story.cursor()
        cur_story.execute(
            """
            SELECT r.username, MAX(r.id) AS latest_id, u.user_id, u.profile_pic
            FROM reels_posts r
            JOIN users u ON r.username = u.username
            WHERE r.media_type = 'Reel'
            GROUP BY r.username
            ORDER BY latest_id DESC
            """
        )
        story_users = cur_story.fetchall()
        conn_story.close()

      if story_users:
        st.markdown("#### 🌈 Reels")
        story_cols = st.columns(min(len(story_users), 6))
        for index, story in enumerate(story_users[:6]):
          story_dict = dict(story)
          story_user = story_dict["username"]
          with story_cols[index]:
            st.image(
                _make_avatar_bytes(
                    story_dict.get("profile_pic", ""),
                    story_user[:1],
                    56,
                    True,
                ),
                width=56,
            )
            st.caption(f"ID {story_dict.get('user_id','N/A')}")
            if st.button(
                f"@{story_user}",
                key=f"chat_story_{story_user}",
                use_container_width=True,
            ):
              st.session_state.active_chat_user = story_user
              st.rerun()

      search_query = st.text_input(
          "🔍 Search User ID / Username",
          placeholder="Search by User ID, username, or name...",
          key="chat_user_search",
      ).strip().lower()

      filtered_peers = []
      for peer in peers:
        p = dict(peer)
        if (
            not search_query
            or search_query in p["username"].lower()
            or search_query in (p.get("full_name") or "").lower()
            or search_query == str(p.get("user_id", ""))
        ):
          filtered_peers.append(p)

      unread_map = {}
      conn_unread = get_db_connection()
      if conn_unread:
        cur_unread = conn_unread.cursor()
        cur_unread.execute(
            """
            SELECT sender, COUNT(*) AS cnt
            FROM messages
            WHERE receiver = ? AND (is_read = 0 OR is_read IS NULL)
            GROUP BY sender
            """,
            (username,),
        )
        for row in cur_unread.fetchall():
          unread_map[row["sender"]] = row["cnt"]
        conn_unread.close()

      for p_dict in filtered_peers:
        peer_uname = p_dict["username"]
        display_name = p_dict.get("full_name") or peer_uname
        peer_id = p_dict.get("user_id", "N/A")
        peer_pic = p_dict.get("profile_pic", "") or ""
        unread_count = unread_map.get(peer_uname, 0)

        c_avatar, c_info, c_chat = st.columns([0.8, 4.1, 1.1])

        with c_avatar:
          st.image(
              _make_avatar_bytes(peer_pic, peer_uname[:1], 42, False),
              width=42,
          )

        with c_info:
          badge = f" · {unread_count} new" if unread_count else ""
          if st.button(
              f"ID: {peer_id} · @{peer_uname}{badge}",
              key=f"open_dm_info_{peer_uname}",
              use_container_width=True,
          ):
            st.session_state.active_chat_user = peer_uname
            st.rerun()
          st.caption(display_name)

        with c_chat:
          if st.button("Chat ➔", key=f"dm_btn_{peer_uname}"):
            conn_read = get_db_connection()
            if conn_read:
              cur_read = conn_read.cursor()
              cur_read.execute(
                  """
                  UPDATE messages
                  SET is_read = 1
                  WHERE sender = ? AND receiver = ?
                  """,
                  (peer_uname, username),
              )
              conn_read.commit()
              conn_read.close()
            st.session_state.active_chat_user = peer_uname
            st.rerun()

        st.markdown(
            f"<hr style='border:0.2px solid {border_color};margin:5px 0;'>",
            unsafe_allow_html=True,
        )

  # ----------------------------------------------------
  # SUB-MODE B: GROUP CHATS (PRIVATE WITH ADMIN CONTROLS)
  # ----------------------------------------------------
  else:
    if st.session_state.active_group_chat is None:
      st.markdown("### 👥 Private Group Chats")
      st.markdown(
          "<p style='color: #888;'>Create your own private group and select user"
          " IDs to add members. Only added members can see and join the"
          " group!</p>",
          unsafe_allow_html=True,
      )

      # Fetch all users for member selection
      conn_u = get_db_connection()
      all_users = []
      if conn_u:
        cur_u = conn_u.cursor()
        cur_u.execute("SELECT username FROM users WHERE username != ?", (username,))
        all_users = [row["username"] for row in cur_u.fetchall()]
        conn_u.close()

      with st.form("create_group_form"):
        st.markdown("#### Create Private Group")
        g_name = st.text_input(
            "Group Name", placeholder="e.g., Robotics Innovators 🤖"
        )
        g_desc = st.text_area(
            "Group Description", placeholder="What is this group about?"
        )
        selected_members = st.multiselect(
            "Select Users to Add",
            options=all_users,
            placeholder="Choose user IDs to include...",
        )

        if st.form_submit_button("Create Group 🚀", use_container_width=True):
          if g_name.strip():
            conn = get_db_connection()
            if conn:
              cursor = conn.cursor()
              try:
                # Insert Group
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
                # Insert Creator as Admin
                cursor.execute(
                    """
                                INSERT OR IGNORE INTO group_members (group_name, username, role)
                                VALUES (?, ?, ?)
                            """,
                    (g_name.strip(), username, "Admin"),
                )
                # Insert Selected Members
                for member in selected_members:
                  cursor.execute(
                      """
                                    INSERT OR IGNORE INTO group_members (group_name, username, role)
                                    VALUES (?, ?, ?)
                                """,
                      (g_name.strip(), member, "Member"),
                  )
                conn.commit()
                st.success(
                    f"Private group '{g_name}' created successfully with"
                    f" {len(selected_members)} initial members!"
                )
              except sqlite3.IntegrityError:
                st.error("A group with this name already exists.")
              conn.close()
              st.rerun()
          else:
            st.warning("Please provide a group name.")

      st.markdown(
          f"<hr style='border: 0.5px solid {border_color};'>",
          unsafe_allow_html=True,
      )
      st.markdown("#### Groups You Are In")

      conn = get_db_connection()
      user_groups = []
      if conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                    SELECT g.* FROM chat_groups g
                    JOIN group_members m ON g.group_name = m.group_name
                    WHERE m.username = ?
                    ORDER BY g.id DESC
                """,
            (username,),
        )
        user_groups = cursor.fetchall()
        conn.close()

      if not user_groups:
        st.info(
            "You are not part of any groups yet. Create one above or ask an"
            " admin to add you!"
        )

      for g in user_groups:
        g_dict = dict(g)
        g_title = g_dict["group_name"]
        g_creator = g_dict["created_by"]
        g_description = g_dict["description"]

        c_ginfo, c_gjoin = st.columns([4, 1])
        with c_ginfo:
          st.markdown(
                    f"""
                    <div style="background-color: {card_bg}; padding: 12px; border-radius: 8px; border: 1px solid {border_color};">
                        <h4 style="margin: 0; color: #00E676;">{g_title}</h4>
                        <p style="margin: 4px 0; font-size: 13px;">{g_description}</p>
                        <small style="color: #888;">Created by @{g_creator}</small>
                    </div>
                """,
              unsafe_allow_html=True,
          )
        with c_gjoin:
          st.markdown("<br>", unsafe_allow_html=True)
          if st.button("Open ➔", key=f"join_group_{g_title}"):
            st.session_state.active_group_chat = g_title
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    else:
      active_group = st.session_state.active_group_chat

      # Check if user is admin of this group
      conn_role = get_db_connection()
      user_role = "Member"
      if conn_role:
        cur_r = conn_role.cursor()
        cur_r.execute(
            "SELECT role FROM group_members WHERE group_name = ? AND username = ?",
            (active_group, username),
        )
        r_res = cur_r.fetchone()
        if r_res:
          user_role = r_res["role"]
        conn_role.close()

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

      # Admin Management Expander
      if user_role == "Admin":
        with st.expander("🛠️ Admin Controls (Manage Members & Admins)"):
          conn_m = get_db_connection()
          current_members = []
          all_system_users = []
          if conn_m:
            cur_m = conn_m.cursor()
            cur_m.execute(
                "SELECT username, role FROM group_members WHERE group_name ="
                " ?",
                (active_group,),
            )
            current_members = cur_m.fetchall()
            cur_m.execute(
                "SELECT username FROM users WHERE username NOT IN (SELECT username"
                " FROM group_members WHERE group_name = ?)",
                (active_group,),
            )
            all_system_users = [row["username"] for row in cur_m.fetchall()]
            conn_m.close()

          st.markdown("##### Current Members")
          for m_row in current_members:
            m_uname = m_row["username"]
            m_role = m_row["role"]
            col_mu, col_mr, col_maction = st.columns([2, 1, 2])
            with col_mu:
              st.markdown(f"**@{m_uname}** ({m_role})")
            with col_mr:
              pass
            with col_maction:
              if m_uname != username:  # Cannot modify self here
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                  if m_role == "Member":
                    if st.button("Make Admin", key=f"make_admin_{m_uname}"):
                      conn_up = get_db_connection()
                      if conn_up:
                        conn_up.execute(
                            "UPDATE group_members SET role = 'Admin' WHERE"
                            " group_name = ? AND username = ?",
                            (active_group, m_uname),
                        )
                        conn_up.commit()
                        conn_up.close()
                      st.success(f"@{m_uname} is now an Admin!")
                      st.rerun()
                  else:
                    if st.button("Demote", key=f"demote_{m_uname}"):
                      conn_up = get_db_connection()
                      if conn_up:
                        conn_up.execute(
                            "UPDATE group_members SET role = 'Member' WHERE"
                            " group_name = ? AND username = ?",
                            (active_group, m_uname),
                        )
                        conn_up.commit()
                        conn_up.close()
                      st.success(f"@{m_uname} demoted to Member.")
                      st.rerun()
                with c_btn2:
                  if st.button("Remove", key=f"remove_member_{m_uname}"):
                    conn_rm = get_db_connection()
                    if conn_rm:
                      conn_rm.execute(
                          "DELETE FROM group_members WHERE group_name = ? AND"
                          " username = ?",
                          (active_group, m_uname),
                      )
                      conn_rm.commit()
                      conn_rm.close()
                    st.success(f"Removed @{m_uname} from group.")
                    st.rerun()

          st.markdown("##### Add New User to Group")
          with st.form("add_member_form"):
            user_to_add = st.selectbox(
                "Select User",
                options=all_system_users,
                placeholder="Choose user...",
            )
            if st.form_submit_button(
                "Add Member to Group", use_container_width=True
            ):
              if user_to_add:
                conn_add = get_db_connection()
                if conn_add:
                  conn_add.execute(
                      """
                                    INSERT OR IGNORE INTO group_members (group_name, username, role)
                                    VALUES (?, ?, 'Member')
                                """,
                      (active_group, user_to_add),
                  )
                  conn_add.commit()
                  conn_add.close()
                st.success(f"Added @{user_to_add} to group successfully!")
                st.rerun()

      st.markdown(
          f"<hr style='border: 0.5px solid {border_color}; margin: 10px 0;'>",
          unsafe_allow_html=True,
      )

      # Optimized group chat loading block without recursive/nested fragmented loops
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

      # PERF FIX: previously get_user_avatar_html() ran its own DB query for
      # every single group message bubble on every rerun. Now we fetch the
      # profile pics for all distinct senders in this group's history in ONE
      # query and reuse that small dict for the whole render.
      distinct_senders = list({dict(gm)["sender"] for gm in group_msgs})
      group_avatar_cache = {}
      if distinct_senders:
        conn_av = get_db_connection()
        if conn_av:
          cur_av = conn_av.cursor()
          placeholders = ",".join("?" * len(distinct_senders))
          cur_av.execute(
              f"SELECT username, profile_pic FROM users WHERE username IN ({placeholders})",
              distinct_senders,
          )
          for row in cur_av.fetchall():
            group_avatar_cache[row["username"]] = row["profile_pic"] or ""
          conn_av.close()

      group_container = st.container(height=420)
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
          avatar_html = get_user_avatar_html(gm["sender"], group_avatar_cache)

          st.markdown(
              f"""
                    <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                        <div style="background-color: {bg}; color: #fff; padding: 10px 14px; border-radius: 10px; max-width: 70%; word-break: break-word;">
                            <div style="margin-bottom: 4px; display: flex; align-items: center;">
                                {avatar_html}
                                <small style="color: #00E676; font-size: 11px; font-weight: bold;">@{gm['sender']} • {gm.get('timestamp','')}</small>
                            </div>
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
        <div style="background-color: {card_bg}; padding: 25px; border-radius: 15px; border: 1px solid {border_color};">
            <h2 style="margin: 0;">{user.get('full_name') or username} <span style="font-size: 15px; color: #888;">(@{username})</span></h2>
            <p style="color: #00C853; font-weight: 600; margin: 4px 0; font-size: 14px;">
                🆔 User ID: {user.get('user_id', 'N/A')} &nbsp;|&nbsp; 
                🔒 Account: {user.get('account_type', 'Public')} &nbsp;|&nbsp; 
                👥 Followers: {followers_num} &nbsp;|&nbsp; Following: {following_num}
            </p>
            <p style="margin: 8px 0 0 0; font-size: 15px;">{user.get('bio') or 'No bio added yet.'}</p>
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

if show_main_nav:
  st.markdown(
      "<p style='text-align: center; color: #555; font-size: 0.7rem;"
      " letter-spacing: 2px; margin-top: 5rem;'>POWERED BY SARAAH ROBOTICS</p>",
      unsafe_allow_html=True,
  )
