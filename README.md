# moonland bot

A bot I made for [my Discord server](https://discord.gg/s3NrXyYjnG) with Python, `discord.py`, `aiogram` and `pygame-ce`.

## Features/Todo list

- [x] Info commands
- [x] Basic moderation tools
- [x] Reminders
- [x] Logging
- [x] Leveling system and ranks
- [x] Quarantine
- [x] User verification
- [x] Minigames
- [x] AI chatbot
- [x] Profile customization
- [x] Telegram crossposting
- [x] Temporary voice channels
- [x] Reputation system
- [ ] Custom roles
- [ ] Story mode

## How to run

Don't.

`.env` file should have 3 variables:

- `BOT_TOKEN` - Discord bot token

- `LOGGING_WEBHOOK` - Webhook URL used to send log messages

- `SERVICE_WEBHOOK` - Webhook URL used to send miscellaneous messages, like VC joins/leaves, anonymous messages, etc.

Other than that, you can configure bot settings in `config.py`.

`data.json` contains data for different features, like list of skins, fonts, mfr cards, etc.

## Optional features

Add these to your `.env` file with the required data to enable the features:

- `AI_KEY` - Provide an `api.navy` API key to enable AI chatbot

- `TG_TOKEN` - Provide a Telegram bot token to enable crossposting from Discord to Telegram and vice versa

If you want to set up the Telegram crossposter, you can add a variable to `.env` with a webhook URL and put that variable name in the `crosspost_pairs` list in `data.json` (explained below).

## `data.json`

Data for different features, like list of skins, fonts, mfr cards, etc. is stored here.

All keys must exist in the file, but they can be empty.

```json
{
    // List of skins
    "skins": { // Skin key
        "red": {
            "name": "Red", // The name of the skin displayed
            "rarity": 1, // How likely this skin is to spawn compared to all other skins
            "emoji": "<:red:1357086642149785722>" // Discord Emoji Markdown of this skin
        },
        // ...
    },
    // List of fonts
    "fonts": {
        "firasans": { // Font key
            "name": "Fira Sans", // The name of the font displayed
            "rarity": 1, // How likely this font is to spawn compared to all other fonts
            "alt": ["fira"], // Optional list of alternative names
            "emoji": "<:firasans:1372154981578182696>" // Discord Emoji Markdown of this font
        },
        // ...
    },
    // List of FAQ pages
    "faq": [
        {
            "name": "Список команд", // The name of the page
            "emoji": "📃", // Emoji shown in the list of pages,
            "alt": ["commands", "команды"], // List of alternative names of this page that can be used to access it via the `ml!faq <page name>` command
            "content": "**Список команд moonland:bot**\n\n[SEP]\n\n- `faq` - Это меню" // Page content
            // Use \n\n to separate paragraphs
            // A line that only contains [SEP] will be changed to a Components V2 line separator
        },
        // ...
    ],
    // Summarized list of features available in ml!faq or when someone joins
    "quick_help": [
        {
            "text": "У нас есть...", // Text of the feature
            "button": { // Button shown beside the text, can be null
                "label": "Скины", // Button text
                "page": 4 // Index of a FAQ page to open when the button is clicked, OR a URL to open in a browser
            }
        },
        null, // You can use this to add a separator between sections
        // ...
    ],
    // List of Da-bot answers that the bot will reply with if the user has beast mode enabled
    "legacy": {
        // If the user's message contents are equal to a certain key, the bot will reply with the corresponding value
        "equals": {
            "да": "пизда",
            "нет": "пидора ответ",
            // ...
        },
        // If the user's message starts with a certain key, the bot will reply with the corresponding value
        "startswith": {
            "шлюхи аргумент": "аргумент не нужен, пидор обнаружен",
            "трактористом буду я": "сам",
            // ...
        }
    },
    // Mishkfrede cards
    "mfr": {
        "regular": { // Rarity key
            "name": "Обычная", // Rarity name,
            "chance": 60, // How likely this rarity is to spawn compared to all other rarities
            "hidden": true, // Optional value, if true then this rarity will not appear in stats (at all, not even the ???s) unless user has obtained it
            "xp": [1, 2], // Min and max range of XP to give when this card is pulled
            "images": [ // List of possible image URLs to get
                "https://moontr3.ru/assets/mfr/regular/1.png",
                "https://moontr3.ru/assets/mfr/regular/2.png",
                // ...
            ],
            "color": "#f09330" // Card embed color
        },
        // ...
    },
    // Telegram-Discord Crosspost channel/chat pairs
    "crosspost_pairs": [
        // List of pairs
        {
            "dc_id": 975809940444819467, // Discord channel ID
            "tg_id": -1003000053798, // Telegram chat/channel ID
            "webhook": null, // A .env variable name that has the webhook URL if you want to send messages thru the webhook instead of the bot account. This will allow to show a custom username.
            "users": null, // If you want to restrict whose messages are crossposted, put here a list of integers with allowed user's IDs whose messages should be crossposted
            "footer": false, // Show a text username and a button with a link to the chat/channel in the discord message's footer and a button with a specified in "dc_link" link in the telegram messages' footer when crossposting
            "show_user": true, // Show a text username above the message when crossposting (will do nothing if you use a webhook or the footer is enabled)
            "allow_bots": false, // Allow bot messages to be crossposted
            "tg_link": null, // A custom telegram channel link to put in the discord message's footer instead of the message link. Only has an effect if the footer is enabled
            "dc_link": null, // A discord invite link to put in the telegram message's footer
            "one_way": true // Whether to only crosspost messages FROM telegram TO discord and not the other way 
        },
        // ...
    ]
}
```
