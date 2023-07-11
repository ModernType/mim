from path_n_data import load_kv, main_scr
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, ListProperty, OptionProperty
import logging
from updater import Updater
from kivy.animation import Animation
from ui.common import TranRoundFlatIconButton
from kivymd.uix.widget import MDWidget
from kivymd.uix.relativelayout import MDRelativeLayout
from threading import Thread
import requests
from kivy.clock import Clock
from kivymd.uix.snackbar import Snackbar
from translation import translate
from ui.web_icon import SearchingIcons
import os
import shutil
import json
from kivymd.uix.dialog import MDDialog
from tkinter.filedialog import askopenfilename
from execution import check_string

load_kv("edit_inst")


class Checker(MDRelativeLayout):
    """Checker which is used near the update link text field"""
    state = OptionProperty("progress", options=["true", "false", "progress"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(state=self._state_change)

    def success(self):
        self.state = "true"
    
    def fail(self):
        self.state = "false"
    
    def progress(self):
        self.state = "progress"

    def _state_change(self, inst, val):
        match self.state:
            case "progress":
                self.ids.check_icon.opacity = 0
                self.ids.check_spin.opacity = 1
            case "true":
                ico = self.ids.check_icon
                ico.icon = "check-circle"
                ico.text_color = "green"
                ico.opacity = 1
                self.ids.check_spin.opacity = 0
            case "false":
                ico = self.ids.check_icon
                ico.icon = "close-circle"
                ico.text_color = "red"
                self.ids.check_icon.opacity = 1
                self.ids.check_spin.opacity = 0


class EditInstall(MDScreen):
    ins: Updater = ObjectProperty(Updater()) # Later there will be InstallItem instance
    prev = StringProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(ins=self.update_ins)
        self._p_ins = Updater() # placeholder for previsious installer
        self.upd_but = TranRoundFlatIconButton(icon="reload", text="Update", size_hint=(1, 1))
        self.checker = Checker()
        self.link_check = Thread(target=self._check_link, daemon=True)
        Clock.schedule_once(lambda t: self.ids.order.parent.bind(height=self._set_order_height))
        Clock.schedule_once(lambda t: self.ids.update_show.bind(opacity=self._set_order_height))
    
    def _check_link(self):
        if not self.ids.link.text:
            Clock.schedule_once(lambda t: self.ids.link_box.remove_widget(self.checker))
            return
        
        Clock.schedule_once(lambda t: self.checker.progress())
        
        try:
            response = requests.get(self.ids.link.text, stream=True)
        except Exception as ex:
            Clock.schedule_once(lambda t: self.checker.fail())
            Clock.schedule_once(lambda t: Snackbar(text=translate("Connection error")).open())
            try:
                self.ids.but_box.remove_widget(self.upd_but)
            except Exception:
                pass
            return
        
        if not ('content-length' in response.headers):
            Clock.schedule_once(lambda t: self.checker.fail())
            def remove():
                try:
                    self.ids.but_box.remove_widget(self.upd_but)
                except Exception as ex:
                    logging.warning(f"Cannot remove upd_but {ex}")
            Clock.schedule_once(lambda t: remove())
                
        else:
            Clock.schedule_once(lambda t: self.checker.success())
            def add():
                try:
                    self.ids.but_box.add_widget(self.upd_but)
                except Exception as ex:
                    logging.warning(f"Cannot add upd_but {ex}")
            Clock.schedule_once(lambda t: add())

    def _set_order_height(self, *args):
        order = self.ids.order
        upd = self.ids.update_show
        order.height = order.parent.height + (upd.height - upd.height * upd.opacity)

    def check_link(self):
        try:
            self.ids.link_box.add_widget(self.checker)
        except Exception:
            pass
        if not self.link_check.is_alive():
            self.link_check = Thread(target=self._check_link, daemon=True)
            self.link_check.start()

    def update_ins(self, *args):
        try:
            self._p_ins.unbind(progress=self.progress, info=self.info, _is_cancelled=self.on_cancelled)
        except Exception as ex:
            logging.warning(ex)
        self.ids.title.text = self.ins.alias
        self.ids.filename.text = self.ins.path.name
        self.ids.icon.source = self.ins.icon
        self.ids.link.text = self.ins.update_link

        # test for order availability
        try:
            with open(self.ins.path / 'order.txt') as order:
                self.ids.order.text = order.read()
            self.ids.order.opacity = 1
            self._set_order_height()
            self.ids.link.opacity = 0
            self.ids.order.error = False
            self.ids.order.helper_text = translate("Type installator's names each in new line")
        except Exception:
            self.ids.order.text = ""
            self.ids.order.opacity = 0
            self.ids.link.opacity = 1
        
        self.ins.bind(progress=self.progress, info=self.info, _is_cancelled=self.on_cancelled)
        
        if self.ins._is_cancelled:
            self.ids.update_show.opacity = 0
            self.upd_but.unbind(on_release=self.cancel_update)
            self.upd_but.text = "Update"
            self.upd_but.icon = "reload"
            self.upd_but.on_release = self.start_update
        else:
            self.ids.update_show.opacity = 1
            self.upd_but.unbind(on_release=self.start_update)
            self.upd_but.text = "Cancel"
            self.upd_but.icon = "cancel"
            self.upd_but.on_release = self.cancel_update

        if self.ins.update_link:
            self.check_link()
            try:
                self.ids.link_box.add_widget(self.checker)
            except Exception:
                pass
            # try:
            #     self.ids.but_box.add_widget(self.upd_but)
            # except Exception:
            #     pass
        
        try:
            self.ids.but_box.remove_widget(self.upd_but)
        except Exception as ex:
            logging.warning(f"Start deleting of upd_but failed due to {ex}")

        self._p_ins = self.ins
    
    def choose_web_icon(self):
        si = SearchingIcons(installer=self.ins)
        MDDialog(
            title=translate("Searching icons..."),
            type="custom",
            content_cls=si,
            on_dismiss=si.cancel
        ).open()

    def choose_local_icon(self):
        path = askopenfilename(filetypes=[("Icons", ['*.png', '*.jpg', '*.jpeg'])])
        if path:
            if "_new" in path:
                new = os.path.join(os.getcwd(), "MIM", ".core", self.ins.alias + "." + path.split(".")[-1])
            else:
                new = os.path.join(os.getcwd(), "MIM", ".core", self.ins.alias + "_new." + path.split(".")[-1])
            shutil.copy(path, new)
            self.ins.icon = new
            self.ids.icon.source = new
        else:
            Snackbar(text=translate("You must choose an icon")).open()

    def start_update(self, *args):
        logging.info("Trying to start")
        self.ins.start_update()
    
    def cancel_update(self, *args):
        self.ins.cancel_update()

    def on_cancelled(self, inst, val):
        Animation(opacity=int(not val), d=.6).start(self.ids.update_show)
        if val:
            self.upd_but.text = "Update"
            self.upd_but.icon = "reload"
            self.upd_but.on_release = self.start_update
        else:
            self.upd_but.text = "Cancel"
            self.upd_but.icon = "cancel"
            self.upd_but.on_release = self.cancel_update

    def info(self, inst, val):
        if main_scr().ids.sm.current == "edit":
            self.ids.info.text = val

    def progress(self, inst, val):
        if main_scr().ids.sm.current == "edit":
            self.ids.progress.value = val
            self.ids.progress_num.text = f"{int(val)}%"

    def back(self):
        main_scr().ids.sm.current = self.prev
        self.ins.unbind()
    
    def order_edit(self, text):
        try:
            check_string(text)
        except SyntaxError as ex:
            self.ids.order.error = True
            self.ids.order.helper_text = f"{ex}"
        else:
            self.ids.order.error = False
            self.ids.order.helper_text = translate("Type installator's names each in new line or commands")

    def save(self):
        try:
            check_string(self.ids.order.text)
        except SyntaxError as ex:
            logging.warning(f"{ex}")
            self.ids.order.error = True
            self.ids.order.helper_text = f"{ex}"
            return

        dir = self.ins.path.parent

        self.ins.alias = self.ids.title.text
        self.ins.update_link = self.ids.link.text

        with open(dir / "loader.json", 'r') as file:
            all = json.load(file)

        all[self.ins.path.name] = self.ins.dict()
        with open(dir / "loader.json", 'w') as file:
            json.dump(all, file)
        
        if self.ids.order.text:
            with open(self.ins.path / 'order.txt', 'w') as file:
                file.write(self.ids.order.text)

        self.ins.update()
        main_scr().ids.sm.transition.direction = "right"
        main_scr().ids.sm.transition.mode = "pop"
        self.back()
