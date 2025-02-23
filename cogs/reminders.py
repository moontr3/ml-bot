from discord.ext import commands, tasks
import discord
import api
import time
from data import *
from log import *
from typing import *
from config import *
import utils
import datetime


# setup
async def setup(bot: commands.Bot):

    # checks api and responds to reminders
    @tasks.loop(seconds=3)
    async def check_reminders():
        mg: api.Manager = bot.mg
        
        # users
        for user in mg.users.values():
            # reminders
            index = 0

            for reminder in user.reminders.copy():
                if time.time() >= reminder.end_time:
                    # reminding
                    log(
                        f'{user.id}\'s reminder "{reminder.text}" done'\
                        f' ({reminder.channel_id}, {reminder.message_id})'
                    )
                    try:
                        channel = await bot.fetch_channel(reminder.channel_id)
                        text = reminder.text if reminder.text != None else ''

                        embed = discord.Embed(
                            title='🔔 Напоминание',
                            description=text if reminder.jump_url == None else None,
                            color=DEFAULT_C
                        )
                        if reminder.jump_url != None:
                            embed.add_field(
                                name=reminder.jump_url,
                                value=text
                            )

                        # sending
                        try:
                            assert reminder.message_id != None
                            message = await channel.fetch_message(reminder.message_id)
                        
                        except:
                            await channel.send(f'<@{user.id}>', embed=embed)
                        
                        else:
                            await message.reply(f'<@{user.id}>', embed=embed)

                    except Exception as e:
                        log(f'Unable to remove reminder: {e}', level=ERROR)

                    # removing reminder
                    mg.remove_reminder(user.id, index)
                    index -= 1

                index += 1


    @bot.event
    async def on_ready():
        if not check_reminders.is_running():
            check_reminders.start()

    # set reminder
    @bot.hybrid_command(
        name='reminder',
        description='Ставит напоминание.',
        aliases=['remindme','напомни','напоминание','remind']
    )
    async def slash_reminder(
        ctx: commands.Context,
        duration: str, *,
        text: str = None
    ):
        '''
        Sets a reminder.
        '''
        log(f'{ctx.author.id} invoked reminder command')
        
        # checking input validity
        data = utils.seconds_from_string(duration)

        if data == None:
            embed = discord.Embed(
                title='🔔 Напоминание', color=ERROR_C,
                description=f'Указана некорректная длина.'
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return
        
        else:
            length = data[0]
            unit_name = data[1]
            unit_length = data[2]

        # adding a reminder
        bot.mg.add_reminder(
            ctx.author.id,
            ctx.message.id if not ctx.interaction else None,
            ctx.channel.id,
            length,
            ctx.message.jump_url if not ctx.interaction else None,
            text
        )

        _time = int(datetime.datetime.fromtimestamp(time.time()+length).timestamp())
        text = f' с текстом **{utils.remove_md(text)}**' if text else ''

        embed = discord.Embed(
            title='🔔 Напоминание', color=DEFAULT_C,
            description=f'Успешно поставлено напоминание на **'\
                f'{unit_length} {unit_name}** (<t:{_time}>)' + text + '.'
        )
        await ctx.reply(embed=embed, ephemeral=True)
