from discord.ext import commands
import discord
from data import *
from log import *
from typing import *
from config import *


# setup
async def setup(bot: commands.Bot):

    # ping command
    @discord.app_commands.command(
        name='ping',
        description='Показывает пинг бота.'
    )
    async def slash_ping(ctx: discord.Interaction):
        '''
        Shows bot ping.
        '''
        ping = round(bot.latency*1000)
        embed = discord.Embed(
            title='🏓 Понг!', description=f'**{ping}** мс',
            color=DEFAULT_C
        )
        await ctx.response.send_message(embed=embed)

    bot.tree.add_command(slash_ping)


    # purge command
    @discord.app_commands.describe(
        amount='Количество сообщений для очистки',
        member='Фильтр для удаления сообщений только указанного участника',
        keywords='Фильтр для удаления сообщений только с нужным текстом'
    )
    @discord.app_commands.command(
        name='purge',
        description='Удаляет определенное количество сообщений в канале.'
    )
    @commands.has_permissions(manage_messages=True)
    async def slash_purge(
        ctx: discord.Interaction, amount:int,
        member:discord.User=None, keywords:str=''
    ):
        '''
        Purges the channel.
        '''
        # just purge
        if member == None and keywords == '':
            deleted = await ctx.channel.purge(limit=amount)
            text = f'Успешно очищено **{len(deleted)}** сообщений!'

        # filter by user
        elif member != None and keywords == '':
            def check(m):
                return m.author.id == member.id
            
            deleted = await ctx.channel.purge(limit=amount, check=check)
            text = f'Успешно очищено **{len(deleted)}** сообщений от {member.mention}!'

        # filter by keywords
        elif member == None and keywords != '':
            def check(m):
                return keywords in m.content
            
            deleted = await ctx.channel.purge(limit=amount, check=check)
            text = f'Успешно очищено **{len(deleted)}** из **{amount}** проверенных сообщений!'
        
        # both
        else:
            def check(m):
                return (keywords in m.content) and\
                    (m.author.id == member.id)
            
            deleted = await ctx.channel.purge(limit=amount, check=check)
            text = f'Успешно очищено **{len(deleted)}** сообщений от {member.mention}!'

        # sending message
        # checking if there even was something deleted
        if len(deleted) == 0:
            embed = discord.Embed(
                title='🗑 Очистка', color=ERROR_C,
                description='По такому запросу не найдено сообщений, которые можно удалить.'
            )
        else:
            embed = discord.Embed(
                title='🗑 Очистка', description=text,
                color=DEFAULT_C
            )
        await ctx.response.send_message(embed=embed)

    bot.tree.add_command(slash_purge)
