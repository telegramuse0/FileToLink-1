import os
import sys
from pyrogram import Client, filters
from info import ADMINS

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart_handler(client, message):
    await message.reply("♻️ Restarting bot...")
    os.execv(sys.executable, ['python'] + sys.argv)
