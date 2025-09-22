import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import utils
import api
from bot import MLBot
import os


# setup
async def setup(bot: MLBot):

    @bot.command(
        name='verify',
        aliases=['вериф', 'верифицировать', 'верифнуть', 'iqтест','iqtest','iq-test','iq_test','iq_тест','iq-тест']
    )
    @api.check_guild
    async def verify(ctx: commands.Context):
        '''
        Verify yourself.
        '''
        log(f'{ctx.author.id} requested verification')

        if ctx.author.get_role(config.VERIFY_ROLE):
            view = to_view('Долбоеб! Ты уже.', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return

        if ctx.channel.id != config.VERIFY_ID:
            view = to_view('Не тот канал!', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
            
        user = bot.mg.get_user(ctx.author.id)
        if user.verifying:
            view = to_view([
                '### Ты уже проходишь IQ-тест!', SEP(),
                'Тебе надо ввести код с картинки в чат.'
            ], ERROR_C)
            await ctx.reply(view=view)
            return

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        user.verifying = True

        text = ''.join(random.choices('0123456789', k=5))
        image = bot.mg.renderer.captcha(text)
        file = discord.File(image, filename='captcha.png')

        view = to_view([
            '### 🧠 IQ-тест', SEP(),
            'Введи **в чат** цифры с картинки.', 'На размышление даётся 60 секунд.',
            ui.MediaGallery(discord.MediaGalleryItem('attachment://captcha.png'))
        ])

        msg = await ctx.reply(file=file, view=view)
        file.close()
        os.remove(image)

        # waiting for response
        try:
            message = await bot.wait_for(
                'message',
                check=lambda m: m.author.id == ctx.author.id and\
                    m.channel.id == ctx.channel.id,
                timeout=60
            )

        except:
            view = to_view([
                '### 🧠 IQ-тест', SEP(),
                'Прошло больше 60 секунд.',
            ], ERROR_C)
            await msg.remove_attachments()
            await msg.edit(view=view)
            user.verifying = False
            return
        
        else:
            user.verifying = False
            await message.delete()
            await msg.remove_attachments()

            if text.lower() == message.content.lower():
                # verified
                log(f'verified {ctx.author.id}')

                # adding role
                await message.author.add_roles(
                    ctx.guild.get_role(config.VERIFY_ROLE)
                )
                
                # sending success message
                view = to_view([
                    '### 🧠 IQ-тест', SEP(),
                    'Вы прошли IQ-тест!',
                    'Ваш IQ: **мало, но для мунленда хватает**', SEP(),
                    f'Прошу пройти в <#{CHAT_CHANNEL}>.'
                ], DEFAULT_C)
                await msg.edit(view=view)

                # sending message in chat
                options = []

                for c, i in enumerate(bot.mg.data.get('faq', [])):
                    options.append(discord.SelectOption(
                        label=i['name'], value=str(c), emoji=i['emoji']
                    ))

                view = to_view([
                    f'### 👋 Добро пожаловать, {ctx.author.name}!', SEP(),
                    'Первым делом советуем узнать больше о сервере, выбрав любой из пунктов FAQ ниже:',
                    ui.ActionRow(discord.ui.Select(
                        custom_id='faq',
                        options=options,
                        placeholder='Выбери страничку...'
                    )),
                    'Посмотреть их снова в любой момент можно по команде `ml!faq`.',
                    'Также можешь повыбирать себе ролей в <id:customize>.',
                    '-# И не забудь прочитать <#1364721575282217074>!'
                ], text=f'<@{ctx.author.id}>')

                channel = ctx.guild.get_channel(CHAT_CHANNEL)
                await channel.send(view=view)
                return
            
            view = to_view([
                '### 🧠 IQ-тест', SEP(),
                'IQ-тест не пройден.', SEP(visible=False),
                f'Вы написали: `{message.content}`',
                f'Нужно было написать: `{text}`',
                SEP(),
                'Попробуйте ввести команду ещё раз.'
            ], ERROR_C)
            await msg.edit(view=view)