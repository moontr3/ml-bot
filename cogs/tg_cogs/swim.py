
from copy import copy
import os
import random
from discord.ext import commands
import api
from log import *
from typing import *
from config import *
from aiogram import Router
import aiogram
from aiogram.filters import Command
from aiogram.utils import keyboard


# telegram bot

router = Router()
dcbot: commands.Bot = None
manager: api.Manager = None


def get_result(user: api.User) -> Tuple[str, str]:
    n = random.randint(1,9 if user and 'boots' in user.swiminv else 15)

    if n != random.randint(1,6):
        if user:
            return {
                None: '|Вы плывете| |✅|',
                'epstein': '|Вы гуляете| |✅|',
                'land': '|Вы идете| |✅|',
                '33': '|Вы крадетесь| |✅|'
            }[user.swimloc], 'discard'
        
        return '|Вы плывете| |✅|', 'discard'
    
    if not user:
        return random.choice([
            '|Вы сосете| |🍆|',
            '|Вы не плывете| |❌|',
            '|Вы сбросили якорь| |⚓️|',
            '|Вы на островке Эпштейна| |🏝️|',
            '|Что-то произошло| |❗️|',
            '|Вы на суше| |🏝️|',
            '|Новый предмет| |❕|',
            '|Вы нашли сапожки| |👢|',
            '|Вход в голосовой канал| |➡️|',
            '|Вы достали собаку из коробки| |🐕|',
            '|Вы утонули| |💀|'
        ]), 'discard'
    
    # user actions
    plist = [
        'random',
        'random',
        'random',
        'random',
        'random',
        'random',
        'loc',
        'anchor',
        'xp',
        'death'
    ]
    if 'boots' not in user.swiminv:
        plist.append('boots')
    
    if len(user.swiminv) < 4:
        plist.append('dog')

    if 'anchor' in user.swiminv:
        plist.append('loc')

    if 'dog' in user.swiminv:
        plist = ['dogeater']

    action = random.choice(plist)

    if action == 'random':
        texts = [
            '|Вы сосете| |🍆|',
            '|Вы не плывете| |❌|',
            '|Новый предмет| |❕|',
            '|Что-то произошло| |❗️|',
            '|Вход в голосовой канал| |➡️|',
        ]
        if user.swimloc == 'epstein':
            texts.append('|Вы Эпштейн| |✅|')

        return random.choice(texts), 'discard'
    
    # boots
    if action == 'boots':
        return '|Вы нашли сапожки| |👢|', 'boots'
        
    # death
    if action == 'death':
        return {
            None: '|Вы утонули| |💀|',
            'epstein': '|Вас отымел дядюшка Эпштейн| |💀|',
            'land': '|Вы задохнулись от жары| |💀|',
            '33': '|Вас обнаружили| |💀|'
        }[user.swimloc], 'death'

    # xp
    if action == 'xp':
        return '|Вы получили 1 XP| |✨|', 'xp'
        
    # dog
    if action == 'dog':
        return '|Вы достали собаку из коробки| |🐕|', 'dog'
    
    if action == 'dogeater':
        return '|Собакоедка съела вашу собаку| |🐕|', 'item:dog'
    
    # location
    if action == 'loc':
        if user.swimloc:
            return '|Вы снова плывёте| |✅|', 'loc'
        
        else:
            return random.choice([
                ('|Вы нашли островок Эпштейна| |🏝️|', 'cloc:epstein'),
                ('|Вы на суше| |🏝️|', 'cloc:land'),
                ('|Вы в убежище Совета| |🌑|', 'cloc:33'),
            ])
    
    # anchor
    if action == 'anchor':
        if 'anchor' in user.swiminv:
            return '|Вы сбросили якорь| |⚓️|', 'anchor'
        return '|Вы нашли якорь| |⚓️|', 'anchor'



@router.chosen_inline_result()
async def inline_result(q: aiogram.types.ChosenInlineResult):
    user = manager.get_user_by_tg(q.from_user.id)
    if not user: return

    if q.result_id == 'discard':
        if 'dog' in user.swiminv:
            manager.add_xp(user.id, 1, 'swimgame')

    elif q.result_id.startswith('cloc:'):
        loc = q.result_id.split(':')[1]
        manager.set_swimloc(user.id, loc)

    elif q.result_id == 'xp':
        manager.add_xp(user.id, 1, 'swimgame')

    elif q.result_id == 'loc':
        manager.set_swimloc(user.id, None)

    elif q.result_id.startswith('item:'):
        item = q.result_id.split(':')[1]
        if item == 'anchor':
            manager.set_swimloc(user.id, None)
        manager.remove_from_swiminv(user.id, item)

    elif q.result_id == 'dog':
        manager.add_to_swiminv(user.id, 'dog')

    elif q.result_id == 'boots':
        manager.add_to_swiminv(user.id, 'boots')

    elif q.result_id == 'death':
        manager.set_swiminv(user.id, [])
        manager.set_swimloc(user.id, None)

    elif q.result_id == 'anchor':
        if 'anchor' in user.swiminv:
            manager.remove_from_swiminv(user.id, 'anchor')
        else:
            manager.add_to_swiminv(user.id, 'anchor')


@router.inline_query()
async def inline(q: aiogram.types.InlineQuery):
    user = manager.get_user_by_tg(q.from_user.id)
    result, result_key = get_result(user)

    desc = 'Нажми чтобы плыть'
    if user and user.swimloc:
        desc = manager.data['swimloc'][user.swimloc]['name']

    items = []
    if user:
        for index, i in enumerate(user.swiminv):
            item = manager.data['swim'][i]
            items.append(
                aiogram.types.InlineQueryResultArticle(id=f'item:{i}:{index}',
                    title=item['emoji'] + ' ' + item['name'],
                    description=item['desc'],
                    input_message_content=aiogram.types.InputTextMessageContent(
                        message_text=manager.data['swim'][i]['text']
                    )
                )
            )

    kb = keyboard.InlineKeyboardBuilder()
    kb.add(aiogram.types.InlineKeyboardButton(
        text='Плыть', switch_inline_query_current_chat=''
    ))

    await q.answer([
        aiogram.types.InlineQueryResultArticle(id=result_key,
            title='⚓ Плыть',
            description=desc,
            input_message_content=aiogram.types.InputTextMessageContent(
                message_text=result,
            ),
            reply_markup=kb.as_markup()
        ),
        *items
    ], cache_time=1, is_personal=True)