import streamlit as st
from config.database import get_db_connection

def render_search_view(current_user):
    st.subheader("🔍 Search Users")
    search_query = st.text_input("Search by username:", key="user_search_input")
    
    if search_query:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT user_id, username, bio FROM users WHERE username LIKE %s AND user_id != %s",
                    (f"%{search_query}%", current_user['user_id'])
                )
                results = cursor.fetchall()
                
                if not results:
                    st.warning("No users found.")
                else:
                    for u in results:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**@{u['username']}** `(ID: {u['user_id']})`")
                            st.caption(u['bio'] if u['bio'] else "No bio provided.")
                        with col2:
                            if st.button("Follow", key=f"follow_search_{u['user_id']}"):
                                try:
                                    c_follow = conn.cursor()
                                    c_follow.execute(
                                        "INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s)",
                                        (current_user['user_id'], u['user_id'])
                                    )
                                    conn.commit()
                                    st.success(f"Followed @{u['username']}!")
                                except Exception:
                                    st.info("Already following.")
                        st.divider()
            except Exception as e:
                st.error(f"Search error: {e}")
            finally:
                conn.close()
