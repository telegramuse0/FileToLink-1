from urllib.parse import quote_plus
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from info import LOG_CHANNEL, URL, SHORTLINK
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size

try:
    from utils import get_shortlink
except ImportError:
    get_shortlink = None


def humanbytes(size):
    size = float(size or 0)
    if size <= 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024


@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def file_receive(client: Client, message: Message):
    # 1. User & Media Info
    user_id = message.from_user.id if message.from_user else 0
    username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else (message.from_user.first_name if message.from_user else "Unknown")

    media = getattr(message, message.media.value, None)
    fileid = media.file_id if media else ""

    # 2. Forward Source Details
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

    # 3. Log channel me send karna
    try:
        log_msg = await message.forward(chat_id=LOG_CHANNEL)
    except Exception:
        log_msg = await client.send_cached_media(chat_id=LOG_CHANNEL, file_id=fileid)

    # Keep the exact filename supplied with the original incoming Telegram file.
    # A copied/forwarded LOG_CHANNEL message can expose incomplete or altered metadata.
    fname = getattr(media, "file_name", None) or get_name(log_msg) or "Telegram Media"
    fsize = humanbytes(get_media_file_size(message))

    # 4. Clean URL formatting
    base_url = URL.strip()
    if base_url and not base_url.endswith("/"):
        base_url += "/"

    file_hash = get_hash(log_msg)
    stream = f"{base_url}watch/{log_msg.id}/{quote_plus(fname)}?hash={file_hash}"
    download = f"{base_url}{log_msg.id}/{quote_plus(fname)}?hash={file_hash}&download=1"

    # 5. Shortlink agar enabled ho
    if SHORTLINK and get_shortlink:
        stream = await get_shortlink(stream)
        download = await get_shortlink(download)

    # 6. Inline buttons
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Fast Download", url=download),
            InlineKeyboardButton("🖥️ Watch Online", url=stream)
        ]
    ])

    # 7. Log channel message
    log_caption = f"""<b><u>log channel</u></b>
<i>{fname}</i>

•• <b>Link generated for ID:</b> #{user_id}
•• <b>Username:</b> {username}
•• <b>File name:</b> {fname}
•• <b>File size:</b> {fsize}
🗳️ <b>Source details</b>
<b>Forward channel:</b> {fwd_channel}
<b>Original message ID:</b> {orig_msg_id}"""

    await log_msg.reply_text(
        text=log_caption,
        reply_markup=markup,
        disable_web_page_preview=True
    )

    # 8. User reply
    user_reply = f"""<i><u>Your Link Generated !</u></i>

<b>🚩 File NAME :</b> <i>{fname}</i>
<b>📦 FILE SIZE :</b> <i>{fsize}</i>

<b>📥 DOWNLOAD :</b> {download}
<b>🖥️ STREAM :</b> {stream}

<b>⚡ Note : LINK EXPIRES IN 24 HRS</b>"""

    await message.reply_text(
        text=user_reply,
        reply_markup=markup,
        disable_web_page_preview=True
    )
