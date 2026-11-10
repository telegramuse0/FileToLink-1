import humanize
from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import URL, SHORTLINK, LOG_CHANNEL
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes
from utils import get_shortlink

@Client.on_message(filters.private & (filters.document | filters.video))
async def handle_upload(client, message):
    file = getattr(message, message.media.value)
    user_id = message.from_user.id
    username = message.from_user.mention
    fileid = file.file_id

    # Detect forward source
    if message.forward_from:
        source = f"User: {message.forward_from.first_name} (ID: {message.forward_from.id})"
    elif message.forward_from_chat:
        source = f"Chat: {message.forward_from_chat.title} (ID: {message.forward_from_chat.id})"
    elif message.forward_sender_name:
        source = f"Anonymous: {message.forward_sender_name}"
    else:
        source = "Direct upload"

    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=fileid,
        caption=f"File from {username} (ID: {user_id})\nForward Source: {source}"
    )

    fname = get_name(log_msg)
    stream = f"{URL}watch/{log_msg.id}/{quote_plus(fname)}?hash={get_hash(log_msg)}"
    download = f"{URL}{log_msg.id}/{quote_plus(fname)}?hash={get_hash(log_msg)}"

    if SHORTLINK:
        stream = await get_shortlink(stream)
        download = await get_shortlink(download)

    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🖥 Stream", url=stream),
        InlineKeyboardButton("📥 Download", url=download)
    ]])

    reply_text = f"""<i><u>𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 !</u></i>

<b>📂 Fɪʟᴇ ɴᴀᴍᴇ :</b> <i>{fname}</i>
<b>📦 Fɪʟᴇ ꜱɪᴢᴇ :</b> <i>{humanbytes(get_media_file_size(message))}</i>
<b>📥 Dᴏᴡɴʟᴏᴀᴅ :</b> <i>{download}</i>
<b>🖥 Sᴛʀᴇᴀᴍ :</b> <i>{stream}</i>

<b>🚸 Nᴏᴛᴇ : LINK EXPIRES IN 24 HRS</b>
"""

    await message.reply_text(reply_text, reply_markup=markup, disable_web_page_preview=True)
