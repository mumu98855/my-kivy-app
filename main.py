from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '650')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
import os
import json
import hashlib
import secrets

Window.clearcolor = (0.05, 0.05, 0.05, 1)

RED = (0.8, 0.1, 0.1, 1)
DARK_RED = (0.4, 0.05, 0.05, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.6, 0.6, 0.6, 1)
PANEL = (0.12, 0.12, 0.12, 1)

class HackerLauncherApp(App):
    def build(self):
        self.data_path = os.path.join(self.user_data_dir, 'vault.json')
        self.events = []
        self.load_vault()
        
        self.root = BoxLayout(orientation='vertical')
        self.show_auth()
        return self.root

    def load_vault(self):
        try:
            with open(self.data_path, 'r', encoding='utf-8') as vault_file:
                data = json.load(vault_file)
            self.pin_salt = data.get('pin_salt')
            self.pin_hash = data.get('pin_hash')
            self.apps = data.get('apps', [])
        except (OSError, ValueError):
            self.pin_salt = None
            self.pin_hash = None
            self.apps = [
                {'name': 'MINECRAFT', 'target': 'minecraft://'},
                {'name': 'BLOX FRUITS', 'target': 'roblox://'},
            ]

    def save_vault(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as vault_file:
            json.dump({
                'pin_salt': self.pin_salt,
                'pin_hash': self.pin_hash,
                'apps': self.apps,
            }, vault_file, indent=2)

    def pin_digest(self, pin, salt):
        return hashlib.pbkdf2_hmac(
            'sha256', pin.encode('utf-8'), bytes.fromhex(salt), 200000
        ).hex()

    def text_label(self, text, size, color=WHITE, bold=False, height=None):
        label = Label(
            text=text,
            font_size=size,
            color=color,
            bold=bold,
            halign='left',
            valign='middle',
            size_hint_y=None if height else 1,
            height=height or 0,
        )
        label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        return label

    def make_button(self, text, callback, color=RED, height=46):
        button = Button(
            text=text,
            size_hint_y=None,
            height=height,
            background_normal='',
            background_down='',
            background_color=color,
            color=WHITE,
            bold=True,
            font_size='14sp',
        )
        button.bind(on_release=callback)
        return button

    def show_auth(self):
        self.root.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=[28, 32], spacing=16)
        
        layout.add_widget(self.text_label('[ SECURE VAULT ]', '22sp', RED, True, 40))
        layout.add_widget(self.text_label('HACKER LAUNCHER / LOCAL ACCESS', '11sp', MUTED, True, 20))
        layout.add_widget(self.text_label(
            'INITIALIZE PIN' if not self.pin_hash else 'VAULT LOCKED',
            '16sp', WHITE, True, 30,
        ))
        
        self.pin_input = TextInput(
            hint_text='Enter 4+ digit PIN', password=True, multiline=False,
            input_filter='int', size_hint_y=None, height=48,
            background_normal='', background_active='', background_color=PANEL,
            foreground_color=WHITE, hint_text_color=MUTED, cursor_color=RED,
            padding=[14, 12], font_size='16sp',
        )
        self.pin_input.bind(on_text_validate=self.authenticate)
        layout.add_widget(self.pin_input)
        
        self.auth_message = self.text_label('', '12sp', RED, height=24)
        layout.add_widget(self.auth_message)
        
        layout.add_widget(self.make_button(
            'UNLOCK VAULT' if self.pin_hash else 'CREATE PIN', self.authenticate
        ))
        
        self.root.add_widget(layout)

    def authenticate(self, *_):
        pin = self.pin_input.text.strip()
        if not self.pin_hash:
            if len(pin) < 4:
                self.auth_message.text = 'PIN must be at least 4 digits.'
                return
            self.pin_salt = secrets.token_hex(16)
            self.pin_hash = self.pin_digest(pin, self.pin_salt)
            self.save_vault()
            self.show_vault()
            return
        if secrets.compare_digest(self.pin_digest(pin, self.pin_salt), self.pin_hash):
            self.show_vault()
        else:
            self.auth_message.text = 'Incorrect PIN.'
            self.pin_input.text = ''

    def show_vault(self):
        self.root.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=[20, 16], spacing=12)
        
        header = BoxLayout(size_hint_y=None, height=45, spacing=8)
        header.add_widget(self.text_label('[ SECURE VAULT ]', '16sp', RED, True))
        header.add_widget(self.make_button('LOCK', lambda *_: self.show_auth(), PANEL, 38))
        layout.add_widget(header)
        
        layout.add_widget(self.make_button('+  ADD & HIDE NEW APP', self.open_add_dialog, RED, 48))

        self.apps_layout = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None)
        self.apps_layout.bind(minimum_height=self.apps_layout.setter('height'))
        
        self.apps_scroll = ScrollView(do_scroll_x=False)
        self.apps_scroll.add_widget(self.apps_layout)
        layout.add_widget(self.apps_scroll)

        layout.add_widget(self.text_label('STATUS LOG', '11sp', RED, True, 20))
        self.log_label = self.text_label('>> VAULT READY & SECURE', '11sp', MUTED, height=30)
        layout.add_widget(self.log_label)
        
        self.root.add_widget(layout)
        self.refresh_apps()

    def refresh_apps(self):
        self.apps_layout.clear_widgets()
        for app in self.apps:
            row = BoxLayout(size_hint_y=None, height=52, spacing=8)
            
            app_btn = Button(
                text=f"> LAUNCH: {app['name']}",
                size_hint_x=0.7,
                background_normal='',
                background_color=DARK_RED,
                color=WHITE,
                bold=True,
                font_size='14sp'
            )
            app_btn.bind(on_release=lambda _, item=app: self.launch(item))
            row.add_widget(app_btn)
            
            rem_btn = Button(
                text='REMOVE',
                size_hint_x=0.3,
                background_normal='',
                background_color=PANEL,
                color=MUTED,
                bold=True,
                font_size='12sp'
            )
            rem_btn.bind(on_release=lambda _, item=app: self.remove_app(item))
            row.add_widget(rem_btn)
            
            self.apps_layout.add_widget(row)

    def open_add_dialog(self, *_):
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        name_input = TextInput(hint_text='App Name (e.g. Roblox)', multiline=False, size_hint_y=None, height=42)
        target_input = TextInput(hint_text='Target Path or Link', multiline=False, size_hint_y=None, height=42)
        message = self.text_label('', '11sp', RED, height=20)
        
        content.add_widget(self.text_label('HIDE NEW APP', '14sp', RED, True, 24))
        content.add_widget(name_input)
        content.add_widget(target_input)
        content.add_widget(message)
        
        popup = Popup(
            title='ADD TO VAULT', content=content, size_hint=(0.85, None), height=260,
            separator_color=RED, background_color=PANEL,
        )

        def save_app(*_):
            name = name_input.text.strip()
            target = target_input.text.strip()
            if not name:
                message.text = 'Please enter an app name.'
                return
            self.apps.append({'name': name, 'target': target or 'app://'})
            self.save_vault()
            self.refresh_apps()
            popup.dismiss()

        content.add_widget(self.make_button('SAVE & HIDE', save_app, RED, 38))
        popup.open()

    def remove_app(self, app):
        self.apps.remove(app)
        self.save_vault()
        self.refresh_apps()

    def launch(self, app):
        self.log_label.text = f">> LAUNCHING {app['name']}..."

if __name__ == '__main__':
    HackerLauncherApp().run()