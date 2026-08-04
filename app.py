import streamlit as st
from config.database import init_database_tables, get_db_connection
from views.auth import render_auth_view
from views.feed import render_feed_view
from views.search import render_search_view
from views.friends import render_friends_view
from views.messages import render_messages_view
from views.profile import render_profile_view

# Page Config
st.set_page_config(
    page_title="Noob Learning",
    page_icon="🚀",
    layout="wide"
)

# Initialize Database Schema
init_database_tables()

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

def main():
    if not st.session_state['logged_in']:
        render_auth_view()
    else:
        st.sidebar.title(f"Welcome, @{st.session_state['username']}!")
        
        # Logout button
        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.session_state['user_id'] = None
            st.rerun()

        st.sidebar.divider()

        # Navigation
        menu = ["📰 Activity Feed", "🔍 Search Users", "👥 Following", "💬 Messages", "👤 Profile"]
        choice = st.sidebar.radio("Navigation", menu)

        current_user = {
            "user_id": st.session_state['user_id'],
            "username": st.session_state['username']
        }

        if choice == "📰 Activity Feed":
            render_feed_view(current_user)
        elif choice == "🔍 Search Users":
            render_search_view(current_user)
        elif choice == "👥 Following":
            render_friends_view(current_user)
        elif choice == "💬 Messages":
            render_messages_view(current_user)
        elif choice == "👤 Profile":
            render_profile_view(current_user)

if __name__ == "__main__":
    main()
