from discord.ext import commands
from discord import Webhook
import aiohttp
import discord
from log import *
from typing import *
from config import *
from bot import MLBot


# setup
async def setup(bot: MLBot):

    async def update_rank(member):
        guild = bot.get_guild(GUILD_ID)
        level = bot.mg.get_user(member.id).xp.level
        roles = []
        rank_roles = [guild.get_role(i) for i in LEVELS]

        for i in range(min(len(LEVELS), level)):
            roles.append(rank_roles[i])
        cur_roles = [i for i in member.roles if i.id in LEVELS]

        for i in cur_roles:
            if i not in roles:
                await member.remove_roles(i)

        for i in roles:
            if i not in cur_roles:
                await member.add_roles(i)

        log(f'Edited {member.id} with rank {level}')


    @bot.listen()
    async def on_member_join(member: discord.Member):
        '''
        Member joins
        '''
        log(f'Updating rank for {member.id}', level=INFO)
        await update_rank(member)
        log(f'Done updating rank for {member.id}', level=INFO)

        # auto adding the bot role
        if member.bot:
            log(f'Bot {member.id} joined', level=INFO)
            role = member.guild.get_role(BOT_ROLE_ID)
            await member.add_roles(role)
            return
        
        # adding the quarantine role
        if member.id in bot.mg.quarantines:
            log(f'Quarantined user {member.id} joined', level=INFO)
            role = member.guild.get_role(QUARANTINE_ROLE)
            await member.add_roles(role)
            return

        # sending verify hint
        channel = bot.get_channel(VERIFY_ID)

        view = to_view([add_accessory(
            [
                '### 👋 Добро пожаловать на moonland!',
                'Еще чуть-чуть!',
                'Для получения доступа к серверу введи команду `ml!verify` в этот чат.'
            ],
            accessory=ui.Thumbnail('https://moontr3.ru/assets/mlverify.png')
        )], text=f'<@{member.id}>')

        await channel.send(view=view)