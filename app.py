import streamlit as st
import streamlit.components.v1 as components
import mysql.connector
import datetime
import base64
import zoneinfo  # Built-in in Python 3.9+ for accurate IST timezone

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NOOB LEARNING", 
    page_icon="🎓", 
    layout="centered"
)

# --- AIVEN DATABASE CONFIGURATION ---
DB_CONFIG = {
    "host": "mysql-22faa093-padmanabhsingh11107035-84a9.l.aivencloud.com",
    "port": 21354,
    "user": "avnadmin",
    "password": "AVNS_iN1XY9WAsRFlUWVhM6k",
    "database": "defaultdb"
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: {err}")
        return None

def setup_database():
    """ Initializes tables and safely updates missing columns """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    bio VARCHAR(255) DEFAULT 'Welcome to NOOB LEARNING!',
                    profile_pic LONGTEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    caption TEXT,
                    media_url LONGTEXT,
                    likes INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT,
                    receiver_id INT,
                    message_text TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(user_id),
                    FOREIGN KEY (receiver_id) REFERENCES users(user_id)
                );
            """)
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
            conn.commit()

            # Ensure extra columns exist on older posts/users tables
            alters = [
                "ALTER TABLE users ADD COLUMN bio VARCHAR(255) DEFAULT 'Welcome to NOOB LEARNING!'",
                "ALTER TABLE users ADD COLUMN profile_pic LONGTEXT",
                "ALTER TABLE posts ADD COLUMN likes INT DEFAULT 0",
                "ALTER TABLE posts MODIFY COLUMN media_url LONGTEXT"
            ]
            for alter_sql in alters:
                try:
                    cursor.execute(alter_sql)
                    conn.commit()
                except mysql.connector.Error:
                    pass
        except Exception as e:
            st.error(f"Setup Error: {e}")
        finally:
            conn.close()

# Run DB Setup
setup_database()

# Session State Initializations
if "user" not in st.session_state:
    st.session_state.user = None
if "view_user_id" not in st.session_state:
    st.session_state.view_user_id = None

def get_user_pic(u_dict):
    if u_dict and isinstance(u_dict, dict) and u_dict.get("profile_pic"):
        return u_dict["profile_pic"]
    return "https://via.placeholder.com/150"

def get_user_bio(u_dict):
    if u_dict and isinstance(u_dict, dict) and u_dict.get("bio"):
        return u_dict["bio"]
    return "Welcome to NOOB LEARNING!"

def convert_file_to_base64(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode()
    mime_type = uploaded_file.type
    return f"data:{mime_type};base64,{base64_str}"

def render_html_image(img_url, width=40, height=40, circle=True):
    style = f"width:{width}px; height:{height}px; object-fit:cover;"
    if circle:
        style += " border-radius:50%;"
    st.markdown(f'<img src="{img_url}" style="{style}">', unsafe_allow_html=True)

def format_to_ist(dt_object):
    """ Helper to format database timestamps accurately into 12-hour IST time """
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

def delete_post_by_id(post_id):
    """ Helper function to delete a post """
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

def update_post_caption(post_id, new_caption):
    """ Helper function to edit a post caption """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE posts SET caption = %s WHERE post_id = %s", (new_caption, post_id))
            conn.commit()
            st.toast("Post updated!", icon="✏️")
        except Exception as e:
            st.error(f"Failed to update post: {e}")
        finally:
            conn.close()

def get_follower_count(user_id):
    """ Returns total followers count for a user_id """
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

def is_following(follower_id, following_id):
    """ Checks if follower_id is following following_id """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT follow_id FROM follows WHERE follower_id = %s AND following_id = %s", (follower_id, following_id))
            return cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            conn.close()
    return False

def toggle_follow(follower_id, following_id):
    """ Follows or Unfollows a user """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if is_following(follower_id, following_id):
                cursor.execute("DELETE FROM follows WHERE follower_id = %s AND following_id = %s", (follower_id, following_id))
                st.toast("Unfollowed user!", icon="👤")
            else:
                cursor.execute("INSERT INTO follows (follower_id, following_id) VALUES (%s, %s)", (follower_id, following_id))
                st.toast("Follow request sent!", icon="➕")
            conn.commit()
        except Exception as e:
            st.error(f"Follow action failed: {e}")
        finally:
            conn.close()

# Dialog for Top Left Profile Icon Click
@st.dialog("📷 Update Profile Picture")
def update_profile_pic_dialog():
    st.write("Upload or take a photo to change your profile picture.")
    photo_source = st.radio(
        "Source:", 
        ["📁 Upload Image", "📷 Camera Capture", "🔗 URL Link"],
        horizontal=True
    )
    new_pic = None
    if photo_source == "📁 Upload Image":
        file = st.file_uploader("Choose file...", type=["png", "jpg", "jpeg", "webp"])
        if file:
            new_pic = convert_file_to_base64(file)
    elif photo_source == "📷 Camera Capture":
        cam_file = st.camera_input("Take photo")
        if cam_file:
            new_pic = convert_file_to_base64(cam_file)
    elif photo_source == "🔗 URL Link":
        url = st.text_input("Enter image link:")
        if url.strip():
            new_pic = url.strip()

    if st.button("Save Picture", use_container_width=True):
        if new_pic:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET profile_pic = %s WHERE user_id = %s", (new_pic, st.session_state.user['user_id']))
                    conn.commit()
                    st.session_state.user['profile_pic'] = new_pic
                    st.success("Profile picture updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    conn.close()

# ================= AUTHENTICATION =================
if not st.session_state.user:
    st.title("🎓 NOOB LEARNING")
    st.write("Log in or create an account to get started.")

    tab_login, tab_signup = st.tabs(["🔒 Log In", "📝 Sign Up"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", use_container_width=True):
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
                    account = cursor.fetchone()
                    if account:
                        st.session_state.user = account
                        st.success("Logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except Exception as e:
                    st.error(f"Login failed: {e}")
                finally:
                    conn.close()

    with tab_signup:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Sign Up", use_container_width=True):
            if new_user and new_pass:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_user, new_pass))
                        conn.commit()
                        st.success("Account created! Please log in.")
                    except mysql.connector.IntegrityError:
                        st.error("Username already taken.")
                    except Exception as e:
                        st.error(f"Sign up error: {e}")
                    finally:
                        conn.close()
            else:
                st.warning("Please fill in both fields.")

# ================= MAIN APP INTERFACE =================
else:
    user = st.session_state.user
    my_followers_count = get_follower_count(user['user_id'])

    # TOP HEADER WITH USER PROFILE ICON & CLOCK
    header_col1, header_col2, header_col3 = st.columns([1, 3, 2])
    with header_col1:
        user_avatar = get_user_pic(user)
        render_html_image(user_avatar, width=44, height=44, circle=True)
        if st.button("📷 Edit", key="top_profile_icon_btn"):
            update_profile_pic_dialog()

    with header_col2:
        st.markdown(f"### **NOOB LEARNING**")
        st.caption(f"Logged in as **@{user['username']}** | 👥 Followers: **{my_followers_count}**")

    with header_col3:
        ist_now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata"))
        st.markdown(f"🕒 **{ist_now.strftime('%I:%M %p')}** | `{ist_now.strftime('%d %b %Y')}`")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.view_user_id = None
            st.rerun()

    st.divider()

    app_tab_feed, app_tab_search, app_tab_friends, app_tab_create, app_tab_msg, app_tab_profile, app_tab_chatway = st.tabs(
        ["🏠 Feed", "🔍 Search", "👥 Add Friends", "➕ Create", "💬 Direct", "👤 Profile", "🤖 AI Support"]
    )

    # ------------------ TAB 1: MAIN FEED ------------------
    with app_tab_feed:
        conn = get_db_connection()
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
                feed_posts = []
            finally:
                conn.close()

            if not feed_posts:
                st.info("No posts yet! Create one in the '➕ Create' tab.")
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
                            if st.button("👤 View Profile", key=f"feed_view_{post['post_id']}"):
                                st.session_state.view_user_id = post['user_id']
                                st.rerun()

                        if post['media_url']:
                            render_html_image(post['media_url'], width=380, height=380, circle=False)

                        # Bottom row: Likes on left, Three Dots Options Popover on far right
                        act_col1, act_col2, act_col3 = st.columns([1, 4, 1])
                        with act_col1:
                            if st.button("❤️", key=f"like_{post['post_id']}"):
                                conn_like = get_db_connection()
                                if conn_like:
                                    c_like = conn_like.cursor()
                                    c_like.execute("UPDATE posts SET likes = likes + 1 WHERE post_id = %s", (post['post_id'],))
                                    conn_like.commit()
                                    conn_like.close()
                                    st.rerun()

                        with act_col3:
                            with st.popover("⋮", help="Post Options"):
                                st.write("**Post Options**")
                                
                                # SHARE OPTION
                                if st.button("🔗 Share Post/Reel", key=f"feed_share_{post['post_id']}", use_container_width=True):
                                    st.code(f"Post ID: {post['post_id']} by @{post['username']}\nCaption: {post['caption']}")
                                    st.toast("Post details copied above!", icon="🔗")

                                # EDIT & DELETE OPTIONS (Only shown if current user is owner)
                                if post['user_id'] == user['user_id']:
                                    st.divider()
                                    with st.expander("✏️ Edit Caption"):
                                        edited_cap = st.text_area("New Caption", value=post['caption'], key=f"feed_edit_txt_{post['post_id']}")
                                        if st.button("Save Changes", key=f"feed_save_edit_{post['post_id']}", use_container_width=True):
                                            update_post_caption(post['post_id'], edited_cap)
                                            st.rerun()

                                    if st.button("🗑️ Delete Post/Reel", key=f"feed_del_{post['post_id']}", type="primary", use_container_width=True):
                                        delete_post_by_id(post['post_id'])
                                        st.rerun()

                        st.write(f"**{post['likes']} likes**")
                        st.write(f"**@{post['username']}**: {post['caption']}")

    # ------------------ TAB 2: SEARCH ------------------
    with app_tab_search:
        st.subheader("🔍 Search Accounts")
        search_query = st.text_input("Search username or user ID...", key="search_bar")
        
        conn = get_db_connection()
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
                found_users = []
            finally:
                conn.close()

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

    # ------------------ TAB 3: ADD FRIENDS ------------------
    with app_tab_friends:
        st.subheader("👥 Add Friends & View All User IDs")
        st.write("Browse all registered accounts, see their user IDs, and send follow requests.")
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT user_id, username, profile_pic, bio FROM users ORDER BY user_id ASC")
                all_users = cursor.fetchall()
            except Exception as e:
                st.error(f"Error fetching users: {e}")
                all_users = []
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

    # ------------------ TAB 4: CREATE POST ------------------
    with app_tab_create:
        st.subheader("📸 Create New Post / Reel")
        
        media_input = None
        media_source = st.radio("Media Type:", ["📁 Image File", "📷 Take Photo", "🔗 Image / Reel URL"], horizontal=True)
        if media_source == "📁 Image File":
            up_f = st.file_uploader("Upload media...", type=["png", "jpg", "jpeg", "webp"])
            if up_f:
                media_input = convert_file_to_base64(up_f)
        elif media_source == "📷 Take Photo":
            cam_f = st.camera_input("Snap picture")
            if cam_f:
                media_input = convert_file_to_base64(cam_f)
        elif media_source == "🔗 Image / Reel URL":
            url_f = st.text_input("Direct URL link")
            if url_f.strip():
                media_input = url_f.strip()

        caption_input = st.text_area("Write a caption...", height=100)

        if st.button("Share Post", use_container_width=True):
            if caption_input.strip():
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        now_ist = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute(
                            "INSERT INTO posts (user_id, caption, media_url, created_at) VALUES (%s, %s, %s, %s)",
                            (user['user_id'], caption_input, media_input, now_ist)
                        )
                        conn.commit()
                        st.success("Published successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to share: {e}")
                    finally:
                        conn.close()
            else:
                st.warning("Please enter a caption.")

    # ------------------ TAB 5: DIRECT MESSAGES ------------------
    with app_tab_msg:
        st.subheader("💬 Direct Messages")
        target_id = st.number_input("Enter User ID to chat with:", min_value=1, step=1, key="dm_target_id")
        
        if target_id:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT sender_id, message_text, sent_at FROM messages
                        WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
                        ORDER BY sent_at ASC
                    """, (user['user_id'], target_id, target_id, user['user_id']))
                    messages = cursor.fetchall()
                except Exception as e:
                    st.error(f"Chat load error: {e}")
                    messages = []
                finally:
                    conn.close()

                st.divider()
                if not messages:
                    st.info("No chat history yet.")
                for m in messages:
                    if m['sender_id'] == user['user_id']:
                        st.chat_message("user").write(m['message_text'])
                    else:
                        st.chat_message("assistant").write(m['message_text'])

            msg_input = st.text_input("Type a message...", key="chat_dm_input")
            if st.button("Send", use_container_width=True):
                if msg_input.strip():
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)",
                                (user['user_id'], target_id, msg_input)
                            )
                            conn.commit()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Send failed: {e}")
                        finally:
                            conn.close()

    # ------------------ TAB 6: PROFILE & SETTINGS ------------------
    with app_tab_profile:
        # Determine whether viewing logged-in user or selected user
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
            render_html_image(get_user_pic(p_user), width=80, height=80, circle=True)
        with p_col2:
            st.write(f"**User ID:** `{p_user['user_id']}`")
            st.write(f"👥 **Followers:** {prof_f_count}")
            st.write(f"🎬 **Posts / Reels:** {user_posts_count}")
            st.write(f"📝 **Bio:** {get_user_bio(p_user)}")

            if p_user['user_id'] != user['user_id']:
                following_p = is_following(user['user_id'], p_user['user_id'])
                p_btn_label = "✔ Following" if following_p else "➕ Send Follow Request"
                if st.button(p_btn_label, key="profile_follow_toggle_btn"):
                    toggle_follow(user['user_id'], p_user['user_id'])
                    st.rerun()

        # Only display edit settings if viewing own profile
        if p_user['user_id'] == user['user_id']:
            with st.expander("⚙️ Edit Bio"):
                new_bio = st.text_input("New Bio Text", value=get_user_bio(user))
                if st.button("Save Bio", use_container_width=True):
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET bio = %s WHERE user_id = %s", (new_bio, user['user_id']))
                            conn.commit()
                            st.session_state.user['bio'] = new_bio
                            st.success("Bio updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update bio: {e}")
                        finally:
                            conn.close()

        st.divider()
        st.write("### 🎬 Posts & Reels Grid")

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT post_id, caption, media_url, likes, created_at FROM posts WHERE user_id = %s ORDER BY created_at DESC", (p_user['user_id'],))
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
                                
                                if st.button("🔗 Share Post/Reel", key=f"prof_share_{item['post_id']}", use_container_width=True):
                                    st.code(f"Post ID: {item['post_id']}\nCaption: {item['caption']}")
                                    st.toast("Post details copied above!", icon="🔗")

                                if p_user['user_id'] == user['user_id']:
                                    st.divider()
                                    with st.expander("✏️ Edit Caption"):
                                        p_edited_cap = st.text_area("New Caption", value=item['caption'], key=f"prof_edit_txt_{item['post_id']}")
                                        if st.button("Save Changes", key=f"prof_save_edit_{item['post_id']}", use_container_width=True):
                                            update_post_caption(item['post_id'], p_edited_cap)
                                            st.rerun()

                                    if st.button("🗑️ Delete Post/Reel", key=f"prof_del_{item['post_id']}", type="primary", use_container_width=True):
                                        delete_post_by_id(item['post_id'])
                                        st.rerun()

                        st.write(f"📝 {item['caption']}")
                        st.caption(format_to_ist(item['created_at']))

    # ------------------ TAB 7: AI SUPPORT ------------------
    with app_tab_chatway:
        st.subheader("🤖 Saraah AI Support Assistant")
        chatway_code = """
        <iframe 
            src="https://chatway.app/widget/UbvqSsHWYpja" 
            width="100%" 
            height="550" 
            style="border:none; border-radius:12px;">
        </iframe>
        """
        components.html(chatway_code, height=570)
