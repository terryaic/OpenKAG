# Capture/Save the viewport to image
import asyncio
from omni.kit.viewport.utility import get_active_viewport
from omni.kit.widget.viewport.capture import FileCapture
viewport_api = get_active_viewport()
image_path = "e:/viewport-shot.png"
capture = viewport_api.schedule_capture(FileCapture(image_path))
captured_aovs = asyncio.ensure_future(capture.wait_for_result())
if captured_aovs:
  print(f'AOV "{captured_aovs}" was written to "{image_path}"')
else:
  print(f'No image was written to "{image_path}"')