
from copy import deepcopy
from discord.ext import commands
import api
from log import *
from typing import *
from config import *
import aiogram


class Messages:
    def __init__(self,
        messages: List[aiogram.types.Message],
        bot: commands.Bot,
        mg: api.Manager
    ):
        self.messages: List[aiogram.types.Message] = messages
        self.message = aiogram.types.Message = messages[0]
        self.dcbot: commands.Bot = bot
        self.mg: api.Manager = mg

        self.bot = messages[0].bot
        self.chat_id = messages[0].chat.id
        self.user = messages[0].from_user
        self.botuser = mg.get_user_by_tg(self.user.id) if self.user else None
        self.content: str = '\n'.join([i.text or i.caption for i in messages if i.text or i.caption])
        self.is_bot = any([i.from_user.is_bot for i in messages if i.from_user])
        self.is_forwarded = any([i.forward_date for i in messages])


# decorators

def linked_user(func):
    async def wrapper(message: Messages, *args, **kwargs):
        # check for linked user
        if not message.botuser:
            # sending error message
            out = await message.message.reply(
                '<b>Аккаунт не привязан!</b>\n\n'\
                    'Зайди на наш Discord-сервер - <b>ml.moontr3.ru</b> - '\
                    'и привяжи свой Discord-аккаунт при помощи команды /link'
            )
            return [[out]]

        result = await func(message, *args, **kwargs)
        return result

    return wrapper


def in_group(func):
    async def wrapper(message: Messages, *args, **kwargs):
        # check for linked user
        if message.chat_id not in COMMAND_TG_CHATS:
            return None

        result = await func(message, *args, **kwargs)
        return result

    return wrapper


def command(texts: List[str]):
    def decorator(func):
        async def wrapper(message: Messages, *args, **kwargs):
            # check for text
            words = message.content.split()
            if not words:
                return

            # checking for prefix
            word = words[0].lower()
            new = deepcopy(word)

            for i in PREFIXES+['/']:
                new = word.removeprefix(i)
                if new != word:
                    break
            else:
                return

            # removing username
            word = new.removesuffix(f'@{TG_BOT_USERNAME}')

            # checking
            if word not in texts:
                return

            # processing
            result = await func(message, *args, **kwargs)
            return result

        return wrapper
    return decorator
