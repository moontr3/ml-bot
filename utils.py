import random
import re
from typing import *

import aiogram
from config import *
import datetime
import time
from aiogram.utils import formatting
from log import *

# functions

def seconds_from_string(string:str) -> "Tuple[int,str,float|int] | None":
    '''
    Parses the string aka 10d, 3m and converts it to the
    amount of seconds.

    Returns None if unable to parse the string.

    Returns an integer as the amount of seconds,
    a string for the unit name and a float for the
    original provided amount.
    '''
    string = string.replace(' ','')
    
    amount = string[0:-1]
    try:
        amount = float(amount)
        if amount == int(amount):
            amount = int(amount)
    except:
        return None

    try:
        unit = UNITTABLE[string[-1]]
        unit_name = UNITNAMES[string[-1]]
    except:
        return None
    
    return int(amount*unit), unit_name, amount
    

def remove_md(string:str, escape_spoilers:bool=False) -> str:
    '''
    Escapes any markdown symbols.
    '''
    string = string.replace('\\', '\\\\') # confusing af 
    string = string.replace('*', '\\*')
    string = string.replace('_', '\\_')
    string = string.replace('~', '\\~')
    if escape_spoilers:
        string = string.replace('|', '\\|')

    return string

def datetime_to_text(time:datetime.datetime) -> str:
    '''
    Converts a datetime.datetime object into a neat string eg.

    11 Sep 2011, 14:22:16, Wed
    '''
    month = [
        'Янв','Фев','Мар','Апр','Май','Июн',
        'Июл','Авг','Сен','Окт','Ноя','Дек'
    ][time.month-1]
    weekday = [
        'Пн','Вт','Ср','Чт','Пт','Сб','Вс'
    ][time.weekday()]

    text = f'{time.day} {month} {time.year}, '\
        f'{time.hour}:{time.minute}:{time.second}'

    return


def random_color(lightness:int, min:int=0) -> Tuple[int,int,int]:
    return (
        random.randint(min,lightness),
        random.randint(min,lightness),
        random.randint(min,lightness)
    )


def lerp(a:float, b:float, t:float) -> float:
    '''
    Interpolates between A and B.
    '''
    t = max(0,min(1,t))
    return (1 - t) * a + t * b


def rand_id(k:int=4) -> str:
    '''
    Generates a random unique (probably) hexadecimal string that can be used as an ID.
    '''
    timestamp = str(int(time.time())) # unique timestamp that changes every second and never repeats after
    random_part = "".join(random.choices('0123456789', k=k)) # randomly generated string to add
                                                             # after the timestamp
    string = hex(int(timestamp+random_part))[2:] # converting the number to hex to make it shorter
    return string


def get_lb_badge(lb: Literal['alltime','season','week','day','vc','stream','mic','q','rep'], active:bool) -> str:
    if active:
        return {
            'alltime': '<:alls1:1356271223797055589><:alls2:1356271234538537151>',
            'season': '<:res1:1356271306550804651><:res2:1356271316600225892>',
            'week': '<:weeks1:1356271350347464795><:weeks2:1356271360074059776>',
            'day': '<:days1:1356271265547161622><:days2:1356271276498354307>',
            'vc': '<:vcs1:1358204944313876531><:vcs2:1358204964878553290>',
            'stream': '<:streams1:1358204814428864722><:streams2:1358204834603470868>',
            'mic': '<:mics1:1358204722489725079><:mics2:1358204738709098576>',
            'q': '<:qs:1372921547848683530>',
            'rep': '<:reps1:1379468318955540613><:reps2:1379468331622334615>'
        }[lb]
    else:
        return {
            'alltime': '<:alld1:1356271199851774023><:alld2:1356271213231476887>',
            'season': '<:red1:1356271286749233232><:red2:1356271296434016518>',
            'week': '<:weekd1:1356271326737858590><:weekd2:1356271336707588159>',
            'day': '<:dayd1:1356271244537888858><:dayd2:1356271255099146407>',
            'vc': '<:vcd1:1358204910952386791><:vcd2:1358204927402578023>',
            'stream': '<:streamd1:1358204762302185492><:streamd2:1358204798477795528>',
            'mic': '<:micd1:1358204688851533874><:micd2:1358204705813172376>',
            'q': '<:qd:1372921533311352923>',
            'rep': '<:repd1:1379468281676828774><:repd2:1379468300563513427>'
        }[lb]


def month_name(month:int) -> str:
    return [
        'Январь','Февраль','Март','Апрель','Май','Июнь',
        'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'
    ][month]


def shorten_number(num:int) -> str:
    sizes = ['', 'k','m','b','t']

    i = 0
    while num >= 1000 and i < len(sizes)-1:
        num /= 1000
        i += 1

    ptnum = f'{num:.1f}' if num < 100 else f'{int(num)}'

    return f'{ptnum if i != 0 else num}{sizes[i]}'


def get_datetime(date: str) -> datetime.datetime:
    year = datetime.datetime.now(datetime.timezone.utc).year
    try:
        return datetime.datetime.strptime(date, '%Y.%m')
    except:
        try:
            return datetime.datetime.strptime(date, '%m.%Y')
        except:
            try:
                return datetime.datetime.strptime(date+f'.{year}', '%m.%Y')
            except:
                months = [
                    'янв', 'фев', 'мар', 'апр', 'май', 'июн',
                    'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'
                ]
                
                if date.lower()[:3] in months:
                    try:
                        return datetime.datetime.strptime(
                            str(months.index(date.lower()[:3])+1)+f'.{year}', '%m.%Y'
                        )
                    except:
                        return None
                    

def to_cool_numbers(string: str) -> str:
    string = str(string)
    out = ''

    for i in string:
        out += COOL_NUMBERS.get(i, i)
    
    return out


def get_word(exclude:List[str]):
    '''
    Returns a random word.
    '''
    word = random.choice(LIKEE_WORDS)
    while word in exclude:
        word = random.choice(LIKEE_WORDS)
    return word

def get_likee():
    '''
    Returns a message string with emojis.
    '''
    # words
    words_amount = 1
    # the increasing will go slower the more there are words
    while words_amount < WORD_MAX_AMOUNT\
    and random.random() < WORD_ADDING_THRESHOLD:
        words_amount += 1

    words = []
    for i in range(words_amount):
        words.append(get_word(words))

    words = ' '.join(words)

    # emojis
    emojis_amount = 1
    # the increasing will go slower the more there are words
    while emojis_amount < EMOJIS_MAX_AMOUNT\
    and random.random() < EMOJIS_ADDING_THRESHOLD:
        emojis_amount += 1

    emojis = random.choice(LIKEE_EMOJI)*emojis_amount

    # returning the result
    return words+emojis


def get_faq_view_items(i: dict) -> list:
    items = []
    items.append(f'### {i["emoji"]} {i["name"]}')

    for element in i['contents'].split('\n\n'):
        if element == '[SEP]':
            items.append(SEP())
            continue

        items.append(element)

    return items


def get_faq_preview_view_items(i: list) -> list:
    items = []

    for element in i:
        if element is None:
            items.append(SEP())
            continue

        if element['button'] is None:
            items.append(ui.TextDisplay(element['text']))
            continue

        if isinstance(element['button']['page'], int):
            button = ui.Button(
                label=element['button']['label'],
                custom_id=f'faq:{element["button"]["page"]}'
            )
        else:
            button = ui.Button(
                label=element['button']['label'],
                url=element["button"]["page"]
            )

        c = ui.Section(
            ui.TextDisplay(element['text']),
            accessory=button
        )

        items.append(c)

    return items


def get_revolver_image(left: int) -> str:
    return f'https://moontr3.ru/assets/r/l{left}.png'


def get_revolver_endgame_image(left: int) -> str:
    return f'https://moontr3.ru/assets/r/d{left}.png'


def truncate(string: str, length: int) -> str:
    if len(string) > length:
        return string[:length-3] + '...'
    return string


def resolve_component_tree(message: discord.Message, components: List) -> str:
    text = ''

    for i in components:
        if hasattr(i, 'content'):
            text += "\n"+discord_clean_content(
                message.guild, message.mentions, message.role_mentions, i.content
            )

        elif hasattr(i, 'children'):
            text += "\n"+resolve_component_tree(message, i.children)

        elif hasattr(i, '_children'):
            text += "\n"+resolve_component_tree(message, i._children)

        elif isinstance(i, discord.SeparatorComponent):
            text += "\n"

    return text


def discord_message_to_text(message: discord.Message) -> str:
    clean_text = message.clean_content
    clean_text += resolve_component_tree(message, message.components)
    clean_text = clean_text.strip()
    return clean_text


#### stolen from discord.py

def discord_clean_content(
    guild: discord.Guild | None,
    mentions: List[discord.User | discord.Member],
    role_mentions: List[discord.Role],
    content: str
) -> str:
    if guild:
        def resolve_member(id: int) -> str:
            m = guild.get_member(id) or utils.get(mentions, id=id)  # type: ignore
            return f'@{m.display_name}' if m else '@deleted-user'

        def resolve_role(id: int) -> str:
            r = guild.get_role(id) or utils.get(role_mentions, id=id)  # type: ignore
            return f'@{r.name}' if r else '@deleted-role'

        def resolve_channel(id: int) -> str:
            c = guild._resolve_channel(id)  # type: ignore
            return f'#{c.name}' if c else '#deleted-channel'

    else:
        def resolve_member(id: int) -> str:
            m = discord.utils.get(mentions, id=id)
            return f'@{m.display_name}' if m else '@deleted-user'

        def resolve_role(id: int) -> str:
            return '@deleted-role'

        def resolve_channel(id: int) -> str:
            return '#deleted-channel'

    transforms = {
        '@': resolve_member,
        '@!': resolve_member,
        '#': resolve_channel,
        '@&': resolve_role,
    }

    def repl(match: re.Match) -> str:
        type = match[1]
        id = int(match[2])
        transformed = transforms[type](id)
        return transformed

    result = re.sub(r'<(@[!&]?|#)([0-9]{15,20})>', repl, content)

    return discord.utils.escape_mentions(result)


def get_random_word() -> str:
    '''
    Returns a random word from a file.
    '''
    with open(WORD_LIST, encoding='utf-8') as f:
        data = f.read()

    return random.choice(data.split('\n'))


def get_dixus_phrase(username: str) -> "str | None":
    # "bitten" thingie
    if random.random() > 0.6:
        word = get_random_word()
        username = remove_md(username)

        return f'{username} надеюсь тя {word} укусит) ты же их так любишь))'
    
    # i'm an old
    else:
        phrases = [
            'я тут олд',
            'я олд',
            'я вообще то олд)',
            'я олд тут',
            'вообще я олд',
            'я олд))',
            'я тут олд)',
        ]
        phrases2 = [
            'ты не зн ничего',
            'ты ниче не знаешь',
            'ниче ты не знаешь',
            'ты не знаешь ничего)',
            'ты ничего не знаешь)',
            'ты ничего не знаешь',
            'ты не знаешь ниче)',
            'ничего ты не знаешь))',
        ]
        chosen = [
            random.choice(phrases),
            random.choice(phrases2),
        ]
        random.shuffle(chosen)

        if random.random() > 0.7:
            chosen.pop(0)

        sep = random.choice([' ',',',', '])
        
        return sep.join(chosen)
    

def get_preview_dc_message_text(message: discord.Message) -> str:
    clean_text = discord_message_to_text(message)
    clean_text = truncate(clean_text.replace('\n', ' '), 50)

    return clean_text
    

def get_preview_tg_message_text(content: str) -> str:
    clean_text = remove_md(content)
    clean_text = truncate(clean_text.replace('\n', ' '), 50)

    return clean_text
    

def get_dc_message_text(message: discord.Message, pair: Dict) -> str:
    '''
    Returns message text and keyboard markup, if there should be one.
    '''
    # text
    clean_text = discord_message_to_text(message)
    clean_text = formatting.Text(clean_text).as_markdown()

    if pair['show_user']:
        name = message.author.name.replace("_", "\\_")
        isbot = '🤖 ' if message.author.bot else ''
        text = f'{isbot}`{name}` 　 {clean_text}'
    else:
        text = clean_text

    return text


def get_tg_message_view(
    messages: List[aiogram.types.Message],
    pair: Dict,
    webhook: str,
    manager,
    gallery: ui.MediaGallery,
) -> ui.LayoutView:
    '''
    Generates a Discord Components V2 view from a list of Telegram messages.
    '''
    view = ui.LayoutView()

    # variables
    chat_id = messages[0].chat.id
    user = messages[0].from_user
    content = '\n'.join([i.text or i.caption for i in messages if i.text or i.caption])
    user_name = user.full_name if not messages[0].sender_chat else messages[0].sender_chat.full_name

    via = next((i.via_bot for i in messages if i.via_bot), None)
    show_caption_above = any([i.show_caption_above_media for i in messages])
    
    forward_data = next((
        i.forward_origin.sender_user if isinstance(i.forward_origin, aiogram.types.MessageOriginUser) else
        i.forward_origin.sender_chat if isinstance(i.forward_origin, aiogram.types.MessageOriginChat) else
        i.forward_origin.chat if isinstance(i.forward_origin, aiogram.types.MessageOriginChannel) else
        i.forward_origin.sender_user_name if isinstance(i.forward_origin, aiogram.types.MessageOriginHiddenUser)
        else None for i in messages if i.forward_origin
    ), None)

    forward_name = (
        forward_data if isinstance(forward_data, str) else
        forward_data.full_name if forward_data else None
    )
    forward_link = (
        None if isinstance(forward_data, str) else
        forward_data.username if forward_data and forward_data.username else None
    )

    # user
    if pair['show_user'] and not webhook and not pair['footer']:
        if user.username:
            username = f'-# 👤 [{user_name}](<https://t.me/{user.username}>)'
        else:
            username = f'-# 👤 {user_name}'

        view.add_item(ui.TextDisplay(username))

    # forwarded
    if forward_name:
        if forward_link:
            name = f'[{forward_name}](<https://t.me/{forward_link}>)'
        else:
            name = forward_name
        view.add_item(ui.TextDisplay(f'-# переслано от {name}'))

    # via
    if via and via.username:
        view.add_item(ui.TextDisplay(f'-# через [@{via.username}](<https://t.me/{via.username}>)'))

    # reply text
    reply = next((i.reply_to_message for i in messages if i.reply_to_message), None)
    reply_text = ''

    if reply:
        data = manager.crossposter.get_dc_by_tg(chat_id, reply.message_id)

        if data:
            preview = data[1].replace(']', '\\]')
            preview = preview.replace('http', '\\http')
            url = data[2]

            if not preview:
                reply_text = f'[╭ _Нажмите, чтобы просмотреть вложение_](<{url}>)\n'
            else:
                reply_text = f'[╭ {preview}](<{url}>)\n'
    
    # gallery if shown above text
    if not show_caption_above and gallery:
        view.add_item(gallery)

    # text
    if len(content) > 0:
        if pair['show_user'] and webhook and not pair['footer'] and user.username:
            content += f'  [{VIEWUSER}](<{messages[0].get_url()}>)'

        view.add_item(ui.TextDisplay(reply_text + content))

    # gallery if shown below text
    if show_caption_above and gallery:
        view.add_item(gallery)

    # button
    if pair['footer']:
        button = ui.Button(
            style=discord.ButtonStyle.link, label=messages[0].chat.title,
            url=pair["tg_link"] if pair["tg_link"] else messages[0].get_url()
        )

        if messages[0].author_signature:
            view.add_item(ui.Section(
                ui.TextDisplay(f'-# {messages[0].author_signature}'),
                accessory=button
            ))
        else:
            view.add_item(ui.ActionRow(button))
    
    # empty view message
    if len(view.children) == 0:
        view.add_item(ui.TextDisplay(f'-# Пустое сообщение  [{VIEWUSER}](<{messages[0].get_url()}>)'))

    return view


def index_to_roulette_pos(index: int) -> Tuple[int,int]:
    return (
        58+(index%3)*112,
        55+(index//3)*90
    )


def unicode_cool_numbers(n: int) -> str:
    string = str(n)
    out = ''

    for i in string:
        out += UNICODE_COOL_NUMBERS.get(i, i)
    
    return out