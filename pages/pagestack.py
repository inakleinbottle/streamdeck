
import asyncio
import logging
import inspect


from collections import defaultdict
from typing import Dict, List, Optional, Union, TYPE_CHECKING, DefaultDict


from pages.base import Page


LOGGER = logging.getLogger(__name__)


class PageStack:
    """
    Holds the currently active pages in a stack and handles heartbeat
    tasks and other watcher tasks associated with the active pages.

    The idea here is to streamline the finding and loading of pages
    in a more efficient way. The page stack will keep a list (stack)
    of the currently active pages. Moving to a new page will correspond
    to pushing a new page object to the stack, and returning to the 
    previous pages corresponds to popping the top page from the stack.
    With this approach, we can ensure that all the tasks and handlers
    that are associated with a given page are started and cancelled
    gracefully, and without the need for the controller object.

    The advantage of this method is that we can not only move up and
    down the page stack by 1 position, but we can also quickly return
    to any specified position and remove all loaded pages above.

    The stack will hold a root page that will always be on the stack
    and cannot be removed. This represents the starting or default page
    that should be displayed if a requested page cannot be found.
    """

    def __init__(self, controller: "Controller", root: Page):
        self._lock = asyncio.Lock()
        self._root = root

        self._stack: List[Page] = [root]
        self._tasks: DefaultDict[str, List[asyncio.Task]] = defaultdict(default_factory=[])


    async def find_page(self, name):
        """
        Attempt to load the page with the given name.
        """
        pass

    async def _push(self, page):
        self._stack.append(page)

    async def push(self, page: Page):
        """
        Push a new page to the stack.

        The name of the page should be provided. 
        """
        async with self._lock:
            await self._push(page)

    async def cancel_jobs_for_page(self, page):
        """
        Cancel all active jobs for a page.
        """
        if isinstance(page, str):
            name = page
        elif isinstance(page, Page):
            name = page.__class__.__name__
        else:
            raise TypeError("Page must be either a Page instance or str")

        async with self._lock:
            tasks = self._tasks[name]

            for task in tasks:
                task.cancel()



    async def pop(self):
        """
        Pop the top page from the stack.

        Pop the page from the stack and unload all of the tasks
        associated with this page.
        """

        async with self._lock:
            if len(self._stack) > 1:
                page = self._stack.pop()
            else:
                # Cannot remove root page
                LOGGER.warning("Cannot remove root page from stack")
                return

        async with self._lock:
            tasks = self._tasks[page.__class__.__name__]

        for task in tasks:
            try:
                task.cancel()
            except Exception as e:
                LOGGER.debug("An exception occurred whist cancelling task")
                LOGGER.debug(e)
        



        




