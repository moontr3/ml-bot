from copy import deepcopy
import os
import random
import time
from discord.ext import commands, tasks
import discord
from log import *
from typing import *
from config import *
import api
import utils
from bot import MLBot

index = 0

# setup
async def setup(bot: MLBot):

    @tasks.loop(seconds=15)
    async def presence_set_loop():
        global index

        # getting text
        stats = bot.mg.get_all_info()

        if index == 0:
            guild = bot.get_guild(GUILD_ID)

            if not guild:
                index += 1
            else:
                emoji = "👥"
                text = f'Обслуживает пидорасов: {utils.unicode_cool_numbers(guild.member_count)}'

        if index == 1:
            guild = bot.get_guild(GUILD_ID)

            if not guild:
                index += 1
            else:
                members = len(guild.get_role(VERIFY_ROLE).members)
                emoji = "🧠"
                text = f'Верифицировано: {utils.unicode_cool_numbers(members)}'

        if index == 2:
            emoji = "🤖"
            text = f'Пользователей бота: {utils.unicode_cool_numbers(len(bot.mg.users))}'

        if index == 3:
            emoji = "✨"
            text = f'Всего опыта: {utils.unicode_cool_numbers(stats["xp"])} 𝗫𝗣'

        if index == 4:
            emoji = "🇶"
            text = f'cобрано: {utils.unicode_cool_numbers(stats["q"])} 𝗤'

        if index == 5:
            emoji = "🔡"
            text = f'Собрано шрифтов: {utils.unicode_cool_numbers(stats["fonts"])}'

        if index == 6:
            emoji = "🎨"
            text = f'Собрано скинов: {utils.unicode_cool_numbers(stats["skins"])}'

        index += 1
        if index > 6:
            index = 0

        # setting presence
        try:
            await bot.change_presence(
                activity=discord.CustomActivity(
                    name=f'{emoji} {text}'
                ),
                status=discord.Status.idle
            )
        except Exception as e:
            log(f'Unable to set presence: {e}', level=ERROR)


    @bot.listen()
    async def on_ready():
        if not presence_set_loop.is_running():
            presence_set_loop.start()