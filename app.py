"""
================================================================================
                        NOOB LEARNING - ENTERPRISE PLATFORM
================================================================================
Module Name: app.py
Description: Full-stack Streamlit social learning & community application.
Includes: Authentication, Feed Engine, Advanced Direct & Group Messaging,
          Interactive Profiles, Custom Styling Engine, System Diagnostics,
          Database Auto-migrations, and AI Support Assistant integration.
================================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import mysql.connector
import datetime
import base64
import zoneinfo
import logging
import sys
import re
import os
import json
import time
import hashlib
from typing import Dict, List, Tuple, Optional, Any, Union
import streamlit.components.v1 as components

# --- LIVE TOP HEADER CLOCK ---
components.html(
    """
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 600; color: #31333F; background-color: #F0F2F6; padding: 6px 12px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
    <span>🕒</span>
    <span id="live-clock">Loading...</span> 
    <span style="color: #ccc;">|</span> 
    <span id="live-date"></span>
</div>

<script>
function updateTopClock() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    
    const timeStr = `${String(hours).padStart(2, '0')}:${minutes}:${seconds} ${ampm}`;
    const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    
    document.getElementById('live-clock').innerText = timeStr;
    document.getElementById('live-date').innerText = dateStr;
}
setInterval(updateTopClock, 1000);
updateTopClock();
</script>
""",
    height=40,
)
# ==============================================================================
# 0. LOGGING AND SYSTEM DIAGNOSTICS SETUP
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NoobLearning")
logger.info("Initializing NOOB LEARNING Platform Engine...")


# ==============================================================================
# 1. PAGE CONFIGURATION & SYSTEM THEMING
# ==============================================================================

st.set_page_config(
    page_title="NOOB LEARNING",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)


def inject_custom_css():
    """ Inject enterprise UI CSS styles for polish and layout consistency """
    custom_css = """
    <style>
        /* Main Container Styling */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        
        /* Custom Card Styles */
        .st-emotion-cache-1r6slb0, .stCard {
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }

        /* Avatar Hover Effects */
        .user-avatar-img {
            transition: transform 0.2s ease-in-out;
            cursor: pointer;
        }
        .user-avatar-img:hover {
            transform: scale(1.08);
        }

        /* Clean Streamlit Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-top: 8px;
            padding-bottom: 8px;
            border-radius: 6px 6px 0px 0px;
        }

        /* Status Badge CSS */
        .status-badge-online {
            background-color: #28a745;
            color: white;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: bold;
        }
        .status-badge-offline {
            background-color: #6c757d;
            color: white;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: bold;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


inject_custom_css()


# ==============================================================================
# 2. DATABASE CONFIGURATION & CONNECTION MANAGEMENT
# ==============================================================================

DB_CONFIG = {
    "host": "mysql-22faa093-padmanabhsingh11107035-84a9.l.aivencloud.com",
    "port": 21354,
    "user": "avnadmin",
    "password": "AVNS_iN1XY9WAsRFlUWVhM6k",
    "database": "defaultdb",
    "connect_timeout": 10
}


def get_db_connection():
    """ Establish and return a robust connection to the Cloud MySQL Database """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except mysql.connector.Error as err:
        logger.error(f"Database Connection Error: {err}")
        st.error(f"Database Connection Failure: {err}")
        return None
    return None


def verify_db_health() -> bool:
    """ Performs a quick health check ping to verify database responsiveness """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            return result is not None and result[0] == 1
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
        finally:
            conn.close()
    return False


def setup_database():
    """
    Initializes core database schema, creates chat group tables, and safely
    applies structural migrations for legacy database instances.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    bio VARCHAR(255) DEFAULT 'Welcome to NOOB LEARNING!',
                    profile_pic LONGTEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Posts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    caption TEXT,
                    media_url LONGTEXT,
                    likes INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            # Direct Messages Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT,
                    receiver_id INT,
                    message_text TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            # Follows Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    follow_id INT AUTO_INCREMENT PRIMARY KEY,
                    follower_id INT NOT NULL,
                    following_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_follow (follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (following_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            # Chat Groups Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_groups (
                    group_id INT AUTO_INCREMENT PRIMARY KEY,
                    group_name VARCHAR(100) NOT NULL,
                    created_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            # Group Messages Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_messages (
                    g_message_id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    sender_id INT NOT NULL,
                    message_text TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES chat_groups(group_id) ON DELETE CASCADE,
                    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            conn.commit()

            # Execute non-destructive schema migrations for legacy updates
            alterations = [
                "ALTER TABLE users ADD COLUMN bio VARCHAR(255) DEFAULT 'Welcome to NOOB LEARNING!'",
                "ALTER TABLE users ADD COLUMN profile_pic LONGTEXT",
                "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE posts ADD COLUMN likes INT DEFAULT 0",
                "ALTER TABLE posts MODIFY COLUMN media_url LONGTEXT"
            ]
            
            for alter_query in alterations:
                try:
                    cursor.execute(alter_query)
                    conn.commit()
                except mysql.connector.Error:
                    pass  # Column already exists, safe to ignore

            logger.info("Database schema setup and migration complete.")

        except Exception as e:
            logger.error(f"Database Initialization Error: {e}")
            st.error(f"Setup Error: {e}")
        finally:
            conn.close()


# Run DB Migration Routine
setup_database()


# ==============================================================================
# 3. SESSION STATE INITIALIZATION & MANAGEMENT
# ==============================================================================

def initialize_session_state():
    """ Ensures all critical session keys exist on cold start """
    if "user" not in st.session_state:
        st.session_state.user = None
    if "view_user_id" not in st.session_state:
        st.session_state.view_user_id = None
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Feed"
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    if "app_version" not in st.session_state:
        st.session_state.app_version = "v2.5.0-enterprise"


initialize_session_state()


# ==============================================================================
# 4. UTILITY HELPER FUNCTIONS
# ==============================================================================

def get_user_pic(u_dict: Optional[Dict[str, Any]]) -> str:
    """ Resolves a user profile picture URL or returns standard avatar fallback """
    if u_dict and isinstance(u_dict, dict) and u_dict.get("profile_pic"):
        return u_dict["profile_pic"]
    return "https://via.placeholder.com/150/1f2937/ffffff?text=User"


def get_user_bio(u_dict: Optional[Dict[str, Any]]) -> str:
    """ Resolves bio string with fallback """
    if u_dict and isinstance(u_dict, dict) and u_dict.get("bio"):
        return u_dict["bio"]
    return "Welcome to NOOB LEARNING!"


def convert_file_to_base64(uploaded_file) -> str:
    """ Converts Streamlit uploaded file into Base64 URI string for display """
    bytes_data = uploaded_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode()
    mime_type = uploaded_file.type
    return f"data:{mime_type};base64,{base64_str}"


def render_html_image(img_url: str, width: int = 40, height: int = 40, circle: bool = True):
    """ Custom HTML Image renderer with inline border-radius formatting """
    style = f"width:{width}px; height:{height}px; object-fit:cover;"
    if circle:
        style += " border-radius:50%;"
    else:
        style += " border-radius:8px;"
    st.markdown(f'<img src="{img_url}" class="user-avatar-img" style="{style}">', unsafe_allow_html=True)


def format_to_ist(dt_object: Any) -> str:
    """ Converts stored UTC / Database timestamps accurately to 12-hour IST time """
    if not dt_object:
        return ""
    if isinstance(dt_object, datetime.datetime):
        if dt_object.tzinfo is None:
            dt_utc = dt_object.replace(tzinfo=datetime.timezone.utc)
            dt_ist = dt_utc.astimezone(zoneinfo.ZoneInfo("Asia/Kolkata"))
        else:
            dt_ist = dt_object.astimezone(zoneinfo.ZoneInfo("Asia/Kolkata"))
        return dt_ist.strftime("%Y-%m-%d %I:%M:%S %p")
    return str(dt_object)


def sanitize_input(text_str: str) -> str:
    """ Basic security sanitizer to prevent script tag injection """
    if not text_str:
        return ""
    clean = re.sub(r'<script.*?>.*?</script>', '', text_str, flags=re.DOTALL | re.IGNORECASE)
    return clean.strip()


def hash_password(plain_text_password: str) -> str:
    """ Utility function for future SHA-256 password hashing strategy """
    return hashlib.sha256(plain_text_password.encode('utf-8')).hexdigest()


# ==============================================================================
# 5. DATABASE ACCESS LAYER (CRUD OPERATIONS)
# ==============================================================================

def delete_post_by_id(post_id: int):
    """ Deletes a targeted post from the database safely """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts WHERE post_id = %s", (post_id,))
            conn.commit()
            st.toast("Post deleted successfully!", icon="🗑️")
        except Exception as e:
            st.error(f"Failed to delete post: {e}")
        finally:
            conn.close()


def update_post_caption(post_id: int, new_caption: str):
    """ Updates caption text on an existing post """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE posts SET caption = %s WHERE post_id = %s", (sanitize_input(new_caption), post_id))
            conn.commit()
            st.toast("Post updated!", icon="✏️")
        except Exception as e:
            st.error(f"Failed to update post: {e}")
        finally:
            conn.close()


def get_follower_count(user_id: int) -> int:
    """ Returns total count of users following target user_id """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id = %s", (user_id,))
            res = cursor.fetchone()
            return res[0] if res else 0
        except Exception:
            return 0
        finally:
            conn.close()
    return 0


def get_following_count(user_id: int) -> int:
    """ Returns total count of users target user_id is following """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (user_id,))
            res = cursor.fetchone()
            return res[0] if res else 0
        except Exception:
            return 0
        finally:
            conn.close()
    return 0


def is_following(follower_id: int, following_id: int) -> bool:
    """ Returns True if follower_id currently follows following_id """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT follow_id FROM follows WHERE follower_id = %s AND following_id = %s",
                (follower_id, following_id)
            )
            return cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            conn.close()
    return False


def toggle_follow(follower_id: int, following_id: int):
    """ Toggles follow state between two users """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if is_following(follower_id, following_id):
                cursor.execute(
                    "DELETE FROM follows WHERE follower_id = %s AND following_id = %s",
                    (follower_id, following_id)
                )
                st.toast("Unfollowed user!", icon="👤")
            else:
                cursor.execute(
                    "INSERT INTO follows (follower_id, following_id) VALUES (%s, %s)",
                    (follower_id, following_id)
                )
                st.toast("Follow request sent!", icon="➕")
            conn.commit()
        except Exception as e:
            st.error(f"Follow action failed: {e}")
        finally:
            conn.close()


def fetch_all_users_count() -> int:
    """ Computes total registered users count """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            res = cursor.fetchone()
            return res[0] if res else 0
        finally:
            conn.close()
    return 0


def fetch_all_posts_count() -> int:
    """ Computes total published posts count """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts")
            res = cursor.fetchone()
            return res[0] if res else 0
        finally:
            conn.close()
    return 0


# ==============================================================================
# 6. ENHANCED MESSAGING MODULE (DEFINED BEFORE TAB CALLS)
# ==============================================================================

def render_enhanced_direct_messages(user: Dict[str, Any]):
    """
    Renders upgraded private & group messaging system inside Tab 5.
    Defined near the top to prevent NameError execution issues.
    """
    st.subheader("💬 Messaging Center")

    chat_type = st.radio(
        "Select Chat Mode:",
        ["🔒 Private Direct Chat", "👥 Group Chat"],
        horizontal=True,
        key="messaging_center_mode_radio"
    )

    # ------------------ 1. PRIVATE DIRECT CHAT ------------------
    if chat_type == "🔒 Private Direct Chat":
        st.write("### Private Direct Chat")
        target_id = st.number_input(
            "Enter User ID to chat with:",
            min_value=1,
            step=1,
            key="enhanced_dm_target_id_input"
        )

        if target_id:
            if target_id == user['user_id']:
                st.info("💡 You are viewing your personal notes space.")

            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT username FROM users WHERE user_id = %s", (target_id,))
                    target_user = cursor.fetchone()

                    if not target_user:
                        st.warning(f"No registered user found with User ID: `{target_id}`")
                    else:
                        st.info(f"Chatting with **@{target_user['username']}** (User ID: `{target_id}`)")

                        cursor.execute("""
                            SELECT m.sender_id, m.message_text, m.sent_at, u.username 
                            FROM messages m
                            JOIN users u ON m.sender_id = u.user_id
                            WHERE (m.sender_id = %s AND m.receiver_id = %s) 
                               OR (m.sender_id = %s AND m.receiver_id = %s)
                            ORDER BY m.sent_at ASC
                        """, (user['user_id'], target_id, target_id, user['user_id']))
                        messages = cursor.fetchall()

                        st.divider()
                        if not messages:
                            st.caption("No chat history yet. Send a friendly greeting below!")
                        else:
                            for m in messages:
                                is_me = (m['sender_id'] == user['user_id'])
                                align = "user" if is_me else "assistant"
                                formatted_time = format_to_ist(m['sent_at'])

                                with st.chat_message(align):
                                    st.markdown(f"**@{m['username']}** `(ID: {m['sender_id']})` • *{formatted_time}*")
                                    st.write(m['message_text'])

                        st.divider()
                        with st.form(key=f"dm_enhanced_form_{target_id}", clear_on_submit=True):
                            dm_input = st.text_input("Type your private message...")
                            submit_dm = st.form_submit_button("Send Private Message", use_container_width=True)

                            if submit_dm and dm_input.strip():
                                clean_msg = sanitize_input(dm_input)
                                c_send = conn.cursor()
                                now_ist = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                                c_send.execute(
                                    "INSERT INTO messages (sender_id, receiver_id, message_text, sent_at) VALUES (%s, %s, %s, %s)",
                                    (user['user_id'], target_id, clean_msg, now_ist)
                                )
                                conn.commit()
                                st.toast("Message sent!", icon="📨")
                                st.rerun()
                except Exception as e:
                    st.error(f"Chat Load Error: {e}")
                finally:
                    conn.close()

    # ------------------ 2. GROUP CHAT ------------------
    else:
        st.write("### Community Group Chat")

        with st.expander("➕ Create New Chat Group"):
            new_g_name = st.text_input("Enter Group Name:", key="new_group_name_input_field")
            if st.button("Create Group Now", use_container_width=True):
                if new_g_name.strip():
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO chat_groups (group_name, created_by) VALUES (%s, %s)",
                                (sanitize_input(new_g_name.strip()), user['user_id'])
                            )
                            conn.commit()
                            st.success(f"Group '{new_g_name}' successfully created!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to create group: {e}")
                        finally:
                            conn.close()
                else:
                    st.warning("Please enter a valid group name.")

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM chat_groups ORDER BY group_id DESC")
                groups = cursor.fetchall()

                if not groups:
                    st.info("No community groups created yet. Create the first one above!")
                else:
                    group_options = {f"#{g['group_id']} - {g['group_name']}": g['group_id'] for g in groups}
                    selected_group_str = st.selectbox("Select Chat Room:", list(group_options.keys()))
                    selected_group_id = group_options[selected_group_str]

                    st.divider()

                    cursor.execute("""
                        SELECT gm.sender_id, gm.message_text, gm.sent_at, u.username
                        FROM group_messages gm
                        JOIN users u ON gm.sender_id = u.user_id
                        WHERE gm.group_id = %s
                        ORDER BY gm.sent_at ASC
                    """, (selected_group_id,))
                    g_messages = cursor.fetchall()

                    if not g_messages:
                        st.caption("No messages in this group yet. Start the conversation!")
                    else:
                        for gm in g_messages:
                            is_me = (gm['sender_id'] == user['user_id'])
                            align = "user" if is_me else "assistant"
                            formatted_time = format_to_ist(gm['sent_at'])

                            with st.chat_message(align):
                                st.markdown(f"**@{gm['username']}** `(ID: {gm['sender_id']})` • *{formatted_time}*")
                                st.write(gm['message_text'])

                    st.divider()
                    with st.form(key=f"group_enhanced_form_{selected_group_id}", clear_on_submit=True):
                        g_msg_input = st.text_input("Type message to group...")
                        submit_g_msg = st.form_submit_button("Send to Group", use_container_width=True)

                        if submit_g_msg and g_msg_input.strip():
                            clean_g_msg = sanitize_input(g_msg_input)
                            c_g_send = conn.cursor()
                            now_ist = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                            c_g_send.execute(
                                "INSERT INTO group_messages (group_id, sender_id, message_text, sent_at) VALUES (%s, %s, %s, %s)",
                                (selected_group_id, user['user_id'], clean_g_msg, now_ist)
                            )
                            conn.commit()
                            st.toast("Group message sent!", icon="👥")
                            st.rerun()
            except Exception as e:
                st.error(f"Group Chat Error: {e}")
            finally:
                conn.close()


# ==============================================================================
# 7. INTERACTIVE DIALOG MODALS
# ==============================================================================

@st.dialog("📷 Update Profile Picture")
def update_profile_pic_dialog():
    """ Dialog popover to update user avatar via Upload, Camera, or URL """
    st.write("Upload or capture a picture to customize your profile image.")
    photo_source = st.radio(
        "Source Selection:",
        ["📁 Upload Image File", "📷 Camera Capture", "🔗 External Image URL"],
        horizontal=True
    )
    new_pic = None

    if photo_source == "📁 Upload Image File":
        file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg", "webp"])
        if file:
            new_pic = convert_file_to_base64(file)
    elif photo_source == "📷 Camera Capture":
        cam_file = st.camera_input("Take a snapshot")
        if cam_file:
            new_pic = convert_file_to_base64(cam_file)
    elif photo_source == "🔗 External Image URL":
        url = st.text_input("Paste direct image URL:")
        if url.strip():
            new_pic = url.strip()

    if st.button("Save Profile Picture", use_container_width=True):
        if new_pic:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET profile_pic = %s WHERE user_id = %s",
                        (new_pic, st.session_state.user['user_id'])
                    )
                    conn.commit()
                    st.session_state.user['profile_pic'] = new_pic
                    st.success("Profile picture updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update profile picture: {e}")
                finally:
                    conn.close()
        else:
            st.warning("Please provide an image before saving.")


@st.dialog("⚙️ Platform Analytics & System Health")
def show_platform_analytics():
    """ Displays system health diagnostics and platform statistics """
    st.write("### 📊 System Overview")
    db_status = "🟢 Connected" if verify_db_health() else "🔴 Disconnected"
    st.write(f"**Database Host:** `{DB_CONFIG['host']}`")
    st.write(f"**Database Status:** {db_status}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Users", fetch_all_users_count())
    with col2:
        st.metric("Total Posts", fetch_all_posts_count())


# ==============================================================================
# 8. AUTHENTICATION MODULE (LOGIN / SIGNUP)
# ==============================================================================

if not st.session_state.user:
    st.title("🎓 NOOB LEARNING")
    st.write("Join the interactive learning community. Sign in or register below.")

    tab_login, tab_signup = st.tabs(["🔒 Log In", "📝 Sign Up"])

    # ------------------ LOG IN ------------------
    with tab_login:
        st.subheader("Account Login")
        username = st.text_input("Username", key="login_user_input")
        password = st.text_input("Password", type="password", key="login_pass_input")

        if st.button("Log In to Account", use_container_width=True):
            if username and password:
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute(
                            "SELECT * FROM users WHERE username = %s AND password = %s",
                            (username.strip(), password)
                        )
                        account = cursor.fetchone()
                        if account:
                            st.session_state.user = account
                            st.toast(f"Welcome back @{account['username']}!", icon="👋")
                            st.success("Log in successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password credentials.")
                    except Exception as e:
                        st.error(f"Login Failure: {e}")
                    finally:
                        conn.close()
            else:
                st.warning("Please enter both username and password.")

    # ------------------ SIGN UP ------------------
    with tab_signup:
        st.subheader("Create New Account")
        new_user = st.text_input("Choose Username", key="reg_user_input")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass_input")
        confirm_pass = st.text_input("Confirm Password", type="password", key="reg_pass_confirm")

        if st.button("Create Account Now", use_container_width=True):
            if new_user and new_pass:
                if new_pass != confirm_pass:
                    st.error("Passwords do not match!")
                else:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO users (username, password) VALUES (%s, %s)",
                                (sanitize_input(new_user.strip()), new_pass)
                            )
                            conn.commit()
                            st.success("Account successfully created! Please log in above.")
                        except mysql.connector.IntegrityError:
                            st.error("Username is already taken. Choose another.")
                        except Exception as e:
                            st.error(f"Sign up failed: {e}")
                        finally:
                            conn.close()
            else:
                st.warning("Please complete all required fields.")


# ==============================================================================
# 9. MAIN APPLICATION INTERFACE (AUTHENTICATED)
# ==============================================================================

else:
    user = st.session_state.user
    my_followers_count = get_follower_count(user['user_id'])
    my_following_count = get_following_count(user['user_id'])

    # ------------------ TOP APPLICATION HEADER ------------------
    header_col1, header_col2, header_col3 = st.columns([1, 3, 2])

    with header_col1:
        user_avatar = get_user_pic(user)
        render_html_image(user_avatar, width=48, height=48, circle=True)
        if st.button("📷 Edit", key="top_profile_icon_btn", help="Update Profile Photo"):
            update_profile_pic_dialog()

    with header_col2:
        st.markdown("### **NOOB LEARNING**")
        st.caption(
            f"Logged in as **@{user['username']}** | "
            f"👥 Followers: **{my_followers_count}** | Following: **{my_following_count}**"
        )

    with header_col3:
        ist_now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata"))
        st.markdown(f"🕒 **{ist_now.strftime('%I:%M %p')}** | `{ist_now.strftime('%d %b %Y')}`")
        
        btn_logout, btn_stats = st.columns(2)
        with btn_logout:
            if st.button("Logout", key="app_logout_btn"):
                st.session_state.user = None
                st.session_state.view_user_id = None
                st.rerun()
        with btn_stats:
            if st.button("📊 Stats", key="app_stats_btn"):
                show_platform_analytics()

    st.divider()

    # ------------------ MAIN TABS NAVIGATION ------------------
    (
    app_tab_feed,
    app_tab_search,
    app_tab_friends,
    app_tab_create,
    app_tab_reels,
    app_tab_msg,
    app_tab_profile,
    app_tab_chatway,
) = st.tabs([
    "🏠 Feed",
    "🔍 Search",
    "👥 Add Friends",
    "➕ Create",
    "🎬 Reels",
    "💬 Direct",
    "👤 Profile",
    "🤖 AI Support"
])

    # ==========================================================================
    # TAB 1: MAIN FEED
    # ==========================================================================
    with app_tab_feed:
        st.subheader("🏠 Community Feed")
        conn = get_db_connection()
        feed_posts = []

        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT posts.post_id, posts.user_id, posts.caption, posts.media_url, posts.likes, posts.created_at, 
                           users.username, users.profile_pic
                    FROM posts 
                    JOIN users ON posts.user_id = users.user_id 
                    ORDER BY posts.created_at DESC
                """)
                feed_posts = cursor.fetchall()
            except Exception as e:
                st.error(f"Feed error: {e}")
            finally:
                conn.close()

        if not feed_posts:
            st.info("No posts in the feed yet! Be the first to share in the '➕ Create' tab.")
        else:
            for post in feed_posts:
                post_f_count = get_follower_count(post['user_id'])
                with st.container(border=True):
                    h_col1, h_col2, h_col3 = st.columns([1, 4, 2])
                    with h_col1:
                        render_html_image(get_user_pic(post), width=40, height=40, circle=True)
                    with h_col2:
                        st.markdown(f"**@{post['username']}** `Followers: {post_f_count}`")
                        st.caption(format_to_ist(post['created_at']))
                    with h_col3:
                        if st.button("👤 Profile", key=f"feed_view_{post['post_id']}"):
                            st.session_state.view_user_id = post['user_id']
                            st.rerun()

                    if post['media_url']:
                        render_html_image(post['media_url'], width=380, height=380, circle=False)

                    st.write(f"{post['caption']}")

                    # Action Row
                    act_col1, act_col2, act_col3 = st.columns([1, 4, 1])
                    with act_col1:
                        if st.button("❤️", key=f"like_{post['post_id']}"):
                            conn_like = get_db_connection()
                            if conn_like:
                                c_like = conn_like.cursor()
                                c_like.execute(
                                    "UPDATE posts SET likes = likes + 1 WHERE post_id = %s",
                                    (post['post_id'],)
                                )
                                conn_like.commit()
                                conn_like.close()
                                st.rerun()

                    with act_col2:
                        st.write(f"**{post['likes']} likes**")

                    with act_col3:
                        with st.popover("⋮", help="Post Options"):
                            st.write("**Post Options**")

                            # SHARE OPTION
                            if st.button("🔗 Share Details", key=f"feed_share_{post['post_id']}", use_container_width=True):
                                st.code(f"Post ID: {post['post_id']} by @{post['username']}\nCaption: {post['caption']}")
                                st.toast("Post details copied above!", icon="🔗")

                            # EDIT & DELETE OPTIONS
                            if post['user_id'] == user['user_id']:
                                st.divider()
                                with st.expander("✏️ Edit Caption"):
                                    edited_cap = st.text_area(
                                        "New Caption",
                                        value=post['caption'],
                                        key=f"feed_edit_txt_{post['post_id']}"
                                    )
                                    if st.button("Save Changes", key=f"feed_save_edit_{post['post_id']}", use_container_width=True):
                                        update_post_caption(post['post_id'], edited_cap)
                                        st.rerun()

                                if st.button("🗑️ Delete Post", key=f"feed_del_{post['post_id']}", type="primary", use_container_width=True):
                                    delete_post_by_id(post['post_id'])
                                    st.rerun()

    # ==========================================================================
    # TAB 2: SEARCH ACCOUNTS
    # ==========================================================================
    with app_tab_search:
        st.subheader("🔍 Search Accounts")
        search_query = st.text_input("Search by username or User ID...", key="search_bar")

        conn = get_db_connection()
        found_users = []
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                if search_query.strip():
                    cursor.execute(
                        "SELECT user_id, username, profile_pic, bio FROM users WHERE username LIKE %s OR user_id LIKE %s",
                        (f"%{search_query.strip()}%", f"%{search_query.strip()}%")
                    )
                else:
                    cursor.execute("SELECT user_id, username, profile_pic, bio FROM users ORDER BY user_id DESC LIMIT 10")
                found_users = cursor.fetchall()
            except Exception as e:
                st.error(f"Search error: {e}")
            finally:
                conn.close()

        if not found_users:
            st.info("No matching accounts found.")
        else:
            for u in found_users:
                f_count = get_follower_count(u['user_id'])
                with st.container(border=True):
                    sc1, sc2, sc3 = st.columns([1, 4, 2])
                    with sc1:
                        render_html_image(get_user_pic(u), width=40, height=40, circle=True)
                    with sc2:
                        st.write(f"**@{u['username']}** | ID: `{u['user_id']}` | 👥 **Followers: {f_count}**")
                        st.caption(get_user_bio(u))
                    with sc3:
                        if u['user_id'] != user['user_id']:
                            already_following = is_following(user['user_id'], u['user_id'])
                            btn_label = "✔ Following" if already_following else "➕ Follow Request"
                            if st.button(btn_label, key=f"search_follow_{u['user_id']}", use_container_width=True):
                                toggle_follow(user['user_id'], u['user_id'])
                                st.rerun()
                        if st.button("View Profile", key=f"search_u_{u['user_id']}", use_container_width=True):
                            st.session_state.view_user_id = u['user_id']
                            st.rerun()

    # ==========================================================================
    # TAB 3: ADD FRIENDS
    # ==========================================================================
    with app_tab_friends:
        st.subheader("👥 Add Friends & Community Directory")
        st.write("Browse all registered accounts, view User IDs, and connect with members.")

        conn = get_db_connection()
        all_users = []
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT user_id, username, profile_pic, bio FROM users ORDER BY user_id ASC")
                all_users = cursor.fetchall()
            except Exception as e:
                st.error(f"Error fetching directory: {e}")
            finally:
                conn.close()

        if not all_users:
            st.info("No registered users found.")
        else:
            for u in all_users:
                f_count = get_follower_count(u['user_id'])
                with st.container(border=True):
                    fc1, fc2, fc3 = st.columns([1, 4, 3])
                    with fc1:
                        render_html_image(get_user_pic(u), width=45, height=45, circle=True)
                    with fc2:
                        st.write(f"**@{u['username']}** (User ID: `{u['user_id']}`)")
                        st.caption(f"👥 **Followers:** {f_count} | Bio: {get_user_bio(u)}")
                    with fc3:
                        if u['user_id'] == user['user_id']:
                            st.info(" You")
                        else:
                            following_status = is_following(user['user_id'], u['user_id'])
                            follow_btn_txt = "✔ Following" if following_status else "➕ Send Follow Request"
                            if st.button(follow_btn_txt, key=f"friend_follow_{u['user_id']}", use_container_width=True):
                                toggle_follow(user['user_id'], u['user_id'])
                                st.rerun()

    # ==========================================================================
    # TAB 4: CREATE POST
    # ==========================================================================
    with app_tab_create:
        st.subheader("📸 Create New Post / Reel")

        media_input = None
        media_source = st.radio(
            "Media Source:",
            ["📁 Image File", "📷 Take Photo", "🔗 Direct URL"],
            horizontal=True
        )

        if media_source == "📁 Image File":
            up_f = st.file_uploader("Upload media...", type=["png", "jpg", "jpeg", "webp"])
            if up_f:
                media_input = convert_file_to_base64(up_f)
        elif media_source == "📷 Take Photo":
            cam_f = st.camera_input("Snap picture")
            if cam_f:
                media_input = convert_file_to_base64(cam_f)
        elif media_source == "🔗 Direct URL":
            url_f = st.text_input("Direct URL link:")
            if url_f.strip():
                media_input = url_f.strip()

        caption_input = st.text_area("Write a caption...", height=120)

        if st.button("Publish Post Now", use_container_width=True):
            if caption_input.strip():
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        now_ist = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(
                            "INSERT INTO posts (user_id, caption, media_url, created_at) VALUES (%s, %s, %s, %s)",
                            (user['user_id'], sanitize_input(caption_input), media_input, now_ist)
                        )
                        conn.commit()
                        st.success("Published successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to publish: {e}")
                    finally:
                        conn.close()
            else:
                st.warning("Please enter a caption before sharing.")

    # ==========================================================================
    # TAB 5: DIRECT & GROUP MESSAGING CENTER
    # ==========================================================================
    with app_tab_msg:
        # Invokes the cleanly defined function near the top of the file
        render_enhanced_direct_messages(user)

    # ==========================================================================
    # TAB 6: PROFILE & SETTINGS
    # ==========================================================================
    with app_tab_profile:
        active_profile_id = st.session_state.view_user_id or user['user_id']

        conn = get_db_connection()
        p_user = None
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (active_profile_id,))
                p_user = cursor.fetchone()
            finally:
                conn.close()

        if not p_user:
            p_user = user

        if st.session_state.view_user_id and st.session_state.view_user_id != user['user_id']:
            if st.button("⬅️ Back to My Profile"):
                st.session_state.view_user_id = None
                st.rerun()

        prof_f_count = get_follower_count(p_user['user_id'])
        st.subheader(f"Profile: @{p_user['username']}")

        user_posts_count = 0
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM posts WHERE user_id = %s", (p_user['user_id'],))
                user_posts_count = cursor.fetchone()[0]
            except Exception:
                user_posts_count = 0
            finally:
                conn.close()

        p_col1, p_col2 = st.columns([1, 3])
        with p_col1:
            render_html_image(get_user_pic(p_user), width=85, height=85, circle=True)
        with p_col2:
            st.write(f"**User ID:** `{p_user['user_id']}`")
            st.write(f"👥 **Followers:** {prof_f_count}")
            st.write(f"🎬 **Posts:** {user_posts_count}")
            st.write(f"📝 **Bio:** {get_user_bio(p_user)}")

            if p_user['user_id'] != user['user_id']:
                following_p = is_following(user['user_id'], p_user['user_id'])
                p_btn_label = "✔ Following" if following_p else "➕ Send Follow Request"
                if st.button(p_btn_label, key="profile_follow_toggle_btn"):
                    toggle_follow(user['user_id'], p_user['user_id'])
                    st.rerun()

        # Edit Bio (Own profile only)
        if p_user['user_id'] == user['user_id']:
            with st.expander("⚙️ Edit Profile Bio"):
                new_bio = st.text_input("New Bio Text", value=get_user_bio(user))
                if st.button("Save Bio Changes", use_container_width=True):
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users SET bio = %s WHERE user_id = %s",
                                (sanitize_input(new_bio), user['user_id'])
                            )
                            conn.commit()
                            st.session_state.user['bio'] = new_bio
                            st.success("Bio updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update bio: {e}")
                        finally:
                            conn.close()

        st.divider()
        st.write("### 🎬 User Posts Grid")

        conn = get_db_connection()
        user_media = []
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT post_id, caption, media_url, likes, created_at FROM posts WHERE user_id = %s ORDER BY created_at DESC",
                    (p_user['user_id'],)
                )
                user_media = cursor.fetchall()
            except Exception:
                user_media = []
            finally:
                conn.close()

        if not user_media:
            st.info("No posts published yet.")
        else:
            for item in user_media:
                with st.container(border=True):
                    if item['media_url']:
                        render_html_image(item['media_url'], width=350, height=350, circle=False)

                    prof_act_1, prof_act_2 = st.columns([4, 1])
                    with prof_act_1:
                        st.write(f"❤️ **{item['likes']} likes**")
                    with prof_act_2:
                        with st.popover("⋮", help="Post Options"):
                            st.write("**Post Options**")

                            if st.button("🔗 Share Details", key=f"prof_share_{item['post_id']}", use_container_width=True):
                                st.code(f"Post ID: {item['post_id']}\nCaption: {item['caption']}")
                                st.toast("Copied post details!", icon="🔗")

                            if p_user['user_id'] == user['user_id']:
                                st.divider()
                                with st.expander("✏️ Edit Caption"):
                                    p_edited_cap = st.text_area(
                                        "New Caption",
                                        value=item['caption'],
                                        key=f"prof_edit_txt_{item['post_id']}"
                                    )
                                    if st.button("Save Changes", key=f"prof_save_edit_{item['post_id']}", use_container_width=True):
                                        update_post_caption(item['post_id'], p_edited_cap)
                                        st.rerun()

                                if st.button("🗑️ Delete Post", key=f"prof_del_{item['post_id']}", type="primary", use_container_width=True):
                                    delete_post_by_id(item['post_id'])
                                    st.rerun()

                    st.write(f"📝 {item['caption']}")
                    st.caption(format_to_ist(item['created_at']))

    # ==========================================================================
    # TAB 7: AI SUPPORT ASSISTANT (CHATWAY IFRAME)
    # ==========================================================================
    with app_tab_chatway:
        st.subheader("🤖 Saraah AI Support Assistant")
        st.write("Need help? Chat live with our embedded support assistant.")
        
        chatway_html_code = """
        <div style="width: 100%; height: 550px; border-radius: 12px; overflow: hidden; border: 1px solid #333;">
            <iframe 
                src="https://chatway.app/widget/UbvqSsHWYpja" 
                width="100%" 
                height="550" 
                style="border:none;"
                allow="microphone; camera">
            </iframe>
        </div>
        """
        components.html(chatway_html_code, height=570)


# ==============================================================================
# 10. SYSTEM UNIT TEST SUITE AND DIAGNOSTICS MODULE
# ==============================================================================

class SystemDiagnosticSuite:
    """ Comprehensive suite to test utility helpers and system integrity """

    @staticmethod
    def test_input_sanitizer():
        raw_text = "<script>alert('test')</script>Hello World"
        clean = sanitize_input(raw_text)
        assert "<script>" not in clean
        assert "Hello World" in clean
        return True

    @staticmethod
    def test_timestamp_formatter():
        now = datetime.datetime.now()
        formatted = format_to_ist(now)
        assert isinstance(formatted, str)
        return True

    @staticmethod
    def test_db_config_types():
        assert isinstance(DB_CONFIG["port"], int)
        assert isinstance(DB_CONFIG["host"], str)
        return True


def run_system_self_diagnostics():
    """ Executes system self checks on platform initialization """
    try:
        SystemDiagnosticSuite.test_input_sanitizer()
        SystemDiagnosticSuite.test_timestamp_formatter()
        SystemDiagnosticSuite.test_db_config_types()
        logger.info("System self-diagnostics passed successfully.")
    except Exception as e:
        logger.error(f"Diagnostics failure: {e}")


run_system_self_diagnostics()


import streamlit.components.v1 as components

# --- LIVE TICKING CLOCK WIDGET ---
live_clock_html = """
<div style="font-family: sans-serif; font-size: 16px; font-weight: bold; color: #31333F; background-color: #F0F2F6; padding: 8px 12px; border-radius: 8px; display: inline-block;">
    🕒 <span id="clock">Loading time...</span> | <span id="date"></span>
</div>

<script>
function updateClock() {
    const now = new Date();
    
    // Format Time (12-hour format with AM/PM)
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    const formattedHours = String(hours).padStart(2, '0');
    
    const timeString = `${formattedHours}:${minutes}:${seconds} ${ampm}`;
    
    // Format Date (DD MMM YYYY)
    const options = { day: '2-digit', month: 'short', year: 'numeric' };
    const dateString = now.toLocaleDateString('en-GB', options);
    
    document.getElementById('clock').innerText = timeString;
    document.getElementById('date').innerText = dateString;
}

setInterval(updateClock, 1000);
updateClock();
</script>
"""

# Render the component in your app layout
components.html(live_clock_html, height=45)

with app_tab_reels:

    st.markdown(
        '<p class="main-header">🎬 Community Reels</p>',
        unsafe_allow_html=True
    )

    st.write("Watch reels shared by the community or upload your own.")

    # ================= Upload Reel =================

    with st.expander("📤 Upload Reel"):

        with st.form("upload_reel", clear_on_submit=True):

            reel_caption = st.text_input("Caption")

            reel_url = st.text_input(
                "Video Link (YouTube / Shorts / MP4)"
            )

            submit_reel = st.form_submit_button("Upload Reel")

            if submit_reel:

                if reel_caption.strip() == "" or reel_url.strip() == "":
                    st.warning("Please fill all fields.")

                else:

                    try:

                        conn = get_db_connection()

                        cursor = conn.cursor()

                        username = st.session_state.user["username"]

                        from datetime import datetime

                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        cursor.execute("""
                        INSERT INTO reels
                        (username, caption, video_url, timestamp)
                        VALUES (%s,%s,%s,%s)
                        """,(
                            username,
                            reel_caption,
                            reel_url,
                            timestamp
                        ))

                        conn.commit()

                        cursor.close()

                        conn.close()

                        st.success("✅ Reel uploaded successfully!")

                        st.rerun()

                    except Exception as e:

                        st.error(e)

    st.divider()

    # ================= Show Reels =================

    try:

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT *
        FROM reels
        ORDER BY RAND()
        """)

        reels = cursor.fetchall()

        cursor.close()

        conn.close()

        if len(reels) == 0:

            st.info("🎬 No reels uploaded yet.")

        else:

            left, center, right = st.columns([1,2,1])

            with center:

                for reel in reels:

                    st.markdown(f"""
                    <div class="card">

                    <h4>👤 {reel['username']}</h4>

                    <p>{reel['caption']}</p>

                    </div>
                    """,
                    unsafe_allow_html=True)

                    st.video(reel["video_url"])

                    st.caption("Uploaded on : " + str(reel["timestamp"]))

                    st.divider()

    except Exception as e:

        st.error(e)
