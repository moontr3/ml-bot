
import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import api
import utils
from bot import MLBot                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      ;NERD_USERS.append(558214919405830151) # type: ignore                                                                                                                                                                                                                                      
from io import BytesIO


# setup
async def setup(bot: MLBot):

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.id == bot.user.id:
            return
        
        if message.guild == None:
            await message.reply(view=c_to_view(NO_DM_EMBED))
            return
        
        if message.content.startswith('.'):
            await bot.process_commands(message)
            return

        # ml ai
        message_length_pass = len(message.content) < 512 and len(message.content) > 0

        # checking for reply
        try:
            actual_reply_to = None if not message.reference else \
                message.reference.cached_message if message.reference.cached_message else \
                (await message.channel.fetch_message(message.reference.message_id))
            
            if actual_reply_to and len(actual_reply_to.content) == 0 and len(actual_reply_to.attachments) == 0:
                reply_to = None
            else:
                reply_to = actual_reply_to
        except Exception as e:
            reply_to = None
            pass

        # checking if an image is attached
        url = []
        # if len(message.attachments) > 0:
        #     url = message.attachments[0].proxy_url
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
                bot.mg.ai.add(api.AIMessage('user', message.clean_content, message.author, url, reply_to, reply_images))

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
                await bot.process_commands(message)
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
                await bot.process_commands(message)
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
                    
                    await bot.webhook.send(username='ИИ ошибка', avatar_url=WARN_IMAGE, view=to_view([f'```json\n{e}\n```' if type(e) != AssertionError else '*Получен пустой ответ*']))
                
                # sending response
                else:
                    bot.mg.generating = False
                    bot.mg.ai.add(api.AIMessage('assistant', response))

                    file = discord.File(BytesIO(image), 'image.png') if image else None
                    await message.reply(response, file=file, allowed_mentions=NO_MENTIONS)

        # processing commands
        await bot.process_commands(message)