# shared/

Files that are byte-identical in every band that uses them live here once, instead of once per
toolchain folder. A file belongs here only when it is identical in every band named by its folder;
anything that differs in even one band stays in that band's own source tree.

| Folder | Taken by |
|---|---|
| `java/`, `resources/` | every band and every loader (added by each `common/build.gradle`) |
| `textures/` | a pool of overlay art, not a resource root: each band copies only the files its models name (`gradle/texture-pool.gradle`) |
| `loaders/<loader>/` | every band of that loader: `fabric`, `forge`, `neoforge` |
| `loaders/<a>+<b>/` | every band of both loaders |
| `eras/<bands>/<module>/` | only the bands named, joined by `+`; the module may name several loaders (`fabric+forge`) |
| `gradle/` | script plugins the bands apply |
| `tools/` | Python the bands' tools import |

Bands are named exactly, never by toolchain folder: `1.20.1`, `1.21.1`, `1.21.4`, `1.21.11`, `26.x`.
So `eras/1.21.1+1.21.4+1.21.11+26.x/common` is common code for those four bands and no other.

Something several loaders of ONE toolchain folder share stays inside that folder, as
`<toolchain>/<a>+<b>/src/<main or band>/java`, like `cloth-config/`.

## How a band picks its folders

`gradle/shared-sources.gradle` decides, and every module's `build.gradle` applies it. It reads the
band's name (`version_band`, else `minecraft_version_label`, else `minecraft_version`) and adds, as
source folders, each `loaders/` folder naming the module, each `eras/` folder naming the band, and
the toolchain's own `<a>+<b>/src/{main,<band>}` folders. `tools/band.py` mirrors the same rules
(`band_name()`, `shared_layers(module)`), so the build tools find a file wherever it lives.

## Moving a file here

Build every band first and keep the jars. Move the file, rebuild, and compare every shipped jar entry
for entry with `tools/jardiff.py <before> <after>`: nothing may be added, removed or changed.
