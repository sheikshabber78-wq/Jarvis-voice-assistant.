import ast
import json
import operator
import os
import re
import threading
import urllib.request
import webbrowser
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.utils import platform

try:
    from plyer import tts
except Exception:
    tts = None

THEMES = {
    "Cyan":   {"bg": (0.015,.035,.07,1), "panel": (.035,.085,.14,1), "accent": (.05,.82,1,1), "text": (.92,.97,1,1), "muted": (.48,.68,.78,1), "bubble": (.025,.11,.17,1)},
    "Blue":   {"bg": (.02,.025,.09,1), "panel": (.055,.07,.19,1), "accent": (.22,.42,1,1), "text": (.94,.96,1,1), "muted": (.58,.65,.84,1), "bubble": (.07,.09,.23,1)},
    "Green":  {"bg": (.015,.055,.045,1), "panel": (.035,.12,.09,1), "accent": (.18,.95,.55,1), "text": (.91,1,.94,1), "muted": (.5,.76,.63,1), "bubble": (.04,.15,.1,1)},
    "Purple": {"bg": (.05,.02,.09,1), "panel": (.12,.055,.18,1), "accent": (.72,.36,1,1), "text": (.98,.94,1,1), "muted": (.75,.62,.82,1), "bubble": (.16,.07,.23,1)},
    "Red":    {"bg": (.075,.02,.035,1), "panel": (.15,.045,.065,1), "accent": (1,.25,.34,1), "text": (1,.94,.95,1), "muted": (.82,.57,.61,1), "bubble": (.19,.055,.075,1)},
    "Gold":   {"bg": (.07,.045,.01,1), "panel": (.15,.1,.025,1), "accent": (1,.72,.16,1), "text": (1,.97,.88,1), "muted": (.8,.7,.48,1), "bubble": (.18,.12,.03,1)},
}

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class SafeCalculator:
    @classmethod
    def evaluate(cls, expression):
        expression = expression.replace("^", "**").strip()
        if not expression or len(expression) > 100:
            raise ValueError("లెక్కను సరిగా నమోదు చేయండి.")
        tree = ast.parse(expression, mode="eval")
        result = cls._visit(tree.body)
        if type(result) not in (int, float) or abs(result) > 1e100:
            raise ValueError("ఈ ఫలితం అనుమతించబడదు.")
        return result

    @classmethod
    def _visit(cls, node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            left, right = cls._visit(node.left), cls._visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Power limit is 10.")
            return _BIN[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](cls._visit(node.operand))
        raise ValueError("సాధారణ + - * / లెక్కలు మాత్రమే.")


KV = r"""
<RootUI>:
    orientation: "vertical"
    padding: dp(10)
    spacing: dp(7)
    canvas.before:
        Color:
            rgba: app.bg_color
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        Label:
            text: "🤖 JARVIS V2"
            bold: True
            font_size: "22sp"
            color: app.text_color
        Button:
            text: "🎨"
            size_hint_x: None
            width: dp(50)
            background_normal: ""
            background_color: app.panel_color
            color: app.accent_color
            on_release: app.show_themes()
        Button:
            text: "⋮"
            size_hint_x: None
            width: dp(44)
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.show_menu()
    Label:
        text: "YOUR PERSONAL ASSISTANT"
        size_hint_y: None
        height: dp(20)
        font_size: "11sp"
        color: app.muted_color
    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: dp(112)
        canvas.before:
            Color:
                rgba: app.panel_color
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(18)]
        Label:
            text: "◉"
            font_size: "54sp"
            color: app.accent_color
        Label:
            text: app.status_text
            font_size: "14sp"
            color: app.text_color
    ScrollView:
        id: chat_scroll
        do_scroll_x: False
        BoxLayout:
            id: chat_box
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(7)
            padding: dp(2), dp(4)
    Label:
        text: app.notice_text
        size_hint_y: None
        height: dp(20)
        font_size: "11sp"
        color: app.muted_color
    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(5)
        TextInput:
            id: message_input
            hint_text: "Message JARVIS..."
            multiline: False
            font_size: "16sp"
            foreground_color: app.text_color
            hint_text_color: app.muted_color
            cursor_color: app.accent_color
            background_normal: ""
            background_active: ""
            background_color: app.panel_color
            on_text_validate: app.send_message()
        Button:
            text: "🎤"
            size_hint_x: None
            width: dp(48)
            background_normal: ""
            background_color: app.panel_color
            color: app.accent_color
            on_release: app.start_voice()
        Button:
            text: "SEND"
            size_hint_x: None
            width: dp(66)
            background_normal: ""
            background_color: app.accent_color
            color: (0.02,0.03,0.05,1)
            on_release: app.send_message()
    GridLayout:
        cols: 4
        size_hint_y: None
        height: dp(86)
        spacing: dp(5)
        row_default_height: dp(40)
        row_force_default: True
        Button:
            text: "Calculator"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.show_calculator()
        Button:
            text: "Web"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.open_web()
        Button:
            text: "Camera"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.open_camera()
        Button:
            text: "Files"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.open_files()
        Button:
            text: "Voice"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.speak_last()
        Button:
            text: "Settings"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.show_settings()
        Button:
            text: "Copy last"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.copy_last()
        Button:
            text: "Clear"
            background_normal: ""
            background_color: app.panel_color
            color: app.text_color
            on_release: app.clear_chat()
"""


class RootUI(BoxLayout):
    pass


class JarvisApp(App):
    bg_color = ListProperty(THEMES["Cyan"]["bg"])
    panel_color = ListProperty(THEMES["Cyan"]["panel"])
    accent_color = ListProperty(THEMES["Cyan"]["accent"])
    text_color = ListProperty(THEMES["Cyan"]["text"])
    muted_color = ListProperty(THEMES["Cyan"]["muted"])
    bubble_color = ListProperty(THEMES["Cyan"]["bubble"])
    status_text = StringProperty("సిద్ధంగా ఉన్నాను, బాస్!")
    notice_text = StringProperty("తెలుగు లేదా Englishలో టైప్ చేయండి")

    def build(self):
        self.title = "JARVIS V2"
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.settings = JsonStore(os.path.join(self.user_data_dir, "settings.json"))
        self.last_response = "నమస్కారం బాస్! నేను JARVIS V2."
        self.chat_history = []
        self.theme_name = "Cyan"
        self.apply_saved_theme()
        Builder.load_string(KV)
        root = RootUI()
        Clock.schedule_once(lambda _dt: self.show_welcome(), .25)
        return root

    def apply_saved_theme(self):
        try:
            if self.settings.exists("theme"):
                name = self.settings.get("theme").get("name", "Cyan")
                if name in THEMES:
                    self.theme_name = name
                    self.set_theme_colors(THEMES[name])
                elif name == "Custom":
                    self.apply_hex(self.settings.get("theme").get("hex", "#00CCFF"), save=False)
        except Exception:
            self.set_theme_colors(THEMES["Cyan"])

    def set_theme_colors(self, theme):
        self.bg_color = theme["bg"]
        self.panel_color = theme["panel"]
        self.accent_color = theme["accent"]
        self.text_color = theme["text"]
        self.muted_color = theme["muted"]
        self.bubble_color = theme["bubble"]

    def choose_theme(self, name):
        if name not in THEMES:
            return
        self.theme_name = name
        self.set_theme_colors(THEMES[name])
        self.save_theme(name)
        self.notice_text = name + " theme applied"

    def save_theme(self, name, hex_color=""):
        try:
            self.settings.put("theme", name=name, hex=hex_color)
        except Exception:
            pass

    def apply_hex(self, value, save=True):
        raw = value.strip().lstrip("#")
        if not re.fullmatch(r"[0-9a-fA-F]{6}", raw):
            self.notice_text = "HEX format: #00CCFF"
            return False
        rgb = tuple(int(raw[i:i+2], 16)/255 for i in (0, 2, 4))
        self.theme_name = "Custom"
        self.bg_color = (.015,.035,.07,1)
        self.panel_color = (.035,.085,.14,1)
        self.accent_color = (*rgb, 1)
        self.text_color = (.92,.97,1,1)
        self.muted_color = (.48,.68,.78,1)
        self.bubble_color = (.025,.11,.17,1)
        if save:
            self.save_theme("Custom", "#" + raw.upper())
        self.notice_text = "Custom theme applied"
        return True

    def show_welcome(self):
        self.add_message("JARVIS", "నమస్కారం బాస్! నేను JARVIS V2.\nమీరు ఏం చేయాలనుకుంటున్నారు?")

    def add_message(self, who, message):
        card = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(9), spacing=dp(4))
        card.bind(minimum_height=card.setter("height"))
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(rgba=self.bubble_color if who == "JARVIS" else self.panel_color)
            rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda inst, val: setattr(rect, "pos", val),
                  size=lambda inst, val: setattr(rect, "size", val))
        title = Label(text=who, bold=True, color=self.accent_color,
                      size_hint_y=None, height=dp(22), halign="left", valign="middle")
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        body = Label(text=str(message), color=self.text_color, size_hint_y=None,
                     halign="left", valign="top")
        body.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        body.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(8)))
        card.add_widget(title)
        card.add_widget(body)
        copy_btn = Button(text="Copy", size_hint_y=None, height=dp(30),
                          size_hint_x=None, width=dp(68), background_normal="",
                          background_color=self.panel_color, color=self.text_color)
        copy_btn.bind(on_release=lambda *_: self.copy_text(str(message)))
        card.add_widget(copy_btn)
        self.root.ids.chat_box.add_widget(card)
        self.chat_history.append((who, str(message)))
        Clock.schedule_once(lambda _dt: setattr(self.root.ids.chat_scroll, "scroll_y", 0), .1)

    def send_message(self, *_):
        message = self.root.ids.message_input.text.strip()
        if not message:
            return
        self.root.ids.message_input.text = ""
        self.add_message("YOU", message)
        self.status_text = "ఆలోచిస్తున్నాను, బాస్..."
        Clock.schedule_once(lambda _dt: self.process_message(message), 0)

    def process_message(self, message):
        answer = self.local_answer(message)
        if answer is None:
            if os.environ.get("JARVIS_BACKEND_URL", "").strip():
                self.ask_backend(message)
                return
            answer = "ఈ ప్రశ్నకు AI సమాధానాల కోసం JARVIS backend ఇంకా కనెక్ట్ కాలేదు, బాస్."
        self.finish_answer(answer)

    def local_answer(self, message):
        text = message.strip()
        low = text.lower()
        if re.fullmatch(r"[\d\s.+\-*/()%^]+", text) and any(x in text for x in "+-*/%^"):
            try:
                return "సమాధానం: " + str(SafeCalculator.evaluate(text))
            except Exception:
                pass
        if any(x in low for x in ("hello", "hi", "hey jarvis")) or any(x in text for x in ("హలో", "హాయ్", "నమస్కారం")):
            return "నమస్కారం బాస్! చెప్పండి, ఏం సహాయం కావాలి?"
        if "నీ పేరు" in text or "your name" in low or "who are you" in low:
            return "నా పేరు JARVIS V2, బాస్."
        if "time" in low or "సమయం" in text or "టైమ్" in text:
            return "ఇప్పుడు సమయం: " + datetime.now().strftime("%I:%M %p")
        if "date" in low or "తేదీ" in text:
            return "ఈ రోజు తేదీ: " + datetime.now().strftime("%d-%m-%Y")
        if "open youtube" in low or "యూట్యూబ్" in text:
            self.open_url("https://www.youtube.com")
            return "YouTube తెరవడానికి ప్రయత్నిస్తున్నాను, బాస్."
        if "open google" in low or "గూగుల్" in text:
            self.open_url("https://www.google.com")
            return "Google తెరవడానికి ప్రయత్నిస్తున్నాను, బాస్."
        if "search " in low or "వెతుకు" in text or "సెర్చ్" in text:
            query = re.sub(r"^(search|వెతుకు|సెర్చ్)\s*", "", text, flags=re.I).strip()
            if query:
                from urllib.parse import quote
                self.open_url("https://www.google.com/search?q=" + quote(query))
                return query + " కోసం వెబ్‌లో వెతుకుతున్నాను."
        if "change theme" in low or "థీమ్ మార్చు" in text:
            Clock.schedule_once(lambda _dt: self.show_themes(), .1)
            return "పై 🎨 బటన్‌లో మీకు నచ్చిన రంగు ఎంచుకోండి, బాస్."
        return None

    def finish_answer(self, answer):
        self.last_response = str(answer)
        self.add_message("JARVIS", self.last_response)
        self.status_text = "సిద్ధంగా ఉన్నాను, బాస్!"
        self.speak_text(self.last_response)

    def ask_backend(self, message):
        url = os.environ.get("JARVIS_BACKEND_URL", "").strip()
        def work():
            try:
                payload = json.dumps({"message": message}).encode("utf-8")
                req = urllib.request.Request(url, data=payload,
                    headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                answer = data.get("response") or data.get("answer") or "Backend సమాధానం ఇవ్వలేదు."
            except Exception:
                answer = "AI backend‌ను సంప్రదించలేకపోయాను. Internet/backend URL తనిఖీ చేయండి."
            Clock.schedule_once(lambda _dt: self.finish_answer(answer), 0)
        threading.Thread(target=work, daemon=True).start()

    def speak_text(self, text):
        if tts is None:
            self.notice_text = "Text-to-Speech అందుబాటులో లేదు"
            return
        try:
            tts.speak(str(text))
        except Exception:
            self.notice_text = "Voice విఫలమైంది; సమాధానం textలో ఉంది"

    def speak_last(self):
        self.speak_text(self.last_response)

    def start_voice(self):
        if platform != "android":
            self.notice_text = "Voice input Android APKలో మాత్రమే అందుబాటులో ఉంటుంది"
            return
        try:
            from android import activity
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            RI = autoclass("android.speech.RecognizerIntent")
            intent = Intent(RI.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RI.EXTRA_LANGUAGE_MODEL, RI.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RI.EXTRA_LANGUAGE, "te-IN")
            intent.putExtra(RI.EXTRA_PROMPT, "మాట్లాడండి బాస్...")
            activity.bind(on_activity_result=self.voice_result)
            PythonActivity.mActivity.startActivityForResult(intent, 7412)
            self.status_text = "వింటున్నాను, బాస్..."
        except Exception:
            self.notice_text = "మైక్ ప్రారంభం కాలేదు. RECORD_AUDIO permission తనిఖీ చేయండి."

    def voice_result(self, request_code, result_code, intent):
        try:
            if request_code != 7412 or intent is None:
                return
            from jnius import autoclass
            Activity = autoclass("android.app.Activity")
            if result_code == Activity.RESULT_OK:
                results = intent.getStringArrayListExtra("android.speech.extra.RESULTS")
                if results and results.size() > 0:
                    self.root.ids.message_input.text = str(results.get(0))
                    self.send_message()
        except Exception:
            self.notice_text = "Voice result చదవలేకపోయాను"
        finally:
            try:
                from android import activity
                activity.unbind(on_activity_result=self.voice_result)
            except Exception:
                pass
            self.status_text = "సిద్ధంగా ఉన్నాను, బాస్!"

    def show_themes(self):
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        popup = Popup(title="Choose Theme", content=layout, size_hint=(.84, .82))
        for name, theme in THEMES.items():
            btn = Button(text=name, size_hint_y=None, height=dp(42),
                         background_normal="", background_color=theme["accent"],
                         color=(.02,.03,.05,1))
            btn.bind(on_release=lambda _btn, n=name: (self.choose_theme(n), popup.dismiss()))
            layout.add_widget(btn)
        custom = Button(text="Custom HEX color", size_hint_y=None, height=dp(42))
        custom.bind(on_release=lambda *_: self.show_custom_hex())
        layout.add_widget(custom)
        close = Button(text="Close", size_hint_y=None, height=dp(38))
        close.bind(on_release=popup.dismiss)
        layout.add_widget(close)
        popup.open()

    def show_custom_hex(self):
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        entry = TextInput(text="#00CCFF", hint_text="#RRGGBB", multiline=False,
                          size_hint_y=None, height=dp(46))
        layout.add_widget(Label(text="HEX color, for example #00CCFF", size_hint_y=None, height=dp(30)))
        layout.add_widget(entry)
        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        apply_btn, cancel_