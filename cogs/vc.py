import os
import random
import aiohttp
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


    @bot.hybrid_command(
        name='vc',
        aliases=['войс','голос','voice'],
        description='Показывает время пользователя в голосовом канале.'
    )
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(
        member='Участник сервера, у которого нужно узнать время.'
    )
    async def slash_vc(ctx:discord.Interaction, member:discord.User=None):
        '''
        Shows user time in VC.
        '''
        if member == None:
            member = ctx.author

        log(f'{ctx.author.id} requested vc time of {member.id}')

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        path = await bot.mg.renderer.user_vc(member)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.listen()
    async def on_voice_state_update(
        member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        '''
        Updates user's VC state on update
        '''
        if member.bot: return
        bot.mg.update_vc_state(member.id, after)

        # leaving/joining vc messages
        session = aiohttp.ClientSession()
        webhook = discord.Webhook.from_url(bot.SERVICE_WEBHOOK, session=session)
    
        if before.channel == None and after.channel != None:
            if after.channel.type == discord.ChannelType.stage_voice:
                await session.close()
                return
            
            await webhook.send(
                f'<@{member.id}>  →  <#{after.channel.id}>',
                avatar_url=JOIN_IMAGE, username='Вход в голосовой канал',
                allowed_mentions=NO_MENTIONS
            )
        
        elif before.channel != None and after.channel == None:
            if before.channel.type == discord.ChannelType.stage_voice:
                await session.close()
                return
            
            await webhook.send(
                f'<@{member.id}>  ←  <#{before.channel.id}>',
                avatar_url=LEAVE_IMAGE, username='Выход из голосового канала',
                allowed_mentions=NO_MENTIONS
            )

        elif before.channel != after.channel and (before.channel != None and after.channel != None):
            await webhook.send(
                f'<#{before.channel.id}>  →  <@{member.id}>  →  <#{after.channel.id}>',
                avatar_url=MOVE_IMAGE, username='Переход в голосовой канал',
                allowed_mentions=NO_MENTIONS
            )

        # live messages
        elif not before.self_stream and after.self_stream:
            if after.channel.type == discord.ChannelType.stage_voice:
                await session.close()
                return
            
            await webhook.send(
                f'<@{member.id}> ・ <#{after.channel.id}>',
                avatar_url=LIVE_IMAGE, username='Включение трансляции экрана',
                allowed_mentions=NO_MENTIONS
            )
            
        elif before.self_stream and not after.self_stream:
            if after.channel.type == discord.ChannelType.stage_voice:
                await session.close()
                return
            
            await webhook.send(
                f'<@{member.id}> ・ <#{after.channel.id}>',
                avatar_url=LIVESTOP_IMAGE, username='Выключение трансляции экрана',
                allowed_mentions=NO_MENTIONS
            )

        await session.close()


    @tasks.loop(seconds=60)
    async def vc_loop():
        '''
        Periodically fetches the voice channel state and updates the database
        '''
        guild = bot.get_guild(GUILD_ID)

        for channel in guild.voice_channels:
            for member in channel.members:
                if member.bot: continue
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