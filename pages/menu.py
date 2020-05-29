import asyncio
import logging

from .base import StreamDeckMiniPage, create_action_method
from .commands import launch_shell, launch_process, BackAction
from .settings import SettingsPage


LOGGER = logging.getLogger(__name__)


class MainMenuPage(StreamDeckMiniPage):
    """
    Main menu page for my StreamDeck
    """

    deck_type = "StreamDeckMini"

    button_1_label = "Steam"
    button_2_label = "Messenger"
    button_3_label = "Mail"
    button_4_label = "System"
    button_5_label = "Settings"
    button_6_label = "Back"

    button_1_icon = "steam_tray.ico"
    button_2_icon = "messenger.png"
    button_3_icon = "mail.png"
    button_4_icon = "sysmon.png"
    button_5_icon = "settings.png"
    button_6_icon = "close.png"

    button_1 = create_action_method(launch_shell, "steam")
    button_2 = create_action_method(launch_shell, "caprine")   
    button_3 = create_action_method(launch_shell, "evolution")
    button_4 = create_action_method(launch_shell, "gnome-system-monitor") 

    async def button_5(self):
        LOGGER.info("Changing to settings page.")
        await self.controller.set_next_page(SettingsPage)

    button_6 = BackAction()

    #async def button_6(self):
    #    LOGGER.info("Back button pressed, returning to previous page")
    #    await self.controller.return_to_previous_page()

    
    
    
