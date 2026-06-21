#== Python Twitch Chat Bot
#=== Kivy GUI
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.settings import SettingsWithSidebar
from kivy.network.urlrequest import UrlRequest
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from textwrap import fill
from kivy import Config

#== Keyboard input and Hotkey Support
import keyboard

#== Twitch Chat Bot API
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import threading
import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
def run_async_loop():
    loop.run_forever()
threading.Thread(target=run_async_loop, daemon=True).start()

#== Environment Variable Loading
from dotenv import load_dotenv
import os

load_dotenv()
APP_ID = os.getenv("TWITCH_CLIENT_ID")
APP_SECRET = os.getenv("TWITCH_SECRET")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

#== Twitch Chat Bot Initialisation

#== Bot Start Code
async def on_ready(ready_event: EventData):
    print('Bot is ready for work, joining channels')
    await ready_event.chat.join_room(TARGET_CHANNEL)

#== Message Recieved
async def on_message(msg: ChatMessage):
    print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')

#== New Subscriber
async def on_sub(sub: ChatSub):
    print(f'New subscription in {sub.room.name}:\n'
          f'  Type: {sub.sub_plan}\n'
          f'  Message: {sub.sub_message}')

#== Custom !help command
async def help_command(cmd: ChatCommand):
    await cmd.reply(f"Welcome to {TARGET_CHANNEL}'s livestream! This bot reads your messages and adds them to his computer")

#== Stopping Chat Bot
stop_signal = False
def stop_bot():
    global stop_signal
    stop_signal = True

#== Bot Setup
async def Botrun():
    twitch = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(twitch, USER_SCOPE, url='http://localhost:3000', loop=loop)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

    #== Register Events
    chat = await Chat(twitch)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.register_event(ChatEvent.SUB, on_sub)
    chat.register_command('help', help_command)
    global stop_signal
    stop_signal = False
    keyboard.add_hotkey('page up+page down', stop_bot)

    chat.start()
    print("Bot Started")
    try:
        while not stop_signal:
            await asyncio.sleep(0.1)
    finally:
        chat.stop()
        await twitch.close()
        print("Bot Stopped")

#== Main Widget
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #== Main Layout
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        #== Button to start Bot
        StartButton = Button(text="Start Bot", size_hint=(1, 0.3),background_color="#00FF00",color="#00FF00")
        StartButton.bind(on_press=lambda x: asyncio.run_coroutine_threadsafe(Botrun(), loop))
        main_layout.add_widget(StartButton)
        #=== Button to start message buffer
        ToggleBufferButton = Button(text="Toggle buffer", size_hint=(1, 0.3),background_color="#00FF00",color="#00FF00")
        main_layout.add_widget(ToggleBufferButton)
        self.add_widget(main_layout)

#== Main Class Build
class MainApp(App):
    title = "Twitch Bot"
    def build(self):
        Window.clearcolor = "#000000"
        self.screenManager = ScreenManager()
        self.screenManager.add_widget(MainMenuScreen())
        return self.screenManager

#=== Main function
if __name__ == '__main__':
    MainApp().run()