# Extensions/Get All Extensions
import omni.kit.app

# there are a lot of extensions, print only first N entries in each loop
PRINT_ONLY_N = 10

# get all registered local extensions (enabled and disabled)
manager = omni.kit.app.get_app().get_extension_manager()
for ext in manager.get_extensions()[:PRINT_ONLY_N]:
    print(ext["id"], ext["package_id"], ext["name"], ext["version"], ext["path"], ext["enabled"])

# get all registered non-local extensions (from the registry)
# this call blocks to download registry (slow). You need to call it at least once, or use refresh_registry() for non-blocking.
manager.sync_registry()
for ext in manager.get_registry_extensions()[:PRINT_ONLY_N]:
    print(ext["id"], ext["package_id"], ext["name"], ext["version"], ext["path"], ext["enabled"])

# functions above print all versions of each extension. There is other API to get them grouped by name (like in ext manager UI).
# "enabled_version" and "latest_version" contains the same dict as returned by functions above, e.g. with "id", "name", etc.
for summary in manager.fetch_extension_summaries()[:PRINT_ONLY_N]:
    print(summary["fullname"], summary["flags"], summary["enabled_version"]["id"], summary["latest_version"]["id"])

# get all versions for particular extension
for ext in manager.fetch_extension_versions("omni.kit.window.script_editor"):
    print(ext["id"])

