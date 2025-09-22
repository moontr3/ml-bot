# moonland bot

A bot I made for [my Discord server](https://discord.gg/s3NrXyYjnG) with Python, `discord.py` and `pygame-ce`.

## Features/Todo list

- [x] Info commands
- [x] Basic moderation tools
- [ ] Custom roles
- [x] Reminders
- [x] Logging
- [x] Leveling system and ranks
- [x] Quarantine
- [x] User verification
- [x] Minigames

## How to run

Don't.

`.env` file should have 5 variables:

- `BOT_TOKEN` - Discord bot token

- `LOGGING_WEBHOOK` - Webhook URL used to send log messages

- `SERVICE_WEBHOOK` - Webhook URL used to send miscellaneous messages, like VC joins/leaves, anonymous messages, etc.

Other than that, you can configure bot settings in `config.py`.

`data.json` contains data for different features, like list of skins, fonts, mfr cards, etc.

## Optional features

Add these to your `.env` file with the required data to enable the features:

- `AI_KEY` - Provide an `api.navy` API key to enable AI chatbot

- `TG_TOKEN` - Provide a Telegram bot token to enable crossposting from Discord to Telegram and vice versa
