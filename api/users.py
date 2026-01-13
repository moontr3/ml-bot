from typing import *
from config import *
import time
from log import *
from copy import deepcopy


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
        self.seasons: Dict[str, Dict[str, int]] = {
            'new': data.get('seasons', {}).get('new', {}),
            're': data.get('seasons', {}).get('re', {}),
            'pre33': data.get('seasons', {}).get('pre33', {}),
        }
        self.reload_levels()


    @property
    def total_xp(self) -> int:
        # return self.get_season_xp('new') + self.get_season_xp('re')
        return sum([self.get_season_xp(key) for key in self.seasons.keys()])


    @property
    def xp(self) -> int:
        # return self.get_season_xp('re')
        return self.get_season_xp('re') + self.get_season_xp('pre33')
    

    def get_season_xp(self, season:str) -> int:
        return sum(self.seasons.get(season, {}).values())
    

    def add_xp(self, season: str, xp: int, reason: str):
        if reason not in self.seasons[season]:
            self.seasons[season][reason] = 0

        self.seasons[season][reason] += xp
        self.reload_levels()


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
            "seasons": self.seasons
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
            'mute': 0.2,
            'normal': 1
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


    def update_minute(self):
        '''
        Updates the current minute.
        '''
        old_min = deepcopy(self.minute)
        self.minute = int(time.time()/60)

        if old_min != self.minute:
            self.xp = 0

    
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
        self.coins: int = data.get('coins', 0)

        self.tg: int | None = data.get('tg', None)
        self.display_name: str | None = data.get('display_name', None)
        self.avatar_url: str | None = data.get('avatar_url', None)
        self.tg_username: str | None = data.get('tg_username', None)

        self.plus_reps: int = data.get('plus_reps', 0)
        self.minus_reps: int = abs(data.get('minus_reps', 0))
        self.plus_rep_timeout: float = data.get('plus_rep_timeout', 0.0)
        self.minus_rep_timeout: float = data.get('minus_rep_timeout', 0.0)
        self.minus_repped: Dict[int, float] = {int(k): v for k, v in data.get('minus_repped', {}).items()}
        self.rep_block_until: float = data.get('rep_block_until', 0.0)

        self.mfr_timeout: float = data.get('mfr_timeout', 0.0)
        self.mfr_stats: Dict[str, int] = data.get('mfr_stats', {})

        self.last_sent_zero: float = 0
        self.verifying: bool = False

        self.skins: Collectibles = Collectibles(data.get('skins', {}))
        self.fonts: Collectibles = Collectibles(data.get('fonts', {}))

        self.vc: VCData = VCData(data.get('vc', {}))
        self.temp_vc_timeout: float = data.get('temp_vc_timeout', 0)

        self.last_msg_channel: int = data.get('last_msg_channel', deepcopy(CHAT_CHANNEL)) 
        self.to_send_lvl_up_msg: bool = False
        self.marked_by_beast: bool = data.get('marked_by_beast', False)
        self.likee: bool = data.get('likee', False)

        self.location: str | None = data.get('location', None)
        self.loc_data: Dict[str, Any] = data.get('loc_data', {})
        self.library: List[str] = data.get('library', [])

        self.minute_stats = MinuteStats()


    @property
    def rep(self) -> int:
        return self.plus_reps - self.minus_reps

    
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
            "plus_reps": self.plus_reps,
            "minus_reps": self.minus_reps,
            "minus_repped": self.minus_repped,
            "plus_rep_timeout": self.plus_rep_timeout,
            "minus_rep_timeout": self.minus_rep_timeout,
            "rep_block_until": self.rep_block_until,
            "mfr_timeout": self.mfr_timeout,
            "mfr_stats": self.mfr_stats,
            "skins": self.skins.to_dict(),
            "fonts": self.fonts.to_dict(),
            "vc": self.vc.to_dict(),
            "temp_vc_timeout": self.temp_vc_timeout,
            "last_msg_channel": self.last_msg_channel,
            "marked_by_beast": self.marked_by_beast,
            "likee": self.likee,
            "coins": self.coins,
            "tg": self.tg,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "tg_username": self.tg_username,
            "location": self.location,
            "loc_data": self.loc_data,
            "library": self.library
        }
    