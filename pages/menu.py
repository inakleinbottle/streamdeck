import asyncio
import logging

from .base import Page, create_action_method

LOGGER = logging.getLogger(__name__)


class MainMenuPage(Page):
    """
    Main menu page for my StreamDeck
    """

    deck_type = "StreamDeckMini"

    button_1_label = "Steam"
    button_2_label = "Clock"
    button_3_label = "Mute"
    button_4_label = "Menu"
    button_5_label = "Settings"
    button_6_label = "Back"

    button_1_icon = "steam_tray.ico"
    button_2_icon = "clock.png"
    button_3_icon = "mic-on.png"
    button_4_icon = "navigation.png"
    button_5_icon = "settings.png"
    button_6_icon = "close.png"

    async def render(self):
        button_1_label = self.button_1_label
        button_2_label = self.button_2_label
        button_3_label = self.button_3_label
        button_4_label = self.button_4_label
        button_5_label = self.button_5_label
        button_6_label = self.button_6_label

        button_1_icon = self.button_1_icon
        button_2_icon = self.button_2_icon
        button_3_icon = self.button_3_icon
        button_4_icon = self.button_4_icon
        button_5_icon = self.button_5_icon
        button_6_icon = self.button_6_icon

        return await asyncio.gather(
            self.render_image_from_file(button_1_icon, button_1_label),
            self.render_image_from_file(button_2_icon, button_2_label),
            self.render_image_from_file(button_3_icon, button_3_label),
            self.render_image_from_file(button_4_icon, button_4_label),
            self.render_image_from_file(button_5_icon, button_5_label),
            self.render_image_from_file(button_6_icon, button_6_label)
        )

    async def button_6(self):
        LOGGER.info("Back button pressed, returning to previous page")
        await self.controller.return_to_previous_page()

    button_1 = button_6
    button_2 = button_6
    button_3 = button_6
    button_4 = button_6
    button_5 = button_6
