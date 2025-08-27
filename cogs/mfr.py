import asyncio
import os
import random
import time
from discord.ext import commands
import discord
import api
from log import *
from typing import *
from config import *
import utils
import datetime


# setup
async def setup(bot: commands.Bot):
    
    @bot.hybrid_command(
        name='mishkfrede',
        description='Случайная карточка мишкфреде (+XP)',
        aliases=['мишкфреде','мф','mf','mfr','мишкафреде','мшкфреди','мшкфреде','мишкфреди','мишкафреди','motherfucker','фреде']
    )
    @discord.app_commands.guild_only()
    async def mishkfrede(ctx: commands.Context):
        botuser: api.User = bot.mg.get_user(ctx.author.id)
        if botuser.mfr_timeout > time.time():
            embed = discord.Embed(
                color=ERROR_C,
                description=f'Использовать команду снова можно будет **<t:{int(botuser.mfr_timeout)}:R>**.'
            )
            await ctx.reply(embed=embed)
            return
        
        card: api.MfrCard = bot.mg.get_random_mfr()
        ephemeral = ctx.channel.id != MFR_CHANNEL
        if not ephemeral:
            bot.mg.add_xp(ctx.author.id, card.xp)
        bot.mg.add_mfr_stat(ctx.author.id, card.key)

        color = discord.Color.from_str(card.color)
        if ephemeral:
            text = f'⚠ Если хотите получать опыт за получение карточек, вводите эту команду в <#{MFR_CHANNEL}>.'
        else:
            text = f'Вы получили **{card.xp} XP** за находку!'

        embed = discord.Embed(
            title=card.name, color=color,
            description=text+f'\n-# 🔴 Кулдаун закончится <t:{int(botuser.mfr_timeout)+1}:R>...'
        )
        embed.set_image(url=card.image)

        message = await ctx.reply(embed=embed, ephemeral=ephemeral)
        await asyncio.sleep(max(0, botuser.mfr_timeout-time.time()))

        embed = discord.Embed(title=card.name, color=color, description=text+f'\n-# 🟢 Можно вводить снова')
        embed.set_image(url=card.image)
        await message.edit(embed=embed)
    

    @bot.hybrid_command(
        name='mishkfredestat',
        description='Посмотреть количество полученных карточек мишкфреде.',
        aliases=['мишкфредестат','мфстат','mfstat','mfrstat','мишкафредестат','мшкфредистат','мшкфредестат','мишкфредистат','мишкафредистат']
    )
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(
        user='Пользователь, статистику которого вы хотите узнать.'
    )
    async def mishkfredestat(ctx: commands.Context, user: discord.User = None):
        if user == None:
            user = ctx.author
            
        botuser: api.User = bot.mg.get_user(user.id)

        text = ''
        for k, v in bot.mg.data['mfr'].items():
            if k in botuser.mfr_stats:
                text += f'`{botuser.mfr_stats[k]}` ・ **{v["name"]}**\n'
            
            elif not v.get('hidden'):
                text += f'`0` ・ ???\n'

        embed = discord.Embed(title=f'Статистика мишкфреде {user.name}', description=text, color=DEFAULT_C)

        await ctx.reply(embed=embed)
