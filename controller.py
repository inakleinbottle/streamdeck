import asyncio
import logging
import pathlib
import time
import traceback


from StreamDeck.Devices.StreamDeck import StreamDeck
from pages import get_page, MainPage

LOGGER = logging.getLogger(__name__)


class Controller:

    def __init__(self, deck=None, loop=None):
        self.page_cache = {}        
        self.loop = loop or asyncio.get_event_loop()
        self.deck = deck

        self._lock = asyncio.Lock(loop=self.loop)

        page = MainPage(self)
        self.default_page = page
        self.current_page = page
        self.previous_page = None
        self.page_cache["MainPage"] = page

        self.current_heartbeat_task = None

    async def set_next_page(self, page):
        if page in self.page_cache:
            LOGGER.info(f"Loading cached paged {page}")
            self.current_page = self.page_cache[page]
            return None
        
        if (new_page:=await get_page(page)) is not None:
            self.current_page = self.page_cache[page] = new_page
            return None
        
        LOGGER.warning("Reverting to default")
        self.previous_page = self.current_page
        self.current_page = self.default_page
        self.force_reload_page = True

    async def return_to_previous_page(self):
        LOGGER.info("Returning to previous page")
        page = self.previous_page or self.default_page
        self.previous_page = self.current_page
        self.current_page = page
        self.force_reload_page = True
        
    async def update_deck(self, deck=None):
        deck = deck or self.deck
        LOGGER.info(f"Updating deck {deck.id()}")
        await self.current_page.render()

    async def set_image(self, button: int, image):
        """
        Set the image on a button of the deck.
        """
        async with self._lock:
            self.deck.set_key_image(button, image)

    async def setup(self, deck):
        await self.current_page.setup()

    def heartbeat(self):
        pass

    async def __call__(self, deck, key, state):
        LOGGER.info(f"Deck {deck.id()} button {key} {'pressed' if state else 'released'}" )
        await self.current_page.dispatch(key, state)

        if not state:
            await self.update_deck(deck)



