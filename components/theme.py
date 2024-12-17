from contextlib import contextmanager

from nicegui import ui

@contextmanager
def ui_frame(nav_name: str):
    ui.colors(primary='#6E93D6', secondary='#53B689', accent='#111B1E', positive='#53B689')
    with ui.header():
        ui.label('Capstone Automation Tool').classes('font-bold')
        ui.space()
        ui.label(nav_name)
        ui.space()
        