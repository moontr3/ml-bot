import asyncio
import random
from typing import *

from discord.ext import commands
from config import *
import json
import os
import time
from log import *
from renderer import *
from copy import deepcopy
import utils
import aiohttp
import base64


# user and user-related classes

class Reminder:
    def __init__(self, data:dict):
        '''
        Represents a reminder.
        '''
        self.message_id: "int | None" = data['id']
        self.channel_id: int = data['channel_id']
        self.end_time: float = data['end_time']
        self.duration: float = data['duration']
        self.text: "str | None" = data['text']
        self.jump_url: "str | None" = data['jump_url']

    def to_dict(self) -> dict:
        '''
        Converts the reminder to a dictionary.
        '''
        return {
            "id": self.message_id,
            "channel_id": self.channel_id,
            "end_time": self.end_time,
            "duration": self.duration,
            "text": self.text,
            "jump_url": self.jump_url
        }
    
    @staticmethod
    def convert(
        message_id:int,
        channel_id:int,
        duration:int,
        jump_url:str,
        text:"str | None"=None
    ) -> "Reminder":
        '''
        Computes the stuff by itself.
        '''
        return Reminder({
            "id": message_id,
            "channel_id": channel_id,
            "end_time": time.time()+duration,
            "duration": duration,
            "jump_url": jump_url,
            "text": text
        })


class XP:
    def __init__(self, data:dict={}):
        '''
        User experience points, level, rank, etc.
        '''
        self.prev_xp: int = data.get('prev_xp', 0)
        self.xp: int = data.get('xp', 0)
        self.reload_levels()


    @property
    def total_xp(self) -> int:
        return self.prev_xp + self.xp


    def reload_levels(self):
        '''
        Reloads levels and percentages.
        '''
        xp = deepcopy(self.xp)
        xp_in_level = 1000
        level = 1
        while xp >= xp_in_level: 
            level += 1
            xp -= xp_in_level
            xp_in_level += 500

        self.level: int = level
        self.level_data: any = config.LEVELS[min(level, len(config.LEVELS))-1]
        self.level_xp: int = xp
        self.level_max_xp: int = xp_in_level
        self.level_percentage: float = xp/xp_in_level


    def to_dict(self) -> dict:
        return {
            "xp": self.xp,
            "prev_xp": self.prev_xp,
        }
    

class Collectibles:
    def __init__(self, data: dict = {}):
        '''
        Collectible list.
        '''
        self.items: list = data.get('items', [])
        self._selected: "str | None" = data.get('selected', None)

    
    @property
    def selected(self) -> str:
        return self._selected if self._selected else 'default'


    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "selected": self._selected
        }
    

class VCData:
    def __init__(self, data: dict = {}):
        '''
        Voice channel data.
        '''
        self.vc_time: int = int(data.get('vc_time', 0))
        self.vc_time_streaming: int = int(data.get('vc_time_streaming', 0))
        self.vc_time_speaking: int = int(data.get('vc_time_speaking', 0))
        self.xp_to_add: float = data.get('xp_to_add', 0.0)
        
        self.state: Literal['none', 'deafen', 'mute', 'normal'] = 'none'
        self.is_streaming: bool = False

    
    @property
    def xp_mult(self) -> int:
        return {
            'none': 0,
            'deafen': 0,
            'mute': 2,
            'normal': 4
        }[self.state] + int(self.is_streaming)

    
    def to_dict(self) -> dict:
        return {
            "vc_time": self.vc_time,
            "vc_time_streaming": self.vc_time_streaming,
            "vc_time_speaking": self.vc_time_speaking,
            "xp_to_add": self.xp_to_add
        }
    

class MinuteStats:
    def __init__(self):
        '''
        Tracks stats of XP gained in the last minute.
        '''
        self.minute: int = 0
        self.update_minute()

        self.xp: int = 0
        self.one_word_messages: int = 0


    def update_minute(self):
        '''
        Updates the current minute.
        '''
        old_min = deepcopy(self.minute)
        self.minute = int(time.time()/60)

        if old_min != self.minute:
            self.xp = 0
            self.one_word_messages = 0

    
    def add_xp(self, xp: int):
        '''
        Adds XP to the counter.
        '''
        self.update_minute()

        self.xp += xp


class User:
    def __init__(self, id:int, data:dict={}):
        '''
        Represents a user.
        '''
        self.id: int = id

        xp: int = data.get('xp', {})
        self.xp = XP(xp)
        self.quarantine: float | None = data.get('quarantine', None)
        self.reminders: List[Reminder] = [Reminder(i) for i in data.get('reminders', [])]
        self.tokens: Dict[int] = data.get('tokens', {})
        self.q: int = data.get('q', 0)
        self.q_level: int = data.get('q_level', self.q)
        self.q_level = min(15, max(0, self.q_level))
        self.coins: int = data.get('coins', 0)

        self.plus_reps: int = data.get('plus_reps', 0)
        self.minus_reps: int = abs(data.get('minus_reps', 0))
        self.plus_rep_timeout: float = data.get('plus_rep_timeout', 0.0)
        self.minus_rep_timeout: float = data.get('minus_rep_timeout', 0.0)
        self.minus_repped: Dict[int, float] = {int(k): v for k, v in data.get('minus_repped', {}).items()}
        self.rep_block_until: float = data.get('rep_block_until', 0.0)

        self.mfr_timeout: float = data.get('mfr_timeout', 0.0)
        self.mfr_stats: Dict[str, int] = data.get('mfr_stats', {})

        self.last_sent_zero: float = 0
        self.verifying: bool = False

        self.skins: Collectibles = Collectibles(data.get('skins', {}))
        self.fonts: Collectibles = Collectibles(data.get('fonts', {}))

        self.vc: VCData = VCData(data.get('vc', {}))
        self.temp_vc_timeout: float = data.get('temp_vc_timeout', 0)

        self.last_msg_channel: int = data.get('last_msg_channel', deepcopy(CHAT_CHANNEL)) 
        self.to_send_lvl_up_msg: bool = False
        self.marked_by_beast: bool = data.get('marked_by_beast', False)
        self.likee: bool = data.get('likee', False)

        self.minute_stats = MinuteStats()


    @property
    def rep(self) -> int:
        return self.plus_reps - self.minus_reps

    
    def to_dict(self) -> dict:
        '''
        Converts the class to a dictionary to store in the file.
        '''
        return {
            "xp": self.xp.to_dict(),
            "quarantine": self.quarantine,
            "reminders": [i.to_dict() for i in self.reminders],
            "tokens": self.tokens,
            "q": self.q,
            "q_level": self.q_level,
            "plus_reps": self.plus_reps,
            "minus_reps": self.minus_reps,
            "minus_repped": self.minus_repped,
            "plus_rep_timeout": self.plus_rep_timeout,
            "minus_rep_timeout": self.minus_rep_timeout,
            "rep_block_until": self.rep_block_until,
            "mfr_timeout": self.mfr_timeout,
            "mfr_stats": self.mfr_stats,
            "skins": self.skins.to_dict(),
            "fonts": self.fonts.to_dict(),
            "vc": self.vc.to_dict(),
            "temp_vc_timeout": self.temp_vc_timeout,
            "last_msg_channel": self.last_msg_channel,
            "marked_by_beast": self.marked_by_beast,
            "likee": self.likee,
            "coins": self.coins
        }
    

# gambling


class GamblingPattern:
    def __init__(self, skin: str, pattern: List[int] = []):
        self.pattern: List[int] = pattern
        self.skin: str = skin


    @classmethod
    def random(cls, skin: str):
        pattern = [
            random.randint(1,8) for _ in range(9)
        ]
        return cls(skin, pattern)
    

    def get_column(self, index: str) -> List[int]:
        return self.pattern[index::3]
    

    def get_patterns(self) -> List[Tuple[List[int], int]]:
        out = []

        for i in GAMBLING_PATTERNS:
            items = [self.pattern[index] for index in i[0]]

            if items[1:] == items[:-1]:
                out.append(i)

        return out
    

    def get_xp(self) -> int:
        return sum([i[1] for i in self.get_patterns()])


# XP Leaderboard

class TimedLeaderboard:
    def __init__(self, data: dict = {}):
        '''
        Daily and weekly leaderboard.
        '''
        self.daily = data.get('daily', {})
        self.weekly = data.get('weekly', {})

        self.daily = {
            int(k): {int(k1): v1 for k1, v1 in v.items()}\
                for k, v in self.daily.items()
        }
        self.weekly = {
            int(k): {int(k1): v1 for k1, v1 in v.items()}\
                for k, v in self.weekly.items()
        }


    @property
    def current_day(self) -> int:
        return int(time.time()//86400)
    

    @property
    def current_week(self) -> int:
        return int(time.time()//604800)


    def check_leaderboard(self):
        if self.current_day not in self.daily:
            self.daily[self.current_day] = {}

        if self.current_week not in self.weekly:
            self.weekly[self.current_week] = {}


    def check_user(self, id:int):
        if id not in self.daily[self.current_day]:
            self.daily[self.current_day][id] = 0

        if id not in self.weekly[self.current_week]:
            self.weekly[self.current_week][id] = 0


    def add_xp(self, id:int, amount:int):
        '''
        Updates the leaderboard.
        '''
        self.check_leaderboard()
        self.check_user(id)

        self.daily[self.current_day][id] += amount
        self.weekly[self.current_week][id] += amount


    def get_daily_xp(self, id:int) -> int:
        self.check_leaderboard()

        if id not in self.daily[self.current_day]:
            return 0
        
        return self.daily[self.current_day][id]


    def get_weekly_xp(self, id:int) -> int:
        self.check_leaderboard()
        
        if id not in self.weekly[self.current_week]:
            return 0
        
        return self.weekly[self.current_week][id]


    def to_dict(self) -> dict:
        return {
            "daily": self.daily,
            "weekly": self.weekly
        }
        

# skin data

class SkinData:
    def __init__(self, key: str, data: dict = {}):
        '''
        Skin data.
        '''
        self.key: str = key
        self.name: str = data.get('name', None)
        self.emoji: str = data.get('emoji', None)
        self.rarity: int = data.get('rarity', None)

        # checking skin files
        for i in [
            'onelinerbg', 'prombg', 'xpbg', 'lbtopbg', 'lbmidbg', 'lbbottombg',
            'skintopbg', 'skinbottombg', 'badge', 'vcbg'
        ]:
            if not os.path.exists(f'assets/skins/{self.key}/{i}.png'):
                log(f'File {i} not found for skin {self.key}', 'api', WARNING)


class FontData:
    def __init__(self, key: str, data: dict = {}):
        '''
        Skin data.
        '''
        self.key: str = key
        self.name: str = data.get('name', None)
        self.emoji: str = data.get('emoji', None)
        self.rarity: int = data.get('rarity', None)
        self.alt: List[str] = data.get('alt', [])

        # checking skin files
        for i in [
            'bolditalic', 'bold', 'semibold', 'medium', 'regular'
        ]:
            if not os.path.exists(f'assets/fonts/{self.key}/{i}.ttf'):
                log(f'File {i} not found for font {self.key}', 'api', WARNING)


# temp VC

class TempVC:
    def __init__(self, id: int, data: dict = {}):
        '''
        Temporary voice channel.
        '''
        self.id: int = id
        self.owner_id: int = data['owner_id']
        self.last_activity: float = data.get('last_activity', time.time())
        self.has_people: "bool | None" = None
        self.name: str = data['name']
        self.checked: bool = False # whether this vc was checked when updating activity
        self.created_at: float = data.get('created_at', time.time())

    
    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "last_activity": self.last_activity,
            "name": self.name,
            "created_at": self.created_at
        }
    

# Q earning

class UnclaimedQ:
    def __init__(self, message_id: int):
        self.message_id: int = message_id
        self.spawned_at: float = time.time()
        self.claimed: List[int] = []


# mishkfrede


class MfrCard:
    def __init__(self, key: str, name: str, xp: int, image: str, color: str):
        self.key: str = key
        self.name: str = name
        self.xp: int = xp
        self.image: str = image
        self.color: str = color


# roulette


class Roulette:
    def __init__(self, user: int, on_end: Callable):
        self.user1: int = user
        self.user2: "int | None" = None
        self.player: "int | None" = None
        self.bullets: int = 6
        self.target: int = None
        self.message: discord.Message = None
        self.on_end: Callable = on_end
        self.processing: bool = False


    def get_opposite(self, user: int) -> int:
        if user == self.user1:
            return self.user2
        elif user == self.user2:
            return self.user1


    def start(self, user: int):
        self.user2 = user
        self.target = random.randint(1, 6)


    async def start_seq(self):
        elements = [
            f'### {GUN} Русская рулетка', SEP(),
            f'**Ну что, <@{self.user1}> и <@{self.user2}>, начинаем игру!**'
        ]

        # deciding on current player
        view = to_view(elements+[
            random.choice([
                '_Для начала выберем, кто будет стрелять первым._',
                '_Сначала выберем, кто будет стрелять первым._',
                '_Выберем, кто будет стрелять первым._',
                '_Определим, кто будет стрелять первым._'
            ])
        ])
        self.player = random.choice([self.user1, self.user2])

        await self.message.edit(view=view)
        await asyncio.sleep(2.5)

        view = to_view(elements+[
            random.choice([
                f'И это <@{self.player}>!',
                f'Выпал <@{self.player}>!',
                f'Первым стреляет <@{self.player}>!',
                f'Первый <@{self.player}>!',
                f'<@{self.player}> стреляет первым!'
            ])
        ])
        await self.message.edit(view=view)
        await asyncio.sleep(2.5)

        await self.spin_barrel()


    async def spin_barrel(self):
        elements = [
            f'### {GUN} Русская рулетка', SEP(),
        ]

        # spinning barrel
        view = to_view(elements+[
            random.choice([
                f'Готовность, <@{self.player}>!',
                f'<@{self.player}>, готовность!',
                f'<@{self.player}>, будь на чеку!',
                f'<@{self.player}>, твой выход!',
            ]),
            random.choice([
                '_Крутим барабан..._',
                '_Раскручиваем барабан..._',
            ]),
            SEP(spacing=discord.SeparatorSpacing.large),
            ui.MediaGallery(
                discord.MediaGalleryItem(
                    utils.get_revolver_image(0)
                )
            )
        ])
        self.target = random.randint(1, 6)
        self.bullets = 6
        await self.message.edit(view=view)
        await asyncio.sleep(2.5)

        await self.move()


    async def move(self):
        elements = [
            f'### {GUN} Русская рулетка', SEP(),
        ]

        # spinning barrel
        view = to_view(elements+[
            random.choice([
                f'<@{self.player}>, ваш ход!',
                f'<@{self.player}>, выбирайте!',
                f'<@{self.player}>, что будете делать?',
                f'<@{self.player}>, что делаем?',
                f'<@{self.player}>, пожалуйста!',
                f'<@{self.player}>, ваше действие?',
                f'<@{self.player}>, куда стреляем?',
            ]),
            [
                ui.Button(
                    style=discord.ButtonStyle.primary,
                    label='В себя', emoji=GUN, custom_id='rouletteself'
                ),
                ui.Button(
                    style=discord.ButtonStyle.primary,
                    label='В противника', emoji=GUN, custom_id='rouletteother'
                ),
                ui.Button(
                    style=discord.ButtonStyle.danger,
                    label='Сдаться', emoji=REJECT, custom_id='giveuproulette'
                )
            ],
            SEP(spacing=discord.SeparatorSpacing.large),
            ui.MediaGallery(
                discord.MediaGalleryItem(
                    utils.get_revolver_image(self.bullets)
                )
            )
        ])
        await self.message.edit(view=view)


    async def shoot_self(self):
        elements = [
            f'### {GUN} Русская рулетка', SEP(),
        ]

        # spinning barrel
        view = to_view(elements+[
            f'<@{self.player}> нажимает на курок...',
            [
                ui.Button(
                    style=discord.ButtonStyle.green, label='В себя', emoji=GUN, disabled=True
                ),
                ui.Button(
                    style=discord.ButtonStyle.gray, label='В противника', emoji=GUN, disabled=True
                ),
                ui.Button(
                    style=discord.ButtonStyle.gray, label='Сдаться', emoji=REJECT, disabled=True
                )
            ],
            SEP(spacing=discord.SeparatorSpacing.large),
            ui.MediaGallery(discord.MediaGalleryItem(utils.get_revolver_image(self.bullets)))
        ])

        await self.message.edit(view=view)
        await asyncio.sleep(random.uniform(2.5, 4))
        is_dead = self.discard_bullet()

        # bro dead :skull:
        if is_dead:
            xp = random.randint(*ROULETTE_XP) if self.message.guild and self.message.guild.id == GUILD_ID else 0

            view = to_view(elements+[
                f'<@{self.player}> нажимает на курок...',
                '### 💥 Выстрел! 💥',
                random.choice([
                    f'<@{self.get_opposite(self.player)}> выигрывает.',
                    f'<@{self.get_opposite(self.player)}> побеждает.',
                    f'<@{self.get_opposite(self.player)}> выиграл.',
                    f'<@{self.get_opposite(self.player)}> победил.',
                    f'<@{self.get_opposite(self.player)}> остался в выигрыше.',
                    f'<@{self.get_opposite(self.player)}> остался в живых.',
                ]),
                f'За выигрыш заработано **{xp} XP**. Поздравляем.' if xp > 0 else\
                    '-# За эту игру можно зарабатывать опыт на нашем сервере - </moonland:1411399171042443447>!',
                SEP(spacing=discord.SeparatorSpacing.large),
                ui.MediaGallery(discord.MediaGalleryItem(utils.get_revolver_endgame_image(self.bullets)))
            ])

            await self.message.edit(view=view)
            self.on_end(self, self.get_opposite(self.player), xp)
            return
        
        # survived
        view = to_view(elements+[
            f'<@{self.player}> нажимает на курок...',
            '### _Щелчок..._',
            SEP(spacing=discord.SeparatorSpacing.large),
            ui.MediaGallery(discord.MediaGalleryItem(utils.get_revolver_image(self.bullets)))
        ])
        await self.message.edit(view=view)
        await asyncio.sleep(2.5)
        await self.move()


    async def shoot_opponent(self):
        elements = [
            f'### {GUN} Русская рулетка', SEP(),
        ]

        # spinning barrel
        view = to_view(elements+[
            f'<@{self.player}> нажимает на курок...',
            [
                ui.Button(
                    style=discord.ButtonStyle.gray, label='В себя', emoji=GUN, disabled=True
                ),
                ui.Button(
                    style=discord.ButtonStyle.green, label='В противника', emoji=GUN, disabled=True
                ),
                ui.Button(
                    style=discord.ButtonStyle.gray, label='Сдаться', emoji=REJECT, disabled=True
                )
            ],
            SEP(spacing=discord.SeparatorSpacing.large),
            ui.MediaGallery(discord.MediaGalleryItem(utils.get_revolver_image(self.bullets)))
        ])

        await self.message.edit(view=view)
        await asyncio.sleep(random.uniform(2.5, 4))
        is_dead = self.discard_bullet()

        # bro dead :skull:
        if is_dead:
            xp = random.randint(*ROULETTE_XP) if self.message.guild and self.message.guild.id == GUILD_ID else 0

            view = to_view(elements+[
                f'<@{self.player}> нажимает на курок...',
                '### 💥 Выстрел! 💥',
                random.choice([
                    f'<@{self.get_opposite(self.player)}> проигрывает.',
                    f'<@{self.get_opposite(self.player)}> проиграл.',
                    f'<@{self.get_opposite(self.player)}> умер.',
                    f'<@{self.get_opposite(self.player)}> перешел в другой мир.',
                ]),
                f'За выигрыш заработано **{xp} XP**. Поздравляем.' if xp > 0 else\
                    '-# За эту игру можно зарабатывать опыт на нашем сервере - </moonland:1411399171042443447>!',
                SEP(spacing=discord.SeparatorSpacing.large),
                ui.MediaGallery(discord.MediaGalleryItem(utils.get_revolver_endgame_image(self.bullets)))
            ])

            await self.message.edit(view=view)
            self.on_end(self, self.player, xp)
            return
        
        # survived
        view = to_view(elements+[
            f'<@{self.player}> нажимает на курок...',
            '### _Щелчок..._',
            SEP(spacing=discord.SeparatorSpacing.large),
            ui.MediaGallery(discord.MediaGalleryItem(utils.get_revolver_image(self.bullets)))
        ])
        await self.message.edit(view=view)
        await asyncio.sleep(2.5)
        self.player = self.get_opposite(self.player)
        await self.spin_barrel()


    def discard_bullet(self):
        if self.target == self.bullets:
            return True
        
        self.bullets -= 1


class Duel:
    def __init__(self, user: int, on_end: Callable):
        self.user1: int = user
        self.user2: "int | None" = None
        self.user1hp: int = 2
        self.user2hp: int = 2
        self.focus: "int | None" = None
        self.message: discord.Message = None
        self.on_end: Callable = on_end
        self.processing: bool = False
        self.stopped: bool = False


    def get_opposite(self, user: int) -> int:
        if user == self.user1:
            return self.user2
        elif user == self.user2:
            return self.user1
        

    def get_hp(self, user: int) -> int:
        if user == self.user1:
            return self.user1hp
        elif user == self.user2:
            return self.user2hp


    def start(self, user: int):
        self.user2 = user


    def get_users(self) -> List[str]:
        em11 = LEFTY if self.user1hp >= 1 else LEFTN
        em12 = RIGHTY if self.user1hp >= 2 else RIGHTN
        em21 = LEFTY if self.user2hp >= 1 else LEFTN
        em22 = RIGHTY if self.user2hp >= 2 else RIGHTN
        focus1 = f'{TARGET} ' if self.focus == self.user1 else ''
        focus2 = f'{TARGET} ' if self.focus == self.user2 else ''

        return [
            f'{em11} {em12} ・ {focus1}<@{self.user1}>',
            f'{em21} {em22} ・ {focus2}<@{self.user2}>',
        ]


    async def start_seq(self):
        elements = [
            add_accessory([f'### 🎯 Дуэль'], ui.Button(
                style=discord.ButtonStyle.danger, label='Сдаться',
                emoji=REJECT, custom_id='giveupduel', disabled=True
            )),
            SEP()
        ]

        view = to_view(elements+[
            f'**Ну что, <@{self.user1}> и <@{self.user2}>, начинаем игру!**',
            '_Нужно нажать на курок быстрее противника._',
            f'_При нажатии на {TARGET} можно увеличить шанс попадания на следующий ход._'
        ])
        await self.message.edit(view=view)
        await asyncio.sleep(5.5)

        await self.move()


    async def move(self):
        elements = [
            add_accessory([f'### 🎯 Дуэль'], ui.Button(
                style=discord.ButtonStyle.danger, label='Сдаться',
                emoji=REJECT, custom_id='giveupduel'
            )),
            SEP()
        ]

        # showing message
        view = to_view(elements+self.get_users()+[
            SEP(),
            [
                ui.Button(
                    style=discord.ButtonStyle.primary, disabled=True, label='Стрелять!',
                ),
                ui.Button(
                    style=discord.ButtonStyle.green if self.focus else discord.ButtonStyle.gray,
                    emoji=TARGET, disabled=True
                ),
            ]
        ])
        if self.stopped:
            return
        await self.message.edit(view=view)
        await asyncio.sleep(random.uniform(2, 6))

        # enabling buttons
        view = to_view(elements+self.get_users()+[
            SEP(),
            [
                ui.Button(
                    style=discord.ButtonStyle.primary, label='Стрелять!', custom_id='duelshoot'
                ),
                ui.Button(
                    style=discord.ButtonStyle.green if self.focus else discord.ButtonStyle.gray,
                    emoji=TARGET, custom_id='duelfocus'
                ),
            ]
        ])
        if self.stopped:
            return
        await self.message.edit(view=view)


    async def shoot(self, user: int):
        elements = [
            add_accessory([f'### 🎯 Дуэль'], ui.Button(
                style=discord.ButtonStyle.danger, label='Сдаться',
                emoji=REJECT, custom_id='giveupduel', disabled=True
            )),
            SEP()
        ]

        # calculating
        chance = 0.3 if self.focus != user else 0.8
        success = random.random() < chance
        self.focus = None

        if success:
            self.remove_hp(self.get_opposite(user))

            # endgame
            if self.get_hp(self.get_opposite(user)) <= 0:
                xp = random.randint(*DUEL_XP) if self.message.guild and self.message.guild.id == GUILD_ID else 0

                view = to_view(elements+self.get_users()+[
                    SEP(),
                    f'💥 <@{user}> стреляет **и попадает!**',
                    random.choice([
                        f'<@{self.get_opposite(user)}> проигрывает...',
                        f'<@{self.get_opposite(user)}> умирает...',
                        f'<@{self.get_opposite(user)}> проиграл...',
                        f'<@{self.get_opposite(user)}> падает на землю замертво...',
                        f'<@{self.get_opposite(user)}> перешел в другой мир...',
                    ]),
                    f'За выигрыш заработано **{xp} XP**. Поздравляем.' if xp > 0 else\
                        '-# За эту игру можно зарабатывать опыт на нашем сервере - </moonland:1411399171042443447>!'
                ])
                await self.message.edit(view=view)
                self.on_end(self, user, xp)
                return

        # showing message
        view = to_view(elements+self.get_users()+[
            SEP(),
            f'💥 <@{user}> стреляет **и попадает!**' if success\
                else f'<@{user}> стреляет, но **промахивается...**',
        ])
        if self.stopped:
            return
        await self.message.edit(view=view)
        await asyncio.sleep(2.5)
        await self.move()


    async def act_focus(self, user: int):
        self.focus = user

        await self.move()


    def remove_hp(self, user: int):
        if user == self.user1:
            self.user1hp -= 1
        elif user == self.user2:
            self.user2hp -= 1


# ai


class AIMessage:
    def __init__(self, role: str, message: str, user: discord.User = None, attachment_url: list[str] = [], reply: discord.Message = None, reply_images: int = 0):
        self.role: str = role
        self.message: str = message
        self.user: discord.User = user
        self.attachment_url: list[str] = attachment_url
        self.reply: discord.Message = reply
        self.reply_images: int = reply_images


    def get_text(self, add_reply: bool = True) -> str:
        prefix = f'Отправил {self.user.display_name}: ' if self.user else ''
        
        if add_reply and self.reply and\
            len(self.reply.content) < 256 and len(self.reply.content) + self.reply_images > 0:
                prefix = f'*Ответ на "{utils.discord_message_to_text(self.reply)}" от '\
                    f'{self.reply.author.display_name}*\n'+prefix
            
        return prefix+self.message


    async def get_data(self, is_last: bool = False, add_reply: bool = True) -> dict:
        text = self.get_text(add_reply)

        if self.attachment_url and is_last:
            content = [{"type": "text", "text": text}]

            async with aiohttp.ClientSession() as session:
                for image in self.attachment_url:
                    async with session.get(image) as resp:
                        if resp.status != 200:
                            raise Exception(f"Failed to fetch image: {resp.status}")
                        
                        encoded_image = base64.b64encode(await resp.read()).decode('utf-8')
                        image_url = f"data:{resp.content_type};base64,{encoded_image}"
                        content.append({"type": "image_url", "image_url": {"url": image_url}})

            return content
        
        return text


class AIHistory:
    def __init__(self):
        self.history: List[AIMessage] = []


    def add(self, message: AIMessage):
        self.history.append(message)
        self.clean_up()


    def clean_up(self):
        new = []
        counter = 0

        for i in self.history[::-1]:
            textlen = len(i.get_text())
            counter += textlen

            # if it's not the 1st message and there's enough characters in history we stop
            if counter > MAX_CHARS_IN_HISTORY and counter > textlen:
                break

            counter += 50
            new.insert(0, i)

        self.history = new


    async def get_history(self) -> dict:
        data = [
            {"role": "system", "content": PROMPT}
        ]
        for index, i in enumerate(self.history):
            is_last = index == len(self.history)-1
            add_reply = index < len(self.history)-1
            data.append({"role": i.role, "content": await i.get_data(is_last, add_reply)})

        return data


# crossposter message history


class Crossposter:
    def __init__(self, file: str):
        self.file: str = file
        self.last_commit: int = 0
        self.reload()


    def new(self):
        '''
        Rewrites the old database with the new one.
        '''
        self.messages: Dict[int, Tuple[int,List[int]]] = {}
        # [Telegram Chat ID, [Discord Message ID, [Telegram Message IDs]]]
        self.commit()


    def panic(self):
        '''
        Creates a duplicate of the database and creates a new one.
        '''
        log('Panic in crossposter file!', 'api', WARNING)

        # copying file
        if os.path.exists(self.file):
            os.rename(self.file, self.file+'.bak')
            log(f'Cloned crossposter data file to {self.file}.bak', 'api')

        # creating a new one
        self.new()


    def reload(self):
        '''
        Reloads crossposter data.
        '''
        # user data
        try:
            with open(self.file, encoding='utf-8') as f:
                data = json.load(f)
        except:
            self.panic()
            return

        self.messages = {int(k): v for k, v in data.get('messages', {}).items()}

        # saving
        self.commit()


    def commit(self):
        '''
        Saves data to the file.
        '''
        if time.time()-self.last_commit < 2:
            return
        self.last_commit = time.time()
        
        data = {
            "messages": self.messages
        }

        # saving
        try:
            json_data = json.dumps(data)
        except Exception as e:
            log(f'Unable to save crossposter data: {e}', 'api', WARNING)
            return

        try:
            with open(self.file+'.temp', 'w') as f:
                f.write(json_data)
                f.flush()
                os.fsync(f.fileno())

            os.replace(self.file+'.temp', self.file)
        except Exception as e:
            log(f'Unable to save crossposter data to file: {e}', 'api', ERROR)


    def add_message(self, chat_id: int, dc_id: int, tg_ids: List[int], preview_text: str, jump_url: str):
        '''
        Adds a pair of IDs to the database.
        '''
        if chat_id not in self.messages:
            self.messages[chat_id] = []

        self.messages[chat_id].append([dc_id, tg_ids, preview_text, jump_url])
        self.commit()


    def get_tg_by_dc(self, dc_id: int) -> Tuple[int, List[int], str, str]:
        '''
        Get Telegram message ID by Discord message ID.

        Returns: (chat_id, message_ids, preview_text, message_url)
        '''
        for chat_id, messages in self.messages.items():
            for message in messages:
                if message[0] == dc_id:
                    return chat_id, message[1], message[2], message[3]
                

    def get_dc_by_tg(self, chat_id: int, tg_id: int) -> Tuple[int, str, str]:
        '''
        Get Discord message ID by Telegram message ID.

        Returns: (message_id, preview_text, message_url)
        '''
        return next((
            (message[0], message[2], message[3]) \
            for message in self.messages.get(chat_id, []) if tg_id in message[1]),
        None)
        

# manager

class Manager:
    def __init__(self, users_file:str, data_file:str, key:str, bot):
        '''
        API and backend manager.
        '''
        self.users_file: str = users_file
        self.data_file: str = data_file
        self.unclaimed: List[int] = []
        self.unclaimed_qs: Dict[int, UnclaimedQ] = {}
        self.in_vc: List[int] = []
        self.temp_vcs: Dict[int, TempVC] = {}
        self.quarantines: Dict[int, int] = {}
        self.renderer = RendererCollection(self, bot)
        self.sk_last_spawn: float = 0
        self.last_commit = 0
        self.roulette_games: List[Roulette] = []
        self.duel_games: List[Duel] = []
        self.ai = AIHistory()
        self.ai_key = key
        self.generating = False
        self.crossposter = Crossposter(CROSSPOSTER_FILE)
        self.reload()


    def new(self):
        '''
        Rewrites the old database with the new one.
        '''
        self.users: Dict[int, User] = {}
        self.timed_lb = TimedLeaderboard()
        self.bump_ping_at = time.time()+BUMP_PING_EVERY
        self.last_bump = 0

        self.commit()


    def panic(self):
        '''
        Creates a duplicate of the database and creates a new one.
        '''
        log('Panic!', 'api', WARNING)

        # copying file
        if os.path.exists(self.users_file):
            os.rename(self.users_file, self.users_file+'.bak')
            log(f'Cloned user data file to {self.users_file}.bak', 'api')

        # creating a new one
        self.new()


    def reload(self):
        '''
        Reloads user data and bot data.
        '''
        # user data
        try:
            with open(self.users_file, encoding='utf-8') as f:
                data = json.load(f)
        except:
            self.panic()
            return

        self.users = {int(id): User(int(id), data) for id, data in data['users'].items()}
        self.temp_vcs = {int(id): TempVC(int(id), data) for id, data in data.get('temp_vcs', {}).items()}
        self.quarantines = {int(id): t for id, t in data.get('quarantines', {}).items()}
        self.timed_lb = TimedLeaderboard(data.get('timed_lb', {}))
        self.sk_last_spawn: float = data.get('sk_last_spawn', 0)
        self.bump_ping_at: float = data.get('bump_ping_at', time.time()+BUMP_PING_EVERY)
        self.last_bump: float = data.get('last_bump', 0)

        # data
        try:
            with open(self.data_file, encoding='utf-8') as f:
                self.data: dict = json.load(f)
        except Exception as e:
            log(f'Unable to load data file: {e}', 'api')

        self.skins: Dict[str, SkinData] = {
            k: SkinData(k, v) for k, v in self.data.get('skins', {}).items()
        }
        self.fonts: Dict[str, FontData] = {
            k: FontData(k, v) for k, v in self.data.get('fonts', {}).items()
        }

        # other data from folder
        
        # emoji list
        try:
            with open(EMOJIS_FILE, encoding='utf-8') as f:
                data = f.read()
                self.emojis: List[str] = data.split('\n')
            log('Reloaded emoji list', 'api')

        except Exception as e:
            log(f'Error while loading emoji list: {e}', 'api', level=ERROR)
        
        # fate actions
        try:
            with open(FATE_ACTIONS_FILE, encoding='utf-8') as f:
                data = f.read()
                self.fate_actions: List[str] = data.split('\n')
            log('Reloaded fate actions', 'api')

        except Exception as e:
            log(f'Error while loading fate actions: {e}', 'api', level=ERROR)

        # saving
        self.commit()


    def commit(self):
        '''
        Saves user data to the file.
        '''
        if time.time()-self.last_commit < 2:
            return
        self.last_commit = time.time()
        
        data = {
            'users': {}
        }

        # users
        for i in self.users:
            data['users'][i] = self.users[i].to_dict()

        data['timed_lb'] = self.timed_lb.to_dict()
        data['temp_vcs'] = {id: i.to_dict() for id, i in self.temp_vcs.items()}
        data['quarantines'] = self.quarantines
        data['sk_last_spawn'] = self.sk_last_spawn
        data['bump_ping_at'] = self.bump_ping_at
        data['last_bump'] = self.last_bump

        # saving
        try:
            json_data = json.dumps(data, indent=4)
        except Exception as e:
            log(f'Unable to save user data: {e}', 'api', WARNING)
            return

        try:
            with open(self.users_file+'.temp', 'w') as f:
                f.write(json_data)
                f.flush()
                os.fsync(f.fileno())

            os.replace(self.users_file+'.temp', self.users_file)
        except Exception as e:
            log(f'Unable to save user data to file: {e}', 'api', ERROR)


    def check_user(self, id:int):
        '''
        Checks if user exists in database. If not, creates one.
        '''
        if id in self.users:
            return
        
        self.users[id] = User(id)


    def get_user(self, id:int):
        '''
        Returns user by ID.
        '''
        self.check_user(id)
        return self.users[id]
    

    def reset_ai(self):
        '''
        Resets AI message context.
        '''
        self.ai = AIHistory()
    

    async def gen_ai(self, history: List[dict]) -> Tuple[str, bytes | None]:
        '''
        Generates an AI message.

        Returns message content and image data, if there is any.
        '''
        async with aiohttp.ClientSession(base_url=BASE_URL, headers={'Authorization': 'Bearer '+self.ai_key}) as session:
            async with session.post('chat/completions', json={
                'model': MODEL,
                'messages': history
            }) as response:
                if response.status != 200:
                    raise Exception(await response.text())
                respjson = await response.json()

        usage = respjson['usage']
        message = respjson['choices'][0]['message']
        text = message['content']

        if 'images' in message:
            img_base64 = message['images'][0]['image_url']['url'].split('base64,')[1]
            return message['content'], base64.b64decode(img_base64)
        
        log(
            f'Prompt tokens: {usage["prompt_tokens"]} / '\
            f'Completion tokens: {usage["completion_tokens"]} / '\
            f'Messages in history: {len(history)}',
        'api')
        return text, None

    def get_roulette_by_user(self, user: int) -> "Roulette | None":
        '''
        Returns a roulette game by user.
        '''
        for i in self.roulette_games:
            if i.user1 == user or i.user2 == user:
                return i
            

    def add_roulette(self, user: int):
        '''
        Create a roulette game.
        '''
        game = Roulette(user, self.remove_roulette)
        self.roulette_games.append(game)
        return game
            
    
    def give_up_roulette(self, user: int) -> "Roulette | None":
        game = self.get_roulette_by_user(user)

        if game is None:
            return

        self.roulette_games.remove(game)
        return game
    

    def remove_roulette(self, game: Roulette, rewardee: int, xp: int):
        self.roulette_games.remove(game)
        if rewardee and xp:
            self.add_xp(rewardee, xp)
    

    def start_roulette(self, user1: int, user2: int) -> "Roulette | None":
        game = self.get_roulette_by_user(user1)
        
        if not game:
            return
        
        if game.user2:
            return
        
        game.start(user2)
        return game


    def get_duel_by_user(self, user: int) -> "Duel | None":
        '''
        Returns a duel game by user.
        '''
        for i in self.duel_games:
            if i.user1 == user or i.user2 == user:
                return i
            

    def add_duel(self, user: int):
        '''
        Create a duel game.
        '''
        game = Duel(user, self.remove_duel)
        self.duel_games.append(game)
        return game
            
    
    def give_up_duel(self, user: int) -> "Duel | None":
        game = self.get_duel_by_user(user)

        if game is None:
            return

        self.duel_games.remove(game)
        game.stopped = True
        return game
    

    def remove_duel(self, game: Duel, rewardee: int, xp: int):
        self.duel_games.remove(game)
        if rewardee and xp:
            self.add_xp(rewardee, xp)
    

    def start_duel(self, user1: int, user2: int) -> "Duel | None":
        game = self.get_duel_by_user(user1)
        
        if not game:
            return
        
        if game.user2:
            return
        
        game.start(user2)
        return game


    def get_random_mfr(self) -> MfrCard:
        '''
        Return a random mishkfrede card
        '''
        rarity = random.choices(
            list(self.data['mfr'].items()),
            [i['chance'] for i in self.data['mfr'].values()]
        )[0]

        url = random.choice(rarity[1]['images'])
        xp = random.randint(*rarity[1]['xp'])
        return MfrCard(rarity[0], rarity[1]['name'], xp, url, rarity[1]['color'])
    

    def bump(self, user_id: int) -> int:
        '''
        Saves a bump and returns gained XP.
        '''
        xp = random.randint(*BUMP_XP)
        self.add_xp(user_id, xp)
        self.bump_ping_at = time.time() + BUMP_TIMEOUT
        self.last_bump = time.time()

        self.commit()
        return xp
    

    def bump_timeout(self) -> int:
        self.bump_ping_at = time.time() + BUMP_PING_EVERY
        self.commit()
    
    
    def add_reminder(self,
        user_id:int,
        message_id:"int | None",
        channel_id:int,
        duration:float,
        jump_url:"str | None",
        text:"str | None"
    ):
        '''
        Adds a reminder.
        '''
        user = self.get_user(user_id)

        reminder = Reminder.convert(
            message_id, channel_id,
            duration, jump_url, text
        )
        user.reminders.append(reminder)

        self.commit()
    

    def remove_reminder(self, user_id:int, index:int):
        '''
        Removes a reminder from a user.
        '''
        user = self.get_user(user_id)
        if index >= len(user.reminders):
            return
        user.reminders.pop(index)
        self.commit()


    def add_q(self, user_id:int, amount:int) -> "int | None":
        '''
        Adds Qs to user and returns the new balance.
        '''
        user = self.get_user(user_id)
        
        user.q += amount
        user.q_level += amount
        if user.q_level > 15:
            user.q_level = 15

        self.commit()
        return user.q


    def add_coin(self, user_id:int, amount:int) -> bool:
        '''
        Exchanges Qs for coins and returns whether it was successful.
        '''
        user = self.get_user(user_id)

        if user.q_level < amount:
            return False
        
        user.q_level -= amount
        user.coins += amount

        self.commit()
        return True


    def add_mfr_stat(self, user_id:int, card:str):
        '''
        Adds Mishkfrede stat to user.
        '''
        user = self.get_user(user_id)

        if user.mfr_timeout < time.time():
            user.mfr_timeout = time.time()+MFR_TIMEOUT

        if card not in user.mfr_stats:
            user.mfr_stats[card] = 0
        user.mfr_stats[card] += 1

        self.commit()


    def add_xp(self, user_id:int, xp:int, store_lvl_up:bool=True) -> "int | None":
        '''
        Adds XP to user.

        If user leveled up, return the new level.
        '''
        user = self.get_user(user_id)

        old_level = deepcopy(user.xp.level)
        user.xp.xp += xp
        user.xp.reload_levels()

        self.timed_lb.add_xp(user_id, xp)
        self.commit()

        if old_level != user.xp.level:
            if store_lvl_up:
                user.to_send_lvl_up_msg = True
                
            return user.xp.level
        

    def set_xp(self, user_id:int, xp:int) -> "int | None":
        '''
        Sets XP to user.

        If user leveled up, return the new level.
        '''
        user = self.get_user(user_id)

        old_level = deepcopy(user.xp.level)
        user.xp.xp = xp
        user.xp.reload_levels()

        if old_level != user.xp.level:
            user.to_send_lvl_up_msg = True
            return user.xp.level
        
        self.commit()


    def check_user_zero(self, user_id:int) -> bool:
        '''
        Checks if user can gain XP for sending zero message.

        If can, update the timer.
        '''
        self.check_user(user_id)

        if time.time()-self.users[user_id].last_sent_zero > 120: # like 2 mins
            self.users[user_id].last_sent_zero = time.time()
            return True
        
        return False


    def get_all_info(self) -> Dict[str, int]:
        '''
        Returns total stats
        '''
        data = {
            "xp": 0,
            "skins": 0,
            "fonts": 0,
            "q": 0
        }
        for i in self.users.values():
            data['xp'] += i.xp.xp
            data['skins'] += len(i.skins.items)
            data['fonts'] += len(i.fonts.items)
            data['q'] += i.q

        return data
    

    def get_lb_finishes(self, user_id:int) -> List[int]:
        finishes: Dict[int,int] = {1:0, 2:0, 3:0}

        for i in self.timed_lb.daily.values():
            if user_id in i:
                place = sorted(i.items(), key=lambda x: x[1], reverse=True).index((user_id, i[user_id]))+1
                if place in finishes:
                    finishes[place] += 1

        return finishes
    

    def set_skin(self, user_id:int, skin:str):
        '''
        Sets skin for a user.
        '''
        user = self.get_user(user_id)
        user.skins._selected = skin

        self.commit()
    

    def add_skin(self, user_id:int, skin:str):
        '''
        Adds skin to a user.
        '''
        user = self.get_user(user_id)

        if skin in user.skins.items:
            return False
        
        user.skins.items.append(skin)
        self.commit()

        return True
    

    def remove_skin(self, user_id:int, skin:str):
        '''
        Removes skin from a user.
        '''
        user = self.get_user(user_id)

        if skin not in user.skins.items:
            return False
        
        user.skins.items.remove(skin)
        self.commit()

        return True
    

    def set_font(self, user_id:int, font:str):
        '''
        Sets font for a user.
        '''
        user = self.get_user(user_id)
        user.fonts._selected = font

        self.commit()
    

    def add_font(self, user_id:int, font:str):
        '''
        Adds font to a user.
        '''
        user = self.get_user(user_id)

        if font in user.fonts.items:
            return False
        
        user.fonts.items.append(font)
        self.commit()

        return True
    

    def remove_font(self, user_id:int, font:str):
        '''
        Removes font from a user.
        '''
        user = self.get_user(user_id)

        if font not in user.fonts.items:
            return False
        
        user.fonts.items.remove(font)
        self.commit()

        return True
    
    
    def get_random_skin(self) -> SkinData:
        '''
        Returns a random skin.
        '''
        skin = random.choices(
            list(self.skins.values()),
            [i.rarity for i in self.skins.values()]
        )[0]
        return skin
    
    
    def get_random_font(self) -> FontData:
        '''
        Returns a random font.
        '''
        font = random.choices(
            list(self.fonts.values()),
            [i.rarity for i in self.fonts.values()]
        )[0]
        return font
    

    def set_last_msg_channel(self, user_id:int, channel_id:int):
        '''
        Sets last message channel for a user.
        '''
        user = self.get_user(user_id)
        user.last_msg_channel = channel_id
        self.commit()


    def repblock(self, id: int, length: int):
        '''
        Repblocks the user
        '''
        user = self.get_user(id)
        user.rep_block_until = time.time()+length
        self.commit()


    def add_rep(self, id: int, amount: int, placer: int = None) -> "float | None":
        '''
        Changes user's rep count.

        Returns a float that indicates when to try again if action is timeouted
        '''
        user = self.get_user(id)

        if placer != None:
            placer: User = self.get_user(placer)

            if amount > 0:
                if placer.plus_rep_timeout > time.time():
                    return placer.plus_rep_timeout
                placer.plus_rep_timeout = time.time()+PLUS_REP_EVERY

            elif amount < 0:
                if placer.id in user.minus_repped:
                    if user.minus_repped[placer.id] > time.time():
                        return user.minus_repped[placer.id]
                
                if placer.minus_rep_timeout > time.time():
                    return placer.minus_rep_timeout
                
                placer.minus_rep_timeout = time.time()+MINUS_REP_EVERY
                user.minus_repped[placer.id] = time.time()+MINUS_REP_COUNTER_TIMEOUT

        if amount > 0:
            user.plus_reps += amount
        else:
            user.minus_reps -= amount

        self.commit()


    def get_rep_limits(self) -> Tuple[int,int]:
        '''
        Returns a tuple with 1st value being the lower limit and 2nd value being the upper limit of reputation.
        '''
        rep = [i.rep for i in self.users.values()]
        return min(rep), max(rep)


    def update_vc_state(self, id: int, state: discord.VoiceState) -> str:
        '''
        Updates the vc state of a user.
        '''
        user = self.get_user(id)

        if state == None or state.channel == None:
            user.vc.state = 'none'
            user.vc.is_streaming = False

            if user.id in self.in_vc:
                self.in_vc.remove(user.id)

            return user.vc.state
        
        if user.id not in self.in_vc:
            self.in_vc.append(user.id)

        if state.self_deaf or state.deaf:
            user.vc.state = 'deafen'

        elif state.self_mute or state.mute:
            user.vc.state = 'mute'

        else:
            user.vc.state = 'normal'

        user.vc.is_streaming = state.self_stream or state.self_video

        return user.vc.state


    def update_vc_xp(self, id: int):
        '''
        Updates the vc xp of a user.
        '''
        user = self.get_user(id)

        # checking xp
        xp = user.vc.xp_mult * 1/60

        # adding stats
        user.vc.vc_time += 1

        if user.vc.is_streaming:
            user.vc.vc_time_streaming += 1

        if user.vc.state == 'normal':
            user.vc.vc_time_speaking += 1

        # not adding xp if alone in vc
        if len(self.in_vc) == 1:
            return
        user.vc.xp_to_add += xp

        # adding xp
        while user.vc.xp_to_add >= 1:
            self.add_xp(id, 1)
            user.vc.xp_to_add -= 1

        self.commit()


    def get_temp_vc(self, id: int) -> "TempVC | None":
        '''
        Returns a temporary VC of a user, if there is one.
        '''
        for i in self.temp_vcs.values():
            if i.owner_id == id:
                return i


    def new_temp_vc(self, name: str, id: int, user: User):
        '''
        Creates a new temporary vc.
        '''
        vc = TempVC(id, {"owner_id": user.id, "name": name})
        self.temp_vcs[id] = vc

        user.temp_vc_timeout = time.time()+TEMP_VC_CREATION_TIMEOUT
        self.commit()
    

    def get_leaders(self, type: Literal['alltime','season','week','day','vc','stream','mic','q','rep'], places=9) -> List[User]:
        '''
        Returns a list of users sorted by type.
        '''
        if type == 'alltime':
            users = sorted(self.users.values(), key=lambda x: x.xp.total_xp, reverse=True)
        elif type == 'season':
            users = sorted(self.users.values(), key=lambda x: x.xp.xp, reverse=True)
        elif type == 'week':
            users = sorted(self.users.values(), key=lambda x: self.timed_lb.get_weekly_xp(x.id), reverse=True)
        elif type == 'day':
            users = sorted(self.users.values(), key=lambda x: self.timed_lb.get_daily_xp(x.id), reverse=True)
        elif type == 'vc':
            users = sorted(self.users.values(), key=lambda x: x.vc.vc_time, reverse=True)
        elif type == 'stream':
            users = sorted(self.users.values(), key=lambda x: x.vc.vc_time_streaming, reverse=True)
        elif type == 'mic':
            users = sorted(self.users.values(), key=lambda x: x.vc.vc_time_speaking, reverse=True)
        elif type == 'q':
            users = sorted(self.users.values(), key=lambda x: x.q, reverse=True)
        elif type == 'rep':
            users = sorted([i for i in self.users.values() if i.plus_reps != 0 or i.minus_reps != 0], key=lambda x: x.rep, reverse=True)
        return users[:places]
    

    def get_place(self, user_id:int, type: Literal['alltime','season','week','day','vc','stream','mic','q','rep']) -> int:
        users = self.get_leaders(type, places=99999)

        place = 0
        prev_xp = None

        for i in users:
            if type == 'alltime':
                xp = i.xp.total_xp
            elif type == 'season':
                xp = i.xp.xp
            elif type == 'week':
                xp = self.timed_lb.get_weekly_xp(i.id)
            elif type == 'day':
                xp = self.timed_lb.get_daily_xp(i.id)
            elif type == 'vc':
                xp = i.vc.vc_time
            elif type == 'stream':
                xp = i.vc.vc_time_streaming
            elif type == 'mic':
                xp = i.vc.vc_time_speaking,
            elif type == 'q':
                xp = i.q
            elif type == 'rep':
                xp = i.rep
                if i.plus_reps == 0 and i.minus_reps == 0:
                    prev_xp = xp
                    continue

            if prev_xp != xp:
                place += 1
                prev_xp = xp

            if i.id == user_id:
                return place
    

    def add_quarantine(self, user_id: int, t: int):
        '''
        Sends someone to quarantine
        '''
        self.check_user(user_id)
        self.quarantines.update({user_id: t})
        self.commit()
    
    def remove_quarantine(self, user_id: int):
        '''
        Removes someone from quarantine
        '''
        self.check_user(user_id)
        self.quarantines.pop(user_id)
        self.commit()


def predicate(ctx: commands.Context):
    if not ctx.guild:
        return False
    if ctx.guild.id != GUILD_ID:
        return False
    return True

check_guild = commands.check(predicate)
