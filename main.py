import ast
from datetime import datetime
import operator
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from plyer import tts

HAS_ANDROID = False

try:
    from android.permissions import Permission, request_permissions
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    RecognizerIntent = autoclass("android.speech.RecognizerIntent")

    HAS_ANDROID = True
except Exception:
    HAS_ANDROID = False


class SafeCalculator:

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
    }

    @classmethod
    def calculate(cls, expression):
        try:
            node = ast.parse(expression, mode="eval").body
            return cls._eval(node)
        except Exception:
            return None

    @classmethod
    def _eval(cls, node):

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError()

        if isinstance(node, ast.BinOp):
            left = cls._eval(node.left)
            right = cls._eval(node.right)
            operation = cls.OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError()

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError()

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):
            operation = cls.OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError()

            return operation(cls._eval(node.operand))

        raise ValueError()


KV = """
<JARVISUI>:
    orientation: "vertical"
    padding: 15
    spacing: 10

    Label:
        text: "JARVIS V1"
        font_size: "26sp"
        bold: True
        size_hint_y: None
        height: 50
        color: 0, 0.7, 1, 1

    Label:
        id: status
        text: "JARVIS READY"
        font_size: "16sp"
        size_hint_y: None
        height: 35

    TextInput:
        id: output
        text: "JARVIS V1 READY"
        readonly: True
        multiline: True
        font_size: "18sp"

    TextInput:
        id: command
        hint_text: "Type command..."
        multiline: False
        size_hint_y: None
        height: 50
        on_text_validate: root.ask()

    Button:
        text: "SPEAK"
        font_size: "18sp"
        bold: True
        size_hint_y: None
        height: 60
        background_color: 0, 0.6, 0.9, 1
        on_release: root.start_voice()

    Button:
        text: "SEND"
        font_size: "17sp"
        bold: True
        size_hint_y: None
        height: 45
        on_release: root.ask()
"""

Builder.load_string(KV)


class JARVISUI(BoxLayout):

    def speak(self, text):
        try:
            tts.speak(str(text))
        except Exception:
            pass

    def show(self, text):
        self.ids.output.text += "\n\nJARVIS: " + str(text)
        self.speak(text)

    # --------------------------------
    # VOICE
    # --------------------------------

    def start_voice(self):
        if not HAS_ANDROID:
            self.ids.status.text = "Android only"
            return

        self.ids.status.text = "Checking permissions..."

        try:
            request_permissions(
                [Permission.RECORD_AUDIO, Permission.INTERNET],
                self.permission_callback,
            )
        except Exception as e:
            self.ids.status.text = "Permission Error"

    def permission_callback(self, permissions, grants):
        try:
            if not all(grants):
                self.ids.status.text = "Permission denied"
                return

            self.start_speech_recognition()
        except Exception:
            self.ids.status.text = "Permission callback error"

    def start_speech_recognition(self):
        try:
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "te-IN")
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "te-IN"
            )
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak now...")

            current_activity = PythonActivity.mActivity
            current_activity.startActivity(intent)
            self.ids.status.text = "Listening..."
        except Exception as e:
            self.ids.status.text = "Google Speech App Missing"
            self.show(
                "ఫోన్‌లో Google Speech Services / Voice Search లేనందున వాయిస్ సపోర్ట్ చేయడం లేదు."
            )

    # --------------------------------
    # TEXT COMMAND
    # --------------------------------

    def ask(self):
        try:
            text = self.ids.command.text.strip()
            if not text:
                return

            self.ids.output.text += "\n\nYOU: " + text
            response = self.handle_command(text)
            self.show(response)
            self.ids.command.text = ""
            self.ids.status.text = "JARVIS READY"
        except Exception:
            self.ids.status.text = "System Error"

    # --------------------------------
    # COMMANDS
    # --------------------------------

    def handle_command(self, text):
        q = text.lower().strip()

        if any(
            word in q
            for word in [
                "hi",
                "hello",
                "hey",
                "హాయ్",
                "హలో",
                "నమస్కారం",
            ]
        ):
            return "Hello Boss. I am JARVIS. How can I help you?"

        if "your name" in q or "name" in q or "నీ పేరు" in q:
            return "My name is JARVIS V1, Boss."

        if "time" in q or "సమయం" in q:
            return "Current time is " + datetime.now().strftime("%I:%M %p")

        if "date" in q or "today" in q or "తేదీ" in q:
            return "Today's date is " + datetime.now().strftime("%d-%m-%Y")

        if "youtube" in q or "యూట్యూబ్" in q:
            try:
                webbrowser.open("https://www.youtube.com")
            except Exception:
                pass
            return "Opening YouTube, Boss."

        if "google" in q or "గూగుల్" in q:
            try:
                webbrowser.open("https://www.google.com")
            except Exception:
                pass
            return "Opening Google, Boss."

        if "help" in q or "సహాయం" in q:
            return (
                "I can understand voice commands, time, date, calculations,"
                " Google and YouTube."
            )

        calc_result = SafeCalculator.calculate(q)
        if calc_result is not None:
            return "Answer: " + str(calc_result)

        return "Sorry Boss, I don't understand that command yet."


class JarvisApp(App):

    def build(self):
        self.title = "JARVIS V1"
        return JARVISUI()


if __name__ == "__main__":
    JarvisApp().run()
