import os
import json
import ast
import operator
import traceback

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty

# Safe TTS import
try:
    from plyer import tts
except Exception:
    tts = None

DIAGNOSTIC_LOG = "jarvis_startup_error.txt"

def save_diagnostic_error(error_text):
    try:
        log_path = os.path.join(App.get_running_app().user_data_dir, DIAGNOSTIC_LOG) if App.get_running_app() else DIAGNOSTIC_LOG
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(str(error_text))
    except Exception:
        pass

# Android voice input
try:
    from android import activity
    from android.permissions import Permission, request_permissions
    from jnius import autoclass

    HAS_ANDROID = True

    Intent = autoclass("android.content.Intent")
    RecognizerIntent = autoclass("android.speech.RecognizerIntent")

except Exception:
    HAS_ANDROID = False


SECRET_FILE = "secret_vault.txt"

FAMILY_DETAILS = {
    "father": "John",
    "mother": "Mary"
}


KV = r'''
<JARVISUI>:
    orientation: "vertical"

    BoxLayout:
        size_hint_y: None
        height: "50dp"
        spacing: "5dp"
        padding: "5dp"

        Button:
            text: "☰"
            size_hint_x: None
            width: "45dp"
            on_release: root.open_sidebar()

        Button:
            text: root.selected_model
            on_release: root.open_model_dropdown(self)

        Button:
            text: "⋮"
            size_hint_x: None
            width: "45dp"
            on_release: root.open_three_dots_menu(self)

    ScrollView:
        id: scroll

        BoxLayout:
            id: chat_logs
            orientation: "vertical"
            size_hint_y: None
            spacing: "6dp"
            padding: "8dp"
            height: self.minimum_height

    BoxLayout:
        size_hint_y: None
        height: "55dp"
        spacing: "4dp"
        padding: "5dp"

        Button:
            text: "📷"
            size_hint_x: None
            width: "42dp"
            on_release: root.open_vision_picker()

        TextInput:
            id: command
            hint_text: "Message JARVIS..."
            multiline: False
            write_tab: False
            on_text_validate: root.ask()

        Button:
            text: "MIC"
            font_size: "9sp"
            bold: True
            size_hint_x: None
            width: "42dp"
            on_release: root.listen_voice_input()

        Button:
            text: "➤"
            size_hint_x: None
            width: "42dp"
            on_release: root.ask()
'''

try:
    Builder.load_string(KV)
except Exception as e:
    save_diagnostic_error(traceback.format_exc())
    raise


class SafeCalculator:

    @staticmethod
    def calculate(expr):
        try:
            allowed = "0123456789+-*/.() "
            expr = expr.strip()

            if not expr:
                return None

            if all(c in allowed for c in expr):
                return eval(
                    expr,
                    {"__builtins__": {}},
                    {}
                )

        except Exception:
            pass

        return None


class MessageBubble(BoxLayout):

    def __init__(
        self,
        text="",
        is_user=False,
        is_secret=False,
        theme_colors=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.size_hint_y = None
        self.height = "40dp"

        prefix = "User" if is_user else "JARVIS"

        self.add_widget(
            Label(
                text=f"{prefix}: {text}",
                text_size=(None, None)
            )
        )


class JARVISUI(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.is_secret_mode = False
        self.is_decoy_panel = False
        self.is_pinned = False
        self.awaiting_password = False

        self.secret_chat_history = []
        self.normal_chat_history = []

        self.theme_colors = {}
        self.selected_model = "Gemini Flash"

        if HAS_ANDROID:
            try:
                activity.bind(
                    on_activity_result=self.on_voice_result
                )
            except Exception:
                pass

    def speak_result(self, text):
        try:
            if tts and text:
                tts.speak(str(text))
        except Exception as e:
            print("TTS Error:", e)

    def listen_voice_input(self):

        if not HAS_ANDROID:
            self.add_message(
                "Voice input is available in the Android APK.",
                is_user=False
            )
            return

        try:
            request_permissions(
                [Permission.RECORD_AUDIO],
                self.voice_permission_callback
            )
        except Exception:
            self.launch_voice_recognizer()

    def voice_permission_callback(self, permissions, grants):
        try:
            if grants and all(grants):
                self.launch_voice_recognizer()
            else:
                self.add_message(
                    "Microphone permission was denied.",
                    is_user=False
                )
        except Exception as e:
            self.add_message(
                f"Permission error: {e}",
                is_user=False
            )

    def launch_voice_recognizer(self):
        try:
            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "te-IN"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT,
                "Speak to JARVIS..."
            )

            activity.startActivityForResult(
                intent,
                5001
            )

        except Exception as e:
            self.add_message(
                f"Voice recognition error: {e}",
                is_user=False
            )

    def on_voice_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != 5001:
            return

        try:
            if result_code == -1 and intent is not None:

                results = intent.getStringArrayListExtra(
                    RecognizerIntent.EXTRA_RESULTS
                )

                if results is not None and results.size() > 0:

                    recognized_text = str(
                        results.get(0)
                    )

                    self.ids.command.text = recognized_text

                    Clock.schedule_once(
                        lambda dt: self.ask(),
                        0.2
                    )

        except Exception as e:
            self.add_message(
                f"Voice result error: {e}",
                is_user=False
            )

    def request_hide_chat_access(self):
        self.awaiting_password = True

        self.add_message(
            "🔒 Enter Security Password:",
            is_user=False
        )

    def verify_password(self, pwd_text):

        clean_pwd = pwd_text.lower().strip()

        self.awaiting_password = False

        if clean_pwd in ("ironman", "iron man"):
            self.open_decoy_chat_panel(is_fake=False)
        else:
            self.open_decoy_chat_panel(is_fake=True)

    def open_decoy_chat_panel(self, is_fake=False):

        self.ids.chat_logs.clear_widgets()

        if is_fake:

            self.is_secret_mode = False
            self.is_decoy_panel = True

            fake_messages = [
                {
                    "text": "Hey, bought milk and grocery items?",
                    "is_user": True
                },
                {
                    "text": "Yes, I got them. Anything else needed?",
                    "is_user": False
                },
                {
                    "text": "No, that is all. Thanks!",
                    "is_user": True
                }
            ]

            for msg in fake_messages:
                self.add_message_bubble(
                    msg["text"],
                    msg["is_user"],
                    is_secret=False
                )

        else:

            self.is_secret_mode = True
            self.is_decoy_panel = False

            self.add_message(
                "⚡ MOSAIC PRIVATE VAULT UNLOCKED ⚡",
                is_user=False
            )

            self.add_message(
                "Type 'pin' to keep history, or 'unpin' to auto-clear on exit.",
                is_user=False
            )

            for msg in self.secret_chat_history:
                self.add_message_bubble(
                    msg["text"],
                    msg["is_user"],
                    is_secret=True
                )

    def exit_secret_mode(self):

        if not self.is_pinned:

            self.secret_chat_history = []

            if os.path.exists(SECRET_FILE):
                try:
                    os.remove(SECRET_FILE)
                except Exception:
                    pass

        else:
            self.save_secret_history()

        self.is_secret_mode = False
        self.is_decoy_panel = False

        self.ids.chat_logs.clear_widgets()

        self.add_message(
            "Exited Private Vault. Back to Main JARVIS.",
            is_user=False
        )

        for msg in self.normal_chat_history:
            self.add_message_bubble(
                msg["text"],
                msg["is_user"],
                is_secret=False
            )

    def save_secret_history(self):

        try:
            with open(
                SECRET_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    self.secret_chat_history,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

        except Exception:
            pass

    def open_three_dots_menu(self, widget):

        dropdown = DropDown()

        btn_mosaic = Button(
            text="Mosaic Vault",
            size_hint_y=None,
            height="44dp",
            background_normal=""
        )

        btn_mosaic.bind(
            on_release=lambda b_obj: (
                dropdown.dismiss(),
                self.exit_secret_mode()
                if self.is_secret_mode
                else self.request_hide_chat_access()
            )
        )

        dropdown.add_widget(btn_mosaic)

        btn_decoy = Button(
            text="Decoy Mode",
            size_hint_y=None,
            height="44dp",
            background_normal=""
        )

        btn_decoy.bind(
            on_release=lambda b_obj: (
                dropdown.dismiss(),
                self.open_decoy_chat_panel(is_fake=True)
            )
        )

        dropdown.add_widget(btn_decoy)

        dropdown.open(widget)

    def open_model_dropdown(self, widget):

        if self.is_secret_mode or self.is_decoy_panel:
            return

        dropdown = DropDown()

        models = [
            "Gemini Flash",
            "Gemini Pro",
            "ChatGPT 4o",
            "JARVIS Local"
        ]

        for m_name in models:

            btn = Button(
                text=m_name,
                size_hint_y=None,
                height="44dp",
                background_normal=""
            )

            btn.bind(
                on_release=lambda b_obj, name=m_name: (
                    setattr(
                        self,
                        "selected_model",
                        name
                    ),
                    dropdown.dismiss()
                )
            )

            dropdown.add_widget(btn)

        dropdown.open(widget)

    def open_sidebar(self):

        popup = Popup(
            title="JARVIS Menu",
            content=Label(
                text="JARVIS AI System v1.0"
            ),
            size_hint=(0.7, 0.4)
        )

        popup.open()

    def open_vision_picker(self):

        content = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=10
        )

        filechooser = FileChooserListView()

        content.add_widget(filechooser)

        btn_layout = BoxLayout(
            size_hint_y=None,
            height="40dp",
            spacing=10
        )

        btn_select = Button(
            text="Select Image"
        )

        btn_cancel = Button(
            text="Cancel"
        )

        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)

        content.add_widget(btn_layout)

        popup = Popup(
            title="Select Document or Image",
            content=content,
            size_hint=(0.9, 0.9)
        )

        def load_file(instance):

            if filechooser.selection:

                selected_path = filechooser.selection[0]

                popup.dismiss()

                self.add_message(
                    f"📷 Selected image: {os.path.basename(selected_path)}",
                    is_user=True
                )

                self.add_message(
                    "Analyzing document / image content...",
                    is_user=False
                )

        btn_select.bind(
            on_release=load_file
        )

        btn_cancel.bind(
            on_release=popup.dismiss
        )

        popup.open()

    def ask(self):

        user_text = self.ids.command.text.strip()

        if not user_text:
            return

        self.ids.command.text = ""

        if self.awaiting_password:
            self.verify_password(user_text)
            return

        self.add_message(
            user_text,
            is_user=True
        )

        if self.is_secret_mode:

            clean_cmd = user_text.lower().strip()

            if clean_cmd == "pin":

                self.is_pinned = True

                self.save_secret_history()

                self.add_message(
                    "📌 Private chat pinned! History will persist.",
                    is_user=False
                )

                return

            elif clean_cmd == "unpin":

                self.is_pinned = False

                self.add_message(
                    "🗑️ Private chat unpinned! History will auto-clear on exit.",
                    is_user=False
                )

                return

        Clock.schedule_once(
            lambda dt: self.generate_response(user_text),
            0.1
        )

    def generate_response(self, user_text):

        lower_text = user_text.lower()

        calc_res = SafeCalculator.calculate(
            user_text
        )

        if calc_res is not None:

            ans = f"🧮 Result: {calc_res}"

            self.add_message(
                ans,
                is_user=False
            )

            self.speak_result(ans)

            return

        for relation, name in FAMILY_DETAILS.items():

            if relation in lower_text:

                ans = (
                    f"Your {relation} is {name}."
                )

                self.add_message(
                    ans,
                    is_user=False
                )

                self.speak_result(ans)

                return

        if self.is_decoy_panel:

            ans = "Updated grocery list."

            self.add_message(
                ans,
                is_user=False
            )

            return

        if (
            "hello" in lower_text
            or "hi" in lower_text
        ):

            response = (
                f"Hello! Operating via "
                f"{self.selected_model}."
            )

        elif "who are you" in lower_text:

            response = (
                "I am JARVIS, your personal AI assistant."
            )

        else:

            response = (
                f"Processed '{user_text}' "
                f"using {self.selected_model}."
            )

        self.add_message(
            response,
            is_user=False
        )

        self.speak_result(response)

    def add_message(
        self,
        text,
        is_user=False
    ):

        msg_obj = {
            "text": text,
            "is_user": is_user
        }

        if self.is_secret_mode:

            self.secret_chat_history.append(
                msg_obj
            )

            if self.is_pinned:
                self.save_secret_history()

        elif not self.is_decoy_panel:

            self.normal_chat_history.append(
                msg_obj
            )

        self.add_message_bubble(
            text,
            is_user,
            is_secret=self.is_secret_mode
        )

    def add_message_bubble(
        self,
        text,
        is_user,
        is_secret=False
    ):

        bubble = MessageBubble(
            text=text,
            is_user=is_user,
            is_secret=is_secret,
            theme_colors=self.theme_colors
        )

        self.ids.chat_logs.add_widget(
            bubble
        )

        Clock.schedule_once(
            lambda dt: setattr(
                self.ids.scroll,
                "scroll_y",
                0
            ),
            0.05
        )


class JARVISApp(App):

    def build(self):

        self.title = "JARVIS AI"

        return JARVISUI()


if __name__ == "__main__":

    try:
        JARVISApp().run()

    except Exception as err:
        print("CRITICAL STARTUP ERROR:")
        print(traceback.format_exc())
        save_diagnostic_error(traceback.format_exc())
        raise
