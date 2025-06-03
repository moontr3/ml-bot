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
from renderer import *
from copy import deepcopy
import utils
import pygame as pg


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
    

class Collectibles:
    def __init__(self, data: dict = {}):
        '''
        Collectible list.
        '''
        self.items: list = data.get('items', [])
        self._selected: "str | None" = data.get('selected', None)

    
    @property
    def selected(self) -> str:
        return self._selected if self._selected else 'default'


    def to_dict(self) -> dict:
        return {
            "items": self.items,
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
        self.q: int = data.get('q', 0)
        self.q_level: int = data.get('q_level', self.q)
        self.q_level = min(15, max(0, self.q_level))

        self.token_dig_timeout: float = data.get('token_dig_timeout', 0.0)
        self.games_timeout: float = data.get('games_timeout', 0.0)

        self.last_sent_zero: float = 0
        self.verifying: bool = False

        self.skins: Collectibles = Collectibles(data.get('skins', {}))
        self.fonts: Collectibles = Collectibles(data.get('fonts', {}))

        self.vc: VCData = VCData(data.get('vc', {}))
        self.temp_vc_timeout: float = data.get('temp_vc_timeout', 0)

        self.last_msg_channel: int = data.get('last_msg_channel', deepcopy(CHAT_CHANNEL)) 
        self.to_send_lvl_up_msg: bool = False
        self.marked_by_beast: bool = data.get('marked_by_beast', False)

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
            "q": self.q,
            "q_level": self.q_level,
            "token_dig_timeout": self.token_dig_timeout,
            "games_timeout": self.games_timeout,
            "skins": self.skins.to_dict(),
            "fonts": self.fonts.to_dict(),
            "vc": self.vc.to_dict(),
            "temp_vc_timeout": self.temp_vc_timeout,
            "last_msg_channel": self.last_msg_channel,
            "marked_by_beast": self.marked_by_beast
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


class FontData:
    def __init__(self, key: str, data: dict = {}):
        '''
        Skin data.
        '''
        self.key: str = key
        self.name: str = data.get('name', None)
        self.emoji: str = data.get('emoji', None)
        self.rarity: int = data.get('rarity', None)
        self.alt: List[str] = data.get('alt', [])

        # checking skin files
        for i in [
            'bolditalic', 'bold', 'semibold', 'medium', 'regular'
        ]:
            if not os.path.exists(f'assets/fonts/{self.key}/{i}.ttf'):
                log(f'File {i} not found for font {self.key}', 'api', WARNING)


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
    

# Q earning

class UnclaimedQ:
    def __init__(self, message_id: int):
        self.message_id: int = message_id
        self.spawned_at: float = time.time()
        self.claimed: List[int] = []


# manager

class Manager:
    def __init__(self, users_file:str, data_file:str):
        '''
        API and backend manager.
        '''
        self.users_file: str = users_file
        self.data_file: str = data_file
        self.unclaimed: List[int] = []
        self.unclaimed_qs: Dict[int, UnclaimedQ] = {}
        self.in_vc: List[int] = []
        self.temp_vcs: Dict[int, TempVC] = {}
        self.quarantines: Dict[int, int] = {}
        self.renderer = RendererCollection(self)
        self.sk_last_spawn: float = 0
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
        self.quarantines = {int(id): t for id, t in data.get('quarantines', {}).items()}
        self.timed_lb = TimedLeaderboard(data.get('timed_lb', {}))
        self.sk_last_spawn: float = data.get('sk_last_spawn', 0)

        # data
        try:
            with open(self.data_file, encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            log(f'Unable to load data file: {e}', 'api')

        self.skins: Dict[str, SkinData] = {
            k: SkinData(k, v) for k, v in self.data.get('skins', {}).items()
        }
        self.fonts: Dict[str, FontData] = {
            k: FontData(k, v) for k, v in self.data.get('fonts', {}).items()
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
        data['quarantines'] = self.quarantines.items()
        data['sk_last_spawn'] = self.sk_last_spawn

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


    def add_q(self, user_id:int, amount:int) -> "int | None":
        '''
        Adds Qs to user and returns the new balance.
        '''
        user = self.get_user(user_id)
        
        user.q += amount
        user.q_level += amount
        if user.q_level > 15:
            user.q_level = 15

        self.commit()
        return user.q


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


    def get_all_info(self) -> Dict[str, int]:
        '''
        Returns total stats
        '''
        data = {
            "xp": 0,
            "skins": 0,
            "fonts": 0,
            "q": 0
        }
        for i in self.users.values():
            data['xp'] += i.xp.xp
            data['skins'] += len(i.skins.items)
            data['fonts'] += len(i.fonts.items)
            data['q'] += i.q

        return data
    

    def get_lb_finishes(self, user_id:int) -> List[int]:
        finishes: Dict[int,int] = {1:0, 2:0, 3:0}

        for i in self.timed_lb.daily.values():
            if user_id in i:
                place = sorted(i.items(), key=lambda x: x[1], reverse=True).index((user_id, i[user_id]))+1
                if place in finishes:
                    finishes[place] += 1

        return finishes
    

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

        if skin in user.skins.items:
            return False
        
        user.skins.items.append(skin)
        self.commit()

        return True
    

    def remove_skin(self, user_id:int, skin:str):
        '''
        Removes skin from a user.
        '''
        user = self.get_user(user_id)

        if skin not in user.skins.items:
            return False
        
        user.skins.items.remove(skin)
        self.commit()

        return True
    

    def set_font(self, user_id:int, font:str):
        '''
        Sets font for a user.
        '''
        user = self.get_user(user_id)
        user.fonts._selected = font

        self.commit()
    

    def add_font(self, user_id:int, font:str):
        '''
        Adds font to a user.
        '''
        user = self.get_user(user_id)

        if font in user.fonts.items:
            return False
        
        user.fonts.items.append(font)
        self.commit()

        return True
    

    def remove_font(self, user_id:int, font:str):
        '''
        Removes font from a user.
        '''
        user = self.get_user(user_id)

        if font not in user.fonts.items:
            return False
        
        user.fonts.items.remove(font)
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
    
    
    def get_random_font(self) -> FontData:
        '''
        Returns a random font.
        '''
        font = random.choices(
            list(self.fonts.values()),
            [i.rarity for i in self.fonts.values()]
        )[0]
        return font
    

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

        # adding stats
        user.vc.vc_time += 1

        if user.vc.is_streaming:
            user.vc.vc_time_streaming += 1

        if user.vc.state == 'normal':
            user.vc.vc_time_speaking += 1

        # not adding xp if alone in vc
        if len(self.in_vc) == 1:
            return
        user.vc.xp_to_add += xp

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
    

    def get_leaders(self, type: Literal['alltime','season','week','day','vc','stream','mic','q'], places=9) -> List[User]:
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
        elif type == 'q':
            users = sorted(self.users.values(), key=lambda x: x.q, reverse=True)
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
    

    def add_quarantine(self, user_id: int, t: int):
        self.check_user(user_id)
        self.quarantines.update({user_id: t})
        self.commit()
    
    def remove_quarantine(self, user_id: int):
        self.check_user(user_id)
        self.quarantines.pop(user_id)
        self.commit()