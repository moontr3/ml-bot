
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import api
import utils


# setup
async def setup(bot: commands.Bot):

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if message.guild == None:
            await message.reply(view=c_to_view(NO_DM_EMBED))
            return
        
        if message.content.startswith('.'):
            await bot.process_commands(message)
            return

        # ml ai
        message_length_pass = len(message.content) < 512 and len(message.content) > 0
        try:
            reply_to = None if not message.reference else \
                message.reference.cached_message if message.reference.cached_message else \
                (await message.channel.fetch_message(message.reference.message_id))
            
            if len(reply_to.content) == 0:
                reply_to = None
        except:
            pass

        url = None
        if len(message.attachments) > 0:
            url = message.attachments[0].proxy_url

        if message_length_pass:
            if message.author.id in NERD_USERS:
                bot.mg.ai.add(api.AIMessage('user', 'Ответь на это сообщение случайным оскорблением с кучей матов слов в 20'))
            else:
                bot.mg.ai.add(api.AIMessage('user', message.content, message.author, url, reply_to))
        
        found_keyword = any([
            'млбот' in message.content.lower(),
            'mlbot' in message.content.lower(),
            'как' in message.content.lower(),
            'мл бот' in message.content.lower(),
            'ии' in message.content.lower(),
        ])
        if (bot.user in message.mentions or found_keyword) and message_length_pass:
            log(f'Received AI prompt from {message.author.id} (msg {message.id}), image {url}')

            if bot.mg.generating:
                log('Already generating response', level=WARNING)
                await bot.process_commands(message)
                return

            async with message.channel.typing():    
                bot.mg.generating = True
                try:
                    response = await bot.mg.gen_ai()
                    assert response
                except Exception as e:
                    log(f'Failed to generate response: {e}', level=ERROR)
                    bot.mg.generating = False
                else:
                    bot.mg.generating = False
                    bot.mg.ai.add(api.AIMessage('assistant', response))

                    view = ui.LayoutView()
                    view.add_item(ui.TextDisplay(response))
                    await message.reply(view=view)

        # processing commands
        await bot.process_commands(message)