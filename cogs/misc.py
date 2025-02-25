from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import utils
import datetime


# setup
async def setup(bot: commands.Bot):

    # ping command
    @bot.hybrid_command(
        name='ping',
        description='Показывает пинг бота.'
    )
    async def slash_ping(ctx: commands.Context):
        '''
        Shows bot ping.
        '''
        log(f'{ctx.author.id} requested bot ping')
        ping = round(bot.latency*1000)
        embed = discord.Embed(
            title='🏓 Понг!', description=f'**{ping}** мс',
            color=DEFAULT_C
        )
        await ctx.reply(embed=embed)


    @bot.hybrid_command(
        name='about',
        description='Показывает информацию о боте.'
    )
    async def slash_about(ctx: commands.Context):
        '''
        Shows bot info.
        '''
        log(f'{ctx.author.id} requested bot info')
        
        embed = discord.Embed(
            color=DEFAULT_C, title='ℹ О боте',
            description='Создатель: `moontr3` (obviously)\n'\
                f'Контрибьютор: `mbutsk`\n'\
                f'Написан на **Python** и **discord.py**'\
                f'Пользователей зарегистрировано: **{len(bot.mg.users)}**\n'\
                f'Участников на сервере: **{ctx.guild.member_count}**'
        )

        await ctx.reply(embed=embed)


    # purge command
    @discord.app_commands.describe(
        amount='Количество сообщений для очистки',
        member='Фильтр для удаления сообщений только указанного участника',
        keywords='Фильтр для удаления сообщений только с нужным текстом'
    )
    @bot.hybrid_command(
        name='purge',
        description='Удаляет определенное количество сообщений в канале.'
    )
    async def slash_purge(
        ctx: commands.Context, amount:int,
        member:discord.User=None, keywords:str=''
    ):
        '''
        Purges the channel.
        '''
        # checking permissions
        if not ctx.permissions.manage_messages:
            await ctx.reply(embed=MISSING_PERMS_EMBED)
            return
        
        # sending loading message
        await ctx.reply(embed=LOADING_EMBED)

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

        log(f'{ctx.author.id} purged {len(deleted)}/{amount} messages in {ctx.channel.id}')

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
        await ctx.response.edit_message(embed=embed)


    # mute command
    @discord.app_commands.describe(
        member='Участник, которого нужно замутить',
        time='Длина мута в формате "10h", "3д" и так далее',
        reason='Причина мута'
    )
    @bot.hybrid_command(
        name='mute',
        description='Мутит определенного участника на сервере.'
    )
    async def slash_mute(
        ctx: commands.Context, member:discord.Member,
        time:str, reason:str=None
    ):
        '''
        Mutes the specified user.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members:
            await ctx.reply(embed=MISSING_PERMS_EMBED)
            return

        # muting user
        data = utils.seconds_from_string(time)
        # checking input validity
        if data == None:
            embed = discord.Embed(
                title='🤐 Таймаут', color=ERROR_C,
                description=f'Указана некорректная длина.'
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return
        
        else:
            length = data[0]
            unit_name = data[1]
            unit_length = data[2]

        length = datetime.timedelta(seconds=length)
        
        # timeouting user
        try:
            await member.timeout(length, reason=reason)
            log(f'{ctx.author.id} timeouted user {member.id} for {time}')
        
        except Exception as e:
            log(f'Error while {ctx.author.id} was timeouting {member.id} for {time}: {e}', level=ERROR)
            embed = discord.Embed(
                title='🤐 Таймаут', color=ERROR_C,
                description=f'Не удалось замутить участника.'
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        # sending message
        if reason == None:
            embed = discord.Embed(
                title='🤐 Таймаут', color=DEFAULT_C,
                description=f'{member.mention} успешно замьючен на **{unit_length} {unit_name}**.'
            )
        else:
            embed = discord.Embed(
                title='🤐 Таймаут', color=DEFAULT_C,
                description=f'{member.mention} успешно замьючен на **{unit_length} {unit_name}**'\
                    f' с причиной **{utils.remove_md(reason)}**.'
            )
        await ctx.reply(embed=embed)


    # unmute command
    @discord.app_commands.describe(
        member='Участник, которого нужно размутить'
    )
    @bot.hybrid_command(
        name='unmute',
        description='Размучивает определенного участника на сервере.'
    )
    async def slash_unmute(
        ctx: commands.Context, member:discord.Member
    ):
        '''
        Unmutes the specified user.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members:
            await ctx.reply(embed=MISSING_PERMS_EMBED)
            return

        # checking if the user is muted or not
        if member.timed_out_until == None:
            embed = discord.Embed(
                title='🤐 Размут', color=ERROR_C,
                description=f'Выбранный участник и так не в муте.'
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        # unmuting
        try:
            await member.timeout(None)
            log(f'{ctx.author.id} unmuted user {member.id}')

        except Exception as e:
            log(f'Error while {ctx.author.id} was unmuting {member.id}: {e}', level=ERROR)
            embed = discord.Embed(
                title='🤐 Размут', color=ERROR_C,
                description=f'Не удалось размутить участника.'
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return
            
        embed = discord.Embed(
            title='🤐 Размут', color=DEFAULT_C,
            description=f'Вы успешно размутили {member.mention}!'
        )
        await ctx.reply(embed=embed)
