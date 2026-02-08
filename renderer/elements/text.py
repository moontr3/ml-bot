from typing import *

from pydantic.fields import PropertyT
from ..renderer import Renderer
from .base import BaseElement
import pygame as pg
from config import *


class CText:
    def __init__(self,
        text: str, size: int, font: str,
        opacity: int = 255, margin: int = 18
    ):
        self.text = text
        self.size = size
        self.font = font
        self.opacity = opacity
        self.margin = margin


    def render_simple(self, r: Renderer) -> pg.Surface:
        '''
        Used in CTextRow.render to render text elements.
        '''
        return r.render_text(
            self.text, self.font, self.size,
            (255,255,255), opacity=self.opacity
        )


    def render(self, r: Renderer) -> pg.Surface:
        '''
        Used for rendering standalone text elements.
        '''
        s = r.render_text(
            self.text, self.font, self.size,
            (255,255,255), opacity=self.opacity
        )
        max_width = WIDTH-self.margin*2
        if max_width < s.get_width():
            s = pg.transform.smoothscale(s, (max_width, s.get_height()))

        return s


class CTextRow:
    def __init__(self, elements: List[CText], margin: int = 18):
        self.elements = elements
        self.margin = margin


    def render(self, r: Renderer) -> pg.Surface:
        '''
        Render all child elements and compose them into a single surface.
        '''
        # rendering texts individually
        surfaces = []
        height = 0
        width = 0

        for i in self.elements:
            text = i.render_simple(r)
            surfaces.append(text)
            if height < text.get_height():
                height = text.get_height()
            width += text.get_width()

        # composing into a single surface
        s = pg.Surface((width, height), pg.SRCALPHA)

        pos = 0
        for i in surfaces:
            s.blit(i, (pos, 0))
            pos += i.get_width()

        # checking if its too wide
        max_width = WIDTH-self.margin*2

        if max_width < width:
            s = pg.transform.smoothscale(s, (max_width, height))

        return s


class CTextBox(BaseElement):
    def __init__(self,
        elements: List[CTextRow | CText | int],
        margin_top: int = 10, margin_bottom: int = 10,
        round_top: int = 30, round_bottom: int = 7
    ):
        super().__init__()
        self.elements = elements
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.round_top = round_top
        self.round_bottom = round_bottom


    def render_mask(self, surface: pg.Surface) -> pg.Surface:
        return self._render_mask(surface.get_size(), [
            self.round_top, self.round_top,
            self.round_bottom, self.round_bottom
        ])


    def render_overlay(self, r: Renderer, user) -> pg.Surface:
        '''
        Render textbox.
        '''
        height = self.margin_top+self.margin_bottom
        surfaces = []

        for i in self.elements:
            if isinstance(i, int):
                surfaces.append(i)
                height += i

            else:
                s = i.render(r)
                surfaces.append(s)
                height += s.get_height()

        # composing into a single surface
        s = pg.Surface((WIDTH, height), pg.SRCALPHA)

        pos = self.margin_top
        for i, element in zip(surfaces, self.elements):
            if isinstance(i, int):
                pos += i

            else:
                s.blit(i, (element.margin, pos))
                pos += i.get_height()

        return s
