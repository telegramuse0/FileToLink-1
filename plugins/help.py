from pyrogram import Client, filters
from Script import script

@Client.on_message(filters.command("help"))
async def help_handler(client, message):
    await message.reply_text(script.HELP_TXT, disable_web_page_preview=True)
