import asyncio
from asyncio.subprocess import DEVNULL
import logging
import os
import time


from pynput.keyboard import Key, Controller
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from typing import Optional, Dict, Tuple


LOGGER = logging.getLogger(__name__)
ASSET_PATH = os.path.expanduser("~/.local/share/streamdeck")


class Button:
    icon: Optional[str] = None
    text: Optional[str] = ""
    font: Optional[str] = "Roboto-Regular.ttf"

    def __init__(self):
        self.image_cache = None
    
    async def setup(self, controller, page):
        return None
    
    async def action(self, deck, state, contoller, page):
        return None

    async def heartbeat(self, deck, controller=None, page=None):
        return None

    # Modification of the python-elgato-streamdeck example code
    def render(self, deck):
        # Create new key image of the correct dimensions, black background.
        image = PILHelper.create_image(deck)

        # Resize the source image asset to best-fit the dimensions of a single key,
        # and paste it onto our blank frame centered as closely as possible.
        
        if self.icon:
            LOGGER.info(f"Drawing {self.icon}")
            icon_filename = os.path.join(ASSET_PATH, "icons", self.icon)
            icon = Image.open(icon_filename).convert("RGBA")
            icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
            icon_pos = ((image.width - icon.width) // 2, 0)
            image.paste(icon, icon_pos, icon)


        # Load a custom TrueType font and use it to overlay the key index, draw key
        # label onto the image.
        draw = ImageDraw.Draw(image)
        font_path = os.path.join(ASSET_PATH, "fonts", self.font)
        font = ImageFont.truetype(font_path, 14)
        label_w, _ = draw.textsize(self.text, font=font)
        label_pos = ((image.width - label_w) // 2, image.height - 20)
        draw.text(label_pos, text=self.text, font=font, fill="white")

        return PILHelper.to_native_format(deck, image)

    def get_image(self, deck):
        if self.image_cache:
            LOGGER.info("Image cached, returning")
            return self.image_cache
        
        LOGGER.info("Rendering and returning image")
        try:
            image = self.render(deck)
        except Exception as e:
            LOGGER.error(f"Exception {e} occurred")
        self.image_cache = image
        return image


class CommandButton(Button):
    command: Optional[str] = None

    async def action(self, deck, state, controller, page):
        if state and self.command is not None:
            await asyncio.create_subprocess_shell(
                cmd=self.command,
                stderr=DEVNULL,
                stdout=DEVNULL,
                stdin=DEVNULL
            )
        return await super().action(deck, state, controller, page)

    

class MenuButton(Button):
    menu_name: Optional[str] = None

    async def action(self, deck, state, controller, page):
        if state:
            LOGGER.info(f"Transition to menu {self.menu_name}")
            await controller.set_next_page(self.menu_name)
        return await super().action(deck, state, controller, page)


class BackButton(Button):
    icon = "close.png"
    text = "Back"

    async def action(self, deck, state, controller, page):
        if state:
            await controller.return_to_previous_page()
        return await super().action(deck, state, controller, page)


class StatefulButton(Button):
    states: Dict[str, Tuple[str, str]]
    default_state: str

    def __init__(self):
        self.state = self.default_state
        self._state_cache = {k: None for k in self.states}

    @property
    def icon(self):
        LOGGER.info(f"Getting icon")
        return self.states[self.state][0]

    @property
    def text(self):
        LOGGER.info(f"Getting text")
        return self.states[self.state][1]

    @property
    def image_cache(self):
        LOGGER.info(f"Loading stateful cache for state {self.state}")
        return self._state_cache[self.state]

    @image_cache.setter
    def image_cache(self, val):
        LOGGER.info(f"Setting stateful cache for state {self.state}")
        self._state_cache[self.state] = val

    async def change_state(self, state):
        self.state = state

    async def action(self, deck, state, controller, page):
        LOGGER.info(f"Calling Stateful action")
        return await super().__init__(deck, state, controller, page)
        
            

    