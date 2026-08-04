import streamlit as st
from config.database import get_db_connection
from utils.helpers import format_to_ist

def render_messages_view(current_user):
    st.subheader("💬 Messages & Chat Groups")
    tab1, tab2 = st.tabs(["Direct Messages", "Group Chats"])

    # --- TAB 1: Direct Messaging ---
    with tab1:
        st.write("### Direct Messaging")
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, username FROM users WHERE user_id != %s", (current_user['user_id'],))
            all_users = cursor.fetchall()
            
            if not all_users:
                st.info("No other users available to message.")
            else:
                user_dict = {u['username']: u['user_id'] for u in all_users}
                selected_user = st.selectbox("Select user to message:", list(user_dict.keys()))
                recipient_id = user_dict[selected_user]

                # Fetch conversation
                cursor.execute("""
                    SELECT m.*, u.username as sender_name
                    FROM messages m
                    JOIN users u ON m.sender_id = u.user_id
                    WHERE (sender_id = %s AND receiver_id = %s)
                       OR (sender_id = %s AND receiver_id = %s)
                    ORDER BY sent_at ASC
                """, (current_user['user_id'], recipient_id, recipient_id, current_user['user_id']))
                chat_history = cursor.fetchall()

                # Display Chat History
                st.write("---")
                st.write(f"**Chat with @{selected_user}:**")
                chat_container = st.container(height=300)
                with chat_container:
                    if not chat_history:
                        st.caption("No messages yet. Start the conversation!")
                    for msg in chat_history:
                        is_me = msg['sender_id'] == current_user['user_id']
                        align = "👉" if is_me else "👈"
                        st.markdown(f"**{align} {msg['sender_name']}** `{format_to_ist(msg['sent_at'])}`:")
                        st.write(msg['message_text'])

                # Send New Message
                with st.form(key="dm_form", clear_on_submit=True):
                    new_msg = st.text_input("Type your message:")
                    submit_dm = st.form_submit_button("Send DM")
                    if submit_dm and new_msg.strip():
                        cursor.execute(
                            "INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)",
                            (current_user['user_id'], recipient_id, new_msg.strip())
                        )
                        conn.commit()
                        st.rerun()
            conn.close()

    # --- TAB 2: Group Chats ---
    with tab2:
        st.write("### Group Messaging")
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Create a New Group Form
            with st.expander("➕ Create New Group"):
                with st.form("create_group_form", clear_on_submit=True):
                    g_name = st.text_input("Group Name:")
                    create_btn = st.form_submit_button("Create Group")
                    if create_btn and g_name.strip():
                        cursor.execute(
                            "INSERT INTO chat_groups (group_name, created_by) VALUES (%s, %s)",
                            (g_name.strip(), current_user['user_id'])
                        )
                        conn.commit()
                        st.success(f"Group '{g_name}' created!")
                        st.rerun()

            # Select Existing Group
            cursor.execute("SELECT * FROM chat_groups ORDER BY created_at DESC")
            groups = cursor.fetchall()

            if not groups:
                st.info("No active groups found. Create one above!")
            else:
                group_dict = {g['group_name']: g['group_id'] for g in groups}
                selected_group_name = st.selectbox("Select Group:", list(group_dict.keys()))
                selected_group_id = group_dict[selected_group_name]

                # Fetch Group Messages
                cursor.execute("""
                    SELECT gm.*, u.username as sender_name
                    FROM group_messages gm
                    JOIN users u ON gm.sender_id = u.user_id
                    WHERE gm.group_id = %s
                    ORDER BY gm.sent_at ASC
                """, (selected_group_id,))
                g_chat = cursor.fetchall()

                # Display Group Chat
                st.write("---")
                st.write(f"**Group: {selected_group_name}**")
                g_container = st.container(height=300)
                with g_container:
                    if not g_chat:
                        st.caption("No group messages yet.")
                    for g_msg in g_chat:
                        st.markdown(f"**@{g_msg['sender_name']}** `{format_to_ist(g_msg['sent_at'])}`:")
                        st.write(g_msg['message_text'])

                # Send Group Message
                with st.form(key="group_msg_form", clear_on_submit=True):
                    new_g_msg = st.text_input("Message group:")
                    submit_g_msg = st.form_submit_button("Send to Group")
                    if submit_g_msg and new_g_msg.strip():
                        cursor.execute(
                            "INSERT INTO group_messages (group_id, sender_id, message_text) VALUES (%s, %s, %s)",
                            (selected_group_id, current_user['user_id'], new_g_msg.strip())
                        )
                        conn.commit()
                        st.rerun()
            conn.close()
