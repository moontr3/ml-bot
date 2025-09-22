import base64
import io
import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import utils
import api
from russian_names import RussianNames
import transliterate
import aiohttp


# setup
async def setup(bot: commands.Bot):

    @bot.hybrid_command(
        name='пипи',
        description='Показать размер пипи.',
        aliases=['pipi','penis','хуй','писька']
    )
    @discord.app_commands.describe(имя='Чей размер показать')
    async def slash_pipi(ctx: commands.Context, *, имя:str):
        '''
        Generates a random number between 1 and 30.
        '''
        name = имя

        length = random.randint(1,30)
        violent_imagery = f'**8{"="*length}D (длина: {length} см)**'
        title = f'✅ писька {name}'

        embed = discord.Embed(
            color=DEFAULT_C, title=title, description=violent_imagery
         )
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)


    @bot.hybrid_command(
        name='недавно',
        description='Недавно меня ...',
        aliases=['nedavno']
    )
    @discord.app_commands.describe(имя='Кто?')
    async def slash_nedavno(ctx: commands.Context, *, имя:str):
        '''
        Недавно меня трахнул.
        '''
        name = имя

        embed = discord.Embed(
            color=DEFAULT_C,
            description=f'Недавно меня трахнул {name}. Я полз по снегу, маленький, чумазый. Меня подняли и погладили. Я посмотрел на {name} своими маленькими добрыми глазками и начал урчать. Тогда {name} достал член из штанов и начал пропихивать мне в анус. Конечно, это было невозможно. Я начал мяукать, стонать. Это было очень больно. Но такое маленькое, беззащитное существо как я не могло ничего ему противопоставить. Ещё одно сильное нажатие - и мой анал порван. {name} почувствовал струйки крови, стекающие по его члену. Я всё кричал. {name} фактически не трахал меня, а просто дрочил мной. Он своим членом размозжил мне желудок. И сердце. А когда эякулировал, сперма вышла через нос и рот. {name} ещё раз погладил тельце милого меня и выкинул на снег. Всё равно такого бедняжку как меня съели бы собаки. А {name} наполнил мою жизнь смыслом. И удовольствием.'
        )
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)


    @bot.hybrid_command(
        name='альцгеймер',
        description='Забыл',
        aliases=['alzheimer']
    )
    @discord.app_commands.describe(текст='Текст, который необходимо повторить')
    async def slash_alzheimer(ctx: commands.Context, *, текст:str):
        '''
        Repeats text several times..
        '''
        text = текст

        # too big message
        num = 10-int(len(text)/15)
        if num <= 1:
            num = 1

        if len(text)*num*2 > 1000:
            await ctx.reply(view=c_to_view(TOO_LONG_EMBED), ephemeral=True)
            return

        # answering
        amount = random.randint(num, num*2)

        embed = discord.Embed(
            color=DEFAULT_C, title='✅ Успешно!',
            description=text*amount
        )
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)
        

    @bot.hybrid_command(
        name='краш',
        description='Крашит что-либо',
        aliases=['crash']
    )
    @discord.app_commands.describe(имя='То, что нужно крашнуть')
    async def slash_crash(ctx: commands.Context, *, имя:str):
        '''
        Crashes smth
        '''
        name = имя

        # text too long
        if len(name) > 100:
            await ctx.reply(view=c_to_view(TOO_LONG_EMBED), ephemeral=True)
            return

        # error
        if random.random() < 0.7:
            fail_message = random.choice([
                'но вайфай выключился',
                'но электричества нет',
                'но твой аккаунт заблокировали',
                'но сервер упал',
                'но в коде вышла ошибка',
                'но что-то пошло не так',
                f'но {name} отразил атаку',
                f'но {name} использовал антивирус'
            ])

            if random.random() < 0.15:
                percentage_text = f'ты хотел крашнуть {name}'
            else:
                percentage_text = 'загрузка дошла до ' + str(random.choices(
                    [random.randint(30,75), random.randint(90,99)],
                    weights=[0.7, 0.1]
                )[0]) + '%'

            embed = discord.Embed(
                color=ERROR_C, title=f'❌ не удалось крашнуть {name}',
                description=f'{percentage_text} {fail_message}'
            )

        # success
        else:
            embed = discord.Embed(
                color=DEFAULT_C, title=f'✅ краш {name} прошел успешно',
                description=f'загрузка закончилась и {name} крашнули!'
            )

        # answering
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)
        
        
    @bot.hybrid_command(
        name='деанон',
        description='Доксит пользователя.',
        aliases=['doxx','dox','докс']
    )
    @commands.cooldown(1, 7, commands.BucketType.user)
    @discord.app_commands.describe(пользователь='Пользователь, которого надо задеанонить')
    async def slash_doxx(ctx: commands.Context, пользователь:discord.User):
        '''
        Generates fake info about user.
        '''
        user = пользователь

        # checking if bot is getting doxxed
        if user.id == bot.user.id:
            view = to_view('а ты не прихуел', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
        
        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        # getting data
        try:
            # name
            name = RussianNames().get_person()

            # phone
            area_code = random.choice([
                *range(900,953),
                *range(955,969),
                *range(972,999)
            ])
            num1 = "".join(random.choices('0123456789',k=3))
            num2 = "".join(random.choices('0123456789',k=2))
            num3 = "".join(random.choices('0123456789',k=2))

            number = f'+7 ({area_code}) {num1}-{num2}-{num3}'

            # gender
            if random.random() > 0.4:
                gender = random.choice(['Муж.','Жен.'])

            else:
                # getting a random russian word
                gender = utils.get_random_word().title()

            # age
            age = random.randint(11,65)

            # ip address
            ip = '.'.join([str(random.randint(1,255)) for i in range(4)])

            # email
            provider = random.choice([
                '@vk.com',
                '@mail.ru',
                '@gmail.com',
                '@yandex.ru',
                '@yahoo.com',
                '@aol.com',
                '@hotmail.com',
                '@yahoo.co.uk',
                '@hotmail.com.au',
                '@web.de',
                '@nproxi.com',
                '@moonland.dev',
                '@bebracraft.ml',
                '@moonland.ml',
                '@femboyhunter.club',
                '@icloud.com',
                '@bk.ru'
            ])
            if random.random() < 0.3:
                numbers = ''
            else:
                numbers = ''.join(random.choices(
                    '0123456789', k=random.randint(2,6)
                ))

            base = utils.remove_md(user.name)

            email = base+numbers+provider

            # token
            userid_encoded = str(user.id).encode()
            token = base64.b64encode(userid_encoded).decode('utf-8')
            token = f'`{token}.xxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`'

            # face
            async with aiohttp.ClientSession() as s:
                async with s.get('https://thispersondoesnotexist.com/') as resp:
                    content = await resp.read()

            image = discord.File(io.BytesIO(content), 'face.jpg')

        except Exception as e:
            # there's an error
            embed = discord.Embed(
                color=ERROR_C, title=f'❌ ой',
                description=f'не задоксили😔\n{e}'
            )
            embed.set_footer(
                text=ctx.author.name,
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            await ctx.reply(embed=embed)
            return

        # sending
        embed = discord.Embed(
            color=DEFAULT_C,
            title=f'✅ {user.name} задеанонен!'
        )
        embed.add_field(name='Имя', value=name, inline=False)
        embed.add_field(name='Номер телефона', value=number, inline=False)
        embed.add_field(name='Пол', value=gender, inline=False)
        embed.add_field(name='Возраст', value=age, inline=False)
        embed.add_field(name='IP-адрес', value=ip, inline=False)
        embed.add_field(name='Почта', value=email, inline=False)
        embed.add_field(name='Токен', value=token, inline=False)
        embed.set_thumbnail(url='attachment://face.jpg')

        embed.set_footer(
            text=ctx.author.name+'\nфейк инфа!',
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed, file=image)


    @bot.hybrid_command(
        name='шанс',
        description='Говорит, насколько процентов возможно ваше предсказание.',
        aliases=['chance']
    )
    @discord.app_commands.describe(запрос='Ваш вопрос')
    async def slash_chance(ctx: commands.Context, *, запрос:str):
        '''
        Answers with a random percentage.
        '''
        prompt = запрос

        if len(prompt) > 100:
            await ctx.reply(view=c_to_view(TOO_LONG_EMBED), ephemeral=True)
            return

        percentage = random.randint(0,100)

        prefix = random.choice([
            'Я думаю, это возможно на',
            'Это возможно на',
            'Шанс этого -',
            'Мне кажется, шанс этого',
            'Вероятность этого -',
            'Мне кажется, это возможно на',
            'Я думаю, что вероятность',
            'Я думаю, это возможно на'
        ])

        # sending
        embed = discord.Embed(
            title=f'✅ {prompt}', description=f'{prefix} **{percentage}%**',
            color=DEFAULT_C
        )
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)


    @bot.hybrid_command(
        name='выбери',
        description='Выбирает одно из выданных вариантов.',
        aliases=['choose','choice','выбор']
    )
    @discord.app_commands.describe(
        запросы='Список вариантов, разделенных через разделитель (по умолч. запятая)',
        разделитель='Разделитель вариантов у текста с запросами (по умолч. запятая)',
    )
    async def slash_chance(ctx: commands.Context, *, запросы:str, разделитель:str=','):
        '''
        Answers with a random percentage.
        '''
        divider = разделитель

        # generating answers
        prompts: List[str] = []
        for i in запросы.split(divider):
            prompts.append(i.strip())

        prompts = [i for i in prompts if i != '' and not i.isspace()]

        if len(prompts) < 2:
            embed = discord.Embed(
                color=ERROR_C, title='❌ ой',
                description=f'надо указать 2 или больше вариантов ответа через `{divider}`'
            )
            await ctx.reply(embed=embed)
            return

        for i in prompts:
            if len(i) > 100:
                await ctx.reply(view=c_to_view(TOO_LONG_EMBED), ephemeral=True)
                return

        prompt = random.choice(prompts)

        # sending
        embed = discord.Embed(
            title='✅ Успешно!', description=f'я выбрал **{utils.remove_md(prompt)}**',
            color=DEFAULT_C
        )
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)


    @bot.hybrid_command(
        name='эмоджи',
        description='Показывает, какой эмоджи охарактерирует пользователя.',
        aliases=['emoji','эмодзи']
    )
    @discord.app_commands.describe(имя='Пользователь, чьего эмодзи вы хотите узнать')
    async def slash_emoji(ctx: commands.Context, имя:str):
        '''
        Shows an emoji corresponding to a user.
        '''
        user = имя

        # composing message
        prefix = random.choice([
            'Я думаю, ',
            'Мне кажется, ',
            'Я думаю что ',
            'Мне кажется что '
        ])
        # using cigarrete emoji if роман
        if user.lower().strip() in ['<@801058884810309673>','рома','роман']:
            emoji = '🚬'
        else:
            emoji = random.choice(bot.mg.emojis)

        # sending
        embed = discord.Embed(
            color=DEFAULT_C, title='✅ Успешно!',
            description=f'{prefix}{emoji} охарактеризует {user}'
        )
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)


    @bot.hybrid_command(
        name='шип',
        description='Шип двух случайных пользователей или кого-то с кем-то.',
        aliases=['ship']
    )
    @discord.app_commands.describe(пользователь='Пользователь, кого вы хотите шипперить.')
    async def slash_ship(ctx: commands.Context, пользователь:discord.User=None):
        '''
        Ships two random users.
        '''
        user = пользователь

        # choosing users
        if user == None:
            user = random.choice(ctx.channel.members)

        rand = user
        while rand == user:
            rand = random.choice(ctx.channel.members)

        # sending
        if user.id != 698457845301248010:
            embed = discord.Embed(
                color=DEFAULT_C, title='✅ Успешно!',
                description=f'{user.mention} ({utils.remove_md(user.name)})'\
                    f' **x** {rand.mention} ({utils.remove_md(rand.name)})'
            )
        # to show coffee as my soulmate
        else:
            embed = discord.Embed(
                color=DEFAULT_C, title='✅ Успешно!',
                description=f'{user.mention} ({utils.remove_md(user.name)})'\
                    f' **x** <@817035020958695536> (warningcoffee3)'
            )
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)


    @bot.hybrid_command(
        name='судьба',
        description='Показывает то, что бы вы сделали с пользователем.',
        aliases=['destiny','fate']
    )
    @discord.app_commands.describe(имя='Человек, судьбу которого вы хотите узнать')
    async def slash_fate(ctx: commands.Context, имя:str):
        '''
        Shows what will happen to a user.
        '''
        user = имя

        # composing message
        index = random.randint(0, len(bot.mg.fate_actions)-1)
        action = bot.mg.fate_actions[index]

        # sending
        desc = f'**Что вы хотите сделать с {utils.remove_md(user)}?**'
        desc += f'\n`{index+1}.` {action}'

        embed = discord.Embed(
            color=DEFAULT_C, title='✅ Успешно!',
            description=desc
        )
        embed.set_image(url=FATE_IMAGE_URL)
        embed.set_footer(
            text=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        await ctx.reply(embed=embed)