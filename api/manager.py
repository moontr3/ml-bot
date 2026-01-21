import random
from typing import *

from .users import *
from .crossposter import *
from .types import *
from .xp import *
from .skins import *
from .ai import *
from .games import *

import aiogram
from config import *
import json
import os
import time
from log import *
from renderer import *
from copy import copy, deepcopy
import aiohttp
import base64


# manager

class Manager:
    def __init__(self, users_file:str, data_file:str, key:str, bot):
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
        self.renderer = RendererCollection(self, bot)
        self.crenderer = CCollection(self, bot)
        self.sk_last_spawn: float = 0
        self.last_commit = 0
        self.roulette_games: List[Roulette] = []
        self.duel_games: List[Duel] = []
        self.ai = AIHistory()
        self.ai_key = key
        self.generating = False
        self.crossposter = Crossposter(CROSSPOSTER_FILE)
        self.tg_link_keys: Dict[int, str] = {} # {dc_id: key}
        self.tg_message_sendable_in: float = 0
        self.reload()


    def new(self):
        '''
        Rewrites the old database with the new one.
        '''
        self.users: Dict[int, User] = {}
        self.timed_lb = TimedLeaderboard()
        self.bump_ping_at = time.time()+BUMP_PING_EVERY
        self.last_bump = 0

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
        self.bump_ping_at: float = data.get('bump_ping_at', time.time()+BUMP_PING_EVERY)
        self.last_bump: float = data.get('last_bump', 0)

        # data
        try:
            with open(self.data_file, encoding='utf-8') as f:
                self.data: dict = json.load(f)
        except Exception as e:
            log(f'Unable to load data file: {e}', 'api')

        self.skins: Dict[str, SkinData] = {
            k: SkinData(k, v) for k, v in self.data.get('skins', {}).items()
        }
        self.fonts: Dict[str, FontData] = {
            k: FontData(k, v) for k, v in self.data.get('fonts', {}).items()
        }

        # other data from folder
        
        # emoji list
        try:
            with open(EMOJIS_FILE, encoding='utf-8') as f:
                data = f.read()
                self.emojis: List[str] = data.split('\n')
            log('Reloaded emoji list', 'api')

        except Exception as e:
            log(f'Error while loading emoji list: {e}', 'api', level=ERROR)
        
        # fate actions
        try:
            with open(FATE_ACTIONS_FILE, encoding='utf-8') as f:
                data = f.read()
                self.fate_actions: List[str] = data.split('\n')
            log('Reloaded fate actions', 'api')

        except Exception as e:
            log(f'Error while loading fate actions: {e}', 'api', level=ERROR)
        self.commit()


    def commit(self):
        '''
        Saves user data to the file.
        '''
        if time.time()-self.last_commit < MIN_SECONDS_BETWEEN_COMMITS:
            return
        self.last_commit = time.time()
        
        data = {
            'users': {}
        }

        # users
        for i in self.users:
            data['users'][i] = self.users[i].to_dict()

        data['timed_lb'] = self.timed_lb.to_dict()
        data['temp_vcs'] = {id: i.to_dict() for id, i in self.temp_vcs.items()}
        data['quarantines'] = self.quarantines
        data['sk_last_spawn'] = self.sk_last_spawn
        data['bump_ping_at'] = self.bump_ping_at
        data['last_bump'] = self.last_bump

        # saving
        try:
            json_data = json.dumps(data)
        except Exception as e:
            log(f'Unable to save user data: {e}', 'api', WARNING)
            return

        try:
            with open(self.users_file+'.temp', 'w') as f:
                f.write(json_data)
                f.flush()
                os.fsync(f.fileno())

            os.replace(self.users_file+'.temp', self.users_file)
        except Exception as e:
            log(f'Unable to save user data to file: {e}', 'api', ERROR)


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


    def get_user_by_tg(self, id:int) -> User | None:
        '''
        Returns user by Telegram user ID.
        '''
        for i in self.users.values():
            if i.tg == id:
                return i


    def get_user_by_tg_username(self, username:str) -> User | None:
        '''
        Returns user by Telegram username.
        '''
        for i in self.users.values():
            if i.tg_username == username:
                return i


    def cache_user_data(self, user:discord.User):
        '''
        Saves user avatar to user data.
        '''
        if user.bot:
            return
        
        botuser = self.get_user(user.id)
        new_url = None if not user.avatar else user.avatar.url

        if new_url != botuser.avatar_url:
            log(f'Updated {botuser.id}\'s cached avatar')
            botuser.avatar_url = new_url
            self.commit()

        if user.display_name != botuser.dc_name:
            log(f'Updated {botuser.id}\'s cached display name')
            botuser.dc_name = user.display_name
            self.commit()


    def cache_tg_user_data(self, user: aiogram.types.User):
        '''
        Saves user's Telegram username.
        '''
        botuser = self.get_user_by_tg(user.id)
        if not botuser:
            return
        
        if user.username != botuser.tg_username:
            log(f'Updated {botuser.id}\'s TG account username to {user.username}')
            botuser.tg_username = user.username
            self.commit()
        

    def get_tg_link_key(self, id: int) -> str:
        '''
        Gets a random key for Telegram account linking.
        '''
        self.tg_link_keys[id] = str(random.randint(10000,99999))
        return self.tg_link_keys[id]
    

    def confirm_tg_link_key(self, tg_id: int, key: str) -> User | None:
        '''
        Link a Telegram account to a Discord account with a key.
        '''
        for dc_id, saved_key in self.tg_link_keys.items():
            if saved_key == key:
                # linking account
                user = self.get_user(dc_id)
                user.tg = tg_id
                self.commit()
                return user
            

    def unlink_tg(self, id: int):
        '''
        Unlink Telegram account from a user.
        '''
        user = self.get_user(id)
        user.tg = None
        self.commit()
            

    def change_display_name(self, id: int, name: str) -> str | None:
        '''
        Changes user's display name.

        Returns old display name.
        '''
        user = self.get_user(id)
        old_name = copy(user.display_name)
        user.display_name = name
        self.commit()
        return old_name
            

    def change_location(self, id: int, location: str):
        '''
        Changes user current event location.
        '''
        user = self.get_user(id)
        user.location = location
        self.commit()
            

    def set_loc_data(self, id: int, key: str, data: str):
        '''
        Changes user current event location data.
        '''
        user = self.get_user(id)
        user.loc_data[key] = data
        self.commit()
            

    def set_swimloc(self, id: int, data: str):
        user = self.get_user(id)
        user.swimloc = data
        self.commit()
            

    def add_to_swiminv(self, id: int, item: str):
        user = self.get_user(id)
        if len(user.swiminv) < 4:
            user.swiminv.append(item)
        self.commit()
            

    def remove_from_swiminv(self, id: int, item: str):
        user = self.get_user(id)
        if item in user.swiminv:
            user.swiminv.remove(item)
        self.commit()
            

    def set_swiminv(self, id: int, items: List[str]):
        user = self.get_user(id)
        user.swiminv = items
        self.commit()
            

    def add_to_library(self, id: int, item: str):
        '''
        Changes user current event location data.
        '''
        user = self.get_user(id)
        if item in user.library:
            return
        
        user.library.append(item)
        log(f'User {id} got item {item} added to library')
        self.commit()
    

    def reset_ai(self):
        '''
        Resets AI message context.
        '''
        self.ai = AIHistory()
    

    async def gen_ai(self, history: List[dict]) -> Tuple[str, bytes | None]:
        '''
        Generates an AI message.

        Returns message content and image data, if there is any.
        '''
        async with aiohttp.ClientSession(base_url=BASE_URL, headers={'Authorization': 'Bearer '+self.ai_key}) as session:
            async with session.post('chat/completions', json={
                'model': MODEL,
                'messages': history
            }) as response:
                if response.status != 200:
                    raise Exception(await response.text())
                respjson = await response.json()

        usage = respjson['usage']
        message = respjson['choices'][0]['message']
        text = message['content']

        if 'images' in message:
            img_base64 = message['images'][0]['image_url']['url'].split('base64,')[1]
            return message['content'], base64.b64decode(img_base64)
        
        log(
            f'Prompt tokens: {usage.get("prompt_tokens", "None")} / '\
            f'Completion tokens: {usage.get("completion_tokens", "None")} / '\
            f'Messages in history: {len(history)}',
        'api')
        return text, None

    def get_roulette_by_user(self, user: int) -> "Roulette | None":
        '''
        Returns a roulette game by user.
        '''
        for i in self.roulette_games:
            if i.user1 == user or i.user2 == user:
                return i
            

    def add_roulette(self, user: int):
        '''
        Create a roulette game.
        '''
        game = Roulette(user, self.remove_roulette)
        self.roulette_games.append(game)
        return game
            
    
    def give_up_roulette(self, user: int) -> "Roulette | None":
        game = self.get_roulette_by_user(user)

        if game is None:
            return

        self.roulette_games.remove(game)
        return game
    

    def remove_roulette(self, game: Roulette, rewardee: int, xp: int):
        self.roulette_games.remove(game)
        if rewardee and xp:
            self.add_xp(rewardee, xp, 'roulette')
    

    def start_roulette(self, user1: int, user2: int) -> "Roulette | None":
        game = self.get_roulette_by_user(user1)
        
        if not game:
            return
        
        if game.user2:
            return
        
        game.start(user2)
        return game


    def get_duel_by_user(self, user: int) -> "Duel | None":
        '''
        Returns a duel game by user.
        '''
        for i in self.duel_games:
            if i.user1 == user or i.user2 == user:
                return i
            

    def add_duel(self, user: int):
        '''
        Create a duel game.
        '''
        game = Duel(user, self.remove_duel)
        self.duel_games.append(game)
        return game
            
    
    def give_up_duel(self, user: int) -> "Duel | None":
        game = self.get_duel_by_user(user)

        if game is None:
            return

        self.duel_games.remove(game)
        game.stopped = True
        return game
    

    def remove_duel(self, game: Duel, rewardee: int, xp: int):
        self.duel_games.remove(game)
        if rewardee and xp:
            self.add_xp(rewardee, xp, 'duel')
    

    def start_duel(self, user1: int, user2: int) -> "Duel | None":
        game = self.get_duel_by_user(user1)
        
        if not game:
            return
        
        if game.user2:
            return
        
        game.start(user2)
        return game


    def get_random_mfr(self) -> MfrCard:
        '''
        Return a random mishkfrede card
        '''
        rarity = random.choices(
            list(self.data['mfr'].items()),
            [i['chance'] for i in self.data['mfr'].values()]
        )[0]

        url = random.choice(rarity[1]['images'])
        xp = random.randint(*rarity[1]['xp'])
        return MfrCard(rarity[0], rarity[1]['name'], xp, url, rarity[1]['color'])
    

    def bump(self, user_id: int) -> int:
        '''
        Saves a bump and returns gained XP.
        '''
        xp = random.randint(*BUMP_XP)
        self.add_xp(user_id, xp, 'bump')
        self.bump_ping_at = time.time() + BUMP_TIMEOUT
        self.last_bump = time.time()

        self.commit()
        return xp
    

    def bump_timeout(self) -> int:
        self.bump_ping_at = time.time() + BUMP_PING_EVERY
        self.commit()
    
    
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
        if index >= len(user.reminders):
            return
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


    def add_coin(self, user_id:int, amount:int) -> bool:
        '''
        Exchanges Qs for coins and returns whether it was successful.
        '''
        user = self.get_user(user_id)

        if user.q_level < amount:
            return False
        
        user.q_level -= amount
        user.coins += amount

        self.commit()
        return True


    def add_mfr_stat(self, user_id:int, card:str):
        '''
        Adds Mishkfrede stat to user.
        '''
        user = self.get_user(user_id)

        if user.mfr_timeout < time.time():
            user.mfr_timeout = time.time()+MFR_TIMEOUT

        if card not in user.mfr_stats:
            user.mfr_stats[card] = 0
        user.mfr_stats[card] += 1

        self.commit()


    def add_xp(self, user_id:int, xp:int, reason:str, store_lvl_up:bool=True) -> "int | None":
        '''
        Adds XP to user.

        If user leveled up, return the new level.
        '''
        user = self.get_user(user_id)

        old_level = deepcopy(user.xp.level)
        user.xp.add_xp(LATEST_SEASON, xp, reason)

        self.timed_lb.add_xp(user_id, xp)
        self.commit()

        if old_level != user.xp.level:
            if store_lvl_up:
                user.to_send_lvl_up_msg = True
                
            return user.xp.level
        

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


    def repblock(self, id: int, length: int):
        '''
        Repblocks the user
        '''
        user = self.get_user(id)
        user.rep_block_until = time.time()+length
        self.commit()


    def add_rep(self, id: int, amount: int, placer: int = None) -> "float | None":
        '''
        Changes user's rep count.

        Returns a float that indicates when to try again if action is timeouted
        '''
        user = self.get_user(id)

        if placer != None:
            placer: User = self.get_user(placer)

            if amount > 0:
                if placer.plus_rep_timeout > time.time():
                    return placer.plus_rep_timeout
                placer.plus_rep_timeout = time.time()+PLUS_REP_EVERY

            elif amount < 0:
                if placer.id in user.minus_repped:
                    if user.minus_repped[placer.id] > time.time():
                        return user.minus_repped[placer.id]
                
                if placer.minus_rep_timeout > time.time():
                    return placer.minus_rep_timeout
                
                placer.minus_rep_timeout = time.time()+MINUS_REP_EVERY
                user.minus_repped[placer.id] = time.time()+MINUS_REP_COUNTER_TIMEOUT

        if amount > 0:
            user.plus_reps += amount
        else:
            user.minus_reps -= amount

        self.commit()


    def get_rep_limits(self) -> Tuple[int,int]:
        '''
        Returns a tuple with 1st value being the lower limit and 2nd value being the upper limit of reputation.
        '''
        rep = [i.rep for i in self.users.values()]
        return min(rep), max(rep)


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
            self.add_xp(id, 1, 'vc')
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
    

    def get_leaders(self, type: Literal['alltime','season','week','day','vc','stream','mic','q','rep'], places=9) -> List[User]:
        '''
        Returns a list of users sorted by type.
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
        elif type == 'rep':
            users = sorted([i for i in self.users.values() if i.plus_reps != 0 or i.minus_reps != 0], key=lambda x: x.rep, reverse=True)
        return users[:places]
    

    def get_place(self, user_id:int, type: Literal['alltime','season','week','day','vc','stream','mic','q','rep']) -> int:
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
                xp = i.vc.vc_time_speaking,
            elif type == 'q':
                xp = i.q
            elif type == 'rep':
                xp = i.rep
                if i.plus_reps == 0 and i.minus_reps == 0:
                    prev_xp = xp
                    continue

            if prev_xp != xp:
                place += 1
                prev_xp = xp

            if i.id == user_id:
                return place
    

    def add_quarantine(self, user_id: int, t: int):
        '''
        Sends someone to quarantine
        '''
        self.check_user(user_id)
        self.quarantines.update({user_id: t})
        self.commit()
    
    def remove_quarantine(self, user_id: int):
        '''
        Removes someone from quarantine
        '''
        self.check_user(user_id)
        self.quarantines.pop(user_id)
        self.commit()
