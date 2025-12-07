import asyncio
import random
from typing import *

from config import *
from log import *


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

