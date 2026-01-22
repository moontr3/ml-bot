from typing import *
from ..renderer import Renderer
from .base import BaseElement
import pygame as pg
from config import *


class XPTitle(BaseElement):
    def __init__(self):
        super().__init__()


    def render_overlay(self, r: Renderer, user) -> pg.Surface:
        surface = pg.Surface((WIDTH, 60), pg.SRCALPHA)
        level_color = (200,200,200)
        level_name = 'в тг пока WIP'

        # level
        max_pos = r.draw_text(
            level_name, (WIDTH-22,28), user.fonts.font('medium'),
            20, level_color, h=1, v=0.5, surface=surface
        )[0]
        
        pg.draw.circle(
            surface, level_color, (WIDTH-42-max_pos, 29), 12
        )
        r.draw_text(
            f'{user.xp.level}', (WIDTH-42-max_pos, 29), user.fonts.font('bold'),
            16, (35,35,35), h=0.5, v=0.5, surface=surface, max_size=22
        )

        # name
        r.draw_text(
            user.name, (20, 28), user.fonts.font('bold'), 20,
            (255,255,255), max_size=WIDTH-(max_pos+80), v=0.5, surface=surface
        )

        return surface


class XPElement(BaseElement):
    def __init__(self):
        super().__init__()


    def render_overlay(self, r: Renderer, user) -> pg.Surface:
        surface = pg.Surface((WIDTH, 112), pg.SRCALPHA)
        level_color = (200,200,200)

        # main xp
        r.draw_text(
            f"{user.xp.xp} XP", (16, 29), user.fonts.font('bold'), 24, (255,255,255),
            v=0.5, surface=surface
        )

        size = r.draw_text(
            f"{user.xp.total_xp} XP", (WIDTH-16,29), user.fonts.font(), 24, (255,255,255),
            h=1, v=0.5, opacity=128, surface=surface
        )[0]
        r.draw_text(
            'всего', (WIDTH-16-size-5, 29), user.fonts.font(), 20, (255,255,255), 
            h=1, v=0.5, opacity=128, surface=surface
        )

        # xp limit
        r.draw_text(
            f"{user.xp.level_xp} XP", (16,60), user.fonts.font(), 14, (255,255,255),
            surface=surface, v=0.5
        )
        r.draw_text(
            f"{user.xp.level_max_xp} XP", (WIDTH-16, 60), user.fonts.font(),
            14, (255,255,255), h=1, v=0.5, opacity=128, surface=surface
        )

        # bar
        bar_width = WIDTH-32

        barsurface = pg.Surface((bar_width, 20), pg.SRCALPHA)
        pg.draw.rect(barsurface, (0,0,0,50), (0, 0, bar_width, 20), border_radius=10)
        surface.blit(barsurface, (16,77))

        barsurface = pg.Surface((bar_width, 20), pg.SRCALPHA)
        rect = pg.Rect((-30,0), (30+bar_width*user.xp.level_percentage, 20))
        pg.draw.rect(barsurface, level_color, rect, border_radius=10)
        image = r.round_image(barsurface, 10)
        surface.blit(image, (16,77))

        # percentage
        percentage = f'{int(user.xp.level_percentage*100)}%'

        if rect.right > 30:
            r.draw_text(
                percentage, (rect.right-5+15, rect.centery+76),
                user.fonts.font('bold'), 14, (35,35,35), h=1, v=0.5, surface=surface
            )
        else:
            r.draw_text(
                percentage, (rect.right+5+15, rect.centery+76),
                user.fonts.font('medium'), 14, (200,200,200), v=0.5, surface=surface
            )

        return surface


class XPLB(BaseElement):
    def __init__(self, user, mg, is_vc: bool = False):
        if not is_vc:
            self.segments = [
                (
                    'сегодня',
                    mg.get_place(user.id, 'day'),
                    f"{mg.timed_lb.get_daily_xp(user.id)} XP"
                ), (
                    'неделя',
                    mg.get_place(user.id, 'week'),
                    f"{mg.timed_lb.get_weekly_xp(user.id)} XP"
                ), (
                    'сезон',
                    mg.get_place(user.id, 'season'),
                    None
                ),
            ]

        else:
            t = user.vc.vc_time_streaming
            vc_stream_str = f'{t//60//60}:{t//60%60:02}:{t%60:02}'
            t = user.vc.vc_time_speaking
            vc_speak_str = f'{t//60//60}:{t//60%60:02}:{t%60:02}'

            self.segments = [
                (
                    'войс',
                    mg.get_place(user.id, 'vc'),
                    None
                ), (
                    'стрим',
                    mg.get_place(user.id, 'stream'),
                    vc_stream_str
                ), (
                    'с микро',
                    mg.get_place(user.id, 'mic'),
                    vc_speak_str
                ),
            ]

        super().__init__()


    def render_mask(self, surface: pg.Surface) -> pg.Surface:
        surface = pg.Surface(surface.size, pg.SRCALPHA)

        size = (136, 60)
        roundings = [
            (30,7,30,7),
            (7,7,7,7),
            (7,30,7,30)
        ]
        pos = 0

        for i in roundings:
            surface.blit(self._render_mask(size, i), (pos, 0))
            pos += 136

            pg.draw.rect(surface, (0,0,0,255), (pos, 0, 6, 60))
            pos += 6

        return surface


    def render_overlay(self, r: Renderer, user) -> pg.Surface:
        surface = pg.Surface((WIDTH, 60), pg.SRCALPHA)

        pos = 0
        width = 136

        for index, (text, place, value) in enumerate(self.segments):
            # place
            if place:
                # bg
                if place < 4:
                    r.draw_image(
                        f'assets/ui/xp{place}.png', (pos, 0), (width, 60), surface=surface
                    )

                # place
                color = (251,172,24) if place == 1 else\
                    (140,140,140) if place == 2 else\
                    (148,66,31) if place == 3 else\
                    (192,192,192)
                
                r.draw_text(
                    f"#{place}", (pos+17,30), user.fonts.font('bolditalic'),
                    20, color, v=0.5, surface=surface
                )

            # texts
            xoffset = -6 if index == 2 else 0
            titlepos = 19 if value else 30
            r.draw_text(
                text, (pos+width-15+xoffset, titlepos), user.fonts.font(),
                14, (255,255,255), h=1, v=0.5, surface=surface, opacity=152
            )

            if value:
                r.draw_text(
                    value, (pos+width-15+xoffset, 40), user.fonts.font('bold'),
                    14, (255,255,255), h=1, v=0.5, surface=surface, opacity=152
                )

            # dark part
            pos += width

            s = pg.Surface((6, 60), pg.SRCALPHA)
            s.fill((0,0,0,64))
            surface.blit(s, (pos,0))

            pos += 6

        return surface