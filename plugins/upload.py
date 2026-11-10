import html
import logging
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
    username = message.from_user.first_name or "Unknown"
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

    # Store the media in LOG_CHANNEL. This message ID is used by stream links.
    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=fileid,
        caption=f"File uploaded by {html.escape(username)} (ID: {user_id})\nSource: {html.escape(source)}"
    )

    fname = get_name(log_msg) or getattr(file, "file_name", None) or "Unknown file"
    file_size = get_media_file_size(log_msg) or get_media_file_size(message)
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

<b>📂 Fɪʟᴇ ɴᴀᴍᴇ :</b> <i>{html.escape(fname)}</i>
<b>📦 Fɪʟᴇ ꜱɪᴢᴇ :</b> <i>{humanbytes(file_size)}</i>
<b>📥 Dᴏᴡɴʟᴏᴀᴅ :</b> <i>{html.escape(download)}</i>
<b>🖥 Sᴛʀᴇᴀᴍ :</b> <i>{html.escape(stream)}</i>

<b>🚸 Nᴏᴛᴇ : LINK EXPIRES IN 24 HRS</b>
"""

    await message.reply_text(reply_text, reply_markup=markup, disable_web_page_preview=True)

    # Send a separate metadata message so the original media message ID stays unchanged.
    log_details = (
        "<b>📋 UPLOAD DETAILS</b>\n"
        f"<b>📂 File:</b> {html.escape(fname)}\n"
        f"<b>📦 Size:</b> {html.escape(humanbytes(file_size))}\n"
        f"<b>👤 Uploader:</b> {html.escape(username)} (<code>{user_id}</code>)\n"
        f"<b>🔁 Source:</b> {html.escape(source)}\n"
        f"<b>🆔 Log Message ID:</b> <code>{log_msg.id}</code>\n"
        f'<b>📥 Download:</b> <a href="{html.escape(download, quote=True)}">Open download link</a>\n'
        f'<b>🖥 Stream:</b> <a href="{html.escape(stream, quote=True)}">Open stream link</a>'
    )
    try:
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=log_details,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_to_message_id=log_msg.id
        )
    except Exception:
        logging.exception("Failed to send upload details to LOG_CHANNEL for message %s", log_msg.id)
