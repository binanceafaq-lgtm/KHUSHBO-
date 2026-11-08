import threading
import requests
import re
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

PINK = (1, 0.12, 0.46, 1)
BLACK = (0.035, 0.025, 0.045, 1)
WHITE = (1, 0.94, 0.97, 1)

Window.clearcolor = BLACK
Window.softinput_mode = "below_target"

HEADERS = {"User-Agent": "KHUSHBO-AFAQ/1.0"}

try:
    from kivy.utils import platform
except Exception:
    platform = "unknown"

# Android native features
ANDROID = platform == "android"

if ANDROID:
    from jnius import autoclass
    from android import activity
    from android.runnable import run_on_ui_thread

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    RecognizerIntent = autoclass(
        "android.speech.RecognizerIntent"
    )
    CameraManager = autoclass(
        "android.hardware.camera2.CameraManager"
    )
    Context = autoclass("android.content.Context")
    IntentFilter = autoclass("android.content.IntentFilter")
    BatteryManager = autoclass("android.os.BatteryManager")


def internet_ok():
    try:
        requests.get(
            "https://www.google.com",
            timeout=6,
            headers=HEADERS
        )
        return True
    except Exception:
        return False


def weather_lahore():
    try:
        r = requests.get(
            "https://wttr.in/Lahore?format=3",
            timeout=12,
            headers=HEADERS
        )
        r.raise_for_status()
        return "Lahore ka mausam: " + r.text.strip()
    except Exception:
        return None


def wikipedia_search(query):
    try:
        r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json"
            },
            timeout=12,
            headers=HEADERS
        )
        r.raise_for_status()
        results = r.json()["query"]["search"]

        if not results:
            return None

        title = results[0]["title"]

        summary = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + requests.utils.quote(title.replace(" ", "_")),
            timeout=12,
            headers=HEADERS
        )
        summary.raise_for_status()

        return summary.json().get("extract", "")[:1200]

    except Exception:
        return None


def duck_search(query):
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1
            },
            timeout=12,
            headers=HEADERS
        )
        r.raise_for_status()
        data = r.json()

        answer = data.get("AbstractText", "")
        if answer:
            return answer[:1200]

        answer = data.get("Answer", "")
        if answer:
            return answer[:1200]

        for item in data.get("RelatedTopics", []):
            if isinstance(item, dict) and item.get("Text"):
                return item["Text"][:1200]

        return None

    except Exception:
        return None


class KhushboApp(App):

    def build(self):
        self.title = "KHUSHBO"
        self.torch_on = False
        self.listening = False
        self.request_code = 1234
        self.mic_animation = None

        if ANDROID:
            activity.bind(
                on_activity_result=self.on_activity_result
            )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )

        title = Label(
            text="[b][color=ff287c]KHUSHBO[/color][/b]",
            markup=True,
            font_size="34sp",
            size_hint_y=None,
            height=dp(65)
        )
        root.add_widget(title)

        subtitle = Label(
            text="[color=ff9cbd]YOUR LOVELY AI ASSISTANT[/color]",
            markup=True,
            font_size="11sp",
            size_hint_y=None,
            height=dp(25)
        )
        root.add_widget(subtitle)

        self.mic = Button(
            text="[b]MIC[/b]\n[color=ffb0cb]BOLO AFAQ[/color]",
            markup=True,
            font_size="23sp",
            size_hint=(None, None),
            size=(dp(145), dp(145)),
            pos_hint={"center_x": 0.5},
            background_normal="",
            background_color=(0.36, 0.035, 0.15, 1)
        )
        self.mic.bind(on_press=self.start_listening)
        root.add_widget(self.mic)

        self.scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(4)
        )

        self.chat = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=dp(10)
        )
        self.chat.bind(
            minimum_height=self.chat.setter("height")
        )
        self.scroll.add_widget(self.chat)
        root.add_widget(self.scroll)

        self.input = TextInput(
            hint_text="AFAQ, apna message likho...",
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            font_size="16sp",
            foreground_color=WHITE,
            hint_text_color=(0.8, 0.5, 0.65, 1),
            background_color=(0.13, 0.07, 0.12, 1),
            cursor_color=PINK,
            padding=[dp(12), dp(12)]
        )
        self.input.bind(
            on_text_validate=self.send_message
        )
        root.add_widget(self.input)

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        send = Button(
            text="BHEJO",
            background_normal="",
            background_color=PINK,
            bold=True
        )
        send.bind(on_press=self.send_message)
        buttons.add_widget(send)

        mic_button = Button(
            text="MIC BOLO",
            background_normal="",
            background_color=(0.36, 0.035, 0.15, 1),
            bold=True
        )
        mic_button.bind(on_press=self.start_listening)
        buttons.add_widget(mic_button)

        root.add_widget(buttons)

        self.add_message(
            "KHUSHBO",
            "Assalam-o-Alaikum AFAQ! ❤️ Main tumhari KHUSHBO hoon. Batao jaan, kya karna hai?"
        )

        return root

    def add_message(self, sender, message):
        color = "ff4b91" if sender == "KHUSHBO" else "ffffff"

        label = Label(
            text=f"[b][color={color}]{sender}:[/color][/b] {message}",
            markup=True,
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size="14sp"
        )

        label.bind(
            width=lambda obj, value: setattr(
                obj, "text_size", (value, None)
            )
        )
        label.bind(
            texture_size=lambda obj, value: setattr(
                obj, "height", value[1] + dp(15)
            )
        )

        self.chat.add_widget(label)

        Clock.schedule_once(
            lambda dt: setattr(self.scroll, "scroll_y", 0),
            0.1
        )

    def reply(self, message, voice=True):
        self.add_message("KHUSHBO", message)
        if voice:
            self.speak(message)

    def speak(self, message):
        if not ANDROID:
            return

        try:
            PythonActivity.mActivity.runOnUiThread(
                lambda: self.android_speak(message)
            )
        except Exception:
            pass

    def android_speak(self, message):
        try:
            TextToSpeech = autoclass(
                "android.speech.tts.TextToSpeech"
            )
            Locale = autoclass("java.util.Locale")

            if not hasattr(self, "tts"):
                self.tts = TextToSpeech(
                    PythonActivity.mActivity, None
                )
                self.tts.setLanguage(Locale("ur", "PK"))

            self.tts.speak(
                message,
                0,
                None,
                "khushbo"
            )
        except Exception:
            pass

    def send_message(self, instance):
        query = self.input.text.strip()

        if not query:
            return

        self.input.text = ""
        self.add_message("AFAQ", query)

        threading.Thread(
            target=self.process,
            args=(query,),
            daemon=True
        ).start()

    def process(self, query):
        q = query.lower().strip()

        def answer(msg):
            Clock.schedule_once(
                lambda dt: self.reply(msg)
            )

        if any(x in q for x in ["salam", "assalam", "السلام"]):
            answer(
                "Wa Alaikum Assalam AFAQ! ❤️ Kaise ho jaan?"
            )
            return

        if "joke" in q or "mazak" in q:
            answer(
                "AFAQ, teacher ne poocha homework kahan hai? "
                "Student bola: Sir, homework online hai aur internet offline! 😂"
            )
            return

        if any(x in q for x in ["bye", "allah hafiz", "khuda hafiz"]):
            answer("Allah Hafiz AFAQ! ❤️ Apna khayal rakhna.")
            return

        if any(x in q for x in ["time", "waqt", "kitne baj"]):
            answer(
                "AFAQ, abhi waqt hai "
                + datetime.now().strftime("%I:%M %p")
            )
            return

        if "battery" in q or "charge" in q:
            answer(self.battery_status())
            return

        if any(x in q for x in ["torch on", "flash on", "torch chalao"]):
            answer(self.set_torch(True))
            return

        if any(x in q for x in ["torch off", "flash off", "torch band"]):
            answer(self.set_torch(False))
            return

        apps = {
            "youtube": "com.google.android.youtube",
            "whatsapp": "com.whatsapp",
            "tiktok": "com.zhiliaoapp.musically"
        }

        for name, package in apps.items():
            if name in q:
                answer(self.open_app(package, name))
                return

        if "camera" in q or "camra" in q:
            answer(self.open_camera())
            return

        if "weather" in q or "mausam" in q:
            if not internet_ok():
                answer("AFAQ, Internet nahi chal raha.")
                return

            result = weather_lahore()
            answer(
                result or "AFAQ, mausam ki information nahi mili."
            )
            return

        if not internet_ok():
            answer("AFAQ, Internet nahi chal raha.")
            return

        result = wikipedia_search(query)

        if not result:
            result = duck_search(query)

        if result:
            answer(result)
        else:
            answer(
                "AFAQ, mujhe iska jawab nahi mila. "
                "Koi doosra sawal poochho jaan."
            )

    def battery_status(self):
        if not ANDROID:
            return "AFAQ, battery status APK mein hi available hoga."

        try:
            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )
            IntentFilter = autoclass(
                "android.content.IntentFilter"
            )
            Intent = autoclass("android.content.Intent")

            context = PythonActivity.mActivity
            battery = context.registerReceiver(
                None,
                IntentFilter(Intent.ACTION_BATTERY_CHANGED)
            )

            level = battery.getIntExtra("level", -1)
            scale = battery.getIntExtra("scale", 100)

            percentage = int(level * 100 / scale)

            return (
                "AFAQ, tumhare mobile ki battery "
                + str(percentage) + " percent hai."
            )
        except Exception:
            return "AFAQ, battery information nahi mil saki."

    def set_torch(self, enabled):
        if not ANDROID:
            return "AFAQ, torch ke liye Android APK zaroori hai."

        try:
            context = PythonActivity.mActivity
            manager = context.getSystemService(
                Context.CAMERA_SERVICE
            )

            ids = manager.getCameraIdList()
            camera_id = None

            for cid in ids:
                chars = manager.getCameraCharacteristics(cid)
                key = autoclass(
                    "android.hardware.camera2.CameraCharacteristics"
                ).FLASH_INFO_AVAILABLE

                if chars.get(key):
                    camera_id = cid
                    break

            if camera_id is None:
                return "AFAQ, torch available nahi hai."

            manager.setTorchMode(camera_id, enabled)
            self.torch_on = enabled

            return (
                "AFAQ, torch on kar di hai. ❤️"
                if enabled else
                "AFAQ, torch off kar di hai. ❤️"
            )

        except Exception:
            return "AFAQ, torch control nahi ho saka. Permission check karo."

    def open_app(self, package, name):
        if not ANDROID:
            return "AFAQ, apps kholne ke liye Android APK chahiye."

        try:
            context = PythonActivity.mActivity
            intent = context.getPackageManager().getLaunchIntentForPackage(
                package
            )

            if intent is None:
                return "AFAQ, " + name + " install nahi hai."

            context.startActivity(intent)
            return "AFAQ, " + name + " khol rahi hoon. ❤️"

        except Exception:
            return "AFAQ, " + name + " nahi khul saka."

    def open_camera(self):
        if not ANDROID:
            return "AFAQ, camera Android APK mein chalega."

        try:
            context = PythonActivity.mActivity
            Intent = autoclass("android.content.Intent")
            intent = Intent(
                "android.media.action.IMAGE_CAPTURE"
            )
            context.startActivity(intent)
            return "AFAQ, camera khol rahi hoon. ❤️"
        except Exception:
            return "AFAQ, camera nahi khul saka."

    def start_listening(self, instance):
        if not ANDROID:
            self.reply("AFAQ, voice recognition Android APK mein chalegi.")
            return

        if self.listening:
            return

        self.listening = True
        self.mic.text = "[b]SUN RAHI HOON[/b]"
        self.mic_animation = (
            Animation(
                background_color=(0.9, 0.02, 0.25, 1),
                duration=0.5
            ) + Animation(
                background_color=(0.36, 0.035, 0.15, 1),
                duration=0.5
            )
        )
        self.mic_animation.repeat = True
        self.mic_animation.start(self.mic)

        try:
            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "ur-PK"
            )
            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT,
                "AFAQ, KHUSHBO se baat karo"
            )

            PythonActivity.mActivity.startActivityForResult(
                intent, self.request_code
            )

        except Exception:
            self.stop_listening()
            self.reply("AFAQ, voice service available nahi hai.")

    def on_activity_result(self, request_code, result_code, intent):
        if request_code != self.request_code:
            return

        self.stop_listening()

        if intent is None:
            self.reply("AFAQ, awaaz samajh nahi aayi.")
            return

        try:
            results = intent.getStringArrayListExtra(
                RecognizerIntent.EXTRA_RESULTS
            )

            if results and results.size() > 0:
                query = str(results.get(0))
                self.input.text = query
                self.send_message(None)
            else:
                self.reply("AFAQ, dobara bolo jaan.")

        except Exception:
            self.reply("AFAQ, voice samajhne mein masla hua.")

    def stop_listening(self):
        self.listening = False

        if self.mic_animation:
            self.mic_animation.cancel(self.mic)

        self.mic.background_color = (0.36, 0.035, 0.15, 1)
        self.mic.text = "[b]MIC[/b]\n[color=ffb0cb]BOLO AFAQ[/color]"


if __name__ == "__main__":
    KhushboApp().run()
