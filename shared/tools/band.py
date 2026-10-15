"""Which Minecraft band the tools are looking at, that band's properties, and the shared source layers.

A folder that builds several bands (1.21/ and 26.x/, with versions/<band>.properties picked by -Pmc)
needs to be told which one: pass `--mc <band>` to any tool, or set SO_MC. A folder with no versions/
is one band, and gradle.properties alone describes it.

The band's file is read OVER gradle.properties, exactly as settings.gradle does for the build.

    import band
    band.band_name()             # '1.21.4', '1.20.1', '26.x': the name era folders use
    band.shared_layers('fabric') # the shared/ folders this module takes in this band

Importing this module also installs an open() hook: a `<module>/src/main/<rest>` path that does not
exist is resolved to the first layer that holds it (this band's era folders, then shared/), so a tool
written against src/main keeps working when a file moves into a shared layer.
"""
import builtins
import functools
import io
import os
import sys

# The band folder the tools look at: SO_BAND_ROOT, or the working directory.
ROOT = os.path.abspath(os.environ.get("SO_BAND_ROOT") or os.getcwd())
if not os.path.isfile(os.path.join(ROOT, "settings.gradle")):
    sys.exit(f"run the tools from a toolchain folder (1.20.1, 1.21, 26.x), not {ROOT}")
SHARED = os.path.join(os.path.dirname(ROOT), "shared")
VERSIONS = os.path.join(ROOT, "versions")


def _read(path):
    out = {}
    with io.open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def _take_mc():
    """--mc from the command line (removed, so a tool's own arguments are unaffected), or SO_MC."""
    if "--mc" in sys.argv:
        i = sys.argv.index("--mc")
        if i + 1 >= len(sys.argv):
            sys.exit("--mc needs a band")
        value = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        os.environ["SO_MC"] = value
        return value
    return os.environ.get("SO_MC")


MC = _take_mc()


def known():
    if not os.path.isdir(VERSIONS):
        return []
    return sorted(f[:-len(".properties")] for f in os.listdir(VERSIONS) if f.endswith(".properties"))


@functools.lru_cache(maxsize=None)
def _props():
    out = _read(os.path.join(ROOT, "gradle.properties"))
    if known():
        if MC not in known():
            sys.exit(f"this folder builds several bands; pass --mc with one of {', '.join(known())}")
        out.update(_read(os.path.join(VERSIONS, MC + ".properties")))
    return out


def props():
    return dict(_props())


def band_name():
    """This band's exact name, as era folders spell it: version_band (26.x), else the version label,
    else minecraft_version (1.20.1, and each band of 1.21/)."""
    p = props()
    return p.get("version_band") or p.get("minecraft_version_label") or p.get("minecraft_version")


def _names(d):
    return os.path.basename(d).split("+")


def _dirs(parent):
    if not os.path.isdir(parent):
        return []
    return sorted(os.path.join(parent, d) for d in os.listdir(parent) if os.path.isdir(os.path.join(parent, d)))


def era_dirs(module_dir):
    """A module's own era folders for this band: src/<x> where x, split on '+', names the band (1.21/)."""
    this = band_name()
    return [d for d in _dirs(os.path.join(module_dir, "src"))
            if os.path.basename(d) != "main" and this in _names(d)]


def shared_layers(module):
    """The shared folders this module takes in this band, as shared-sources.gradle adds them:
    shared/loaders/<loader>[+<loader>], shared/eras/<bands>/<module>[+<module>], then this toolchain
    folder's own <a>+<b>/src/<main|era>. Each holds java/ and resources/."""
    this = band_name()
    out = []
    if module != "common":
        out += [d for d in _dirs(os.path.join(SHARED, "loaders")) if module in _names(d)]
    for era in _dirs(os.path.join(SHARED, "eras")):
        if this in _names(era):
            out += [d for d in _dirs(era) if module in _names(d)]
    for group in _dirs(ROOT):
        if "+" in os.path.basename(group) and module in _names(group):
            out += [d for d in _dirs(os.path.join(group, "src"))
                    if os.path.basename(d) == "main" or this in _names(d)]
    return out


def layers(module_main):
    """Every folder a module's src/main is spread over in this band, widest last."""
    module_dir = os.path.dirname(os.path.dirname(os.path.normpath(module_main)))
    module = os.path.basename(module_dir)
    out = [module_main] + era_dirs(module_dir) + shared_layers(module)
    if module == "common":
        out.append(SHARED)
    return out


# ---------------------------------------------------------------- the open() hook
_SEP = os.sep + "src" + os.sep + "main" + os.sep
_real_exists = os.path.exists
_real_isfile = os.path.isfile
_real_open = builtins.open
_real_io_open = io.open


def resolve(path):
    if not isinstance(path, (str, os.PathLike)):
        return path
    text = os.path.normpath(os.path.abspath(os.fspath(path)))
    if _SEP not in text or _real_exists(text):
        return path
    module_main, rest = text.split(_SEP, 1)
    module_main += os.sep + "src" + os.sep + "main"
    for layer in layers(module_main)[1:]:
        candidate = os.path.join(layer, rest)
        if _real_exists(candidate):
            return candidate
    return path


def _install():
    os.path.exists = lambda p: _real_exists(resolve(p))
    os.path.isfile = lambda p: _real_isfile(resolve(p))
    builtins.open = lambda p, *a, **k: _real_open(resolve(p), *a, **k)
    io.open = lambda p, *a, **k: _real_io_open(resolve(p), *a, **k)


_install()
