import random
from typing import *

import numpy as np

import utils
from .renderer import Renderer
import easing_functions as easing
import pygame as pg


class ColumnEffect:
    def __init__(self, r: Renderer, column: int):
        self.r = r
        self.pos = column*114
        self.lifetime: int = 10
        self.max_lifetime = 10


    def draw(self, surface: pg.Surface):
        opacity = easing.SineEaseIn().ease(self.lifetime/self.max_lifetime)*128
        self.r.draw_image('assets/glow.png', (self.pos, 0), (112, 290), opacity=opacity, surface=surface)


    def update(self):
        self.lifetime -= 1


class HitEffect:
    def __init__(self, r: Renderer, pos: int, index: int):
        self.r = r
        self.pos = pos

        pos = utils.index_to_roulette_pos(pos)
        self.x = pos[0]
        self.y = pos[1]

        self.size_mod = index*3
        self.lifetime = 20+index
        self.max_lifetime = 20+index


    def draw(self, surface: pg.Surface):
        ease = easing.ExponentialEaseIn().ease(self.lifetime/self.max_lifetime)
        opacity = ease*255
        size = 200-ease*60+self.size_mod

        self.r.draw_image(
            'assets/fxglow.png', (self.x, self.y), (size, size),
            0.5, 0.5, opacity=opacity, surface=surface
        )


    def update(self):
        self.lifetime -= 1


# class HitNumber:
#     def __init__(self, r: Renderer, poss: List[int], text: str, index: int):
#         self.r = r
#         self.text = text

#         pos1 = utils.index_to_roulette_pos(poss[0])
#         pos2 = utils.index_to_roulette_pos(poss[-1])
#         self.x = (pos1[0]+pos2[0])//2
#         self.y = (pos1[1]+pos2[1])//2
#         self.rot = 0

#         self.x_vel = random.uniform(-3, 3)
#         self.y_vel = random.uniform(-5, -1.5)
#         self.rot_vel = random.uniform(-3, 3)

#         self.size = 40+index
#         self.lifetime = 35
#         self.max_lifetime = 35


#     def draw(self, surface: pg.Surface):
#         opacity = min(255, self.lifetime/6*255)
#         size = self.size-(self.lifetime/self.max_lifetime*10)

#         self.r.draw_text(
#             self.text, (self.x, self.y), 'assets/captchafont.ttf', int(size),
#             (255, 230, 55), 0.5, 0.5, rotation=self.rot, opacity=opacity, surface=surface
#         )

#     def update(self):
#         self.lifetime -= 1

#         self.x += self.x_vel
#         self.y += self.y_vel
#         self.rot += self.rot_vel

#         self.y_vel += 0.3


class HitNumber:
    def __init__(self, r: Renderer, poss: List[int], text: str, index: int):
        self.r = r
        self.text = text

        pos1 = utils.index_to_roulette_pos(poss[0])
        pos2 = utils.index_to_roulette_pos(poss[-1])
        self.x = (pos1[0]+pos2[0])//2
        self.y = (pos1[1]+pos2[1])//2

        self.size = 12+index
        self.lifetime = 35
        self.max_lifetime = 35


    def draw(self, surface: pg.Surface):
        opacity = min(255, self.lifetime/6*255)
        size = self.size+(5-self.lifetime/self.max_lifetime*5)
        size_y = size*1.5
        image = 'wn' if self.lifetime % 4 >= 2 else 'n'

        # drawing images
        x = self.x-(len(self.text)-1)/2*size

        for char in self.text:
            self.r.draw_image(
                f'assets/{image}{char}.png', (x, self.y), (size, size_y),
                0.5, 0.5, opacity=opacity, surface=surface
            )
            x += size


    def update(self):
        self.lifetime -= 1

        self.y -= 0.5
        if self.lifetime > 27:
            self.y -= 2


class HitParticle:
    def __init__(self, r: Renderer, pos: int):
        self.r = r
        self.pos = pos

        pos = utils.index_to_roulette_pos(pos)
        self.x = pos[0]
        self.y = pos[1]
        self.x_vel = random.randint(-10, 10)
        self.y_vel = random.randint(-10, 10)

        self.size = random.randint(4,16)
        self.style = random.randint(1, 3)

        self.lifetime = random.randint(5, 20)


    def draw(self, surface: pg.Surface):
        opacity = easing.ExponentialEaseOut().ease(self.lifetime/19)*255

        if opacity <= 0:
            return
        
        self.r.draw_image(
            f'assets/particle{self.style}.png', (self.x, self.y),
            (self.size, self.size), 0.5, 0.5, surface=surface, opacity=opacity
        )


    def update(self):
        self.lifetime -= 1

        self.x += self.x_vel
        self.y += self.y_vel

        self.x_vel *= 0.9
        self.y_vel *= 0.9


# effect manager


class Effects:
    def __init__(self, r: Renderer):
        self.r = r
        self.effects: List[ColumnEffect] = []
        self.text: str = 'КРУТИМ'


    @property
    def ended(self) -> bool:
        return len(self.effects) == 0


    def add(self, effect):
        self.effects.append(effect)

    
    def update(self, surface: pg.Surface):
        new = []

        for effect in self.effects:
            effect.update()
            effect.draw(surface)

            if effect.lifetime > 0:
                new.append(effect)

        self.r.draw_text(
            self.text, (200, 35), 'assets/gamblingfont.ttf', 24,
            (255,115,35), 0.5, 0.5
        )
        self.effects = new


# renderer


class RouletteRenderer:
    def __init__(self, mg, bot):
        '''
        Collection of renderers for roulette (slot machine).
        '''
        self.mg = mg
        self.bot = bot


    def add_text(self, r: Renderer, text: str):
        r.draw_text(
            text, (200, 35), 'assets/gamblingfont.ttf', 24,
            (255,115,35), 0.5, 0.5
        )


    def draw_static_pattern(self, r: Renderer, surface: pg.Surface, pattern):
        for column in range(3):
            xpos = 58+column*112

            for index, element in enumerate(pattern.get_column(column)):
                ypos = 55+index*90
                r.draw_image(
                    f'assets/gambling/{pattern.skin}/{element}.png', (xpos, ypos),
                    (80,80), 0.5, 0.5, surface=surface
                )


    def static(self, text: str, pattern = None) -> str:
        r = Renderer(image='assets/gamblingbg.png')

        # text
        self.add_text(r, text)

        # pattern
        if pattern:
            surface = pg.Surface((340, 290), pg.SRCALPHA)
            self.draw_static_pattern(r, surface=surface, pattern=pattern)
            r.surface.blit(surface, (30, 85))

        # exporting
        path = r.save('temp', 'png')
        return path
    

    def gif(self, pattern) -> Tuple[str, int]:
        skin: str = pattern.skin
        columns = [
            pattern.get_column(index)+[random.randint(1,8) for _ in range(10)]
            for index in range(3)
        ]
        columns_scroll_ended = [False, False, False]

        column_height = len(columns[0])*90
        ease1 = easing.BackEaseOut()
        ease2 = easing.SineEaseOut()

        # rendering
        r = Renderer(image=f'assets/gamblingbg.png')
        effects = Effects(r)

        # spinning anim
        frames = 50

        for frame in range(frames+1):
            # columns
            anim = pg.Surface((340, 290), pg.SRCALPHA)
            xpos = 58

            for i, column in enumerate(columns):
                index = min(1, frame/(frames-20+i*10))

                if index == 1 and not columns_scroll_ended[i]:
                    effects.add(ColumnEffect(r, i))
                    columns_scroll_ended[i] = True

                ease = ease1.ease(index)*0.4+ease2.ease(index)*0.6
                ypos = -column_height+ease*column_height+55
            
                for element in column:
                    if ypos < -40:
                        ypos += 90
                        continue

                    if ypos > 330:
                        ypos += 90
                        continue

                    offset = max(0, (1-ease)*40)

                    r.draw_image(
                        f'assets/gambling/{skin}/{element}.png', (xpos, ypos),
                        (80-offset,80+offset), 0.5, 0.5, surface=anim
                    )
                    ypos += 90
                
                xpos += 112

            amount = round(np.sin(frame/5)*3+3)
            effects.text = (' '*amount) + 'КРУТИМ' + (' '*(5-amount))
            effects.update(anim)
            r.surface.blit(anim, (30, 85))

            # new frame
            r.new_image(image=f'assets/gamblingbg.png')

        # count anim
        items: List[Tuple[List[int], int]] = pattern.get_patterns()
        frames = 15

        for index, item in enumerate(items):
            p, xp = item[0], item[1]
            effects.text = f'КОМБО X{index+1}'

            # adding effects
            effects.add(HitNumber(r, p, f'+{xp}', index))

            for pos in p:
                effects.add(HitEffect(r, pos, index))
                
                for i in range(min(15, 4+index)):
                    effects.add(HitParticle(r, pos))

            # drawing effects
            for frame in range(int(frames)):
                anim = pg.Surface((340, 290), pg.SRCALPHA)

                # drawing static image
                self.draw_static_pattern(r, anim, pattern)
                effects.update(anim)
                r.surface.blit(anim, (30, 85))

                r.new_image(image=f'assets/gamblingbg.png')

            frames *= 0.9

        effects.text = f'+{pattern.get_xp()}XP - КОМБО X{len(items)}' if len(items) > 0 else 'НЕУДАЧА...'

        # finishing effects
        counted = False

        while not effects.ended or not counted:
            counted = True

            anim = pg.Surface((340, 290), pg.SRCALPHA)

            # drawing static image
            self.draw_static_pattern(r, anim, pattern)

            effects.update(anim)
            r.surface.blit(anim, (30, 85))

            # new frame
            if not effects.ended:
                r.new_image(image=f'assets/gamblingbg.png')

        # exporting
        path = r.to_gif('temp', 30)
        return path, len(r.surfaces)