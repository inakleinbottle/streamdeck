import asyncio
import logging

import simpleobsws as obs

from .base import Page, create_action_method
from .commands import launch_shell
from .menu import MainMenuPage

LOGGER = logging.getLogger(__name__)


class MainPage(Page):
    """
    Main page for my StreamDeck
    """

    deck_type = "StreamDeckMini"

    button_1_label = "Terminal"
    button_2_label = "Clock"
    button_3_label = "Mute"
    button_4_label = "Menu"
    button_5_label = {
        "stopped": "Start/Record",
        "recording": "Pause",
        "paused": "Resume"
    }
    button_6_label = "Stop"

    button_1_icon = "terminal-code.png"
    button_2_icon = "clock.png"
    button_3_icon = "mic-on.png"
    button_4_icon = "navigation.png"
    button_5_icon = {
        "stopped": "play-record.png",
        "recording": "play-pause.png",
        "paused": "play-record.png"        
    }
    button_6_icon = "play-stop.png"

    def __init__(self, controller):
        super().__init__(controller)

        self.obs_state = "stopped"
        self.obs_ws = None
        
    async def render(self):

        async with self._lock:
            obs_state = self.obs_state

        button_1_label = self.button_1_label
        button_2_label = self.button_2_label
        button_3_label = self.button_3_label
        button_4_label = self.button_4_label
        button_5_label = self.button_5_label[obs_state]
        button_6_label = self.button_6_label

        button_1_icon = self.button_1_icon
        button_2_icon = self.button_2_icon
        button_3_icon = self.button_3_icon
        button_4_icon = self.button_4_icon
        button_5_icon = self.button_5_icon[obs_state]
        button_6_icon = self.button_6_icon

        return await asyncio.gather(
            self.render_image_from_file(button_1_icon, button_1_label),
            self.render_image_from_file(button_2_icon, button_2_label),
            self.render_image_from_file(button_3_icon, button_3_label),
            self.render_image_from_file(button_4_icon, button_4_label),
            self.render_image_from_file(button_5_icon, button_5_label),
            self.render_image_from_file(button_6_icon, button_6_label)
        )

    async def setup(self):
        LOGGER.info(f"Running page {self} setup")
        self.obs_ws = ws = obs.obsws(loop=self.controller.loop)
        ws.register(self.connection_lost_callback, "Exiting")
        ws.register(self.recording_started_callback, "RecordingStarted")
        ws.register(self.recording_paused_callback, "RecordingPaused")
        ws.register(self.recording_stopped_callback, "RecordingStopping")
        await self.connect_obs()


    async def obs_call(self, cmd, data=None):
        ws = self.obs_ws
        LOGGER.debug(f"Calling OBS command {cmd}")
        try:
            result = await ws.call(cmd, data)
        except obs.ConnectionFailure:
            LOGGER.error("Connection to OBS failed")
        except obs.MessageTimeout:
            LOGGER.error("Connection to OBS timed out")
        except obs.MessageFormatError:
            LOGGER.error("Incorrect OBS message format")
        else:
            if result["status"] == "error":
                LOGGER.error(f"OBS error: {result['error']}")

    async def connect_obs(self):
        """
        Connect to the OBS web socket
        """
        try:
            await self.obs_ws.connect()
            LOGGER.info("Connected to OBS")
            return True
        except ConnectionError:
            LOGGER.info("Connection to OBS failed")
        return False

    async def obs_conn_alive(self):
        try:
            return self.obs_ws.recv_task is not None
        except Exception as e:
            LOGGER.error(e)
            return False

    async def connection_lost_callback(self, data=None):
        LOGGER.info("OBS connection lost event callback")
        async with self._lock:
            await self.obs_ws.disconnect()
            self.obs_state = "stopped"
        await self.controller.update_deck()

    async def recording_started_callback(self, data=None):
        async with self._lock:
            LOGGER.info("Recording started event callback")
            self.obs_state = "recording"
        await self.controller.update_deck()

    async def recording_paused_callback(self, data=None):
        async with self._lock:
            LOGGER.info("Recording paused event callback")
            self.obs_state = "paused"
        await self.controller.update_deck()

    async def recording_stopped_callback(self, data=None):
        async with self._lock:
            LOGGER.info("Recording stopped event callback")
            self.obs_state = "stopped"
        await self.controller.update_deck()

    button_1 = create_action_method(launch_shell, "gnome-terminal")
    alt_button_1 = button_1

    async def button_2(self):
        """
        Display clock page
        """
        pass

    alt_button_2 = button_2

    async def button_3(self):
        """
        Mute microphone
        """
        pass

    alt_button_3 = button_3

    async def button_4(self):
        """
        Open main menu page
        """
        LOGGER.info("Loading menu page")
        await self.controller.set_next_page(MainMenuPage)

    alt_button_4 = button_4

    async def button_5(self):
        """
        Start/pause recording
        """

        LOGGER.info("Getting OBS state")
        async with self._lock:
            LOGGER.debug("Aquired lock")
            state = self.obs_state

        LOGGER.debug(f"Current OBS state {state}")
        if state == "stopped":
            LOGGER.info("Starting OBS recording")
            await self.obs_call("StartRecording")
        elif state == "paused":
            LOGGER.info("Resuming OBS recording")
            await self.obs_call("ResumeRecording")
        elif state == "recording":
            LOGGER.info("Pausing OBS recording")
            await self.obs_call("PauseRecording")

    alt_button_5 = button_5

    async def button_6(self):
        """
        Stop recording
        """
        await self.obs_call("StopRecording")

    alt_button_6 = button_6
