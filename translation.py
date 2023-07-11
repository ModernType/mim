from kivy.properties import StringProperty, ListProperty
from path_n_data import Config, res_path
from kivy.factory import Factory
import os
import logging

def _read_langs():
    langs = {}
    for lang in os.listdir(res_path / "langs"):
        with open(res_path / "langs" / lang, encoding='utf-8') as file:
            data: str = file.read()
        data = data.splitlines()
        # for i in data:
        #     print(i.split("::"))
        langs[lang.split('.')[0]] = dict(i.split('::') for i in data)
    return langs


main_dict = _read_langs()


class Translated:
    translatable = ListProperty()

    def __init__(self) -> None:
        self.bind(translatable=self._register)
        self._register()
        
    def _register(self, *args):
        # logging.info(f"{self.__class__.__name__}: Registering translateable attrs {self.translatable}")
        for i in self.translatable:
            arg = {i: lambda inst, val: self.translate(i, val)}
            self.bind(**arg)

    def translate(self, attr, val):
        self.__setattr__(attr, translate(val))


Factory.register("Translated", Translated)


def translate(val):
    lang_dict = main_dict[Config().lang]
    return lang_dict.get(val, val)
