#!/usr/local/bin/python3.8

import asyncio
from contextlib import asynccontextmanager
import logging
import os
import sys
from subprocess import DEVNULL

from StreamDeck.DeviceManager import DeviceManager

from controller import Controller



MAIN_LOOP_SLEEP = 60

LOGGER = logging.getLogger(__name__)




        

DECKS = {}


@asynccontextmanager
async def setup_decks():
    LOGGER.info("Setting up stream decks")
    devices = DeviceManager().enumerate()

    LOGGER.info(f"Found {len(devices)} stream decks")

    for deck in devices:

        deck.open()
        deck.reset()

        if (i_d:=deck.id()) in DECKS:
            controller = DECKS[i_d]
        else:
            controller = Controller(deck)
            DECKS[i_d] = controller 

        deck.set_key_callback_async(controller)
        await controller.setup(deck)
        await controller.update_deck(deck)

    try:
        yield devices
    finally:
        LOGGER.info("Closing stream decks")
        for deck in devices:
            deck.reset()
            deck.close()


def exception_handler(loop, context):
    LOGGER.error(f"{context['message']}")

async def main():
    LOGGER.info("Starting main application")
    loop = asyncio.get_event_loop()

    loop.set_exception_handler(exception_handler)

    async with setup_decks():
        while True:
            await asyncio.sleep(MAIN_LOOP_SLEEP)





    








if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
