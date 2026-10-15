import ast
import datetime
import operator
import os
import urllib.parse
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.utils import platform

from plyer import tts


APP_TITLE = "JARVIS V2"

# Add a secure backend URL later if you have one.
# Do not put your Gemini API key in this Android app.
BACKEND_URL = os.environ.get("JARVIS_BACKEND_URL", "").strip()


THEMES = {
    "Cyan": {
        "bg": (0.025, 0.045, 0.085, 1),
        "panel": (0.045, 0.075, 0.13, 1),
        "accent": (0.0, 0.85, 1.0, 1),
        "text": (0.92, 0.97, 1.0, 1),
        "muted": (0.55, 0.68, 0.78, 1),
        "bubble": (0.07, 0.15, 0.23, 1),
    },
    "Green": {
        "bg": (0.02, 0.07, 0.055, 1),
        "panel": (0.035, 0.12, 0.09, 1),
        "accent": (0.15, 1.0, 0.55, 1),
        "text": (0.91, 1.0, 0.94, 1),
        "muted": (0.55, 0.75, 0.64, 1),
        "bubble": (0.06, 0.17, 0.12, 1),
    },
    "Purple": {
        "bg": (0.055, 0.03, 0.09, 1),
        "panel": (0.10, 0.055, 0.15, 1),
        "accent": (0.75, 0.40, 1.0, 1),
        "text": (0.97, 0.93, 1.0, 1),
        "muted": (0.72, 0.62, 0.80, 1),
        "bubble": (0.15, 0.08, 0.21, 1),
    },
    "Red": {
        "bg": (0.08, 0.025, 0.035, 1),
        "panel": (0.15, 0.045, 0.06, 1),
        "accent": (1.0, 0.25, 0.30, 1),
        "text": (1.0, 0.93, 0.93, 1),
        "muted": (0.80, 0.60, 0.62, 1),
        "bubble": (0.20, 0.07, 0.09, 1),
    },
}


KV = r"""
#:import dp kivy.metrics.dp

<DarkButton@Button>:
    background_normal: ""
    background_down: ""
    background_color: app.panel_color
    color: app.text_color
    font_size: "14sp"
    size_hint_y: None
    height: dp(44)

<ChatBubble@BoxLayout>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(10)
    spacing: dp(5)

    canvas.before:
        Color:
            rgba: app.bubble_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<RootUI>:
    orientation: "vertical"
    spacing: dp(7)
    padding: dp(10)

    canvas.before:
        Color:
            rgba: app.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(8)

        Label:
            text: "🤖 JARVIS V2"
            bold: True
            font_size: "21sp"
            color: app.accent_color
            halign: "left"
            valign: "middle"
            text_size: self.size

        Button:
            text: "🎨"
            size_hint_x: None
            width: dp(48)
            background_normal: ""
            background_color: app.panel_color
            on_release: app.show_themes()

        Button:
            text: "⋮"
            size_hint_x: None
            width: dp(48)
            background_normal: ""
            background_color: app.panel_color
            on_release: app.show_menu()

    Label:
        text: "YOUR PERSONAL ASSISTANT"
        size_hint_y: None
        height: dp(22)
        font_size: "11sp"
        color: app.muted_color
        halign: "left"
        text_size: self.size

    ScrollView:
        id: chat_scroll
        do_scroll_x: False
        bar_width: dp(3)

        GridLayout:
            id: chat_box
            cols: 1
            spacing: dp(9)
            padding: dp(2)
            size_hint_y: None
            height: self.minimum_height

    Label:
        text: app.status_text
        size_hint_y: None
        height: dp(24)
        font_size: "12sp"
        color: app.accent_color
        halign: "left"
        text_size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(100)
        spacing: dp(6)

        TextInput:
            id: message_input
            hint_text: "Message JARVIS..."
            multiline: True
            background_normal: ""
            background_active: ""
            background_color: app.panel_color
            foreground_color: app.text_color
            hint_text_color: app.muted_color
            cursor_color: app.accent_color
            padding: [dp(10), dp(10), dp(10), dp(10)]
            size_hint_x: 1

        BoxLayout:
            orientation: "vertical"
            size_hint_x: None
            width: dp(58)
            spacing: dp(5)

            Button:
                text: "🎤"
                background_normal: ""
                background_color: app.panel_color
                on_release: app.start_voice()

            Button:
                text: "➤"
                background_normal: ""
                background_color: app.accent_color
                color: 0.02, 0.03, 0.05, 1
                on_release: app.send_message()

    GridLayout:
        cols: 4
        spacing: dp(5)
        size_hint_y: None
        height: dp(98)
        row_default_height: dp(46)
        row_force_default: True

        DarkButton:
            text: "🧮 Calculator"
            on_release: app.show_calculator()

        DarkButton:
            text: "🌐 Web"
            on_release: app.open_web()

        DarkButton:
            text: "📷 Camera"
            on_release: app.open_camera()

        DarkButton:
            text: "📁 Files"
            on_release: app.open_files()

        DarkButton:
            text: "🔊 Voice"
            on_release: app.speak_last()

        DarkButton:
            text: "🎨 Themes"
            on_release: app.show_themes()

        DarkButton:
            text: "⚙️ Settings"
            on_release: app.show_settings()

        DarkButton:
            text: "🗑️ Clear"
            on_release: app.clear_chat()
"""


class SafeCalculator:
    """Evaluate basic arithmetic without executing arbitrary Python."""

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    @classmethod
    def evaluate_node(cls, node):
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.Num):
            return node.n

        if isinstance(node, ast.BinOp):
            left = cls.evaluate_node(node.left)
            right = cls.evaluate_node(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Exponent is too large.")

            operation = cls.OPERATORS.get(type(node.op))
            if operation is None:
                raise ValueError("Operator not allowed.")

            result = operation(left, right)

            if abs(result) > 1e100:
                raise ValueError("Result is too large.")

            return result

        if isinstance(node, ast.UnaryOp):
            operation = cls.OPERATORS.get(type(node.op))
            if operation is None:
                raise ValueError("Operator not allowed.")
            return operation(cls.evaluate_node(node.operand))

        raise ValueError("Invalid calculation.")

    @classmethod
    def calculate(cls, expression):
        tree = ast.parse(expression, mode="eval")
        return cls.evaluate_node(tree.body)


class RootUI(BoxLayout):
    pass


class JarvisApp(App):
    bg_color = THEMES["Cyan"]["bg"]
    panel_color = THEMES["Cyan"]["panel"]
    accent_color = THEMES["Cyan"]["accent"]
    text_color = THEMES["Cyan"]["text"]
    muted_color = THEMES["Cyan"]["muted"]
    bubble_color = THEMES["Cyan"]["bubble"]

    status_text = StringProperty("Ready, Boss.")

    def build(self):
        self.title = APP_TITLE
        self.theme_name = "Cyan"
        self.last_response = "Hello Boss! I am JARVIS V2."
        self.chat_history = []

        Builder.load_string(KV)
        self.root_ui = RootUI()

        Clock.schedule_once(self.show_welcome, 0.4)
        return self.root_ui

    def show_welcome(self, *_):
        self.add_message(
            "JARVIS",
            "నమస్కారం బాస్! నేను JARVIS V2.\n"
            "మీ మెసేజ్ టైప్ చేయండి లేదా 🎤 నొక్కండి."
        )

    def add_message(self, sender, message):
        message = str(message)

        bubble = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(70),
            padding=dp(10),
            spacing=dp(5),
        )

        from kivy.graphics import Color, RoundedRectangle

        with bubble.canvas.before:
            Color(*self.bubble_color)
            bubble.background_rect = RoundedRectangle(
                pos=bubble.pos,
                size=bubble.size,
                radius=[dp(12)],
            )

        def update_rect(instance, *_):
            instance.background_rect.pos = instance.pos
            instance.background_rect.size = instance.size

        bubble.bind(pos=update_rect, size=update_rect)

        title = Label(
            text=sender,
            color=self.accent_color,
            bold=True,
            font_size="12sp",
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            text_size=(None, None),
        )

        body = Label(
            text=message,
            color=self.text_color,
            font_size="15sp",
            size_hint_y=None,
            halign="left",
            valign="middle",
            text_size=(None, None),
        )

        def update_body(instance, *_):
            instance.text_size = (max(dp(100), bubble.width - dp(24)), None)
            instance.texture_update()
            instance.height = max(
                dp(25),
                instance.texture_size[1] + dp(6)
            )

        body.bind(width=update_body, text=update_body)
        Clock.schedule_once(lambda *_: update_body(body), 0)

        bubble.add_widget(title)
        bubble.add_widget(body)

        actions = BoxLayout(
            size_hint_y=None,
            height=dp(32),
            spacing=dp(5),
        )

        copy_button = Button(
            text="Copy",
            size_hint_x=None,
            width=dp(65),
            background_normal="",
            background_color=self.panel_color,
            color=self.text_color,
        )
        copy_button.bind(
            on_release=lambda *_: self.copy_text(message)
        )

        select_button = Button(
            text="Select text",
            size_hint_x=None,
            width=dp(100),
            background_normal="",
            background_color=self.panel_color,
            color=self.text_color,
        )
        select_button.bind(
            on_release=lambda *_: self.show_text_popup(message)
        )

        actions.add_widget(copy_button)
        actions.add_widget(select_button)
        bubble.add_widget(actions)

        bubble.height = (
            dp(20) + body.height + dp(32) + dp(35)
        )

        self.root_ui.ids.chat_box.add_widget(bubble)
        self.chat_history.append((sender, message))

        Clock.schedule_once(self.scroll_to_bottom, 0.15)

    def scroll_to_bottom(self, *_):
        self.root_ui.ids.chat_scroll.scroll_y = 0

    def copy_text(self, text):
        Clipboard.copy(text)
        self.status_text = "Copied to clipboard."

    def show_text_popup(self, text):
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10),
        )

        field = TextInput(
            text=text,
            multiline=True,
            readonly=False,
            size_hint_y=1,
        )

        close_button = Button(
            text="Close",
            size_hint_y=None,
            height=dp(44),
        )

        popup = Popup(
            title="Select or copy text",
            content=layout,
            size_hint=(0.92, 0.75),
        )

        close_button.bind(on_release=popup.dismiss)
        layout.add_widget(field)
        layout.add_widget(close_button)
        popup.open()

    def send_message(self):
        field = self.root_ui.ids.message_input
        message = field.text.strip()

        if not message:
            self.status_text = "Type a message first."
            return

        field.text = ""
        self.add_message("YOU", message)
        self.status_text = "Thinking..."

        Clock.schedule_once(
            lambda dt: self.process_message(message),
            0.1
        )

    def process_message(self, message):
        lowered = message.lower().strip()

        if self.looks_like_calculation(message):
            try:
                result = SafeCalculator.calculate(
                    message.replace(",", "")
                )
                response = f"Answer: {result}"
            except Exception:
                response = self.local_response(message)

        elif any(word in lowered for word in [
            "hello", "hi", "hey", "నమస్కారం", "హాయ్"
        ]):
            response = "Hello Boss! ఎలా సహాయం చేయాలి?"

        elif any(word in lowered for word in [
            "your name", "నీ పేరు", "నీ పేరేంటి"
        ]):
            response = "నా పేరు JARVIS V2, బాస్!"

        elif any(word in lowered for word in [
            "time", "సమయం", "టైమ్"
        ]):
            response = datetime.datetime.now().strftime(
                "ఇప్పుడు సమయం %I:%M %p"
            )

        elif any(word in lowered for word in [
            "date", "today", "తేదీ", "ఈ రోజు"
        ]):
            response = datetime.datetime.now().strftime(
                "ఈ రోజు తేదీ %d-%m-%Y"
            )

        elif any(word in lowered for word in [
            "open youtube", "యూట్యూబ్"
        ]):
            webbrowser.open("https://www.youtube.com")
            response = "YouTube తెరవడానికి ప్రయత్నిస్తున్నాను, బాస్."

        elif any(word in lowered for word in [
            "open google", "గూగుల్"
        ]):
            webbrowser.open("https://www.google.com")
            response = "Google తెరవడానికి ప్రయత్నిస్తున్నాను, బాస్."

        elif BACKEND_URL:
            response = self.ask_backend(message)

        else:
            response = self.local_response(message)

        self.last_response = response
        self.add_message("JARVIS", response)
        self.status_text = "Ready, Boss."

    def looks_like_calculation(self, message):
        allowed = set("0123456789+-*/().% ^")
        cleaned = message.strip()

        if not cleaned or not any(ch.isdigit() for ch in cleaned):
            return False

        return all(ch in allowed for ch in cleaned)

    def local_response(self, message):
        lowered = message.lower()

        if any(word in lowered for word in [
            "help", "సహాయం"
        ]):
            return (
                "బాస్, నేను ఇప్పుడే basic commands చేయగలను.\n"
                "ఉదాహరణలు:\n"
                "• 25 * 4\n"
                "• What time is it?\n"
                "• Open Google\n"
                "• Open YouTube\n\n"
                "సాధారణ AI conversation కోసం backend కనెక్ట్ చేయాలి."
            )

        return (
            "బాస్, ఈ ప్రశ్నకు సమాధానం ఇవ్వడానికి నాకు ఇంకా "
            "AI backend కనెక్ట్ కాలేదు.\n\n"
            "ప్రస్తుతం Calculator, Time, Date, Web Search "
            "వంటి basic features ఉపయోగించవచ్చు."
        )

    def ask_backend(self, message):
        # This runs only when a backend URL has been configured.
        # The backend must accept POST JSON: {"message": "..."}
        # and return JSON containing {"response": "..."}.
        try:
            import json
            import requests

            result = requests.post(
                BACKEND_URL,
                json={"message": message},
                timeout=25,
            )
            result.raise_for_status()
            data = result.json()

            answer = data.get("response", "")
            if answer:
                return str(answer)

            return "Backend నుంచి సరైన సమాధానం రాలేదు."

        except Exception:
            return (
                "AI backend కనెక్షన్‌లో సమస్య వచ్చింది. "
                "ఇంటర్నెట్ లేదా backend settings చెక్ చేయండి."
            )

    def speak_text(self, text):
        try:
            tts.speak(text)
            self.status_text = "Speaking..."
        except Exception:
            self.status_text = "Text-to-Speech is unavailable."

    def speak_last(self):
        if self.last_response:
            self.speak_text(self.last_response)
        else:
            self.status_text = "No response to speak."

    def start_voice(self):
        if platform != "android":
            self.show_info(
                "Voice",
                "Voice recognition ఈ Android APKలో ఉపయోగించండి."
            )
            return

        try:
            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )
            Intent = autoclass("android.content.Intent")
            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

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
                "మాట్లాడండి బాస్..."
            )

            activity = PythonActivity.mActivity
            activity.startActivityForResult(intent, 1234)

            self.status_text = "Listening..."

        except Exception as error:
            self.show_info(
                "Voice error",
                "Voice Recognition తెరవలేకపోయాను.\n"
                + str(error)
            )

    def on_activity_result(
        self, request_code, result_code, data
    ):
        if request_code == 1234 and data is not None:
            try:
                from jnius import autoclass

                Activity = autoclass("android.app.Activity")
                RecognizerIntent = autoclass(
                    "android.speech.RecognizerIntent"
                )

                if result_code != Activity.RESULT_OK:
                    self.status_text = "Voice input cancelled."
                    return

                results = data.getStringArrayListExtra(
                    RecognizerIntent.EXTRA_RESULTS
                )

                if results is not None and results.size() > 0:
                    spoken_text = str(results.get(0))
                    self.root_ui.ids.message_input.text = spoken_text
                    self.send_message()

            except Exception as error:
                self.show_info(
                    "Voice error",
                    str(error)
                )

    def show_themes(self):
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10),
        )

        popup = Popup(
            title="Choose JARVIS Theme",
            content=layout,
            size_hint=(0.8, 0.55),
        )

        for name in THEMES:
            button = Button(
                text=name,
                size_hint_y=None,
                height=dp(45),
                background_normal="",
                background_color=THEMES[name]["accent"],
                color=(0.02, 0.03, 0.05, 1),
