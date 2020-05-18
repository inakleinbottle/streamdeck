import logging
import simpleobsws as obs

from pages.buttons import (
    Button, CommandButton, MenuButton, StatefulButton
)
from pages.page import Page

LOGGER = logging.getLogger(__name__)

class TerminalButton(CommandButton):
    icon = "terminal-code.png"
    text = "Terminal"
    command = "gnome-terminal"


class ClockButton(Button):
    icon = "clock.png"
    text = "Clock"


class MicButton(Button):
    icon = "mic-on.png"
    text = "Microphone"
    

class MainMenuButton(MenuButton):
    icon = "navigation.png"
    text = "Menu"
    menu_name = "main-menu"


class PlayRecordButton(StatefulButton):
    states = {
        "stopped": ("play-record.png", "Play/Record"),
        "recording": ("play-pause.png", "Pause"),
        "paused": ("play-record.png", "Resume")
    }
    default_state = "stopped"

    async def setup(self, controller, page):
        self.page = page

    async def obs_call(self, cmd, data=None):
        ws = self.page.obs_ws
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
          

    async def action(self, deck, state, controller, page):
        LOGGER.info("Calling Play/Pause action")
        if not state:
            return await super().action(deck, state, controller, page)
        
        if not await self.page.obs_conn_alive():
            connected = await self.page.connect_obs()
            if not connected:
                LOGGER.info("No OBS connection, returning")
                return await super().action(deck, state, controller, page)

        if self.state == "stopped":
            LOGGER.info("Starting OBS recording")
            await self.obs_call("StartRecording")
        elif self.state == "paused":
            LOGGER.info("Resuming OBS recording")
            await self.obs_call("ResumeRecording")
        elif self.state == "recording":
            LOGGER.info("Pausing OBS recording")
            await self.obs_call("PauseRecording")
        return await super().action(deck, state, controller, page)


class PlayStopButton(Button):
    icon = "play-stop.png"
    text = "Stop"

    async def setup(self, controller, page):
        self.page = page

    async def obs_call(self, cmd, data=None):
        ws = self.page.obs_ws
        try:
            await ws.call(cmd, data)
        except obs.ConnectionFailure:
            LOGGER.error("Connection to OBS failed")
        except obs.MessageTimeout:
            LOGGER.error("Connection to OBS timed out")
        except obs.MessageFormatError:
            LOGGER.error("Incorrect OBS message format")


    async def action(self, deck, state, controller, page):
        if not state:
            return await super().action(deck, state, controller, self)
        
        await self.obs_call("StopRecording")
        return await super().action(deck, state, controller, page)



class MainPage(Page):

    async def connection_lost_callback(self, data=None):
        LOGGER.info("OBS connection lost event callback")
        await self.obs_ws.disconnect()
        self.buttons[4].state = self.buttons[4].default_state
        await self.controller.update_deck()
        self.obs_ws = None

    async def recording_started_callback(self, data=None):
        LOGGER.info("Recording started event callback")
        self.buttons[4].state = "recording"
        await self.controller.update_deck()

    async def recording_paused_callback(self, data=None):
        LOGGER.info("Recording paused event callback")
        self.buttons[4].state = "paused"
        await self.controller.update_deck()

    async def recording_stopped_callback(self, data=None):
        LOGGER.info("Recording stopped event callback")
        self.buttons[4].state = "stopped"
        await self.controller.update_deck()

    async def connect_obs(self):
        try:
            await self.obs_ws.connect()
            LOGGER.info("Connected to OBS")
            return True
        except ConnectionError:
            LOGGER.info("Connection to OBS failed")
        return False
        

    async def setup(self, controller):
        await super().setup(controller)

        self.obs_ws = ws = obs.obsws(loop=controller.loop)
        ws.register(self.connection_lost_callback, "Exiting")
        ws.register(self.recording_started_callback, "RecordingStarted")
        ws.register(self.recording_paused_callback, "RecordingPaused")
        ws.register(self.recording_stopped_callback, "RecordingStopping")
        await self.connect_obs()

    async def obs_conn_alive(self):
        return self.obs_ws.recv_task is not None

    async def heartbeat(self, deck, controller):
        LOGGER.info("Running Main page heartbeat")
        await self.connect_obs()
        await super().heartbeat(deck, controller)


PAGE = MainPage(
    "Main",
    TerminalButton,
    ClockButton,
    MicButton,
    MainMenuButton,
    PlayRecordButton,
    PlayStopButton
)