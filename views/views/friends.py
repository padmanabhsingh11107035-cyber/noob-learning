import streamlit as st
from config.database import get_db_connection

def render_friends_view(current_user):
    st.subheader("👥 Following & Network")
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.user_id, u.username, u.bio 
            FROM follows f
            JOIN users u ON f.followed_id = u.user_id
            WHERE f.follower_id = %s
        """, (current_user['user_id'],))
        following = cursor.fetchall()
        
        st.write("### Accounts You Follow")
        if not following:
            st.info("You aren't following anyone yet.")
        else:
            for f in following:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**@{f['username']}** `(ID: {f['user_id']})`")
                with col2:
                    if st.button("Unfollow", key=f"unfollow_{f['user_id']}"):
                        cursor.execute(
                            "DELETE FROM follows WHERE follower_id = %s AND followed_id = %s",
                            (current_user['user_id'], f['user_id'])
                        )
                        conn.commit()
                        st.rerun()
    except Exception as e:
        st.error(f"Network error: {e}")
    finally:
        conn.close()
