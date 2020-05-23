import asyncio
import logging
import pathlib
import time
import traceback


from StreamDeck.Devices.StreamDeck import StreamDeck

LOGGER = logging.getLogger(__name__)


class Controller:

    def __init__(self, deck=None, loop=None):
        self.page_cache = {}        
        self.loop = loop or asyncio.get_event_loop()
        self.deck = deck

        self._lock = asyncio.Lock(loop=self.loop)

        page = self.load_page("main")
        self.default_page = page
        self.current_page = page
        self.previous_page = None
        self.page_cache["main"] = page

        self.force_reload_page = False
        self.heartbeat_delay = 60

        self.current_heartbeat_task = None


    @staticmethod
    def load_page(page):
        LOGGER.info(f"Loading page {page}")
        path = pathlib.Path("pages", f"{page}.py")
        if path.exists():
            ns = {"__name__": __name__}
            exec(path.read_bytes(), ns)
            if "PAGE" in ns:
                return ns["PAGE"]
        LOGGER.warning(f"Page {page} not found")
        return None

    async def set_next_page(self, page):
        if page in self.page_cache:
            LOGGER.info(f"Loading cached paged {page}")
            self.current_page = self.page_cache[page]
            return None
        
        if (new_page:=self.load_page(page)) is not None:
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
        await self.current_page.draw_buttons(deck)


    async def set_image(self, button: int, image):
        """
        Set the image on a button of the deck.
        """
        async with self._lock:
            self.deck.set_key_image(button, image)



    async def setup(self, deck):
        await self.current_page.setup(self)

    def heartbeat(self):
        self.loop.create_task(self.current_page.heartbeat, name="Page-heartbeat")
        self.loop.call_later(self.heartbeat_delay, self.heartbeat)

    async def __call__(self, deck, key, state):
        await self.current_page.action(deck, key, state, self)
        if self.force_reload_page:
            LOGGER.info("Force reloading page")
        
        if (not state) or self.force_reload_page:
            LOGGER.info(f"Button released, updating deck")
            await self.update_deck(deck)
            self.force_reload_page = False


