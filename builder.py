# Components v2 builder

import discord
from discord import ui


SEP = ui.Separator

ACTIONROW_ELEMENTS = [
    ui.Button,
    ui.Select,
    ui.RoleSelect,
    ui.ChannelSelect,
    ui.UserSelect,
    ui.MentionableSelect
]


def to_container(elements: list, accent_color: discord.Color = None, spoiler: bool = False, no_container: bool = False) -> ui.Container:
    '''
    Converts a list of elements into a view.
    '''
    view = ui.Container(accent_color=accent_color, spoiler=spoiler)
    if no_container:
        view = ui.LayoutView(timeout=None)

    if isinstance(elements, str):
        view.add_item(ui.TextDisplay(elements))
        return view
    
    if not isinstance(elements, list):
        elements = [elements]

    for i in elements:
        if i is None:
            continue
        elif isinstance(i, str):
            view.add_item(ui.TextDisplay(i))
        elif isinstance(i, list):
            view.add_item(ui.ActionRow(*i))
        elif any([isinstance(i, element) for element in ACTIONROW_ELEMENTS]):
            row = ui.ActionRow()
            row.add_item(i)
            view.add_item(row)
        else:
            view.add_item(i)

    return view


def add_accessory(elements: list, accessory: ui.Item) -> ui.Section:
    items = [
        ui.TextDisplay(i) if isinstance(i, str) else None if i is None else i
        for i in elements
    ]
    return ui.Section(*items, accessory=accessory)


def to_view(elements: list, accent_color: discord.Color = None, spoiler: bool = False, text: str = None) -> ui.View:
    view = ui.LayoutView(timeout=None)
    c = to_container(elements, accent_color, spoiler)
    if text:
        view.add_item(ui.TextDisplay(text))
    view.add_item(c)
    return view


def c_to_view(c: ui.Container, text: str = None) -> ui.View:
    view = ui.LayoutView(timeout=None)
    if text:
        view.add_item(ui.TextDisplay(text))
    view.add_item(c)
    return view