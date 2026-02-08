
from log import *
from typing import *
from config import *
from .base import *


@command(['help','хелп','помощь'])
async def help(messages: Messages):
    text = f'<b><tg-emoji emoji-id="5406784743813451518">🌑</tg-emoji> Привет!</b>\n\n'\
        'Я - moonland bot, бот помогающий в управлении '\
            '<a href="https://ml.moontr3.ru/">Discord-сервера moonland</a>.\n\n'\
        'У нас есть <a href="https://t.me/moonlandre">Telegram-чат</a>, '\
            'в который пересылаются все сообщения с Discord-сервера и обратно.'

    if not messages.botuser:
        text += '\n\nВы можете связать свой Discord-аккаунт с Telegram-аккаунтом '\
            'зайдя на сервер, верифицировавшись и прописав соответствующую команду /link:'\
            '\n\n<b>https://ml.moontr3.ru/</b>\n\nХотя не знаю, будет ли кому-то не лень.'

    if messages.botuser:
        text += f'\n\n<b>Я вижу, твой аккаунт уже привязан к Discord. Круто!</b>'

    out = await messages.message.reply(
        text, link_preview_options=aiogram.types.LinkPreviewOptions(is_disabled=True)
    )
    return [[out]]
