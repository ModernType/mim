from kivymd.uix.screen import MDScreen
from path_n_data import load_kv, Config
from kivymd.uix.menu import MDDropdownMenu
from translation import main_dict, translate
from kivymd.uix.snackbar import Snackbar

load_kv("setts_scr")


class SettingsScreen(MDScreen):
    def open_lang_menu(self):
        if not hasattr(self, "lang_menu"):
            lang_items = [
                {
                    "viewclass": "OneLineListItem",
                    "text": i,
                    "height": 50,
                    "on_release": lambda x=i: self.choose_lang(x)
                }
                for i in main_dict.keys()
            ]
            self.lang_menu = MDDropdownMenu(items=lang_items, caller=self.ids.lang)
        self.lang_menu.open()

    def choose_lang(self, lang):
        conf = Config()
        conf.lang = lang
        Snackbar(text=translate("Reload app to apply changes")).open()
        self.ids.lang.text = lang
        self.lang_menu.dismiss()
    
    def change_edit_mode(self, val):
        Config().edit_mode = val
        Snackbar(text=translate("Reload app to apply changes")).open()
