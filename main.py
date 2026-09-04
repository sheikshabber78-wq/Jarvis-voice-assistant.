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
        hint_text: "Ask JARVIS..."
        multiline: False
        font_size: "18sp"
        size_hint_y: None
        height: "55dp"
        on_text_validate: root.process_command(self.text)

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

    status = StringProperty("Ready to assist, Boss!")
    response = StringProperty(
        "JARVIS: Hello Boss!\\n"
        "How can I help you?"
    )

    def process_command(self, text):

        command = text.strip()

        if not command:
            return

        self.ids.command.text = ""

        self.response += "\\n\\nYou: " + command

        answer = self.handle_command(command)

        self.response += "\\nJARVIS: " + answer

        self.status = "Ready"

        try:
            tts.speak(answer)
        except Exception:
            pass


    def handle_command(self, command):

        text = command.lower().strip()


        # Greeting
        if text in ["hi", "hello", "hey", "hai"]:

            return "Hello Boss! How can I help you?"


        # Time
        if "time" in text:

            return (
                "The current time is "
                + datetime.now().strftime("%I:%M %p")
            )


        # Date
        if "date" in text or "today" in text:

            return (
                "Today's date is "
                + datetime.now().strftime("%d %B %Y")
            )


        # YouTube
        if "open youtube" in text:

            webbrowser.open(
                "https://www.youtube.com"
            )

            return "Opening YouTube."


        # Google
        if "open google" in text:

            webbrowser.open(
                "https://www.google.com"
            )

            return "Opening Google."


        # Search Google
        if text.startswith("search "):

            query = command[7:].strip()

            if query:

                url = (
                    "https://www.google.com/search?q="
                    + query.replace(" ", "+")
                )

                webbrowser.open(url)

                return "Searching Google for " + query


        # Calculator
        if text.startswith("calculate "):

            expression = command[10:].strip()

            try:

                allowed = (
                    "0123456789+-*/(). "
                )

                if not all(
                    char in allowed
                    for char in expression
                ):
                    return "Please use a basic calculation."

                result = eval(
                    expression,
                    {"__builtins__": None},
                    {}
                )

                return "The answer is " + str(result)

            except Exception:

                return "I could not calculate that."


        # Who are you
        if "who are you" in text:

            return (
                "I am JARVIS V1, "
                "your personal assistant."
            )


        # Help
        if text == "help":

            return (
                "You can say: Hello, Time, Date, "
                "Open YouTube, Open Google, "
                "Search followed by a topic, "
                "or Calculate followed by a number."
            )


        # Default response
        return (
            "I can handle basic commands without "
            "an API right now. AI conversation can "
            "be added later when you have an API key."
        )


    def clear_chat(self):

        self.response = (
            "JARVIS: Chat cleared.\\n"
            "How can I help you?"
        )

        self.ids.command.text = ""

        self.status = "Ready"


class JarvisApp(App):

    def build(self):

        self.title = "JARVIS V1"

        return JARVISUI()


if __name__ == "__main__":
    JarvisApp().run()