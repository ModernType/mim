import pathlib
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from path_n_data import res_path, Config
from kivy.core.window import Window
import shutil


pathlib.Path("MIM/.core").mkdir(parents=True, exist_ok=True)


class App(MDApp):
    title = "Modern Install Manager"
    icon = str(res_path / 'mim_icon.png')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sm = MDScreenManager()

    def build(self):
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = "Orange"

        return self.sm

    def on_start(self):
        Window.minimum_width = 800
        Window.minimum_height = 600
        return super().on_start()

    def on_stop(self):
        shutil.rmtree("tmp", ignore_errors=True)
        Config().save()


APP = App()
