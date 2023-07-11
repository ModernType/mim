from kivy.properties import ObjectProperty, ListProperty
from kivy.factory import Factory
from threading import Thread
from kivy.clock import Clock
from kivymd.uix.dialog import MDDialog
from icrawler.builtin import GoogleImageCrawler
from PIL import Image
from ui.common import ImageButton
import os
import shutil
from path_n_data import load_kv, res_path, edit_scr
from translation import translate
import logging

load_kv("web_icon")

tmp = "tmp" # os.path.join(os.path.abspath("."), "tmp")


def washer(*args):
    shutil.rmtree(tmp, ignore_errors=True)


class SearchingIcons(Factory.MDProgressBar):
    installer = ObjectProperty()
    imgs = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "indeterminate"
        self.start()
        self.bind(imgs=self.found)
        self.is_canceled = False
        def find():
            try:
                crawler = GoogleImageCrawler(storage={"root_dir": tmp})
                crawler.crawl(self.installer.alias + " icon", max_num=9, overwrite=True)
                if self.is_canceled:
                    shutil.rmtree(tmp, ignore_errors=True)
                    return
                self.imgs = os.listdir(tmp)
            except Exception as ex:
                logging.warning(f"{ex}")
                self.parent.parent.parent.dismiss()
        self.finder = Thread(target=find, daemon=True).start()

    def cancel(self, *args):
        self.is_canceled = True

    def found(self, inst, val):
        Clock.schedule_once(self.at_found)

    def at_found(self, *args):
        if not self.is_canceled:
            MDDialog(
                title=translate("Choose Icon"),
                type="custom",
                content_cls=WebIconChoose(installer=self.installer, imgs=self.imgs),
                on_dismiss=washer
            ).open()
        self.parent.parent.parent.dismiss()


class WebIconChoose(Factory.MDGridLayout):
    installer = ObjectProperty()
    imgs = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        def but(inst):
            ico = Image.open(inst.source)
            form = inst.source.split(".")[-1]
            ico.resize((64, 64))
            if "_new" in self.installer.icon:
                path = f"MIM/.core/{self.installer.alias}.{form}"
            else:
                path = f"MIM/.core/{self.installer.alias}_new.{form}"
            ico.save(path)
            self.installer.icon = path
            edit_scr().ids.icon.source = path
            self.parent.parent.parent.dismiss()

        self.clear_widgets()
        for i in self.imgs:
            self.add_widget(ImageButton(source="tmp/" + i, on_release=but))
