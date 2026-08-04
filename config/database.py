import mysql.connector
from mysql.connector import pooling
import streamlit as st

DB_CONFIG = {
    "host": st.secrets.get("DB_HOST", "localhost"),
    "port": int(st.secrets.get("DB_PORT", 3306)),
    "user": st.secrets.get("DB_USER", "root"),
    "password": st.secrets.get("DB_PASSWORD", ""),
    "database": st.secrets.get("DB_NAME", "noob_learning_db"),
    "pool_name": "mypool",
    "pool_size": 5
}

@st.cache_resource
def get_db_pool():
    try:
        pool = mysql.connector.pooling.MySQLConnectionPool(**DB_CONFIG)
        return pool
    except Exception as e:
        st.error(f"Failed to initialize MySQL Connection Pool: {e}")
        return None

def get_db_connection():
    try:
        pool = get_db_pool()
        if pool:
            return pool.get_connection()
        return mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

def init_database_tables():
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        
        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                bio TEXT,
                profile_pic LONGTEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Posts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                media_url LONGTEXT NOT NULL,
                media_type VARCHAR(20) DEFAULT 'image',
                caption TEXT,
                likes_count INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                message_text TEXT NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Follows Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS follows (
                follow_id INT AUTO_INCREMENT PRIMARY KEY,
                follower_id INT NOT NULL,
                followed_id INT NOT NULL,
                status VARCHAR(20) DEFAULT 'accepted',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (followed_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE KEY unique_follow (follower_id, followed_id)
            )
        """)
        
        # Chat Groups Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_groups (
                group_id INT AUTO_INCREMENT PRIMARY KEY,
                group_name VARCHAR(150) NOT NULL,
                created_by INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Group Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                g_msg_id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT NOT NULL,
                sender_id INT NOT NULL,
                message_text TEXT NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES chat_groups(group_id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
    except Exception as e:
        st.error(f"Schema Migration Error: {e}")
    finally:
        cursor.close()
        conn.close()
