from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from Script import script  # make sure script has HELP_TXT, ABOUT_TXT

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    if query.data == "help":
        await query.message.edit_text(
            text=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="start"),
                 InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif query.data == "about":
        await query.message.edit_text(
            text=script.ABOUT_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="start"),
                 InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif query.data == "start":
        await query.message.edit_text(
            text=script.START_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Help", callback_data="help"),
                 InlineKeyboardButton("About", callback_data="about")],
                [InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif query.data == "close":
        await query.message.delete()
