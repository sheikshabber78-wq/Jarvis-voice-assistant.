import ast
import operator
import webbrowser
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from plyer import tts

HAS_ANDROID = False

try:
    from android import activity
    from android.permissions import Permission, request_permissions
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
        height: 50
        on_text_validate: root.ask()

    Button:
        text: "మాట్లాడండి"
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if HAS_ANDROID:
            try:
                activity.bind(
                    on_activity_result=self.on_activity_result
                )
            except Exception:
                pass

    def speak(self, text):

        try:
            tts.speak(str(text))
        except Exception:
            pass

    def show(self, text):

        self.ids.output.text += "\n\nJARVIS: " + str(text)

        self.speak(text)

    def start_voice(self):

        if not HAS_ANDROID:

            self.ids.status.text = "Desktop Mode"

            self.show(
                "వాయిస్ ఫీచర్ Androidలో మాత్రమే పనిచేస్తుంది."
            )

            return

        try:

            request_permissions(
                [Permission.RECORD_AUDIO]
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

            current_activity = PythonActivity.mActivity

            current_activity.startActivityForResult(
                intent,
                1001
            )

            self.ids.status.text = "వింటున్నాను..."

        except Exception:

            self.ids.status.text = "Voice Error"

            self.show(
                "వాయిస్ సిస్టమ్ ప్రారంభం కాలేదు."
            )

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != 1001:
            return

        try:

            if intent is None:
                self.ids.status.text = "ఏమీ వినిపించలేదు."
                return

            results = intent.getStringArrayListExtra(
                RecognizerIntent.EXTRA_RESULTS
            )

            if results is None or results.size() == 0:

                self.ids.status.text = "మళ్లీ మాట్లాడండి."

                return

            text = str(results.get(0))

            self.ids.command.text = text

            self.ids.status.text = "విన్నాను."

            Clock.schedule_once(
                lambda dt: self.ask(),
                0.2
            )

        except Exception:

            self.ids.status.text = "Voice Result Error"

    def ask(self):

        try:

            text = self.ids.command.text.strip()

            if not text:
                return

            self.ids.output.text += (
                "\n\nమీరు: " + text
            )

            response = self.handle_command(text)

            self.show(response)

            self.ids.command.text = ""

            self.ids.status.text = "సిద్ధంగా ఉన్నాను, బాస్!"

        except Exception:

            self.ids.status.text = "System Error"

            self.show(
                "క్షమించండి బాస్, ఒక చిన్న సమస్య వచ్చింది."
            )

    def handle_command(self, text):

        q = text.lower().strip()

        if any(
            word in q
            for word in [
                "హాయ్",
                "హలో",
                "నమస్కారం",
                "hi",
                "hello",
                "hey"
            ]
        ):

            return (
                "నమస్కారం బాస్! "
                "నేను JARVIS. "
                "మీకు ఎలా సహాయపడగలను?"
            )

        if (
            "నీ పేరు" in q
            or "నీ పేరేంటి" in q
            or "your name" in q
        ):

            return "నా పేరు JARVIS V1, బాస్."

        if (
            "సమయం" in q
            or "time" in q
        ):

            return (
                "ప్రస్తుత సమయం "
                + datetime.now().strftime("%I:%M %p")
            )

        if (
            "తేదీ" in q
            or "date" in q
            or "today" in q
        ):

            return (
                "ఈరోజు తేదీ "
                + datetime.now().strftime("%d-%m-%Y")
            )

        if (
            "యూట్యూబ్" in q
            or "youtube" in q
        ):

            try:
                webbrowser.open(
                    "https://www.youtube.com"
                )
            except Exception:
                pass

            return "యూట్యూబ్ ఓపెన్ చేస్తున్నాను, బాస్."

        if (
            "గూగుల్" in q
            or "google" in q
        ):

            try:
                webbrowser.open(
                    "https://www.google.com"
                )
            except Exception:
                pass

            return "గూగుల్ ఓపెన్ చేస్తున్నాను, బాస్."

        if (
            "సహాయం" in q
            or "help" in q
        ):

            return (
                "నేను సమయం, తేదీ, "
                "లెక్కలు, గూగుల్ మరియు "
                "యూట్యూబ్ వంటి కమాండ్లను చేయగలను."
            )

        calc_result = SafeCalculator.calculate(q)

        if calc_result is not None:

            return "సమాధానం: " + str(calc_result)

        return (
            "సారీ బాస్, "
            "ఈ కమాండ్ ప్రస్తుతం నాకు అర్థం కాలేదు."
        )


class JarvisApp(App):

    def build(self):

        self.title = "JARVIS V1"

        return JARVISUI()


if __name__ == "__main__":

    JarvisApp().run()