from kivy.app import App
from kivy.uix.label import Label


class JarvisApp(App):

    def build(self):
        return Label(
            text="Hello! Jarvis is Ready.",
            font_size="24sp"
        )


if __name__ == "__main__":
    JarvisApp().run()