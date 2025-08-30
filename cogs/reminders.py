from discord.ext import commands, tasks
import discord
import api
import time
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

                        elements = ['### 🔔 Напоминание', SEP()]

                        if reminder.jump_url:
                            elements.append(reminder.jump_url)
                        if reminder.text:
                            elements.append(reminder.text)

                        view = to_view(elements, text=f'<@{user.id}>')

                        # sending
                        try:
                            assert reminder.message_id != None
                            message = await channel.fetch_message(reminder.message_id)
                        except:
                            await channel.send(view=view)
                        else:
                            await message.reply(view=view)

                    except Exception as e:
                        log(f'Unable to remove reminder: {e}', level=ERROR)

                    # removing reminder
                    mg.remove_reminder(user.id, index)
                    index -= 1

                index += 1


    @bot.listen()
    async def on_ready():
        if not check_reminders.is_running():
            check_reminders.start()


    @bot.hybrid_command(
        name='reminder',
        description='Ставит напоминание.',
        aliases=['remindme','напомни','напоминание','remind']
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        duration='Через сколько времени напомнить.',
        text='Текст напоминания.'
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
        botuser: api.User = bot.mg.get_user(ctx.author.id)

        if len(botuser.reminders) >= MAX_REMINDERS:
            view = to_view(f'Вы достигли лимита напоминаний в **{len(botuser.reminders)} штук**.', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
        
        # checking input validity
        data = utils.seconds_from_string(duration)

        if data == None:
            await ctx.reply(view=c_to_view(INCORRECT_LENGTH_EMBED), ephemeral=True)
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

        _time = int(time.time()+length)
        text = f' с текстом **{utils.remove_md(text)}**' if text else ''

        view = to_view([
            '### 🔔 Напоминание', SEP(),
            f'Успешно поставлено напоминание на **{unit_length} {unit_name}** (<t:{_time}>)' + text + '.'
        ], DEFAULT_C)
        await ctx.reply(view=view, ephemeral=True)


    def get_reminders_view(author: int, reminders: List[api.Reminder]) -> ui.LayoutView:
        if len(reminders) == 0:
            return to_view([
                '### Напоминаний нет!', SEP(),
                'Используй `ml!reminder <длительность> <текст>` для создания.'
            ])
        
        elements = []

        for index, i in enumerate(reminders):
            texts = []

            if i.end_time >= 2**33:
                text = 'Дохуя'
            else:
                text = f'**<t:{int(i.end_time)}>** (<t:{int(i.end_time)}:R>)'
            
            if i.jump_url:
                text += f' ・ [Перейти ↗](<{i.jump_url}>)'
            texts.append(text)

            if i.text:
                texts.append(i.text)

            elements.append(add_accessory(texts, accessory=ui.Button(
                style=discord.ButtonStyle.danger,
                emoji='<:delete:1410978047607439410>', custom_id=f'deletereminder:{index}:{author}'
            )))

            elements.append(SEP())

        elements = elements[:-1]

        return to_view(elements)


    @bot.hybrid_command(
        name='reminders',
        description='Посмотреть список своих напоминаний.',
        aliases=['remindmes','напоминания','reminds']
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def slash_reminders(
        ctx: commands.Context
    ):
        '''
        Shows reminder list
        '''
        log(f'{ctx.author.id} invoked reminders command')
        botuser: api.User = bot.mg.get_user(ctx.author.id)
        
        view = get_reminders_view(ctx.author.id, botuser.reminders)
        await ctx.reply(view=view, ephemeral=True)


    # handling components
    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        if not interaction.data['custom_id'].startswith('deletereminder'):
            return
        
        # checking data
        index = int(interaction.data['custom_id'].split(':')[1])
        user = int(interaction.data['custom_id'].split(':')[2])

        if user != interaction.user.id:
            await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
            return
        
        # removing reminder
        bot.mg.remove_reminder(user, index)
        
        botuser: api.User = bot.mg.get_user(user)
        view = get_reminders_view(user, botuser.reminders)    
        
        await interaction.response.edit_message(view=view)