# Settings/Set Setting
import carb.settings

settings = carb.settings.get_settings()

# set different types into different keys
# guideline: each extension puts settings in /ext/[ext name]/ and lists them extension.toml for discoverability
settings.set("/exts/your.ext.name/test/value_int", 23)
settings.set("/exts/your.ext.name/test/value_float", 502.45)
settings.set("/exts/your.ext.name/test/value_bool", False)
settings.set("/exts/your.ext.name/test/value_str", "summer")
settings.set("/exts/your.ext.name/test/value_array", [9,13,17,21])
settings.set("/exts/your.ext.name/test/value_dict", { "a": 2, "b": "winter"})

# print all:
print(settings.get("/exts/your.ext.name/test"))
