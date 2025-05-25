from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import utils
import datetime
import os


# setup
async def setup(bot: commands.Bot):

    @bot.listen()
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        if message.guild == None:
            return
        
        if message.content.lower() in ['йоуу эщкере', 'йоу эщкерее']:
            length = datetime.timedelta(seconds=60)
            try:
                await message.author.timeout(length, reason='10.0 обман')
            except:
                return

            embed = discord.Embed(
                title='🤐 Таймаут', color=DEFAULT_C,
                description=f'{message.author.mention} успешно замьючен на **365 дн**'\
                    f' с причиной **10.0 обман**.'
            )

            await message.reply(embed=embed)
            