import asyncio
import logging

from StreamDeck.Devices.StreamDeck import StreamDeck

from pages.buttons import Button

LOGGER = logging.getLogger(__name__)


class Page:

    def __init__(self, name, *buttons):
        self.name = name
        self.buttons = [button() for button in buttons]
        self.controller = None

    def __len__(self):
        return len(self.buttons)

    async def setup(self, controller):
        self.controller = controller
        for button in self.buttons:
            await button.setup(controller, self)

    async def heartbeat(self, deck, controller):
        LOGGER.info("Running hearbeat")
        
        for button in self.buttons:
            await button.heartbeat(deck, controller)
        
        await self.draw_buttons(deck)

    async def draw_buttons(self, deck: StreamDeck):
        LOGGER.info(f"Redrawing buttons for page {self.name}")
        for i, button in enumerate(self.buttons):
            LOGGER.info(f"Getting image for button {i}")
            image = button.get_image(deck)
            deck.set_key_image(i, image)
        
    async def action(self, deck, key, state, controller):
        button = self.buttons[key]
        if state:
            LOGGER.info(f"Key {key} pressed")
        else:
            LOGGER.info(f"Key {key} released")
        await button.action(deck, state, controller, self)


