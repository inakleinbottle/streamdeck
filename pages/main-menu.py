from pages.buttons import Button, CommandButton, MenuButton, BackButton
from pages.page import Page


class TempBackButton(MenuButton):
    icon = "terminal-code.png"
    text = "Back"
    menu_name = "main"


class SteamButton(Button):
    icon = "steam_tray.ico"
    text = "Steam"


PAGE = Page(
    "Main menu",
    SteamButton,
    TempBackButton,
    TempBackButton,
    TempBackButton,
    TempBackButton,
    BackButton,
)