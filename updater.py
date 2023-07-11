from fileloader import Installer
import requests
from time import time
from path_n_data import res_path
import logging
import os
import shutil
from threading import Thread
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.event import EventDispatcher
from kivy.clock import Clock


def check_internet(url='http://www.google.com/', timeout=5):
    try:
        _ = requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No internet connection available.")
    return False


def byte_vals(count: int, ndigits: int = 2, val: str = ""):
    if val == 'b' or count < 1024:
        return f"{count} B"
    elif val == "kb" or count < 1024 ** 2:
        return f"{round(count / 1024, ndigits)} KB"
    elif val == 'mb' or count < 1024 ** 3:
        return f"{round(count / (1024 ** 2), ndigits)} MB"
    elif val == "gb" or count: # > 1024 ** 3:
        return f"{round(count / (1024 ** 3), ndigits)} GB"


class Updater(EventDispatcher, Installer):
    progress = NumericProperty(0)
    info: str = StringProperty("Pinging...")
    _is_cancelled: bool = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_event_type('on_finish')
    
    @classmethod
    def from_ins(cls, ins: Installer):
        return cls(**ins.dict())

    def cancel_update(self):
        self._is_cancelled = True

    def start_update(self):
        if self._is_cancelled:
            logging.info(f"{self.alias}: Update started")
            self._is_cancelled = False
            Thread(target=self._process_update, daemon=True).start()

    def _process_update(self):
        url = self.update_link
        try:
            response = requests.get(url, stream=True)
        except requests.exceptions.ConnectionError:
            self.info = "Connection Error..."
            self.dispatch("on_finish")
            return
        
        total_length = int(response.headers.get('content-length'))
        start = time()

        tmp_path = str(res_path / f"{self.alias}_dwnl.tmp")
        with open(tmp_path, "wb") as handle:
            counter = 0
            last = 0
            last_time = 0
            speed = byte_vals(0)
            for data in response.iter_content(128):
                if self._is_cancelled:
                    break
                counter += len(data)
                if int(time() - start) - last_time > 0:
                    last_time = int(time() - start)
                    speed = byte_vals(counter - last)
                    last = counter
                # logging.info(f"{byte_vals(counter)} / {byte_vals(total_length)}, {speed}/s")
                self.info = f"{byte_vals(counter)} / {byte_vals(total_length)}, {speed}/s"
                self.progress = counter / total_length * 100
                handle.write(data)

        if not self._is_cancelled:
            finish = round(time() - start, 2)
            logging.info(f"{self.alias}: Finished update in {finish} s")
            shutil.copy(tmp_path, self.path)
            self.info = f"Finished in {finish} s"
            Clock.schedule_once(lambda t: self.dispatch("on_finish"))
        
        os.remove(tmp_path)
    
    def on_finish(self):
        pass
