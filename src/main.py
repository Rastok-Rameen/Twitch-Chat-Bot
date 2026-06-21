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

#== Environment Variable Loading
from dotenv import load_dotenv
import os

#== Main Widget
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #== Main Layout
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        #=== Button to start message buffer
        StartButton = Button(text="Start buffer", size_hint=(1, 0.3),background_color="#00FF00",color="#00FF00")
        main_layout.add_widget(StartButton)
        # === Button to stop message buffer
        StopButton = Button(text="Stop buffer", size_hint=(1, 0.3),background_color="#00FF00",color="#00FF00")
        main_layout.add_widget(StopButton)
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