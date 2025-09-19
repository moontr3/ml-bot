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
        aliases=['мишкфреде','мф','mf','ьа','mfr','мишкафреде','мшкфреди','мшкфреде','мишкфреди','мишкафреди','motherfucker','фреде']
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def mishkfrede(ctx: commands.Context):
        botuser: api.User = bot.mg.get_user(ctx.author.id)
        if botuser.mfr_timeout > time.time():
            view = to_view(f'Использовать команду снова можно будет **<t:{int(botuser.mfr_timeout)}:R>**.', ERROR_C)
            await ctx.reply(view=view)
            return
        
        card: api.MfrCard = bot.mg.get_random_mfr()
        ephemeral = ctx.channel.id != MFR_CHANNEL
        if not ephemeral:
            bot.mg.add_xp(ctx.author.id, card.xp)
        bot.mg.add_mfr_stat(ctx.author.id, card.key)

        color = discord.Color.from_str(card.color)
        if ephemeral:
            text = f':warning: Если хотите получать опыт за получение карточек, вводите эту команду в <#{MFR_CHANNEL}>.'
        else:
            text = f'Вы получили **{card.xp} XP** за находку!'

        elements = [
            f'### {card.name}', text,
            ui.MediaGallery(discord.MediaGalleryItem(card.image)),
            SEP()
        ]
        view = to_view(elements+['-# 🔴 Команда на кулдауне...'], color)

        message = await ctx.reply(view=view, ephemeral=ephemeral)
        await asyncio.sleep(max(0, botuser.mfr_timeout-time.time()))

        view = to_view(elements+['-# 🟢 Можно отправлять снова'], color)
        await message.edit(view=view)
    

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
