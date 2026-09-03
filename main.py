from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

class JarvisApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1) # Dark theme background

        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Title Label
        self.title_label = Label(
            text="JARVIS AI", 
            font_size='30sp', 
            bold=True,
            color=(0, 0.8, 1, 1)
        )
        
        # Status Label
        self.status_label = Label(
            text="Welcome Boss Abdul Lathif!\nI am online and ready.", 
            font_size='18sp',
            halign='center'
        )

        # Action Button
        self.listen_btn = Button(
            text="Tap to Speak",
            size_hint=(1, 0.2),
            background_color=(0, 0.6, 0.8, 1),
            font_size='20sp'
        )
        self.listen_btn.bind(on_press=self.start_listening)

        layout.add_widget(self.title_label)
        layout.add_widget(self.status_label)
        layout.add_widget(self.listen_btn)

        return layout

    def start_listening(self, instance):
        self.status_label.text = "Listening... Speak now, Boss!"

if __name__ == "__main__":
    JarvisApp().run()
