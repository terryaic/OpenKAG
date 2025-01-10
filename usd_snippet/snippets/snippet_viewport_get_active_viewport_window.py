# Viewport/Get the active ViewportWindow
from omni.kit.viewport.utility import get_active_viewport_window

#
# Get the default Viewport window
viewport_window = get_active_viewport_window()

print("")
print(f"Active ViewportWindow is {viewport_window}")
print(f"Viewport is available with .viewport_api, its resolution is: {viewport_window.viewport_api.resolution}")

# get_active_viewport_window can fail if querying for a specific ViewportWindow that doesn't exists
non_existant_viewport_window_name = "This Viewport Doesn't Exist"
non_existant_viewport_window = get_active_viewport_window(window_name=non_existant_viewport_window_name)

print("")
print(f"Viewport window named {non_existant_viewport_window_name} is {non_existant_viewport_window}")
