# Settings/Subscribe To Setting Changes
import carb.settings
import omni.kit.app

settings = carb.settings.get_settings()

def on_change(value, change_type: carb.settings.ChangeEventType):
    print(value, change_type)

# subscribe to value changes, returned object is subscription holder. To unsubscribe - destroy it.
subscription1 = omni.kit.app.SettingChangeSubscription("/exts/your.ext.name/test/test/value", on_change)

settings.set("/exts/your.ext.name/test/test/value", 23)
settings.set("/exts/your.ext.name/test/test/value", "fall")
settings.set("/exts/your.ext.name/test/test/value", None)
settings.set("/exts/your.ext.name/test/test/value", 89)
subscription1 = None # no more notifications
settings.set("/exts/your.ext.name/test/test/value", 100)

