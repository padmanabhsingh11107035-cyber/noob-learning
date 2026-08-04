import sys
import os
import time
import datetime
import zoneinfo
import base64
import hashlib
import re
import mysql.connector
from mysql.connector import errorcode
import streamlit as st

# ==============================================================================
# 1. PAGE CONFIGURATION & GLOBAL STYLES
# ==============================================================================
st.set_page_config(
    page_title="Noob Learning - Social & Learning Hub",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for polished visual appearance
st.markdown("""
<style>
    /* Main container tweaks */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    /* Card style containers */
    .stCard {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    /* Badge styling */
    .user-badge {
        background-color: #e1f5fe;
        color: #0288d1;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.85em;
    }
    /* Chat bubbles */
    .chat-bubble-me {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 10px 14px;
        border-radius: 15px 15px 0px 15px;
        margin-bottom: 8px;
        width: fit-content;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-bubble-other {
        background-color: #f8d7da;
        color: #842029;
        padding: 10px 14px;
        border-radius: 15px 15px 15px 0px;
        margin-bottom: 8px;
        width: fit-content;
        max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HELPER UTILITIES & DATETIME FORMATTERS
# ==============================================================================
def format_to_ist(dt_obj):
    """
    Safely converts UTC/Naive datetimes or strings into IST formatted output.
    """
    if not dt_obj:
        return "N/A"
    
    if isinstance(dt_obj, str):
        try:
            dt_obj = datetime.datetime.strptime(dt_obj, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                dt_obj = datetime.datetime.strptime(dt_obj, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                return dt_obj

    try:
        ist_tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)
        
        local_dt = dt_obj.astimezone(ist_tz)
        return local_dt.strftime("%I:%M %p | %d %b %Y")
    except Exception as e:
        return str(dt_obj)

def get_current_ist_timestamp():
    """Returns current date time string in IST timezone standard."""
    ist_tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    now_ist = datetime.datetime.now(ist_tz)
    return now_ist.strftime('%Y-%m-%d %H:%M:%S')

def file_to_base64(file_bytes):
    """Converts uploaded file binaries into base64 standard strings."""
    if not file_bytes:
        return ""
    return base64.b64encode(file_bytes).decode('utf-8')

def make_hashes(password):
    """Hashes passwords using standard SHA-256 algorithm."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Validates user password hash against database records."""
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def is_valid_url(url_string):
    """Validates standard web URLs using regex patterns."""
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url_string) is not None

# ==============================================================================
# 3. DATABASE MANAGEMENT & RELATIONAL SCHEMA
# ==============================================================================
def get_db_connection():
    """
    Connects to MySQL instance using Streamlit Secrets.
    """
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            port=st.secrets["mysql"].get("port", 3306)
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"❌ Database Connection Error: {err}")
        return None
    except Exception as e:
        st.error(f"❌ Configuration Error: Make sure .streamlit/secrets.toml is configured. ({e})")
        return None

def init_database_tables():
    """
    Initializes database schema and ensures required table foreign keys exist.
    """
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    tables = {}

    # Users Table
    tables['users'] = (
        "CREATE TABLE IF NOT EXISTS `users` ("
        "  `user_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `username` VARCHAR(50) NOT NULL UNIQUE,"
        "  `password_hash` VARCHAR(255) NOT NULL,"
        "  `bio` TEXT,"
        "  `avatar_url` TEXT,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    )

    # Posts Table
    tables['posts'] = (
        "CREATE TABLE IF NOT EXISTS `posts` ("
        "  `post_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `user_id` INT NOT NULL,"
        "  `media_url` LONGTEXT NOT NULL,"
        "  `media_type` VARCHAR(10) DEFAULT 'image',"
        "  `caption` TEXT,"
        "  `likes_count` INT DEFAULT 0,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    )

    # Comments Table
    tables['comments'] = (
        "CREATE TABLE IF NOT EXISTS `comments` ("
        "  `comment_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `post_id` INT NOT NULL,"
        "  `user_id` INT NOT NULL,"
        "  `comment_text` TEXT NOT NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`post_id`) REFERENCES `posts`(`post_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    )

    # Follows Network Table
    tables['follows'] = (
        "CREATE TABLE IF NOT EXISTS `follows` ("
        "  `follower_id` INT NOT NULL,"
        "  `followed_id` INT NOT NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  PRIMARY KEY (`follower_id`, `followed_id`),"
        "  FOREIGN KEY (`follower_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`followed_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    )

    # Direct Messages Table
    tables['messages'] = (
        "CREATE TABLE IF NOT EXISTS `messages` ("
        "  `message_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `sender_id` INT NOT NULL,"
        "  `receiver_id` INT NOT NULL,"
        "  `message_text` TEXT NOT NULL,"
        "  `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`sender_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`receiver_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    )

    # Chat Groups Table
    tables['chat_groups'] = (
        "CREATE TABLE IF NOT EXISTS `chat_groups` ("
        "  `group_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `group_name` VARCHAR(100) NOT NULL,"
        "  `description` TEXT,"
        "  `created_by` INT NOT NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`created_by`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    )

    # Group Messages Table
    tables['group_messages'] = (
        "CREATE TABLE IF NOT EXISTS `group_messages` ("
        "  `g_msg_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `group_id` INT NOT NULL,"
        "  `sender_id` INT NOT NULL,"
        "  `message_text` TEXT NOT NULL,"
        "  `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`group_id`) REFERENCES `chat_groups`(`group_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`sender_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
    )

    for table_name, table_sql in tables.items():
        try:
            cursor.execute(table_sql)
        except mysql.connector.Error as err:
            st.error(f"Error initializing table '{table_name}': {err}")

    conn.commit()
    cursor.close()
    conn.close()

# Execute schema setup on load
init_database_tables()

# ==============================================================================
# 4. SESSION STATE MANAGEMENT
# ==============================================================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# ==============================================================================
# 5. AUTHENTICATION MODULE (LOGIN / SIGNUP)
# ==============================================================================
def render_auth_view():
    st.title("🚀 Noob Learning Portal")
    st.write("Welcome to the student and tech learning platform! Please log in or create an account.")
    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔑 User Login")
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username:", placeholder="Enter your username")
            password_input = st.text_input("Password:", type='password', placeholder="Enter your password")
            submit_login = st.form_submit_button("Log In", use_container_width=True)

            if submit_login:
                if not username_input.strip() or not password_input.strip():
                    st.warning("Please fill in both fields.")
                else:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute("SELECT * FROM users WHERE username = %s", (username_input.strip(),))
                        user = cursor.fetchone()
                        cursor.close()
                        conn.close()

                        if user and check_hashes(password_input, user['password_hash']):
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = user['username']
                            st.session_state['user_id'] = user['user_id']
                            st.success(f"Welcome back, @{user['username']}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please try again.")

    with col2:
        st.subheader("📝 New User Registration")
        with st.form("signup_form", clear_on_submit=True):
            new_username = st.text_input("Choose Username:", placeholder="e.g. padmanabh")
            new_password = st.text_input("Choose Password:", type='password')
            confirm_password = st.text_input("Confirm Password:", type='password')
            submit_signup = st.form_submit_button("Register Account", use_container_width=True)

            if submit_signup:
                if not new_username.strip() or not new_password.strip():
                    st.warning("All fields are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            hashed_pwd = make_hashes(new_password)
                            cursor.execute(
                                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                                (new_username.strip(), hashed_pwd)
                            )
                            conn.commit()
                            st.success("Account created successfully! You can now log in on the left.")
                        except mysql.connector.Error as err:
                            if err.errno == 1062:
                                st.error("Username already taken! Please choose another.")
                            else:
                                st.error(f"Registration error: {err}")
                        finally:
                            cursor.close()
                            conn.close()

# ==============================================================================
# 6. ACTIVITY FEED & COMMENTS MODULE
# ==============================================================================
def render_feed_view(current_user):
    st.header("📰 Activity Feed")
    st.caption("See posts, updates, and media shared by all members.")
    st.divider()

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, u.username 
            FROM posts p
            JOIN users u ON p.user_id = u.user_id
            ORDER BY p.created_at DESC
        """)
        posts = cursor.fetchall()

        if not posts:
            st.info("No posts published yet. Be the first to share an update!")
            return

        for post in posts:
            with st.container():
                st.markdown("---")
                # Header row
                col_u1, col_u2 = st.columns([5, 2])
                with col_u1:
                    st.markdown(f"### **@{post['username']}**")
                with col_u2:
                    st.caption(f"🕒 {format_to_ist(post['created_at'])}")

                # Media Display
                media_url = post['media_url']
                if post['media_type'] == 'video':
                    st.video(media_url)
                else:
                    if media_url.startswith("http://") or media_url.startswith("https://"):
                        st.image(media_url, use_container_width=True)
                    else:
                        st.image(f"data:image/png;base64,{media_url}", use_container_width=True)

                # Caption
                if post['caption']:
                    st.markdown(f"**Caption:** {post['caption']}")

                # Action Bar (Likes / Delete)
                col_l1, col_l2, _ = st.columns([1, 1, 4])
                with col_l1:
                    if st.button(f"❤️ Like ({post['likes_count']})", key=f"feed_like_{post['post_id']}"):
                        cursor.execute("UPDATE posts SET likes_count = likes_count + 1 WHERE post_id = %s", (post['post_id'],))
                        conn.commit()
                        st.rerun()

                if post['user_id'] == current_user['user_id']:
                    with col_l2:
                        if st.button("🗑️ Delete", key=f"feed_del_{post['post_id']}"):
                            cursor.execute("DELETE FROM posts WHERE post_id = %s", (post['post_id'],))
                            conn.commit()
                            st.success("Post deleted successfully.")
                            st.rerun()

                # Comments Expander
                cursor.execute("""
                    SELECT c.*, u.username 
                    FROM comments c
                    JOIN users u ON c.user_id = u.user_id
                    WHERE c.post_id = %s
                    ORDER BY c.created_at ASC
                """, (post['post_id'],))
                comments = cursor.fetchall()

                with st.expander(f"💬 Comments ({len(comments)})"):
                    for c in comments:
                        st.markdown(f"**@{c['username']}** `({format_to_ist(c['created_at'])})`: {c['comment_text']}")
                    
                    with st.form(key=f"comment_form_{post['post_id']}", clear_on_submit=True):
                        new_comment = st.text_input("Add a comment...", key=f"c_input_{post['post_id']}")
                        send_comment = st.form_submit_button("Post Comment")
                        if send_comment and new_comment.strip():
                            cursor.execute(
                                "INSERT INTO comments (post_id, user_id, comment_text) VALUES (%s, %s, %s)",
                                (post['post_id'], current_user['user_id'], new_comment.strip())
                            )
                            conn.commit()
                            st.rerun()

    except Exception as e:
        st.error(f"Error loading feed: {e}")
    finally:
        cursor.close()
        conn.close()

# ==============================================================================
# 7. SEARCH & USER DISCOVERY MODULE
# ==============================================================================
def render_search_view(current_user):
    st.header("🔍 Search & Discover Users")
    st.caption("Find classmates, creators, and other network members.")
    st.divider()

    search_query = st.text_input("Search username:", placeholder="Type a name...", key="global_search")

    if search_query.strip():
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT user_id, username, bio, created_at FROM users WHERE username LIKE %s AND user_id != %s",
                    (f"%{search_query.strip()}%", current_user['user_id'])
                )
                results = cursor.fetchall()

                if not results:
                    st.warning("No matching users found.")
                else:
                    st.write(f"Found **{len(results)}** match(es):")
                    for u in results:
                        with st.container():
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"### **@{u['username']}**")
                                st.write(u['bio'] if u['bio'] else "_No bio provided._")
                                st.caption(f"Joined: {format_to_ist(u['created_at'])}")
                            with col2:
                                cursor.execute(
                                    "SELECT * FROM follows WHERE follower_id = %s AND followed_id = %s",
                                    (current_user['user_id'], u['user_id'])
                                )
                                is_following = cursor.fetchone()

                                if is_following:
                                    if st.button("Unfollow", key=f"s_unfollow_{u['user_id']}"):
                                        cursor.execute(
                                            "DELETE FROM follows WHERE follower_id = %s AND followed_id = %s",
                                            (current_user['user_id'], u['user_id'])
                                        )
                                        conn.commit()
                                        st.rerun()
                                else:
                                    if st.button("Follow", key=f"s_follow_{u['user_id']}"):
                                        cursor.execute(
                                            "INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s)",
                                            (current_user['user_id'], u['user_id'])
                                        )
                                        conn.commit()
                                        st.success(f"Now following @{u['username']}!")
                                        st.rerun()
                            st.divider()
            except Exception as e:
                st.error(f"Search failed: {e}")
            finally:
                conn.close()

# ==============================================================================
# 8. NETWORK & FOLLOWING MODULE
# ==============================================================================
def render_friends_view(current_user):
    st.header("👥 Following & Connections")
    st.caption("Manage accounts you follow and explore your network.")
    st.divider()

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.user_id, u.username, u.bio, f.created_at as followed_since 
            FROM follows f
            JOIN users u ON f.followed_id = u.user_id
            WHERE f.follower_id = %s
            ORDER BY f.created_at DESC
        """, (current_user['user_id'],))
        following = cursor.fetchall()

        if not following:
            st.info("You are not following anyone yet. Use the Search tab to find users!")
        else:
            st.subheader(f"Following ({len(following)})")
            for f in following:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**@{f['username']}**")
                        st.write(f['bio'] if f['bio'] else "_No bio_")
                        st.caption(f"Followed since: {format_to_ist(f['followed_since'])}")
                    with col2:
                        if st.button("Unfollow", key=f"f_unfollow_{f['user_id']}"):
                            cursor.execute(
                                "DELETE FROM follows WHERE follower_id = %s AND followed_id = %s",
                                (current_user['user_id'], f['user_id'])
                            )
                            conn.commit()
                            st.rerun()
                    st.divider()
    except Exception as e:
        st.error(f"Error loading connections: {e}")
    finally:
        conn.close()

# ==============================================================================
# 9. DIRECT MESSAGES & GROUP CHAT MODULE
# ==============================================================================
def render_messages_view(current_user):
    st.header("💬 Communication Center")
    st.divider()

    tab1, tab2 = st.tabs(["💬 Direct Messages", "📢 Group Channels"])

    # --- TAB 1: Direct Messaging ---
    with tab1:
        st.subheader("Direct Messages")
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, username FROM users WHERE user_id != %s ORDER BY username ASC", (current_user['user_id'],))
            all_users = cursor.fetchall()

            if not all_users:
                st.info("No other registered users available to chat.")
            else:
                user_dict = {f"@{u['username']}": u['user_id'] for u in all_users}
                selected_label = st.selectbox("Select user to message:", list(user_dict.keys()))
                recipient_id = user_dict[selected_label]

                cursor.execute("""
                    SELECT m.*, u.username as sender_name
                    FROM messages m
                    JOIN users u ON m.sender_id = u.user_id
                    WHERE (sender_id = %s AND receiver_id = %s)
                       OR (sender_id = %s AND receiver_id = %s)
                    ORDER BY sent_at ASC
                """, (current_user['user_id'], recipient_id, recipient_id, current_user['user_id']))
                messages = cursor.fetchall()

                st.write("---")
                chat_box = st.container(height=350)
                with chat_box:
                    if not messages:
                        st.caption("No message history. Say hi!")
                    for msg in messages:
                        is_me = msg['sender_id'] == current_user['user_id']
                        if is_me:
                            st.markdown(f"<div class='chat-bubble-me'><b>You</b> ({format_to_ist(msg['sent_at'])}):<br>{msg['message_text']}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='chat-bubble-other'><b>@{msg['sender_name']}</b> ({format_to_ist(msg['sent_at'])}):<br>{msg['message_text']}</div>", unsafe_allow_html=True)

                with st.form("dm_input_form", clear_on_submit=True):
                    col_input, col_send = st.columns([5, 1])
                    with col_input:
                        dm_text = st.text_input("Type your message...", label_visibility="collapsed")
                    with col_send:
                        dm_send = st.form_submit_button("Send", use_container_width=True)

                    if dm_send and dm_text.strip():
                        cursor.execute(
                            "INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)",
                            (current_user['user_id'], recipient_id, dm_text.strip())
                        )
                        conn.commit()
                        st.rerun()
            conn.close()

    # --- TAB 2: Group Messaging ---
    with tab2:
        st.subheader("Group Channels")
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            with st.expander("➕ Create New Group Channel"):
                with st.form("new_group_form", clear_on_submit=True):
                    g_name = st.text_input("Group Title:")
                    g_desc = st.text_area("Group Description:")
                    btn_g = st.form_submit_button("Create Group")

                    if btn_g and g_name.strip():
                        cursor.execute(
                            "INSERT INTO chat_groups (group_name, description, created_by) VALUES (%s, %s, %s)",
                            (g_name.strip(), g_desc.strip(), current_user['user_id'])
                        )
                        conn.commit()
                        st.success(f"Group '{g_name}' created!")
                        st.rerun()

            cursor.execute("SELECT * FROM chat_groups ORDER BY created_at DESC")
            groups = cursor.fetchall()

            if not groups:
                st.info("No group channels created yet.")
            else:
                g_dict = {g['group_name']: g['group_id'] for g in groups}
                selected_g_name = st.selectbox("Select Group Channel:", list(g_dict.keys()))
                selected_g_id = g_dict[selected_g_name]

                cursor.execute("""
                    SELECT gm.*, u.username as sender_name
                    FROM group_messages gm
                    JOIN users u ON gm.sender_id = u.user_id
                    WHERE gm.group_id = %s
                    ORDER BY gm.sent_at ASC
                """, (selected_g_id,))
                g_msgs = cursor.fetchall()

                st.write("---")
                g_chat_box = st.container(height=350)
                with g_chat_box:
                    if not g_msgs:
                        st.caption("No group messages yet.")
                    for gm in g_msgs:
                        st.markdown(f"**@{gm['sender_name']}** `({format_to_ist(gm['sent_at'])})`: {gm['message_text']}")

                with st.form("group_chat_form", clear_on_submit=True):
                    g_text = st.text_input("Message group channel...")
                    g_send = st.form_submit_button("Send to Group")

                    if g_send and g_text.strip():
                        cursor.execute(
                            "INSERT INTO group_messages (group_id, sender_id, message_text) VALUES (%s, %s, %s)",
                            (selected_g_id, current_user['user_id'], g_text.strip())
                        )
                        conn.commit()
                        st.rerun()
            conn.close()

# ==============================================================================
# 10. PROFILE & POST PUBLISHING MODULE
# ==============================================================================
def render_profile_view(current_user):
    st.header(f"👤 Profile: @{current_user['username']}")
    st.divider()

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT bio, created_at FROM users WHERE user_id = %s", (current_user['user_id'],))
        user_data = cursor.fetchone()

        current_bio = user_data['bio'] if user_data and user_data['bio'] else ""
        
        st.write(f"**Member Since:** {format_to_ist(user_data['created_at']) if user_data else 'N/A'}")
        st.write(f"**Current Bio:** {current_bio if current_bio else '_No bio set yet._'}")

        with st.expander("✏️ Edit Profile Bio"):
            with st.form("bio_update_form"):
                updated_bio = st.text_area("Update Bio:", value=current_bio)
                save_bio = st.form_submit_button("Update Bio")
                if save_bio:
                    cursor.execute("UPDATE users SET bio = %s WHERE user_id = %s", (updated_bio.strip(), current_user['user_id']))
                    conn.commit()
                    st.success("Bio updated!")
                    st.rerun()

        st.divider()

        # Publish Post Section
        st.subheader("➕ Create New Post")
        with st.form("new_post_form", clear_on_submit=True):
            media_type = st.radio("Media Source Type:", ["Upload Image File", "Image / Video URL"], horizontal=True)
            caption = st.text_area("Caption / Description:")

            uploaded_file = None
            url_input = ""

            if media_type == "Upload Image File":
                uploaded_file = st.file_uploader("Choose image file:", type=["png", "jpg", "jpeg", "gif", "webp"])
            else:
                url_input = st.text_input("Enter URL (Image link or YouTube video link):")

            publish_btn = st.form_submit_button("Publish Post")

            if publish_btn:
                final_media = ""
                m_type = "image"

                if uploaded_file is not None:
                    final_media = file_to_base64(uploaded_file.getvalue())
                    m_type = "image"
                elif url_input.strip():
                    final_media = url_input.strip()
                    if "youtube.com" in final_media or "youtu.be" in final_media or final_media.endswith(".mp4"):
                        m_type = "video"

                if not final_media:
                    st.error("Please provide an uploaded image or a valid URL.")
                else:
                    cursor.execute(
                        "INSERT INTO posts (user_id, media_url, media_type, caption) VALUES (%s, %s, %s, %s)",
                        (current_user['user_id'], final_media, m_type, caption.strip())
                    )
                    conn.commit()
                    st.success("Post published successfully!")
                    st.rerun()

        st.divider()

        # Manage User Posts
        st.subheader("🖼️ Your Published Posts")
        cursor.execute("SELECT * FROM posts WHERE user_id = %s ORDER BY created_at DESC", (current_user['user_id'],))
        my_posts = cursor.fetchall()

        if not my_posts:
            st.info("You haven't posted anything yet.")
        else:
            for post in my_posts:
                with st.container():
                    st.caption(f"Posted: {format_to_ist(post['created_at'])}")
                    media = post['media_url']
                    if post['media_type'] == 'video':
                        st.video(media)
                    else:
                        if media.startswith("http://") or media.startswith("https://"):
                            st.image(media, use_container_width=True)
                        else:
                            st.image(f"data:image/png;base64,{media}", use_container_width=True)

                    if post['caption']:
                        st.write(f"**Caption:** {post['caption']}")
                    st.write(f"❤️ Likes: {post['likes_count']}")

                    if st.button("🗑️ Delete Post", key=f"p_del_{post['post_id']}"):
                        cursor.execute("DELETE FROM posts WHERE post_id = %s", (post['post_id'],))
                        conn.commit()
                        st.success("Post deleted!")
                        st.rerun()
                    st.divider()

    except Exception as e:
        st.error(f"Profile error: {e}")
    finally:
        cursor.close()
        conn.close()

# ==============================================================================
# 11. MAIN ROUTER & APP ENTRY POINT
# ==============================================================================
def main():
    if not st.session_state['logged_in']:
        render_auth_view()
    else:
        # Sidebar Profile Info
        st.sidebar.title("🚀 Noob Learning")
        st.sidebar.markdown(f"LoggedIn as: **@{st.session_state['username']}**")
        
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.session_state['user_id'] = None
            st.rerun()

        st.sidebar.divider()

        # Sidebar Menu Navigation
        nav_choice = st.sidebar.radio(
            "Navigation Menu",
            ["📰 Activity Feed", "🔍 Search Users", "👥 Network", "💬 Messages", "👤 My Profile"]
        )

        current_user = {
            "user_id": st.session_state['user_id'],
            "username": st.session_state['username']
        }

        # Page Dispatcher
        if nav_choice == "📰 Activity Feed":
            render_feed_view(current_user)
        elif nav_choice == "🔍 Search Users":
            render_search_view(current_user)
        elif nav_choice == "👥 Network":
            render_friends_view(current_user)
        elif nav_choice == "💬 Messages":
            render_messages_view(current_user)
        elif nav_choice == "👤 My Profile":
            render_profile_view(current_user)

if __name__ == "__main__":
    main()
# ==============================================================================
# UPDATED AUTHENTICATION MODULE (TOGGLE LOGIN / SIGNUP)
# ==============================================================================
def render_auth_view():
    st.subheader("Welcome to Noob Learning 🚀")
    
    # Initialize session state for auth mode if not present
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'

    # Display Login Screen
    if st.session_state['auth_mode'] == 'login':
        st.subheader("🔑 User Login")
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username", placeholder="Enter your username")
            password_input = st.text_input("Password", type='password', placeholder="Enter your password")
            submit_login = st.form_submit_button("Log In", use_container_width=True)

            if submit_login:
                if not username_input.strip() or not password_input.strip():
                    st.warning("Please fill in both fields.")
                else:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute("SELECT * FROM users WHERE username = %s", (username_input.strip(),))
                        user = cursor.fetchone()
                        cursor.close()
                        conn.close()

                        if user and check_hashes(password_input, user['password_hash']):
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = user['username']
                            st.session_state['user_id'] = user['user_id']
                            st.success(f"Welcome back, @{user['username']}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

        st.write("Don't have an account?")
        if st.button("Create Account"):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()

    # Display Create Account Screen
    elif st.session_state['auth_mode'] == 'signup':
        st.subheader("📝 Create New Account")
        with st.form("signup_form", clear_on_submit=True):
            new_username = st.text_input("Choose Username", placeholder="e.g. padmanabh")
            new_password = st.text_input("Choose Password", type='password')
            confirm_password = st.text_input("Confirm Password", type='password')
            submit_signup = st.form_submit_button("Register Account", use_container_width=True)

            if submit_signup:
                if not new_username.strip() or not new_password.strip():
                    st.warning("All fields are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            hashed_pwd = make_hashes(new_password)
                            cursor.execute(
                                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                                (new_username.strip(), hashed_pwd)
                            )
                            conn.commit()
                            st.success("Account created successfully! Redirecting to login...")
                            st.session_state['auth_mode'] = 'login'
                            st.rerun()
                        except Exception as err:
                            st.error(f"Registration error or username taken: {err}")
                        finally:
                            cursor.close()
                            conn.close()

        st.write("Already have an account?")
        if st.button("Back to Login"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()
