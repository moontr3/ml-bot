from discord.ext import commands
from discord import Webhook
import aiohttp
import discord
from log import *
from typing import *
from config import *


# setup
async def setup(bot: commands.Bot):

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

        if member.bot:
            log(f'Bot {member.id} joined', level=INFO)
            role = member.guild.get_role(BOT_ROLE_ID)
            await member.add_roles(role)
            return

        # sending verify hint
        channel = bot.get_channel(VERIFY_ID)

        view = ui.LayoutView()
        
        c = ui.Container()
        c.add_item(ui.Section(
            ui.TextDisplay('### 👋 Добро пожаловать на moonland!'),
            ui.TextDisplay('Для получения доступа к серверу введи команду `ml!verify` в этот чат.'),
            accessory=ui.Thumbnail('https://moontr3.ru/assets/mlverify.png')
        ))

        view.add_item(ui.TextDisplay(f'<@{member.id}>'))
        view.add_item(c)

        await channel.send(view=view)