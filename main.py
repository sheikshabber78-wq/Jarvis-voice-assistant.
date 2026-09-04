import ast
from datetime import datetime
import operator
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from plyer import tts

# ============================================================
# ANDROID / PYJNIUS
# ============================================================

HAS_ANDROID = False

try:
    from android.permissions import Permission, request_permissions
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    RecognizerIntent = autoclass("android.speech.RecognizerIntent")

    HAS_ANDROID = True

except Exception as e:
    print("Android/Pyjnius unavailable:", e)


# ============================================================
# SAFE CALCULATOR
# ============================================================


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

            # Prevent extremely large powers
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError()

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):

            operation = cls.OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError()

            return operation(cls._eval(node.operand))

        raise ValueError()


# ============================================================
# KIVY UI
# ============================================================

KV = """
<JARVISUI>:
    orientation: "vertical"
    padding: 15
    spacing: 10

    Label:
        text: "🤖 JARVIS V1"
        font_size: "28sp"
        bold: True
        size_hint_y: None
        height: 55
        color: 0, 0.7, 1, 1

    Label:
        id: status
        text: "సిద్ధంగా ఉన్నాను, బాస్!"
        font_size: "16sp"
        size_hint_y: None
        height: 35

    TextInput:
        id: output
        text: "నమస్కారం బాస్! నేను JARVIS V1."
        readonly: True
        multiline: True
        font_size: "18sp"

    TextInput:
        id: command
        hint_text: "కమాండ్ లేదా లెక్కలు టైప్ చేయండి..."
        multiline: False
        size_hint_y: None
        height: 55
        on_text_validate: root.ask()

    Button:
        text: "🎤 మాట్లాడండి"
        font_size: "18sp"
        bold: True
        size_hint_y: None
        height: 60
        background_color: 0, 0.6, 0.9, 1
        on_release: root.start_voice()

    Button:
        text: "SEND"
        font_size: "17sp"
        size_hint_y: None
        height: 50
        on_release: root.ask()
"""

Builder.load_string(KV)


# ============================================================
# JARVIS UI LOGIC
# ============================================================


class JARVISUI(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def speak(self, text):
        try:
            tts.speak(text)
        except Exception as e:
            print("TTS ERROR:", e)

    def show(self, text):
        self.ids.output.text += "\n\nJARVIS: " + text
        self.ids.status.text = "JARVIS మాట్లాడుతోంది..."
        self.speak(text)
        Clock.schedule_once(self.ready, 1)

    def ready(self, dt):
        self.ids.status.text = "సిద్ధంగా ఉన్నాను, బాస్!"

    def start_voice(self):
        if not HAS_ANDROID:
            self.ids.status.text = "Desktop Mode"
            return

        try:
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "te-IN")
            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT, "మాట్లాడండి బాస్..."
            )

            current_activity = PythonActivity.mActivity
            current_activity.startActivityForResult(intent, 100)
            self.ids.status.text = "వింటున్నాను..."
        except Exception as e:
            self.ids.status.text = "Voice Error"
            print("Voice Error:", e)

    def ask(self):
        text = self.ids.command.text.strip()
        if not text:
            return

        self.ids.output.text += f"\n\nమీరు: {text}"
        response = self.handle_command(text)
        self.show(response)
        self.ids.command.text = ""

    def handle_command(self, text):
        q = text.lower().strip()

        # Greetings
        if any(
            w in q for w in ["హాయ్", "హలో", "నమస్కారం", "hi", "hello", "hey"]
        ):
            return "నమస్కారం బాస్! నేను మీకు ఎలా సహాయపడగలను?"

        # Time
        if "సమయం" in q or "time" in q:
            return "ప్రస్తుత సమయం " + datetime.now().strftime("%I:%M %p")

        # Date
        if "తేదీ" in q or "date" in q:
            return "ఈరోజు తేదీ " + datetime.now().strftime("%d-%m-%Y")

        # YouTube
        if "యూట్యూబ్" in q or "youtube" in q:
            webbrowser.open("https://www.youtube.com")
            return "యూట్యూబ్ ఓపెన్ చేస్తున్నాను."

        # Google
        if "గూగుల్" in q or "google" in q:
            webbrowser.open("https://www.google.com")
            return "గూగుల్ ఓపెన్ చేస్తున్నాను."

        # Safe Calculator
        calc_result = SafeCalculator.calculate(q)
        if calc_result is not None:
            return f"సమాధానం: {calc_result}"

        return "సారీ బాస్, ఈ కమాండ్ నాకు అర్థం కాలేదు."


# ============================================================
# MAIN APP CLASS
# ============================================================


class JarvisApp(App):

    def build(self):
        self.title = "JARVIS V1"
        return JARVISUI()

    def on_start(self):
        if HAS_ANDROID:

            def get_permissions(dt):
                request_permissions(
                    [Permission.RECORD_AUDIO, Permission.INTERNET]
                )

            Clock.schedule_once(get_permissions, 1)


if __name__ == "__main__":
    JarvisApp().run()
