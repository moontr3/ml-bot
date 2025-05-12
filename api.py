import random
import threading
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

        log(f'downloading image {url}', 'api')

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(path, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

        log(f'image {path} downloaded in {time.time()-start_time}s', 'api')
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
    

class Skins:
    def __init__(self, data: dict = {}):
        '''
        Embed skins.
        '''
        self.skins: list = data.get('skins', [])
        self._selected: "str | None" = data.get('selected', None)

    
    @property
    def selected(self) -> str:
        return self._selected if self._selected else 'default'


    def to_dict(self) -> dict:
        return {
            "skins": self.skins,
            "selected": self._selected
        }
    

class VCData:
    def __init__(self, data: dict = {}):
        '''
        Voice channel data.
        '''
        self.vc_time: int = int(data.get('vc_time', 0))
        self.vc_time_streaming: int = int(data.get('vc_time_streaming', 0))
        self.vc_time_speaking: int = int(data.get('vc_time_speaking', 0))
        self.xp_to_add: float = data.get('xp_to_add', 0.0)
        
        self.state: Literal['none', 'deafen', 'mute', 'normal'] = 'none'
        self.is_streaming: bool = False

    
    @property
    def xp_mult(self) -> int:
        return {
            'none': 0,
            'deafen': 0,
            'mute': 2,
            'normal': 4
        }[self.state] + int(self.is_streaming)

    
    def to_dict(self) -> dict:
        return {
            "vc_time": self.vc_time,
            "vc_time_streaming": self.vc_time_streaming,
            "vc_time_speaking": self.vc_time_speaking,
            "xp_to_add": self.xp_to_add
        }
    

class MinuteStats:
    def __init__(self):
        '''
        Tracks stats of XP gained in the last minute.
        '''
        self.minute: int = 0
        self.update_minute()

        self.xp: int = 0
        self.one_word_messages: int = 0


    def update_minute(self):
        '''
        Updates the current minute.
        '''
        old_min = deepcopy(self.minute)
        self.minute = int(time.time()/60)

        if old_min != self.minute:
            self.xp = 0
            self.one_word_messages = 0

    
    def add_xp(self, xp: int):
        '''
        Adds XP to the counter.
        '''
        self.update_minute()

        self.xp += xp


class User:
    def __init__(self, id:int, data:dict={}):
        '''
        Represents a user.
        '''
        self.id: int = id

        xp: int = data.get('xp', {})
        self.xp = XP(xp)
        self.quarantine: float | None = data.get('quarantine', None)
        self.reminders: List[Reminder] = [Reminder(i) for i in data.get('reminders', [])]
        self.tokens: Dict[int] = data.get('tokens', {})

        self.token_dig_timeout: float = data.get('token_dig_timeout', 0.0)
        self.games_timeout: float = data.get('games_timeout', 0.0)

        self.last_sent_zero: float = 0
        self.verifying: bool = False

        self.skins: Skins = Skins(data.get('skins', {}))

        self.vc: VCData = VCData(data.get('vc', {}))
        self.temp_vc_timeout: float = data.get('temp_vc_timeout', 0)

        self.last_msg_channel: int = data.get('last_msg_channel', deepcopy(CHAT_CHANNEL)) 
        self.to_send_lvl_up_msg: bool = False

        self.minute_stats = MinuteStats()

    
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
            "games_timeout": self.games_timeout,
            "skins": self.skins.to_dict(),
            "vc": self.vc.to_dict(),
            "temp_vc_timeout": self.temp_vc_timeout,
            "last_msg_channel": self.last_msg_channel
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
        

# skin data

class SkinData:
    def __init__(self, key: str, data: dict = {}):
        '''
        Skin data.
        '''
        self.key: str = key
        self.name: str = data.get('name', None)
        self.emoji: str = data.get('emoji', None)
        self.rarity: int = data.get('rarity', None)

        # checking skin files
        for i in [
            'onelinerbg', 'prombg', 'xpbg', 'lbtopbg', 'lbmidbg', 'lbbottombg',
            'skintopbg', 'skinbottombg', 'badge', 'vcbg'
        ]:
            if not os.path.exists(f'assets/skins/{self.key}/{i}.png'):
                log(f'File {i} not found for skin {self.key}', 'api', WARNING)


# temp VC

class TempVC:
    def __init__(self, id: int, data: dict = {}):
        '''
        Temporary voice channel.
        '''
        self.id: int = id
        self.owner_id: int = data['owner_id']
        self.last_activity: float = data.get('last_activity', time.time())
        self.has_people: "bool | None" = None
        self.name: str = data['name']
        self.checked: bool = False # whether this vc was checked when updating activity
        self.created_at: float = data.get('created_at', time.time())

    
    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "last_activity": self.last_activity,
            "name": self.name,
            "created_at": self.created_at
        }


# manager

class Manager:
    def __init__(self, users_file:str, data_file:str):
        '''
        API and backend manager.
        '''
        self.users_file: str = users_file
        self.data_file: str = data_file
        self.unclaimed: List[int] = []
        self.in_vc: List[int] = []
        self.temp_vcs: Dict[int, TempVC] = []
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
        self.temp_vcs = {int(id): TempVC(int(id), data) for id, data in data.get('temp_vcs', {}).items()}
        self.timed_lb = TimedLeaderboard(data.get('timed_lb', {}))

        # data
        try:
            with open(self.data_file, encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            log(f'Unable to load data file: {e}', 'api')

        self.skins: Dict[str, SkinData] = {
            k: SkinData(k, v) for k, v in self.data.get('skins', {}).items()
        }

        # saving
        self.commit()


    def commit(self):
        '''
        Это костыль или гениальное решение?
        Anti Ctrl+C Device
        '''
        threading.Thread(target=self._commit).start()
        

    def _commit(self):
        '''
        Saves user data to the file.
        '''
        data = {
            'users': {}
        }

        # users
        for i in self.users:
            data['users'][i] = self.users[i].to_dict()

        data['timed_lb'] = self.timed_lb.to_dict()
        data['temp_vcs'] = {id: i.to_dict() for id, i in self.temp_vcs.items()}

        # saving
        try:
            json_data = json.dumps(data, indent=4)
        except Exception as e:
            log(f'Unable to save user data: {e}', 'api', WARNING)    
            return

        with open(self.users_file, 'w', encoding='utf-8') as f:
            f.write(json_data)


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
        user = self.get_user(user_id)

        reminder = Reminder.convert(
            message_id, channel_id,
            duration, jump_url, text
        )
        user.reminders.append(reminder)

        self.commit()
    

    def remove_reminder(self, user_id:int, index:int):
        '''
        Removes a reminder from a user.
        '''
        user = self.get_user(user_id)
        user.reminders.pop(index)
        self.commit()


    def add_xp(self, user_id:int, xp:int, store_lvl_up:bool=True) -> "int | None":
        '''
        Adds XP to user.

        If user leveled up, return the new level.
        '''
        user = self.get_user(user_id)

        old_level = deepcopy(user.xp.level)
        user.xp.xp += xp
        user.xp.reload_levels()

        self.timed_lb.add_xp(user_id, xp)

        if old_level != user.xp.level:
            if store_lvl_up:
                user.to_send_lvl_up_msg = True
                
            return user.xp.level
        
        self.commit()


    def set_xp(self, user_id:int, xp:int) -> "int | None":
        '''
        Sets XP to user.

        If user leveled up, return the new level.
        '''
        user = self.get_user(user_id)

        old_level = deepcopy(user.xp.level)
        user.xp.xp = xp
        user.xp.reload_levels()

        if old_level != user.xp.level:
            user.to_send_lvl_up_msg = True
            return user.xp.level
        
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
    

    def set_skin(self, user_id:int, skin:str):
        '''
        Sets skin for a user.
        '''
        user = self.get_user(user_id)
        user.skins._selected = skin

        self.commit()
    

    def add_skin(self, user_id:int, skin:str):
        '''
        Adds skin to a user.
        '''
        user = self.get_user(user_id)

        if skin in user.skins.skins:
            return False
        
        user.skins.skins.append(skin)
        self.commit()

        return True
    

    def remove_skin(self, user_id:int, skin:str):
        '''
        Removes skin from a user.
        '''
        user = self.get_user(user_id)

        if skin not in user.skins.skins:
            return False
        
        user.skins.skins.remove(skin)
        self.commit()

        return True
    
    
    def get_random_skin(self) -> SkinData:
        '''
        Returns a random skin.
        '''
        skin = random.choices(
            list(self.skins.values()),
            [i.rarity for i in self.skins.values()]
        )[0]
        return skin
    

    def set_last_msg_channel(self, user_id:int, channel_id:int):
        '''
        Sets last message channel for a user.
        '''
        user = self.get_user(user_id)
        user.last_msg_channel = channel_id
        self.commit()
    

    def update_vc_state(self, id: int, state: discord.VoiceState) -> str:
        '''
        Updates the vc state of a user.
        '''
        user = self.get_user(id)

        if state == None or state.channel == None:
            user.vc.state = 'none'
            user.vc.is_streaming = False

            if user.id in self.in_vc:
                self.in_vc.remove(user.id)

            return user.vc.state
        
        if user.id not in self.in_vc:
            self.in_vc.append(user.id)

        if state.self_deaf or state.deaf:
            user.vc.state = 'deafen'

        elif state.self_mute or state.mute:
            user.vc.state = 'mute'

        else:
            user.vc.state = 'normal'

        user.vc.is_streaming = state.self_stream or state.self_video

        return user.vc.state


    def update_vc_xp(self, id: int):
        '''
        Updates the vc xp of a user.
        '''
        user = self.get_user(id)

        # checking xp
        xp = user.vc.xp_mult * 1/60
        user.vc.xp_to_add += xp

        # adding stats
        user.vc.vc_time += 1

        if user.vc.is_streaming:
            user.vc.vc_time_streaming += 1

        if user.vc.state == 'normal':
            user.vc.vc_time_speaking += 1

        # not adding xp if alone in vc
        if len(self.in_vc) == 1:
            return

        # adding xp
        while user.vc.xp_to_add >= 1:
            self.add_xp(id, 1)
            user.vc.xp_to_add -= 1

        self.commit()


    def get_temp_vc(self, id: int) -> "TempVC | None":
        '''
        Returns a temporary VC of a user, if there is one.
        '''
        for i in self.temp_vcs.values():
            if i.owner_id == id:
                return i


    def new_temp_vc(self, name: str, id: int, user: User):
        '''
        Creates a new temporary vc.
        '''
        vc = TempVC(id, {"owner_id": user.id, "name": name})
        self.temp_vcs[id] = vc

        user.temp_vc_timeout = time.time()+TEMP_VC_CREATION_TIMEOUT
        self.commit()


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
    

    def get_leaders(self, type: Literal['alltime','season','week','day','vc','stream','mic'], places=9) -> List[User]:
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
        elif type == 'vc':
            users = sorted(self.users.values(), key=lambda x: x.vc.vc_time, reverse=True)
        elif type == 'stream':
            users = sorted(self.users.values(), key=lambda x: x.vc.vc_time_streaming, reverse=True)
        elif type == 'mic':
            users = sorted(self.users.values(), key=lambda x: x.vc.vc_time_speaking, reverse=True)
        return users[:places]
    

    def get_place(self, user_id:int, type: Literal['alltime','season','week','day','vc','stream','mic']) -> int:
        users = self.get_leaders(type, places=99999)

        place = 0
        prev_xp = None

        for i in users:
            if type == 'alltime':
                xp = i.xp.total_xp
            elif type == 'season':
                xp = i.xp.xp
            elif type == 'week':
                xp = self.timed_lb.get_weekly_xp(i.id)
            elif type == 'day':
                xp = self.timed_lb.get_daily_xp(i.id)
            elif type == 'vc':
                xp = i.vc.vc_time
            elif type == 'stream':
                xp = i.vc.vc_time_streaming
            elif type == 'mic':
                xp = i.vc.vc_time_speaking

            if prev_xp != xp:
                place += 1
                prev_xp = xp

            if i.id == user_id:
                return place


    async def render_leaders(self,
        guild: discord.Guild,
        type: Literal['alltime','season','week','day','vc','stream','mic']='season'
    ) -> str:
        '''
        Renders leaderboard as an image.
        '''
        users = self.get_leaders(type)

        r = Renderer((420, 544))

        # 61, 17, 12
        start = 0
        place = 0
        prev_xp = None

        for index, i in enumerate(users):
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
                str(place), (17, start+7), 'assets/bolditalic.ttf', 32,
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
                string, (402, start+17), 'assets/semibold.ttf', 18,
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
                    18, (255,255,255), opacity=128, max_size=280+45-xp_size
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
        skin = botuser.skins.selected
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
            (255,255,255), max_size=300+42+14-start-max_pos
        )

        # xp
        r.draw_text(
            f"{botuser.xp.xp} XP", (16,88), 'assets/bold.ttf', 24, (255,255,255),
        )
        size = r.draw_text(
            f"{botuser.xp.total_xp} XP", (404,88), 'assets/regular.ttf', 24, (255,255,255),
            h=1, opacity=128
        )[0]
        r.draw_text(
            'всего', (404-size-5, 92), 'assets/regular.ttf', 20, (255,255,255), 
            h=1, opacity=128
        )

        # xp limit
        r.draw_text(
            f"{botuser.xp.level_xp} XP", (16,125), 'assets/regular.ttf', 14, (255,255,255),
        )
        r.draw_text(
            f"{botuser.xp.level_max_xp} XP", (404,125), 'assets/regular.ttf',
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
                'assets/bold.ttf', 14, (35,35,35), h=1, v=0.5
            )
        else:
            r.draw_text(
                percentage, (rect.right+5+15, rect.centery+150),
                'assets/medium.ttf', 14, (200,200,200), v=0.5
            )

        # xp today
        pos = self.get_place(user.id, 'day')

        if pos == None:
            r.draw_text(
                f"???", (68,217), 'assets/bolditalic.ttf', 20, (255,255,255),
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
        pos = self.get_place(user.id, 'week')

        if pos == None:
            r.draw_text(
                f"???", (68+142,217), 'assets/bolditalic.ttf', 20, (255,255,255),
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
        pos = self.get_place(user.id, 'season')

        if pos == None:
            r.draw_text(
                f"???", (68+142+142,217), 'assets/bolditalic.ttf', 20, (255,255,255),
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
                f"#{pos}", (300,217), 'assets/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"сезон", (414-15, 221), 'assets/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        path = r.save('temp', 'png')
        return path
    

    async def render_user_vc(self, user: discord.User) -> str:
        '''
        Renders the VC time embed for a discord user.
        '''
        botuser = self.get_user(user.id)
        skin = botuser.skins.selected
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
            'assets/medium.ttf', 16, (255,255,255), opacity=128
        )
        r.draw_text(
            vc_time_str, (17,40), 'assets/bold.ttf', 24, (255,255,255),
        )
        # r.draw_text(
        #     vc_speak_str, (33,50), 'assets/medium.ttf', 16, (255,255,255), opacity=128
        # )
        # r.draw_text(
        #     vc_stream_str, (420-40,50), 'assets/medium.ttf', 16, (255,255,255),
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
        pos = self.get_place(user.id, 'vc')

        if pos == None:
            r.draw_text(
                f"???", (68,217), 'assets/bolditalic.ttf', 20, (255,255,255),
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
                f"#{pos}", (18,119), 'assets/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"войс", (137-15, 123), 'assets/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        # time streaming
        pos = self.get_place(user.id, 'stream')

        if pos == None:
            r.draw_text(
                f"???", (68+142,217), 'assets/bolditalic.ttf', 20, (255,255,255),
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
                f"#{pos}", (159,119), 'assets/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"стрим", (278-15, 113), 'assets/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                vc_stream_str, (278-15, 132), 'assets/bold.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        # time with mic on
        pos = self.get_place(user.id, 'mic')

        if pos == None:
            r.draw_text(
                f"???", (68+142+142,217), 'assets/bolditalic.ttf', 20, (255,255,255),
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
                f"#{pos}", (300,119), 'assets/bolditalic.ttf', 20, color,
            )
            r.draw_text(
                f"с микро", (414-15, 113), 'assets/regular.ttf',
                14, (255,255,255), h=1, opacity=128
            )
            r.draw_text(
                vc_speak_str, (414-15, 132), 'assets/bold.ttf',
                14, (255,255,255), h=1, opacity=128
            )

        path = r.save('temp', 'png')
        return path
    

    def render_prom(self, user: User, level: int, role: discord.Role = None) -> str:
        skin = user.skins.selected
        r = Renderer(
            image=f'assets/skins/{skin}/prombg.png' if role else\
                f'assets/skins/{skin}/onelinerbg.png'
            )

        # title
        r.draw_text(
            f"Повышение!", (17,14), 'assets/bold.ttf', 24, (255,255,255)
        )

        # levels
        size = 420-18

        size -= r.draw_text(
            f'{level}', (size, 14), 'assets/bold.ttf', 24, (255,255,255), h=1, opacity=128
        )[0]+7
        size -= r.draw_text(
            f'>', (size, 14), 'assets/regular.ttf', 24, (255,255,255), h=1, opacity=128
        )[0]+7
        size -= r.draw_text(
            f'{level-1}', (size, 14), 'assets/bold.ttf', 24, (255,255,255), h=1, opacity=128
        )[0]+7
        r.draw_text(
            f'Уровень', (size, 18), 'assets/regular.ttf', 18, (255,255,255), h=1, opacity=128
        )

        # up indicator
        if role:
            pos = 359*((level-1)/(len(LEVELS)-1))+30
            size = r.get_text_size(role.name, 'assets/medium.ttf', 16)[0]
            text_pos = deepcopy(pos)
            if text_pos-size/2 < 20:
                text_pos = 20+size/2
            if text_pos+size/2 > 300:
                text_pos = 400-size/2

            r.draw_text(
                role.name.capitalize(), (text_pos, 51), 'assets/medium.ttf', 16,
                role.color.to_rgb(), h=0.5
            )

            pg.draw.line(
                r.surface, (255,255,255), (pos, 81-3), (pos, 101+2), width=2
            )

        path = r.save('temp', 'png')
        return path
    

    def render_skin_claim(self, user: discord.User, skin: str) -> str:
        '''
        Renders image for skin claiming.
        '''
        r = Renderer(image=f'assets/skins/{skin}/onelinerbg.png')
        skin: SkinData = self.skins[skin]
        
        # skin name
        name_size = r.get_text_size('получил скин', 'assets/regular.ttf', 20)[0]+\
            r.get_text_size(skin.name+'!', 'assets/bold.ttf', 20)[0]+10
        
        # name
        pos = 17
        max_size = 420-17-17-name_size

        if type(user) != int:
            # username
            pos += r.draw_text(
                user.display_name, (pos,14), 'assets/regular.ttf', 20, (255,255,255),
                max_size=max_size
            )[0]+5
        else:
            # user id if couldnt fetch the user
            pos += r.draw_text(
                str(user), (pos,14), 'assets/regular.ttf', 20, (255,255,255),
                opacity=96, max_size=max_size
            )[0]+5

        # text
        pos += r.draw_text(
            'получил скин', (pos,14), 'assets/regular.ttf', 20, (255,255,255),
            opacity=128
        )[0]+5
        r.draw_text(
            skin.name+'!', (pos,14), 'assets/bold.ttf', 20, (255,255,255)
        )

        path = r.save('temp', 'png')
        return path
    

    def render_skin_set(self, skin: str) -> str:
        '''
        Renders image for skin setting.
        '''
        r = Renderer(image=f'assets/skins/{skin}/onelinerbg.png')
        skin: SkinData = self.skins[skin]

        # text
        pos = r.draw_text(
            'Вы установили скин', (17,14), 'assets/regular.ttf', 20, (255,255,255),
            opacity=128
        )[0]+4
        r.draw_text(
            skin.name+'!', (pos+17,14), 'assets/bold.ttf', 20, (255,255,255)
        )

        path = r.save('temp', 'png')
        return path
    

    def render_skin_list(self, user: discord.User) -> str:
        '''
        Renders a list of skins this user has.
        '''
        botuser = self.get_user(user.id)
        r = Renderer(image=f'assets/skins/{botuser.skins.selected}/skintopbg.png')

        # title
        r.draw_text(
            f'Скины {user.display_name}', (17,14), 'assets/bold.ttf', 20, (255,255,255),
            max_size=420-17-17
        )
        pos = r.draw_text(
            f'Разблокировано: ', (17,45), 'assets/regular.ttf', 16, (255,255,255),
            opacity=128
        )[0]
        r.draw_text(
            f'{len(botuser.skins.skins)} / {len(self.skins)}', (pos+17,45),
            'assets/medium.ttf', 16, (255,255,255)
        )

        # skin list
        x = 0
        y = 85
        r.extend(65+6+6)

        for index, i in enumerate(self.skins.values()):
            r.draw_image(
                f'assets/skins/{i.key}/badge.png', (x,y),
            )

            # badge
            if i.key == botuser.skins.selected:
                r.draw_image(f'assets/selected.png', (x,y))
                r.draw_text(
                    f'{index+1}', (x+8,y+4), 'assets/bolditalic.ttf', 16, (132,255,87),
                    opacity=128
                )

            elif i.key not in botuser.skins.skins:
                r.draw_image(f'assets/locked.png', (x,y))

            else:
                r.draw_text(
                    f'{index+1}', (x+7,y+3), 'assets/bolditalic.ttf', 16, (255,255,255),
                    opacity=128
                )

            # changing pos
            x += 65+6

            if x >= 370 and index < len(self.skins)-1:
                x = 0
                y += 65+6
                r.extend(65+6)

        # end
        y += 65+6
        r.extend(45)
        r.draw_image(
            f'assets/skins/{botuser.skins.selected}/skinbottombg.png', (0, y)
        )

        pos = r.draw_text(
            f'ml!setskin <номер> ', (17,y+12), 'assets/medium.ttf', 14,
            (255,255,255), opacity=128
        )[0]
        if botuser.skins._selected:
            pos += r.draw_text(
                f'или ', (pos+17,y+12), 'assets/regular.ttf', 14,
                (255,255,255), opacity=128
            )[0]
            pos += r.draw_text(
                f'ml!removeskin ', (pos+17,y+12), 'assets/medium.ttf', 14,
                (255,255,255), opacity=128
            )[0]
        r.draw_text(
            f'для смены', (pos+17,y+12), 'assets/regular.ttf', 14,
            (255,255,255), opacity=128
        )

        path = r.save('temp', 'png')
        return path


    def render_xp_calendar(self, user: discord.User, year: int, month: int) -> str:
        '''
        Renders a calendar of user's XP earnings.
        '''
        botuser = self.get_user(user.id)
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
            f'Опыт {user.display_name}', (17,14), 'assets/bold.ttf', 20, (255,255,255),
            max_size=420-17-17
        )
        pos = r.draw_text(
            f'За ', (17,45), 'assets/regular.ttf', 16, (255,255,255),
            opacity=128
        )[0]
        r.draw_text(
            f'{utils.month_name((month-1)%12)}, {year}', (pos+17,45),
            'assets/medium.ttf', 16, (255,255,255), opacity=128
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
                f'{date.day}', (x+6,y+3), 'assets/bolditalic.ttf', 14, (255,255,255),
                opacity=128
            )

            # data
            day = int(date.timestamp()//86400)+1
            lb = self.timed_lb.daily.get(day, {})
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
                    f"#{place}", (x+54-6, y+3), 'assets/bold.ttf', 14, color, h=1,
                )

            # xp
            if xp > 0:
                r.draw_text(
                    utils.shorten_number(xp), (x+28, y+25),
                    'assets/medium.ttf', 16, (255,255,255), h=0.5
                )
            else:
                r.draw_text(
                    '0', (x+27, y+25),
                    'assets/medium.ttf', 16, (255,255,255), h=0.5, opacity=60
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
            f'ml!calendar <дата> ', (17,y+12), 'assets/medium.ttf', 14,
            (255,255,255), opacity=128
        )[0]
        r.draw_text(
            f'для смены месяца', (pos+17,y+12), 'assets/regular.ttf', 14,
            (255,255,255), opacity=128
        )

        path = r.save('temp', 'png')
        return path
