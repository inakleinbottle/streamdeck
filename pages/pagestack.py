
import asyncio
import logging
import inspect
from enum import Enum


from collections import defaultdict
from typing import Dict, List, Optional, Union, TYPE_CHECKING, DefaultDict


from pages.base import Page

if TYPE_CHECKING:
    from controller import Controller


LOGGER = logging.getLogger(__name__)


class PageState(Enum):
    """
    Status of a page.

    Inactive means the page is not currently on the stack.
    Loaded means the page is on the stack but not at the top.
    Active means the page is on top of the stack.
    """
    Inactive = 0
    Loaded = 1
    Active = 2


class PageStack:
    """
    Holds the currently active pages in a stack and handles heartbeat
    tasks and other watcher tasks associated with the active pages.

    The idea here is to streamline loading of pages. The page stack will 
    keep a list (stack) of the currently active pages. Moving to a new 
    page will correspond to pushing a new page object to the stack, and 
    returning to the previous pages corresponds to popping the top page 
    from the stack. With this approach, we can ensure that all the tasks
    and handlers that are associated with a given page are started and 
    cancelled gracefully, and without the need for the controller object.

    The advantage of this method is that we can not only move up and
    down the page stack by 1 position, but we can also quickly return
    to any specified position and remove all loaded pages above.

    The stack will hold a root page that will always be on the stack
    and cannot be removed. This represents the starting or default page
    that should be displayed if a requested page cannot be found.
    """

    _stack: List[Page]
    _tasks: DefaultDict[str, List[asyncio.Task]]

    def __init__(self, root: Page):
        self._lock = asyncio.Lock()
        self._root = root

        self._stack = []
        self._tasks = defaultdict(list)
        self._push(root)

    def _push(self, page):

        LOGGER.debug(f"Pushing {page} to stack")

        self._stack.append(page)
        name = page.__class__.__name__

        LOGGER.debug(f"Setting up heartbeat task")
        task = asyncio.create_task(page.heartbeat())
        self._tasks[name].append(task)

        LOGGER.debug(f"Setting up background tasks")
        new_tasks = page.get_background_jobs()
        self._tasks[name].extend(new_tasks)

    async def current_page(self):
        """
        Get the active page.
        """
        LOGGER.debug("Getting active page")
        async with self._lock:
            return self._stack[-1]

    async def get_status(self, page: Page) -> PageState:
        """
        Determine the status of a page.

        This is used to control the updating of the deck according to
        the current state of the page.
        """
        LOGGER.debug(f"Getting status for page {page}")
        async with self._lock:
            if self._stack[-1] is page:
                # The most important case is when the page is active,
                # because this means something needs to be done to the
                # deck in most cases. Do this first.
                return PageState.Active
            
            if page in self._stack:
                return PageState.Loaded
            
            return PageState.Inactive

    async def push(self, page: Page):
        """
        Push a new page to the stack.

        The name of the page should be provided. 
        """
        LOGGER.debug(f"Pushing page {page} onto stack")
        async with self._lock:

            if page is self._stack[-1]:
                LOGGER.debug(f"Page {page} currently active")
                return

            self._push(page)

    async def cancel_jobs_for_page(self, page):
        """
        Cancel all active jobs for a page.
        """
        LOGGER.debug(f"Cancelling jobs for page {page}")
        if isinstance(page, str):
            name = page
        elif isinstance(page, Page):
            name = page.__class__.__name__
        else:
            raise TypeError("Page must be either a Page instance or str")

        async with self._lock:
            tasks = self._tasks.pop(name)

            for task in tasks:
                task.cancel()

    async def pop(self):
        """
        Pop the top page from the stack.

        Pop the page from the stack and unload all of the tasks
        associated with this page.
        """
        LOGGER.debug(f"Popping active page from stack")
        async with self._lock:
            if len(self._stack) > 1:
                page = self._stack.pop()
            else:
                # Cannot remove root page
                LOGGER.warning("Cannot remove root page from stack")
                return

        await self.cancel_jobs_for_page(page)
        
    async def pop_all(self, bottom=1):
        """
        Pop all pages back to the root page.
        """
        LOGGER.debug("Popping all pages from stack")
        async with self._lock:
            while len(self._stack) > bottom:
                await self.pop()
