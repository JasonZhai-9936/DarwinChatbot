from nicegui import ui

def test_nicegui():
    ui.label('Hello from NiceGUI!')
    ui.button('Click me', on_click=lambda: ui.notify('Button clicked!'))

test_nicegui()
ui.run(port=8080)