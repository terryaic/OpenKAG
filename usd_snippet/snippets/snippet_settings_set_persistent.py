# Settings/Set Persistent Setting
import carb.settings

settings = carb.settings.get_settings()

# all settings stored under "/persistent" saved between sessions
# run that snippet again after restarting an app to see that value is still there:
key = "/persistent/exts/your.ext.name/test/value"
print("{}: {}".format(key, settings.get(key)))
settings.set(key, "string from previous session")

# Below is a setting with location of a file where persistent settings are stored.
# To reset settings: delete it or run kit with `--reset-user`
print("persistent settings are stored in: {}".format(settings.get("/app/userConfigPath")))

