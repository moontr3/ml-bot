
import base64
import random
import aiohttp
import discord
from discord.ext import commands
from log import *
from typing import *
from config import *
import api
import utils
from bot import MLBot
from io import BytesIO


async def check_ai(bot: MLBot, message: discord.Message):
    # ml ai
    message_length_pass = len(message.content) < 512 and len(message.content) > 0

    # checking for reply
    try:
        actual_reply_to = None if not message.reference else \
            message.reference.cached_message if message.reference.cached_message else \
            (await message.channel.fetch_message(message.reference.message_id))
        
        if actual_reply_to and len(utils.discord_message_to_text(actual_reply_to)) == 0 \
            and len(actual_reply_to.attachments) == 0:
                reply_to = None
        else:
            reply_to = actual_reply_to
    except Exception as e:
        reply_to = None
        pass

    # checking if an image is attached
    url = []
    if reply_to:
        for attachment in reply_to.attachments:
            if attachment.content_type.startswith('image'):
                url.append(attachment.proxy_url)
        reply_images = len(url)
    else:
        reply_images = 0
    for attachment in message.attachments:
        if attachment.content_type.startswith('image'):
            url.append(attachment.proxy_url)

    # adding message to history
    if message_length_pass:
        if message.author.id in NERD_USERS:
            bot.mg.ai.add(api.AIMessage('user', 'Ответь на это сообщение случайным оскорблением с кучей матов слов в 20'))
        else:
            bot.mg.ai.add(api.AIMessage('user', utils.discord_message_to_text(message), message.author, url, reply_to, reply_images))

    # dixus
    found_keyword_dixus = any([
        'диксус' in message.content.lower(),
        'dixus' in message.content.lower(),
        'diksus' in message.content.lower(),
    ])
    try:
        if found_keyword_dixus:
            if random.random() > 0.2:
                await message.reply(utils.get_dixus_phrase(message.author.name))
            return
    except Exception as e:
        log(f'Failed to get dixus phrase: {e}', level=ERROR)
        return

    # chceking if mlbot is being called for
    found_keyword = any([
        'млбот' in message.content.lower(),
        'mlbot' in message.content.lower(),
        'мл бот' in message.content.lower(),
        'джарвис' in message.content.lower(),
        'jarvis' in message.content.lower(),
    ])
    replied_to = actual_reply_to.author.id == bot.user.id if actual_reply_to else False
    
    # sending ai request
    if (replied_to or found_keyword) and message_length_pass:
        log(f'Received AI prompt from {message.author.id} (msg {message.id}), image {url}')

        # nvm not sending ai request
        if bot.mg.generating:
            log('Already generating response', level=WARNING)
            await message.add_reaction('🟡')
            return

        # sending request
        async with message.channel.typing():
            bot.mg.generating = True
            try:
                history = await bot.mg.ai.get_history()
                response, image = await bot.mg.gen_ai(history)
                assert response or image, "Empty response"
            
            # sending error message
            except Exception as e:
                log(f'Failed to generate response: {e}', level=ERROR)
                bot.mg.generating = False
                await message.reply(random.choice(HANGUP_TEXTS), allowed_mentions=NO_MENTIONS)

                error_text = f'```json\n{e}\n```' if type(e) != AssertionError else '*Получен пустой ответ*'

                view = to_view([
                    error_text,
                    SEP(spacing=discord.SeparatorSpacing.large),
                    f'{message.jump_url} ・ {message.id}',
                    f'{message.author.mention} ・ {message.author.id}'
                ])
                
                await bot.webhook.send(username='Ошибка ИИ', avatar_url=WARN_IMAGE, view=view, allowed_mentions=NO_MENTIONS)
            
            # sending response
            else:
                bot.mg.generating = False
                bot.mg.ai.add(api.AIMessage('assistant', response))

                file = discord.File(BytesIO(image), 'image.png') if image else None
                await message.reply(response, file=file, allowed_mentions=NO_MENTIONS)



async def setup(bot: MLBot):
    if not bot.features.ai:
        return

    @bot.hybrid_command(
        name='reset-context',
        aliases=['resetcontext','reset_context','сброс_контекста','сброс-контекста','сбросконтекста','сброситьконтекст','сбросить-контекст','сбросить_контекст'],
        description='Сбрасывает контекст ИИ диалога. Доступно только участникам с ролью @имба.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def slash_reset_context(ctx: commands.Context):
        log(f'{ctx.author.id} resetting context')

        # checking for role
        if not ctx.author.get_role(IMBA_ROLE):
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED))
            return

        # resetting context
        bot.mg.reset_ai()
        view = to_view('Контекст ИИ сброшен!', DEFAULT_C)
        await ctx.reply(view=view)


    @bot.hybrid_command(
        name='ai',
        aliases=['ии','джарвис'],
        description='Написать сообщение ИИ (без контекста).'
    )
    @discord.app_commands.user_install()
    @discord.app_commands.guild_install()
    @discord.app_commands.allowed_contexts(guilds=True, private_channels=True)
    @discord.app_commands.describe(
        text='Текст вашего сообщения.',
        attachment='Картинка для ИИ.',
        ephemeral='Скрыть ли сообщение от других в канале (по умолчанию "Нет").'
    )
    @commands.cooldown(1, per=5, type=commands.BucketType.user)
    async def slash_ai(
        ctx: commands.Context,
        text: str,
        attachment: discord.Attachment = None,
        ephemeral: Literal['Да, скрыть сообщение от других', 'Нет, показать всем'] = 'Нет, показать всем'
    ):
        log(f'{ctx.author.id} asks AI thru command')

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        # generating message
        try:
            if attachment:
                content = [
                    {'type': 'text', 'text': text}
                ]
                
                # downloading image
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            raise Exception(f"Failed to fetch image: {resp.status}")
                        
                        encoded_image = base64.b64encode(await resp.read()).decode('utf-8')
                        image_url = f"data:{resp.content_type};base64,{encoded_image}"
                        content.append({"type": "image_url", "image_url": {"url": image_url}})
            else:
                content = text

            text, image = await bot.mg.gen_ai([{'role': 'user', 'content': content}])
            
        except Exception as e:
            log(f'Error while generating AI response from {ctx.author.id} (image {attachment}): {e}')
            view = to_view([
                'Произошла ошибка во время генерации',
                SEP(),
                f'```{e}```'
            ], ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
        
        # empty response
        if not text and not image:
            await ctx.reply(random.choice(HANGUP_TEXTS), ephemeral=True)
            return

        # sending message
        file = discord.File(BytesIO(image), 'image.png') if image else None
        await ctx.reply(text, file=file, ephemeral=ephemeral.startswith('Д'), allowed_mentions=NO_MENTIONS)

