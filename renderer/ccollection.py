import copy
from tkinter.constants import N
from typing import *
import pygame as pg
from log import *
from config import *
from .renderer import *
from .cbox import CBox
from .elements import *


class CCollection:
    def __init__(self, mg, bot):
        '''
        Collection of renderers.
        '''
        self.mg = mg
        self.bot = bot


    def user_xp(self, mg, user, is_tg: bool = True) -> str:
        '''
        Renders the XP embed for a discord user.
        '''
        r = Renderer((WIDTH, 100), (0,255,0))

        c = CBox([
            XPTitle(),
            14,
            XPElement(),
            14,
            XPLB(user, mg),
        ], user)
        c.render(r, is_tg)

        path = r.save('temp', 'png')
        return path


    def collectible_popup(self,
        user, text: str, name: str, skin: str = None,
        font: str = None, is_tg: bool = True
    ) -> str:
        '''
        Renders the skin/font collection or set popup.
        '''
        r = Renderer((WIDTH, 100), (0,255,0))

        # editing font / skin
        user = copy.deepcopy(user)

        if skin:
            user.skins._selected = skin
        if font:
            user.fonts._selected = font

        # rendering
        c = CBox([
            CTextBox([
                CTextRow([
                    CText(text, 20, user.fonts.font('regular'), opacity=128),
                    CText(' '+name+'!', 20, user.fonts.font('bold'))
                ]),
            ], 15, 20, 30, 30)
        ], user)
        c.render(r, is_tg)

        path = r.save('temp', 'png')
        return path


    def skin_claim(self, user, skin, is_tg: bool = True) -> str:
        return self.collectible_popup(
            user, 'Вы получили скин', skin.name, skin=skin.key, is_tg=is_tg
        )

    def font_claim(self, user, font, is_tg: bool = True) -> str:
        return self.collectible_popup(
            user, 'Вы получили шрифт', font.name, font=font.key, is_tg=is_tg
        )

    def skin_set(self, user, skin, is_tg: bool = True) -> str:
        return self.collectible_popup(
            user, 'Вы установили скин', skin.name, skin=skin.key, is_tg=is_tg
        )

    def font_set(self, user, font, is_tg: bool = True) -> str:
        return self.collectible_popup(
            user, 'Вы установили шрифт', font.name, font=font.key, is_tg=is_tg
        )


    def skin_list(self, mg, user, is_tg: bool = True) -> str:
        '''
        Renders the skin inventory for a user.
        '''
        r = Renderer((WIDTH, 100), (0,255,0))

        # computing skins
        totalskins = len(mg.skins)
        unlocked = len(user.skins.items)

        if user.id == BOT_ID:
            totalskins = 24
            unlocked = '09'

        rows = [[]]

        for index, i in enumerate(mg.skins.values()):
            rows[-1].append((index, i))
            if len(rows[-1]) == 8:
                rows.append([])

        skins = []

        for i in rows:
            skins.append(SkinBody(user, mg, i))
            skins.append(5)

        # rendering
        texts = [CText('ml!setskin <номер> ', 14, user.fonts.font('medium'), opacity=128)]

        if user.skins._selected:
            texts.extend([
                CText('или', 14, user.fonts.font(), opacity=128),
                CText(' ml!removeskin ', 14, user.fonts.font('medium'), opacity=128)
            ])

        texts.append(CText('для смены', 14, user.fonts.font(), opacity=128))

        c = CBox([
            CTextBox([
                CText(f"Скины {user.name}", 20, user.fonts.font('bold')),
                8,
                CTextRow([
                    CText("Разблокировано: ", 16, user.fonts.font(), opacity=128),
                    CText(f"{unlocked} / {totalskins}", 16, user.fonts.font('medium'))
                ]),
            ], 12, 12, 30, 7),
            5,
            *skins,
            CTextBox([
                CTextRow(texts)
            ], 12, 16, 7, 30)
        ], user)
        c.render(r, is_tg)

        path = r.save('temp', 'png')
        return path
