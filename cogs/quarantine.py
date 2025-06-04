from discord.ext import commands, tasks
import discord
from log import *
from config import *
import utils
import time
import copy

# setup
async def setup(bot: commands.Bot):

    @bot.hybrid_command(
        name='quarantine',
        aliases=['карантин', 'гречкамартини', 'quar'],
        description='Отправляет пользователя на карантин'
    )
    @discord.app_commands.describe(
        member='Участник, которого нужно отправить на карантин',
        length='Длина карантина в формате "10h", "3д" и так далее',
    )
    async def quarantine(ctx: commands.Context,
        member:discord.Member, length:str
    ):
        '''
        Sends the specified user to quarantine.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members and ctx.author.id not in ADMINS:
            await ctx.reply(embed=MISSING_PERMS_EMBED)
            return
        
        time_data = utils.seconds_from_string(length)

        if not time_data:
            embed = discord.Embed(
                title='🦠 Карантин', color=ERROR_C,
                description=f'Указана некорректная длина.'
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        epoch_time = time.time() + time_data[0]
        unit_name = time_data[1]
        unit_length = time_data[2]

        role = ctx.guild.get_role(QUARANTINE_ROLE)

        if role in member.roles:
            embed = discord.Embed(
                title='🦠 Карантин', color=ERROR_C,
                description=f'{member.mention} уже **гречка мартини**.'
            )

            return await ctx.reply(embed=embed)


        try:
            await member.add_roles(role)
            bot.mg.add_quarantine(member.id, epoch_time)
            log(f'{ctx.author.id} sent to quarantine user {member.id} for {length}')
        
        except Exception as e:
            log(f'Error while {ctx.author.id} was sending to quarantine {member.id} for {length}: {e}', level=ERROR)
            embed = discord.Embed(
                title='🦠 Карантин', color=ERROR_C,
                description=f'Не удалось сделать участника **гречка мартини**.'
            )
            return await ctx.reply(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
                title='🦠 Карантин', color=DEFAULT_C,
                description=f'{member.mention} успешно стал **гречка мартини** на **{unit_length} {unit_name}**.'
            )

        await ctx.reply(embed=embed)
    
    @bot.hybrid_command(
        name='unquarantine',
        aliases=['разкарантин', 'негречкамартини', 'unquar'],
        description='Снимает пользователя с карантина'
    )
    @discord.app_commands.describe(
        member='Участник, которого нужно снять с карантина',
    )
    async def unquarantine(ctx: commands.Context,
        member:discord.Member
    ):
        '''
        Removes quarantine from specified user.
        '''

        # checking permissions
        if not ctx.permissions.moderate_members and ctx.author.id not in ADMINS:
            await ctx.reply(embed=MISSING_PERMS_EMBED)
            return
        
        role = ctx.guild.get_role(QUARANTINE_ROLE)
        if role not in member.roles:
            embed = discord.Embed(
                title='🦠 Карантин', color=ERROR_C,
                description=f'{member.mention} не **гречка мартини**.'
            )
            return await ctx.reply(embed=embed)
        
        try:
            await member.remove_roles(role)
            bot.mg.remove_quarantine(member.id)
            log(f'{ctx.author.id} remove from quarantine user {member.id}')
        except Exception as e:
            log(f'Error while {ctx.author.id} was removimg from quarantine {member.id}: {e}', level=ERROR)
            embed = discord.Embed(
                title='🦠 Карантин', color=ERROR_C,
                description=f'Не удалось сделать участника не **гречка мартини**.'
            )
            return await ctx.reply(embed=embed, ephemeral=True)

        embed = discord.Embed(
                title='🦠 Карантин', color=DEFAULT_C,
                description=f'{member.mention} больше не **гречка мартини**.'
            )

        await ctx.reply(embed=embed)
    
    # task loop
    @tasks.loop(seconds=10)
    async def loop():
        cur_time = time.time()
        guild = bot.get_guild(GUILD_ID)
        role = guild.get_role(QUARANTINE_ROLE)

        quars = copy.deepcopy(list(bot.mg.quarantines.items()))

        for user_id, end_time in quars:
            if cur_time >= end_time:
                member = guild.get_member(user_id)
                await member.remove_roles(role)
                bot.mg.remove_quarantine(user_id)
                log(f'Quarantine is removed from user{user_id}')
    
    @bot.listen()
    async def on_ready():
        if not loop.is_running():
            loop.start()