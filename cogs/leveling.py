from discord.ext import commands
import discord
from data import *
from log import *
from typing import *
from config import *
import api


# setup
async def setup(bot: commands.Bot):

    # xp command
    @discord.app_commands.describe(
        member='Участник сервера, у которого нужно узнать опыт.'
    )
    @bot.hybrid_command(
        name='xp',
        description='Показывает текущий опыт пользователя.'
    )
    async def slash_xp(ctx:discord.Interaction, member:discord.Member=None):
        '''
        Shows user XP level.
        '''
        if member == None:
            member = ctx.user
        acc: api.User = bot.mg.get_user(member.id)

        log(f'{ctx.user.id} requested xp level of {member.id}')
        role = ctx.guild.get_role(acc.xp.level_data)

        desc = f'### {role.name.title()} ・ Уровень {acc.xp.level} ・ {acc.xp.xp} XP'\
            f'\n**{acc.xp.level_xp}** / **{acc.xp.level_max_xp}** (**{int(acc.xp.level_percentage*100)}%**)'

        embed = discord.Embed(
            description=desc, color=role.color
        )
        embed.set_author(name=f'✨ Опыт {member.display_name}')
        await ctx.reply(embed=embed)
