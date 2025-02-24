from copy import deepcopy
import json

with open(input('Enter old db:'), encoding='utf-8') as f:
    data = json.load(f)

new_data: dict[int, dict] = {}

def check_data(id:int):
    if id not in new_data:
        new_data[id] = {
            "xp": 0,
            "quarantine": None,
            "reminders": [],
            "tokens": {},
            "token_dig_timeout": 0.0,
            "games_timeout": 0.0
        }


for i in data['remindme']:
    check_data(i['id'])

    d = deepcopy(i)
    d['id'] = int(i['jump_url'].split('/')[-1])
    new_data[i['id']]['reminders'].append(d)


for k,v in data['inventory'].items():
    check_data(int(k))

    new_data[int(k)]['tokens'] = v


for k,v in data['dig_timeout'].items():
    check_data(int(k))

    new_data[int(k)]['token_dig_timeout'] = v


for k,v in data['game_timeout'].items():
    check_data(int(k))

    new_data[int(k)]['games_timeout'] = v


for k,v in data['rank'].items():
    check_data(int(k))

    new_data[int(k)]['xp'] = v


total_data = {"users": new_data}


with open(input('Enter new db:'), 'w', encoding='utf-8') as f:
    json.dump(total_data, f, ensure_ascii=False, indent=4)