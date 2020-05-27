


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