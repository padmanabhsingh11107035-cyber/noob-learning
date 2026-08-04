import streamlit as st
from config.database import get_db_connection
from utils.helpers import format_to_ist

def render_feed_view(user):
    st.subheader("📰 Activity Feed")
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
            st.info("No posts in the feed yet. Be the first to share something!")
            return
            
        for post in posts:
            with st.container():
                st.markdown("---")
                col_u1, col_u2 = st.columns([1, 6])
                with col_u1:
                    st.write(f"**@{post['username']}**")
                with col_u2:
                    st.caption(f"Posted on {format_to_ist(post['created_at'])}")
                
                media_url = post['media_url']
                if post['media_type'] == 'video':
                    st.video(media_url)
                else:
                    if media_url.startswith("http://") or media_url.startswith("https://"):
                        st.image(media_url, use_container_width=True)
                    else:
                        st.image(f"data:image/png;base64,{media_url}", use_container_width=True)
                
                st.write(post['caption'])
                
                col_l1, col_l2, _ = st.columns([1, 1, 4])
                with col_l1:
                    if st.button(f"❤️ {post['likes_count']}", key=f"like_{post['post_id']}"):
                        cursor.execute("UPDATE posts SET likes_count = likes_count + 1 WHERE post_id = %s", (post['post_id'],))
                        conn.commit()
                        st.rerun()
                
                if post['user_id'] == user['user_id']:
                    with col_l2:
                        if st.button("🗑️ Delete", key=f"del_{post['post_id']}"):
                            cursor.execute("DELETE FROM posts WHERE post_id = %s", (post['post_id'],))
                            conn.commit()
                            st.success("Post deleted!")
                            st.rerun()
    except Exception as e:
        st.error(f"Error loading feed: {e}")
    finally:
        cursor.close()
        conn.close()
