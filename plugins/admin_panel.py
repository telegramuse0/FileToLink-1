# plugins/admin_panel.py

from pyrogram import filters
from TechVJ.bot import TechVJBot
from Script import script

ADMINS = [1708370518]  # Replace with your real Telegram user ID(s)
banned_users = set()

def is_admin(func):
    async def wrapper(client, message):
        if message.from_user.id not in ADMINS:
            await message.reply(script.UNAUTHORIZED_MSG)
            return
        return await func(client, message)
    return wrapper

@TechVJBot.on_message(filters.command("admin") & filters.private)
@is_admin
async def admin_panel(client, message):
    await message.reply(script.ADMIN_MENU)

@TechVJBot.on_message(filters.command("ban") & filters.private)
@is_admin
async def ban_user(client, message):
    try:
        user_id = int(message.text.split()[1])
        banned_users.add(user_id)
        await message.reply(script.BANNED_SUCCESS.format(user_id), parse_mode="markdown")
    except:
        await message.reply("Usage: /ban [user_id]")

@TechVJBot.on_message(filters.command("unban") & filters.private)
@is_admin
async def unban_user(client, message):
    try:
        user_id = int(message.text.split()[1])
        banned_users.discard(user_id)
        await message.reply(script.UNBANNED_SUCCESS.format(user_id), parse_mode="markdown")
    except:
        await message.reply("Usage: /unban [user_id]")

# Global check for banned users (can also be integrated per-handler)
@TechVJBot.on_message(filters.private)
async def check_ban(client, message):
    if message.from_user.id in banned_users and not message.text.startswith("/admin"):
        await message.reply(script.BANNED_MSG)
