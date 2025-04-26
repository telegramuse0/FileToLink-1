from pyrogram import Client, filters
from datetime import datetime

# Your log channel ID (make sure bot is admin there)
LOG_CHANNEL_ID = -1002408348111  # <<< replace with your log channel id

@Client.on_message(filters.private & (filters.photo | filters.video | filters.document))
async def handle_file(client, message):
    now = datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    if message.forward_from_chat:
        chat = message.forward_from_chat

        # Prepare user reply
        reply_text = f"Forwarded from {chat.type}: **{chat.title}**\n"
        
        if chat.username:
            link = f"https://t.me/{chat.username}"
            reply_text += f"Link: [Open Channel]({link})"
        else:
            reply_text += "This is a private channel or group. No public link available."

        await message.reply_text(reply_text, disable_web_page_preview=True)

        # Prepare log message
        log_text = (
            f"**New Forwarded File**\n\n"
            f"**User:** {user_mention}\n"
            f"**User ID:** `{message.from_user.id}`\n"
            f"**Time:** `{time}`\n"
            f"**Forwarded From:** {chat.title}\n"
        )
        if chat.username:
            log_text += f"**Link:** [Open Channel](https://t.me/{chat.username})\n"
        else:
            log_text += "**Link:** Private Channel/Group\n"
        
    else:
        # User sent a file directly
        reply_text = "This file was sent directly (not forwarded from any channel or group)."
        await message.reply_text(reply_text)

        log_text = (
            f"**New Direct File**\n\n"
            f"**User:** {user_mention}\n"
            f"**User ID:** `{message.from_user.id}`\n"
            f"**Time:** `{time}`\n"
            "**Forwarded From:** Not forwarded.\n"
        )

    # Send file to log channel WITH caption
    await message.copy(LOG_CHANNEL_ID, caption=log_text, disable_notification=True)
