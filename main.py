
import ast
import operator
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout


THEMES = {
    "Cyan": {
        "bg": (0.015, 0.035, 0.07, 1),
        "panel": (0.035, 0.085, 0.14, 1),
        "accent": (0.05, 0.82, 1, 1),
        "text": (0.92, 0.97, 1, 1),
    },
    "Green": {
        "bg": (0.015, 0.055, 0.045, 1),
        "panel": (0.035, 0.12, 0.09, 1),
        "accent": (0.18, 0.95, 0.55, 1),
        "text": (0.91, 1, 0.94, 1),
    },
    "Purple": {
        "bg": (0.05, 0.02, 0.09, 1),
        "panel": (0.12, 0.055, 0.18, 1),
        "accent": (0.72, 0.36, 1, 1),
        "text": (0.98, 0.94, 1, 1),
    },
    "Red": {
        "bg": (0.075, 0.02, 0.035, 1),
        "panel": (0.15, 0.045, 0.065, 1),
        "accent": (1, 0.25, 0.34, 1),
        "text": (1, 0.94, 0.95, 1),
    },
}

BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def calculate(expression):
    if not expression or len(expression) > 100:
        raise ValueError("Invalid calculation")

    tree = ast.parse(expression.replace("^", "**"), mode="eval")

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPS:
            left = visit(node.left)
            right = visit(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Power too large")

            result = BINARY_OPS[type(node.op)](left, right)

            if not isinstance(result, (int, float)):
                raise ValueError("Invalid result")
            if abs(result) > 1e100:
                raise ValueError("Result too large")

            return result

        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
            return UNARY_OPS[type(node.op)](visit(node.operand))

        raise ValueError("Unsupported expression")

    return visit(tree.body)


KV = """
<RootUI>:
    orientation: "vertical"
    padding: dp(10)
    spacing: dp(8)

    canvas.before:
        Color:
            rgba: app.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(52)

        Label:
            text: "JARVIS V2"
            bold: True
            font_size: "23sp"
            color: app.text_color

        Button:
            text: "THEME"
            size_hint_x: None
            width: dp(85)
            background_normal: ""
            background_color: app.panel_color
            color: app.accent_color
            on_release: app.next_theme()

    Label:
        text: app.status_text
        size_hint_y: None
        height: dp(28)
        color: app.accent_color

    ScrollView:
        id: chat_scroll
        do_scroll_x: False

        GridLayout:
            id: messages
            cols: 1
            spacing: dp(8)
            padding: dp(4)
            size_hint_y: None
            height: self.minimum_height

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(6)

        TextInput:
            id: user_input
            hint_text: "Type a message..."
            multiline: False
            font_size: "16sp"
            foreground_color: app.text_color
            cursor_color: app.accent_color
            background_normal: ""
            background_active: ""
            background_color: app.panel_color
            on_text_validate: app.send_message()

        Button:
            text: "SEND"
            size_hint_x: None
            width: dp(76)
            background_normal: ""
            background_color: app.accent_color
            color: (0.02, 0.03, 0.05, 1)
            on_release: app.send_message()

    GridLayout:
        cols: 3
        size_hint_y: None
        height: dp(100)
        spacing: dp(6)
        row_default_height: dp(46)
        row_force_default: True

        Button:
            text: "Calculator"
            on_release: app.quick_calculator()
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color

        Button:
            text: "Time"
            on_release: app.quick_time()
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color

        Button:
            text: "Date"
            on_release: app.quick_date()
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color

        Button:
            text: "Clear Chat"
            on_release: app.clear_chat()
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
"""


class RootUI(BoxLayout):
    pass


class JarvisApp(App):
    bg_color = ListProperty(THEMES["Cyan"]["bg"])
    panel_color = ListProperty(THEMES["Cyan"]["panel"])
    accent_color = ListProperty(THEMES["Cyan"]["accent"])
    text_color = ListProperty(THEMES["Cyan"]["text"])
    status_text = StringProperty("Ready, Boss!")

    def build(self):
        self.title = "JARVIS V2"
        self.theme_index = 0
        self.apply_theme()
        Builder.load_string(KV)
        self.root_widget = RootUI()
        Clock.schedule_once(self.welcome, 0.3)
        return self.root_widget

    def apply_theme(self):
        theme = THEMES[list(THEMES.keys())[self.theme_index]]
        self.bg_color = theme["bg"]
        self.panel_color = theme["panel"]
        self.accent_color = theme["accent"]
        self.text_color = theme["text"]

    def next_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        self.apply_theme()
        self.reply("Theme changed successfully.")

    def welcome(self, _dt):
        self.reply("నమస్కారం బాస్! నేను JARVIS V2. ఎలా సహాయం చేయాలి?")

    def add_message(self, who, message):
        label = __import__("kivy.uix.label", fromlist=["Label"]).Label(
            text=f"{who}: {message}",
            size_hint_y=None,
            color=self.text_color,
            halign="left",
            valign="middle",
            font_size="16sp",
        )

        label.bind(
            width=lambda obj, width: setattr(
                obj, "text_size", (max(width - dp(16), 1), None)
            )
        )
        label.bind(
            texture_size=lambda obj, size: setattr(
                obj, "height", size[1] + dp(18)
            )
        )

        self.root_widget.ids.messages.add_widget(label)
        Clock.schedule_once(
            lambda _dt: setattr(
                self.root_widget.ids.chat_scroll, "scroll_y", 0
            ),
            0.1,
        )

    def reply(self, message):
        self.status_text = "Ready, Boss!"
        self.add_message("JARVIS", str(message))

    def send_message(self):
        message = self.root_widget.ids.user_input.text.strip()
        if not message:
            return

        self.root_widget.ids.user_input.text = ""
        self.add_message("YOU", message)
        low = message.lower()

        if low in ("hi", "hello", "hey") or "నమస్కారం" in message:
            self.reply("నమస్కారం బాస్! ఎలా ఉన్నారు?")
            return

        if "your name" in low or "నీ పేరు" in message:
            self.reply("నా పేరు JARVIS V2, బాస్!")
            return

        if "time" in low or "సమయం" in message:
            self.quick_time()
            return

        if "date" in low or "తేదీ" in message:
            self.quick_date()
            return

        try:
            result = calculate(message)
            self.reply(f"సమాధానం: {result}")
            return
        except Exception:
            pass

        self.reply(
            "ఈ బేస్ వెర్షన్‌లో ఈ ప్రశ్నకు సమాధానం అందుబాటులో లేదు, బాస్. "
            "AI కనెక్షన్‌ను తర్వాత జోడిద్దాం."
        )

    def quick_calculator(self):
        self.root_widget.ids.user_input.text = ""
        self.status_text = "ఉదాహరణ: 25 * (4 + 2)"
        self.root_widget.ids.user_input.focus = True

    def quick_time(self):
        self.reply("ఇప్పుడు సమయం: " + datetime.now().strftime("%I:%M %p"))

    def quick_date(self):
        self.reply("ఈ రోజు తేదీ: " + datetime.now().strftime("%d-%m-%Y"))

    def clear_chat(self):
        self.root_widget.ids.messages.clear_widgets()
        self.status_text = "Chat cleared"


if __name__ == "__main__":
    JarvisApp().run()
