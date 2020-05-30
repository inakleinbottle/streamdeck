import asyncio
import functools
import logging
import pathlib
import time
import traceback
import inspect

from typing import List, Union

from StreamDeck.Devices.StreamDeck import StreamDeck
from pages import get_page, MainPage, Page
from pages.pagestack import PageStack, PageState


LOGGER = logging.getLogger(__name__)


class Controller:

    def __init__(self, deck: StreamDeck, main_page=MainPage, loop=None):
        self.page_cache = {}        
        self.loop = loop or asyncio.get_event_loop()
        self.deck = deck

        self._lock = asyncio.Lock()

        page = main_page(self)
        self.default_page = page
        self.current_page = page
        self.previous_page = None
        self.page_cache["MainPage"] = page

        self.page_stack = PageStack(page)

        self.current_heartbeat_task = None

    async def set_next_page(self, page):
        
        if inspect.isclass(page) and issubclass(page, Page):
            if (name:=page.__name__) in self.page_cache:
                LOGGER.info(f"Loading cached paged {name}")
                new_page = self.page_cache[name]
            else:
                LOGGER.info(f"Loading new page {name}")
                new_page = self.page_cache[name] = page(self)
        elif page in self.page_cache:
            LOGGER.info(f"Loading cached paged {page}")
            new_page = self.page_cache[page]
        elif (page_class:=await get_page(page)) is not None:
            new_page = self.page_cache[page] = page_class(self)
        else:
            LOGGER.warning("Page not found, no change will occur")
            return

        LOGGER.info(f"Setting page {new_page}")
        await self.page_stack.push(new_page)
        await self.update_deck()

    async def return_to_root(self):
        """
        Return to the root page.
        """
        await self.page_stack.pop_all()
        await self.update_deck()

    async def return_to_previous_page(self):
        await self.page_stack.pop()
        await self.update_deck()

    async def update_deck(self):
        deck = self.deck
        LOGGER.info(f"Updating deck {deck.id()}")
        async with self._lock:
            LOGGER.debug(f"Rendering page {self.current_page}")
            current = await self.page_stack.current_page()
            images = await current.render()
            LOGGER.debug(f"Setting images")
            for i, image in enumerate(images):
                await self._set_image(i, image)

    async def maybe_update_deck(self, page):
        """
        Trigger an update of the deck if the requesting page
        is active.
        """
        status = await self.page_stack.get_status(page)
        if status == PageState.Active:
            self.update_deck()

    async def update_key(self, key, image):
        """
        Update the image on a given key.
        """
        async with self._lock:
            await self._set_image(key, image)

    async def maybe_update_key(self, page, key, image):
        """
        Trigger an update of a given key if the requesting page
        is active.
        """
        status = await self.page_stack.get_status(page)
        if status == PageState.Active:
            await self.update_key(key, image)

    async def _set_image(self, button: int, image):
        """
        Set the image on a button of the deck.
        """
        self.deck.set_key_image(button, image)

    async def setup(self):
        await self.current_page.setup()

    def heartbeat(self):
        pass

    async def __call__(self, deck, key, state):
        LOGGER.info(f"Deck {deck.id()} button {key} {'pressed' if state else 'released'}" )
        current = await self.page_stack.current_page()
        await current.dispatch(key, state)




