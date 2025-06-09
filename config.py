import discord

PREFIXES = ('tml!', 'ml!', 'odbs!','мл!','penis!','пенис!')
TEMP_VC_CREATE_COMMANDS = ['!типа где', '!типо где', '!тип где', '!tipa gde', '!tipo gde']
ADMINS = [698457845301248010]

LEVELS = [
    976773904968343572,
    976774001793843241,
    976774340714590208,
    976774065782153246,
    976774608197939220,
    976774691966582804,
    976774777291296798,
    976774897470668860,
    976774995516751985,
    976775077376974858,
    976775159358844968
]

GUILD_ID = 975809939920539729
ZERO_ID = 975809940444819467
ZERO_TEXT = 'на часах 00'
COUNTER_ID = 1024411443929550858
VERIFY_ID = 996491256865767475
VERIFY_ROLE = 996492289562136638
CHAT_CHANNEL = 975809940444819467
TEMP_VC_CATEGORY = 975809940444819466

CHATTABLE_CHANNELS = [
    975809940444819467,
    1301244013243928729,
    1091095982294438028,
    1052634269891170335,
    975817187191324814,
    1239901014757474334,
    1019936005912010772,
    1019941166613008425,
    1019938361718345738,
]

COGS_FOLDER = 'cogs'
LOG_FILE = 'log.txt'
USERS_FILE = 'users.json'
DATA_FILE = 'data.json'

DEFAULT_C = discord.Color.green()
LOADING_C = discord.Color.yellow()
ERROR_C = discord.Color.red()

MISSING_PERMS_EMBED = discord.Embed(
    title='❌ Ошибка!', color=ERROR_C,
    description='Недостаточно прав для ввода этой команды.'
)
UNKNOWN_ERROR_EMBED = discord.Embed(
    title='❌ Ошибка!', color=ERROR_C,
    description=f'Произошла неизвестная ошибка. Попробуйте ещё раз.'
)
ARGS_REQUIRED_EMBED = discord.Embed(
    title='❌ Ошибка!', color=ERROR_C,
    description='Приведено недостаточно аргументов.'
)
UNKNOWN_USER_EMBED = discord.Embed(
    title='❌ Ошибка!', color=ERROR_C,
    description='Неизвестный пользователь.'
)
UNKNOWN_CHANNEL_EMBED = discord.Embed(
    title='❌ Ошибка!', color=ERROR_C,
    description='Неизвестный канал.'
)
LOADING_EMBED = discord.Embed(
    title='Загружаем...', color=LOADING_C
)
NO_DM_EMBED = discord.Embed(
    description='Бота можно использовать только на сервере.', color=ERROR_C
)

WARN_IMAGE = 'https://moontr3.ru/assets/warn.png'
JOIN_IMAGE = 'https://moontr3.ru/assets/wpbot/join.png'
LEAVE_IMAGE = 'https://moontr3.ru/assets/wpbot/leave.png'
TIMEOUT_IMAGE = 'https://moontr3.ru/assets/timeout.png'

PLACE1 = '<:1p:1373797888831918100>'
PLACE2 = '<:2p:1373797899921788988>'
PLACE3 = '<:3p:1373797912164827246>'

UNITTABLE = {
    's': 1,
    'm': 60,
    'h': 60*60,
    'd': 60*60*24,
    'w': 60*60*24*7,
    'y': 60*60*24*365,

    'с': 1,
    'м': 60,
    'ч': 60*60,
    'д': 60*60*24,
    'н': 60*60*24*7,
    'л': 60*60*24*365
}
UNITNAMES = {
    's': 'сек',
    'm': 'мин',
    'h': 'час',
    'd': 'дн',
    'w': 'нед',
    'y': 'г.',

    'с': 'сек',
    'м': 'мин',
    'ч': 'час',
    'д': 'дн',
    'н': 'нед',
    'л': 'г.',
}

COOL_NUMBERS = {
    # "0": "<:0_:1371603686878347285>",
    # "1": "<:1_:1371603698178064585>",
    # "2": "<:2_:1371603711142396114>",
    # "3": "<:3_:1371603725789171752>",
    # "4": "<:4_:1371603740490072195>",
    # "5": "<:5_:1371603752808612001>",
    # "6": "<:6_:1371603764342947901>",
    # "7": "<:7_:1371603776523341904>",
    # "8": "<:8_:1371603788158472253>",
    # "9": "<:9_:1371603802242945074>",
    # "-": "<:__:1371603912280244294>"
    "-": "<:-f:1371606495485231124>",
    "9": "<:9f:1371606485502529597>",
    "8": "<:8f:1371606475591520297>",
    "7": "<:7f:1371606464728268980>",
    "6": "<:6f:1371606453298790480>",
    "5": "<:5f:1371606440866877584>",
    "4": "<:4f:1371606429861150740>",
    "3": "<:3f:1371606416514875432>",
    "2": "<:2f:1371606406599544852>",
    "1": "<:1f:1371606395954397325>",
    "0": "<:0f:1371606379940544552>"
}


Q_CHANCE = 0.01
SKIN_CHANCE = 0.007
FONT_CHANCE = 0.004
MAX_MINUTE_XP = 30
ONE_WORD_MSGS = 3
TEMP_VC_INACTIVITY_TIME = 60*5
TEMP_VC_CREATION_TIMEOUT = 60*10
DEAFEN_MUTE_LEVEL_REQ = 5
MAX_QS = 15

QUARANTINE_ROLE = 1003696913138323496

REP_COMMANDS = {
    '+rep': 1,
    '++rep': 2,
    '+++rep': 3,
    '+реп': 1,
    '++реп': 2,
    '+++реп': 3,
    '+ rep': 1,
    '++ rep': 2,
    '+++ rep': 3,
    '+ реп': 1,
    '++ реп': 2,
    '+++ реп': 3,
    '+': 1,
    '++': 2,
    '+++': 3,
    '- реп': -1,
    '\\- реп': -1,
    '- rep': -1,
    '\\- rep': -1,
    '-rep': -1,
    '-реп': -1,
    '-': -1,
    'сигма': 1,
    'не сигма': -1,
    'плюс реп': 1,
    'минус реп': -1,
    'plus rep': 1,
    'minus rep': -1,
}

REP_EMOJIS = {
    1: '<:rep:1379781056689078403>',
    2: '<:2rep:1381636774652149920>',
    3: '<:3rep:1381636788736753725>',
    -1: '<:minusrep:1379781112464932894>'
}
REP_EMOJI_IDS = {
    1379781056689078403: 1,
    1381636774652149920: 2,
    1381636788736753725: 3,
    1379781112464932894: -1
}

PLUS_REP_EVERY = 30
MINUS_REP_EVERY = 120
MINUS_REP_COUNTER_TIMEOUT = 300
