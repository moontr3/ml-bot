from typing import *
from config import *
import json
import os
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
    def __init__(self, xp:int):
        '''
        User experience points, level, rank, etc.
        '''
        self.xp: int = xp
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

    
    def to_dict(self) -> dict:
        '''
        Converts the class to a dictionary to store in the file.
        '''
        return {
            "xp": self.xp.xp,
            "quarantine": self.quarantine,
            "reminders": [i.to_dict() for i in self.reminders],
            "tokens": self.tokens,
            "token_dig_timeout": self.token_dig_timeout,
            "games_timeout": self.games_timeout
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