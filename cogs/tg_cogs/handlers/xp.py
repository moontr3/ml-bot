
import api
from log import *
from typing import *
from config import *
import os
from .base import *


@command(['xp','опыт'])
@in_group
@linked_user
async def xp(messages: Messages):
    path = messages.mg.crenderer.user_xp(messages.mg, messages.botuser)
    out = await messages.message.reply_photo(aiogram.types.FSInputFile(path))
    os.remove(path)

    return [[out]]


@command(['skins','скины'])
@in_group
@linked_user
async def skins(messages: Messages):
    path = messages.mg.crenderer.skin_list(messages.mg, messages.botuser)
    out = await messages.message.reply_photo(aiogram.types.FSInputFile(path))
    os.remove(path)

    return [[out]]
