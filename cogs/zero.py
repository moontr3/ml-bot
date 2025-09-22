import random
from discord.ext import commands, tasks
import discord
from log import *
from typing import *
from config import *
import utils
from bot import MLBot
import datetime


sent = False
# setup
async def setup(bot: MLBot):

    # task loop
    @tasks.loop(seconds=2)
    async def zero_loop():
        global sent
        cur_time = datetime.datetime.now()

        if cur_time.minute == 0 and cur_time.hour == 0 and cur_time.second > 10:
            if not sent:
                sent = True
                await bot.get_guild(GUILD_ID).get_channel(ZERO_ID).send(ZERO_TEXT)
                log(f'Sent {ZERO_TEXT}')
        elif sent:
            sent = False


    @bot.listen()
    async def on_ready():
        if not zero_loop.is_running():
            zero_loop.start()