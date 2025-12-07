import asyncio
import random
from typing import *

from config import *
from log import *
import utils

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
