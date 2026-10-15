import ast
import operator
import os
import threading
import urllib.request
import urllib.error
import json
import webbrowser

from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout

from plyer import tts


# --------------------------------------------------
# JARVIS SETTINGS
# --------------------------------------------------

APP_NAME = "JARVIS V1"

# Backend URL is required for secure Gemini access.
# Add your real backend URL here after setting it up.
BACKEND_URL = os.environ.get("JARVIS_BACKEND_URL", "").strip()

Window.clearcolor = (0.025, 0.035, 0.07, 1)


# --------------------------------------------------
# SAFE CALCULATOR
# --------------------------------------------------

class SafeCalculator:
    OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    @classmethod
    def calculate(cls, expression):
        try:
            tree = ast.parse(expression, mode="eval")
            result = cls._evaluate(tree.body)

            if isinstance(result, (int, float)):
                if abs(result) > 1e100:
                    return "Result is too large."
                return str(result)

            return "Invalid calculation."

        except ZeroDivisionError:
            return "Cannot divide by zero."
        except Exception:
            return None

    @classmethod
    def _evaluate(cls, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid number")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)

            if op_type not in cls.OPS:
                raise ValueError("Operation not allowed")

            left = cls._evaluate(node.left)
            right = cls._evaluate(node.right)

            if op_type == ast.Pow:
                if abs(right) > 10:
                    raise ValueError("Exponent too large")

            return cls.OPS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)

            if op_type not in cls.OPS:
                raise ValueError("Operation not allowed")

            return cls.OPS[op_type](cls._evaluate(node.operand))

        raise ValueError("Invalid expression")


# --------------------------------------------------
# USER INTERFACE
# --------------------------------------------------

KV = """
<JarvisLayout>:
    orientation: "vertical"
    padding: "16dp"
    spacing: "12dp"

    Label:
        text: "[b]🤖 JARVIS V1[/b]"
        markup: True
        font_size: "28sp"
        size_hint_y: None
        height: "55dp"
        color: 0.1, 0.85, 1, 1

    Label:
        id: status
        text: "సిద్ధంగా ఉన్నాను, బాస్!"
        font_size: "17sp"
        size_hint_y: None
        height: "35dp"
        color: 0.5, 1, 0.8, 1

    TextInput:
        id: conversation
        hint_text: "ఇక్కడ JARVIS సమాధానాలు కనిపిస్తాయి..."
        readonly: True
        multiline: True
        font_size: "16sp"
        background_color: 0.06, 0.09, 0.15, 1
        foreground_color: 1, 1, 1, 1

    TextInput:
        id: command
        hint_text: "కమాండ్ లేదా లెక్కలు టైప్ చేయండి..."
        multiline: False
        size_hint_y: None
        height: "52dp"
        font_size: "17sp"
        on_text_validate: root.send_message()

    BoxLayout:
        size_hint_y: None
        height: "54dp"
        spacing: "8dp"

        Button:
            text: "SEND"
            on_release: root.send_message()

        Button:
            text: "🔊 SPEAK"
            on_release: root.speak_last()

    BoxLayout:
        size_hint_y: None
        height: "54dp"
        spacing: "8dp"

        Button:
            text: "🎤 తెలుగు వాయిస్"
            on_release: root.start_voice()

        Button:
            text: "🌐 వెబ్"
            on_release: root.open_website()

    Button:
        text: "🧹 CLEAR"
        size_hint_y: None
        height: "44dp"
        on_release: root.clear_chat()
"""


# --------------------------------------------------
# JARVIS LOGIC
# --------------------------------------------------

class JarvisLayout(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_reply = "నమస్కారం బాస్! నేను JARVIS V1."
        self.add_message(
            "JARVIS",
            "నమస్కారం బాస్! నేను JARVIS V1."
        )

    def set_status(self, message):
        self.ids.status.text = message

    def add_message(self, speaker, message):
        current = self.ids.conversation.text

        if current:
            current += "\n\n"

        current += f"{speaker}: {message}"
        self.ids.conversation.text = current

        Clock.schedule_once(
            lambda dt: setattr(
                self.ids.conversation,
                "cursor",
                (0, 0)
            ),
            0
        )

    def clear_chat(self):
        self.ids.conversation.text = ""
        self.add_message("JARVIS", "చెప్పండి బాస్!")
        self.set_status("సిద్ధంగా ఉన్నాను, బాస్!")

    def send_message(self):
        message = self.ids.command.text.strip()

        if not message:
            return

        self.ids.command.text = ""
        self.add_message("మీరు", message)
        self.set_status("ఆలోచిస్తున్నాను...")

        threading.Thread(
            target=self.process_message,
            args=(message,),
            daemon=True
        ).start()

    def process_message(self, message):
        # Calculator
        result = SafeCalculator.calculate(message)

        if result is not None:
            self.show_reply(result)
            return

        # Basic offline commands
        lower = message.lower()

        if lower in ("hi", "hello", "హాయ్", "హలో"):
            self.show_reply("నమస్కారం బాస్! ఎలా సహాయం చేయాలి?")
            return

        if "time" in lower or "సమయం" in message:
            result = datetime.now().strftime("%I:%M %p")
            self.show_reply("ప్రస్తుతం సమయం " + result)
            return

        if "date" in lower or "తేదీ" in message:
            result = datetime.now().strftime("%d-%m-%Y")
            self.show_reply("ఈ రోజు తేదీ " + result)
            return

        # Secure backend call
        if not BACKEND_URL:
            self.show_reply(
                "బాస్, Gemini కనెక్షన్ ఇంకా ఏర్పాటు కాలేదు. "
                "సురక్షిత backend URL అవసరం. "
                "ఇప్పటికైతే లెక్కలు, సమయం, తేదీ వంటి "
                "ప్రాథమిక కమాండ్లు మాత్రమే పనిచేస్తాయి."
            )
            return

        try:
            reply = self.ask_backend(message)
            self.show_reply(reply)

        except Exception as error:
            self.show_reply(
                "బాస్, AI కనెక్షన్‌లో సమస్య వచ్చింది. "
                "ఇంటర్నెట్ మరియు backend సెట్టింగులను తనిఖీ చేయండి."
            )

    def ask_backend(self, message):
        payload = json.dumps({
            "message": message,
            "language": "te"
        }).encode("utf-8")

        request = urllib.request.Request(
            BACKEND_URL,
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        reply = data.get("reply", "")

        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("Empty backend reply")

        return reply.strip()

    def show_reply(self, reply):
        Clock.schedule_once(
            lambda dt: self._display_reply(reply)
        )

    def _display_reply(self, reply):
        self.last_reply = reply
        self.add_message("JARVIS", reply)
        self.set_status("సిద్ధంగా ఉన్నాను, బాస్!")

    def speak_last(self):
        if not self.last_reply:
            self.set_status("ముందుగా ఒక సమాధానం పొందండి.")
            return

        try:
            tts.speak(self.last_reply)
        except Exception:
            self.set_status(
                "వాయిస్ అందుబాటులో లేదు. "
                "ఫోన్ Text-to-Speech సెట్టింగులు తనిఖీ చేయండి."
            )

    def start_voice(self):
        if platform != "android":
            self.set_status("వాయిస్ కోసం Android యాప్ ఉపయోగించండి.")
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

            self.set_status(
                "మాట్లాడండి బాస్... ఫోన్‌లో వాయిస్ గుర్తింపు తెరవాలి."
            )

        except Exception:
            self.set_status(
                "వాయిస్ ప్రారంభం కాలేదు. "
                "Android permissions మరియు build సెట్టింగులు తనిఖీ చేయండి."
            )

    def open_website(self):
        webbrowser.open("https://www.google.com")
        self.set_status("Google తెరవడానికి ప్రయత్నిస్తున్నాను...")


# --------------------------------------------------
# ANDROID APP
# --------------------------------------------------

class JarvisApp(App):

    def build(self):
        self.title = APP_NAME
        Builder.load_string(KV)
        return JarvisLayout()


if __name__ == "__main__":
    JarvisApp().run()