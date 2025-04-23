from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ADMINS

@Client.on_message(filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users", callback_data="users")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban")],
    ])
    await message.reply("🔧 Admin Panel:", reply_markup=keyboard)
