# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

# Clone Code Credit : YT - @Tech_VJ / TG - @VJ_Bots / GitHub - @VJBots

import sys, glob, importlib, logging, logging.config, pytz, asyncio
from pathlib import Path

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

from pyrogram import Client, idle 
from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from Script import script 
from datetime import date, datetime 
from aiohttp import web
from plugins import web_server

from TechVJ.bot import TechVJBot
from TechVJ.util.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)
TechVJBot.start()
loop = asyncio.get_event_loop()

from pyrogram import Client, filters
from pyrogram.types import Message
from ban_list import ban_user, is_banned

app = Client("FileToLinkBot")  # Make sure this line is at the top of your bot.py

# List of admin user IDs
ADMIN_IDS = [1708370518]  # Replace with the actual Telegram user IDs of bot admins

@app.on_message(filters.private | filters.group | filters.channel)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id  # The chat ID from where the message is sent
    chat_type = message.chat.type  # 'private', 'group', 'supergroup', 'channel'

    # Check if the user is banned
    if is_banned(user_id):
        await message.reply_text("You are banned.")
        return

    # Determine where the message came from
    if chat_type == "private":
        chat_origin = "Private Chat"
    elif chat_type == "group":
        chat_origin = "Group Chat"
    elif chat_type == "supergroup":
        chat_origin = "Supergroup Chat"
    elif chat_type == "channel":
        chat_origin = "Channel"
    else:
        chat_origin = "Unknown"

    # Check what kind of file is sent
    if message.document:
        file_type = "document"
        file_name = message.document.file_name
        file_size = message.document.file_size
    elif message.video:
        file_type = "video"
        file_name = message.video.file_name
        file_size = message.video.file_size
    elif message.audio:
        file_type = "audio"
        file_name = message.audio.file_name
        file_size = message.audio.file_size
    elif message.photo:
        file_type = "photo"
        file_name = "Photo (no name)"
        file_size = message.photo.file_size
    else:
        await message.reply_text("Unsupported file type.")
        return

    # Respond with file details
    await message.reply_text(
        f"Received a {file_type} from a {chat_origin}:\n"
        f"File Name: {file_name}\n"
        f"Size: {file_size / (1024 * 1024):.2f} MB\n"
        f"Chat ID: {chat_id}"
    )
