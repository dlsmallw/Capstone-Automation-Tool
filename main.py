from backend import dialog

from nicegui import ui

ui.button('Test General Dialog', on_click=dialog.gen_dialog('TEST DIALOG').open)
ui.button('Test Error Dialog', on_click=dialog.err_dialog('TEST ERR', 'TEST ERROR MSG').open)

ui.run(native=True)