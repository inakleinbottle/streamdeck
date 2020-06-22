import asyncio
import datetime
import traceback
import logging

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from .base import Page, cache
from .commands import BackAction

LOGGER = logging.getLogger(__name__)


MINUTE_KEY = 1
HOUR_KEY = 0


async def wait_for_next_minute(ref_time):
    """
    Wait until the next clock minute relative to a reference time.
    """
    time_now = datetime.datetime.now()
    LOGGER.debug(f"Time now {time_now}, relative time {ref_time}")
    if time_now.minute == ref_time.minute:
        LOGGER.debug(f"Sleeping for {60 - time_now.second} seconds")
        await asyncio.sleep(60 - time_now.second)
    return time_now


class ClockPage(Page):
    """
    Main menu page for my StreamDeck
    """

    deck_type = "StreamDeckMini"

    heartbeat_time = 60

    button_6_label = "Back"

    button_6_icon = "close.png"

    def __init__(self, controller):
        super().__init__(controller)
        
        self._last = None

    @cache
    async def render_clock_number(self, number: int) -> Image.Image:
    
        LOGGER.info(f"Rendering number {number}")
        image = PILHelper.create_image(self.controller.deck)

        text = f"{number:02d}"

        font = await self.get_font(self.label_font, 50)
        draw = ImageDraw.Draw(image)
        w, _h = draw.textsize(text, font=font)

        h_pos = image.height // 8
        pos = ((image.width - w) // 2, h_pos)
        draw.text(pos, text=text, font=font, fill="white")

        return PILHelper.to_native_format(self.controller.deck, image)
        
    async def render(self):
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        day = now.day
        month = now.month

        async with self._lock:
            self._last = now

        button_6_label = self.button_6_label
        button_6_icon = self.button_6_icon

        return await asyncio.gather(
            self.render_clock_number(hour),
            self.render_clock_number(minute),
            self.render_image_from_file(None, None),
            self.render_clock_number(day),
            self.render_clock_number(month),
            self.render_image_from_file(button_6_icon, button_6_label)
        )

    button_6 = BackAction()

    async def heartbeat(self):
        render_num = self.render_clock_number
        ref_time = datetime.datetime.now()
        next_minute_image = None
        next_hour_image = None

        LOGGER.debug("Entering heartbeat loop")
        while True:
            try:
                minute = ref_time.minute + 1
                next_minute = minute % 60

                update_hour = minute // 60
                next_hour = (ref_time.hour + update_hour) % 24
                LOGGER.debug(f"Heartbeat: {next_minute=}, {next_hour=}")

                next_minute_image = await render_num(next_minute)
                LOGGER.debug(f"Rendering minute {next_minute}")
                if update_hour:
                    LOGGER.debug(f"Rendering hour {next_hour}")
                    next_hour_image = await render_num(next_hour)

                ref_time = await wait_for_next_minute(ref_time)


                if ref_time.hour == 23 and ref_time.minute == 59:
                    await self.controller.maybe_update_deck(self)
                    continue

                LOGGER.debug("Rendering next minute")
                await self.controller.maybe_update_key(
                    self, MINUTE_KEY, next_minute_image
                )

                if update_hour:
                    LOGGER.debug("Rendering next hour")
                    await self.controller.maybe_update_key(
                        self, HOUR_KEY, next_hour_image
                    )
            except asyncio.CancelledError:
                break


            



