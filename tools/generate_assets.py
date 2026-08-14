#!/usr/bin/env python3
"""
Generates Seamless Ores' client assets: blockstates, two-layer block models, item model
definitions, the lang file, and (optionally) the ore overlay textures.

Run with Python 3.14 -- Pillow is only installed there on this machine:

    py -3.14 tools/generate_assets.py                # JSON only (safe, idempotent)
    py -3.14 tools/generate_assets.py --textures     # ALSO re-extract the 8 overlay PNGs

--textures is OFF by default on purpose. The extraction is a starting point that needs hand
cleanup in a pixel editor, and re-running it would silently throw that work away.

How the overlays are derived
----------------------------
Vanilla ore textures are the base stone with ore blobs painted over it, so `iron_ore.png` minus
`stone.png` isolates the blobs. Vanilla also *shades* the stone around each blob, though, and a
naive diff captures that shading too -- it shows up as grey haze over granite. The colour-distance
threshold below discards those near-stone pixels. Coal is the worst case (dark blobs, dark
shading) and needs the most hand cleanup.

These overlays are derived from Mojang's textures and therefore remain Mojang's IP. Do not claim
ownership of them in the README or on any store page.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile

MOD_ID = "seamlessores"

# Classic Forge's datapack condition key. SINGULAR, and it takes ONE object rather than an array -
# it is ICondition.DEFAULT_FIELD, verified as "forge:condition" in forge 52 and 61 alike. Spelled
# differently again on 1.20.x Forge (unnamespaced "conditions", array), so re-verify against the
# real jar before carrying this to an older branch.
FORGE_CONDITION_KEY = "conditions"

# 1.20.x DATA FOLDER NAMES. These are PLURAL here and singular from 1.21 onward. Read out of the
# real client jar rather than remembered: data/minecraft/{loot_tables,tags/blocks,tags/items}/.
# 1.20.1's data pack_format, read from the client jar. 1.20.1 knows ONLY pack_format;
# supported_formats arrives at 1.21.1 and min_format/max_format at 1.21.11.
PACK_FORMAT = 15

LOOT_DIR = "loot_tables"
TAG_BLOCK_DIR = ("tags", "blocks")
TAG_ITEM_DIR = ("tags", "items")

# Common-tag namespaces. At 1.20.x the ecosystem is SPLIT - Fabric uses `c:` and Forge uses
# `forge:` - where 1.21+ settled on `c:` for both. Both are written: the one a given loader does
# not read is simply a tag nobody queries, which costs nothing and keeps one data tree for both.
CONVENTION_NAMESPACES = ("c", "forge")

# Colour-distance (summed per-channel) above which a pixel counts as ore rather than shaded stone.
# 0 keeps 141/256 px for iron and hazes over granite; 60 keeps 76 and looks right; 90 eats real blobs.
THRESHOLD = 60

CLIENT_JAR = os.path.expanduser(
    "~/.gradle/caches/neoformruntime/artifacts/minecraft_1.20.1_client.jar"
)

# Create (Create Fly, mod id 'create') jar - source of the zinc loot table shape and the zinc ore
# texture the overlay is derived from. Machine-specific default, override with the CREATE_JAR env
# var. Licence: the jar ships CC0 at root plus the original Create MIT - deriving the overlay is
# fine; keep the attribution line in the README. When the jar is missing, zinc JSON still generates
# (the loot shape is baked below, verified identical to vanilla iron_ore's) but the texture step
# skips zinc.
CREATE_JAR = os.environ.get("CREATE_JAR", "../jars/1.20.1-create-1.20.1-6.0.8.jar")

# Mythic Upgrades (mod id 'mythicupgrades', MIT, 26.2 on all four loaders). Source of its ore
# textures and the facts behind the entries below. Override with MYTHIC_UPGRADES_JAR.
MYTHIC_UPGRADES_JAR = os.environ.get(
    "MYTHIC_UPGRADES_JAR", "../jars/1.20.1-mythicupgrades-forge-1.20.1-5.1.0.jar")

# Mythic Metals (mod id 'mythicmetals', MIT). Fabric only on every version it has ever shipped, so
# its variants only ever register there. Source of its ore textures, loot tables and tool tags.
SILENT_GEMS_JAR = os.environ.get(
    "SILENT_GEMS_JAR",
    "../jars/1.20.1-silents-gems-1.20.1-4.7.0.jar")

MYTHIC_METALS_JAR = os.environ.get(
    "MYTHIC_METALS_JAR", "../jars/1.20.1-mythicmetals-0.19.12+1.20.1.jar")

# EVERY jar above is the 1.20.1 build of that mod, not a newer one. That matters: the generator
# TRANSFORMS each mod's own loot table, so reading a 1.21-era jar would bake a 1.21-shaped table
# into a 1.20.1 datapack. Fetch them per version from the Modrinth API rather than reusing whatever
# happens to be in a test profile.

# Every third-party jar we read, keyed by the mod id used in the ORES table below. A missing jar is
# a warning rather than an error: the JSON still generates, only the texture step is skipped.

POWAH_JAR = os.environ.get("POWAH_JAR", "../jars/1.20.1-Powah-5.0.11.jar")

TFMG_JAR = os.environ.get("TFMG_JAR", "../jars/1.20.1-tfmg-1.0.2f.jar")

ENERGIZEDPOWER_JAR = os.environ.get("ENERGIZEDPOWER_JAR", "../jars/1.20.1-energizedpower-1.20.1-2.15.22-forge.jar")

ICEANDFIRE_JAR = os.environ.get("ICEANDFIRE_JAR", "../jars/iceandfire-2.1.13-1.20.1-beta-5.jar")
EXPORES_JAR = os.environ.get("EXPORES_JAR", "../jars/1.20.1-expores-1.0.0+mc1.20.1.jar")
THINGS_JAR = os.environ.get("THINGS_JAR", "../jars/1.20.1-things-0.3.3+1.20.jar")

SILENTGEAR_JAR = os.environ.get("SILENTGEAR_JAR", "../jars/1.20.1-silent-gear-1.20.1-3.6.7.jar")

CREATE_NEW_AGE_JAR = os.environ.get("CREATE_NEW_AGE_JAR", "../jars/1.20.1-create-new-age-1.2.0+forge-mc1.20.1.jar")

MOD_JARS = {"create_new_age": CREATE_NEW_AGE_JAR,
            "silentgear": SILENTGEAR_JAR,
            "things": THINGS_JAR,
            "iceandfire": ICEANDFIRE_JAR,
            "expores": EXPORES_JAR,
            "energizedpower": ENERGIZEDPOWER_JAR,
            "tfmg": TFMG_JAR,
            "powah": POWAH_JAR,
            "create": CREATE_JAR, "mythicupgrades": MYTHIC_UPGRADES_JAR,
            "silentgems": SILENT_GEMS_JAR,
            "mythicmetals": MYTHIC_METALS_JAR}

# Host stones that receive ore but have no matching ore texture in vanilla.
# KEEP IN SYNC WITH HostStone.java.
#   tier - which vanilla ore this stone stands in for
#   side / end - the model's base textures for side faces and up/down faces. For most stones they
#     are the same sprite, but basalt AND blackstone are cube_column blocks in vanilla (side + _top
#     textures); using the side sprite on all six faces makes our tops visibly mismatch the
#     neighbouring stone. Values read from the vanilla block models, not guessed.
# Stone and deepslate are absent (vanilla ships matching ores). Calcite and smooth basalt are absent
# because they are in no ore replaceables tag, so ore never generates in them at all.
HOSTS = {
    "granite":    {"tier": "stone",     "side": "minecraft:block/granite",     "end": "minecraft:block/granite"},
    "diorite":    {"tier": "stone",     "side": "minecraft:block/diorite",     "end": "minecraft:block/diorite"},
    "andesite":   {"tier": "stone",     "side": "minecraft:block/andesite",    "end": "minecraft:block/andesite"},
    "tuff":       {"tier": "deepslate", "side": "minecraft:block/tuff",        "end": "minecraft:block/tuff"},
    "basalt":     {"tier": "nether",    "side": "minecraft:block/basalt_side", "end": "minecraft:block/basalt_top"},
    "blackstone": {"tier": "nether",    "side": "minecraft:block/blackstone",  "end": "minecraft:block/blackstone_top"},
}

# Ore definitions. KEEP IN SYNC WITH OreType.java.
#   name    - id suffix, so <host>_<name>_ore
#   overlay - texture key; separate from name because overworld and nether gold are different
#             textures (gold specks over stone vs over netherrack) while both yield <host>_gold_ore
#   tiers   - vanilla ore per host tier; a pairing only exists where the tier is present
#   source  - vanilla texture the overlay is extracted from
#   base    - vanilla texture it is diffed AGAINST (stone for overworld, netherrack for nether)
# Note tuff uses the LIGHT stone overlay, not the deepslate one.
# Animated overlays. An ore whose source texture animates needs its overlay to animate in step, or
# our variant sits still next to a pulsing one. Values are copied from the SOURCE MOD'S OWN mcmeta
# rather than chosen, so the two stay synchronised.
#
# Only two Mythic Metals ore blocks animate (every mcmeta in the jar was checked): stormyx on both
# its hosts, and the DEEPSLATE unobtainium ore while its stone one is a still image.
#
# This is the safe vanilla path: a plain N-frame vertical strip on an ordinary sprite. It is NOT the
# same as animating a Fusion connecting sheet, which crashes the game on load - see the maintainer notes.
ANIMATED_OVERLAYS = {
    "stormyx": {"frametime": 20, "interpolate": True},              # 5 frames, matches stormyx_ore
    "unobtainium_deepslate": {"frametime": 60, "interpolate": True},  # 4 frames, deepslate ore only
}

# Third-party mods whose ores get variants.
#
# KEEP IN SYNC with OreType.java's requiredModId values and with
# SeamlessOresConfigScreenFactory.MOD_CATEGORIES. generate_readme() cross-checks this against the
# mod ids actually used in ORE_DEFS and fails if the two disagree, so drift is caught at build time
# rather than showing up as a mod missing from the README's credits.
#
#   display  - the mod's own name for itself; also the config category label
#   category - config category key, which differs from the mod id wherever the name does
#   licence  - READ FROM THE JAR'S OWN METADATA, never from the platform listing
#   author   - as the jar declares it; blank where it declares none. Do not guess one.
#
# The licences matter here rather than being decoration: the overlay for each of these is DERIVED
# from that mod's own ore texture, so attribution is an obligation, not a courtesy.
MODS = {
    "create":         {"display": "Create",            "category": "create",
                       "licence": "MIT",          "author": ""},
    "create_new_age": {"display": "Create: New Age",   "category": "create_new_age",
                       "licence": "BSD-3-Clause", "author": "Antarctic Gardens"},
    "tfmg":           {"display": "Create: TFMG",      "category": "tfmg",
                       "licence": "MIT",          "author": "DrMangoTea, Pepa, Luna"},
    "energizedpower": {"display": "Energized Power",   "category": "energized_power",
                       "licence": "MIT",          "author": "JDDev0"},
    "mythicmetals":   {"display": "Mythic Metals",     "category": "mythic_metals",
                       "licence": "MIT",          "author": "Noaaan"},
    "mythicupgrades": {"display": "Mythic Upgrades",   "category": "mythic_upgrades",
                       "licence": "MIT",          "author": "TriQue"},
    "powah":          {"display": "Powah",             "category": "powah",
                       "licence": "LGPL-3.0",     "author": "owmii, Technici4n, shartte"},
    "silentgear":     {"display": "Silent Gear",       "category": "silent_gear",
                       "licence": "MIT",          "author": "SilentChaos512"},
    "silentgems":     {"display": "Silent's Gems",     "category": "silents_gems",
                       "licence": "MIT",          "author": "SilentChaos512"},
    "iceandfire":     {"display": "Ice and Fire",      "category": "ice_and_fire",
                       "licence": "LGPL-3.0",     "author": "Alexthe666, TheBv"},
    "expores":        {"display": "Exp Ores",          "category": "exp_ores",
                       "licence": "MIT",          "author": "TriQue"},
    "things":         {"display": "Things",            "category": "things",
                       "licence": "MIT",          "author": "glisco"},
}

ORE_DEFS = [
    {"name": "coal",     "overlay": "coal",     "source": "coal_ore",     "base": "stone",
     "tiers": {"stone": "coal_ore", "deepslate": "deepslate_coal_ore"}},
    {"name": "iron",     "overlay": "iron",     "source": "iron_ore",     "base": "stone",
     "tiers": {"stone": "iron_ore", "deepslate": "deepslate_iron_ore"}},
    {"name": "copper",   "overlay": "copper",   "source": "copper_ore",   "base": "stone",
     "tiers": {"stone": "copper_ore", "deepslate": "deepslate_copper_ore"}},
    {"name": "gold",     "overlay": "gold",     "source": "gold_ore",     "base": "stone",
     "tiers": {"stone": "gold_ore", "deepslate": "deepslate_gold_ore"}},
    {"name": "lapis",    "overlay": "lapis",    "source": "lapis_ore",    "base": "stone",
     "tiers": {"stone": "lapis_ore", "deepslate": "deepslate_lapis_ore"}},
    {"name": "diamond",  "overlay": "diamond",  "source": "diamond_ore",  "base": "stone",
     "tiers": {"stone": "diamond_ore", "deepslate": "deepslate_diamond_ore"}},
    {"name": "emerald",  "overlay": "emerald",  "source": "emerald_ore",  "base": "stone",
     "tiers": {"stone": "emerald_ore", "deepslate": "deepslate_emerald_ore"}},
    {"name": "redstone", "overlay": "redstone", "source": "redstone_ore", "base": "stone",
     "tiers": {"stone": "redstone_ore", "deepslate": "deepslate_redstone_ore"}},
    # Nether. These ADD ore - vanilla's nether features match netherrack only - so their worldgen
    # injection is config-gated in OreTargetInjector. Registration and assets are unconditional.
    {"name": "gold",     "overlay": "nether_gold", "source": "nether_gold_ore",   "base": "netherrack",
     "tiers": {"nether": "nether_gold_ore"}},
    {"name": "quartz",   "overlay": "quartz",      "source": "nether_quartz_ore", "base": "netherrack",
     "tiers": {"nether": "nether_quartz_ore"}},
    # Zinc (Create). "mod" marks a third-party ore: ids live in that namespace, its blocks exist
    # only when the mod is loaded (registration is gated in SeamlessOresContent), the loot table
    # gets both loaders' conditions, tag entries become optional ({"required": false}), and the
    # texture/loot source is CREATE_JAR rather than the client jar. Verified from the real jar:
    # loot = vanilla iron shape dropping create:raw_zinc; tool tier = needs_iron_tool (NOT stone).
    {"name": "zinc",     "overlay": "zinc",        "source": "zinc_ore",          "base": "stone",
     "mod": "create", "raw_drop": "create:raw_zinc",
     "tiers": {"stone": "zinc_ore", "deepslate": "deepslate_zinc_ore"}},
    # Mythic Upgrades. All verified from its jar: every one is needs_iron_tool, drops a single item
    # with the ore_drops fortune formula, and returns the block on Silk Touch. The five overworld
    # ores target the same replaceables tags as vanilla, so injecting them is balance-neutral.
    # Ruby and sapphire are netherrack-only, so their basalt/blackstone variants ADD ore, exactly
    # like our nether gold and quartz, and ride the same host toggles and bastion protection.
    # Ametrine and jade are deliberately absent: end_stone only, and the End has no second stone.
    {"name": "aquamarine", "overlay": "aquamarine", "source": "aquamarine_ore", "base": "stone",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:aquamarine",
     "tiers": {"stone": "aquamarine_ore", "deepslate": "deepslate_aquamarine_ore"}},
    {"name": "citrine",    "overlay": "citrine",    "source": "citrine_ore",    "base": "stone",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:citrine",
     "tiers": {"stone": "citrine_ore", "deepslate": "deepslate_citrine_ore"}},
    {"name": "peridot",    "overlay": "peridot",    "source": "peridot_ore",    "base": "stone",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:peridot",
     "tiers": {"stone": "peridot_ore", "deepslate": "deepslate_peridot_ore"}},
    {"name": "topaz",      "overlay": "topaz",      "source": "topaz_ore",      "base": "stone",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:topaz",
     "tiers": {"stone": "topaz_ore", "deepslate": "deepslate_topaz_ore"}},
    # Necoium is the odd one: a METAL, so it drops raw_necoium and gives no XP, unlike the gems.
    {"name": "necoium",    "overlay": "necoium",    "source": "necoium_ore",    "base": "stone",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:raw_necoium",
     "tiers": {"stone": "necoium_ore", "deepslate": "deepslate_necoium_ore"}},
    {"name": "ruby",       "overlay": "ruby",       "source": "ruby_ore",       "base": "netherrack",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:ruby",
     "tiers": {"nether": "ruby_ore"}},
    {"name": "sapphire",   "overlay": "sapphire",   "source": "sapphire_ore",   "base": "netherrack",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:sapphire",
     "tiers": {"nether": "sapphire_ore"}},

    # --- Mythic Metals (mod id mythicmetals, MIT, Fabric only on every version) ------------------
    # KEEP IN SYNC WITH OreType.java. Hosts derived from the real jar's configured features; the
    # full table is in the maintainer notes.
    #
    # THE RULE THAT STOPS US INVENTING ORE: the "stone tier only" block below targets
    # stone_ore_replaceables ONLY, so those ores generate in granite, diorite and andesite but NEVER
    # in tuff, which lives in deepslate_ore_replaceables. No deepslate tier means no tuff variant.
    #
    # Loot comes from transforming Mythic Metals' own tables, NOT the vanilla iron shape: theirs use
    # set_count 1-2 plus rare secondary drops, so a hand-built table would halve the yield.
    {"name": "adamantite", "overlay": "adamantite", "source": "adamantite_ore", "base": "stone",
     "mod": "mythicmetals",
     "tiers": {"stone": "adamantite_ore", "deepslate": "deepslate_adamantite_ore"}},
    {"name": "carmot", "overlay": "carmot", "source": "carmot_ore", "base": "stone",
     "mod": "mythicmetals",
     "tiers": {"stone": "carmot_ore", "deepslate": "deepslate_carmot_ore"}},
    {"name": "morkite", "overlay": "morkite", "source": "morkite_ore", "base": "stone",
     "mod": "mythicmetals",
     "tiers": {"stone": "morkite_ore", "deepslate": "deepslate_morkite_ore"}},
    {"name": "mythril", "overlay": "mythril", "source": "mythril_ore", "base": "stone",
     "mod": "mythicmetals",
     "tiers": {"stone": "mythril_ore", "deepslate": "deepslate_mythril_ore"}},
    {"name": "prometheum", "overlay": "prometheum", "source": "prometheum_ore", "base": "stone",
     "mod": "mythicmetals",
     "tiers": {"stone": "prometheum_ore", "deepslate": "deepslate_prometheum_ore"}},
    {"name": "runite", "overlay": "runite", "source": "runite_ore", "base": "stone",
     "mod": "mythicmetals",
     "tiers": {"stone": "runite_ore", "deepslate": "deepslate_runite_ore"}},
    # Unobtainium's DEEPSLATE ore is animated (4 frames) and its stone one is not, so the tuff
    # variant needs its own overlay. This is the only ore that needs deepslate_overlay.
    {"name": "unobtainium", "overlay": "unobtainium", "deepslate_overlay": "unobtainium_deepslate",
     "source": "unobtainium_ore", "base": "stone", "mod": "mythicmetals",
     "tiers": {"stone": "unobtainium_ore", "deepslate": "deepslate_unobtainium_ore"}},
    # Stone tier only: three hosts each, never tuff.
    {"name": "aquarium", "overlay": "aquarium", "source": "aquarium_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "aquarium_ore"}},
    {"name": "banglum", "overlay": "banglum", "source": "banglum_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "banglum_ore"}},
    {"name": "kyber", "overlay": "kyber", "source": "kyber_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "kyber_ore"}},
    {"name": "manganese", "overlay": "manganese", "source": "manganese_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "manganese_ore"}},
    {"name": "osmium", "overlay": "osmium", "source": "osmium_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "osmium_ore"}},
    {"name": "platinum", "overlay": "platinum", "source": "platinum_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "platinum_ore"}},
    {"name": "quadrillum", "overlay": "quadrillum", "source": "quadrillum_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "quadrillum_ore"}},
    {"name": "silver", "overlay": "silver", "source": "silver_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "silver_ore"}},
    {"name": "starrite", "overlay": "starrite", "source": "starrite_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "starrite_ore"}},
    {"name": "tin", "overlay": "tin", "source": "tin_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "tin_ore"}},
    # Mythic Metals ships its own tuff_orichalcum_ore through an explicit block_match
    # target ahead of its deepslate tag entry, so tuff is already seamless there.
    {"name": "orichalcum", "overlay": "orichalcum", "source": "orichalcum_ore", "base": "stone",
     "mod": "mythicmetals", "tiers": {"stone": "orichalcum_ore"}},
    # Nether. Like our own gold and quartz these ADD ore, so they ride the basalt and blackstone
    # host toggles and the bastion protection. Banglum's nether form reuses the plain name for the
    # same reason nether gold does: the host already disambiguates.
    {"name": "banglum", "overlay": "nether_banglum", "source": "nether_banglum_ore", "base": "netherrack",
     "mod": "mythicmetals", "tiers": {"nether": "nether_banglum_ore"}},
    {"name": "midas_gold", "overlay": "midas_gold", "source": "midas_gold_ore", "base": "netherrack",
     "mod": "mythicmetals", "tiers": {"nether": "midas_gold_ore"}},
    {"name": "palladium", "overlay": "palladium", "source": "palladium_ore", "base": "netherrack",
     "mod": "mythicmetals", "tiers": {"nether": "palladium_ore"}},
    # Mythic Metals already ships blackstone_stormyx_ore, so we only add the basalt one. Its
    # overlay is animated (5 frames), matching their own stormyx_ore.
    {"name": "stormyx", "overlay": "stormyx", "source": "stormyx_ore", "base": "netherrack",
     "mod": "mythicmetals", "skip_hosts": ["blackstone"], "tiers": {"nether": "stormyx_ore"}},

    # --- Silent's Gems (mod id silentgems, MIT) -------------------------------------------------
    # Every gem targets BOTH replaceables tags, so all four hosts apply and the restyle is
    # balance-neutral. Loot is the plain vanilla shape, so the tables transform directly.
    # KEEP IN SYNC WITH OreType.java, INCLUDING the silents_ prefixes: aquamarine, citrine,
    # peridot, topaz and silver would otherwise produce a block id we already register for
    # Mythic Upgrades or Mythic Metals. Ruby and sapphire need no prefix, because Mythic Upgrades
    # puts those in netherrack only while ours are overworld, so the ids never meet.
    {"name": "alexandrite",             "overlay": "alexandrite",             "source": "alexandrite_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:alexandrite",
     "tiers": {"stone": "alexandrite_ore", "deepslate": "deepslate_alexandrite_ore"}},
    {"name": "ammolite",                "overlay": "ammolite",                "source": "ammolite_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:ammolite",
     "tiers": {"stone": "ammolite_ore", "deepslate": "deepslate_ammolite_ore"}},
    {"name": "black_diamond",           "overlay": "black_diamond",           "source": "black_diamond_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:black_diamond",
     "tiers": {"stone": "black_diamond_ore", "deepslate": "deepslate_black_diamond_ore"}},
    {"name": "carnelian",               "overlay": "carnelian",               "source": "carnelian_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:carnelian",
     "tiers": {"stone": "carnelian_ore", "deepslate": "deepslate_carnelian_ore"}},
    {"name": "heliodor",                "overlay": "heliodor",                "source": "heliodor_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:heliodor",
     "tiers": {"stone": "heliodor_ore", "deepslate": "deepslate_heliodor_ore"}},
    {"name": "iolite",                  "overlay": "iolite",                  "source": "iolite_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:iolite",
     "tiers": {"stone": "iolite_ore", "deepslate": "deepslate_iolite_ore"}},
    {"name": "kyanite",                 "overlay": "kyanite",                 "source": "kyanite_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:kyanite",
     "tiers": {"stone": "kyanite_ore", "deepslate": "deepslate_kyanite_ore"}},
    {"name": "moldavite",               "overlay": "moldavite",               "source": "moldavite_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:moldavite",
     "tiers": {"stone": "moldavite_ore", "deepslate": "deepslate_moldavite_ore"}},
    {"name": "rose_quartz",             "overlay": "rose_quartz",             "source": "rose_quartz_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:rose_quartz",
     "tiers": {"stone": "rose_quartz_ore", "deepslate": "deepslate_rose_quartz_ore"}},
    {"name": "ruby",                    "overlay": "ruby",                    "source": "ruby_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:ruby",
     "tiers": {"stone": "ruby_ore", "deepslate": "deepslate_ruby_ore"}},
    {"name": "sapphire",                "overlay": "sapphire",                "source": "sapphire_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:sapphire",
     "tiers": {"stone": "sapphire_ore", "deepslate": "deepslate_sapphire_ore"}},
    {"name": "turquoise",               "overlay": "turquoise",               "source": "turquoise_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:turquoise",
     "tiers": {"stone": "turquoise_ore", "deepslate": "deepslate_turquoise_ore"}},
    {"name": "white_diamond",           "overlay": "white_diamond",           "source": "white_diamond_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:white_diamond",
     "tiers": {"stone": "white_diamond_ore", "deepslate": "deepslate_white_diamond_ore"}},
    {"name": "silents_citrine",         "overlay": "silents_citrine",         "source": "citrine_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:citrine",
     "tiers": {"stone": "citrine_ore", "deepslate": "deepslate_citrine_ore"}},
    {"name": "silents_peridot",         "overlay": "silents_peridot",         "source": "peridot_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:peridot",
     "tiers": {"stone": "peridot_ore", "deepslate": "deepslate_peridot_ore"}},
    {"name": "silents_topaz",           "overlay": "silents_topaz",           "source": "topaz_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:topaz",
     "tiers": {"stone": "topaz_ore", "deepslate": "deepslate_topaz_ore"}},
    {"name": "silents_silver",          "overlay": "silents_silver",          "source": "silver_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:raw_silver",
     "tiers": {"stone": "silver_ore", "deepslate": "deepslate_silver_ore"}},

    # --- Seven more third-party mods -------------------------------------------------------
    # NO raw_drop on any of these, deliberately: their loot is TRANSFORMED from the mod's own
    # tables. Dense Mekanism and Powah both use set_count, so a hand-built vanilla-shape table
    # would change their yields, exactly as it would have for Mythic Metals.
    # energized_tin is prefixed because plain tin is already Mythic Metals'.
    {"name": "uraninite", "overlay": "uraninite", "source": "uraninite_ore", "base": "stone",
     "mod": "powah",
     "tiers": {"stone": "uraninite_ore", "deepslate": "deepslate_uraninite_ore"}},
    {"name": "uraninite_poor", "overlay": "uraninite_poor", "source": "uraninite_ore_poor", "base": "stone",
     "mod": "powah",
     "tiers": {"stone": "uraninite_ore_poor", "deepslate": "deepslate_uraninite_ore_poor"}},
    {"name": "uraninite_dense", "overlay": "uraninite_dense", "source": "uraninite_ore_dense", "base": "stone",
     "mod": "powah",
     "tiers": {"stone": "uraninite_ore_dense", "deepslate": "deepslate_uraninite_ore_dense"}},
    {"name": "lead", "overlay": "lead", "source": "lead_ore", "base": "stone",
     "mod": "tfmg",
     "tiers": {"stone": "lead_ore", "deepslate": "deepslate_lead_ore"}},
    {"name": "lithium", "overlay": "lithium", "source": "lithium_ore", "base": "stone",
     "mod": "tfmg",
     "tiers": {"stone": "lithium_ore", "deepslate": "deepslate_lithium_ore"}},
    {"name": "nickel", "overlay": "nickel", "source": "nickel_ore", "base": "stone",
     "mod": "tfmg",
     "tiers": {"stone": "nickel_ore", "deepslate": "deepslate_nickel_ore"}},
    {"name": "energized_tin", "overlay": "energized_tin", "source": "tin_ore", "base": "stone",
     "mod": "energizedpower",
     "tiers": {"stone": "tin_ore", "deepslate": "deepslate_tin_ore"}},
    {"name": "gleaming", "overlay": "gleaming", "source": "gleaming_ore", "base": "stone",
     "mod": "things",
     "tiers": {"stone": "gleaming_ore", "deepslate": "deepslate_gleaming_ore"}},
    {"name": "bort", "overlay": "bort", "source": "bort_ore", "base": "stone",
     "mod": "silentgear",
     "tiers": {"stone": "bort_ore", "deepslate": "deepslate_bort_ore"}},
    {"name": "thorium", "overlay": "thorium", "source": "thorium_ore", "base": "stone",
     "mod": "create_new_age",
     "tiers": {"stone": "thorium_ore"}},

    # Silent's Gems in the NETHER. ONLY the eight that actually generate: the other thirteen have
    # count 0 AND size 0 in their placed features, so they are registered but place nothing, and a
    # variant would invent ore. These ADD ore (the mod targets c:netherracks only), so they ride the
    # host toggles, the nether dials and bastion protection, exactly like our gold and quartz.
    # They reuse the overworld overlay: measured against the mod’s own nether textures it lands
    # 96-100% on the gem pixels, because the same blobs are drawn on netherrack as on stone.
    {"name": "alexandrite", "overlay": "alexandrite", "source": "alexandrite_nether_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "alexandrite_nether_ore"}},
    {"name": "black_diamond", "overlay": "black_diamond", "source": "black_diamond_nether_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "black_diamond_nether_ore"}},
    {"name": "carnelian", "overlay": "carnelian", "source": "carnelian_nether_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "carnelian_nether_ore"}},
    {"name": "silents_citrine", "overlay": "silents_citrine", "source": "citrine_nether_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "citrine_nether_ore"}},
    {"name": "iolite", "overlay": "iolite", "source": "iolite_nether_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "iolite_nether_ore"}},
    {"name": "moldavite", "overlay": "moldavite", "source": "moldavite_nether_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "moldavite_nether_ore"}},
    # --- Ice and Fire (mod id iceandfire, LGPL-3.0) --------------------------------------------
    # Forge only at 1.20.1, and this mod exists on no other branch we ship.
    # Both ids are PREFIXED: Silent's Gems has its own sapphire and silver, and at 1.20.1 both mods
    # are Forge, so they genuinely coexist and <host>_sapphire_ore would collide. Block ids are a
    # one-way door, so the newcomer takes the prefix.
    # sapphire targets stone_ore_replaceables ONLY - no deepslate tier, so no tuff variant. A tuff
    # one would invent ore, exactly like the ten Mythic Metals ores in the same position.
    {"name": "iceandfire_sapphire", "overlay": "iceandfire_sapphire", "source": "sapphire_ore",
     "base": "stone", "mod": "iceandfire",
     "tiers": {"stone": "sapphire_ore"}},
    {"name": "iceandfire_silver", "overlay": "iceandfire_silver", "source": "silver_ore",
     "base": "stone", "mod": "iceandfire",
     "tiers": {"stone": "silver_ore", "deepslate": "deepslate_silver_ore"}},

    # --- Exp Ores (mod id expores, MIT) ---------------------------------------------------------
    # Fabric only at 1.20.1. Its ore drops minecraft:air and pays in experience alone -
    # UniformInt(96, 128), read from EXPBlocks - so the transformed table correctly drops nothing.
    {"name": "experience", "overlay": "experience", "source": "experience_ore", "base": "stone",
     "mod": "expores",
     "tiers": {"stone": "experience_ore", "deepslate": "deepslate_experience_ore"}},
    # The nether one targets the base_stone_nether TAG, so it ALREADY generates in basalt and
    # blackstone. That makes these two a pure restyle at zero balance cost - unlike our own gold and
    # quartz, which add ore - so they ride no rarity dial and need no "adds ore" caveat.
    {"name": "experience", "overlay": "nether_experience", "source": "nether_experience_ore",
     "base": "netherrack", "mod": "expores",
     "tiers": {"nether": "nether_experience_ore"}},
]

FACES = ["down", "up", "north", "south", "west", "east"]

# Tool tags are NOT hardcoded per ore: they are read from the jar and mirrored per variant, keyed on
# the vanilla equivalent. This matters because it is not uniform by ore - overworld gold_ore is in
# needs_iron_tool but nether_gold_ore is in NO tool tag (wooden pickaxe), and coal is in none either.
TOOL_TAGS = ["needs_stone_tool", "needs_iron_tool", "needs_diamond_tool"]


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resources_dir():
    return os.path.join(repo_root(), "common", "src", "main", "resources")


# Loader modules that can actually host a third-party ore on THIS Minecraft version.
#
# WHY THIS EXISTS, AND WHY ONLY ON THIS BRANCH: at Forge 52 a loot table is loaded by
# LootDataType.deserialize, which calls codec.parse directly with NO ConditionCodec wrapper, so
# "forge:condition" is simply ignored there. (Forge DOES honour it on datapack registries such as
# worldgen - that path is patched, this one is not.) A conditional loot table naming an absent mod's
# item therefore logs "Couldn't parse element ... Unknown registry key" on every world load.
#
# It is dead weight anyway: neither Create nor Mythic Upgrades has a Forge build at 1.21 or 1.21.1
# (checked on the Modrinth API), so those blocks can never register on Forge here. Writing the
# conditional tables into the loader modules that CAN use them keeps the Forge jar clean instead of
# shipping 28 files that only ever produce errors. Re-check the loader matrix on any version bump.
# PER MOD, because the loader matrix is not the same for all of them. Getting this wrong is silent
# and serious in BOTH directions: a table written to a loader the mod cannot run on is harmless
# noise, but a table MISSING from a loader the mod CAN run on means our variants register there and
# drop NOTHING when broken.
#
# Verified on the Modrinth API for this branch (1.21 / 1.21.1):
#   create         neoforge only          (Create Fabric does not exist here)
#   mythicupgrades fabric + neoforge
#   mythicmetals   fabric only
#   silentgems     forge + neoforge       <- the one that forced this to be per mod
#
# Silent's Gems is also the case where the Forge caveat above actually bites: its tables MUST ship
# in the Forge jar or its 88 variants drop nothing there, and Forge 52 will log a parse error per
# table on instances that do not have the mod. A noisy log beats blocks that drop nothing.
CONDITIONAL_LOOT_MODULES_BY_MOD = {
    # RE-QUERIED PER GAME VERSION for 1.20.1, never carried over from another branch. That array on
    # a project page is the UNION across every file it has ever shipped, so it lies about any single
    # version. Query instead:
    #   /v2/project/<slug>/version?game_versions=["1.20.1"]  -> union of THAT file set's loaders
    #
    # There are only two modules here, because 1.20.1 has no separate NeoForge module: NeoForge
    # 47.1.x provides the `forge` mod id, so a mod tagged neoforge OR forge counts as "forge".
    #
    # DENSE MEKANISM IS ABSENT ENTIRELY - it stops at 1.19.2 - so it gets no modules at all and its
    # twenty variants can never register here. Its assets still ship and are inert, and its config
    # category hides itself because the mod is never loaded.
    "create": ("fabric", "forge"),        # forge/neoforge direct, fabric via the Create Fabric port
    "create_new_age": ("fabric", "forge"),
    "tfmg": ("forge",),                   # slug is create-tfmg, forge only at 1.20.1
    "energizedpower": ("fabric", "forge"),
    "mythicmetals": ("fabric",),
    "mythicupgrades": ("fabric", "forge"),
    "powah": ("fabric", "forge"),
    "silentgear": ("forge",),
    "silentgems": ("forge",),
    "things": ("fabric",),
    # Both of these exist at 1.20.x and on no other branch we ship.
    "iceandfire": ("forge",),
    "expores": ("fabric",),
}

# Mods whose Forge-side data ships as a BUILT-IN DATAPACK rather than as ordinary resources.
#
# Forge 1.20.1 cannot gate a loot table or a worldgen file on a mod being present: grepping Forge
# 47's own sources, CraftingHelper.processConditions is called from RecipeManager, ConditionalRecipe
# and ConditionalAdvancement and nowhere else. An absent mod would mean 167 "Couldn't parse element"
# errors per world load, and for the worldgen files an outright crash on unbound registry values.
#
# So those files go to forge/src/main/resources/packs/<mod>/ instead, each with its own pack.mcmeta,
# and SeamlessOresDataPacks offers each pack only when ModList says that mod is loaded.
# Keep this in step with SeamlessOresDataPacks.PACKED_MODS.
FORGE_PACK_MODS = tuple(
    mod for mod, modules in CONDITIONAL_LOOT_MODULES_BY_MOD.items() if "forge" in modules)

DEFAULT_CONDITIONAL_LOOT_MODULES = ("fabric", "forge")


def forge_pack_dir(mod):
    """Root of the built-in datapack that carries `mod`'s Forge-side data. See FORGE_PACK_MODS."""
    return os.path.join(repo_root(), "forge", "src", "main", "resources", "packs", mod)


def forge_pack_data_dir(mod, namespace):
    return os.path.join(forge_pack_dir(mod), "data", namespace)


def conditional_data_dir(module, namespace):
    return os.path.join(repo_root(), module, "src", "main", "resources", "data", namespace)


def assets_dir():
    return os.path.join(resources_dir(), "assets", MOD_ID)


def data_dir(namespace):
    return os.path.join(resources_dir(), "data", namespace)


def variants():
    """Every (host, host config, ore def, vanilla equivalent) pairing that actually exists.

    A pairing exists only where the ore has a vanilla equivalent for that host's tier, which is what
    keeps granite quartz and basalt iron from being invented. Mirrors SeamlessOresContent.
    """
    for host, host_cfg in HOSTS.items():
        for ore in ORE_DEFS:
            # skip_hosts: the ore's own mod already ships a seamless variant for that stone, so ours
            # would take the host over (the injector prepends). Mirrors OreType.skipHosts.
            if host in ore.get("skip_hosts", ()):
                continue
            vanilla = ore["tiers"].get(host_cfg["tier"])
            if vanilla is not None:
                yield host, host_cfg, ore, vanilla


def overlay_for(ore, host_cfg):
    """Overlay key for this host, honouring a per-tier override. Mirrors OreType.overlayFor."""
    if host_cfg["tier"] == "deepslate" and ore.get("deepslate_overlay"):
        return ore["deepslate_overlay"]
    return ore["overlay"]


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def variant_name(host, ore):
    return f"{host}_{ore}_ore"


# Display-name overrides where the id fragment is not the vanilla display word. Vanilla calls the
# block "Lapis Lazuli Ore" (id lapis_ore) - "Granite Lapis Ore" would be the exact naming
# inconsistency users reported on the incumbent. Quartz stays "Quartz" (no "Nether" prefix: that
# prefix distinguishes an overworld quartz that does not exist, and ours is already host-prefixed).
DISPLAY_NAMES = {"lapis": "Lapis Lazuli"}


def title(name):
    words = [DISPLAY_NAMES.get(part, part.capitalize()) for part in name.split("_")]
    return " ".join(words)


def cube_faces(side_ref, end_ref=None):
    """Full-cube faces: side_ref on the four sides, end_ref (default same) on up/down."""
    end_ref = end_ref or side_ref
    face = {}
    for side in FACES:
        ref = end_ref if side in ("up", "down") else side_ref
        face[side] = {"uv": [0, 0, 16, 16], "texture": ref, "cullface": side}
    return face


def generate_json():
    root = assets_dir()
    count = 0

    for host, host_cfg, ore, _vanilla in variants():
            name = variant_name(host, ore["name"])

            # Blockstate. Note redstone needs no lit variant: vanilla's own redstone_ore blockstate
            # is a single model too -- the lit state only changes light emission, not the model.
            write_json(
                os.path.join(root, "blockstates", f"{name}.json"),
                {"variants": {"": {"model": f"{MOD_ID}:block/{name}"}}},
            )

            # Two-layer block model, following vanilla's own grass_block pattern: two coincident
            # full cubes. The base is opaque so it lands on the solid layer; the overlay has alpha
            # and must land on cutout, or its transparent pixels are drawn opaque.
            #
            # THE RENDER TYPE MUST BE DECLARED BELOW 26.1. From 26.1 the chunk layer is DERIVED from
            # the texture's alpha and no per-loader API exists at all; here 1.21.1 still routes
            # through ItemBlockRenderTypes, whose map is private and whose default is solid, so an
            # undeclared block renders as opaque garbage with NOTHING logged.
            #
            # "render_type" covers NeoForge and Forge only - both read it off the block model JSON
            # (ExtendedBlockModelDeserializer on each, verified in neoforge 21.1.80 and forge 52).
            # Vanilla and Fabric ignore the key, so FABRIC IS HANDLED IN CODE by
            # SeamlessOresFabricClient calling BlockRenderLayerMap. Both halves are needed.
            write_json(
                os.path.join(root, "models", "block", f"{name}.json"),
                {
                    "parent": "minecraft:block/block",
                    "render_type": "minecraft:cutout",
                    "textures": {
                        "particle": host_cfg["side"],
                        "side": host_cfg["side"],
                        "end": host_cfg["end"],
                        "overlay": f"{MOD_ID}:block/{overlay_for(ore, host_cfg)}_overlay",
                    },
                    "elements": [
                        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": cube_faces("#side", "#end")},
                        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": cube_faces("#overlay")},
                    ],
                },
            )

            # Item model. The assets/<ns>/items/ DEFINITION layer only arrives at 1.21.4, so at
            # 1.21/1.21.1 a block item is given its look the old way: a models/item/ file that
            # simply parents the block model. Writing an items/ file here would be read by nothing.
            write_json(
                os.path.join(root, "models", "item", f"{name}.json"),
                {"parent": f"{MOD_ID}:block/{name}"},
            )
            count += 1

    lang = {
        f"block.{MOD_ID}.{variant_name(host, ore['name'])}": title(variant_name(host, ore["name"]))
        for host, _cfg, ore, _v in variants()
    }
    # Cloth Config / AutoConfig screen strings. The key shapes are fixed by AutoConfig:
    # text.autoconfig.<modid>.title / .option.<field> / .option.<field>.@Tooltip
    # A @Tooltip(count = n) needs n indexed keys instead of the bare one.
    lang.update({
        # Our own creative tab, so 295 variants stop burying vanilla's Natural Blocks.
        f"itemGroup.{MOD_ID}.ores": "Seamless Ores",
        f"text.autoconfig.{MOD_ID}.title": "Seamless Ores",

        # Category tabs. Split by dimension first, then by mod, so a Create or Mythic Upgrades
        # player finds everything about that mod in one place.
        f"text.autoconfig.{MOD_ID}.category.overworld": "Overworld",
        f"text.autoconfig.{MOD_ID}.category.nether": "Nether",
        f"text.autoconfig.{MOD_ID}.category.create": "Create",
        f"text.autoconfig.{MOD_ID}.category.mythic_upgrades": "Mythic Upgrades",
        f"text.autoconfig.{MOD_ID}.category.mythic_metals": "Mythic Metals",
        # One category per supported mod, even where it holds a single switch. Finer control can
        # then be added later without moving anybody's existing setting to a different screen.
        f"text.autoconfig.{MOD_ID}.category.silents_gems": "Silent's Gems",
        f"text.autoconfig.{MOD_ID}.category.dense_mekanism": "Dense Mekanism",
        f"text.autoconfig.{MOD_ID}.category.powah": "Powah",
        f"text.autoconfig.{MOD_ID}.category.tfmg": "Create: TFMG",
        f"text.autoconfig.{MOD_ID}.category.energized_power": "Energized Power",
        f"text.autoconfig.{MOD_ID}.category.exp_ores": "Exp Ores",
        f"text.autoconfig.{MOD_ID}.category.ice_and_fire": "Ice and Fire",
        f"text.autoconfig.{MOD_ID}.category.things": "Things",
        f"text.autoconfig.{MOD_ID}.category.silent_gear": "Silent Gear",
        f"text.autoconfig.{MOD_ID}.category.create_new_age": "Create: New Age",

        f"text.autoconfig.{MOD_ID}.option.granite": "Granite variants",
        f"text.autoconfig.{MOD_ID}.option.granite.@Tooltip":
            "Generate granite-backed ore where granite would already contain ore.",
        f"text.autoconfig.{MOD_ID}.option.diorite": "Diorite variants",
        f"text.autoconfig.{MOD_ID}.option.diorite.@Tooltip":
            "Generate diorite-backed ore where diorite would already contain ore.",
        f"text.autoconfig.{MOD_ID}.option.andesite": "Andesite variants",
        f"text.autoconfig.{MOD_ID}.option.andesite.@Tooltip":
            "Generate andesite-backed ore where andesite would already contain ore.",
        f"text.autoconfig.{MOD_ID}.option.tuff": "Tuff variants",
        f"text.autoconfig.{MOD_ID}.option.tuff.@Tooltip":
            "Generate tuff-backed ore instead of the deepslate-textured ore vanilla puts in tuff.",

        f"text.autoconfig.{MOD_ID}.option.basalt": "Basalt variants (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.basalt.@Tooltip[0]":
            "Puts gold and quartz in basalt. Vanilla generates NEITHER there,",
        f"text.autoconfig.{MOD_ID}.option.basalt.@Tooltip[1]":
            "so this ADDS ore - most noticeably in basalt deltas. Turn off for vanilla amounts.",
        f"text.autoconfig.{MOD_ID}.option.blackstone": "Blackstone variants (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.blackstone.@Tooltip[0]":
            "Puts gold and quartz in blackstone. Vanilla generates NEITHER there,",
        f"text.autoconfig.{MOD_ID}.option.blackstone.@Tooltip[1]":
            "so this ADDS ore. Turn off for vanilla amounts.",

        f"text.autoconfig.{MOD_ID}.option.oreVeins": "Restyle large ore veins",
        f"text.autoconfig.{MOD_ID}.option.oreVeins.@Tooltip[0]":
            "The big copper and iron veins are packed with granite and tuff. This makes their ore",
        f"text.autoconfig.{MOD_ID}.option.oreVeins.@Tooltip[1]":
            "match that filler. Cosmetic only - the amount of ore is identical either way.",

        f"text.autoconfig.{MOD_ID}.option.createZinc": "Create: zinc variants",
        f"text.autoconfig.{MOD_ID}.option.createZinc.@Tooltip":
            "Generate host-matched zinc ore. Does nothing unless Create is installed.",

        f"text.autoconfig.{MOD_ID}.option.mythicUpgrades": "Mythic Upgrades: variants",
        f"text.autoconfig.{MOD_ID}.option.mythicMetals": "Mythic Metals: variants",
        f"text.autoconfig.{MOD_ID}.option.mythicMetals.@Tooltip":
            "Generate host-matched Mythic Metals ore. Does nothing unless the mod is installed.",
        f"text.autoconfig.{MOD_ID}.option.mythicUpgrades.@Tooltip":
            "Generate host-matched Mythic Upgrades ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.zincVeinSize": "Create: zinc vein size",
        f"text.autoconfig.{MOD_ID}.option.zincVeinSize.@Tooltip[0]":
            "How large each zinc vein is. Create's own value is 12; lower means less zinc.",
        f"text.autoconfig.{MOD_ID}.option.zincVeinSize.@Tooltip[1]":
            "Create spreads zinc evenly from Y -63 to 70, so it is equally common everywhere.",
        f"text.autoconfig.{MOD_ID}.option.zincVeinSize.@Tooltip[2]":
            "Set this to 12 to leave Create's generation completely untouched.",

        f"text.autoconfig.{MOD_ID}.option.netherGems": "Ruby and sapphire in deltas",
        f"text.autoconfig.{MOD_ID}.option.netherGems.@Tooltip[0]":
            "Scatter Mythic Upgrades ruby and sapphire through basalt deltas, as rarely as",
        f"text.autoconfig.{MOD_ID}.option.netherGems.@Tooltip[1]":
            "ancient debris. Ruby sits around Y 28, sapphire around Y 12, never surface exposed.",

        f"text.autoconfig.{MOD_ID}.option.netherGemSize": "Ruby and sapphire amount",
        f"text.autoconfig.{MOD_ID}.option.netherGemSize.@Tooltip[0]":
            "How many gems each find holds. 3 matches ancient debris exactly, 6 is double.",
        f"text.autoconfig.{MOD_ID}.option.netherGemSize.@Tooltip[1]":
            "Higher values make finds both larger and easier to come across.",

        f"text.autoconfig.{MOD_ID}.option.netherVeinSize": "Nether vein size",
        f"text.autoconfig.{MOD_ID}.option.netherVeinSize.@Tooltip[0]":
            "How big each nether gold or quartz vein is, as a percent of vanilla. 100 is vanilla.",
        f"text.autoconfig.{MOD_ID}.option.netherVeinSize.@Tooltip[1]":
            "Below its thin basalt crust a delta is netherrack, so some of what you dig through",
        f"text.autoconfig.{MOD_ID}.option.netherVeinSize.@Tooltip[2]":
            "there is vanilla's own ore. Unlike the rarity setting, this affects that too.",

        f"text.autoconfig.{MOD_ID}.option.netherOreRarity": "Nether ore rarity",
        f"text.autoconfig.{MOD_ID}.option.netherOreRarity.@Tooltip[0]":
            "One in this many basalt or blackstone veins becomes ore. 1 converts every vein.",
        f"text.autoconfig.{MOD_ID}.option.netherOreRarity.@Tooltip[1]":
            "Basalt deltas run twice the usual gold and quartz, and are almost all basalt,",
        f"text.autoconfig.{MOD_ID}.option.netherOreRarity.@Tooltip[2]":
            "so without this nearly every vein there converted. Vanilla ore is unaffected.",

        f"text.autoconfig.{MOD_ID}.option.bastionSafeNether": "Protect bastion remnants",
        f"text.autoconfig.{MOD_ID}.option.bastionSafeNether.@Tooltip[0]":
            "Keep basalt and blackstone ore out of bastion remnants.",
        f"text.autoconfig.{MOD_ID}.option.bastionSafeNether.@Tooltip[1]":
            "Bastions are built from those blocks, so without this their walls can",
        f"text.autoconfig.{MOD_ID}.option.bastionSafeNether.@Tooltip[2]":
            "turn into ore and invite you to mine the structure apart.",

        # Silent's Gems is the one mod with more than a single switch. Its overworld gems restyle
        # ore that already generates; its eight generating nether gems target netherrack only, so
        # our basalt and blackstone variants ADD ore exactly as our own gold and quartz do - and so
        # they get their own copies of the same two dials.
        f"text.autoconfig.{MOD_ID}.option.silentGems": "Silent's Gems: overworld variants",
        f"text.autoconfig.{MOD_ID}.option.silentGems.@Tooltip[0]":
            "Generate host-matched Silent's Gems ore. Does nothing unless the mod is installed.",
        f"text.autoconfig.{MOD_ID}.option.silentGems.@Tooltip[1]":
            "Purely a restyle: the amount of gem ore is identical either way.",

        f"text.autoconfig.{MOD_ID}.option.silentGemsNether": "Silent's Gems: nether variants (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.silentGemsNether.@Tooltip[0]":
            "Puts Silent's Gems nether gems in basalt and blackstone. That mod generates them in",
        f"text.autoconfig.{MOD_ID}.option.silentGemsNether.@Tooltip[1]":
            "netherrack only, so this ADDS ore, most noticeably in basalt deltas.",
        f"text.autoconfig.{MOD_ID}.option.silentGemsNether.@Tooltip[2]":
            "Turn off to leave the Nether exactly as Silent's Gems generates it.",

        f"text.autoconfig.{MOD_ID}.option.silentGemsNetherRarity": "Silent's Gems: nether rarity",
        f"text.autoconfig.{MOD_ID}.option.silentGemsNetherRarity.@Tooltip[0]":
            "One in this many basalt or blackstone gem veins becomes ore. 1 converts every vein.",
        f"text.autoconfig.{MOD_ID}.option.silentGemsNetherRarity.@Tooltip[1]":
            "Separate from the Nether page's dial, so gems and gold can be balanced apart.",

        f"text.autoconfig.{MOD_ID}.option.silentGemsNetherVeinSize": "Silent's Gems: nether vein size",
        f"text.autoconfig.{MOD_ID}.option.silentGemsNetherVeinSize.@Tooltip[0]":
            "How big each nether gem vein is, as a percent of the mod's own value. 100 is untouched.",
        f"text.autoconfig.{MOD_ID}.option.silentGemsNetherVeinSize.@Tooltip[1]":
            "As on the Nether page, this also shrinks the mod's own netherrack veins.",

        # One switch per remaining mod. All of these are pure restyles - the mod's ore already
        # generates in these host stones, so only its appearance changes.
        f"text.autoconfig.{MOD_ID}.option.denseMekanism": "Dense Mekanism: variants",
        f"text.autoconfig.{MOD_ID}.option.denseMekanism.@Tooltip[0]":
            "Generate host-matched Dense Mekanism ore. Does nothing unless the mod is installed.",
        f"text.autoconfig.{MOD_ID}.option.denseMekanism.@Tooltip[1]":
            "Mekanism's own ore is not covered: it uses a feature type this mod cannot extend.",

        f"text.autoconfig.{MOD_ID}.option.powah": "Powah: variants",
        f"text.autoconfig.{MOD_ID}.option.powah.@Tooltip":
            "Generate host-matched uraninite ore. Does nothing unless Powah is installed.",

        f"text.autoconfig.{MOD_ID}.option.tfmg": "Create: TFMG variants",
        f"text.autoconfig.{MOD_ID}.option.tfmg.@Tooltip":
            "Generate host-matched TFMG ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.expOres": "Exp Ores: variants",
        f"text.autoconfig.{MOD_ID}.option.expOres.@Tooltip[0]":
            "Generate host-matched experience ore. Does nothing unless Exp Ores is installed.",
        f"text.autoconfig.{MOD_ID}.option.expOres.@Tooltip[1]":
            "Includes basalt and blackstone, where that mod already generates it. Adds no ore.",

        f"text.autoconfig.{MOD_ID}.option.iceAndFire": "Ice and Fire: variants",
        f"text.autoconfig.{MOD_ID}.option.iceAndFire.@Tooltip":
            "Generate host-matched sapphire and silver ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.energizedPower": "Energized Power: variants",
        f"text.autoconfig.{MOD_ID}.option.energizedPower.@Tooltip":
            "Generate host-matched tin ore. Does nothing unless Energized Power is installed.",

        f"text.autoconfig.{MOD_ID}.option.things": "Things: variants",
        f"text.autoconfig.{MOD_ID}.option.things.@Tooltip":
            "Generate host-matched gleaming ore. Does nothing unless Things is installed.",

        f"text.autoconfig.{MOD_ID}.option.silentGear": "Silent Gear: variants",
        f"text.autoconfig.{MOD_ID}.option.silentGear.@Tooltip":
            "Generate host-matched bort ore. Does nothing unless Silent Gear is installed.",

        f"text.autoconfig.{MOD_ID}.option.createNewAge": "Create: New Age variants",
        f"text.autoconfig.{MOD_ID}.option.createNewAge.@Tooltip":
            "Generate host-matched thorium ore. Does nothing unless the mod is installed.",
    })
    write_json(os.path.join(root, "lang", "en_us.json"), lang)

    # Animation metadata for the overlays that need it. Written next to the texture, which is where
    # the vanilla sprite loader looks; nothing else has to know.
    textures = os.path.join(root, "textures", "block")
    for overlay, animation in ANIMATED_OVERLAYS.items():
        texture = os.path.join(textures, f"{overlay}_overlay.png")
        if not os.path.exists(texture):
            print(f"  !! {overlay}_overlay.png is missing, so its animation metadata was skipped")
            continue
        write_json(texture + ".mcmeta", {"animation": animation})
    print(f"  {count} blockstates, {count} block models, {count} item models, "
          f"{len(ANIMATED_OVERLAYS)} animated overlays")
    print(f"  {len(lang)} lang entries")


# Filled in by generate_data(): modded ores whose source loot table is not in that mod's build for
# this Minecraft version, so no variant data is written for them. Reported at the end of the run.
ABSENT_AT_THIS_VERSION = {}


def generate_data():
    """Loot tables and tags. Loot is TRANSFORMED from vanilla's own tables, never reconstructed."""

    if not os.path.exists(CLIENT_JAR):
        sys.exit(f"Client jar not found at {CLIENT_JAR} - needed to copy vanilla loot tables")

    ours = data_dir(MOD_ID)
    mc = data_dir("minecraft")

    mineable = []
    tool_tags = {}
    conv_block = {}
    conv_item = {}
    ores_in_ground = {}

    with zipfile.ZipFile(CLIENT_JAR) as jar:

        # Read the real vanilla tool tags once, then mirror membership per variant. NOT hardcoded
        # per ore, because it is not uniform by ore: overworld gold_ore is in needs_iron_tool but
        # nether_gold_ore is in none of them (wooden pickaxe), and coal is in none either.
        vanilla_tool_tags = {}
        for tag in TOOL_TAGS:
            with jar.open(f"data/minecraft/tags/blocks/{tag}.json") as handle:
                vanilla_tool_tags[tag] = set(json.load(handle)["values"])

        # Modded ores' tool tags come from THEIR jar - zinc is needs_iron_tool via Create's own
        # data, and hardcoding would have guessed stone-tool wrong. Read every mod we cover, not
        # just Create: the entries merge, and each mod only ever names its own blocks.
        modded_tool_tags = {}
        for mod_id, mod_jar in MOD_JARS.items():
            if not os.path.exists(mod_jar):
                print(f"  !! {mod_id} jar not found ({mod_jar}) - its tool tags fall back to needs_iron_tool")
                for ore in ORE_DEFS:
                    if ore.get("mod") != mod_id:
                        continue
                    for tier_ore in ore["tiers"].values():
                        modded_tool_tags.setdefault("needs_iron_tool", set()).add(f"{mod_id}:{tier_ore}")
                continue
            with zipfile.ZipFile(mod_jar) as mod_jar_zip:
                for tag in TOOL_TAGS:
                    try:
                        with mod_jar_zip.open(f"data/minecraft/tags/blocks/{tag}.json") as handle:
                            values = {str(v) for v in json.load(handle)["values"]}
                    except KeyError:
                        continue
                    modded_tool_tags.setdefault(tag, set()).update(values)
        for host, host_cfg, ore, vanilla in variants():
                name = variant_name(host, ore["name"])
                our_id = f"{MOD_ID}:{name}"
                mod = ore.get("mod")
                vanilla_id = f"{mod}:{vanilla}" if mod else f"minecraft:{vanilla}"

                # --- loot table -------------------------------------------------------------
                if mod is None:
                    # Read vanilla's table and swap only the identity bits. Ore loot is NOT uniform:
                    # copper is uniform 2-5, lapis 4-9, redstone 4-5 with uniform_bonus_count rather
                    # than ore_drops. Copying the real table is the only way to guarantee parity.
                    with jar.open(f"data/minecraft/{LOOT_DIR}/blocks/{vanilla}.json") as handle:
                        table = json.load(handle)
                    for pool in table.get("pools", []):
                        for entry in pool.get("entries", []):
                            for child in entry.get("children", []):
                                if any(
                                    cond.get("condition") == "minecraft:match_tool"
                                    for cond in child.get("conditions", [])
                                ):
                                    # Silk-touch branch drops the block itself - ours.
                                    child["name"] = our_id
                    # No random_sequence: 1.20.1's own tables do not have that field yet
                    # (checked against data/minecraft/loot_tables/blocks/iron_ore.json).
                else:
                    # Third-party ore: TRANSFORM THAT MOD'S OWN TABLE, exactly as we do for vanilla.
                    #
                    # This replaced "write our own in the vanilla iron_ore shape", which was correct
                    # only while zinc was the only modded ore, because Create's zinc table IS that
                    # shape. Mythic Metals' are not: set_count uniform 1-2 on the raw drop (so our
                    # own table would give HALF the yield), bonus_rolls, and rare secondary drops
                    # behind their own mythicmetals:random_chance_with_luck condition. Writing our
                    # own would be a visible balance break across every variant. All three mods we
                    # cover are MIT, and we credit them.
                    #
                    # Hard error rather than a fallback if the jar is missing: silently shipping a
                    # table with the wrong yield is exactly the class of bug this project keeps
                    # finding, and a generator run is a dev-time step where failing loudly is free.
                    modules = CONDITIONAL_LOOT_MODULES_BY_MOD.get(
                        mod, DEFAULT_CONDITIONAL_LOOT_MODULES)
                    if not modules:
                        # No build on any loader at this Minecraft version, so the variant can
                        # never register and no loot table is wanted anywhere. Skip before
                        # demanding a jar that would only be needed to transform a dead file.
                        continue
                    mod_jar_path = MOD_JARS.get(mod)
                    if not mod_jar_path or not os.path.exists(mod_jar_path):
                        raise SystemExit(
                            f"  !! cannot generate the loot table for {name}: the {mod} jar is "
                            f"required to transform its own table and was not found at "
                            f"{mod_jar_path}. Set the matching *_JAR environment variable."
                        )
                    with zipfile.ZipFile(mod_jar_path) as mod_zip:
                        loot_path = f"data/{mod}/{LOOT_DIR}/blocks/{vanilla}.json"
                        try:
                            with mod_zip.open(loot_path) as handle:
                                table = json.load(handle)
                        except KeyError:
                            # The ore does not exist in THAT mod's build for THIS Minecraft
                            # version. Skip it and report, rather than failing the whole run or
                            # silently writing a table for a block nobody has.
                            #
                            # This is not hypothetical: Silent's Gems 4.7.0 (1.20.1) has no chaos,
                            # garnet, pearl, tanzanite or aquamarine ore at all, and it names its
                            # nether ores <gem>_nether_ore where the newer builds use
                            # nether_<gem>_ore. An ore def is shared across branches, so per
                            # version it has to be checked against that version's jar.
                            ABSENT_AT_THIS_VERSION.setdefault(mod, []).append(f"{name} ({vanilla})")
                            continue
                    for pool in table.get("pools", []):
                        for entry in pool.get("entries", []):
                            for child in entry.get("children", []):
                                if any(
                                    cond.get("condition") == "minecraft:match_tool"
                                    for cond in child.get("conditions", [])
                                ):
                                    # Silk-touch branch drops the block itself - ours.
                                    child["name"] = our_id
                    # Fabric's conditions keep it inert when the mod is absent. There is NO
                    # Forge key here, and that is not an oversight: Forge 1.20.1 does not honour
                    # conditions on loot tables at all, so the Forge copy is gated by shipping it
                    # in a per-mod built-in datapack instead. See FORGE_PACK_MODS.
                    fabric_table = {
                        "fabric:load_conditions": [
                            {"condition": "fabric:registry_contains",
                             "registry": "minecraft:block", "values": [vanilla_id]}
                        ],
                        **table,
                    }

                if mod:
                    # Conditional table: goes only to the loaders that can host that mod at this
                    # Minecraft version, never to common.
                    if "fabric" in modules:
                        write_json(os.path.join(conditional_data_dir("fabric", MOD_ID),
                                                LOOT_DIR, "blocks", f"{name}.json"), fabric_table)
                    if "forge" in modules:
                        # Into that mod's own built-in datapack, with no condition keys: the pack is
                        # only offered to the game when the mod is loaded, so the file is never read
                        # otherwise. Forge 1.20.1 cannot gate it any other way.
                        write_json(os.path.join(forge_pack_data_dir(mod, MOD_ID),
                                                LOOT_DIR, "blocks", f"{name}.json"), table)
                else:
                    write_json(os.path.join(ours, LOOT_DIR, "blocks", f"{name}.json"), table)

                # --- tags -------------------------------------------------------------------
                # A modded variant's block only exists when its mod is loaded, so its tag entries
                # are optional objects - a plain string would log a tag error without the mod.
                entry = {"id": our_id, "required": False} if mod else our_id
                mineable.append(entry)
                source_tags = modded_tool_tags if mod else vanilla_tool_tags
                for tag, members in source_tags.items():
                    if vanilla_id in members:
                        tool_tags.setdefault(tag, []).append(entry)
                conv_block.setdefault(ore["name"], []).append(entry)
                conv_item.setdefault(ore["name"], []).append(entry)
                # c:ores_in_ground/<stone|deepslate|netherrack> - keyed on the ore we stand in for,
                # so consumers treat a variant exactly like its counterpart.
                ground = {"stone": "stone", "deepslate": "deepslate", "nether": "netherrack"}[host_cfg["tier"]]
                ores_in_ground.setdefault(ground, []).append(entry)

    # Tags MERGE with vanilla's by default (no "replace": true), so these add to the existing lists
    # rather than clobbering them. Getting this wrong would unregister 417 vanilla pickaxe entries.
    write_json(os.path.join(mc, *TAG_BLOCK_DIR, "mineable", "pickaxe.json"), {"values": mineable})
    for tag, values in tool_tags.items():
        write_json(os.path.join(mc, *TAG_BLOCK_DIR, f"{tag}.json"), {"values": values})

    all_ids = sorted(mineable, key=lambda e: e["id"] if isinstance(e, dict) else e)
    # Written into BOTH common-tag namespaces, because 1.20.x is the era where the ecosystem is
    # split: Fabric mods read c:ores, Forge mods read forge:ores. The copy a given loader ignores
    # is just a tag nobody queries.
    for namespace in CONVENTION_NAMESPACES:
        conv = data_dir(namespace)
        write_json(os.path.join(conv, *TAG_BLOCK_DIR, "ores.json"), {"values": all_ids})
        write_json(os.path.join(conv, *TAG_ITEM_DIR, "ores.json"), {"values": all_ids})
        for ore, values in conv_block.items():
            write_json(os.path.join(conv, *TAG_BLOCK_DIR, "ores", f"{ore}.json"), {"values": values})
        for ore, values in conv_item.items():
            write_json(os.path.join(conv, *TAG_ITEM_DIR, "ores", f"{ore}.json"), {"values": values})
        for ground, values in ores_in_ground.items():
            write_json(
                os.path.join(conv, *TAG_BLOCK_DIR, "ores_in_ground", f"{ground}.json"),
                {"values": values},
            )

    # A pack.mcmeta per built-in datapack. Without it Pack.readMetaAndCreate returns null and the
    # pack is silently skipped, which would look exactly like the loot tables never being written.
    #
    # pack_format 15 is 1.20.1's data format. NO supported_formats / min_format / max_format here:
    # 1.20.1 knows only pack_format (grepped from the client jar - supported_formats arrives at
    # 1.21.1 and min_format/max_format at 1.21.11), and an unknown key in a pack it is about to
    # load is not worth the risk for a pack that only ever ships beside this one jar.
    for mod in FORGE_PACK_MODS:
        root = forge_pack_dir(mod)
        if not os.path.isdir(os.path.join(root, "data")):
            continue                    # nothing landed here, so do not leave a stray pack.mcmeta
        write_json(os.path.join(root, "pack.mcmeta"), {
            "pack": {
                "description": f"Seamless Ores ore variants for {MODS[mod]['display']}",
                "pack_format": PACK_FORMAT,
            }
        })
    print(f"  forge built-in datapacks: "
          f"{', '.join(m for m in FORGE_PACK_MODS if os.path.isdir(os.path.join(forge_pack_dir(m), 'data'))) or 'none'}")

    if ABSENT_AT_THIS_VERSION:
        print("  !! NOT PRESENT in these mods' 1.20.1 builds, so no variant data was written:")
        for mod, items in sorted(ABSENT_AT_THIS_VERSION.items()):
            print(f"     {mod}: {len(items)} - {', '.join(sorted(items))}")
        print("     Remove them from ORE_DEFS and OreType.java for this branch, or they register "
              "as blocks that can never generate.")

    print(f"  {len(mineable)} loot tables")
    print(f"  tags: mineable/pickaxe, {', '.join(sorted(tool_tags))}, "
          f"{'/'.join(CONVENTION_NAMESPACES)}:ores (+{len(conv_block)} per-ore), "
          f"ores_in_ground ({', '.join(sorted(ores_in_ground))})")


def generate_textures():
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is required for --textures. Run this with 'py -3.14'.")

    if not os.path.exists(CLIENT_JAR):
        sys.exit(f"Client jar not found at {CLIENT_JAR}")

    out_dir = os.path.join(assets_dir(), "textures", "block")
    os.makedirs(out_dir, exist_ok=True)

    # Each overlay is diffed against its OWN base: overworld ores against stone, nether ores against
    # netherrack. Diffing nether gold against stone would keep almost every pixel and produce a
    # texture that hides the host stone entirely. Modded ore textures come from THEIR jar.
    needed = {}
    for ore in ORE_DEFS:
        if ore.get("mod") and not os.path.exists(MOD_JARS.get(ore["mod"], "")):
            print(f"  !! {ore['mod']} jar not found - skipping {ore['overlay']}_overlay extraction")
            continue
        needed[ore["overlay"]] = (ore["source"], ore["base"], ore.get("mod"))

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(CLIENT_JAR) as jar:
            wanted = {f"{s}.png" for s, _, m in needed.values() if not m} | {f"{b}.png" for _, b, _ in needed.values()}
            for filename in sorted(wanted):
                member = f"assets/minecraft/textures/block/{filename}"
                with jar.open(member) as src, open(os.path.join(tmp, filename), "wb") as dst:
                    dst.write(src.read())
        modded_sources = {f"{s}.png": m for s, _, m in needed.values() if m}
        for needed_mod in sorted({m for m in modded_sources.values()}):
            if not os.path.exists(MOD_JARS.get(needed_mod, "")):
                continue
            with zipfile.ZipFile(MOD_JARS[needed_mod]) as create_jar:
                for filename, mod in ((f, m) for f, m in modded_sources.items() if m == needed_mod):
                    member = f"assets/{mod}/textures/block/{filename}"
                    with create_jar.open(member) as src, open(os.path.join(tmp, filename), "wb") as dst:
                        dst.write(src.read())

        for overlay_name, (source, base_name, _mod) in sorted(needed.items()):
            # NEVER overwrite an overlay that already exists. Most of them have been hand cleaned
            # after extraction, and silently replacing that work with a fresh machine diff is a
            # one-way loss - the old behaviour made --textures a destructive flag nobody could run
            # safely. Delete the PNG to force a re-extraction of that one.
            if os.path.exists(os.path.join(out_dir, f"{overlay_name}_overlay.png")):
                continue
            base = Image.open(os.path.join(tmp, f"{base_name}.png")).convert("RGBA")
            ore_img = Image.open(os.path.join(tmp, f"{source}.png")).convert("RGBA")
            if ore_img.size != base.size:
                print(f"  !! {source}.png is {ore_img.size}, {base_name} is {base.size} - skipped")
                continue

            overlay = Image.new("RGBA", ore_img.size, (0, 0, 0, 0))
            kept = 0
            for y in range(ore_img.height):
                for x in range(ore_img.width):
                    pixel = ore_img.getpixel((x, y))
                    reference = base.getpixel((x, y))
                    if sum(abs(a - b) for a, b in zip(pixel[:3], reference[:3])) > THRESHOLD:
                        overlay.putpixel((x, y), pixel)
                        kept += 1

            overlay.save(os.path.join(out_dir, f"{overlay_name}_overlay.png"))
            print(f"  {overlay_name}_overlay.png  {kept}/{ore_img.width * ore_img.height} px kept"
                  f"  (from {source} over {base_name})")


OVERWORLD_HOSTS = ["granite", "diorite", "andesite", "tuff"]
NETHER_HOSTS = ["basalt", "blackstone"]


def _table(hosts, rows):
    """A markdown table: one column per host, one row per (label, {host: block id})."""
    out = ["| | " + " | ".join(hosts) + " |",
           "|---|" + "---|" * len(hosts)]
    for label, ids in rows:
        cells = [f"`{ids[h]}`" if h in ids else " " for h in hosts]
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    return out


def _block_list():
    """The full block list, grouped by the mod that owns the ore.

    GENERATED rather than hand written, and that is the point. The list ran to 295 ids across twelve
    sources while the README still said 64, because nothing forced the two to agree. Anything here
    that a human would have to retype when an ore is added belongs in this function instead.
    """
    # source mod id (None = vanilla) -> list of (ore def, {host: block id}), in ORE_DEFS order
    grouped = {}
    for host, host_cfg, ore, _vanilla in variants():
        entry = grouped.setdefault(ore.get("mod"), {}).setdefault(id(ore), (ore, {}))
        entry[1][host] = variant_name(host, ore["name"])

    order = [None] + [m for m in MODS if m in grouped]
    unknown = [m for m in grouped if m is not None and m not in MODS]
    if unknown:
        raise SystemExit(f"ORE_DEFS names mod(s) missing from MODS: {sorted(unknown)}")

    lines = [f"**{len(list(variants()))} blocks** in the `{MOD_ID}` namespace.", ""]
    for mod in order:
        if mod not in grouped:
            continue
        entries = list(grouped[mod].values())
        if mod is None:
            heading, note = "Vanilla", ""
        else:
            heading = MODS[mod]["display"]
            note = f", requires `{mod}`"

        for hosts, suffix in ((OVERWORLD_HOSTS, "Overworld"), (NETHER_HOSTS, "Nether")):
            rows = [(title(ore["name"]), {h: i for h, i in ids.items() if h in hosts})
                    for ore, ids in entries]
            rows = [r for r in rows if r[1]]
            if not rows:
                continue
            used = [h for h in hosts if any(h in ids for _l, ids in rows)]
            lines.append(f"**{heading}, {suffix}{note}**")
            lines.append("")
            lines += _table(used, rows)
            lines.append("")
    return lines + _loader_counts()


def _loader_counts():
    """How many blocks each loader can actually reach, from the same per-version mod/loader matrix
    that decides where the conditional loot tables ship.

    Derived rather than written down because it is the single most version-specific fact in this
    README: which mods have a build for a given loader flips between Minecraft versions, and a
    number copied forward from another branch is wrong without looking wrong.
    """
    per_mod = {}
    for _host, _cfg, ore, _v in variants():
        per_mod[ore.get("mod")] = per_mod.get(ore.get("mod"), 0) + 1
    vanilla = per_mod.pop(None, 0)

    rows = []
    for loader in ("fabric", "neoforge", "forge"):
        total = vanilla
        available = []
        for mod, count in per_mod.items():
            modules = CONDITIONAL_LOOT_MODULES_BY_MOD.get(mod, DEFAULT_CONDITIONAL_LOOT_MODULES)
            if loader in modules:
                total += count
                available.append(MODS[mod]["display"])
        rows.append((loader, total, sorted(available)))

    lines = [
        "A variant is registered only when the mod that owns its ore is installed, so how many of",
        "these you can actually see depends on which mods have a build for your loader at this",
        "Minecraft version:",
        "",
        "| Loader | Blocks | Supported mods available here |",
        "|---|---|---|",
    ]
    # Spelled out rather than capitalize()d: that would give "Neoforge".
    display = {"fabric": "Fabric", "neoforge": "NeoForge", "forge": "Forge"}
    for loader, total, available in rows:
        names = ", ".join(available) if available else "none at this Minecraft version"
        lines.append(f"| {display[loader]} | {total} | {names} |")
    return lines + [
        "",
        "The registered block set is derived from which mods are loaded rather than from config, so",
        "a client and a server running the same mods always agree and nobody is kicked on join.",
        "",
    ]


def _overlay_list():
    """Every overlay texture a resource pack would need to replace, and how many there are."""
    overlays = sorted({overlay_for(ore, host_cfg) for _h, host_cfg, ore, _v in variants()})
    return [
        f"Every variant of one ore shares a single overlay texture, so covering all "
        f"{len(list(variants()))} blocks takes **{len(overlays)} PNG files**:",
        "",
        "```",
        f"assets/{MOD_ID}/textures/block/<ore>_overlay.png",
        "```",
        "",
        "where `<ore>` is one of:",
        "",
    ] + ["".join(f"`{o}` " for o in overlays).strip(), ""]


def _credits():
    """Attribution for the derived overlay art, per mod, with the licence read from its own jar."""
    used = {ore.get("mod") for ore in ORE_DEFS} - {None}
    lines = [
        "The vanilla ore overlays are derived from Minecraft's own textures and remain Mojang's",
        "property. Each supported mod's overlay is derived from that mod's own ore texture, so it",
        "is theirs and is used under the licence shown:",
        "",
        "| Mod | Author | Licence |",
        "|---|---|---|",
    ]
    for mod in MODS:
        if mod not in used:
            continue
        info = MODS[mod]
        # A bare "-" for an unstated author. A dash is normally banned from public-facing text, but
        # a column rule / not-applicable marker inside a markdown table is the documented exception.
        lines.append(f"| {info['display']} | {info['author'] or '-'} | {info['licence']} |")
    return lines + [""]


def generate_readme():
    """Rewrites the generated sections of README.md in place, leaving the prose alone.

    Only the regions between the markers are touched, so hand-written explanation survives. A
    marker that goes missing is an error rather than a silent no-op: the failure mode otherwise is
    a README that quietly stops being updated, which is exactly how it came to claim 64 blocks.
    """
    path = os.path.join(repo_root(), "README.md")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    sections = {
        "block-list": _block_list(),
        "overlay-list": _overlay_list(),
        "credits": _credits(),
    }
    for name, lines in sections.items():
        begin, end = f"<!-- BEGIN GENERATED {name} -->", f"<!-- END GENERATED {name} -->"
        if begin not in text or end not in text:
            raise SystemExit(f"README.md is missing the '{name}' markers")
        head, rest = text.split(begin, 1)
        _stale, tail = rest.split(end, 1)
        text = head + begin + "\n" + "\n".join(lines).rstrip() + "\n" + end + tail

    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print(f"  README.md: {len(list(variants()))} blocks, "
          f"{len({overlay_for(o, c) for _h, c, o, _v in variants()})} overlays, "
          f"{len({o.get('mod') for o in ORE_DEFS} - {None})} mods credited")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--textures",
        action="store_true",
        help="extract overlay PNGs that do not exist yet (existing ones are never overwritten)",
    )
    args = parser.parse_args()

    print("Generating client assets...")
    generate_json()
    print("Generating loot tables and tags...")
    generate_data()
    print("Updating README...")
    generate_readme()

    if args.textures:
        print("Extracting overlay textures...")
        generate_textures()
    else:
        print("Skipped textures (pass --textures to extract any that are missing).")


if __name__ == "__main__":
    main()
