import os
import random
from discord.ext import commands, tasks
import discord
from log import *
from typing import *
from config import *
import api

import utils


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
    async def on_voice_state_update(
        member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        '''
        Updates user's VC state on update
        '''
        bot.mg.update_vc_state(member.id, after)


    @tasks.loop(seconds=60)
    async def vc_loop():
        '''
        Periodically fetches the voice channel state and updates the database
        '''
        guild = bot.get_guild(GUILD_ID)

        for channel in guild.voice_channels:
            for member in channel.members:
                bot.mg.update_vc_state(member.id, member.voice)


    @tasks.loop(seconds=1)
    async def xp_gain_loop():
        '''
        Periodically fetches the voice channel state and updates the database
        '''
        guild = bot.get_guild(GUILD_ID)

        for channel in guild.voice_channels:
            for member in channel.members:
                bot.mg.update_vc_xp(member.id)


    @bot.listen()
    async def on_ready():
        if not vc_loop.is_running():
            vc_loop.start()

        if not xp_gain_loop.is_running():
            xp_gain_loop.start()