from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from Script import script

@Client.on_callback_query(filters.regex("help"))
async def help_cb(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text(script.HELP_TXT, disable_web_page_preview=True)

@Client.on_callback_query(filters.regex("about"))
async def about_cb(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text(script.ABOUT_TXT, disable_web_page_preview=True)
