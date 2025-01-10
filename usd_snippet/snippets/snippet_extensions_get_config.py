# Extensions/Get Extension Config
import omni.kit.app

manager = omni.kit.app.get_app().get_extension_manager()

# There could be multiple extensions with same name, but different version
# Extension id is: [ext name]-[ext version].
# Many functions accept extension id:
ext_id = manager.get_enabled_extension_id("omni.kit.window.script_editor")
data = manager.get_extension_dict(ext_id)

# Extension dict contains whole extension.toml as well as some runtime data:
# package section
print(data["package"])
# is enabled?
print(data["state/enabled"])
# resolved runtime dependencies
print(data["state/dependencies"])
# time it took to start it (ms)
print(data["state/startupTime"])

# can be converted to python dict for convenience and to prolong lifetime
data = data.get_dict()
print(type(data))

