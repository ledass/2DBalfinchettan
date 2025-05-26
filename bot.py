import logging, tgcrypto
import logging.config
import asyncio
from datetime import datetime, timedelta
import os
import sys

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media, Media2, choose_mediaDB, db as clientDB
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, SECONDDB_URI, DATABASE_URI
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types

# prevent asyncio logging spam
logging.getLogger("asyncio").setLevel(logging.CRITICAL - 1)

# peer ID invalid fix
from pyrogram import utils as pyroutils
pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

from plugins.webcode import bot_run
from os import environ
from aiohttp import web as webserver

from sample_info import tempDict

PORT_CODE = environ.get("PORT", "8080")


class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        await Media2.ensure_indexes()

        # Choose the right DB by checking free space
        stats = await clientDB.command('dbStats')
        free_dbSize = round(512 - ((stats['dataSize'] / (1024 * 1024)) + (stats['indexSize'] / (1024 * 1024))), 2)
        if SECONDDB_URI and free_dbSize < 350:
            tempDict["indexDB"] = SECONDDB_URI
            logging.info(f"Since Primary DB has only {free_dbSize} MB left, Secondary DB will be used.")
        elif SECONDDB_URI is None:
            logging.error("Missing second DB URI! Add SECONDDB_URI now. Exiting...")
            exit()
        else:
            logging.info(f"Primary DB has enough space ({free_dbSize} MB), continuing with it.")

        await choose_mediaDB()

        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} (Pyrogram v{__version__}, Layer {layer}) started on @{me.username}.")
        await self.send_message(chat_id=LOG_CHANNEL, text="Bot Started ✓\nKuttu Bot2\n2db Features...")
        print("Og Eva Re-editeD 2 db Using Feature⚡")

        client = webserver.AppRunner(await bot_run())
        await client.setup()
        bind_address = "0.0.0.0"
        await webserver.TCPSite(client, bind_address, PORT_CODE).start()

        # Schedule auto-restart every 24 hours
        asyncio.create_task(self.schedule_restart())

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

    
# 24 hrs restart fn()
    async def restart(self):
        logging.info("Restarting bot process...")
        await self.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    async def schedule_restart(self, hours: int = 24):
        await asyncio.sleep(hours * 60 * 60)  # Wait for 24 hours
        await self.send_message(chat_id=LOG_CHANNEL, text="Auto Restarting the 2 DB Featrure Bot (24 hrs refresh)...")
        await self.restart()
#restarting fn() end;

    
    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                yield message
                current += 1


app = Bot()
app.run()
