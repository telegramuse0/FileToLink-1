from pyrogram import Client, filters
from info import ADMINS
from database.users_chats_db import db

@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def users_list(client, message):
    users = await db.get_all_users()
    text = f"👥 Total users: {len(users)}\n\n"
    for u in users[:50]:  # Limit output
        text += f"• {u['id']}\n"
    await message.reply_text(text)
