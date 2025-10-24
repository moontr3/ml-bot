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


# setup
async def setup(bot: MLBot):

    # gaining xp
    @bot.listen()
    async def on_message_edit(before: discord.Message, after: discord.Message):
        # checking if bot
        if after.author.id != BUMP_BOT_ID:
            return

        if not after.guild or after.guild.id != GUILD_ID:
            return
        
        if len(after.embeds) == 0:
            return
        
        embed = after.embeds[0]

        if not embed.title.endswith(' | Объявление рассылается'):
            return
        
        if not after.interaction_metadata:
            return
        
        user = after.interaction_metadata.user
        log(f'Detected bump from {user.id}')

        # sending success
        bumptime = deepcopy(bot.mg.last_bump)
        xp = bot.mg.bump(user.id)

        view = to_view([
            f'### 🤜 Спасибо за бамп, <@{user.id}>!',
            f'За него вы получили **{xp} XP**.',
            SEP(),
            f'-# Прошлый бамп был <t:{int(bumptime)}:R>.'
        ])
        await after.channel.send(view=view)

        
    @tasks.loop(seconds=1)
    async def ping_check_loop():
        if bot.mg.bump_ping_at > time.time():
            return
        bump_bot = bot.get_guild(GUILD_ID).get_member(BUMP_BOT_ID)
        if not bump_bot or bump_bot.status == discord.Status.offline:
            return
        
        bot.mg.bump_timeout()

        channel = bot.get_channel(BUMP_CHANNEL)

        if channel is None:
            log(f'Channel {BUMP_CHANNEL} for bumping not found', level=ERROR)
            return
        
        await channel.send(f'<@&{BUMP_PING_ROLE}> ・ </bump:1135998835311775768>')


    @bot.listen()
    async def on_ready():
        if not ping_check_loop.is_running():
            ping_check_loop.start()