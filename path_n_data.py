import os
import sys
from pathlib import Path
from kivymd.app import MDApp
from kivy.lang import Builder
import json

res_path = Path(getattr(sys, "_MEIPASS", os.path.abspath(".")))
core_path = Path(os.path.abspath(".")) / "MIM" / ".core"
app = MDApp.get_running_app

def main_scr():
    return app().sm.children[0]


def edit_scr():
    return main_scr().ids.edit


def load_kv(module_name: str):
    Builder.load_file(str(res_path / "ui" / module_name / (module_name + ".kv")))


def update():
    main_scr().update()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self) -> None:
        self._attrs = []
        try:
            with open(core_path / "settings.json") as file:
                setts = json.load(file)
        except Exception:
            # using default settings if we can't read existing
            setts = {
                "edit_mode": True,
                "lang": 'ua'
            }
        for k, v in setts.items():
            self._attrs.append(k)
            self.__setattr__(k, v)

    def __getitem__(self, key):
        try:
            return self.__getattribute__(key)
        except AttributeError:
            raise KeyError(f"Unknown key. Use on of {self._attrs}")
    
    def __setitem__(self, key, value):
        return self.__setattr__(key, value)
    
    def save(self):
        setts = {}
        for k in self._attrs:
            setts[k] = self[k]
        
        print(f"Saving config: {setts}")

        with open(core_path / "settings.json", 'w') as file:
            json.dump(setts, file)
