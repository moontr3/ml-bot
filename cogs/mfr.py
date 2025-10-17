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
from bot import MLBot
import datetime


# setup
async def setup(bot: MLBot):
    
    @bot.hybrid_command(
        name='mishkfrede',
        description='Случайная карточка мишкфреде (+XP)',
        aliases=['мишкфреде','мф','mf','ьа','mfr','мишкафреде','мшкфреди','мшкфреде','мишкфреди','мишкафреди','motherfucker','фреде']
    )
    @discord.app_commands.user_install()
    @discord.app_commands.guild_install()
    @discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def mishkfrede(ctx: commands.Context):
        # command
        botuser: api.User = bot.mg.get_user(ctx.author.id)
        guild = ctx.guild and ctx.guild.id == GUILD_ID

        card: api.MfrCard = bot.mg.get_random_mfr()
        ephemeral = ctx.channel.id != MFR_CHANNEL

        if guild and not ephemeral and botuser.mfr_timeout <= time.time():
            bot.mg.add_xp(ctx.author.id, card.xp)

        color = discord.Color.from_str(card.color)
        
        if not guild:
            text = '-# Получать опыт за карточки можно только на сервере </moonland:1411399171042443447>.'
        elif ephemeral:
            text = f':warning: Если хотите получать опыт за получение карточек, вводите эту команду в <#{MFR_CHANNEL}>.'
        elif botuser.mfr_timeout > time.time():
            text = f'-# Опыт за находку карточки можно будет получить только **<t:{int(botuser.mfr_timeout)}:R>**.'
        else:
            text = f'Вы получили **{card.xp} XP** за находку!'

        bot.mg.add_mfr_stat(ctx.author.id, card.key)

        elements = [
            f'### {card.name}', text,
            ui.MediaGallery(discord.MediaGalleryItem(card.image))
        ]
        view = to_view(elements, color)

        await ctx.reply(view=view, ephemeral=ephemeral)
    

    @bot.hybrid_command(
        name='mishkfredestat',
        description='Посмотреть количество полученных карточек мишкфреде.',
        aliases=[
            'мишкфредестат','мфстат','mfstat','mfrstat','мфрстат',
            'мишкфредестатс','мфстатс','mfstats','mfrstats','мфрстатс','mishkfredestats',
            'мишкфредестата','мфстата','мфрстата','мишкфредестаты','мфстаты','мфрстаты',
         ]
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        user='Пользователь, статистику которого вы хотите узнать.'
    )
    async def mishkfredestat(ctx: commands.Context, user: discord.User = None):
        if user == None:
            user = ctx.author
            
        botuser: api.User = bot.mg.get_user(user.id)

        elements = [f'### 📊 Статистика мишкфреде {user.name}', SEP()]

        for k, v in bot.mg.data['mfr'].items():
            if k in botuser.mfr_stats:
                elements.append(f'`{botuser.mfr_stats[k]}` ・ **{v["name"]}**')
            
            elif not v.get('hidden'):
                elements.append('`0` ・ ???')

        view = to_view(elements)
        await ctx.reply(view=view)
