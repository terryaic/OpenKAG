# change or Switch camera in the viewport
def switch_camera(camera_path):
    from omni.kit.viewport.utility import get_active_viewport
    # get the active viewport first.
    viewport = get_active_viewport()
    if not viewport:
        print("No active Viewport")
        return
    # then set the Viewport's active camera to the one just created
    viewport.camera_path = camera_path

# Switch camera to the current selected prim
import omni.usd
stage = omni.usd.get_context().get_stage()
selections = omni.usd.get_context().get_selection().get_selected_prim_paths()
switch_camera(selections[0])