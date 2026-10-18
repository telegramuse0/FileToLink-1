
import html
import humanize
from urllib.parse import quote_plus

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from info import URL, LOG_CHANNEL, SHORTLINK
from TechVJ.util.file_properties import get_name, get_hash, get_media_file_size
from TechVJ.util.human_readable import humanbytes
from database.users_chats_db import db
from utils import temp, get_shortlink


# Force subscribe channel
CHANNEL = "shoppingdeals_Discounts"
CHANNEL_URL = "https://t.me/shoppingdeals_Discounts"


def esc(value):
    return html.escape(str(value or ""), quote=True)


async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(
            "@" + CHANNEL, user_id
        )
        status = getattr(member.status, "value", member.status)
        return str(status).lower() not in (
            "left", "kicked", "banned"
        )
    except Exception:
        return False


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📢 Join Channel", url=CHANNEL_URL
        )],
        [InlineKeyboardButton(
            "✅ I've Joined — Check Again",
            callback_data="check_subscription"
        )]
    ])


async def subscription_required(client, message):
    if not message.from_user:
        return False

    if await is_subscribed(client, message.from_user.id):
        return True

    await message.reply_text(
        "🔒 <b>Join Required!</b>\n\n"
        "Bot use karne se pehle channel join karein.",
        reply_markup=join_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )
    return False


@Client.on_callback_query(
    filters.regex("^check_subscription$")
)
async def check_subscription(client, query):
    if await is_subscribed(client, query.from_user.id):
        await query.answer(
            "✅ Subscription verified!", show_alert=True
        )
        try:
            await query.message.edit_text(
                "🎉 <b>Subscription verified!</b>\n"
                "Ab bot par file bhej sakte hain.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass
    else:
        await query.answer(
            "❌ Pehle channel join karein.",
            show_alert=True
        )


def get_source_details(message):
    """Telegram message se available forwarding metadata."""
    details = []

    chat = getattr(message, "forward_from_chat", None)
    user = getattr(message, "forward_from", None)
    message_id = getattr(message, "forward_from_message_id", None)
    sender_name = getattr(message, "forward_sender_name", None)
    forward_date = getattr(message, "forward_date", None)

    # Newer Pyrogram versions may expose forward_origin
    origin = getattr(message, "forward_origin", None)

    if chat:
        details.append(
            f"<b>Forward channel:</b> {esc(chat.title)}"
        )

        if getattr(chat, "username", None):
            source_url = f"https://t.me/{chat.username}"
            details.append(
                f'<b>Channel link:</b> <a href="{source_url}">'
                f'Open channel</a>'
            )

            if message_id:
                post_url = f"{source_url}/{message_id}"
                details.append(
                    f'<b>Original post:</b> <a href="{post_url}">'
                    f'Open post</a>'
                )
        elif message_id:
            details.append(
                f"<b>Original message ID:</b> {message_id}"
            )

    elif user:
        full_name = " ".join(filter(None, [
            user.first_name, user.last_name
        ]))
        details.append(
            f"<b>Forwarded user:</b> {esc(full_name)}"
        )
        details.append(
            f"<b>Source user ID:</b> <code>{user.id}</code>"
        )
        if user.username:
            details.append(
                f"<b>Source username:</b> @{esc(user.username)}"
            )

    elif sender_name:
        details.append(
            f"<b>Forward source name:</b> {esc(sender_name)}"
        )
        details.append(
            "<i>Telegram ne source ki ID hide ki hai.</i>"
        )

    elif origin:
        # ForwardOrigin is available in some Pyrogram versions.
        origin_type = getattr(origin, "type", None)
        details.append(
            f"<b>Forward origin type:</b> {esc(origin_type or 'Available')}"
        )
        origin_chat = getattr(origin, "chat", None)
        origin_user = getattr(origin, "sender_user", None)

        if origin_chat:
            details.append(
                f"<b>Origin chat:</b> {esc(getattr(origin_chat, 'title', 'Channel'))}"
            )
            origin_username = getattr(origin_chat, "username", None)
            origin_msg_id = getattr(origin, "message_id", None)
            if origin_username:
                details.append(
                    f"<b>Origin channel:</b> https://t.me/{esc(origin_username)}"
                )
                if origin_msg_id:
                    details.append(
                        f"<b>Origin post:</b> "
                        f"https://t.me/{esc(origin_username)}/{origin_msg_id}"
                    )

        if origin_user:
            details.append(
                f"<b>Origin user ID:</b> {origin_user.id}"
            )

    else:
        details.append(
            "Direct upload / Telegram source metadata unavailable"
        )

    if forward_date:
        details.append(
            f"<b>Forward date:</b> {esc(forward_date)}"
        )

    return "\n".join(details)


@Client.on_message(
    filters.command("start") & filters.incoming
)
async def start(client, message):
    user = message.from_user
    if not user:
        return

    if not await subscription_required(client, message):
        return

    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
        try:
            await client.send_message(
                LOG_CHANNEL,
                script.LOG_TEXT_P.format(user.id, user.mention)
            )
        except Exception as e:
            print(f"New-user log error: {e}")

    await client.send_message(
        user.id,
        script.START_TXT.format(
            user.mention, temp.U_NAME, temp.B_NAME
        ),
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_message(
    filters.private
    & (filters.document | filters.video | filters.audio)
)
async def stream_start(client, message):
    user = message.from_user
    if not user:
        return

    if not await subscription_required(client, message):
        return

    media = getattr(message, message.media.value, None)
    if not media:
        await message.reply_text("❌ File details nahi mile.")
        return

    user_name = " ".join(filter(None, [
        user.first_name, user.last_name
    ])) or "Unknown"
    username = f"@{user.username}" if user.username else "Not set"

    original_name = getattr(media, "file_name", None) or "Unknown"
    size = humanize.naturalsize(media.file_size)

    # File ko LOG_CHANNEL mein copy karein
    try:
        log_msg = await client.send_cached_media(
            chat_id=LOG_CHANNEL,
            file_id=media.file_id
        )
    except Exception as e:
        print(f"File copy to LOG_CHANNEL failed: {e}")
        await message.reply_text(
            "❌ File log channel mein copy nahi ho saki. "
            "Bot permissions aur LOG_CHANNEL setting check karein."
        )
        return

    # URLs existing project logic se banayein
    try:
        file_name = get_name(log_msg)

        stream_url = (
            f"{URL}watch/{log_msg.id}/"
            f"{quote_plus(file_name)}?hash={get_hash(log_msg)}"
        )
        download_url = (
            f"{URL}{log_msg.id}/"
            f"{quote_plus(file_name)}?hash={get_hash(log_msg)}"
        )

        if SHORTLINK:
            stream_url = await get_shortlink(stream_url)
            download_url = await get_shortlink(download_url)

    except Exception as e:
        print(f"Link generation failed: {e}")
        await message.reply_text(
            "❌ Link generate nahi hua. Server/shortlink settings check karein."
        )
        return

    # Screenshot jaisa caption + extra source logging
    caption = (
        f"•• Link generated for ID #{user.id}\n"
        f"•• Username: {esc(username)}\n"
        f"•• Name: {esc(user_name)}\n"
        f"•• File name: {esc(original_name)}\n"
        f"•• File size: {esc(size)}\n"
        f"•• File type: {esc(message.media.value)}\n"
        f"•• Upload time: {esc(message.date)}\n\n"
        f"<b>📤 Source details</b>\n"
        f"{get_source_details(message)}\n\n"
        f"<b>🚀 Fast Download:</b>\n{esc(download_url)}\n\n"
        f"<b>🖥 Watch Online:</b>\n{esc(stream_url)}"
    )

    # Log details ko copied file ke neeche post karein
    try:
        await log_msg.reply_text(
            caption,
            quote=True,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🚀 Fast Download", url=download_url
                ),
                InlineKeyboardButton(
                    "🖥 Watch Online", url=stream_url
                )
            ]])
        )
    except Exception as e:
        print(f"Log details post failed: {e}")

    # User ko links
    await message.reply_text(
        text=(
            "<b>✅ Your Link Is Generated!</b>\n\n"
            f"<b>📂 File:</b> {esc(file_name)}\n"
            f"<b>📦 Size:</b> "
            f"{esc(humanbytes(get_media_file_size(message)))}\n\n"
            "Neeche option select karein:"
        ),
        quote=True,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🖥 Stream", url=stream_url
            ),
            InlineKeyboardButton(
                "📥 Download", url=download_url
            )
        ]])
    )
