
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
    apimessage = api.AIMessage(
        'user', utils.discord_message_to_text(message),
        message.author, url, reply_to, reply_images
    )

    # skip AI if message too long
    if len(apimessage.get_text()) > MAX_MESSAGE_LEN:
        log(f'AI message {message.id} from {message.author.id} too long', level=WARNING)
        await message.add_reaction(AI_TOOLONG)
        return

    if message.author.id in NERD_USERS:
        bot.mg.ai.add(api.AIMessage(
            'user', 'Ответь на это сообщение случайным оскорблением с кучей матов слов в 20')
        )
    else:
        bot.mg.ai.add(apimessage)

    # chceking if mlbot is being called for
    found_keyword = any([
        'млбот' in message.content.lower(),
        'mlbot' in message.content.lower(),
        'мл бот' in message.content.lower(),
        'джарвис' in message.content.lower(),
        'jarvis' in message.content.lower(),
        'grok' in message.content.lower(),
        'лоли' in message.content.lower(),
        'loli' in message.content.lower(),
    ])
    replied_to = actual_reply_to.author.id == bot.user.id if actual_reply_to else False
    
    # sending ai request
    if replied_to or found_keyword:
        log(f'Received AI prompt from {message.author.id} (msg {message.id}), image {url}')

        # nvm not sending ai request
        if bot.mg.generating:
            log('Already generating response', level=WARNING)
            await message.add_reaction(AI_RATELIMIT)
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
                
                await bot.webhook.send(username='Ошибка ИИ', avatar_url=ERROR_IMAGE, view=view, allowed_mentions=NO_MENTIONS)
            
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
        prompt='При необходимости можно установить свой системный промпт для ИИ.',
        ephemeral='Скрыть ли сообщение от других в канале (по умолчанию "Нет").'
    )
    @commands.cooldown(1, per=5, type=commands.BucketType.user)
    async def slash_ai(
        ctx: commands.Context,
        *,
        text: str,
        attachment: discord.Attachment = None,
        prompt: str = None,
        ephemeral: Literal['Да, скрыть сообщение от других', 'Нет, показать всем'] = 'Нет, показать всем'
    ):
        log(f'{ctx.author.id} asks AI thru command')

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=ephemeral.startswith('Д'))
        else:
            await ctx.channel.typing()

        if attachment is None and ctx.message.attachments:
            attachments = ctx.message.attachments
        elif attachment is None:
            attachments = []
        else:
            attachments = [attachment]

        # generating message
        try:
            prompt = PROMPT_COMMAND if prompt is None else prompt
            prompt_dict = {"role": "system", "content": prompt}

            if attachments:
                content = [
                    {'type': 'text', 'text': text}
                ]
                
                # downloading image
                async with aiohttp.ClientSession() as session:
                    for i in attachments:
                        async with session.get(i.url) as resp:
                            if resp.status != 200:
                                raise Exception(f"Failed to fetch image: {resp.status}")
                            
                            encoded_image = base64.b64encode(await resp.read()).decode('utf-8')
                            image_url = f"data:{resp.content_type};base64,{encoded_image}"
                            content.append({"type": "image_url", "image_url": {"url": image_url}})
            else:
                content = text

            text, image = await bot.mg.gen_ai([prompt_dict, {'role': 'user', 'content': content}])
            
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


    @bot.tree.context_menu(
        name='Объяснить сообщение',
    )
    async def cm_explain(
        inter: discord.Interaction, message: discord.Message,
    ):
        log(f'{inter.user.id} asks to explain message {message.id}')

        await inter.response.defer(ephemeral=True)
        attachments = message.attachments
        text = utils.discord_message_to_text(message)

        # generating message
        try:
            prompt = PROMPT_EXPLAIN
            prompt_dict = {"role": "system", "content": prompt}

            if attachments:
                content = [
                    {'type': 'text', 'text': text}
                ]
                
                # downloading image
                async with aiohttp.ClientSession() as session:
                    for i in attachments:
                        async with session.get(i.url) as resp:
                            if resp.status != 200:
                                raise Exception(f"Failed to fetch image: {resp.status}")
                            
                            encoded_image = base64.b64encode(await resp.read()).decode('utf-8')
                            image_url = f"data:{resp.content_type};base64,{encoded_image}"
                            content.append({"type": "image_url", "image_url": {"url": image_url}})
            else:
                content = text

            text, image = await bot.mg.gen_ai(
                [prompt_dict, {'role': 'user', 'content': content}]
            )
            
        except Exception as e:
            log(f'Error while generating AI response from {inter.user.id} (message {message.id}): {e}', level=ERROR)
            view = to_view([
                'Произошла ошибка во время генерации',
                SEP(),
                f'```{e}```'
            ], ERROR_C)
            await inter.followup.send(view=view)
            return
        
        # empty response
        if not text and not image:
            await inter.followup.send(random.choice(HANGUP_TEXTS))
            return

        # sending message
        try:
            file = discord.File(BytesIO(image), 'image.png') if image else None
            if not file:
                await inter.followup.send(content=text)
            else:
                await inter.followup.send(content=text, file=file)
        except Exception as e:
            log(f'Error while sending AI response from {inter.user.id} (message {message.id}): {e}', level=ERROR)

