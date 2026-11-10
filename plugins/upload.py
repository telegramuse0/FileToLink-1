import os
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from info import LOG_CHANNEL, URL, SHORTLINK
from utils import get_name, get_hash, humanbytes, get_media_file_size
# Agar aapke project me shortlink ka helper alag file me hai:
try:
    from utils import get_shortlink
except ImportError:
    get_shortlink = None

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def file_receive(client: Client, message: Message):
    # 1. User aur File details nikalna
    user_id = message.from_user.id if message.from_user else 0
    username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else (message.from_user.first_name if message.from_user else "Unknown")
    fileid = getattr(message, message.media.value).file_id

    # 2. Forward Source details nikalna
    fwd_channel = "Direct upload"
    orig_msg_id = message.id
    if message.forward_from_chat:
        fwd_channel = message.forward_from_chat.title or str(message.forward_from_chat.id)
        orig_msg_id = message.forward_from_message_id or message.id
    elif message.forward_from:
        fwd_channel = f"User: {message.forward_from.first_name}"
        orig_msg_id = message.forward_from_message_id or message.id
    elif message.forward_sender_name:
        fwd_channel = f"Anonymous: {message.forward_sender_name}"

    # 3. File ko Log Channel me forward karna (1st Image format)
    try:
        log_msg = await message.forward(chat_id=LOG_CHANNEL)
    except Exception:
        # Fallback agar privacy restrictions ki wajah se forward block ho
        log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=fileid)

    fname = get_name(log_msg)
    fsize = humanbytes(get_media_file_size(message))

    # 4. URL Fix: Ensure trailing slash exists
    base_url = URL.strip()
    if base_url and not base_url.endswith("/"):
        base_url += "/"

    file_hash = get_hash(log_msg)
    stream = f"{base_url}watch/{log_msg.id}/{quote_plus(fname)}?hash={file_hash}"
    download = f"{base_url}{log_msg.id}/{quote_plus(fname)}?hash={file_hash}"

    # Shortlink check
    if SHORTLINK and get_shortlink:
        stream = await get_shortlink(stream)
        download = await get_shortlink(download)

    # 5. Buttons (Fast Download aur Watch Online)
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Fast Download", url=download),
            InlineKeyboardButton("🖥️ Watch Online", url=stream)
        ]
    ])

    # 6. Log Channel Caption (1st image jaisa exact format)
    log_caption = (
        f"<b><u>log channel</u></b>\n"
        f"<i>{fname}</i>\n\n"
        f"•• <b>Link generated for ID</b> #{user_id}\n"
        f"•• <b>Username:</b> {username}\n"
        f"•• <b>File name:</b> {fname}\n"
        
