import asyncio
import time
import logging
import functools
import pathlib
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Dict, Optional
    from controller import Controller


LOGGER = logging.getLogger(__name__)


PAGE_REGISTRY: "Dict[str, Page]" = {}


def create_action_method(coro, *args, **kwargs):
    @functools.wraps(coro)
    async def method(self):
        nonlocal args, kwargs
        LOGGER.info(f"Calling {coro.__name__}{args}")
        await coro(self, *args, **kwargs)
    return method


async def get_page(name):
    """
    Load a page
    """
    global PAGE_REGISTRY
    if name in PAGE_REGISTRY:
        LOGGER.info(f"Got page {name} from registry")
        return PAGE_REGISTRY["name"]
    
    # TODO: Implement loading from spec files
    LOGGER.warning(f"No page named {name}")



def cache(coro):
    coro_cache = {}
    lock = asyncio.Lock()
    @functools.wraps(coro)
    async def wrapper(self, *args):
        async with lock:
            if args in coro_cache:
                LOGGER.debug(f"Loading {args} from cache")
                return coro_cache[args]
            LOGGER.debug(f"Computing {args} for cache")
            result = await coro(self, *args)
            coro_cache[args] = result
            return result
    return wrapper


class PageMeta(type):

    def __new__(cls, name, bases, ns):
        new_cls = super().__new__(cls, name, bases, ns)
        PAGE_REGISTRY[name] = new_cls
        return new_cls


class Page(metaclass=PageMeta):
    pressed_threshold: float = 3.0
    heartbeat_time: float = 60.0

    asset_path = pathlib.Path("~/.local/share/streamdeck").expanduser()
    label_font: str = "Roboto-Regular.ttf"
    deck_type: str = "StreamDeck"


    controller: "Controller"

    def __init__(self, controller):
        self.controller = controller
        self._lock = asyncio.Lock()
        self._pressed = None

    def __str__(self):
        return f"Deck {self.__class__.__name__}"

    async def default_action(self):
        """
        Action called when a specific action has not been created.
        """
        LOGGER.info("No action detected, using default")

    async def alt_dispatch(self, button):
        """
        Dispatcher for long press actions.
        """
        func = getattr(self, f"alt_button_{button}", self.default_action)

        await func()

    async def dispatch(self, button, status):
        """
        Generic dispatcher for a button press event.

        Calls specific button action method. Also handles
        long press dispatching.
        """
        
        async with self._lock:
            if status:
                self._pressed = time.time()
                return
            else:
                pressed_time = time.time() - self._pressed

        # long press
        if pressed_time >= self.pressed_threshold:
            LOGGER.info("Long press detected")
            await self.alt_dispatch(button+1)
            return

        LOGGER.info(f"Short press detected, calling `button_{button+1}`")

        # short press
        func = getattr(self, f"button_{button+1}", self.default_action)
        await func()
        return

    async def setup(self):
        """
        Setup function called when the page is loaded.
        """
        pass

    async def teardown(self):
        """
        Teardown function called when the page is changed.
        """
        pass

    async def heartbeat(self):
        """
        Called periodically by the controller, according to the
        heartbeat time class attribute.

        Used to periodically update the page attributes according
        to the system environment.
        """
        while True:
            try:
                await asyncio.sleep(self.heartbeat_time)
            except asyncio.CancelledError:
                break

    @cache
    async def get_font(self, font: str, size: int) -> ImageFont.ImageFont:
        """
        Load the font from file with the given size, return the
        font as n ImageFont.
        """
        font_path = self.asset_path / "fonts" / font
        return ImageFont.truetype(str(font_path), size)

    @cache
    async def render_image_from_file(self, icon: str, label: str):
        """
        Render the image from file into an image with optional label.

        this funckwargstion code is based on the render helper function from the
        python-elgato-streamdeck example code.

        Missing icons are not rendered.
        """
        image = PILHelper.create_image(self.controller.deck)

        if icon:
            icon_path = self.asset_path / "icons" / icon

            if icon_path.is_file():
                LOGGER.info(f"Rendering icon {icon}")
                icon_image = Image.open(str(icon_path)).convert("RGBA")
                icon_image.thumbnail((image.width, image.height - 20), Image.LANCZOS)
                icon_pos = ((image.width - icon_image.width) // 2, 0)
                image.paste(icon_image, icon_pos, icon_image)
            else:
                LOGGER.warning(f"Icon {icon} cannot be found")

        if label:
            LOGGER.debug("Getting font and rendering label")
            draw = ImageDraw.Draw(image)
            font = await self.get_font(self.label_font, 14)
            label_w, _ = draw.textsize(label, font=font)
            label_pos = ((image.width - label_w) // 2, image.height - 20)
            draw.text(label_pos, text=label, font=font, fill="white")

        return PILHelper.to_native_format(self.controller.deck, image)

    async def render(self):
        """
        Render the page images on the deck.

        This should return a list of images to render on the deck.
        """
        pass



class StreamDeckMiniPage(Page):
    """
    Base class for StreamDeckMini pages.

    Includes an implementation of the render method for
    simple pages on the stream deck mini. 
    """
    deck_type = "StreamDeckMini"

    button_1_label: "Optional[str]" = None
    button_2_label: "Optional[str]" = None
    button_3_label: "Optional[str]" = None
    button_4_label: "Optional[str]" = None
    button_5_label: "Optional[str]" = None
    button_6_label: "Optional[str]" = None

    button_1_icon: "Optional[str]" = None
    button_2_icon: "Optional[str]" = None
    button_3_icon: "Optional[str]" = None
    button_4_icon: "Optional[str]" = None
    button_5_icon: "Optional[str]" = None
    button_6_icon: "Optional[str]" = None

    async def render(self):
        LOGGER.debug("Calling render routine")
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