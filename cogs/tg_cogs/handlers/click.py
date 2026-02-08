
import api
from log import *
from typing import *
from config import *
import utils
from .base import *


@command(['click'])
@in_group
async def click(messages: Messages):
    text = utils.gen_moan()
    out = await messages.message.reply(text)
    return [[out]]
