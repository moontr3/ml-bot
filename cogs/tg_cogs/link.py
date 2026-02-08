from discord.ext import commands
import api
from log import *
from typing import *
from config import *
from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
import aiogram


# telegram bot

router = Router()
dcbot: commands.Bot = None
manager: api.Manager = None


async def do_swim(message: aiogram.types.Message):
    user = manager.get_user_by_tg(message.from_user.id)

    text = f'<b>👋 Привет!</b>\n\n'\
        'Если вкратце, я - бот, помогающий в управлении '\
            '<a href="https://ml.moontr3.ru/">Discord-сервера moonland</a>.\n'\
        'У нас есть <a href="https://t.me/moonlandre">Telegram-чат</a>, '\
            'в который пересылаются все сообщения с Discord-сервера и обратно.\n\n'\
        '<b>То, до куда ты сейчас добрался - это рофляная мини-игра "Плыть".</b>\n\n'\

    if user:
        text += f'Так как у тебя уже привязан Discord-аккаунт, в этой мини-игре '\
            'ты можешь реально собирать и использовать предметы и перемещаться по локациям.\n\n'\
            'Если бы ты не привязывал аккаунт, то всё, что бы делала эта мини-игра - это '\
            'показывала рандомные фразы.'

    else:
        text += 'Сейчас тебе доступна только "базовая" версия этой игры - '\
            'всё, что она делает, это показывает случайные фразы, от которых ничего не меняется.\n'\
            'Если ты зайдёшь на наш Discord-сервер и привяжешь свой аккаунт, то '\
            'тебе откроется возможность собирать и использовать предметы, '\
            'перемещаться по локациям, и иногда даже получать серверный опыт.\n\n'\
            f'<b>Подробности о привязке посмотри в /help.</b>'

    await message.reply(text, link_preview_options=aiogram.types.LinkPreviewOptions(is_disabled=True))


@router.message(CommandStart(True))
async def on_message(message: aiogram.types.Message, command: CommandObject):
    if not command.args:
        return

    code = command.args
    if code == 'swim':
        await do_swim(message)
        return

    user = manager.confirm_tg_link_key(message.from_user.id, code)

    if not user:
        return

    name = dcbot.get_user(user.id)
    usertext = ''
    if name:
        usertext = f'\n\n<b>{name.name}</b>, верно?'

    # confirming
    await message.reply(
        f'<b>👋 Привет!</b>{usertext}\n\nТеперь твои аккаунты успешно связаны.'\
        '\nОтвязать можно по команде <b>ml!link</b> в Discord.'
    )



@router.message(Command('link'))
async def on_message(message: aiogram.types.Message):
    if message.chat.type != 'private':
        return

    if len(message.text.split()) != 2:
        return

    code = message.text.split()[1]
    user = manager.confirm_tg_link_key(message.from_user.id, code)

    if not user:
        return

    name = dcbot.get_user(user.id)
    usertext = ''
    if name:
        usertext = f'\n\n<b>{name.name}</b>, верно?'

    # confirming
    await message.reply(
        f'<b>👋 Привет!</b>{usertext}\n\nТеперь твои аккаунты успешно связаны.'\
        '\nОтвязать можно по команде <b>ml!link</b> в Discord.'
    )
