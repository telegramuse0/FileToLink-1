from pyrogram import Client, filters
from info import ADMINS
from database.users_chats_db import db

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client, message):
    if len(message.command) < 2:
        await message.reply("⚠️ Provide a user ID to ban.")
        return
    user_id = int(message.command[1])
    await db.ban_user(user_id)
    await message.reply(f"✅ User {user_id} has been banned.")

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_user(client, message):
    if len(message.command) < 2:
        await message.reply("⚠️ Provide a user ID to unban.")
        return
    user_id = int(message.command[1])
    await db.remove_ban(user_id)
    await message.reply(f"✅ User {user_id} has been unbanned.")
