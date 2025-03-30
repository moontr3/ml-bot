import discord

PREFIXES = ('tml!', 'ml!')
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
LOADING_EMBED = discord.Embed(
    title='Загружаем...', color=LOADING_C
)

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
