from discord.ext import commands
import discord
import api
from log import *
from typing import *
from config import *

from bot import MLBot


# setting up

async def setup(bot: MLBot):
    if not bot.features.crossposter:
        return
    
    # discord
    
    @bot.hybrid_command(
        name='link',
        description='Привязать аккаунт в Telegram',
        aliases=['тг','тгч','тгчат','чаттг','линк','linktg','телеграм','telegram','tglink','tgc','tgchat'],
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def link_tg(ctx: commands.Context):
        # checking if already linked
        user = bot.mg.get_user(ctx.author.id)

        if user.tg:
            view = to_view([
                ui.Section(
                    ui.TextDisplay('### ✈️ Привязка к аккаунту в Telegram'),
                    accessory=ui.Button(
                        style=discord.ButtonStyle.danger, label='Отвязать',
                        custom_id=f'unlinktg:{ctx.author.id}'
                    )
                ),
                SEP(),
                'У вас привязан Telegram-аккаунт! Круто!',
                (
                    f'-# ID: `{user.tg}`' if not user.tg_username
                    else f'-# **@{user.tg_username}**  ・  ID: `{user.tg}`'
                )
            ])
            await ctx.reply(view=view, ephemeral=True)
            return

        # generating code
        code = bot.mg.get_tg_link_key(ctx.author.id)

        elements = [
            '### ✈️ Привязка к аккаунту в Telegram', SEP(),
            'У основного чата moonland:re есть **чат-зеркало в Telegram**, куда пересылаются все '\
                'сообщения с чата в Discord и наоборот.',
            '### https://t.me/moonlandre',
            'Пересылка работает и **без привязки аккаунтов**, но при привязке станет доступно пару плюсов.',\
            SEP(), '**Что будет, если подключить аккаунт в Telegram**',
            '- При пинге в Telegram вы будете пингануты и в Discord (и наоборот)\n'\
            '- Будет отображаться аватарка вашего Discord-профиля при пересылке сообщения из Telegram\n'\
            '- ~~Вы будете получать опыт за сообщения, отправленные в Telegram~~\n'\
            '- ~~Возможность изменить отображаемое имя у ваших пересланных в Telegram сообщений~~\n',\
            SEP(), '**Как подключить**',
        ]

        if not ctx.interaction:
            elements.append(
                '- Получить код по команде </link:1428473934793146519>\n'\
                '- Отправить полученный код в ЛС боту [@moonlandrebot](https://t.me/moonlandrebot)'
            )

        else:
            link = f'https://t.me/moonlandrebot?start={code}'
            elements.append(
                ui.Section(
                    f'Перейти по [ссылке]({link}) и нажать кнопку "Начать" у бота',
                    '-# или',
                    f'Отправить команду `/link {code}` Telegram-боту [@moonlandrebot](https://t.me/moonlandrebot) в ЛС',
                    accessory=ui.Button(
                        label='Перейти',
                        url=link
                    )
                )
            )

        view = to_view(elements)
        await ctx.reply(view=view, ephemeral=True)


    # handling components
    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        botuser: api.User = bot.mg.get_user(interaction.user.id)
        
        # unlinking account
        if interaction.data['custom_id'].startswith('unlinktg:'):
            user = int(interaction.data['custom_id'].split(':')[1])

            if user != interaction.user.id:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            # unlinking
            bot.mg.unlink_tg(user)

            # editing view
            view = to_view([
                '### ✈️⏸️ Привязка к аккаунту в Telegram', SEP(),
                'Вы успешно отвязали свой Telegram-аккаунт!',
                'Привязать снова можно по команде </link:1428473934793146519>.'
            ])

            await interaction.response.edit_message(view=view)
