

import abc
import asyncio
from asyncio.subprocess import DEVNULL

import logging

LOGGER = logging.getLogger(__name__)


async def launch_shell(self, cmd):
    LOGGER.info(f"Invoking shell command {cmd}")
    await asyncio.create_subprocess_shell(
                cmd=cmd,
                stderr=DEVNULL,
                stdout=DEVNULL,
                stdin=DEVNULL
          )

async def launch_process(self, app, *args):
    LOGGER.info(f"Starting application {app}")
    await asyncio.create_subprocess_exec(
                program=app,
                args=args,
                stderr=DEVNULL,
                stdout=DEVNULL,
                stdin=DEVNULL
          ) 


class MultiAction(abc.ABC):

    @abc.abstractmethod
    def short_press(self):
        pass

    @abc.abstractmethod
    def long_press(self):
        pass

class BackAction(MultiAction):

    def short_press(self):
        async def short_f(self):
            LOGGER.debug("Returning to previous page")
            await self.controller.return_to_previous_page()
        return short_f

    def long_press(self):
        async def long_f(self):
            LOGGER.debug("Returning to root page")
            await self.controller.return_to_root()
        return long_f