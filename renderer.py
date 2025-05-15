import random
import discord
from typing import *
from copy import deepcopy
import pygame as pg
import aiohttp
import aiofiles
from log import *
import time
import os
import utils
from config import *

pg.display.init()
pg.font.init()


# pygame renderer

class Renderer:
    def __init__(self,
        size: Tuple[int, int] = None,
        fill: "Tuple[int, int, int] | None" = None,
        image: "str | None" = None
    ):
        '''
        A class that you can render images in.
        '''
        if image:
            self.surface = pg.image.load(image)
        
        else:
            self.surface: pg.Surface = pg.Surface(size, pg.SRCALPHA)
            if fill:
                self.surface.fill(fill)

        self.images: Dict[str, pg.Surface] = {}
        self.fonts: Dict[str, pg.font.Font] = {}
        self.init_time = time.time()
        self.cleanup: List[str] = []


    async def download_image(self, url:str) -> str:
        path = f'temp/{utils.rand_id()}.png'
        start_time = time.time()

        log(f'downloading image {url}', 'api')

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(path, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

        log(f'image {path} downloaded in {time.time()-start_time}s', 'renderer')
        self.cleanup.append(path)
        return path
    

    def extend(self, size: int):
        new = pg.Surface((self.surface.get_width(), self.surface.get_height()+size), pg.SRCALPHA)
        new.blit(self.surface, (0,0))
        self.surface = new


    def get_image(self,
        path: str
    ):
        if path not in self.images:
            self.images[path] = pg.image.load(path)
        return self.images[path]


    def draw_image(self,
        path: str, pos: Tuple[int, int],
        size: Tuple[int, int] = None,
        h=0, v=0, area: pg.Rect=None,
        rotation: int = 0, opacity: int = 255
    ):
        image = self.get_image(path)

        if size:
            image = image.copy()
            image = pg.transform.smoothscale(image, size)
        
        if rotation != 0:
            image = pg.transform.rotate(image, rotation)

        if h != 0 or v != 0:
            pos = [
                pos[0]-image.get_width()*h,
                pos[1]-image.get_height()*v,
            ]

        image.set_alpha(opacity)
        
        if area:
            self.surface.blit(image, pos, area)
        else:
            self.surface.blit(image, pos)


    def get_font(self,
        path: str, size: int
    ) -> pg.font.Font:
        if path+str(size) not in self.fonts:
            self.fonts[path+str(size)] = pg.font.Font(path, size)
        return self.fonts[path+str(size)]


    def draw_text(self,
        text: str, pos: Tuple[int, int], font:str, size:int,
        color:Tuple[int, int, int], h=0, v=0, rotation: int = 0,
        opacity: int = 255, max_size: int = None
    ) -> Tuple[int,int]:
        font: pg.font.Font = self.get_font(font, size)
        text: pg.Surface = font.render(text, True, color)

        if rotation != 0:
            text = pg.transform.rotate(text, rotation)

        if max_size and text.get_width() > max_size:
            text = pg.transform.smoothscale(text, (max_size, text.get_height()))

        if h != 0 or v != 0:
            pos = [
                pos[0]-text.get_width()*h,
                pos[1]-text.get_height()*v,
            ]

        if opacity != 255:
            text.set_alpha(opacity)

        self.surface.blit(text, pos)
        return text.get_rect().size
    

    def get_text_size(self,
        text: str, font:str, size:int
    ) -> Tuple[int,int]:
        font: pg.font.Font = self.get_font(font, size)
        return font.size(text)


    def round_image(self, surface: pg.Surface, radius: int) -> pg.Surface:
        '''
        Makes an image have rounded corners.
        '''
        rect = pg.Rect((0,0), surface.get_size())
        rect = rect.inflate(radius*2,radius*2)

        new = pg.Surface(surface.get_size(), pg.SRCALPHA)
        new.blit(surface, (0,0))
        pg.draw.rect(new, (0,0,0,0), rect, radius, radius*3)

        return new


    def save(self, dir:str, ext:str='jpg') -> str:
        start_time = time.time()
        filename = dir.rstrip('/\\')+'/' + utils.rand_id() + '.'+ext
        pg.image.save(self.surface, filename)
        log(f'image {filename} saved in {time.time()-start_time}s', 'renderer')

        for i in self.cleanup:
            os.remove(i)
        self.cleanup = []
        
        log(f'image {filename} completed {time.time()-self.init_time}s', 'renderer')
        return filename



class RendererCollection:
    def __init__(self, mg):
        '''
        Collection of renderers.
        '''
        self.mg = mg


    def captcha(self, text: int) -> str:
        '''
        Renders a captcha for a user.
        '''
        r = Renderer((3,3), (0,0,0))

        # gradient bg
        for x in range(3):
            for y in range(3):
                pg.draw.rect(r.surface, utils.random_color(50), (x,y,1,1))

        r.surface = pg.transform.smoothscale(r.surface, (256,256))

        # symbols bg
        for i in range(100):
            x = random.randint(0, 255)
            y = random.randint(0, 255)
            r.draw_text(
                random.choice('QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'),
                (x,y), 'assets/captchabg.ttf', random.randint(10,60),
                utils.random_color(128), 0.5, 0.5, random.randint(0,360),
                random.randint(20,100)
            )

        # text
        start = random.randint(30,50)
        end = random.randint(210,230)

        for index, i in enumerate(text):
            x = utils.lerp(start, end, index/(len(text)-1))+random.randint(-5,5)
            y = random.randint(90,150)

            r.draw_text(
                i, (x,y), 'assets/captchafont.ttf', random.randint(50,80),
                utils.random_color(255,128), 0.5, 0.5, random.randint(-25,25),
            )

        # saving
        path = r.save('temp')

        return path

    
    async def leaders(self,
        guild: discord.Guild,
        type: Literal['alltime','season','week','day','vc','stream','mic']='season'
    ) -> str:
        '''
        Renders leaderboard as an image.
        '''
        users = self.mg.get_leaders(type)

        r = Renderer((420, 544))

        # 61, 17, 12
        start = 0
        place = 0
        prev_xp = None

        for index, i in enumerate(users):
            font = i.fonts.selected
            user = guild.get_member(i.id)
            name = 52

            # xp
            if type == 'alltime':
                xp = i.xp.total_xp
            elif type == 'season':
                xp = i.xp.xp
            elif type == 'week':
                xp = self.mg.timed_lb.get_weekly_xp(i.id)
            elif type == 'day':
                xp = self.mg.timed_lb.get_daily_xp(i.id)
            elif type == 'vc':
                xp = i.vc.vc_time
            elif type == 'stream':
                xp = i.vc.vc_time_streaming
            elif type == 'mic':
                xp = i.vc.vc_time_speaking

            if type in ('vc','stream','mic'):
                string = f'{xp//60//60}ч {xp//60%60:02}м {xp%60:02}с'
            else:
                string = f'{xp:,} XP'.replace(',',' ')

            if prev_xp != xp:
                place += 1
                prev_xp = xp

            # bg
            pos = 'top' if index == 0 else 'mid' if index < len(users)-1 else 'bottom'
            r.draw_image(
                f'assets/skins/{i.skins.selected}/lb{pos}bg.png', (0,start),
            )

            # glow
            if place <= 3:
                r.draw_image(
                    f'assets/place{place}.png', (0,start),
                )

            # pos
            color = (251,172,24) if place == 1 else\
                (140,140,140) if place == 2 else\
                (148,66,31) if place == 3 else\
                (255,255,255)
            
            r.draw_text(
                str(place), (17, start+7), f'assets/fonts/{font}/bolditalic.ttf', 32,
                color, opacity=96 if place > 3 else 255
            )

            # avatar
            # if user.avatar:
            #     image = await r.download_image(user.avatar.with_size(32).url)
            #     r.draw_image(image, (name, start+12), (32,32))
            #     name = 96

            # xp
            xp_size = 20
            xp_size += r.draw_text(
                string, (402, start+17), f'assets/fonts/{font}/semibold.ttf', 18,
                (255,255,255), h=1
            )[0]

            role = guild.get_role(i.xp.level_data)
            pg.draw.circle(
                r.surface, role.color.to_rgb(), (402-xp_size, start+28), 12
            )
            r.draw_text(
                f'{i.xp.level}', (402-xp_size, start+28), f'assets/fonts/{font}/bold.ttf', 14,
                (35,35,35), h=0.5, v=0.5,
            )

            # name
            if user:
                r.draw_text(
                    user.display_name, (name,start+17), f'assets/fonts/{font}/regular.ttf',
                    18, (255,255,255), max_size=280+45-xp_size
                )
            else:
                r.draw_text(
                    str(i.id), (name,start+17), f'assets/fonts/{font}/regular.ttf',
                    18, (255,255,255), opacity=128, max_size=280+45-xp_size
                )

            start += 61

        # saving
        path = r.save('temp', 'png')
        return path
    

    async def user_xp(self, user: discord.User, role: discord.Role) -> str:
        '''
        Renders the XP embed for a discord user.
        '''
        botuser = self.mg.get_user(user.id)
        skin = botuser.skins.selected
        font = botuser.fonts.selected
        r = Renderer(image=f'assets/skins/{skin}/xpbg.png')

        # avatar 14, 12, 32
        start = 14
        if user.avatar and False:
            image = await r.download_image(user.avatar.with_size(32).url)
            avatar = r.get_image(image)
            avatar = r.round_image(avatar, 16)
            r.surface.blit(avatar, (14,14))
            start += 42

        # level
        max_pos = r.draw_text(
            role.name.capitalize(), (398,15), f'assets/fonts/{font}/medium.ttf', 20, role.color.to_rgb(), h=1
        )[0]
        
        pg.draw.circle(
            r.surface, role.color.to_rgb(), (378-max_pos, 29), 12
        )
        r.draw_text(
            f'{botuser.xp.level}', (378-max_pos, 29), f'assets/fonts/{font}/bold.ttf', 16,
            (35,35,35), h=0.5, v=0.5,
        )

        # name
        r.draw_text(
            user.display_name, (start,16), f'assets/fonts/{font}/bold.ttf', 20,
            (255,255,255), max_size=300+42+14-start-max_pos
        )

        # xp
        r.draw_text(
            f"{botuser.xp.xp} XP", (16,88), f'assets/fonts/{font}/bold.ttf', 24, (255,255,255),
        )
        size = r.draw_text(
            f"{botuser.xp.total_xp} XP", (404,88), f'assets/fonts/{font}/regular.ttf', 24, (255,255,255),
            h=1, opacity=128
        )[0]
        r.draw_text(
            'всего', (404-size-5, 92), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255), 
            h=1, opacity=128
        )

        # xp limit
        r.draw_text(
            f"{botuser.xp.level_xp} XP", (16,125), f'assets/fonts/{font}/regular.ttf', 14, (255,255,255),
        )
        r.draw_text(
            f"{botuser.xp.level_max_xp} XP", (404,125), f'assets/fonts/{font}/regular.ttf',
            14, (255,255,255), h=1, opacity=128
        )

        # bar
        surface = pg.Surface((388,20), pg.SRCALPHA)
        rect = pg.Rect((-30,0), (30+388*botuser.xp.level_percentage, 20))
        pg.draw.rect(surface, role.color.to_rgb(), rect, border_radius=10)
        image = r.round_image(surface, 10)
        r.surface.blit(image, (16,151))

        # percentage
        percentage = f'{int(botuser.xp.level_percentage*100)}%'

        if rect.right > 30:
            r.draw_text(
                percentage, (rect.right-5+15, rect.centery+150),
                f'assets/fonts/{font}/bold.ttf', 14, (35,35,35), h=1, v=0.5
            )
        else:
            r.draw_text(
                percentage, (rect.right+5+15, rect.centery+150),
                f'assets/fonts/{font}/medium.ttf', 14, (200,200,200), v=0.5
            )

        # xp today
        pos = self.mg.get_place(user.id, 'day')

        if pos == None:
            r.draw_text(
                f"???", (68,217), f'assets/fonts/{font}/bolditalic.ttf', 20, (255,255,255),
                h=0.5, opacity=128
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}1.png', (0,200))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (18,217), f'assets/fonts/{font}/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"сегодня", (137-15, 209), f'assets/fonts/{font}/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                f"{self.mg.timed_lb.get_daily_xp(botuser.id)} XP", (137-15, 230),
                f'assets/fonts/{font}/bold.ttf', 14, (255,255,255), h=1, opacity=128
            )

        # xp this week
        pos = self.mg.get_place(user.id, 'week')

        if pos == None:
            r.draw_text(
                f"???", (68+142,217), f'assets/fonts/{font}/bolditalic.ttf', 20, (255,255,255),
                h=0.5, opacity=128
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}2.png', (142,200))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (159,217), f'assets/fonts/{font}/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"неделя", (278-15, 209), f'assets/fonts/{font}/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                f"{self.mg.timed_lb.get_weekly_xp(botuser.id)} XP", (278-15, 230),
                f'assets/fonts/{font}/bold.ttf', 14, (255,255,255), h=1, opacity=128
            )

        # season placement
        pos = self.mg.get_place(user.id, 'season')

        if pos == None:
            r.draw_text(
                f"???", (68+142+142,217), f'assets/fonts/{font}/bolditalic.ttf', 20, (255,255,255),
                h=0.5, opacity=128
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}3.png', (283,200))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (300,217), f'assets/fonts/{font}/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"сезон", (414-15, 221), f'assets/fonts/{font}/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        path = r.save('temp', 'png')
        return path
    

    async def user_vc(self, user: discord.User) -> str:
        '''
        Renders the VC time embed for a discord user.
        '''
        botuser = self.mg.get_user(user.id)
        skin = botuser.skins.selected
        font = botuser.fonts.selected
        r = Renderer(image=f'assets/skins/{skin}/vcbg.png')

        # time
        t = botuser.vc.vc_time
        vc_time_str = f'{t//60//60}ч {t//60%60:02}м {t%60:02}с'
        t = botuser.vc.vc_time_speaking
        vc_speak_str = f'{t//60//60}:{t//60%60:02}:{t%60:02}'
        t = botuser.vc.vc_time_streaming
        vc_stream_str = f'{t//60//60}:{t//60%60:02}:{t%60:02}'
        
        r.draw_text(
            f'Статистика войсов {user.display_name}', (17,15),
            f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), opacity=128
        )
        r.draw_text(
            vc_time_str, (17,40), f'assets/fonts/{font}/bold.ttf', 24, (255,255,255),
        )
        # r.draw_text(
        #     vc_speak_str, (33,50), f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), opacity=128
        # )
        # r.draw_text(
        #     vc_stream_str, (420-40,50), f'assets/fonts/{font}/medium.ttf', 16, (255,255,255),
        #     h=1, opacity=128
        # )

        # icons
        # r.draw_image(
        #     'assets/mic.png', (17,56)
        # )
        # r.draw_image(
        #     'assets/stream.png', (389,56)
        # )
        
        # time vc
        pos = self.mg.get_place(user.id, 'vc')

        if pos == None:
            r.draw_text(
                f"???", (68,217), f'assets/fonts/{font}/bolditalic.ttf', 20, (255,255,255),
                h=0.5, opacity=128
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}1.png', (0,103))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (18,119), f'assets/fonts/{font}/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"войс", (137-15, 123), f'assets/fonts/{font}/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        # time streaming
        pos = self.mg.get_place(user.id, 'stream')

        if pos == None:
            r.draw_text(
                f"???", (68+142,217), f'assets/fonts/{font}/bolditalic.ttf', 20, (255,255,255),
                h=0.5, opacity=128
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}2.png', (142,103))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (159,119), f'assets/fonts/{font}/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"стрим", (278-15, 113), f'assets/fonts/{font}/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                vc_stream_str, (278-15, 132), f'assets/fonts/{font}/bold.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        # time with mic on
        pos = self.mg.get_place(user.id, 'mic')

        if pos == None:
            r.draw_text(
                f"???", (68+142+142,217), f'assets/fonts/{font}/bolditalic.ttf', 20, (255,255,255),
                h=0.5, opacity=128
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}3.png', (283,103))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (300,119), f'assets/fonts/{font}/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"с микро", (414-15, 113), f'assets/fonts/{font}/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                vc_speak_str, (414-15, 132), f'assets/fonts/{font}/bold.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        path = r.save('temp', 'png')
        return path
    

    def prom(self, user, level: int, role: discord.Role = None) -> str:
        skin = user.skins.selected
        font = user.fonts.selected
        r = Renderer(
            image=f'assets/skins/{skin}/prombg.png' if role else\
                f'assets/skins/{skin}/onelinerbg.png'
            )

        # title
        r.draw_text(
            f"Повышение!", (17,14), f'assets/fonts/{font}/bold.ttf', 24, (255,255,255)
        )

        # levels
        size = 420-18

        size -= r.draw_text(
            f'{level}', (size, 14), f'assets/fonts/{font}/bold.ttf', 24, (255,255,255), h=1, opacity=128
        )[0]+7
        size -= r.draw_text(
            f'>', (size, 14), f'assets/fonts/{font}/regular.ttf', 24, (255,255,255), h=1, opacity=128
        )[0]+7
        size -= r.draw_text(
            f'{level-1}', (size, 14), f'assets/fonts/{font}/bold.ttf', 24, (255,255,255), h=1, opacity=128
        )[0]+7
        r.draw_text(
            f'Уровень', (size, 18), f'assets/fonts/{font}/regular.ttf', 18, (255,255,255), h=1, opacity=128
        )

        # up indicator
        if role:
            pos = 359*((level-1)/(len(LEVELS)-1))+30
            size = r.get_text_size(role.name, f'assets/fonts/{font}/medium.ttf', 16)[0]
            text_pos = deepcopy(pos)
            if text_pos-size/2 < 20:
                text_pos = 20+size/2
            if text_pos+size/2 > 300:
                text_pos = 400-size/2

            r.draw_text(
                role.name.capitalize(), (text_pos, 51), f'assets/fonts/{font}/medium.ttf', 16,
                role.color.to_rgb(), h=0.5
            )

            pg.draw.line(
                r.surface, (255,255,255), (pos, 81-3), (pos, 101+2), width=2
            )

        path = r.save('temp', 'png')
        return path
    

    def skin_claim(self, user: discord.User, skin: str) -> str:
        '''
        Renders image for skin claiming.
        '''
        botuser = self.mg.get_user(user.id)
        font = botuser.fonts.selected
        r = Renderer(image=f'assets/skins/{skin}/onelinerbg.png')
        skin = self.mg.skins[skin]
        
        # skin name
        name_size = r.get_text_size('получил скин', f'assets/fonts/{font}/regular.ttf', 20)[0]+\
            r.get_text_size(skin.name+'!', f'assets/fonts/{font}/bold.ttf', 20)[0]+10
        
        # name
        pos = 17
        max_size = 420-17-17-name_size

        if type(user) != int:
            # username
            pos += r.draw_text(
                user.display_name, (pos,14), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255),
                max_size=max_size
            )[0]+5
        else:
            # user id if couldnt fetch the user
            pos += r.draw_text(
                str(user), (pos,14), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255),
                opacity=96, max_size=max_size
            )[0]+5

        # text
        pos += r.draw_text(
            'получил скин', (pos,14), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255),
            opacity=128
        )[0]+5
        r.draw_text(
            skin.name+'!', (pos,14), f'assets/fonts/{font}/bold.ttf', 20, (255,255,255)
        )

        path = r.save('temp', 'png')
        return path
    

    def font_claim(self, user: discord.User, font: str) -> str:
        '''
        Renders image for font claiming.
        '''
        botuser = self.mg.get_user(user.id)
        skin = botuser.skins.selected
        r = Renderer(image=f'assets/skins/{skin}/onelinerbg.png')
        fontdata = self.mg.fonts[font]
        
        # skin name
        name_size = r.get_text_size('получил шрифт', f'assets/fonts/{font}/regular.ttf', 20)[0]+\
            r.get_text_size(fontdata.name+'!', f'assets/fonts/{font}/bold.ttf', 20)[0]+10
        
        # name
        pos = 17
        max_size = 420-17-17-name_size

        if type(user) != int:
            # username
            pos += r.draw_text(
                user.display_name, (pos,14), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255),
                max_size=max_size
            )[0]+5
        else:
            # user id if couldnt fetch the user
            pos += r.draw_text(
                str(user), (pos,14), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255),
                opacity=96, max_size=max_size
            )[0]+5

        # text
        pos += r.draw_text(
            'получил шрифт', (pos,14), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255),
            opacity=128
        )[0]+5
        r.draw_text(
            fontdata.name+'!', (pos,14), f'assets/fonts/{font}/bold.ttf', 20, (255,255,255)
        )

        path = r.save('temp', 'png')
        return path
    

    def skin_set(self, user, skin: str) -> str:
        '''
        Renders image for skin setting.
        '''
        r = Renderer(image=f'assets/skins/{skin}/onelinerbg.png')
        font = user.fonts.selected
        skin = self.mg.skins[skin]

        # text
        pos = r.draw_text(
            'Вы установили скин', (17,14), f'assets/fonts/{font}/regular.ttf', 20, (255,255,255),
            opacity=128
        )[0]+4
        r.draw_text(
            skin.name+'!', (pos+17,14), f'assets/fonts/{font}/bold.ttf', 20, (255,255,255)
        )

        path = r.save('temp', 'png')
        return path
    

    def font_set(self, user, font: str) -> str:
        '''
        Renders image for font setting.
        '''
        skin = user.skins.selected
        r = Renderer(image=f'assets/skins/{skin}/onelinerbg.png')
        font = self.mg.fonts[font]

        # text
        pos = r.draw_text(
            'Вы установили шрифт', (17,14), f'assets/fonts/{font.key}/regular.ttf', 20, (255,255,255),
            opacity=128
        )[0]+4
        r.draw_text(
            font.name+'!', (pos+17,14), f'assets/fonts/{font.key}/bold.ttf', 20, (255,255,255)
        )

        path = r.save('temp', 'png')
        return path
    

    def font_list(self, user: discord.User) -> str:
        '''
        Renders a list of fonts this user has.
        '''
        botuser = self.mg.get_user(user.id)
        skin = botuser.skins.selected
        font = botuser.fonts.selected
        r = Renderer(image=f'assets/skins/{skin}/skintopbg.png')

        # title
        r.draw_text(
            f'Шрифты {user.display_name}', (17,14), f'assets/fonts/{font}/bold.ttf', 20, (255,255,255),
            max_size=420-17-17
        )
        pos = r.draw_text(
            f'Разблокировано: ', (17,45), f'assets/fonts/{font}/regular.ttf', 16, (255,255,255),
            opacity=128
        )[0]
        r.draw_text(
            f'{len(botuser.fonts.items)} / {len(self.mg.fonts)}', (pos+17,45),
            f'assets/fonts/{font}/medium.ttf', 16, (255,255,255)
        )

        # font list
        x = 0
        y = 85
        r.extend(40)

        for index, i in enumerate(self.mg.fonts.values()):
            color = (100,230,50) if i.key == botuser.fonts.selected else (255,255,255)
            opacity = 255 if i.key in botuser.fonts.items or\
                i.key == botuser.fonts.selected else 192
            currentfont = f'assets/fonts/{i.key}/medium.ttf'

            # bg
            if x == 0:
                r.draw_image(
                    f'assets/skins/{skin}/fontbg.png', (x, y)
                )

            # text
            r.draw_text(
                i.name, (x+7, y+10), currentfont, 14, color,
                opacity=opacity, max_size=180, v=0.5
            )

            # badges
            if i.key == botuser.fonts.selected:
                r.draw_image(
                    f'assets/fontselected.png', (x, y)
                )
            elif i.key not in botuser.fonts.items:
                r.draw_image(
                    f'assets/fontlocked.png', (x, y)
                )

            # changing pos
            x += 212

            if x >= 400 and index < len(self.mg.fonts)-1:
                x = 0
                y += 25
                r.extend(25)

        # end
        y += 25
        r.extend(35)
        r.draw_image(
            f'assets/skins/{skin}/skinbottombg.png', (0, y)
        )

        pos = r.draw_text(
            f'ml!setfont <номер> ', (17,y+12), f'assets/fonts/{font}/medium.ttf', 14,
            (255,255,255), opacity=128
        )[0]
        if botuser.fonts._selected:
            pos += r.draw_text(
                f'или ', (pos+17,y+12), f'assets/fonts/{font}/regular.ttf', 14,
                (255,255,255), opacity=128
            )[0]
            pos += r.draw_text(
                f'ml!removefont ', (pos+17,y+12), f'assets/fonts/{font}/medium.ttf', 14,
                (255,255,255), opacity=128
            )[0]
        r.draw_text(
            f'для смены', (pos+17,y+12), f'assets/fonts/{font}/regular.ttf', 14,
            (255,255,255), opacity=128
        )

        path = r.save('temp', 'png')
        return path
    

    def skin_list(self, user: discord.User) -> str:
        '''
        Renders a list of skins this user has.
        '''
        botuser = self.mg.get_user(user.id)
        font = botuser.fonts.selected
        r = Renderer(image=f'assets/skins/{botuser.skins.selected}/skintopbg.png')

        # title
        r.draw_text(
            f'Скины {user.display_name}', (17,14), f'assets/fonts/{font}/bold.ttf', 20, (255,255,255),
            max_size=420-17-17
        )
        pos = r.draw_text(
            f'Разблокировано: ', (17,45), f'assets/fonts/{font}/regular.ttf', 16, (255,255,255),
            opacity=128
        )[0]
        r.draw_text(
            f'{len(botuser.skins.items)} / {len(self.mg.skins)}', (pos+17,45),
            f'assets/fonts/{font}/medium.ttf', 16, (255,255,255)
        )

        # skin list
        x = 0
        y = 85
        r.extend(48+5+5)

        for index, i in enumerate(self.mg.skins.values()):
            r.draw_image(
                f'assets/skins/{i.key}/badge.png', (x,y),
            )

            # badge
            if i.key == botuser.skins.selected:
                r.draw_image(f'assets/selected.png', (x,y))
                r.draw_text(
                    f'{index+1}', (x+6,y+2), f'assets/fonts/{font}/bolditalic.ttf', 14, (132,255,87),
                    opacity=128
                )

            elif i.key not in botuser.skins.items:
                r.draw_image(f'assets/locked.png', (x,y))

            else:
                r.draw_text(
                    f'{index+1}', (x+6,y+2), f'assets/fonts/{font}/bolditalic.ttf', 14, (255,255,255),
                    opacity=128
                )

            # changing pos
            x += 48+5

            if x >= 400 and index < len(self.mg.skins)-1:
                x = 0
                y += 48+5
                r.extend(48+5)

        # end
        y += 48+5
        r.extend(45)
        r.draw_image(
            f'assets/skins/{botuser.skins.selected}/skinbottombg.png', (0, y)
        )

        pos = r.draw_text(
            f'ml!setskin <номер> ', (17,y+12), f'assets/fonts/{font}/medium.ttf', 14,
            (255,255,255), opacity=128
        )[0]
        if botuser.skins._selected:
            pos += r.draw_text(
                f'или ', (pos+17,y+12), f'assets/fonts/{font}/regular.ttf', 14,
                (255,255,255), opacity=128
            )[0]
            pos += r.draw_text(
                f'ml!removeskin ', (pos+17,y+12), f'assets/fonts/{font}/medium.ttf', 14,
                (255,255,255), opacity=128
            )[0]
        r.draw_text(
            f'для смены', (pos+17,y+12), f'assets/fonts/{font}/regular.ttf', 14,
            (255,255,255), opacity=128
        )

        path = r.save('temp', 'png')
        return path


    def xp_calendar(self, user: discord.User, year: int, month: int) -> str:
        '''
        Renders a calendar of user's XP earnings.
        '''
        botuser = self.mg.get_user(user.id)
        font = botuser.fonts.selected
        r = Renderer(image=f'assets/skins/{botuser.skins.selected}/skintopbg.png')
        
        # date
        date = datetime.datetime(year, month, 1)
        while date.weekday() != 0:
            date -= datetime.timedelta(days=1)

        target_date = datetime.datetime(year, month, 1)
        while (target_date.year == year and target_date.month == month)\
            or target_date.weekday() != 6:
                target_date += datetime.timedelta(days=1)

        # title
        r.draw_text(
            f'Опыт {user.display_name}', (17,14), f'assets/fonts/{font}/bold.ttf', 20, (255,255,255),
            max_size=420-17-17
        )
        pos = r.draw_text(
            f'За ', (17,45), f'assets/fonts/{font}/regular.ttf', 16, (255,255,255),
            opacity=128
        )[0]
        r.draw_text(
            f'{utils.month_name((month-1)%12)}, {year}', (pos+17,45),
            f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), opacity=128
        )

        # date list
        x = 0
        y = 85
        r.extend(65+6+6)

        today = datetime.datetime.now(datetime.timezone.utc)

        while date <= target_date:
            is_today = date.day == today.day and date.month == today.month
            r.draw_image(
                (
                    'assets/calendartodaybg.png' if is_today else\
                    'assets/calendarempty.png' if date.weekday() not in [5,6] else\
                    'assets/calendarweekday.png'
                ), (x,y), opacity=128 if date.month != month else 255
            )

            r.draw_text(
                f'{date.day}', (x+6,y+3), f'assets/fonts/{font}/bolditalic.ttf', 14, (255,255,255),
                opacity=128
            )

            # data
            day = int(date.timestamp()//86400)+1
            lb = self.mg.timed_lb.daily.get(day, {})
            xp = lb.get(user.id, 0)
            
            lb = sorted(lb.items(), key=lambda x: x[1], reverse=True)

            place = 0
            prev_xp = None

            for i in lb:
                cur_xp = i[1]

                if prev_xp != cur_xp:
                    place += 1
                    prev_xp = cur_xp

                if i[0] == user.id:
                    break

            # underlay
            if place in [1,2,3]:
                r.draw_image(
                    f'assets/calendar{place}.png', (x, y)
                )
            elif is_today:
                r.draw_image(
                    f'assets/calendartoday.png', (x, y)
                )

            # place
            if place > 0:
                color = (251,172,24) if place == 1 else\
                    (140,140,140) if place == 2 else\
                    (148,66,31) if place == 3 else\
                    (192,192,192)
                
                r.draw_text(
                    f"#{place}", (x+54-6, y+3), f'assets/fonts/{font}/bold.ttf', 14, color, h=1,
                )

            # xp
            if xp > 0:
                r.draw_text(
                    utils.shorten_number(xp), (x+28, y+25),
                    f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), h=0.5
                )
            else:
                r.draw_text(
                    '0', (x+27, y+25),
                    f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), h=0.5, opacity=60
                )

            # changing pos
            x += 54+6
            date += datetime.timedelta(days=1)

            if x >= 380:
                x = 0
                if date <= target_date:
                    y += 54+6
                    r.extend(54+6)

        # end
        y += 54+6
        r.extend(45)
        r.draw_image(
            f'assets/skins/{botuser.skins.selected}/skinbottombg.png', (0, y)
        )

        pos = r.draw_text(
            f'ml!calendar <дата> ', (17,y+12), f'assets/fonts/{font}/medium.ttf', 14,
            (255,255,255), opacity=128
        )[0]
        r.draw_text(
            f'для смены месяца', (pos+17,y+12), f'assets/fonts/{font}/regular.ttf', 14,
            (255,255,255), opacity=128
        )

        path = r.save('temp', 'png')
        return path


    def server_calendar(self, user: discord.User, year: int, month: int) -> str:
        '''
        Renders a calendar of the server total's XP earnings.
        '''
        botuser = self.mg.get_user(user.id)
        font = botuser.fonts.selected
        r = Renderer(image=f'assets/skins/{botuser.skins.selected}/skintopbg.png')
        
        # date
        date = datetime.datetime(year, month, 1)
        while date.weekday() != 0:
            date -= datetime.timedelta(days=1)

        target_date = datetime.datetime(year, month, 1)
        while (target_date.year == year and target_date.month == month)\
            or target_date.weekday() != 6:
                target_date += datetime.timedelta(days=1)

        # title
        r.draw_text(
            f'Серверный опыт', (17,14), f'assets/fonts/{font}/bold.ttf', 20, (255,255,255),
            max_size=420-17-17
        )
        pos = r.draw_text(
            f'За ', (17,45), f'assets/fonts/{font}/regular.ttf', 16, (255,255,255),
            opacity=128
        )[0]
        r.draw_text(
            f'{utils.month_name((month-1)%12)}, {year}', (pos+17,45),
            f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), opacity=128
        )

        # date list
        x = 0
        y = 85
        r.extend(65+6+6)

        today = datetime.datetime.now(datetime.timezone.utc)

        while date <= target_date:
            # data
            is_today = date.day == today.day and date.month == today.month

            day = int(date.timestamp()//86400)+1
            lb = self.mg.timed_lb.daily.get(day, {})
            xp = sum(lb.values())
            max_xp = max([sum(i.values()) for i in self.mg.timed_lb.daily.values()])
            key = xp/(max_xp+1)*4
            opacity = (key%1)*255
            image = round(key//1)
            darken = int(date.month != month)+1
            bgopacity = 255 if date.month == month else\
                128-(opacity/128)

            # temperature bg
            r.draw_image(
                f'assets/calendartemp{image+1}.png', (x, y), opacity=bgopacity
            )
            r.draw_image(
                f'assets/calendartemp{image+2}.png', (x, y), opacity=opacity/(darken)
            )

            r.draw_text(
                f'{date.day}', (x+6,y+3), f'assets/fonts/{font}/bolditalic.ttf', 14, (255,255,255),
                opacity=128
            )

            if date.weekday() in [5,6]:
                r.draw_image(
                    f'assets/calendarweekdayborder.png', (x, y),
                    opacity=128 if date.month != month else 255
                )

            if is_today:
                r.draw_image(
                    f'assets/calendartoday.png', (x, y),
                    opacity=128 if date.month != month else 255
                )

            # xp
            if xp > 0:
                r.draw_text(
                    utils.shorten_number(xp), (x+28, y+25),
                    f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), h=0.5
                )
            else:
                r.draw_text(
                    '0', (x+27, y+25),
                    f'assets/fonts/{font}/medium.ttf', 16, (255,255,255), h=0.5, opacity=60
                )

            # changing pos
            x += 54+6
            date += datetime.timedelta(days=1)

            if x >= 380:
                x = 0
                if date <= target_date:
                    y += 54+6
                    r.extend(54+6)

        # end
        y += 54+6
        r.extend(45)
        r.draw_image(
            f'assets/skins/{botuser.skins.selected}/skinbottombg.png', (0, y)
        )

        pos = r.draw_text(
            f'ml!scal <дата> ', (17,y+12), f'assets/fonts/{font}/medium.ttf', 14,
            (255,255,255), opacity=128
        )[0]
        r.draw_text(
            f'для смены месяца', (pos+17,y+12), f'assets/fonts/{font}/regular.ttf', 14,
            (255,255,255), opacity=128
        )

        path = r.save('temp', 'png')
        return path