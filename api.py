import random
from typing import *

import aiofiles
import discord.ext.commands
from config import *
import json
import os
import time
import discord.ext
from log import *
from copy import deepcopy
import pygame as pg
import aiohttp
import utils

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

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(path, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

        log(f'image {path} downloaded in {time.time()-start_time}s', 'api')
        self.cleanup.append(path)
        return path


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
        rotation: int = 0
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
        log(f'image {filename} saved in {time.time()-start_time}s', 'api')

        for i in self.cleanup:
            os.remove(i)
        self.cleanup = []
        
        log(f'image {filename} completed {time.time()-self.init_time}s', 'api')
        return filename


# user and user-related classes

class Reminder:
    def __init__(self, data:dict):
        '''
        Represents a reminder.
        '''
        self.message_id: "int | None" = data['id']
        self.channel_id: int = data['channel_id']
        self.end_time: float = data['end_time']
        self.duration: float = data['duration']
        self.text: "str | None" = data['text']
        self.jump_url: "str | None" = data['jump_url']

    def to_dict(self) -> dict:
        '''
        Converts the reminder to a dictionary.
        '''
        return {
            "id": self.message_id,
            "channel_id": self.channel_id,
            "end_time": self.end_time,
            "duration": self.duration,
            "text": self.text,
            "jump_url": self.jump_url
        }
    
    @staticmethod
    def convert(
        message_id:int,
        channel_id:int,
        duration:int,
        jump_url:str,
        text:"str | None"=None
    ) -> "Reminder":
        '''
        Computes the stuff by itself.
        '''
        return Reminder({
            "id": message_id,
            "channel_id": channel_id,
            "end_time": time.time()+duration,
            "duration": duration,
            "jump_url": jump_url,
            "text": text
        })


class XP:
    def __init__(self, data:dict={}):
        '''
        User experience points, level, rank, etc.
        '''
        self.prev_xp: int = data.get('prev_xp', 0)
        self.xp: int = data.get('xp', 0)
        self.reload_levels()


    @property
    def total_xp(self) -> int:
        return self.prev_xp + self.xp


    def reload_levels(self):
        '''
        Reloads levels and percentages.
        '''
        xp = deepcopy(self.xp)
        xp_in_level = 1000
        level = 1
        while xp >= xp_in_level: 
            level += 1
            xp -= xp_in_level
            xp_in_level += 500

        self.level: int = level
        self.level_data: any = config.LEVELS[min(level, len(config.LEVELS))-1]
        self.level_xp: int = xp
        self.level_max_xp: int = xp_in_level
        self.level_percentage: float = xp/xp_in_level


    def to_dict(self) -> dict:
        return {
            "xp": self.xp,
            "prev_xp": self.prev_xp,
        }


class User:
    def __init__(self, id:int, data:dict={}):
        '''
        Represents a user.
        '''
        self.id: int = id

        xp: int = data.get('xp', 0)
        self.xp = XP(xp)
        self.quarantine: float | None = data.get('quarantine', None)
        self.reminders: List[Reminder] = [Reminder(i) for i in data.get('reminders', [])]
        self.tokens: Dict[int] = data.get('tokens', {})

        self.token_dig_timeout: float = data.get('token_dig_timeout', 0.0)
        self.games_timeout: float = data.get('games_timeout', 0.0)

        self.last_sent_zero: float = 0
        self.verifying: bool = False

    
    def to_dict(self) -> dict:
        '''
        Converts the class to a dictionary to store in the file.
        '''
        return {
            "xp": self.xp.to_dict(),
            "quarantine": self.quarantine,
            "reminders": [i.to_dict() for i in self.reminders],
            "tokens": self.tokens,
            "token_dig_timeout": self.token_dig_timeout,
            "games_timeout": self.games_timeout
        }
    

# XP Leaderboard

class TimedLeaderboard:
    def __init__(self, data: dict = {}):
        '''
        Daily and weekly leaderboard.
        '''
        self.daily = data.get('daily', {})
        self.weekly = data.get('weekly', {})

        self.daily = {
            int(k): {int(k1): v1 for k1, v1 in v.items()}\
                for k, v in self.daily.items()
        }
        self.weekly = {
            int(k): {int(k1): v1 for k1, v1 in v.items()}\
                for k, v in self.weekly.items()
        }


    @property
    def current_day(self) -> int:
        return int(time.time()//86400)
    

    @property
    def current_week(self) -> int:
        return int(time.time()//604800)


    def check_leaderboard(self):
        if self.current_day not in self.daily:
            self.daily[self.current_day] = {}

        if self.current_week not in self.weekly:
            self.weekly[self.current_week] = {}


    def check_user(self, id:int):
        if id not in self.daily[self.current_day]:
            self.daily[self.current_day][id] = 0

        if id not in self.weekly[self.current_week]:
            self.weekly[self.current_week][id] = 0


    def add_xp(self, id:int, amount:int):
        '''
        Updates the leaderboard.
        '''
        self.check_leaderboard()
        self.check_user(id)

        self.daily[self.current_day][id] += amount
        self.weekly[self.current_week][id] += amount


    def get_daily_xp(self, id:int) -> int:
        self.check_leaderboard()

        if id not in self.daily[self.current_day]:
            return 0
        
        return self.daily[self.current_day][id]


    def get_weekly_xp(self, id:int) -> int:
        self.check_leaderboard()
        
        if id not in self.weekly[self.current_week]:
            return 0
        
        return self.weekly[self.current_week][id]


    def to_dict(self) -> dict:
        return {
            "daily": self.daily,
            "weekly": self.weekly
        }
        


# manager

class Manager:
    def __init__(self, users_file:str, data_file:str):
        '''
        API and backend manager.
        '''
        self.users_file: str = users_file
        self.data_file: str = data_file
        self.reload()


    def new(self):
        '''
        Rewrites the old database with the new one.
        '''
        self.users: Dict[int, User] = {}
        self.timed_lb = TimedLeaderboard()

        self.commit()


    def panic(self):
        '''
        Creates a duplicate of the database and creates a new one.
        '''
        log('Panic!', 'api', WARNING)

        # copying file
        if os.path.exists(self.users_file):
            os.rename(self.users_file, self.users_file+'.bak')
            log(f'Cloned user data file to {self.users_file}.bak', 'api')

        # creating a new one
        self.new()


    def reload(self):
        '''
        Reloads user data and bot data.
        '''
        # user data
        try:
            with open(self.users_file, encoding='utf-8') as f:
                data = json.load(f)
        except:
            self.panic()
            return

        self.users = {int(id): User(int(id), data) for id, data in data['users'].items()}

        self.timed_lb = TimedLeaderboard(data.get('timed_lb', {}))

        # saving
        self.commit()


    def commit(self):
        '''
        Saves user data to the file.
        '''
        data = {
            'users': {}
        }

        # users
        for i in self.users:
            data['users'][i] = self.users[i].to_dict()

        # timed lb
        data['timed_lb'] = self.timed_lb.to_dict()

        # saving
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    def check_user(self, id:int):
        '''
        Checks if user exists in database. If not, creates one.
        '''
        if id in self.users:
            return
        
        self.users[id] = User(id)


    def get_user(self, id:int):
        '''
        Returns user by ID.
        '''
        self.check_user(id)
        return self.users[id]
    
    
    def add_reminder(self,
        user_id:int,
        message_id:"int | None",
        channel_id:int,
        duration:float,
        jump_url:"str | None",
        text:"str | None"
    ):
        '''
        Adds a reminder.
        '''
        self.check_user(user_id)

        reminder = Reminder.convert(
            message_id, channel_id,
            duration, jump_url, text
        )
        self.users[user_id].reminders.append(reminder)

        self.commit()
    

    def remove_reminder(self, user_id:int, index:int):
        '''
        Removes a reminder from a user.
        '''
        self.users[user_id].reminders.pop(index)
        self.commit()


    def add_xp(self, user_id:int, xp:int) -> "int | None":
        '''
        Adds XP to user.

        If user leveled up, return the new level.
        '''
        self.check_user(user_id)

        old_level = deepcopy(self.users[user_id].xp.level)
        self.users[user_id].xp.xp += xp
        self.users[user_id].xp.reload_levels()

        if old_level != self.users[user_id].xp.level:
            return self.users[user_id].xp.level
        
        self.timed_lb.add_xp(user_id, xp)
        
        self.commit()


    def set_xp(self, user_id:int, xp:int) -> "int | None":
        '''
        Sets XP to user.

        If user leveled up, return the new level.
        '''
        self.check_user(user_id)

        old_level = deepcopy(self.users[user_id].xp.level)
        self.users[user_id].xp.xp = xp
        self.users[user_id].xp.reload_levels()

        if old_level != self.users[user_id].xp.level:
            return self.users[user_id].xp.level
        
        self.commit()


    def check_user_zero(self, user_id:int) -> bool:
        '''
        Checks if user can gain XP for sending zero message.

        If can, update the timer.
        '''
        self.check_user(user_id)

        if time.time()-self.users[user_id].last_sent_zero > 120: # like 2 mins
            self.users[user_id].last_sent_zero = time.time()
            return True
        
        return False


    def get_all_xp(self) -> int:
        '''
        Returns sum of each members's xp
        '''
        total_xp = 0
        for i in self.users.values():
            total_xp += i.xp.xp
        return total_xp


    def render_captcha(self, text: int) -> str:
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
    

    def get_leaders(self, type: Literal['alltime','season','week','day'], places=9) -> List[User]:
        '''
        Returns a list of users sorted by xp.
        '''
        if type == 'alltime':
            users = sorted(self.users.values(), key=lambda x: x.xp.total_xp, reverse=True)
        elif type == 'season':
            users = sorted(self.users.values(), key=lambda x: x.xp.xp, reverse=True)
        elif type == 'week':
            users = sorted(self.users.values(), key=lambda x: self.timed_lb.get_weekly_xp(x.id), reverse=True)
        elif type == 'day':
            users = sorted(self.users.values(), key=lambda x: self.timed_lb.get_daily_xp(x.id), reverse=True)
        return users[:places]


    async def render_leaders(self,
        guild: discord.Guild,
        type: Literal['alltime','season','week','day']='season'
    ) -> str:
        '''
        Renders leaderboard as an image.
        '''
        users = self.get_leaders(type)

        r = Renderer(image='assets/leadersbg.png')

        # 61, 17, 12
        start = 0
        for i in users:
            user = guild.get_member(i.id)
            name = 52

            # xp
            if type == 'alltime':
                xp = i.xp.total_xp
            elif type == 'season':
                xp = i.xp.xp
            elif type == 'week':
                xp = self.timed_lb.get_weekly_xp(i.id)
            elif type == 'day':
                xp = self.timed_lb.get_daily_xp(i.id)

            # avatar
            # if user.avatar:
            #     image = await r.download_image(user.avatar.with_size(32).url)
            #     r.draw_image(image, (name, start+12), (32,32))
            #     name = 96

            # xp
            xp_size = 20
            xp_size += r.draw_text(
                f'{xp} XP', (402, start+17), 'assets/semibold.ttf', 18,
                (255,255,255), h=1
            )[0]

            role = guild.get_role(i.xp.level_data)
            pg.draw.circle(
                r.surface, role.color.to_rgb(), (402-xp_size, start+28), 12
            )
            r.draw_text(
                f'{i.xp.level}', (402-xp_size, start+28), 'assets/bold.ttf', 14,
                (35,35,35), h=0.5, v=0.5,
            )

            # name
            if user:
                r.draw_text(
                    user.display_name, (name,start+17), 'assets/regular.ttf',
                    18, (255,255,255), max_size=280+45-xp_size
                )
            else:
                r.draw_text(
                    str(i.id), (name,start+17), 'assets/regular.ttf',
                    18, (128,128,128), max_size=280+45-xp_size
                )

            start += 61

        # saving
        path = r.save('temp', 'png')
        return path
    

    async def render_user_xp(self, user: discord.User, role: discord.Role) -> str:
        '''
        Renders the XP embed for a discord user.
        '''
        botuser = self.get_user(user.id)
        r = Renderer(image='assets/xpbg.png')

        # avatar 14, 12, 32
        start = 14
        if user.avatar:
            image = await r.download_image(user.avatar.with_size(32).url)
            avatar = r.get_image(image)
            avatar = r.round_image(avatar, 16)
            r.surface.blit(avatar, (14,14))
            start += 42

        # level
        max_pos = r.draw_text(
            role.name.capitalize(), (398,15), 'assets/medium.ttf', 20, role.color.to_rgb(), h=1
        )[0]
        
        pg.draw.circle(
            r.surface, role.color.to_rgb(), (378-max_pos, 29), 12
        )
        r.draw_text(
            f'{botuser.xp.level}', (378-max_pos, 29), 'assets/bold.ttf', 16,
            (35,35,35), h=0.5, v=0.5,
        )

        # name
        r.draw_text(
            user.display_name, (start,16), 'assets/bold.ttf', 20,
            (255,255,255), max_size=300-max_pos
        )

        # xp
        r.draw_text(
            f"{botuser.xp.xp} XP", (16,88), 'assets/bold.ttf', 24, (255,255,255),
        )
        size = r.draw_text(
            f"{botuser.xp.total_xp} XP", (404,88), 'assets/regular.ttf', 24, (128,128,128), h=1
        )[0]
        r.draw_text(
            'всего', (404-size-5, 92), 'assets/regular.ttf', 20, (128,128,128), h=1
        )

        # xp limit
        r.draw_text(
            f"{botuser.xp.level_xp} XP", (16,125), 'assets/regular.ttf', 14, (255,255,255),
        )
        r.draw_text(
            f"{botuser.xp.level_max_xp} XP", (404,125), 'assets/regular.ttf',
            14, (128,128,128), h=1
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
                'assets/bold.ttf', 14, (35,35,35), h=1, v=0.5
            )
        else:
            r.draw_text(
                percentage, (rect.right+5+15, rect.centery+150),
                'assets/medium.ttf', 14, (200,200,200), v=0.5
            )

        # xp today
        try:
            lb = self.get_leaders('day')
            pos = lb.index(botuser)+1

        except:
            r.draw_text(
                f"???", (68,217), 'assets/bolditalic.ttf', 20, (128,128,128), h=0.5
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}1.png', (0,200))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (18,217), 'assets/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"сегодня", (137-15, 209), 'assets/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                f"{self.timed_lb.get_daily_xp(botuser.id)} XP", (137-15, 230),
                'assets/bold.ttf', 14, (255,255,255), h=1, opacity=128
            )

        # xp this week
        try:
            lb = self.get_leaders('week')
            pos = lb.index(botuser)+1

        except:
            r.draw_text(
                f"???", (68+142,217), 'assets/bolditalic.ttf', 20, (128,128,128), h=0.5
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}2.png', (142,200))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (159,217), 'assets/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"неделя", (278-15, 209), 'assets/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                f"{self.timed_lb.get_weekly_xp(botuser.id)} XP", (278-15, 230),
                'assets/bold.ttf', 14, (255,255,255), h=1, opacity=128
            )

        # season placement
        try:
            lb = self.get_leaders('season')
            pos = lb.index(botuser)+1

        except:
            r.draw_text(
                f"???", (68+142+142,217), 'assets/bolditalic.ttf', 20, (128,128,128), h=0.5
            )

        else:
            if pos < 4:
                r.draw_image(f'assets/{pos}3.png', (283,200))

            color = (251,172,24) if pos == 1 else\
                (140,140,140) if pos == 2 else\
                (148,66,31) if pos == 3 else\
                (192,192,192)
            
            r.draw_text(
                f"#{pos}", (300,217), 'assets/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"сезон", (414-15, 221), 'assets/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        path = r.save('temp', 'png')
        return path