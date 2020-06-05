import asyncio
import datetime

import logging

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

from .base import Page, cache
from .commands import BackAction

LOGGER = logging.getLogger(__name__)

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

        text = str(number)

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
        last = datetime.datetime.now()
        next_minute_image = None
        next_hour_image = None
        while True:
            try:
                next_minute = (last.minute+1) % 60
                next_hour = (last.hour+1) % 24

                next_minute_image = await render_num(next_minute)
                if not next_minute:
                    next_hour_image = await render_num(next_hour)

                now = datetime.datetime.now()
                await asyncio.sleep(60 - now.second)
                if now.hour == 23 and now.minute == 59:
                    await self.controller.maybe_update_deck(self)
                    continue

                await self.controller.maybe_update_key(
                    self, 1, next_minute_image
                )

                if last.minute == 59:
                    await self.controller.maybe_update_key(
                        self, 0, next_hour_image
                    )
            except asyncio.CancelledError:
                break
            last = now
            



