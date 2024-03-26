import discord

PREFIXES = ('!')
ADMINS = [698457845301248010]

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
