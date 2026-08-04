import streamlit as st
import streamlit.components.v1 as components
import mysql.connector
import datetime
import base64

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NOOB LEARNING", 
    page_icon="🎓", 
    layout="centered"
)

# --- FORCE BLACK TEXT & LIGHT THEME STYLING ---
st.markdown("""
    <style>
    /* Hide Streamlit Chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Force Light App Background & Black Text everywhere */
    .stApp, div[data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Force all Headings, Titles, Labels, Subtitles to Black */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #000000 !important;
    }

    /* Tab Headers Black Text */
    button[data-baseweb="tab"] div {
        color: #000000 !important;
        font-weight: 600;
    }

    /* Input Field Labels & Text */
    .stTextInput label, .stTextArea label, .stNumberInput label {
        color: #000000 !important;
        font-weight: 600;
    }

    /* Profile Circular Avatar Ring */
    .profile-pic-container {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .profile-pic {
        width: 86px;
        height: 86px;
        border-radius: 50%;
        padding: 3px;
        background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
    }
    .profile-pic-inner {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background-color: white;
        padding: 2px;
        object-fit: cover;
    }

    /* Profile Stats Text */
    .stat-number {
        font-weight: 700;
        font-size: 16px;
        text-align: center;
        margin-bottom: 0px;
        color: #000000 !important;
    }
    .stat-label {
        font-size: 12px;
        color: #555555 !important;
        text-align: center;
    }

    /* Action Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        background-color: #EFEFEF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        height: 38px;
    }
    .stButton>button:hover {
        background-color: #DBDBDB !important;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

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
    """ Initializes tables and updates missing columns safely """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # 1. Create base tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                caption TEXT,
                media_url VARCHAR(1000),
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
        conn.commit()

        # 2. Add missing columns to existing users table if absent
        for alter_query in [
            "ALTER TABLE users ADD COLUMN bio VARCHAR(255) DEFAULT 'Welcome to NOOB LEARNING!'",
            "ALTER TABLE users ADD COLUMN profile_pic LONGTEXT"
        ]:
            try:
                cursor.execute(alter_query)
                conn.commit()
            except mysql.connector.Error:
                # Ignores error if column already exists
                pass

        conn.close()

# Run DB Setup
setup_database()

# Session State for User Auth
if "user" not in st.session_state:
    st.session_state.user = None

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

# ================= AUTHENTICATION (LOGIN / SIGNUP) =================
if not st.session_state.user:
    st.markdown("<h2 style='text-align: center; color: #000000;'>🎓 NOOB LEARNING</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #333333;'>Log in or create an account to get started.</p>", unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["🔒 Log In", "📝 Sign Up"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", use_container_width=True):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
                account = cursor.fetchone()
                conn.close()
                if account:
                    st.session_state.user = account
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

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
                    finally:
                        conn.close()
            else:
                st.warning("Please enter both username and password.")

# ================= MAIN APP INTERFACE =================
else:
    user = st.session_state.user

    # TOP HEADER NAVIGATION
    nav_col1, nav_col2 = st.columns([5, 1])
    with nav_col1:
        st.markdown("<h2 style='margin:0; color: #000000;'>NOOB LEARNING</h2>", unsafe_allow_html=True)
    with nav_col2:
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # APP TABS
    app_tab_feed, app_tab_search, app_tab_create, app_tab_msg, app_tab_profile, app_tab_chatway = st.tabs(
        ["🏠 Feed", "🔍 Search", "➕ Create", "💬 Direct", "👤 Profile", "🤖 AI Support"]
    )

    # ------------------ TAB 1: MAIN FEED ------------------
    with app_tab_feed:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT posts.post_id, posts.caption, posts.media_url, posts.likes, posts.created_at, 
                       users.username, users.profile_pic
                FROM posts 
                JOIN users ON posts.user_id = users.user_id 
                ORDER BY posts.created_at DESC
            """)
            feed_posts = cursor.fetchall()
            conn.close()

            if not feed_posts:
                st.info("No posts yet! Be the first to share something in the '➕ Create' tab.")
            else:
                for post in feed_posts:
                    with st.container(border=True):
                        h_col1, h_col2 = st.columns([1, 6])
                        with h_col1:
                            pic_url = get_user_pic(post)
                            st.markdown(f'<img src="{pic_url}" style="width:36px; height:36px; border-radius:50%; object-fit:cover;">', unsafe_allow_html=True)
                        with h_col2:
                            st.markdown(f"**{post['username']}**")

                        if post['media_url']:
                            st.image(post['media_url'], use_container_width=True)

                        act_col1, act_col2, act_col3, act_col4 = st.columns([1, 1, 1, 5])
                        with act_col1:
                            if st.button("❤️", key=f"like_{post['post_id']}"):
                                conn = get_db_connection()
                                if conn:
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE posts SET likes = likes + 1 WHERE post_id = %s", (post['post_id'],))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
                        with act_col2:
                            st.button("💬", key=f"comment_{post['post_id']}")
                        with act_col3:
                            st.button("✈️", key=f"share_{post['post_id']}")

                        st.markdown(f"**{post['likes']} likes**")
                        st.markdown(f"**{post['username']}** {post['caption']}")
                        st.caption(f"{post['created_at']}")

    # ------------------ TAB 2: SEARCH ------------------
    with app_tab_search:
        st.markdown("### 🔍 Explore Users")
        search_query = st.text_input("Search username...", key="search_bar")
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            if search_query:
                cursor.execute("SELECT user_id, username, profile_pic, bio FROM users WHERE username LIKE %s", (f"%{search_query}%",))
            else:
                cursor.execute("SELECT user_id, username, profile_pic, bio FROM users ORDER BY user_id DESC LIMIT 10")
            found_users = cursor.fetchall()
            conn.close()

            for u in found_users:
                with st.container(border=True):
                    sc1, sc2, sc3 = st.columns([1, 4, 2])
                    with sc1:
                        user_pic = get_user_pic(u)
                        st.markdown(f'<img src="{user_pic}" style="width:40px; height:40px; border-radius:50%; object-fit:cover;">', unsafe_allow_html=True)
                    with sc2:
                        st.markdown(f"**@{u['username']}** `(# {u['user_id']})`")
                        st.caption(get_user_bio(u))
                    with sc3:
                        st.button("View", key=f"user_view_{u['user_id']}")

    # ------------------ TAB 3: CREATE POST ------------------
    with app_tab_create:
        st.markdown("### 📸 Create New Post")
        img_url_input = st.text_input("Image or Video URL")
        caption_input = st.text_area("Write a caption...", height=100)

        if st.button("Share Post", use_container_width=True):
            if caption_input.strip():
                final_img = img_url_input.strip()
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO posts (user_id, caption, media_url) VALUES (%s, %s, %s)",
                        (user['user_id'], caption_input, final_img)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Published successfully!")
                    st.rerun()
            else:
                st.warning("Please enter a caption.")

    # ------------------ TAB 4: DIRECT MESSAGES ------------------
    with app_tab_msg:
        st.markdown("### 💬 Direct Messages")
        target_id = st.number_input("Enter User ID to chat with:", min_value=1, step=1, key="dm_target_id")
        
        if target_id:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT sender_id, message_text, sent_at FROM messages
                    WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
                    ORDER BY sent_at ASC
                """, (user['user_id'], target_id, target_id, user['user_id']))
                messages = cursor.fetchall()
                conn.close()

                st.write("---")
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
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)",
                            (user['user_id'], target_id, msg_input)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

    # ------------------ TAB 5: PROFILE & SETTINGS ------------------
    with app_tab_profile:
        top_col1, top_col2 = st.columns([6, 1])
        with top_col1:
            st.markdown(f"### **{user['username']}**")

        st.write("")

        user_posts_count = 0
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts WHERE user_id = %s", (user['user_id'],))
            user_posts_count = cursor.fetchone()[0]
            conn.close()

        p_col1, p_col2 = st.columns([2.5, 6])

        with p_col1:
            prof_pic = get_user_pic(user)
            st.markdown(f"""
                <div class="profile-pic-container">
                    <div class="profile-pic">
                        <img class="profile-pic-inner" src="{prof_pic}" />
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with p_col2:
            st.markdown(f'<p class="stat-number">{user_posts_count}</p>', unsafe_allow_html=True)
            st.markdown('<p class="stat-label">posts</p>', unsafe_allow_html=True)

        st.markdown(f"**{user['username']}**")
        st.markdown(f"{get_user_bio(user)}")

        with st.expander("⚙️ Settings & Profile Picture (➕ Add / Change)"):
            st.markdown("#### Update Profile Picture")
            
            photo_source = st.radio(
                "Select image source:", 
                ["📁 Gallery / File Upload", "📷 Camera Capture", "🔗 Image URL"],
                horizontal=True
            )
            
            new_pic_data = None

            if photo_source == "📁 Gallery / File Upload":
                uploaded_file = st.file_uploader("Choose an image from gallery...", type=["png", "jpg", "jpeg", "webp"])
                if uploaded_file:
                    new_pic_data = convert_file_to_base64(uploaded_file)

            elif photo_source == "📷 Camera Capture":
                camera_file = st.camera_input("Take a photo")
                if camera_file:
                    new_pic_data = convert_file_to_base64(camera_file)

            elif photo_source == "🔗 Image URL":
                url_input = st.text_input("Enter image direct link:")
                if url_input.strip():
                    new_pic_data = url_input.strip()

            if st.button("➕ Save Profile Picture", use_container_width=True):
                if new_pic_data:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET profile_pic = %s WHERE user_id = %s", (new_pic_data, user['user_id']))
                        conn.commit()
                        conn.close()
                        st.session_state.user['profile_pic'] = new_pic_data
                        st.success("Profile picture updated!")
                        st.rerun()
                else:
                    st.warning("Please select or capture a photo first.")

            st.divider()
            
            st.markdown("#### Edit Bio")
            new_bio = st.text_input("New Bio Text", value=get_user_bio(user))
            if st.button("Save Bio", use_container_width=True):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET bio = %s WHERE user_id = %s", (new_bio, user['user_id']))
                    conn.commit()
                    conn.close()
                    st.session_state.user['bio'] = new_bio
                    st.success("Bio updated successfully!")
                    st.rerun()

        st.divider()

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT media_url FROM posts WHERE user_id = %s ORDER BY created_at DESC", (user['user_id'],))
            user_media = cursor.fetchall()
            conn.close()

            grid_images = [item['media_url'] for item in user_media if item['media_url']]
            
            if not grid_images:
                st.info("No posts yet.")
            else:
                for i in range(0, len(grid_images), 3):
                    g_col1, g_col2, g_col3 = st.columns(3)
                    with g_col1:
                        if i < len(grid_images):
                            st.image(grid_images[i], use_container_width=True)
                    with g_col2:
                        if i + 1 < len(grid_images):
                            st.image(grid_images[i+1], use_container_width=True)
                    with g_col3:
                        if i + 2 < len(grid_images):
                            st.image(grid_images[i+2], use_container_width=True)

    # ------------------ TAB 6: AI SUPPORT ------------------
    with app_tab_chatway:
        st.markdown("### 🤖 Saraah AI Support Assistant")
        chatway_code = """
        <iframe 
            src="https://chatway.app/widget/UbvqSsHWYpja" 
            width="100%" 
            height="550" 
            style="border:none; border-radius:12px;">
        </iframe>
        """
        components.html(chatway_code, height=570)
