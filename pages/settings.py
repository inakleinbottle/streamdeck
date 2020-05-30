
import logging


from .base import StreamDeckMiniPage, cache
from .commands import BackAction

LOGGER = logging.getLogger(__name__)


class SettingsPage(StreamDeckMiniPage):
    deck_type = "StreamDeckMini"

    button_1_label = None
    button_2_label = None
    button_3_label = None
    button_4_label = None
    button_5_label = None
    button_6_label = "Back"

    button_1_icon = None
    button_2_icon = None
    button_3_icon = None
    button_4_icon = None
    button_5_icon = None
    button_6_icon = "close.png"


    botton_6 = BackAction()