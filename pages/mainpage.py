import asyncio

from .base import Page



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

    async def __init__(self, controller):
        super().__init__(controller)

        self.obs_state = "stopped"
        
    async def render(self):

        with self._lock:
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

        images = await asyncio.gather(
            self.render_image_from_file(button_1_icon, button_1_label),
            self.render_image_from_file(button_2_icon, button_2_label),
            self.render_image_from_file(button_3_icon, button_3_label),
            self.render_image_from_file(button_4_icon, button_4_label),
            self.render_image_from_file(button_5_icon, button_5_label),
            self.render_image_from_file(button_6_icon, button_6_label)
        )
        
        await asyncio.gather(
            *[self.controller.set_image(i, image)
            for i, image in enumerate(images)]
        )


    async def button_1(self):
        """
        Open new terminal
        """
        pass

    async def button_2(self):
        """
        Display clock page
        """
        pass

    async def button_3(self):
        """
        Mute microphone
        """
        pass

    async def button_4(self):
        """
        Open main menu page
        """
        pass

    async def button_5(self):
        """
        Start/pause recording
        """
        pass

    async def button_6(self):
        """
        Stop recording
        """
        pass

