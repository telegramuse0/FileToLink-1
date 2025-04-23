from pyrogram import Client, filters
from info import ADMINS
from database.users_chats_db import db

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_handler(client, message):
    total_users = await db.total_users_count()
    await message.reply_text(f"📊 Total users: <b>{total_users}</b>")
