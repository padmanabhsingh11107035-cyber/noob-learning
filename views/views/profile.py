import streamlit as st
from config.database import get_db_connection
from utils.helpers import file_to_base64, format_to_ist

def render_profile_view(current_user):
    st.subheader(f"👤 Profile: @{current_user['username']}")
    
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)
        
        # Display/Update Bio Section
        cursor.execute("SELECT bio, created_at FROM users WHERE user_id = %s", (current_user['user_id'],))
        u_info = cursor.fetchone()
        
        current_bio = u_info['bio'] if u_info and u_info['bio'] else ""
        st.write(f"**Member Since:** {format_to_ist(u_info['created_at']) if u_info else 'N/A'}")
        
        with st.expander("✏️ Edit Bio"):
            with st.form("edit_bio_form"):
                new_bio = st.text_area("Update your bio:", value=current_bio)
                if st.form_submit_button("Save Bio"):
                    cursor.execute("UPDATE users SET bio = %s WHERE user_id = %s", (new_bio, current_user['user_id']))
                    conn.commit()
                    st.success("Bio updated successfully!")
                    st.rerun()

        st.divider()

        # Create New Post Section
        st.subheader("➕ Create a New Post")
        with st.form("create_post_form", clear_on_submit=True):
            media_type = st.radio("Media Type:", ["Image", "Video"], horizontal=True)
            caption = st.text_area("Write a caption:")
            
            if media_type == "Image":
                uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "gif"])
                media_url_input = st.text_input("OR enter Image URL:")
            else:
                uploaded_file = None
                media_url_input = st.text_input("Enter Video URL (YouTube, MP4 link, etc.):")

            submit_post = st.form_submit_button("Publish Post")

            if submit_post:
                final_media = ""
                m_type = "image" if media_type == "Image" else "video"

                if uploaded_file is not None:
                    bytes_data = uploaded_file.getvalue()
                    final_media = file_to_base64(bytes_data)
                elif media_url_input.strip():
                    final_media = media_url_input.strip()

                if not final_media:
                    st.error("Please upload a file or provide a valid URL.")
                else:
                    cursor.execute(
                        "INSERT INTO posts (user_id, media_url, media_type, caption) VALUES (%s, %s, %s, %s)",
                        (current_user['user_id'], final_media, m_type, caption)
                    )
                    conn.commit()
                    st.success("Post published successfully!")
                    st.rerun()

        st.divider()

        # User's Own Posts Grid/List
        st.subheader("🖼️ Your Posts")
        cursor.execute("SELECT * FROM posts WHERE user_id = %s ORDER BY created_at DESC", (current_user['user_id'],))
        my_posts = cursor.fetchall()

        if not my_posts:
            st.info("You haven't posted anything yet.")
        else:
            for post in my_posts:
                with st.container():
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
                    st.write(f"❤️ Likes: {post['likes_count']}")
                    
                    if st.button("🗑️ Delete Post", key=f"my_del_{post['post_id']}"):
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
