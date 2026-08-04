import streamlit as st
import streamlit.components.v1 as components
import mysql.connector
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Instagram | NOOB LEARNING", 
    page_icon="📸", 
    layout="centered"
)

# --- CHATWAY SIDEBAR INTEGRATION ---
with st.sidebar:
    st.subheader("🤖 Saraah AI Assistant")
    chatway_code = """
    <iframe 
        src="https://chatway.app/widget/UbvqSsHWYpja" 
        width="100%" 
        height="450" 
        style="border:none; border-radius:12px;">
    </iframe>
    """
    components.html(chatway_code, height=470)

# --- INSTAGRAM CUSTOM CSS STYLING ---
st.markdown("""
    <style>
    /* Hide Streamlit Chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background-color: #FFFFFF;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
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

    /* Stories Circle Bar Styling */
    .story-container {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .story-circle {
        width: 62px;
        height: 62px;
        border-radius: 50%;
        padding: 2px;
        background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888);
        cursor: pointer;
    }
    .story-img {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px solid white;
        object-fit: cover;
    }
    .story-username {
        font-size: 11px;
        text-align: center;
        margin-top: 4px;
        color: #262626;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 65px;
    }

    /* Profile Stats Text */
    .stat-number {
        font-weight: 700;
        font-size: 16px;
        text-align: center;
        margin-bottom: 0px;
    }
    .stat-label {
        font-size: 12px;
        color: #737373;
        text-align: center;
    }

    /* Instagram Action Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        background-color: #EFEFEF;
        color: #000000;
        border: none;
        height: 35px;
    }
    .stButton>button:hover {
        background-color: #DBDBDB;
        color: #000000;
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
    """ Initializes tables in Aiven MySQL database """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                bio VARCHAR(255) DEFAULT 'Here for a good time',
                profile_pic VARCHAR(500) DEFAULT 'https://picsum.photos/200'
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
        conn.close()

# Run DB Setup
setup_database()

# Session State for User Auth
if "user" not in st.session_state:
    st.session_state.user = None

# ================= AUTHENTICATION (LOGIN / SIGNUP) =================
if not st.session_state.user:
    st.markdown("<h2 style='text-align: center; font-family: sans-serif;'>📸 Instagram</h2>", unsafe_allow_html=True)
    st.caption("Log in or create an account to start sharing.")

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
        st.markdown("<h2 style='margin:0; font-family: sans-serif;'>Instagram</h2>", unsafe_allow_html=True)
    with nav_col2:
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # APP TABS (NAVIGATION BAR AT BOTTOM/TOP)
    app_tab_feed, app_tab_search, app_tab_create, app_tab_msg, app_tab_profile = st.tabs(
        ["🏠 Feed", "🔍 Search", "➕ Create", "💬 Direct", "👤 Profile"]
    )

    # ------------------ TAB 1: MAIN INSTAGRAM FEED ------------------
    with app_tab_feed:
        # HORIZONTAL STORIES BAR
        st.markdown("### Stories")
        story_cols = st.columns(5)
        sample_stories = [
            ("Your story", user['profile_pic']),
            ("super_santi", "https://picsum.photos/200?random=11"),
            ("lil_wyatt", "https://picsum.photos/200?random=12"),
            ("liam_beanz", "https://picsum.photos/200?random=13"),
            ("sprinkles", "https://picsum.photos/200?random=14"),
        ]

        for idx, (s_name, s_img) in enumerate(sample_stories):
            with story_cols[idx]:
                st.markdown(f"""
                    <div class="story-container">
                        <div class="story-circle">
                            <img class="story-img" src="{s_img}" />
                        </div>
                        <div class="story-username">{s_name}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.divider()

        # FEED POSTS DISPLAY
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT posts.post_id, posts.caption, posts.media_url, posts.likes, posts.created_at, 
                       users.username, users.profile_pic
                FROM posts JOIN users ON posts.user_id = users.user_id 
                ORDER BY posts.created_at DESC
            """)
            feed_posts = cursor.fetchall()
            conn.close()

            if not feed_posts:
                st.info("No posts yet! Be the first to share something in the '➕ Create' tab.")
            
            for post in feed_posts:
                with st.container(border=True):
                    # Post Header (User Avatar + Username)
                    h_col1, h_col2 = st.columns([1, 6])
                    with h_col1:
                        pic_url = post["profile_pic"]
                        st.markdown(f'<img src="{pic_url}" style="width:36px; height:36px; border-radius:50%; object-fit:cover;">', unsafe_allow_html=True)
                    with h_col2:
                        st.markdown(f"**{post['username']}**")

                    # Post Media Image
                    if post['media_url']:
                        st.image(post['media_url'], use_container_width=True)

                    # Action Bar (Like, Comment, Share)
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

                    # Likes & Caption
                    st.markdown(f"**{post['likes']} likes**")
                    st.markdown(f"**{post['username']}** {post['caption']}")
                    st.caption(f"{post['created_at']}")

    # ------------------ TAB 2: SEARCH & USERS ------------------
    with app_tab_search:
        st.subheader("🔍 Explore Users")
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
                        user_pic = u['profile_pic']
                        st.markdown(f'<img src="{user_pic}" style="width:40px; height:40px; border-radius:50%; object-fit:cover;">', unsafe_allow_html=True)
                    with sc2:
                        st.markdown(f"**@{u['username']}** `(# {u['user_id']})`")
                        st.caption(u['bio'])
                    with sc3:
                        st.button("View", key=f"user_view_{u['user_id']}")

    # ------------------ TAB 3: CREATE NEW POST ------------------
    with app_tab_create:
        st.subheader("📸 Create New Post")
        img_url_input = st.text_input("Image URL (e.g. https://picsum.photos/600/600)")
        caption_input = st.text_area("Write a caption...", height=100)

        if st.button("Share Post", use_container_width=True):
            if caption_input.strip():
                final_img = img_url_input.strip() if img_url_input.strip() else "https://picsum.photos/600/600"
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO posts (user_id, caption, media_url) VALUES (%s, %s, %s)",
                        (user['user_id'], caption_input, final_img)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Post published successfully!")
                    st.rerun()
            else:
                st.warning("Please enter a caption before sharing.")

    # ------------------ TAB 4: DIRECT MESSAGES (DM) ------------------
    with app_tab_msg:
        st.subheader("💬 Direct Messages")
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
                    st.info("No chat history yet. Send a message below!")
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

    # ------------------ TAB 5: INSTAGRAM PROFILE PAGE ------------------
    with app_tab_profile:
        # Top Header Bar
        top_col1, top_col2, top_col3 = st.columns([6, 1, 1])
        with top_col1:
            st.markdown(f"### **{user['username']}** ∨")
        with top_col2:
            st.markdown("### ➕")
        with top_col3:
            st.markdown("### ☰")

        st.write("")

        # User's total posts count
        user_posts_count = 0
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts WHERE user_id = %s", (user['user_id'],))
            user_posts_count = cursor.fetchone()[0]
            conn.close()

        # Profile Header Section (Avatar + Stats)
        p_col1, p_col2, p_col3, p_col4 = st.columns([2.5, 2, 2, 2])

        with p_col1:
            prof_pic = user['profile_pic']
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

        with p_col3:
            st.markdown('<p class="stat-number">1,134</p>', unsafe_allow_html=True)
            st.markdown('<p class="stat-label">followers</p>', unsafe_allow_html=True)

        with p_col4:
            st.markdown('<p class="stat-number">513</p>', unsafe_allow_html=True)
            st.markdown('<p class="stat-label">following</p>', unsafe_allow_html=True)

        # Bio Section
        st.markdown(f"**{user['username']}**")
        st.markdown(f"{user['bio']}")
        st.markdown(f"🔗 **{user['username']}**")

        # Profile Action Buttons
        b_col1, b_col2, b_col3 = st.columns([4, 4, 1])
        with b_col1:
            st.button("Edit profile", use_container_width=True)
        with b_col2:
            st.button("Share profile", use_container_width=True)
        with b_col3:
            st.button("👤+", use_container_width=True)

        st.divider()

        # Grid Tabs (Posts / Reels / Repost / Tagged)
        tab_grid, tab_reels, tab_repost, tab_tagged = st.tabs(["田", "🎬", "🔄", "👤"])

        with tab_grid:
            # Fetch User's Own Posts for the 3-Column Grid
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT media_url FROM posts WHERE user_id = %s ORDER BY created_at DESC", (user['user_id'],))
                user_media = cursor.fetchall()
                conn.close()

                grid_images = [item['media_url'] for item in user_media if item['media_url']]
                
                # Fallback placeholder images if the user hasn't posted anything yet
                if not grid_images:
                    grid_images = [
                        "https://picsum.photos/300/300?random=1",
                        "https://picsum.photos/300/300?random=2",
                        "https://picsum.photos/300/300?random=3",
                        "https://picsum.photos/300/300?random=4",
                        "https://picsum.photos/300/300?random=5",
                        "https://picsum.photos/300/300?random=6"
                    ]

                # Render 3-Column Image Grid
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
