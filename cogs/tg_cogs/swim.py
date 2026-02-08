import random
from aiogram.types.inline_query_results_button import InlineQueryResultsButton
from discord.ext import commands
import api
from log import *
from typing import *
from config import *
from aiogram import Router
import aiogram
from aiogram.utils import keyboard


# telegram bot

router = Router()
dcbot: commands.Bot = None
manager: api.Manager = None


def get_result(user: api.User | None) -> Tuple[str, str]:
    chance = 15

    if user:
        for i in range(user.swiminv.count('boots')):
            chance /= 1.5

    n = int(random.uniform(1,chance))

    if n != 1:
        if user and user.swimloc:
            return manager.data['swimloc'][user.swimloc]['text'], 'discard'

        return '|Вы плывете| |✅|', 'discard'

    if not user:
        return random.choice([
            '|You swim| |✅|',
            '|Переход в огрызок| |🔀|',
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
            '|Саксофон упал с неба| |🎷|',
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
        'random',
        'loc',
        'xp',
        'death'
    ]

    if len(user.swiminv) < 4:
        plist.append('dog')
        plist.append('sax')
        plist.append('anchor')
        plist.append('box')
        plist.append('boots')

    if len(user.swiminv) > 0:
        plist.append('tax')

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
            '|You swim| |✅|',
            '|Многоходовочка| |🔀|'
        ]
        if user.id == 736244361951576159:
            texts.append('|Вы Вексурем| |✅|')
        if user.swimloc == 'epstein':
            texts.append('|Вы Эпштейн| |✅|')

        return random.choice(texts), 'discard'

    # boots
    if action == 'boots':
        return '|Вы нашли сапожки| |👢|', 'boots'

    # tax
    if action == 'tax':
        item = random.choice(user.swiminv)
        itemdata = manager.data['swim']['item']['name']
        return f'|Путин наложил налог на {itemdata}| |🇷🇺|', f'ritem:{item}'

    # death
    if action == 'death':
        if user and user.id == 1134429503985291284:
            return '|Вы ослепли| |💀|', 'death'

        if user and user.swimloc:
            return manager.data['swimloc'][user.swimloc]['death'], 'death'

        return '|Вы утонули| |💀|', 'death'

    # xp
    if action == 'xp':
        return '|Вы получили 1 XP| |✨|', 'xp'

    # dog
    if action == 'dog':
        return '|Вы достали собаку из коробки| |🐕|', 'dog'

    if action == 'dogeater':
        if random.choice([True, False]):
            return '|Собакоедка съела вашу собаку| |🐕|', 'item:dog'
        else:
            return '|Вы съели собакоедку| |🐕|', 'dogeater'

    # sax
    if action == 'sax':
        return '|Саксофон упал с неба| |🎷|', 'sax'

    # box
    if action == 'box':
        return '|Вы нашли бокс| |📦|', 'box'

    # location
    if action == 'loc':
        if user.swimloc:
            return '|Вы снова плывёте| |✅|', 'loc'

        else:
            return random.choice([
                ('|Вы нашли островок Эпштейна| |🏝️|', 'cloc:epstein'),
                ('|Вы на суше| |🏝️|', 'cloc:land'),
                ('|Вы в убежище Совета| |🌑|', 'cloc:33'),
                ('|Вы прилетели на Марс| |🔴|', 'cloc:mars'),
                ('|Переход в огрызок| |🔀|', 'cloc:vc'),
            ])

    # anchor
    if action == 'anchor':
        if 'anchor' in user.swiminv:
            return '|Вы сбросили якорь| |⚓️|', 'anchor'
        return '|Вы нашли якорь| |⚓️|', 'anchor'


def action(text: str, user):
    if text.startswith('cloc:'):
        loc = text.split(':')[1]
        manager.set_swimloc(user.id, loc)

    elif text == 'box':
        manager.add_to_swiminv(user.id, 'box')

    elif text == 'xp':
        manager.add_xp(user.id, 1, 'swimgame')

    elif text == 'loc':
        manager.set_swimloc(user.id, None)

    elif text.startswith('ritem:'):
        item = text.split(':')[1]
        manager.remove_from_swiminv(user.id, item)

    elif text.startswith('item:'):
        item = text.split(':')[1]
        manager.remove_from_swiminv(user.id, item)

        if item == 'anchor':
            manager.set_swimloc(user.id, None)

        if item == 'box':
            manager.remove_from_swiminv(user.id, 'box')
            t = random.choice([
                'cloc:land',
                'cloc:epstein',
                'cloc:33',
                'cloc:mars',
                'cloc:vc',
                'xp',
                'loc',
                'dog',
                'sax',
                'boots',
                'death',
                'anchor'
            ])
            action(t, user)

    elif text == 'dog':
        manager.add_to_swiminv(user.id, 'dog')

    elif text == 'dogeater':
        manager.remove_from_swiminv(user.id, 'dog')
        manager.add_to_swiminv(user.id, 'dogeater')

    elif text == 'sax':
        manager.add_to_swiminv(user.id, 'sax')

    elif text == 'boots':
        manager.add_to_swiminv(user.id, 'boots')

    elif text == 'death':
        manager.set_swiminv(user.id, [])
        manager.set_swimloc(user.id, None)

    elif text == 'anchor':
        if 'anchor' in user.swiminv:
            manager.remove_from_swiminv(user.id, 'anchor')
        else:
            manager.add_to_swiminv(user.id, 'anchor')


@router.chosen_inline_result()
async def inline_result(q: aiogram.types.ChosenInlineResult):
    user = manager.get_user_by_tg(q.from_user.id)
    if not user:
        return

    if q.result_id == 'discard':
        if 'dog' in user.swiminv:
            manager.add_xp(user.id, 1, 'swimgame')
        return

    action(q.result_id, user)


@router.inline_query()
async def inline(q: aiogram.types.InlineQuery):
    user = manager.get_user_by_tg(q.from_user.id)
    result, result_key = get_result(user)

    # sax
    if user:
        for i in range(user.swiminv.count('sax')):
            sax = random.choice(manager.data['swimsax'])
            result += f'\n|{sax}| |🎷|'

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
    ], button=InlineQueryResultsButton(
        text='Что это?', start_parameter='swim'
    ) if not user else None, cache_time=0, is_personal=True)
