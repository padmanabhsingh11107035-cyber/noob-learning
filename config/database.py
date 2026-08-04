import mysql.connector
from mysql.connector import errorcode
import streamlit as st

def get_db_connection():
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
        st.error(f"Database connection error: {err}")
        return None

def init_database_tables():
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    tables = {}

    tables['users'] = (
        "CREATE TABLE IF NOT EXISTS `users` ("
        "  `user_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `username` VARCHAR(50) NOT NULL UNIQUE,"
        "  `password_hash` VARCHAR(255) NOT NULL,"
        "  `bio` TEXT,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ") ENGINE=InnoDB;"
    )

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
        ") ENGINE=InnoDB;"
    )

    tables['follows'] = (
        "CREATE TABLE IF NOT EXISTS `follows` ("
        "  `follower_id` INT NOT NULL,"
        "  `followed_id` INT NOT NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  PRIMARY KEY (`follower_id`, `followed_id`),"
        "  FOREIGN KEY (`follower_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`followed_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB;"
    )

    tables['messages'] = (
        "CREATE TABLE IF NOT EXISTS `messages` ("
        "  `message_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `sender_id` INT NOT NULL,"
        "  `receiver_id` INT NOT NULL,"
        "  `message_text` TEXT NOT NULL,"
        "  `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`sender_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`receiver_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB;"
    )

    tables['chat_groups'] = (
        "CREATE TABLE IF NOT EXISTS `chat_groups` ("
        "  `group_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `group_name` VARCHAR(100) NOT NULL,"
        "  `created_by` INT NOT NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`created_by`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB;"
    )

    tables['group_messages'] = (
        "CREATE TABLE IF NOT EXISTS `group_messages` ("
        "  `g_msg_id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `group_id` INT NOT NULL,"
        "  `sender_id` INT NOT NULL,"
        "  `message_text` TEXT NOT NULL,"
        "  `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`group_id`) REFERENCES `chat_groups`(`group_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`sender_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB;"
    )

    for table_name, table_sql in tables.items():
        try:
            cursor.execute(table_sql)
        except mysql.connector.Error as err:
            st.error(f"Error creating table {table_name}: {err}")

    conn.commit()
    cursor.close()
    conn.close()
