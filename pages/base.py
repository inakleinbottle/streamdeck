import asyncio
import time
import logging
import functools
import pathlib


from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper


LOGGER = logging.getLogger(__name__)

PAGE_REGISTRY = {}


async def get_page(name):
    """
    Load a page
    """
    global PAGE_REGISTRY
    if name in PAGE_REGISTRY:
        return PAGE_REGISTRY["name"]
    
    # TODO: Implement loading from spec files
    LOGGER.warning(f"No page named {name}")


class PageMeta(type):

    def __new__(cls, name, bases, ns):
        new_cls = super().__new__(cls, name, bases, ns)
        PAGE_REGISTRY[name] = new_cls
        return new_cls


class Page(metaclass=PageMeta):
    pressed_threshold = 3.0
    heatbeat_time = 30.0

    asset_path = pathlib.Path()
    label_font = "Roboto-Regular.ttf"
    deck_type = "StreamDeck"

    def __init__(self, controller):
        self.controller = controller
        self._lock = asyncio.Lock()
        self._pressed = None

    async def default_action(self):
        """
        Action called when a specific action has not been created.
        """
        pass

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
            await self.alt_dispatch(button)
            return

        # short press
        func = getattr(self, f"button_{button}", self.default_action)
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

    async def heatbeat(self):
        """
        Called periodically by the controller, according to the
        heartbeat time class attribute.

        Used to periodically update the page attributes according
        to the system environment.
        """

    @functools.lru_cache
    async def render_image_from_file(self, icon: str, label: str):
        """
        Render the image from file into an image with optional label.

        this function code is based on the render helper function from the
        python-elgato-streamdeck example code.

        This function uses a lru cache to cache past executions so that
        subsequent calls will not incur additional overhead.

        Missing icons are not rendered
        """
        icon_path = self.asset_path / "icons" / icon

        image = PILHelper.create_image(self.controller.deck)

        if icon.is_file():
            LOGGER.info(f"Rendering icon {icon}")
            icon_image = Image.open(icon_path).convert("RGBA")
            icon_image.thumbnail((image.width, image.height - 20), Image.LANCZOS)
            icon_pos = ((image.width - icon.width) // 2, 0)
            image.paste(icon_image, icon_pos, icon_image)
        else:
            LOGGER.warning(f"Icon {icon} cannot be found")

        draw = ImageDraw.Draw(image)
        font_path = self.asset_path / "fonts" / self.label_font
        font = ImageFont.truetype(font_path, 14)
        label_w, _ = draw.textsize(label, font=font)
        label_pos = ((image.width - label_w) // 2, image.height - 20)
        draw.text(label_pos, text=label, font=font, fill="white")

        return PILHelper.to_native_format(self.controller.deck, image)


    async def render(self):
        """
        Render the page images on the deck.

        This should call the controller instance `set_image` for each
        button to set the image.
        """

    


        

