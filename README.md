# Twitch Chat Bot

A Twitch Chat Bot that I have made on request of a friend, written in Python, and exported via Pyinstaller.
It connects to a Twitch Chat, and will log incoming messages and type it out as if it were your keyboard, if you desire chat to type for you.

The executible is unsigned, so it is highly likely that Windows Defender will try to block this application.

<img width="805" height="639" alt="image" src="https://github.com/user-attachments/assets/0d7bd1ac-3f40-40d1-9171-0522953cf5b5" />


## Features

- Kivy based GUI
- Custom !Commands via json
- Customisable Hotkeys to manage the bot
- Message filtering for censors
- Scrollable chat log
- Settings Panel to customise the app

## Installation (Executable)

1. Download the latest release from the Releases page.
2. Extract the ZIP file.
3. Run `TwitchBot.exe`.
4. Open **Settings** and enter:
   - Twitch Client ID
   - Twitch Client Secret
   - Target Channel
5. Also from **Settings**:
   - Select a list of banned words to filter (Optional)
   - Customise the Hotkeys
6. Start the bot.
7. Authenticate using a Twitch Account - This is the account that the !command responses will be posted from.
