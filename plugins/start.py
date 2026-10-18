
import html
import humanize
from urllib.parse import quote_plus

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script
from info import URL, LOG_CHANNEL, SHORTLINK
from TechVJ.util.file_properties import (
    get_name, get_hash, get_media_file_size
)
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
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
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
    """Available forwarding source details and clickable links."""
    details = []

    chat = getattr(message, "forward_from_chat", None)
    message_id = getattr(message, "forward_from_message_id", None)
    user = getattr(message, "forward_from", None)
    sender_name = getattr(message, "forward_sender_name", None)
    forward_date = getattr(message, "forward_date", None)

    # Support for newer Telegram/Pyrogram forward metadata
    origin = getattr(message, "forward_origin", None)

    if chat:
        title = esc(getattr(chat, "title", "Forward channel"))
        username = getattr(chat, "username", None)
        source_link = None

        if username:
            if message_id:
                source_link = (
                    f"https://t.me/{username}/{message_id}"
                )
            else:
                source_link = f"https://t.me/{username}"

        elif message_id:
            # Private channel message link. The viewer must have access.
            chat_id = str(chat.id)
            if chat_id.startswith("-100"):
                internal_id = chat_id[4:]
                source_link = (
                    f"https://t.me/c/{internal_id}/{message_id}"
                )

        if source_link:
            details.append(
                f'<b>Forward channel:</b> '
                f'<a href="{esc(source_link)}">{title}</a>'
            )
        else:
            details.append(
                f"<b>Forward channel:</b> {title}"
            )
            details.append(
                "<i>Source link unavailable from Telegram metadata.</i>"
            )

        if message_id:
            details.append(
                f"<b>Original message ID:</b> {message_id}"
            )

    elif user:
        full_name = esc(" ".join(filter(None, [
            user.first_name, user.last_name
        ])) or "Unknown")

        details.append(f"<b>Forwarded user:</b> {full_name}")
        details.append(
            f"<b>Source user ID:</b> <code>{user.id}</code>"
        )

        if user.username:
            details.append(
                f'<b>Source profile:</b> '
                f'<a href="https://t.me/{user.username}">'
                f'@{esc(user.username)}</a>'
            )

    elif origin:
        # Metadata format used by some newer Pyrogram versions
        origin_chat = getattr(origin, "chat", None)
        origin_user = getattr(origin, "sender_user", None)
        origin_message_id = getattr(origin, "message_id", None)

        if origin_chat:
            title = esc(
                getattr(origin_chat, "title", "Forward channel")
            )
            username = getattr(origin_chat, "username", None)
            link = None

            if username:
                link = f"https://t.me/{username}"
                if origin_message_id:
                    link += f"/{origin_message_id}"
            elif origin_message_id:
                chat_id = str(origin_chat.id)
                if chat_id.startswith("-100"):
                    link = (
                        f"https://t.me/c/{chat_id[4:]}/"
                        f"{origin_message_id}"
                    )

            if link:
                details.append(
                    f'<b>Forward channel:</b> '
                    f'<a href="{esc(link)}">{title}</a>'
                )
            else:
                details.append(
                    f"<b>Forward channel:</b> {title}"
                )

        elif origin_user:
            name = esc(" ".join(filter(None, [
                origin_user.first_name,
                origin_user.last_name
            ])) or "Unknown")
            details.append(f"<b>Forwarded user:</b> {name}")
            details.append(
                f"<b>Source user ID:</b> "
                f"<code>{origin_user.id}</code>"
            )
        else:
            details.append(
                "<b>Forward source:</b> Telegram metadata available "
                "but no public source link"
            )

    elif sender_name:
        details.append(
            f"<b>Forward source:</b> {esc(sender_name)}"
        )
        details.append(
            "<i>Telegram has hidden the original source identity.</i>"
        )

    else:
        details.append(
            "<b>Forward source:</b> Direct upload or unavailable"
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
            print(f"New user log error: {e}")

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

    # Copy the file into LOG_CHANNEL
    try:
        log_msg = await client.send_cached_media(
            chat_id=LOG_CHANNEL,
            file_id=media.file_id
        )
    except Exception as e:
        print(f"File log error: {e}")
        await message.reply_text(
            "❌ File log channel mein copy nahi ho saki. "
            "Bot permissions aur LOG_CHANNEL setting check karein."
        )
        return

    # Generate URLs using existing project functions
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
        print(f"Link generation error: {e}")
        await message.reply_text(
            "❌ Link generate nahi hua. Server/shortlink settings check karein."
        )
        return

    # Log user, file, source and generated links
    caption = (
        f"•• Link generated for ID #{user.id}\n"
        f"•• Username: {esc(username)}\n"
        f"•• File name: {esc(original_name)}\n"
        f"•• File size: {esc(size)}\n"
        f"<b>📤 Source details</b>\n"
        f"{get_source_details(message)}\n\n"
    )

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
        print(f"Log details error: {e}")

    # Send generated links to the user
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
