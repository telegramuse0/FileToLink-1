from pyrogram import Client, filters
from Script import script

@Client.on_message(filters.command("about"))
async def about_handler(client, message):
    await message.reply_text(script.ABOUT_TXT, disable_web_page_preview=True)
