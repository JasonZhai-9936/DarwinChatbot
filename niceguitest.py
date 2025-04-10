from nicegui import ui

ui.label('Test app running!')
ui.run(host='0.0.0.0', port=8080, show=False)
print("\n\nAccess your app at: http://[your-pod-id].runpod.io:8080\n\n")