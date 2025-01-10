# PIP/Install pip package

# omni.kit.pipapi extension is required
import omni.kit.pipapi

# It wraps `pip install` calls and reroutes package installation into user specified environment folder.
# That folder is added to sys.path.
# Note: This call is blocking and slow. It is meant to be used for debugging, development. For final product packages
# should be installed at build-time and packaged inside extensions.
omni.kit.pipapi.install(
    package="semver",
    version="2.13.0",
    module="semver", # sometimes module is different from package name, module is used for import check
    ignore_import_check=False,
    ignore_cache=False,
    use_online_index=True,
    surpress_output=False,
    extra_args=[]
)

# use
import semver
ver = semver.VersionInfo.parse('1.2.3-pre.2+build.4')
print(ver)
