from nicegui import ui

def err_dialog(err: str, msg: str):
    with ui.dialog() as dialog, ui.card().classes('w-[300px] h-[150px]'):
        with ui.row().classes('mx-auto'):
            ui.label(f'{err}').classes('justify-center bold')

        with ui.row().classes('mx-auto'):
            ui.label(f'{msg}').classes('justify-start')

        with ui.row().classes('mx-auto'):
            ui.button('OK', on_click=dialog.close).classes('justify-center')

        return dialog

def gen_dialog(msg: str):
    with ui.dialog() as dialog, ui.card().classes('w-[300px] h-[150px]'):
        with ui.grid(columns='80px 1fr').classes('mx-auto'):
            ui.label('MSG:')
            ui.label(msg)
        
            ui.button('OK', on_click=dialog.close).classes('justify-center')
        return dialog