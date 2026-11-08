import sys, glob, importlib, logging, logging.config, pytz, asyncio
from pathlib import Path
import signal

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

from pyrogram import Client, idle
from pyrogram.errors import FloodWait 
from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from Script import script 
from datetime import date, datetime 
from aiohttp import web
from plugins import web_server

from TechVJ.bot import TechVJBot
from TechVJ.util.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)
async def start_bot_with_floodwait_retry(max_retries=5):
    """Start Telegram without blocking the HTTP health-check server."""
    for attempt in range(1, max_retries + 1):
        try:
            await TechVJBot.start()
            logging.info("Telegram bot connected successfully.")
            return
        except FloodWait as error:
            wait_seconds = max(1, int(getattr(error, "value", 30))) + 2
            logging.warning(
                "Telegram FloodWait during bot login. Waiting %s seconds before retry %s/%s.",
                wait_seconds, attempt, max_retries
            )
            if attempt >= max_retries:
                raise
            await asyncio.sleep(wait_seconds)


async def start():
    print('\n')
    print('Initializing MovieMasalas web service')

    # Start HTTP first so Koyeb health checks pass while Telegram applies FloodWait.
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, int(PORT)).start()
    logging.info("HTTP server listening on %s:%s", bind_address, PORT)

    print('Connecting Telegram bot')
    await start_bot_with_floodwait_retry()
    bot_info = await TechVJBot.get_me()
    await initialize_clients()
    
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
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    me = await TechVJBot.get_me()
    temp.BOT = TechVJBot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    
    await TechVJBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    
    await idle()

def handle_sigterm(signal, frame):
    logging.info("Received SIGTERM, shutting down gracefully...")
    sys.exit(0)  # Graceful exit on receiving SIGTERM

# Register the SIGTERM signal handler
signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == '__main__':
    try:
        # Get the event loop once and use it for all async tasks
        loop = asyncio.get_event_loop()

        # Make sure the loop is used correctly
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
