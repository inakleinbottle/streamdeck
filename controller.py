import asyncio
import functools
import logging
import pathlib
import time
import traceback
import inspect

from StreamDeck.Devices.StreamDeck import StreamDeck
from pages import get_page, MainPage, Page

LOGGER = logging.getLogger(__name__)



class Controller:

    def __init__(self, deck: StreamDeck, loop=None):
        self.page_cache = {}        
        self.loop = loop or asyncio.get_event_loop()
        self.deck = deck

        self._lock = asyncio.Lock()

        page = MainPage(self)
        self.default_page = page
        self.current_page = page
        self.previous_page = None
        self.page_cache["MainPage"] = page

        self.current_heartbeat_task = None

    async def set_next_page(self, page):
        
        if inspect.isclass(page) and issubclass(page, Page):
            if (name:=page.__name__) in self.page_cache:
                LOGGER.info(f"Loading cached paged {name}")
                new_page = self.page_cache[name]
            else:
                LOGGER.info(f"Loading new page {name}")
                new_page = page(self)
                self.page_cache[name] = new_page
        elif page in self.page_cache:
            LOGGER.info(f"Loading cached paged {page}")
            new_page = self.page_cache[page]
        elif (page_class:=await get_page(page)) is not None:
            new_page = self.page_cache[page] = page_class(self)
        else:
            LOGGER.warning("Reverting to default")
            new_page = self.default_page

        LOGGER.info(f"Setting page {new_page}")
        
        await new_page.setup()
        async with self._lock:
            self.previous_page = self.current_page
            self.current_page = new_page

        await self.update_heartbeat()
        await self.update_deck()

    async def return_to_previous_page(self):
        LOGGER.info("Returning to previous page")
        page = self.previous_page or self.default_page
        async with self._lock:
            LOGGER.debug("Aquired lock")
            self.previous_page = self.current_page
            self.current_page = page
        LOGGER.debug("Released lock")
        await self.update_heartbeat()
        await self.update_deck()

    async def update_deck(self):
        deck = self.deck
        LOGGER.info(f"Updating deck {deck.id()}")
        async with self._lock:
            LOGGER.debug(f"Rendering page {self.current_page}")
            images = await self.current_page.render()
            LOGGER.debug(f"Setting images")
            for i, image in enumerate(images):
                await self._set_image(i, image)

    async def _set_image(self, button: int, image):
        """
        Set the image on a button of the deck.
        """
        self.deck.set_key_image(button, image)

    async def update_heartbeat(self):
        LOGGER.debug("Updating heartbeat task")
        async with self._lock: 
            if (task:=self.current_heartbeat_task) is not None:
                LOGGER.debug("Cancelling current heartbeat")
                task.cancel()
            LOGGER.debug("Creating new heartbeat coroutine")

            coro = self.current_page.heartbeat()
            self.current_heartbeat_task = self.loop.create_task(coro)


    async def setup(self):
        await self.update_heartbeat()
        await self.current_page.setup()

    def heartbeat(self):
        pass

    async def __call__(self, deck, key, state):
        LOGGER.info(f"Deck {deck.id()} button {key} {'pressed' if state else 'released'}" )
        await self.current_page.dispatch(key, state)




