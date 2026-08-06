# Seamless Ores

Ore blocks whose background matches the stone they generate in. Granite, diorite, andesite and tuff
variants for every overworld ore, plus basalt and blackstone in the Nether, Create's zinc, and Mythic
Upgrades' gems.

**In the Overworld it adds no ore.** The same veins, in the same places, drawn to fit their
surroundings. The Nether variants are the one exception, and they are config gated.

| | |
|---|---|
| Minecraft | 26.2 |
| Loaders | Fabric, NeoForge, Quilt (untested) |
| Wiki | https://chillpavz.com/seamless-ores |
| Licence | PolyForm Shield 1.0.0, see `LICENSE` |

An original mod. Not a fork or a port of any other project.

## Companion resource pack

**Seamless Glowing Ores** makes every ore glow, with an optional connected outline that joins
touching ore of the same type across different host stones.

## Block list

64 blocks in the `seamlessores` namespace.

**Vanilla, Overworld**

| | granite | diorite | andesite | tuff |
|---|---|---|---|---|
| Coal | `granite_coal_ore` | `diorite_coal_ore` | `andesite_coal_ore` | `tuff_coal_ore` |
| Copper | `granite_copper_ore` | `diorite_copper_ore` | `andesite_copper_ore` | `tuff_copper_ore` |
| Iron | `granite_iron_ore` | `diorite_iron_ore` | `andesite_iron_ore` | `tuff_iron_ore` |
| Gold | `granite_gold_ore` | `diorite_gold_ore` | `andesite_gold_ore` | `tuff_gold_ore` |
| Redstone | `granite_redstone_ore` | `diorite_redstone_ore` | `andesite_redstone_ore` | `tuff_redstone_ore` |
| Lapis | `granite_lapis_ore` | `diorite_lapis_ore` | `andesite_lapis_ore` | `tuff_lapis_ore` |
| Diamond | `granite_diamond_ore` | `diorite_diamond_ore` | `andesite_diamond_ore` | `tuff_diamond_ore` |
| Emerald | `granite_emerald_ore` | `diorite_emerald_ore` | `andesite_emerald_ore` | `tuff_emerald_ore` |

**Vanilla, Nether**

| | basalt | blackstone |
|---|---|---|
| Gold | `basalt_gold_ore` | `blackstone_gold_ore` |
| Quartz | `basalt_quartz_ore` | `blackstone_quartz_ore` |

**Create, requires `create`**

| | granite | diorite | andesite | tuff |
|---|---|---|---|---|
| Zinc | `granite_zinc_ore` | `diorite_zinc_ore` | `andesite_zinc_ore` | `tuff_zinc_ore` |

**Mythic Upgrades, requires `mythicupgrades`**

| | granite | diorite | andesite | tuff |
|---|---|---|---|---|
| Aquamarine | `granite_aquamarine_ore` | `diorite_aquamarine_ore` | `andesite_aquamarine_ore` | `tuff_aquamarine_ore` |
| Citrine | `granite_citrine_ore` | `diorite_citrine_ore` | `andesite_citrine_ore` | `tuff_citrine_ore` |
| Peridot | `granite_peridot_ore` | `diorite_peridot_ore` | `andesite_peridot_ore` | `tuff_peridot_ore` |
| Topaz | `granite_topaz_ore` | `diorite_topaz_ore` | `andesite_topaz_ore` | `tuff_topaz_ore` |
| Necoium | `granite_necoium_ore` | `diorite_necoium_ore` | `andesite_necoium_ore` | `tuff_necoium_ore` |

| | basalt | blackstone |
|---|---|---|
| Ruby | `basalt_ruby_ore` | `blackstone_ruby_ore` |
| Sapphire | `basalt_sapphire_ore` | `blackstone_sapphire_ore` |

The modded variants are not registered when their mod is absent, so the counts are 60 without Create
(which is Fabric only at 26.2), 40 without Mythic Upgrades, and 36 with neither. The registered block
set is derived from which mods are loaded rather than from config, so a client and a server running
the same mods always agree and nobody is kicked on join.

Mythic Upgrades' ametrine and jade are deliberately absent: they are `block_match end_stone`, and the
End has no second stone type, so there is nothing to be seamless with.

## For resource pack authors

Every variant of one ore shares a single overlay texture, so supporting all 64 blocks takes **18 PNG
files**:

```
assets/seamlessores/textures/block/<ore>_overlay.png
```

where `<ore>` is one of `coal`, `copper`, `iron`, `gold`, `redstone`, `lapis`, `diamond`, `emerald`,
`nether_gold`, `quartz`, `zinc`, `aquamarine`, `citrine`, `peridot`, `topaz`, `necoium`, `ruby`,
`sapphire`.

Each file is the ore layer only, blobs on transparency. The host stone is referenced straight from
vanilla, so you do not supply it, and if your pack retextures granite then these blocks pick that up
automatically.

## Building

Requires JDK 25.

```
./gradlew build
```

Jars land in `fabric/build/libs` and `neoforge/build/libs`. Take the plain jar, not the `-sources` or
`-javadoc` one. Fabric Loader rejects the sources jar, because its metadata still holds unexpanded
build placeholders.

Assets, loot tables and tags are generated rather than hand written:

```
py -3.14 tools/generate_assets.py
```

It is idempotent and does not touch textures unless you pass `--textures`, which overwrites the hand
cleaned overlays.

## Project layout

| Path | What it holds |
|---|---|
| `common/` | Everything shared: content registration, worldgen injection, config holder |
| `fabric/`, `neoforge/` | Loader entry points and the Cloth Config data class |
| `tools/generate_assets.py` | Generates blockstates, models, lang, loot tables and tags |

The two loader config classes are duplicated on purpose and must stay identical. Cloth Config cannot
live in `common`, because loader dependencies are not on its classpath.

## How it works, briefly

Seamless Ores does not add worldgen features. At server start it extends the target lists of the ore
features that already exist, adding one entry per host stone ahead of vanilla's. The game then picks
the ore texture from the block that was actually at each position, which is why distribution is
unchanged and why veins blend across a stone boundary by themselves.

Patching the live registry rather than shipping replacement JSON files is deliberate: it composes
with worldgen overhauls and ore datapacks instead of overwriting them.

The two exceptions, both config gated and both stated on the store page: basalt and blackstone gold
and quartz add ore, because vanilla's Nether features match netherrack only; and Mythic Upgrades'
ruby and sapphire in basalt deltas are placed by a feature of ours, because that mod restricts its
own ore to a single biome and there was nothing to extend.

Full detail is on the wiki.

## Credits

The ore overlays are derived from Minecraft's own textures and remain Mojang's property. The zinc
overlay is derived from Create, which is CC0 and MIT licensed. The Mythic Upgrades overlays are
derived from Mythic Upgrades by TriQue, which is MIT licensed.

Built on [MultiLoader Template](https://github.com/jaredlll08/MultiLoader-Template) by jaredlll08.
