from typing import *
import pygame as pg
from log import *
from config import *
from .renderer import *
from .elements import BaseElement


GAP_SURFACE = pg.Surface((WIDTH, 100), pg.SRCALPHA)
GAP_SURFACE.fill((0,0,0,GAP_SURFACE_OPACITY))


class CBox:
    def __init__(self, elements: List[BaseElement | int], user):
        '''
        Collection of renderers.
        '''
        self.elements: List[BaseElement | int] = elements
        self.user = user

    
    def render(self, r: Renderer, is_tg: bool = True) -> pg.Surface:
        # rendering overlay
        surfaces = []
        masks = []
        height = 0

        for element in self.elements:
            # gap
            if isinstance(element, int):
                surfaces.append(element)
                height += element
                
                if not is_tg:
                    masks.append(element)

            # image
            else:
                surface = element.render_overlay(r, self.user)
                surfaces.append(surface)
                height += surface.height

                if not is_tg:
                    mask = element.render_mask(surface)
                    masks.append(mask)

        # rendering result
        result = pg.Surface((WIDTH, height), pg.SRCALPHA)
        pos = 0

        for i in surfaces:
            # gap
            if isinstance(i, int):
                if is_tg:
                    n = pg.transform.scale(GAP_SURFACE.copy(), (WIDTH, i))

                    result.blit(n, (0, pos))

                pos += i

            # surface
            else:
                result.blit(i, (0, pos))
                pos += i.height
        
        # background
        bg = pg.Surface((WIDTH, height), pg.SRCALPHA)

        if height >= WIDTH:
            r.draw_image(
                self.user.skins.skin(), (WIDTH//2, 0),
                size=(height, height), h=0.5, surface=bg
            )

        else:
            r.draw_image(
                self.user.skins.skin(), (0, height//2),
                size=(WIDTH, WIDTH), v=0.5, surface=bg
            )
            
        bg.blit(result, (0,0))

        # masks
        if not is_tg:
            pos = 0
            for i in masks:
                if isinstance(i, int):
                    pg.draw.rect(bg, (0,0,0,0), (0, pos, WIDTH, i))
                    pos += i

                else:
                    bg.blit(i, (0, pos), special_flags=pg.BLEND_RGBA_SUB)
                    pos += i.height

        # result
        r.surface = bg

        return bg