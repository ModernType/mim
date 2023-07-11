from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.factory import Factory
from kivymd.uix.textfield import MDTextField
from path_n_data import load_kv
from translation import Translated
from kivy.uix.screenmanager import ShaderTransition

load_kv("common")


class MyTransition(ShaderTransition):
    fs = """$HEADER$
    uniform float t;
    uniform sampler2D tex_in;
    uniform sampler2D tex_out;

    void main(void) {
        vec4 cin = texture2D(tex_in, tex_coord0);
        vec4 cout = texture2D(tex_out, tex_coord0);
        gl_FragColor = mix(cout, cin, clamp((-1.5 + 1.5*tex_coord0.y + 2.5*t),
            0.0, 1.0));
    }"""


class IconListItem(Factory.OneLineIconListItem):
    icon = StringProperty()


class TooltipMDIconButton(Factory.MDIconButton, Factory.MDTooltip, Translated):
    translatable = ListProperty(["tooltip_text"])


class ImageButton(Factory.FitImage, Factory.Button):
    pass


class TranTextField(MDTextField, Translated):
    translatable = ListProperty(["hint_text", "helper_text"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(hint_text=lambda inst, val: self.translate("hint_text", val))


class TranRoundFlatIconButton(Factory.MDRoundFlatIconButton, Translated):
    translatable = ListProperty(["text"])
    line_width = NumericProperty(1.01)


class TranFillRoundFlatButton(Factory.MDFillRoundFlatButton, Translated):
    translatable = ListProperty(["text"])


class MDNumberField(TranTextField):
    def insert_text(sub_str: str, undo=False):
        if sub_str.isdigit():
            super().insert_text(sub_str, undo)


Factory.register("IconListItem", IconListItem)
Factory.register("TooltipMDIconButton", TooltipMDIconButton)
Factory.register("ImageButton", ImageButton)
Factory.register("MDNumberField", MDNumberField)
Factory.register("TranTextField", TranTextField)
Factory.register("TranRoundFlatIconButton", TranRoundFlatIconButton)
Factory.register("TranFillRoundFlatButton", TranFillRoundFlatButton)
