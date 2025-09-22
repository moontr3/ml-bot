
import random
import discord
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
            return

        # sending request
        async with message.channel.typing():
            bot.mg.generating = True
            try:
                response, image = await bot.mg.gen_ai()
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



async def setup(*args):
    return