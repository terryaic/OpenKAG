# Extensions/Enable Extension
import omni.kit.app

manager = omni.kit.app.get_app().get_extension_manager()

# enable immediately
manager.set_extension_enabled_immediate("omni.kit.window.about", True)
print(manager.is_extension_enabled("omni.kit.window.about"))

# or next update (frame), multiple commands are be batched
manager.set_extension_enabled("omni.kit.window.about", True)
manager.set_extension_enabled("omni.kit.window.console", True)
