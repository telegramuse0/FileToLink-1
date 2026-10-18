
import random
import humanize
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import URL, LOG_CHANNEL, SHORTLINK
from urllib.parse import quote_plus
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp, get_shortlink

CHANNEL = "shoppingdeals_Discounts"
CHANNEL_URL = "https://t.me/shoppingdeals_Discounts"


async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(
            chat_id="@" + CHANNEL,
            user_id=user_id
        )
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return False


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton(
            "✅ I've Joined — Check Again",
            callback_data="check_subscription"
        )]
    ])


async def subscription_required(client, message):
    user = message.from_user
    if not user:
        return False

    if await is_subscribed(client, user.id):
        return True

    await message.reply_text(
        "🔒 <b>Join Required!</b>\n\n"
        "Bot use karne se pehle hamare channel ko join karein.\n\n"
        "1. Join Channel button dabayein.\n"
        "2. Channel join karein.\n"
        "3. I've Joined — Check Again dabayein.",
        reply_markup=join_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )
    return False


@Client.on_callback_query(filters.regex("^check_subscription$"))
async def check_subscription(client, query):
    if await is_subscribed(client, query.from_user.id):
        await query.answer("✅ Subscription verified!", show_alert=True)
        await query.message.edit_text(
            "🎉 <b>Subscription Verified!</b>\n\n"
            "Ab aap bot use kar sakte hain.\n"
            "File bhejein aur apna link generate karein.",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await query.answer(
            "❌ Pehle channel join karein, phir dobara check karein.",
            show_alert=True
        )


@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not message.from_user:
        return

    if not await subscription_required(client, message):
        return

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(
            message.from_user.id,
            message.from_user.first_name
        )
        await client.send_message(
            LOG_CHANNEL,
            script.LOG_TEXT_P.format(
                message.from_user.id,
                message.from_user.mention
            )
        )

    await client.send_message(
        chat_id=message.from_user.id,
        text=script.START_TXT.format(
            message.from_user.mention,
            temp.U_NAME,
            temp.B_NAME
        ),
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_message(filters.private & (filters.document | filters.video))
async def stream_start(client, message):
    if not await subscription_required(client, message):
        return

    file = getattr(message, message.media.value)
    filename = file.file_name
    filesize = humanize.naturalsize(file.file_size)
    fileid = file.file_id
    user_id = message.from_user.id
    username = message.from_user.mention

    log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=fileid
    )

    fileName = get_name(log_msg)

    if SHORTLINK is False:
        stream = (
            f"{URL}watch/{log_msg.id}/"
            f"{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        )
        download = (
            f"{URL}{log_msg.id}/"
            f"{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        )
    else:
        stream = await get_shortlink(
            f"{URL}watch/{log_msg.id}/"
            f"{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        )
        download = await get_shortlink(
            f"{URL}{log_msg.id}/"
            f"{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        )

    await log_msg.reply_text(
        text=(
            f"•• Link generated for ID #{user_id}\n"
            f"•• Username: {username}\n"
            f"•• File name: {fileName}"
        ),
        quote=True,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Fast Download", url=download),
            InlineKeyboardButton("🖥️ Watch Online", url=stream)
        ]])
    )

    await message.reply_text(
        text=(
            "<b>✅ Your Link Is Generated!</b>\n\n"
            f"<b>📂 File:</b> {get_name(log_msg)}\n"
            f"<b>📦 Size:</b> "
            f"{humanbytes(get_media_file_size(message))}\n\n"
            "<b>Choose an option below:</b>"
        ),
        quote=True,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🖥 Stream", url=stream),
            InlineKeyboardButton("📥 Download", url=download)
        ]])
    )
