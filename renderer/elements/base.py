from typing import *
from ..renderer import Renderer
import pygame as pg
from config import *


class BaseElement:
    def __init__(self):
        pass


    def _render_mask(self, size: Tuple[int,int], corners: Tuple[int,int,int,int]=(30,30,30,30)) -> pg.Surface:
        surface = pg.Surface(size, pg.SRCALPHA)
        surface.fill((0,0,0,255))
        pg.draw.rect(surface, (0,0,0,0), surface.get_rect(), 0, -1, *[i+1 for i in corners])

        for index, i in enumerate([
            (corners[0],           corners[0]          ),
            (size[0]-corners[1]-1, corners[1]          ),
            (corners[2],           size[1]-corners[2]-1),
            (size[0]-corners[3]-1, size[1]-corners[3]-1),
        ]):
            pg.draw.aacircle(surface, (0,0,0,0), i, corners[index])

        return surface


    def render_mask(self, surface: pg.Surface) -> pg.Surface:
        return self._render_mask(surface.size)


    def render_overlay(self, r: Renderer, user) -> pg.Surface:
        surface = pg.Surface((WIDTH, 100), pg.SRCALPHA)
        r.draw_text(
            'Test element', surface.get_rect().center, user.fonts.font(), 20,
            (255,255,255), h=0.5, v=0.5, opacity=128, surface=surface
        )
        return surface
