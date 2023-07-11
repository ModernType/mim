# import sys
# if True: # hasattr(sys, "_MEIPASS"):
#     from elevate import elevate
#     try:
#         elevate(False)
#     except Exception:
#         sys.exit(0)

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from app import APP
from ui.main_scr import MainScreen

if __name__ == "__main__":
    APP.sm.add_widget(MainScreen())
    APP.run()
