from kivy.properties import ObjectProperty, ListProperty, StringProperty, ColorProperty, BooleanProperty, NumericProperty
from fileloader import Folder, load_dirs
from kivymd.uix.boxlayout import MDBoxLayout
from ui.common import TooltipMDIconButton, TranFillRoundFlatButton, MyTransition, TranRoundFlatIconButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from path_n_data import app, load_kv, main_scr, Config, edit_scr, res_path
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
import logging
from kivymd.uix.progressbar import MDProgressBar
from updater import Updater
from kivy.clock import Clock
from kivymd.uix.snackbar import Snackbar
from translation import Translated, translate
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
import json
import os
import shutil
from kivy.core.window import Window
from kivy.uix.screenmanager import CardTransition
from configparser import ConfigParser
from execution import execute_string
from threading import Thread
from time import sleep

load_kv("main_scr")

registered_downloads = dict()


class MainScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = load_dirs()
        for c in categories:
            self.ids.rail.add_but(FolderItem(folder=c))
        if Config().edit_mode:
            self.ids.rail.add_but(NavigationButton(text="Add Folder", icon="folder-plus"))
        Window.bind(on_drop_file=self.on_file_drag)
    
    def on_file_drag(self, inst, filename: bytes, *args):
        filename = filename.decode()
        logging.info(f"{self.name}: Dropped file {filename}")
        if not (os.path.isdir(filename) or filename.endswith(".exe") or filename.endswith(".bat") or filename.endswith(".msi")):
            Snackbar(text=translate("Wrong file type. Should be .exe, .bat file or folder")).open()
        else:
            logging.info(f"Current screen name {self.ids.sm.current}")
            if not self.ids.sm.current or self.ids.sm.current == "setts":
                Snackbar(text=translate("You can drop installers only after folder is choosen")).open()
            else:
                fold = self.ids.sm.get_screen(self.ids.sm.current).folder
                name = filename.split('\\')[-1]
                if os.path.isdir(filename):
                    try:
                        shutil.copytree(filename, f"{fold.path}/{name}")
                    except Exception:
                        pass
                else:
                    try:
                        shutil.copy(filename, f"{fold.path}/{name}")
                    except shutil.SameFileError:
                        pass
                
                self.update()

    def add_new(self):
        pass
        # MDDialog(
        #     title="Add new installer via link",
        #     type="custom",
        #     content_cls=AddNew()
        # ).open()

    def search(self, text=""):
        self.ids.main_menu.search(text)

    def update(self):
        try:
            self.ids.sm.get_screen(self.ids.sm.current).update()
        except Exception as ex:
            logging.error(f"{ex}")

    def rail_choose(self, inst):
        self.ids.sm.current = inst.scr.name

    def transition(self):
        self.manager.transition.direction = 'left'
        self.manager.current = 'settings'


class NavigationButton(ButtonBehavior, MDBoxLayout, Translated):
    icon = StringProperty("folder")
    text = StringProperty("")
    selected = BooleanProperty(False)
    icon_color = ColorProperty(app().theme_cls.primary_color)
    custom_icon_color = BooleanProperty(False)
    custom_text_color = BooleanProperty(False)
    text_color = ColorProperty(app().theme_cls.text_color)
    _select_color = ColorProperty(app().theme_cls.bg_dark)
    _init_x = NumericProperty()
    translatable = ListProperty(["text"])
    # hovered = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        def change_icon(inst, val):
            pass
            self.ids.ico.icon = self.icon
            self.ids.ico.theme_text_color = "Custom" if self.custom_icon_color else "Primary"
            self.ids.ico.text_color = self.icon_color
            
        def change_text(inst, val):
            self.ids.lbl.text = self.text
            self.ids.lbl.theme_text_color = "Custom" if self.custom_text_color else "Primary"
            self.ids.lbl.text_color = self.text_color

        self.bind(
            icon=change_icon,
            icon_color=change_icon,
            custom_icon_color=change_icon
        )
        self.bind(
            text=change_text,
            text_color=change_text,
            custom_text_color=change_text
        )
        self.bind(x=self.setter('_init_x'))
        self.bind(selected=self._on_selected)
        Clock.schedule_once(lambda t: self._on_selected(self, False))
        # Window.bind(mouse_pos=self._on_mousepos)
        # self.bind(hovered=self.on_hover)

    # def _on_mousepos(self, window, pos):
    #     if self.collide_point(*pos):
    #         self.hovered = True
    #     else:
    #         self.hovered = False

    def _on_selected(self, inst, val):
        if val:
            Animation.stop_all(self)
            Animation(_select_color=app().theme_cls.bg_normal, d=.1).start(self)
            self.custom_text_color = True
            self.text_color = app().theme_cls.primary_color
            self.custom_icon_color = True
            self.icon_color = app().theme_cls.primary_color
        else:
            Animation(_select_color=app().theme_cls.bg_dark, d=.2).start(self)
            self.custom_text_color = False
            self.custom_icon_color = False

    def _find_bar(self, parent=None):
        parent = self.parent if parent is None else parent.parent
        if not isinstance(parent, NavigationBar):
            parent = self._find_bar(parent)
        return parent

    def on_press(self):
        if not self.selected:
            Animation(_select_color=app().theme_cls.bg_normal).start(self)
            self._find_bar().on_item_press(self)

    # def on_hover(self, inst, val):
        # if val:
        #     self.custom_text_color = True
        #     self.text_color = app().theme_cls.primary_color
        # else:
        #     if not self.selected:
        #         self.custom_text_color = False

    def on_touch_up(self, touch):
        touch = super().on_touch_up(touch)
        if touch is None and not self.selected:
            Animation.stop_all(self, "_select_color")
            Animation(_select_color=app().theme_cls.bg_dark, d=0.1).start(self)

    def on_release(self):
        self.selected = True
        self._find_bar()._on_item_release(self)

    def deselect(self):
        self.selected = False
    
    def select(self):
        self.selected = True
        Clock.schedule_once(lambda t: self._find_bar()._on_item_release(self))


class IconTextItem(OneLineIconListItem):
    text = StringProperty()
    icon = StringProperty()


class FolderItem(NavigationButton):
    folder: Folder = ObjectProperty(Folder())
    scr: MDScreen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = self.folder.alias
        self.icon = self.folder.icon
        self.scr = MainMenu(name=self.folder.path.name, folder=self.folder)
        def init_scr(t):
            main_scr().ids.sm.add_widget(self.scr)
            self.scr.search()
        Clock.schedule_once(init_scr)
        menu_items = [
            {
                "viewclass": "IconTextItem",
                "text": translate("Rename"),
                "icon": "pencil",
                "height": 50,
                "on_release": self.edit
            },
            {
                "viewclass": "IconTextItem",
                "text": translate("Change icon"),
                "icon": "image-edit",
                "height": 50,
                "on_release": self.change_icon
            },
            {
                "viewclass": "IconTextItem",
                "text": translate("Delete"),
                "icon": "trash-can",
                "height": 50,
                "on_release": self.delete
            }
        ]
        self.menu = MDDropdownMenu(
            caller=self,
            items=menu_items,
            width_mult=3.5
        )
        
        self.lbl = self.ids.lbl
    
    def _apply_edit(self, name):
        self.remove_widget(self.inp)
        self.add_widget(self.lbl)

        if name != self.text:
            with open("MIM/loader.json") as file:
                dirs = json.load(file)
            self.folder.path = self.folder.path.rename(f"MIM/{name}")
            self.folder.alias = name
            dirs[self.folder.path.name] = self.folder.dict()
            with open("MIM/loader.json", 'w') as file:
                json.dump(dirs, file)

            self.scr.name = self.folder.path.name
            self.text = name

            self.scr.reload()

    def edit(self):
        def apply(inst, val=None):
            if not inst.error:
                self._apply_edit(inst.text)
            else:
                self._apply_edit(self.text)
        self.inp = MDTextField(text=self.text,
                               required=True
                              )
        self.remove_widget(self.ids.lbl)
        self.add_widget(self.inp)
        self.inp.focus = True
        self.inp.bind(focus=apply)
        self.menu.dismiss()

    def _choose_icon(self, icon: str):
        with open("MIM/loader.json") as file:
            dirs = json.load(file)
        self.folder.icon = icon
        dirs[self.folder.path.name] = self.folder.dict()
        with open("MIM/loader.json", 'w') as file:
            json.dump(dirs, file)
        self.icon = icon
        self.icon_chooser.dismiss()

    def change_icon(self):
        icons = {'folder-zip', 'folder-image', 'folder-check', 'folder-edit', 'folder-play', 'folder-home', 'folder-marker', 'folder', 'folder-lock-open', 'folder-remove', 'folder-move', 'folder-minus', 'folder-refresh', 'folder-cog', 'folder-multiple-plus', 'folder-arrow-left', 'folder-pound', 'folder-lock', 'folder-arrow-left-right', 'folder-star-multiple', 'folder-settings', 'folder-swap', 'folder-plus', 'folder-account', 'folder-arrow-right', 'folder-google-drive', 'folder-key-network', 'folder-question', 'folder-eye', 'folder-sync', 'folder-off', 'folder-open', 'folder-heart', 'folder-table', 'folder-network', 'folder-upload', 'folder-key', 'folder-music', 'folder-star', 'folder-alert', 'folder-hidden', 'folder-search', 'folder-download', 'folder-multiple-image', 'folder-arrow-up', 'folder-information', 'folder-multiple', 'folder-clock', 'folder-arrow-down', 'folder-wrench', 'folder-file', 'folder-cancel', 'folder-text', 'folder-arrow-up-down'}

        menu_items = [
            {
                "viewclass": "IconTextItem",
                "icon": i,
                "text": i,
                "height": 50,
                "on_release": lambda x=i: self._choose_icon(x)
            }
            for i in icons
        ]

        self.icon_chooser = MDDropdownMenu(
            caller=self,
            items=menu_items,
            width_mult=3
        )
        self.menu.dismiss()
        self.icon_chooser.open()
    
    def delete(self):
        anim = Animation(height=0, opacity=0, d=.5)
        anim.on_complete = lambda x: self._find_bar().ids.scroll.remove_widget(self)
        anim.start(self)
        shutil.rmtree(self.folder.path)
        with open("MIM/loader.json") as file:
            dirs: dict = json.load(file)
        dirs.pop(self.folder.path.name, None)
        with open("MIM/loader.json", 'w') as file:
            json.dump(dirs, file)
        self.menu.dismiss()
        main_scr().ids.sm.remove_widget(self.scr)

    def on_touch_down(self, touch):
        if touch.button == "right":
            if Config().edit_mode and self.collide_point(touch.x, touch.y):
                self.menu.open()
            else:
                return super().on_touch_down(touch)
        else:
            return super().on_touch_down(touch)


class NavigationBar(MDBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buts = []
        # Clock.schedule_once(lambda t: self.ids.scroll.bind(minimum_height=self.ids.scroll.setter('height')))

    def on_item_press(self, inst):
        pass
        # logging.info(f"SideBar: Recieved release press from {inst}")
    
    def add_but(self, but: NavigationButton, ind=0):
        self.buts.append(but)
        self.ids.scroll.add_widget(but, index=ind)

    def _on_item_release(self, inst):
        for i in self.children:
            if i != inst:
                i.selected = False
        for i in self.buts:
            if i != inst:
                i.selected = False

        self.on_item_release(inst)

    def _find_free_name(self, att=0):
        dirs = os.listdir("MIM")
        if not att:
            if "New folder" in dirs:
                return self._find_free_name(att+1)
            return "New folder"
        if f"New folder ({att})" in dirs:
            return self._find_free_name(att+1)
        return f"New folder ({att})"

    def on_item_release(self, inst):
        if main_scr().ids.sm.current == "edit":
            main_scr().ids.sm.transition.direction = "right"
            main_scr().ids.sm.transition.mode = "pop"
        else:
            main_scr().ids.sm.transition = MyTransition()

        if inst.text == translate("Settings"):
            main_scr().ids.sm.current = "setts"
        elif inst.text == translate("Add Folder"):
            inst.deselect()
            name = translate("New folder")
            path = f"MIM/{self._find_free_name()}"
            os.mkdir(path)
            f = Folder(path, name)
            fi = FolderItem(folder=f, height=0, opacity=0)
            self.add_but(fi, 1)
            Clock.schedule_once(lambda t: fi.select())
            Clock.schedule_once(lambda t: Animation(height=70, opacity=1, d=.5).start(fi))
            with open("MIM/loader.json") as file:
                dirs: dict = json.load(file)
            dirs[f.path.name] = f.dict()
            with open("MIM/loader.json", 'w') as file:
                json.dump(dirs, file)
        else:
            main_scr().rail_choose(inst)
        # logging.info(f"SideBar: Recieved release signal from {inst}")


class InstallItem(MDBoxLayout, Updater):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        edit_mode = Config().edit_mode
        if self.update_link and edit_mode:
            if str(self.path) in registered_downloads:
                self._is_cancelled = False
                self.progress_bar = MDProgressBar(size_hint_y=None, height=4, pos_hint={"center_y": .5})
                self.upd_but = TranFillRoundFlatButton(text="Update", opacity=0, on_release=self.download_update, pos_hint={'center_y': .5}, md_bg_color=[0.56, 0.56, 0.56, 1])
                self.cancel_but = TooltipMDIconButton(icon='cancel', on_release=self.cancel_download, tooltip_text="Cancel updating", theme_icon_color="Hint", pos_hint={'center_y': 0.5})
                registered_downloads[str(self.path)].bind(progress=self.progress_bar.setter('value'))
                registered_downloads[str(self.path)].on_finish = self.on_finish
                self.add_widget(self.progress_bar)
                self.add_widget(self.cancel_but)
            else:
                self.progress_bar = MDProgressBar(opacity=0, size_hint_y=None, height=4, pos_hint={"center_y": .5})
                self.upd_but = TranFillRoundFlatButton(text="Update", on_release=self.download_update, pos_hint={'center_y': .5}, md_bg_color=[0.56, 0.56, 0.56, 1])
                self.cancel_but = TooltipMDIconButton(icon='cancel', opacity=0, on_release=self.cancel_download, tooltip_text="Cancel updating", theme_icon_color="Hint", pos_hint={'center_y': 0.5})
                self.bind(progress=self.progress_bar.setter('value'))
                self.add_widget(self.upd_but)
        if edit_mode:
            self.edit_but = TooltipMDIconButton(icon="pencil", theme_icon_color="Hint", tooltip_text="Edit appearance", on_release=self.show_edit, pos_hint={'center_y': 0.5})
            self.add_widget(TooltipMDIconButton(icon="trash-can", theme_icon_color="Hint", tooltip_text="Delete", pos_hint={'center_y': 0.5}, on_release=self.delete))
            self.add_widget(self.edit_but)
        self.ins_but = TooltipMDIconButton(icon="download-circle", tooltip_text="Install app", theme_icon_color="Custom", icon_color=app().theme_cls.primary_color, on_release=self.run, icon_size="36dp", pos_hint={'center_y': 0.5})
        self.add_widget(self.ins_but)

    def update(self):
        # self.ids.alias.text = f"  {self.alias}"
        # self.ids.ico.source = self.icon
        self.clear_widgets()
        self.__init__(path=self.path, alias=self.alias, icon=self.icon, update_link=self.update_link)


    def delete(self, inst):
        os.remove(self.path)
        self.size_hint_y=None
        anim = Animation(height=0, opacity=0, d=.5)
        anim.on_complete = lambda x: self.parent.remove_widget(self)
        anim.start(self)

    def cancel_download(self, _=None):
        try:
            del registered_downloads[str(self.path)]
        except Exception:
            pass
        self.cancel_update()
        self.progress = 0
        def fase2(_):
            self.remove_widget(self.cancel_but)
            self.remove_widget(self.progress_bar)
            try:
                self.add_widget(self.upd_but, index=3)
            except Exception:
                pass
            Animation(opacity=1, d=.3).start(self.upd_but)
        anim = Animation(opacity=0, d=.3)
        anim.on_complete = fase2
        anim.start(self.progress_bar)
        anim.start(self.cancel_but)


    def download_update(self, _):
        self.start_update()
        registered_downloads[str(self.path)] = self
        def fase2(_):
            self.add_widget(self.cancel_but, index=3)
            self.add_widget(self.progress_bar, index=4)
            anim = Animation(opacity=1, d=.3)
            anim.start(self.progress_bar)
            anim.start(self.cancel_but)
        anim = Animation(opacity=0, d=.3)
        anim.on_complete = fase2
        anim.start(self.upd_but)
    
    def on_finish(self, *_):
        self.cancel_download()
        Snackbar(text=f"{self.alias} download is finished").open()

    def show_edit(self, *args):
        edit_scr().ins = self
        edit_scr().prev = main_scr().ids.sm.current
        main_scr().ids.sm.transition = CardTransition(direction="left", mode="push")
        main_scr().ids.sm.current = "edit"


class StartScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Window.bind(size=self.set_pos)
    
    def set_pos(self, inst, val):
        self.ids.lbl.y = val[1] - 220


class MainMenu(MDScreen):
    folder: Folder = ObjectProperty(Folder())
    changed: bool = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder_items = self.folder.load_installers()
        self.count = len(os.listdir(self.folder.path))
        self.bind(changed=lambda *a: self.apply_auto_reload)
        # Thread(target=self.auto_reload, daemon=True).start()
    
    def apply_auto_reload(self):
        if self.changed:
            self.changed = False

            self.update()

    def auto_reload(self):
        while True:
            if self.manager is None:
                sleep(5)
            elif self.manager.current == self.name:
                logging.info(f"Checking for screen {self.name}")
                if cur_count := len(os.listdir(self.folder.path)) != self.count:
                    logging.info(f"Auto reloaded {self.name}")
                    self.count = cur_count
                    self.update()
                sleep(5)


    def reload_items(self):
        logging.info(f"{self.folder.alias}: Reloaded items")
        self.folder_items = self.folder.load_installers()

    def activate(self):
        def do_activate(inst):
            parser = ConfigParser()
            parser.read(res_path / "KMSAuto++.ini", encoding='utf-8-sig')
            parser.set("Configurations", "Lang", Config().lang.upper())
            with open(res_path / "KMSAuto++.ini", 'w', encoding='utf-8-sig') as file:
                parser.write(file)
            
            def execute():
                execute_string(f"""unzip activation.zip
copy KMSAuto++.ini activation
run activation/KMSAuto++.exe
remove activation""", str(res_path))

            Thread(target=execute).start()
            inst.parent.parent.parent.parent.dismiss()
        
        MDDialog(
            title=translate("Attention!"),
            text=translate("Windows Defender prevents activation program to start. To continue you should to disable \"Real time security\" of your Windows Defender in settnigs"),
            buttons=[
                TranRoundFlatIconButton(text="Cancel", on_release=lambda inst: inst.parent.parent.parent.parent.dismiss(), icon="cancel"),
                TranFillRoundFlatButton(text="Continue", on_release=do_activate)
            ]
        ).open()

    def search(self, text=""):
        scroll = self.ids.scroll
        scroll.clear_widgets()
        if not self.folder_items:
            lbl = MDLabel(halign='center', markup=True)
            def set_text(inst, val):
                lbl.text = translate("Drop your installers in folder ") + f"[color=ff9800][u][ref=f]{str(self.folder.path)}[/ref][/u][/color]" + translate(" or directly on window")
                lbl.bind(on_ref_press=lambda *a: os.startfile(self.folder.path))
            set_text(lbl, None)
            self.bind(name=set_text)
            scroll.add_widget(lbl)
            return
        if text:
            for i in self.folder_items:
                if text.lower() in i.alias.lower():
                    scroll.add_widget(InstallItem.from_ins(i))
        else:
            for i in self.folder_items:
                scroll.add_widget(InstallItem.from_ins(i))

    def update(self):
        text = self.ids.searcher.text
        self.reload_items()
        self.search(text)
    