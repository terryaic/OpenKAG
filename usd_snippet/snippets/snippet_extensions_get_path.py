# Extensions/Get Extension Path
import omni.kit.app

manager = omni.kit.app.get_app().get_extension_manager()

# There could be multiple extensions with same name, but different version
# Extension id is: [ext name]-[ext version].
# Many functions accept extension id.
# You can get extension of enabled extension by name or by python module name:
ext_id = manager.get_enabled_extension_id("omni.kit.window.script_editor")
print(ext_id)
ext_id = manager.get_extension_id_by_module("omni.kit.window.script_editor")
print(ext_id)

# There are few ways to get fs path to extension:
print(manager.get_extension_path(ext_id))
print(manager.get_extension_dict(ext_id)["path"])
print(manager.get_extension_path_by_module("omni.kit.window.script_editor"))


