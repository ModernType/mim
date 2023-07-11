import json
import win32gui, win32ui, win32api, win32con
from PIL import Image
import os
from psutil import Popen
from threading import Thread
from pathlib import Path
from typing import List
from path_n_data import res_path
from execution import execute_string
from kivymd.uix.snackbar import Snackbar
from kivy.clock import Clock
from translation import translate
import logging


class Installer:
    def __init__(self, path: str | Path = "", alias: str = "", update_link: str = "", icon: str = ""):
        self.path = path if isinstance(path, Path) else Path(path)
        self.alias = alias if alias else self.path.name.removesuffix('.exe')
        self.update_link = update_link

        if icon and os.path.exists(icon):
            self._icon = icon
        if os.path.isdir(self.path):
            self._icon = icon if icon and os.path.exists(icon) else str(res_path / "folder.png")

            if self.path != Path("."):
                if (self.path / "order.txt").exists(): # os.path.exists(os.path.join(self.path, "order.txt")):
                    with open(self.path / "order.txt") as order:
                        self.order = order.read()
                else:
                    self.order = "\n".join(os.listdir(self.path))
                    with open(self.path / "order.txt", 'w') as order:
                        order.write(self.order)

    @property
    def icon(self):
        if not hasattr(self, "_icon") or not self._icon:
            try:
                self._exe_icon().save(f"MIM/.core/{self.path.name}.png")
                self._icon = f"MIM/.core/{self.path.name}.png"
            except Exception:
                self._icon = str(res_path / "folder.png")
        return self._icon

    @icon.setter
    def icon(self, val):
        self._icon = val

    def __str__(self):
        return f"<Installer: {self.path}: \"{self.alias}\" >"

    def __bool__(self):
        return bool(self.path)

    def dict(self):
        return dict(path=str(self.path), alias=self.alias, update_link=self.update_link,
                    icon="" if self.icon == str(res_path / "folder.png") else self.icon)

    @classmethod
    def from_dict(cls, d: dict):
        res = {}
        for k, v in d.items():
            if k in ("path", 'alias', 'icon', 'update_link'):
                res[k] = v

        return cls(**res)

    def _exe_icon(self) -> Image:
        path = str(self.path)
        icoX = win32api.GetSystemMetrics(win32con.SM_CXICON)
        icoY = win32api.GetSystemMetrics(win32con.SM_CXICON)

        large, small = win32gui.ExtractIconEx(path, 0)
        win32gui.DestroyIcon(small[0])

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, icoX, icoY)
        hdc = hdc.CreateCompatibleDC()

        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), large[0])

        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGBA',
            (32, 32),
            bmpstr, 'raw', 'BGRA', 0, 1
        )

        return img

    def run(self, *args) -> bool:
        if hasattr(self, 'order'):
            def _waiter():
                try:
                    execute_string(self.order, str(self.path))
                except Exception as ex:
                    logging.warning(f"{ex}")
                    with open("error.log", 'w', encoding='utf-8') as log:
                        log.write(f"{ex}")
                    Clock.schedule_once(lambda t, s=ex: Snackbar(text=f"Error installing: {s}").open())
                    Clock.schedule_once(lambda t: Snackbar(text=translate("Check error.log for full info")).open(), 5)
                else:
                    Clock.schedule_once(lambda t: Snackbar(text=self.alias + translate(" instalation is finished")).open())
            Thread(target=_waiter, daemon=True).start()
        else:
            try:
                Popen(self.path)
            except Exception:
                return False
        return True

    start = run


class Folder:
    def __init__(self, path: str | Path = "", alias: str = "", icon: str = ""):
        self.path: Path = path if isinstance(path, Path) else Path(path)
        self.alias = alias if alias else self.path.name
        self.icon = icon if icon else "folder"

    def __str__(self):
        return f"<Folder: {self.path}: \"{self.alias}\" >"

    def __bool__(self):
        return bool(self.path)

    def dict(self) -> dict:
        return dict(path=str(self.path), alias=self.alias, icon=self.icon)

    @classmethod
    def from_dict(cls, d: dict):
        if "path" not in d:
            raise KeyError("There is no \"path\" key in this dictionary")
        res = {}
        for k, v in d.items():
            if k in ("path", 'alias', 'icon'):
                res[k] = v
        return cls(**res)

    def load_installers(self) -> list[Installer]:
        insts = os.listdir(str(self.path))
        if "loader.json" in insts:
            with open(self.path / "loader.json") as file:
                try:
                    loader = json.load(file)
                except json.decoder.JSONDecodeError:
                    loader = {}
        else:
            loader = {}
        out = []

        for i in insts:
            if i in loader:
                loader[i]["path"] = f"{self.path}/{i}"
                out.append(Installer.from_dict(loader[i]))
            elif (i.endswith('.exe') or i.endswith('.msi') or os.path.isdir(self.path / i)) and not i.startswith('.'):
                ins = Installer(path=self.path/i)
                loader[i] = ins.dict()
                out.append(ins)

        with open(self.path / "loader.json", 'w') as file:
            json.dump(loader, file)

        return out


def load_dirs() -> List[Folder]:
    categories = os.listdir("MIM")
    # Loading custom settings from special file
    if "loader.json" in categories:
        with open("MIM/loader.json") as file:
            try:
                loader = json.load(file)
            except json.decoder.JSONDecodeError:
                loader = {}
    else:
        loader = {}
    out = []
    for c in categories:
        if not c.startswith(".") and os.path.isdir("MIM\\" + c):
            if c in loader:
                out.append(Folder.from_dict(loader[c]))
            else:
                fold = Folder(Path("MIM", c))
                out.append(fold)
                loader[c] = fold.dict()
    with open("MIM/loader.json", 'w') as file:
        json.dump(loader, file)
    return out
