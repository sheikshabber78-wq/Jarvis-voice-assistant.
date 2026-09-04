import webbrowser
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from plyer import tts


KV = """
<JARVISUI>:
    orientation: "vertical"
    padding: 15
    spacing: 10

    Label:
        text: "JARVIS V1"
        font_size: "30sp"
        bold: True
        size_hint_y: None
        height: "55dp"
        color: 0, 0.7, 1, 1

    Label:
        text: root.status
        font_size: "16sp"
        size_hint_y: None
        height: "35dp"

    TextInput:
        text: root.response
        readonly: True
        multiline: True
        font_size: "17sp"

    TextInput:
        id: command
        hint_text: "తెలుగులో టైప్ చేయండి..."
        multiline: False
        font_size: "18sp"
        size_hint_y: None
        height: "55dp"
        on_text_validate: root.process_command(self.text)

    Button:
        text: "🎤 తెలుగులో మాట్లాడండి"
        font_size: "18sp"
        size_hint_y: None
        height: "60dp"
        background_color: 0, 0.5, 0.8, 1
        on_press: root.start_voice()

    Button:
        text: "ASK JARVIS"
        font_size: "18sp"
        size_hint_y: None
        height: "55dp"
        on_press: root.process_command(command.text)

    Button:
        text: "CLEAR CHAT"
        size_hint_y: None
        height: "45dp"
        on_press: root.clear_chat()
"""


Builder.load_string(KV)


class JARVISUI(BoxLayout):

    status = StringProperty("సిద్ధంగా ఉన్నాను, Boss Abdul Lathif!")
    response = StringProperty(
        "JARVIS: నమస్కారం Boss!\n"
        "నాతో తెలుగులో మాట్లాడండి."
    )

    def speak_telugu(self, text):
        try:
            tts.speak(text)
        except Exception:
            pass

    def start_voice(self):
        self.status = "వాయిస్ ఇన్ పుట్ పద్ధతి..."
        # వాయిస్ ఇన్ పుట్ కోసం టెక్స్ట్ బాక్స్ సజెషన్
        self.response += "\n\nJARVIS: మీ మైక్ ద్వారా టైప్ లేదా మాట్లాడవచ్చు."
        self.speak_telugu("మీరు మాట్లాడవచ్చు బాస్.")

    def process_command(self, command):
        command = command.strip()
        if not command:
            return

        self.ids.command.text = ""
        self.response += "\n\nమీరు: " + command
        answer = self.handle_command(command)
        self.response += "\nJARVIS: " + answer
        self.status = "సిద్ధంగా ఉన్నాను"
        self.speak_telugu(answer)

    def handle_command(self, command):
        text = command.lower().strip()

        # తెలుగు / English greetings
        if (
            "హలో" in text
            or "హాయ్" in text
            or "నమస్కారం" in text
            or text in ["hi", "hello", "hey", "hai"]
        ):
            return "నమస్కారం Boss! నేను మీకు ఎలా సహాయం చేయాలి?"

        # Time
        if "సమయం" in text or "time" in text or "టైమ్" in text:
            return (
                "ప్రస్తుతం సమయం "
                + datetime.now().strftime("%I:%M %p")
            )

        # Date
        if (
            "తేదీ" in text
            or "ఈ రోజు" in text
            or "date" in text
            or "today" in text
        ):
            return (
                "ఈ రోజు తేదీ "
                + datetime.now().strftime("%d-%m-%Y")
            )

        # YouTube
        if "యూట్యూబ్" in text or "youtube" in text:
            webbrowser.open("https://www.youtube.com")
            return "యూట్యూబ్ ఓపెన్ చేస్తున్నాను Boss."

        # Google
        if "గూగుల్" in text or "google" in text:
            webbrowser.open("https://www.google.com")
            return "గూగుల్ ఓపెన్ చేస్తున్నాను Boss."

        # Search
        if (
            text.startswith("search ")
            or text.startswith("వెతుకు ")
            or text.startswith("వెతకండి ")
        ):
            if text.startswith("search "):
                query = command[7:].strip()
            elif text.startswith("వెతుకు "):
                query = command[7:].strip()
            else:
                query = command[8:].strip()

            if query:
                url = (
                    "https://www.google.com/search?q="
                    + query.replace(" ", "+")
                )
                webbrowser.open(url)
                return query + " కోసం గూగుల్‌లో వెతుకుతున్నాను."

        # Calculator
        if (
            text.startswith("calculate ")
            or text.startswith("లెక్క ")
            or text.startswith("calculate")
        ):
            if text.startswith("calculate "):
                expression = command[10:].strip()
            elif text.startswith("లెక్క "):
                expression = command[5:].strip()
            else:
                return "లెక్క చెప్పండి Boss."

            try:
                allowed = "0123456789+-*/(). "
                if not all(char in allowed for char in expression):
                    return "సాధారణ లెక్క మాత్రమే ఇవ్వండి."
                result = eval(expression, {"__builtins__": None}, {})
                return "సమాధానం " + str(result)
            except Exception:
                return "ఆ లెక్కను చేయలేకపోయాను."

        # Who are you
        if (
            "నువ్వు ఎవరు" in text
            or "మీరు ఎవరు" in text
            or "who are you" in text
        ):
            return "నేను JARVIS V1. మీ వ్యక్తిగత Android assistant."

        # Help
        if text == "help" or "సహాయం" in text:
            return (
                "మీరు నన్ను సమయం, తేదీ, యూట్యూబ్/గూగుల్ ఓపెన్ చేయడం లేదా "
                "లెక్కలు అడగవచ్చు."
            )

        # Default response
        return "క్షమించండి బాస్, ఈ కమాండ్ నాకు అర్థం కాలేదు. సహాయం కోసం 'help' లేదా 'సహాయం' అని టైప్ చేయండి."

    def clear_chat(self):
        self.response = (
            "JARVIS: చాట్ క్లియర్ చేయబడింది.\n"
            "నేను మీకు ఎలా సహాయపడగలను?"
        )
        self.ids.command.text = ""
        self.status = "సిద్ధంగా ఉన్నాను"


class JarvisApp(App):
    def build(self):
        self.title = "JARVIS V1"
        return JARVISUI()


if __name__ == "__main__":
    JarvisApp().run()
