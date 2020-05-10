import asyncio
from contextlib import asynccontextmanager
import logging
import os
from subprocess import DEVNULL

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from pynput.keyboard import Key, Controller
from PIL import Image, ImageDraw, ImageFont

MAIN_LOOP_SLEEP = 10

LOGGER = logging.getLogger(__name__)
ASSET_PATH = os.path.expanduser("~/.local/share/streamdeck")

DECKS = {
    "Stream Deck Mini": [
        {"icon": "macro-key.png", "text": "Terminal", "command": "gnome-terminal", "key_press": None, "produce_text": None},
        {"icon": "macro-key.png", "text": "Two", "command": "gnome-terminal", "key_press": None, "produce_text": None},
        {"icon": "macro-key.png", "text": "Three", "command": "gnome-terminal", "key_press": None, "produce_text": None},
        {"icon": "macro-key.png", "text": "Four", "command": "gnome-terminal", "key_press": None, "produce_text": None},
        {"icon": "macro-key.png", "text": "Five", "command": "gnome-terminal", "key_press": None, "produce_text": None},
        {"icon": "macro-key.png", "text": "Six", "command": "gnome-terminal", "key_press": None, "produce_text": None},
    ]
}

CACHE = {}


# From the exampls of python-elgato-streamdeck
def render_key_image(deck, icon_filename, font_filename, label_text):
    # Create new key image of the correct dimensions, black background.
    image = PILHelper.create_image(deck)

    # Resize the source image asset to best-fit the dimensions of a single key,
    # and paste it onto our blank frame centered as closely as possible.
    icon = Image.open(icon_filename).convert("RGBA")
    icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
    icon_pos = ((image.width - icon.width) // 2, 0)
    image.paste(icon, icon_pos, icon)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    label_w, label_h = draw.textsize(label_text, font=font)
    label_pos = ((image.width - label_w) // 2, image.height - 20)
    draw.text(label_pos, text=label_text, font=font, fill="white")

    return PILHelper.to_native_format(deck, image)



async def update_keys(deck):
    global DECKS, CACHE

    buttons = DECKS[deck.deck_type()]

    for i, button in enumerate(buttons):
        cname=f"{deck}-{i}"
        if not cname in CACHE:
            image = CACHE[cname] = render_key_image(
                deck, 
                f"{ASSET_PATH}/icons/{button['icon']}",
                f"{ASSET_PATH}/fonts/Roboto-Regular.ttf",
                button["text"]
            )
        else:
            image = CACHE[cname]
        deck.set_key_image(i, image)

        


async def key_callback(deck, key, state):
    global DECKS
    button = DECKS[deck.deck_type()][key]

    if state:
        LOGGER.info(f"Key {key} pressed")

        if (cmd:=button["command"]) is not None:
            LOGGER.info(f"Launching cmd: {cmd}")
            await asyncio.create_subprocess_shell(cmd, stdout=DEVNULL, stderr=DEVNULL, stdin=DEVNULL)

        if (keys:=button["key_press"]) is not None:
            LOGGER.info(f"Pressing keys: {keys}")

        if (text:=button["produce_text"]) is not None:
            LOGGER.info(f"Producing text: {text}")
            kb_controller = Controller()
            kb_controller.type(text)
           
    else:
        LOGGER.info(f"Key {key} released")

    await update_keys(deck)



@asynccontextmanager
async def setup_decks():
    LOGGER.info("Setting up stream decks")
    devices = DeviceManager().enumerate()

    LOGGER.info(f"Found {len(devices)} stream decks")

    for deck in devices:
        if not (t:=deck.deck_type()) in DECKS:
            LOGGER.warning(f"Detected {t}, which has no configuration set")
            continue
        deck.open()
        deck.reset()
        deck.set_key_callback_async(key_callback)
        await update_keys(deck)

    try:
        yield devices
    finally:
        LOGGER.info("Closing stream decks")
        for deck in devices:
            deck.reset()
            deck.close()

    

async def main():
    LOGGER.info("Starting main application")

    async with setup_decks():
        while True:
            await asyncio.sleep(MAIN_LOOP_SLEEP)





    








if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
