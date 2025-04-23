# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys, glob, importlib, logging, logging.config, pytz, asyncio, os
from pathlib import Path
from pyrogram import idle
from datetime import date, datetime
from aiohttp import web

from TechVJ.bot import TechVJBot
from TechVJ.bot.clients import initialize_clients
from TechVJ.util.keepalive import ping_server  # Not used in Koyeb
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from plugins import web_server

# Logging Setup
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

# Find all plugins
ppath = "plugins/*.py"
files = glob.glob(ppath)
TechVJBot.start()
loop = asyncio.get_event_loop()

async def start():
    print("\nInitializing Your Bot...\n")
    bot_info = await TechVJBot.get_me()

    await initialize_clients()

    # Plugin loader
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("Tech VJ Imported => " + plugin_name)

    # Store bot info for global use
    temp.BOT = TechVJBot
    temp.ME = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name

    # Restart log message
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    today = date.today()
    time = now.strftime("%H:%M:%S %p")
    await TechVJBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))

    # Start web server (for Koyeb)
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", int(os.environ.get("PORT", 8080))).start()

    print("Bot is running. Waiting for events...")
    await idle()  # Prevent app from stopping

if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
