


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