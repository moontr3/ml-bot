import aiohttp
from discord.ext import commands, tasks
import discord
from log import *
from config import *
import utils
import time
import copy
import api
from bot import MLBot

# setup
async def setup(bot: MLBot):

    @bot.hybrid_command(
        name='quarantine',
        aliases=['карантин', 'гречкамартини', 'quar', 'кар'],
        description='👩‍⚖️ Отправляет пользователя в карантин.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        member='Участник, которого нужно отправить в карантин.',
        length='Длина карантина в формате "10h", "3д" и так далее.',
    )
    async def quarantine(ctx: commands.Context,
        member:discord.Member, length:str
    ):
        '''
        Sends the specified user to quarantine.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members and ctx.author.id not in ADMINS:
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED))
            return
        
        time_data = utils.seconds_from_string(length)

        if not time_data:
            await ctx.reply(view=c_to_view(INCORRECT_LENGTH_EMBED), ephemeral=True)
            return

        epoch_time = time.time() + time_data[0]
        unit_name = time_data[1]
        unit_length = time_data[2]

        # checking if quarantined
        if member.id in bot.mg.quarantines:
            release_at = bot.mg.quarantines[member.id]

            view = to_view([
                f'{member.name} и так в карантине.',
                f'-# Выпуск <t:{int(release_at)}:R>'
            ], ERROR_C)
            return await ctx.reply(view=view)

        # adding quarantine role
        try:
            role = ctx.guild.get_role(QUARANTINE_ROLE)
            verify_role = ctx.guild.get_role(VERIFY_ROLE)
            await member.add_roles(role)
            await member.remove_roles(verify_role)

        except Exception as e:
            log(f'Error while {ctx.author.id} was adding quarantine role to {member.id}: {e}', level=ERROR)
            view = to_view('Не удалось выдать участнику роль карантина.', ERROR_C)
            return await ctx.reply(view=view, ephemeral=True)
        
        # adding quarantine
        bot.mg.add_quarantine(member.id, epoch_time)
        log(f'{ctx.author.id} sent user {member.id} to quarantine for {length}')
        
        view = to_view([
            '### 🦠 Карантин', SEP(),
            f'{member.name} успешно помещен в карантин на **{unit_length} {unit_name}**.'
        ])
        await ctx.reply(view=view)

    
    @bot.hybrid_command(
        name='release',
        aliases=['разкарантин', 'негречкамартини', 'unquar', 'разкар', 'выпустить', 'unquarantine'],
        description='👩‍⚖️ Выпускает пользователя с карантина.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        member='Участник, которого нужно выпустить с карантина',
    )
    async def unquarantine(ctx: commands.Context,
        member:discord.Member
    ):
        '''
        Removes quarantine from specified user.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members and ctx.author.id not in ADMINS:
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED))
            return
        
        if member.id not in bot.mg.quarantines:
            view = to_view(f'{member.name} и так не в карантине.', ERROR_C)
            return await ctx.reply(view=view)
        
        # removing from quarantine
        log(f'{ctx.author.id} released user {member.id} from quarantine')
        bot.mg.remove_quarantine(member.id)

        view = to_view([
            '### 🦠 Карантин', SEP(),
            f'{member.name} успешно выпущен с карантина.'
        ], DEFAULT_C)

        try:
            role = ctx.guild.get_role(QUARANTINE_ROLE)
            verify_role = ctx.guild.get_role(VERIFY_ROLE)
            await member.remove_roles(role)
            await member.add_roles(verify_role)
            
        except Exception as e:
            log(f'Unable to remove quarantine role from user {member.id}: {e}', level=ERROR)
            view = to_view([
                '### 🦠 Карантин', SEP(),
                f'{member.name} успешно выпущен с карантина.',
                '-# :warning: Не удалось снять роль карантина с участинка!'
            ], DEFAULT_C)

        await ctx.reply(view=view)
    
    
    @tasks.loop(seconds=5)
    async def quarantine_end_loop():
        guild = bot.get_guild(GUILD_ID)
        role = guild.get_role(QUARANTINE_ROLE)
        verify_role = guild.get_role(VERIFY_ROLE)

        quars = copy.deepcopy(list(bot.mg.quarantines.items()))

        for user_id, end_time in quars:
            if time.time() < end_time:
                return
            
            try:
                member = await guild.fetch_member(user_id)
                await member.remove_roles(role)
                await member.add_roles(verify_role)
            except Exception as e:
                log(f'Unable to remove quarantine role from {user_id}: {e}', level=ERROR)

            bot.mg.remove_quarantine(user_id)
            log(f'Quarantine ended for user {user_id}')

            # sending quarantine end message
            await bot.service_webhook.send(
                f'<@{user_id}> пережил свое наказание...',
                avatar_url=TIMEOUT_IMAGE, username='Выход из карантина',
            )

    
    @bot.listen()
    async def on_ready():
        if not quarantine_end_loop.is_running():
            quarantine_end_loop.start()