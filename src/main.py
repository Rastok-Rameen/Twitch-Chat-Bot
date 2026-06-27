#== Python Twitch Chat Bot
#=== Kivy GUI
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.settings import SettingsWithSidebar
from kivy.network.urlrequest import UrlRequest
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.utils import get_color_from_hex
from kivy.config import ConfigParser
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.clock import Clock
from textwrap import fill
from kivy import Config

#== Keyboard input, Hotkeys and Storage
import keyboard
import json

#== Twitch Chat Bot API
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import threading
import asyncio
from datetime import datetime

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
def run_async_loop():
    loop.run_forever()
threading.Thread(target=run_async_loop, daemon=True).start()

#== Environment Variable Loading
#from dotenv import load_dotenv
#import os
#load_dotenv()
#APP_ID = os.getenv("TWITCH_CLIENT_ID")
#APP_SECRET = os.getenv("TWITCH_SECRET")
#TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")

#== Global API variables
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
APP_ID = None
APP_SECRET = None
TARGET_CHANNEL = None
message_queue = asyncio.Queue()
botActive = False
statusBot = False
currentMessage = None
banned_words = []

#== Append Message Log
def append_log(username, content, timestamp):
    app = App.get_running_app()
    screen = app.screenManager.get_screen("main")
    Clock.schedule_once(lambda x: screen.get_log().add_message(username, content, timestamp))

#== Twitch Chat Bot Initialisation
#== Bot Start Code
async def on_ready(ready_event: EventData):
    print('Bot is ready for work, joining channels')
    await ready_event.chat.join_room(TARGET_CHANNEL)

#== Message Received
async def on_message(msg: ChatMessage):
    global message_queue
    await message_queue.put(msg)
    append_log(msg.user.name, msg.text, datetime.fromtimestamp(msg.sent_timestamp / 1000).strftime("%H:%M:%S"))
    print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')
async def message_work():
    global currentMessage
    banned_file = App.get_running_app().config.get("Panel 4", "bannedwords")
    if banned_file:
        try:
            with open(banned_file, "r") as f:
                global banned_words
                banned_words = [line.strip().lower() for line in f if line.strip()]
        except:
            pass
    while True:
        while paused:
            await asyncio.sleep(0.1)
        currentMessage = await message_queue.get()
        if any(word in currentMessage.text.lower() for word in banned_words):
            continue
        while paused:
            await asyncio.sleep(0.1)
        keyboard.write(currentMessage.text)
        await asyncio.sleep(0.1)

#== Clear Message Buffer
def clearQueue():
    global message_queue
    global currentMessage
    try:
        while not message_queue.empty():
            message_queue.get_nowait()
    except:
        pass
    currentMessage = None
    append_log("System", "Message Buffer Cleared", datetime.now().strftime("%H:%M:%S"))

#== New Subscriber
async def on_sub(sub: ChatSub):
    print(f'New subscription in {sub.room.name}:\n'
          f'  Type: {sub.sub_plan}\n'
          f'  Message: {sub.sub_message}')

#== Custom !commands
async def dynamic_command(cmd: ChatCommand):
    name = cmd.name.lower()
    with open("src/dynamic_commands.json", "r") as f:
        custom_commands = json.load(f)
    if name in custom_commands:
        reply = custom_commands[name]
        reply = reply.format(TARGET_CHANNEL=TARGET_CHANNEL, USER=cmd.user.name)
        await cmd.reply(reply)

#== Stopping Chat Bot
stop_signal = False
def stop_bot():
    global stop_signal
    stop_signal = True

#== Pause/Unpause Chat Bot
paused = False
def pauseToggle():
    global paused
    paused = not paused
    print("paused: " , paused)
    App.get_running_app().updateStatus()
    if paused:
        append_log("System", "Message Buffer Paused", datetime.now().strftime("%H:%M:%S"))
    else:
        append_log("System", "Message Buffer UnPaused", datetime.now().strftime("%H:%M:%S"))

#== Bot Setup
async def Botrun():
    global botActive
    if botActive:
        stop_bot()
        return
    botActive = True
    global APP_ID
    global APP_SECRET
    global TARGET_CHANNEL
    app = App.get_running_app()
    APP_ID = app.config.get("Panel 1", "appID")
    APP_SECRET = app.config.get("Panel 1", "appSecret")
    TARGET_CHANNEL = app.config.get("Panel 1", "target_channel")
    stopkey = app.config.get("Panel 3", "stopbot")
    pausekey = app.config.get("Panel 3", "pausetoggle")
    clearkey = app.config.get("Panel 3", "clearbuffer")
    if (APP_ID == "") or (APP_SECRET == "") or (TARGET_CHANNEL == ""):
        Clock.schedule_once(lambda x: errorPopup("Missing keys in settings."))
        botActive = False
        stop_bot()
        return
    twitch = await Twitch(APP_ID, APP_SECRET)
    #auth = UserAuthenticator(twitch, USER_SCOPE)
    #token, refresh_token = await auth.authenticate()
    #await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)
    helper = UserAuthenticationStorageHelper(twitch, USER_SCOPE)
    await helper.bind()
    print("bind complete")

    #== Register Events
    chat = await Chat(twitch)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.register_event(ChatEvent.SUB, on_sub)
    #== Dynamic/Custom commands
    with open("src/dynamic_commands.json", "r") as f:
        custom_commands = json.load(f)
    for item in custom_commands.keys():
        chat.register_command(item, dynamic_command)
    global stop_signal
    stop_signal = False
    keyboard.add_hotkey(stopkey, stop_bot)
    keyboard.add_hotkey(pausekey, pauseToggle)
    keyboard.add_hotkey(clearkey, clearQueue)
    asyncio.create_task(message_work())

    chat.start()
    print("Bot Started")
    append_log("System", "Bot is ready!", datetime.now().strftime("%H:%M:%S"))
    global statusBot
    statusBot = True
    app.updateStatus()
    try:
        while not stop_signal:
            await asyncio.sleep(0.1)
    finally:
        chat.stop()
        await twitch.close()
        botActive = False
        statusBot = False
        app.updateStatus()
        print("Bot Stopped")
        append_log("System", "Bot stopped!", datetime.now().strftime("%H:%M:%S"))

#== Error popup
def errorPopup(error_message):
    app = App.get_running_app()
    errorLayout = BoxLayout(orientation="vertical", padding=20, spacing=10)
    errorLayout.add_widget(Label(text=error_message, color=app.config.get("Panel 2", "fgcolor")))
    closeButton = Button(text="OK", size_hint=(1, 0.3), background_color=app.config.get("Panel 2", "buttoncolor"), color=app.config.get("Panel 2", "fgcolor"))
    errorLayout.add_widget(closeButton)
    error_popup = Popup(title="Error", content=errorLayout, size_hint=(0.6, 0.4), separator_color=app.config.get("Panel 2", "accentcolor"), title_color=app.config.get("Panel 2", "fgcolor")
                        ,background_color=app.config.get("Panel 2", "bgcolor"))
    closeButton.bind(on_press=error_popup.dismiss)
    error_popup.open()

#== Main Widget
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = App.get_running_app()
        #== Main Layouts
        main_layout = BoxLayout(orientation="horizontal", padding=20, spacing=10)
        left_layout = BoxLayout(orientation="vertical", padding=20, spacing=10, size_hint_x=0.6)
        right_layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        #== Button to start Bot
        StartButton = Button(text="Start/Stop Bot", size_hint=(1, 0.3),background_color=app.config.get("Panel 2", "buttoncolor"),color=app.config.get("Panel 2", "fgcolor"))
        StartButton.bind(on_press=lambda x: asyncio.run_coroutine_threadsafe(Botrun(), loop))
        left_layout.add_widget(StartButton)
        #=== Button to toggle message buffer
        ToggleBufferButton = Button(text="Toggle message buffer", size_hint=(1, 0.3),background_color=app.config.get("Panel 2", "buttoncolor"),color=app.config.get("Panel 2", "fgcolor"))
        ToggleBufferButton.bind(on_press=lambda x: pauseToggle())
        left_layout.add_widget(ToggleBufferButton)
        #=== Button to open Settings
        SettingsButton = Button(text="Settings", size_hint=(1, 0.3),background_color=app.config.get("Panel 2", "buttoncolor"),color=app.config.get("Panel 2", "fgcolor"))
        SettingsButton.bind(on_press=lambda x: App.get_running_app().open_settings())
        left_layout.add_widget(SettingsButton)
        main_layout.add_widget(left_layout)
        #== Message Log
        self.message_log = Scrollable()
        self.message_log.size_hint_y = 1
        self.statusLabel = Label(text=app.status_text, height=30, size_hint_y=0.1, color=app.config.get("Panel 2", "fgcolor"))
        right_layout.add_widget(self.statusLabel)
        right_layout.add_widget(self.message_log)
        main_layout.add_widget(right_layout)
        self.add_widget(main_layout)

    def get_log(self):
        return self.message_log

    #== Updating Status Label
    def updateLabel(self):
        self.statusLabel.text = App.get_running_app().status_text

#== Scrollable Message View
class Scrollable(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #== Initialise Values
        self.scroll_x = 0
        self.scroll_y = 1
        self.size_hint_y = 0.9
        #== Embedded Box Layout
        self.emb_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self.add_widget(self.emb_box)

    #== Add Message to View
    def add_message(self, username, content, timestamp):
        new_message = MessageContainer(username, content, timestamp)
        self.emb_box.add_widget(new_message)
        self.emb_box.height += new_message.height
        Clock.schedule_once(lambda x: setattr(self, "scroll_y", 0), 0)

#== Message Container
class MessageContainer(BoxLayout):
    def __init__(self, username, content, timestamp, **kwargs):
        super().__init__(**kwargs)
        #== Initialise Values
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 50
        self.padding = [8, 4]
        app = App.get_running_app()

        #== Visible Message Content
        self.horizontal_box = BoxLayout(orientation="horizontal", size_hint_x=0.5)
        if username == "System":
            colour = app.config.get("Panel 2", "sysfgcolor")
        else:
            colour = app.config.get("Panel 2", "usrfgcolor")
        namelabel = Label(text=username, size_hint_y=1, color=colour)
        timelabel = Label(text=timestamp, size_hint_y=1, color=colour)
        #== Scrollable Message Length
        text_scroll = ScrollView(size_hint_x=0.8,size_hint_y=1,do_scroll_x=False,do_scroll_y=True,bar_width=4,always_overscroll=False)
        textlabel = Label(text=content,color=colour,size_hint_y=None,halign="left",valign="top")
        textlabel.bind(
            texture_size=lambda inst, val: setattr(inst, "height", inst.texture_size[1]),
            width=lambda inst, val: setattr(inst, "text_size", (val, None))
        )
        text_scroll.add_widget(textlabel)
        self.horizontal_box.add_widget(namelabel)
        self.horizontal_box.add_widget(timelabel)
        self.add_widget(self.horizontal_box)
        self.add_widget(text_scroll)

#== Main Class Build
class MainApp(App):
    title = "Twitch Bot"
    use_kivy_settings = False
    status_text = StringProperty("Bot Offline | Buffer Disabled")
    def build(self):
        #== Settings Panel
        self.settings_cls = SettingsWithSidebar
        self.config = ConfigParser()
        self.config.read('src/settings.ini')
        self.screenManager = ScreenManager()
        self.screenManager.add_widget(MainMenuScreen(name="main"))
        Window.clearcolor = self.config.get("Panel 2", "bgcolor")
        return self.screenManager

    #== Add panels to settings
    def build_settings(self, settings):
        settings.add_json_panel('Twitch Bot', self.config, 'src/twitch_settings.json')
        settings.add_json_panel('App Appearance', self.config, 'src/appearance_settings.json')
        settings.add_json_panel('Hotkeys', self.config, 'src/hotkeys_settings.json')
        settings.add_json_panel('Filter', self.config, 'src/filter_settings.json')

    #== Update Status String
    def updateStatus(self):
        if statusBot and not paused:
            App.get_running_app().status_text = "Bot Online | Buffer Disabled"
        elif statusBot and paused:
            App.get_running_app().status_text = "Bot Online | Buffer Enabled"
        elif not statusBot and paused:
            App.get_running_app().status_text = "Bot Offline | Buffer Enabled"
        elif not statusBot and not paused:
            App.get_running_app().status_text = "Bot Offline | Buffer Disabled"
        screen = App.get_running_app().screenManager.get_screen("main")
        Clock.schedule_once(lambda x: screen.updateLabel())


#== Main function
if __name__ == '__main__':
    MainApp().run()