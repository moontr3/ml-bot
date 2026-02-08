from typing import *

from pydantic.fields import PropertyT
from ..renderer import Renderer
from .base import BaseElement
import pygame as pg
from config import *


class SkinBody(BaseElement):
    def __init__(self, user, mg, skins: List[Tuple]):
        self.user = user
        self.mg = mg
        self.skins = skins

        super().__init__()


    def render_mask(self, surface: pg.Surface) -> pg.Surface:
        surface = pg.Surface(surface.size, pg.SRCALPHA)

        size = (48, 48)
        pos = 0

        for i in range(len(self.skins)):
            surface.blit(self._render_mask(size, (7,7,7,7)), (pos, 0))
            pos += 48

            width = 5
            if i == len(self.skins)-1:
                width = (8-len(self.skins))*53

            pg.draw.rect(surface, (0,0,0,255), (pos, 0, width, 48))
            pos += 5

        return surface


    def render_overlay(self, r: Renderer, user) -> pg.Surface:
        surface = pg.Surface((WIDTH, 48), pg.SRCALPHA)

        pos = 0
        width = 48

        for i, (index, skin) in enumerate(self.skins):
            # skin
            r.draw_image(f"assets/badges/{skin.key}.png", (pos,0), (48,48), surface=surface)

            # selected
            if skin.key == user.skins.selected:
                r.draw_image('assets/ui/selected.png', (pos,0), (48,48), surface=surface)
                r.draw_text(
                    f'{index+1}', (pos+6,2), user.fonts.font('bolditalic'), 14, (132,255,87),
                    opacity=128, surface=surface
                )

            # locked
            elif skin.key not in user.skins.items:
                r.draw_image('assets/ui/locked.png', (pos,0), surface=surface)

            # unlocked
            else:
                r.draw_text(
                    f'{index+1}', (pos+6,2), user.fonts.font('bolditalic'), 14, (255,255,255),
                    opacity=128, surface=surface
                )

            # dark part
            pos += width

            # gray part
            gray_size = 5
            if i == len(self.skins)-1:
                gray_size = (8-len(self.skins))*53

            s = pg.Surface((gray_size, 48), pg.SRCALPHA)
            s.fill((0,0,0,GAP_SURFACE_OPACITY))
            surface.blit(s, (pos,0))

            pos += 5

        return surface
