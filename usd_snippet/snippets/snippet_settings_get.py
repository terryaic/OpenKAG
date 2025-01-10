# Settings/Get Setting
import carb.settings

settings = carb.settings.get_settings()

# get a string
print(settings.get("/log/file"))

# get an array (tuple)
print(settings.get("/app/exts/folders"))

# get an array element syntax:
print(settings.get("/app/exts/folders/0"))

# get a whole dictionary
exts = settings.get("/app/exts")
print(exts)
print(exts["folders"])

# get `None` if doesn't exist
print(settings.get("/app/DOES_NOT_EXIST_1111"))
