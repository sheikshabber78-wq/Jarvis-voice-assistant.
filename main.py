import webbrowser
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.clock import Clock
from plyer import tts

# Android వాయిస్ రికగ్నిషన్ కోసం pyjnius (Android API)
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    HAS_ANDROID = True
except Exception:
    HAS_ANDROID = False


KV = """
<JARVISUI>:
    orientation: "vertical"
    padding: 15
    spacing: 10

    Label:
        text: "🤖 JARVIS V1 (తెలుగు)"
        font_size: "28sp"
        size_hint_y: None
        height: 55
        color: 0, 0.7, 1, 1

    Label:
        id: status
        text: "Ready"
        font_size: "16sp"
        size_hint_y: None
        height: 35

    TextInput:
        id: output
        text: "నమస్కారం బాస్! నేను JARVIS. నన్ను ఏదైనా అడగండి."
        readonly: True
        multiline: True
        font_size: "18sp"

    TextInput:
        id: command
        hint_text: "ఇక్కడ టైప్ చేయండి..."
        multiline: False
        size_hint_y: None
        height: 55
        on_text_validate: root.ask()

    Button:
        text: "🎤 తెలుగులో మాట్లాడండి"
        font_size: "18sp"
        size_hint_y: None
        height: 55
        background_color: 0, 0.5, 0.8, 1
        on_release: root.start_voice()

    Button:
        text: "ASK JARVIS"
        font_size: "18sp"
        size_hint_y: None
        height: 55
        on_release: root.ask()

    Button:
        text: "CLEAR CHAT"
        size_hint_y: None
        height: 45
        on_release: root.clear_chat()
"""

Builder.load_string(KV)


class JARVISUI(BoxLayout):

    def speak(self, text):
        try:
            tts.speak(text)
        except Exception:
            pass

    def show(self, text):
        self.ids.output.text += f"\n\nJARVIS: {text}"
        self.speak(text)

    def start_voice(self):
        if HAS_ANDROID:
            try:
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "te-IN")
                intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "మాట్లాడండి బాస్...")
                current_activity = PythonActivity.mActivity
                current_activity.startActivityForResult(intent, 100)
            except Exception:
                self.ids.status.text = "Voice Error"
                self.show("మైక్ ఓపెన్ చేయడంలో సమస్య వచ్చింది.")
        else:
            self.ids.status.text = "వాయిస్ ఇన్ పుట్..."
            self.show("Android ఫోన్‌లో ఈ బటన్ నొక్కితే Google మైక్ ఓపెన్ అవుతుంది బాస్.")

    def ask(self):
        text = self.ids.command.text.strip()

        if not text:
            return

        self.ids.output.text += f"\n\nమీరు: {text}"
        self.ids.status.text = "Processing..."

        response = self.handle_command(text)

        self.show(response)
        self.ids.status.text = "Ready"
        self.ids.command.text = ""

    def handle_command(self, text):
        q = text.lower().strip()

        # Greetings
        if any(w in q for w in ["హాయ్", "హలో", "నమస్కారం", "hi", "hello", "hey"]):
            return "నమస్కారం బాస్! నేను మీకు ఎలా సహాయపడగలను?"

        # Time
        if "సమయం" in q or "టైమ్" in q or "time" in q:
            return "ప్రస్తుత సమయం " + datetime.now().strftime("%I:%M %p")

        # Date
        if "తేదీ" in q or "ఈరోజు" in q or "date" in q or "today" in q:
            return "ఈరోజు తేదీ " + datetime.now().strftime("%d-%m-%Y")

        # YouTube
        if "యూట్యూబ్" in q or "youtube" in q:
            webbrowser.open("https://www.youtube.com")
            return "యూట్యూబ్ ఓపెన్ చేస్తున్నాను బాస్."

        # Google
        if "గూగుల్" in q or "google" in q:
            webbrowser.open("https://www.google.com")
            return "గూగుల్ ఓపెన్ చేస్తున్నాను బాస్."

        # Search
        if q.startswith("search ") or q.startswith("వెతుకు "):
            query = text.replace("search", "").replace("వెతుకు", "").strip()
            if query:
                webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
                return f"{query} కోసం గూగుల్‌లో వెతుకుతున్నాను."

        # Calculator
        if q.startswith("calculate ") or q.startswith("లెక్క "):
            expr = text.replace("calculate", "").replace("లెక్క", "").strip()
            try:
                allowed = "0123456789+-*/(). "
                if not all(c in allowed for c in expr):
                    return "సాధారణ లెక్క మాత్రమే ఇవ్వండి."
                res = eval(expr, {"__builtins__": None}, {})
                return f"సమాధానం {res}"
            except Exception:
                return "ఆ లెక్క చేయలేకపోయాను బాస్."

        # Who are you
        if "నువ్వు ఎవరు" in q or "who are you" in q:
            return "నేను JARVIS V1, మీ పర్సనల్ అసిస్టెంట్‌ని."

        # Help
        if q == "help" or "సహాయం" in q:
            return "మీరు సమయం, తేదీ, యూట్యూబ్, గూగుల్ సెర్చ్ లేదా లెక్కలు అడగవచ్చు."

        return "క్షమించండి బాస్, ఈ కమాండ్ నాకు ఇంకా అర్థం కాలేదు."

    def clear_chat(self):
        self.ids.output.text = "JARVIS: చాట్ క్లియర్ చేయబడింది."
        self.ids.command.text = ""
        self.ids.status.text = "Ready"


class JarvisApp(App):
    def build(self):
        self.title = "JARVIS V1"
        return JARVISUI()


if __name__ == "__main__":
    JarvisApp().run()
