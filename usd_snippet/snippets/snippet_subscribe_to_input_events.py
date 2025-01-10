# App/Subscribe to Input Event
import carb.imgui
import carb.windowing
import carb.input
import omni.appwindow

appwindow = omni.appwindow.get_default_app_window()
keyboard = appwindow.get_keyboard()


def on_input(e):
	print("{} ({})".format(e.input, e.type))
	return True


input = carb.input.acquire_input_interface()
keyboard_sub_id = input.subscribe_to_keyboard_events(keyboard, on_input)
