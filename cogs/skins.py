import os
import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import api
from PIL import Image, ImageDraw, ImageFont

import utils


# setup
async def setup(bot: commands.Bot):


    # @discord.app_commands.describe(
    #     member='Участник сервера, у которого нужно поменять опыт.',
    #     action='Действие',
    #     amount='Количество опыта'
    # )
    @bot.command(
        name='skin',
        description='Изменить скины пользователя.'
    )
    async def slash_manage_skins(ctx:commands.Context, member:discord.Member, action:Literal['set','add','remove'], skin:str):
        '''
        Changes user skins.
        '''
        if ctx.author.id not in ADMINS:
            embed = discord.Embed(
                description='Вы не администратор бота!',
                color=ERROR_C
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        log(f'{ctx.author.id} {action}s skins of {member.id}: {skin}')
        
        if action == 'set':
            if skin == 'none':
                skin = None
            bot.mg.set_skin(member.id, skin)
            desc = f'{member.mention} установлен скин **{skin}**'
        elif action == 'add':
            success = bot.mg.add_skin(member.id, skin)
            if success:
                desc = f'К {member.mention} добавлен скин **{skin}**'
            else:
                desc = f'АТАТА!!! ❌❌❌ у {member.mention} уже есть этот скин.'
        else:
            success = bot.mg.remove_skin(member.id, skin)
            if success:
                desc = f'У {member.mention} убран скин **{skin}**'
            else:
                desc = f'АТАТА!!! ❌❌❌ у {member.mention} не было этого скина.'

        embed = discord.Embed(
            description=desc, color=DEFAULT_C
        )
        await ctx.reply(embed=embed)
