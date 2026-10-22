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
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

# The overlay art lives once, in the repository's shared/textures pool (shared/tools/assetgen.py).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "shared", "tools"))
import parity  # noqa: E402
from assetgen import (POOL, TOOL_TAGS, assert_no_dashes, era_file, jar, jar_tags,  # noqa: E402
                      look_models, read_mod_tags, defer_to_source, silk_touch_to, stone_name, texture_path, title,
                      write_json, write_texture_json)
import placed  # noqa: E402
import renamed  # noqa: E402
import retired  # noqa: E402

MOD_ID = "seamlessores"

BAND = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

# Classic Forge's datapack condition key. SINGULAR, and it takes ONE object rather than an array -
# it is ICondition.DEFAULT_FIELD, verified as "forge:condition" in forge 52 and 61 alike. Spelled
# differently again on 1.20.x Forge (unnamespaced "conditions", array), so re-verify against the
# real jar before carrying this to an older branch.
FORGE_CONDITION_KEY = "forge:condition"

# Colour-distance (summed per-channel) above which a pixel counts as ore rather than shaded stone.
# 0 keeps 141/256 px for iron and hazes over granite; 60 keeps 76 and looks right; 90 eats real blobs.
THRESHOLD = 60

CLIENT_JAR = os.path.expanduser(
    "~/.gradle/caches/neoformruntime/artifacts/minecraft_1.21.4_client.jar"
)

# Create (Create Fly, mod id 'create') jar - source of the zinc loot table shape and the zinc ore
# texture the overlay is derived from. Machine-specific default, override with the CREATE_JAR env
# var. Licence: the jar ships CC0 at root plus the original Create MIT - deriving the overlay is
# fine; keep the attribution line in the README. When the jar is missing, zinc JSON still generates
# (the loot shape is baked below, verified identical to vanilla iron_ore's) but the texture step
# skips zinc.
CREATE_JAR = jar("create-1.21.1-6.0.10.jar", "CREATE_JAR")

# Mythic Upgrades (mod id 'mythicupgrades', MIT, 26.2 on all four loaders). Source of its ore
# textures and the facts behind the entries below. Override with MYTHIC_UPGRADES_JAR.
MYTHIC_UPGRADES_JAR = jar("mythicupgrades-neoforge-1.21.1-5.1.1.jar", "MYTHIC_UPGRADES_JAR")

# Mythic Metals (mod id 'mythicmetals', MIT). Fabric only on every version it has ever shipped, so
# its variants only ever register there. Source of its ore textures, loot tables and tool tags.
SILENT_GEMS_JAR = jar("silentgems-26.1.2-neoforge-5.1.4.jar", "SILENT_GEMS_JAR")

MYTHIC_METALS_JAR = jar("mythicmetals-0.25.3+1.21.4.jar", "MYTHIC_METALS_JAR")

# Every third-party jar we read, keyed by the mod id used in the ORES table below. A missing jar is
# a warning rather than an error: the JSON still generates, only the texture step is skipped.
DENSEMEKANISM_JAR = jar("densemekanism-1.21.1-1.2.jar", "DENSEMEKANISM_JAR")

POWAH_JAR = jar("Powah-7.0.4-alpha.jar", "POWAH_JAR")

TFMG_JAR = jar("tfmg-1.2.2.jar", "TFMG_JAR")

ENERGIZEDPOWER_JAR = jar("energizedpower-3.0.0+26.2.x-neoforge.jar", "ENERGIZEDPOWER_JAR")

THINGS_JAR = jar("things-0.4.2+1.21.jar", "THINGS_JAR")

SILENTGEAR_JAR = jar("silent-gear-26.1.2-neoforge-4.2.2.jar", "SILENTGEAR_JAR")

CREATE_NEW_AGE_JAR = jar("create-new-age-1.2.0+neoforge-mc1.21.1.jar", "CREATE_NEW_AGE_JAR")

# Sept 2026 wave: Tech Reborn only. Its three builds in this range (5.12.9 for 1.21.4, 5.13.4 for
# 1.21.5, 5.14.2 for 1.21.6-1.21.8) ship byte-identical ores, loot, tags, textures and worldgen, and
# none has uranium, so the 1.21.4 build serves the whole jar.
TECHREBORN_JAR = jar("1.21.4-TechReborn-5.12.9.jar", "TECHREBORN_JAR")
# Extreme Reactors 2.4.20 is its only build in this range: NeoForge, 1.21.4, CurseForge only. Its ores,
# loot, textures and worldgen are identical to 2.4.9 at 1.21.1; only its c:ores tag gained deepslate
# yellorite.
EXTREME_REACTORS_JAR = jar("1.21.4-ExtremeReactors2-1.21.4-2.4.20.jar", "EXTREME_REACTORS_JAR")

MOD_JARS = {"create_new_age": CREATE_NEW_AGE_JAR,
            "techreborn": TECHREBORN_JAR,
            "bigreactors": EXTREME_REACTORS_JAR,
            "silentgear": SILENTGEAR_JAR,
            "things": THINGS_JAR,
            "energizedpower": ENERGIZEDPOWER_JAR,
            "tfmg": TFMG_JAR,
            "powah": POWAH_JAR,
            "densemekanism": DENSEMEKANISM_JAR,
            "create": CREATE_JAR, "mythicupgrades": MYTHIC_UPGRADES_JAR,
            "silentgems": SILENT_GEMS_JAR,
            "mythicmetals": MYTHIC_METALS_JAR}

# How each host stone is drawn, which only this script needs: the host table itself (which stones,
# which tier, which ores) is READ from HostStone.java (shared/tools/placed.py), so the blocks that
# register and the files generated here cannot drift apart. A host with several looks must be mirrored
# exactly, or its ore is the one tile that never varies. Read from each stone's own blockstate and
# models in this band's jars (assetgen.look_models has the looks).
#   column: basalt AND blackstone are cube_column blocks in vanilla (side + _top textures), and so is
#   Twigs' rhyolite (a pillar, placed upright); the side sprite on all six faces mismatches the tops.
HOST_LOOK = {
    "minecraft:granite": ("single", "minecraft:block/granite"),
    "minecraft:diorite": ("single", "minecraft:block/diorite"),
    "minecraft:andesite": ("single", "minecraft:block/andesite"),
    "minecraft:tuff": ("single", "minecraft:block/tuff"),
    "minecraft:dripstone_block": ("single", "minecraft:block/dripstone_block"),
    "minecraft:basalt": ("column", "minecraft:block/basalt_side", "minecraft:block/basalt_top"),
    "minecraft:blackstone": ("column", "minecraft:block/blackstone", "minecraft:block/blackstone_top"),
    "blockus:limestone": ("single", "blockus:block/limestone"),
    "blockus:marble": ("single", "blockus:block/marble"),
    "blockus:bluestone": ("single", "blockus:block/bluestone"),
    "blockus:viridite": ("single", "blockus:block/viridite"),
    "create:asurine": ("textures4", "create:block/palettes/stone_types/natural/asurine_"),
    "create:crimsite": ("textures4", "create:block/palettes/stone_types/natural/crimsite_"),
    "create:limestone": ("single", "create:block/palettes/stone_types/limestone"),
    "create:ochrum": ("textures4", "create:block/palettes/stone_types/natural/ochrum_"),
    "create:scorchia": ("single", "create:block/palettes/stone_types/scorchia"),
    "create:scoria": ("single", "create:block/palettes/stone_types/scoria"),
    "create:veridium": ("textures4", "create:block/palettes/stone_types/natural/veridium_"),
    "minecraft:calcite": ("single", "minecraft:block/calcite"),
    "minecraft:smooth_basalt": ("single", "minecraft:block/smooth_basalt"),
    "promenade:asphalt": ("single", "promenade:block/asphalt"),
    "promenade:blunite": ("single", "promenade:block/blunite"),
    "wilderwild:gabbro": ("mirrored_turned", "wilderwild:block/gabbro"),
    "biomeswevegone:dacite": ("single", "biomeswevegone:block/dacite"),
    "biomeswevegone:white_dacite": ("single", "biomeswevegone:block/white_dacite"),
    "biomeswevegone:red_rock": ("single", "biomeswevegone:block/red_rock"),
}

# The mods that PLACE a host stone, for the README and the config screen, and the jar each one's
# stone textures are read from (a translucent ore's overlay is painted over them). Where each exists
# here, on both platforms: so-older-band-stone-survey in the maintainer notes.
STONE_MODS = {
    # Deep blackstone: the game's rock, laid by Terralith's caves (the mod or its datapack).
    "minecraft": {"display": "Terralith", "bands": "its mod or datapack, Fabric and NeoForge"},
    "blockus": {"display": "Blockus", "bands": "Fabric, read from its 1.21.10 build"},
    "create": {"display": "Create", "bands": "Create Fly, Fabric, read from its 1.21.8 build"},
    "promenade": {"display": "Promenade", "bands": "Fabric, read from its 1.21.9 build"},
    "wilderwild": {"display": "Wilder Wild", "bands": "Fabric, read from its 1.21.10 build"},
    "biomeswevegone": {"display": "Oh The Biomes We've Gone", "bands": "Fabric and NeoForge, its 1.21.4 build"},
}
STONE_JARS = {"minecraft": CLIENT_JAR,
              "blockus": jar("blockus-2.14.1+1.21.10.jar"),
              "create": jar("create-fly-1.21.8-6.0.9-2.jar"),
              "promenade": jar("1.21.4-promenade-5.3.1.jar"),
              "wilderwild": jar("WilderWild-4.2.1-mc1.21.10.jar"),
              "biomeswevegone": jar("Oh-The-Biomes-Weve-Gone-NeoForge-3.2.5.jar")}
HOST_TABLE = era_file(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                   "common"), BAND, "java/com/chillpavz/seamlessores/content/HostStone.java")

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
# same as animating a Fusion connecting sheet, which crashes the game on load.
ANIMATED_OVERLAYS = {
    "stormyx": {"frametime": 20, "interpolate": True},              # 5 frames, matches stormyx_ore
    "unobtainium_deepslate": {"frametime": 60, "interpolate": True},  # 4 frames, deepslate ore only
    # Extreme Reactors' yellorite: 6 frames played in a custom order (a pulse, then a long rest),
    # copied verbatim from its own yellorite_ore.png.mcmeta. The frame list IS the animation here,
    # so frametime alone would play the pulse back to back with no rest.
    "yellorite": {"frametime": 2, "frames": [0, 1, 2, 3, 4, 5, 5, 5, 4, 3, 2, 1,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0]},
    # Extreme Reactors' benitoite: 10 frames, same pulse-and-rest shape, from its own mcmeta.
    "benitoite": {"frametime": 2, "frames": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 8, 7, 6, 5, 4, 3, 2, 1,
                                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
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
    "densemekanism":  {"display": "Dense Mekanism",    "category": "dense_mekanism",
                       "licence": "MIT",          "author": ""},
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
    "things":         {"display": "Things",            "category": "things",
                       "licence": "MIT",          "author": "glisco"},
    "techreborn":     {"display": "Tech Reborn",       "category": "tech_reborn",
                       "licence": "MIT",          "author": "Team Reborn, modmuss50, drcrazy"},
    "bigreactors":    {"display": "Extreme Reactors",  "category": "extreme_reactors",
                       "licence": "MIT",          "author": "ZeroNoRyouki"},
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
    # No dripstone emerald: emerald generates in the mountains only, where dripstone caves never reach.
    {"name": "emerald",  "overlay": "emerald",  "source": "emerald_ore",  "base": "stone",
     "skip_hosts": ["dripstone"],
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
    # target ahead of its deepslate tag entry, so tuff is already seamless there: skipped.
    {"name": "orichalcum", "overlay": "orichalcum", "source": "orichalcum_ore", "base": "stone",
     "mod": "mythicmetals", "skip_hosts": ["tuff"],
     "tiers": {"stone": "orichalcum_ore", "deepslate": "deepslate_orichalcum_ore"}},
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
    {"name": "chaos",                   "overlay": "chaos",                   "source": "chaos_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:chaos_essence",
     "tiers": {"stone": "chaos_ore", "deepslate": "deepslate_chaos_ore"}},
    {"name": "garnet",                  "overlay": "garnet",                  "source": "garnet_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:garnet",
     "tiers": {"stone": "garnet_ore", "deepslate": "deepslate_garnet_ore"}},
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
    {"name": "pearl",                   "overlay": "pearl",                   "source": "pearl_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:pearl",
     "tiers": {"stone": "pearl_ore", "deepslate": "deepslate_pearl_ore"}},
    {"name": "rose_quartz",             "overlay": "rose_quartz",             "source": "rose_quartz_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:rose_quartz",
     "tiers": {"stone": "rose_quartz_ore", "deepslate": "deepslate_rose_quartz_ore"}},
    # Ruby and sapphire share a block NAME with Mythic Upgrades' nether ruby and sapphire (the hosts never
    # overlap), but NOT the art. The overlay key is separate, or both write ruby_overlay.png and one mod's
    # variants wear the other's art: exactly what happened until Sept 2026 (87-89 px apart).
    {"name": "ruby",                    "overlay": "silents_ruby",            "source": "ruby_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:ruby",
     "tiers": {"stone": "ruby_ore", "deepslate": "deepslate_ruby_ore"}},
    {"name": "sapphire",                "overlay": "silents_sapphire",        "source": "sapphire_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:sapphire",
     "tiers": {"stone": "sapphire_ore", "deepslate": "deepslate_sapphire_ore"}},
    {"name": "tanzanite",               "overlay": "tanzanite",               "source": "tanzanite_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:tanzanite",
     "tiers": {"stone": "tanzanite_ore", "deepslate": "deepslate_tanzanite_ore"}},
    {"name": "turquoise",               "overlay": "turquoise",               "source": "turquoise_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:turquoise",
     "tiers": {"stone": "turquoise_ore", "deepslate": "deepslate_turquoise_ore"}},
    {"name": "white_diamond",           "overlay": "white_diamond",           "source": "white_diamond_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:white_diamond",
     "tiers": {"stone": "white_diamond_ore", "deepslate": "deepslate_white_diamond_ore"}},
    {"name": "silents_aquamarine",      "overlay": "silents_aquamarine",      "source": "aquamarine_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:aquamarine",
     "tiers": {"stone": "aquamarine_ore", "deepslate": "deepslate_aquamarine_ore"}},
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
    {"name": "dense_fluorite", "overlay": "dense_fluorite", "source": "dense_fluorite_ore", "base": "stone",
     "mod": "densemekanism",
     "tiers": {"stone": "dense_fluorite_ore", "deepslate": "dense_deepslate_fluorite_ore"}},
    {"name": "dense_lead", "overlay": "dense_lead", "source": "dense_lead_ore", "base": "stone",
     "mod": "densemekanism",
     "tiers": {"stone": "dense_lead_ore", "deepslate": "dense_deepslate_lead_ore"}},
    {"name": "dense_osmium", "overlay": "dense_osmium", "source": "dense_osmium_ore", "base": "stone",
     "mod": "densemekanism",
     "tiers": {"stone": "dense_osmium_ore", "deepslate": "dense_deepslate_osmium_ore"}},
    {"name": "dense_tin", "overlay": "dense_tin", "source": "dense_tin_ore", "base": "stone",
     "mod": "densemekanism",
     "tiers": {"stone": "dense_tin_ore", "deepslate": "dense_deepslate_tin_ore"}},
    {"name": "dense_uranium", "overlay": "dense_uranium", "source": "dense_uranium_ore", "base": "stone",
     "mod": "densemekanism",
     "tiers": {"stone": "dense_uranium_ore", "deepslate": "dense_deepslate_uranium_ore"}},
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
    {"name": "alexandrite", "overlay": "alexandrite", "source": "nether_alexandrite_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_alexandrite_ore"}},
    {"name": "black_diamond", "overlay": "black_diamond", "source": "nether_black_diamond_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_black_diamond_ore"}},
    {"name": "carnelian", "overlay": "carnelian", "source": "nether_carnelian_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_carnelian_ore"}},
    {"name": "silents_citrine", "overlay": "silents_citrine", "source": "nether_citrine_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_citrine_ore"}},
    {"name": "iolite", "overlay": "iolite", "source": "nether_iolite_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_iolite_ore"}},
    {"name": "moldavite", "overlay": "moldavite", "source": "nether_moldavite_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_moldavite_ore"}},
    {"name": "pearl", "overlay": "pearl", "source": "nether_pearl_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_pearl_ore"}},
    {"name": "tanzanite", "overlay": "tanzanite", "source": "nether_tanzanite_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_tanzanite_ore"}},
    # Tech Reborn (Fabric only, 1.21.4 to 1.21.8). Its eight overworld ores all target the vanilla
    # replaceables tags: a pure restyle. No uranium in this range. The four end stone ores are not
    # covered. Prefixed where the plain name is already taken; the names match every other branch.
    {"name": "techreborn_bauxite", "overlay": "techreborn_bauxite", "source": "bauxite_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "bauxite_ore", "deepslate": "deepslate_bauxite_ore"}},
    {"name": "galena", "overlay": "galena", "source": "galena_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "galena_ore", "deepslate": "deepslate_galena_ore"}},
    {"name": "iridium", "overlay": "iridium", "source": "iridium_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "iridium_ore", "deepslate": "deepslate_iridium_ore"}},
    {"name": "techreborn_lead", "overlay": "techreborn_lead", "source": "lead_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "lead_ore", "deepslate": "deepslate_lead_ore"}},
    {"name": "techreborn_ruby", "overlay": "techreborn_ruby", "source": "ruby_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "ruby_ore", "deepslate": "deepslate_ruby_ore"}},
    {"name": "techreborn_sapphire", "overlay": "techreborn_sapphire", "source": "sapphire_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "sapphire_ore", "deepslate": "deepslate_sapphire_ore"}},
    {"name": "techreborn_silver", "overlay": "techreborn_silver", "source": "silver_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "silver_ore", "deepslate": "deepslate_silver_ore"}},
    {"name": "techreborn_tin", "overlay": "techreborn_tin", "source": "tin_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "tin_ore", "deepslate": "deepslate_tin_ore"}},
    # Extreme Reactors: yellorite, animated (see ANIMATED_OVERLAYS). Anglesite is end stone.
    {"name": "yellorite", "overlay": "yellorite", "source": "yellorite_ore", "base": "stone",
     "mod": "bigreactors",
     "tiers": {"stone": "yellorite_ore", "deepslate": "deepslate_yellorite_ore"}},
    # Nether ores that ADD ore: each targets netherrack only, so basalt and blackstone variants put
    # ore where the mod places none. Behind that mod's own nether switch, and thinned by the same
    # netherOreRarity / netherVeinSize dials as our gold and quartz.
    {"name": "cinnabar", "overlay": "cinnabar", "source": "cinnabar_ore", "base": "netherrack",
     "mod": "techreborn",
     "tiers": {"nether": "cinnabar_ore"}},
    {"name": "pyrite", "overlay": "pyrite", "source": "pyrite_ore", "base": "netherrack",
     "mod": "techreborn",
     "tiers": {"nether": "pyrite_ore"}},
    {"name": "sphalerite", "overlay": "sphalerite", "source": "sphalerite_ore", "base": "netherrack",
     "mod": "techreborn",
     "tiers": {"nether": "sphalerite_ore"}},
    {"name": "benitoite", "overlay": "benitoite", "source": "benitoite_ore", "base": "netherrack",
     "mod": "bigreactors",
     "tiers": {"nether": "benitoite_ore"}},
]

# This generator writes ONE band of the 1.21 folder: everything it emits goes to
# <module>/src/<BAND>/resources, which only that band's build compiles (see settings.gradle).
BAND_LOADERS = {"1.21.1": ("fabric", "neoforge", "forge"), "1.21.4": ("fabric", "neoforge"),
                "1.21.11": ("fabric", "neoforge", "forge")}[BAND]


# Every ore has a KEY, unique across the table: the id part in a stone another mod places and the geology
# rule's key. The overlay, unless set (placed.index_ores); Silent's Gems' Nether gems share the overlay of
# their overworld gem and are keyed nether_<gem>. Mirrors OreType.key() and OreType.silentNether.
for _ore in ORE_DEFS:
    if _ore.get("mod") == "silentgems" and set(_ore["tiers"]) == {"nether"}:
        _ore["key"] = f"nether_{_ore['name']}"

# A translucent ore takes the colour of the rock behind it, so on a stone another mod places it gets an
# overlay painted over that stone (placed.translucent_overlays), from the layer the pack's solvers
# recovered: shared/textures/layers.
LAYERS = os.path.join(os.path.dirname(POOL), "layers")
for _ore in ORE_DEFS:
    if _ore.get("mod") == "cobblemon" or _ore["overlay"] == "opal":
        _ore["translucent"] = os.path.join(LAYERS, f"{_ore['overlay']}_translucent_layer.png")

# The hosts, with the stones other mods place and the ores the pair model measured in them
# (references/tools/som-grid/older-bands, from the real jars, in modded_pairs.json), cut by the geology
# rule. shared/tools/placed.py.
HOSTS = placed.Hosts(HOST_TABLE, ORE_DEFS, os.path.join(os.path.dirname(os.path.abspath(__file__)), "modded_pairs.json"),
                     HOST_LOOK)


def repo_root():
    """The 1.21 folder: this file is 1.21/tools/<band>/generate_assets.py."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resources_dir():
    return os.path.join(repo_root(), "common", "src", BAND, "resources")


# Loader modules that can actually host a third-party ore on THIS Minecraft version.
#
# THIS BRANCH IS FABRIC + NEOFORGE ONLY. Classic Forge is dropped for 1.21.4-1.21.10: Forge has a
# hard binary wall inside the range (eventbus 6 -> 7, FMLJavaModLoadingContext -> BusGroup, at
# 1.21.5/1.21.6), so one Forge jar cannot span it. There is no forge module, so no table is ever
# written to one.
#
# The map still matters for Fabric vs NeoForge. A conditional loot table naming an absent mod's item
# is inert (the load condition fails and the table is skipped), so a table written to a loader the
# mod cannot run on is harmless. But a table MISSING from a loader the mod CAN run on means our
# variants register there and drop NOTHING - silent and serious. So route each mod's conditional
# loot to exactly the loader(s) it ships for in-range.
#
# VERIFIED PER MINECRAFT VERSION on the Modrinth API for 1.21.4-1.21.10, not from the project-level
# "loaders" array (that is the union across every file a project ever shipped and lies per version):
#   create         fabric only    (Create Fly, mod id 'create', fabric/quilt at 1.21.8 and 1.21.10)
#   mythicmetals   fabric only    (0.25.3+1.21.4; MM stops at 1.21.4 and is Fabric-only always)
#   energizedpower fabric + neoforge   (the whole range)
#   techreborn     fabric only    (added Sept 2026: 5.12.9 at 1.21.4, 5.13.4 at 1.21.5, 5.14.2 at
#                                  1.21.6-1.21.8, nothing at 1.21.9-1.21.10)
#
# Every OTHER mod below has NO fabric/neoforge build anywhere in 1.21.4-1.21.10 (most jumped from
# 1.21.1 to 1.21.11+ or to 26.x). Their variants therefore never register on this range and their
# data is inert. They are kept, with their 1.21.1-era loader routing, purely so the derived
# registration lights them up with no code change if any of them ever ships an in-range build; the
# routing is only reached if that happens. Re-query per version on any bump.
CONDITIONAL_LOOT_MODULES_BY_MOD = {
    "minecraft": ('fabric', 'neoforge'),   # deep blackstone (Terralith): the game's rock, every loader
    "create": ("fabric",),            # Create Fly is Fabric here, not NeoForge as at 1.21.1
    "mythicupgrades": ("fabric", "neoforge"),
    "mythicmetals": ("fabric",),
    "silentgems": ("neoforge",),
    "densemekanism": ("neoforge",),
    "powah": ("neoforge",),
    "tfmg": ("neoforge",),
    "energizedpower": ("fabric", "neoforge"),
    "things": ("fabric",),
    "silentgear": ("neoforge",),
    "create_new_age": ("neoforge",),
    "techreborn": ("fabric",),
    "bigreactors": ("neoforge",),
    # The mods that place a host stone route the same way: a variant's table goes only to the loaders
    # that carry its stone's mod AND its ore's (loot_modules). Both platforms, per version (survey).
    "blockus": ('fabric',),
    "promenade": ('fabric',),
    "wilderwild": ('fabric',),
    "biomeswevegone": ("fabric", "neoforge"),   # Oh The Biomes We've Gone: Fabric and NeoForge
}
DEFAULT_CONDITIONAL_LOOT_MODULES = ("fabric", "neoforge")

# Which supported mods a player can ACTUALLY see on this range, and on which loader. Only three of
# the eleven have any Fabric/NeoForge build in 1.21.4-1.21.10; the rest are inert here (see the note
# on CONDITIONAL_LOOT_MODULES_BY_MOD above). This drives the README's honest per-loader block count
# and "supported mods available here" list, so it must reflect real availability, not the inert
# routing. Verified on the Modrinth API, per version. Re-query on any bump.
IN_RANGE_AVAILABILITY = {
    "create": ("fabric",),                    # Create Fly, 1.21.8 and 1.21.10
    "mythicmetals": ("fabric",),              # 0.25.3, 1.21.4 only
    "energizedpower": ("fabric", "neoforge"),  # the whole range
    "techreborn": ("fabric",),                # 1.21.4 to 1.21.8, and 1.21.10 on CurseForge
    "bigreactors": ("neoforge",),             # 2.4.20, 1.21.4 only, CurseForge only
}


gate_of = placed.gate_of


def loot_modules(gate):
    """The loader modules every mod of a variant's gate ships for."""
    return placed.loot_modules(gate, CONDITIONAL_LOOT_MODULES_BY_MOD, DEFAULT_CONDITIONAL_LOOT_MODULES)


# The loaders each stone mod's variants register on (ModdedPairs.shipsHere): exactly those its loot goes to.
STONE_LOADERS = {c["placed_by"]: tuple(CONDITIONAL_LOOT_MODULES_BY_MOD.get(c["placed_by"], DEFAULT_CONDITIONAL_LOOT_MODULES))
                 for c in HOSTS.placed()}


def conditional_data_dir(module, namespace):
    return os.path.join(repo_root(), module, "src", BAND, "resources", "data", namespace)


def fabric_pack_data_dir(mod, namespace):
    """Data folder of the Fabric built-in pack that loads only alongside `mod` (write_material_tags)."""
    return os.path.join(repo_root(), "fabric", "src", BAND, "resources", "resourcepacks", mod, "data", namespace)


def write_material_tags(conv, conv_block, conv_item, entry_mod):
    """Write the per-material c:ores/<x> tags so that none exists in a Fabric world lacking its mods.

    FABRIC'S tags_populated CONDITION ASKS WHETHER A TAG EXISTS, NOT WHETHER ANYTHING IS IN IT:
    ResourceConditionsImpl.setTags records every tag id the reload built. A c:ores/nickel file whose
    only entries are optional TFMG variants therefore "populated" c:ores/nickel in a world without
    TFMG, recipes gated on it loaded with an ingredient that matches nothing, and Alloy Forgery's
    1.21.4 build crashed on world load reading the first ingredient of one. Fabric applies no resource
    conditions to tag files, so such a tag simply must not exist there: each mod's entries go in a
    built-in data pack of their own (fabric/.../resourcepacks/<mod>/), which SeamlessOresFabric
    registers only when that mod is loaded, and entries for a mod with no Fabric build are left out.
    NeoForge keeps exactly the file it always had. A material with no modded entries stays shared.
    """
    fabric_c = conditional_data_dir("fabric", "c")
    neoforge_c = conditional_data_dir("neoforge", "c")
    packs = os.path.join(repo_root(), "fabric", "src", BAND, "resources", "resourcepacks")
    # All three are written only here, so clearing them is what keeps a renamed tag from lingering.
    for stale in (packs, os.path.join(fabric_c, "tags"), os.path.join(neoforge_c, "tags")):
        if os.path.isdir(stale):
            shutil.rmtree(stale)
    for kind, table in (("block", conv_block), ("item", conv_item)):
        for ore, values in table.items():
            # An ore name is c:ores/<name>; a key with a slash is a whole path (c:ore_rates/dense).
            rel = os.path.join("tags", kind, *(ore.split("/") if "/" in ore else ("ores", ore))) + ".json"
            shared = os.path.join(conv, rel)
            # A mod's entries go to that mod's conditional pack; an optional entry that belongs to
            # no mod (the game's ore in a stone another mod places) is shared like a plain one.
            modded = [v for v in values if isinstance(v, dict) and v["id"] in entry_mod]
            if not modded:
                write_json(shared, {"values": values})
                continue
            if os.path.exists(shared):
                os.remove(shared)
            write_json(os.path.join(neoforge_c, rel), {"values": values})
            plain = [v for v in values if not (isinstance(v, dict) and v["id"] in entry_mod)]
            if plain:
                write_json(os.path.join(fabric_c, rel), {"values": plain})
            by_mod = {}
            for v in modded:
                by_mod.setdefault(entry_mod[v["id"]], []).append(v)
            for mod, entries in by_mod.items():
                if "fabric" in CONDITIONAL_LOOT_MODULES_BY_MOD.get(mod, DEFAULT_CONDITIONAL_LOOT_MODULES):
                    write_json(os.path.join(fabric_pack_data_dir(mod, "c"), rel), {"values": entries})


def assets_dir():
    return os.path.join(resources_dir(), "assets", MOD_ID)


def data_dir(namespace):
    return os.path.join(resources_dir(), "data", namespace)


def variants():
    """Every (host, host config, ore def, source form, source tier) that actually exists (placed.py)."""
    return HOSTS.variants()


def overlay_for(ore, host_cfg, face="side"):
    return HOSTS.overlay_for(ore, host_cfg, face)


def all_overlay_keys():
    return HOSTS.overlay_keys()


def variant_name(host, ore):
    return HOSTS.name_of(host, ore)


def block_title(host, ore):
    return HOSTS.title_of(host, ore)

def generate_json():
    root = assets_dir()
    count = 0
    # Every file of these folders is written here, so one this run does not write is a variant that no
    # longer exists: cleared first, so a host or ore taken out of the tables leaves nothing behind.
    for sub in (("blockstates",), ("models", "block"), ("models", "item"), ("items",)):
        folder = os.path.join(root, *sub)
        for name in os.listdir(folder) if os.path.isdir(folder) else []:
            if name.endswith(".json"):
                os.remove(os.path.join(folder, name))
    painted = placed.translucent_overlays(HOSTS, os.path.join(root, "textures", "block"), STONE_JARS)
    if painted:
        print(f"  {painted} translucent overlays painted over the stones other mods place")

    for host, host_cfg, ore, _vanilla, _tier in variants():
            name = variant_name(host, ore)

            # Blockstate and models, in the host's look (assetgen.look_models). Two coincident full
            # cubes, following vanilla's own grass_block pattern: the opaque stone lands on the solid
            # layer, the overlay has alpha and must land on cutout, or its transparent pixels are
            # drawn opaque.
            #
            # THE RENDER TYPE MUST BE DECLARED BELOW 26.1. From 26.1 the chunk layer is DERIVED from
            # the texture's alpha and no per-loader API exists at all; here the game still routes
            # through ItemBlockRenderTypes, whose map is private and whose default is solid, so an
            # undeclared block renders as opaque garbage with NOTHING logged.
            #
            # "render_type" covers NeoForge and Forge only - both read it off the block model JSON.
            # Vanilla and Fabric ignore the key, so FABRIC IS HANDLED IN CODE by
            # SeamlessOresFabricClient calling BlockRenderLayerMap. Both halves are needed.
            state, block_models = look_models(name, host_cfg["look"], host_cfg["side"], host_cfg["end"],
                                              None, None, render_type="minecraft:cutout",
                                              overlays=HOSTS.overlays_of(ore, host_cfg))
            for model_name, model in block_models.items():
                write_json(os.path.join(root, "models", "block", f"{model_name}.json"), model)
            write_json(os.path.join(root, "blockstates", f"{name}.json"), state)

            # Item model definition. The assets/<ns>/items/ DEFINITION layer arrives at 1.21.4, so
            # a block item is given its look with an items/ file pointing straight at the block
            # model. Vanilla ships no models/item/ file for a block item, so neither do we; writing
            # one here would be dead weight.
            write_json(
                os.path.join(root, "items", f"{name}.json"),
                {"model": {"type": "minecraft:model", "model": f"{MOD_ID}:block/{name}"}},
            )
            count += 1

    lang = {
        f"block.{MOD_ID}.{variant_name(host, ore)}": block_title(host, ore)
        for host, _cfg, ore, _v, _t in variants()
    }
    # Cloth Config / AutoConfig screen strings. The key shapes are fixed by AutoConfig:
    # text.autoconfig.<modid>.title / .option.<field> / .option.<field>.@Tooltip
    # A @Tooltip(count = n) needs n indexed keys instead of the bare one.
    lang.update({
        # Our own creative tab, so 295 variants stop burying vanilla's Natural Blocks.
        f"itemGroup.{MOD_ID}.ores": "Seamless Ores: Vanilla Stones",
        f"itemGroup.{MOD_ID}.modded_stones": "Seamless Ores: Modded Stones",
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
        f"text.autoconfig.{MOD_ID}.category.extreme_reactors": "Extreme Reactors",
        f"text.autoconfig.{MOD_ID}.category.things": "Things",
        f"text.autoconfig.{MOD_ID}.category.silent_gear": "Silent Gear",
        f"text.autoconfig.{MOD_ID}.category.create_new_age": "Create: New Age",
        f"text.autoconfig.{MOD_ID}.category.tech_reborn": "Tech Reborn",

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
        f"text.autoconfig.{MOD_ID}.option.dripstone": "Dripstone variants",
        f"text.autoconfig.{MOD_ID}.option.dripstone.@Tooltip":
            "Dripstone caves cover their walls in dripstone around the ore. This makes that ore match.",
        f"text.autoconfig.{MOD_ID}.option.lushCaves": "Lush Caves clay and moss (removes ore)",
        f"text.autoconfig.{MOD_ID}.option.lushCaves.@Tooltip[0]":
            "Ore left bare in a Lush Caves clay floor or moss carpet becomes clay or moss, so a",
        f"text.autoconfig.{MOD_ID}.option.lushCaves.@Tooltip[1]":
            "little ore is removed there. Bone meal on moss works exactly as in vanilla.",

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

        f"text.autoconfig.{MOD_ID}.option.overworldCopper": "Copper amount",
        f"text.autoconfig.{MOD_ID}.option.overworldCopper.@Tooltip[0]":
            "How much copper generates, as a percent of vanilla. 100 leaves vanilla untouched.",
        f"text.autoconfig.{MOD_ID}.option.overworldCopper.@Tooltip[1]":
            "Reduces the NUMBER of veins rather than their size, so a vein you find is still",
        f"text.autoconfig.{MOD_ID}.option.overworldCopper.@Tooltip[2]":
            "worth mining out. This changes vanilla generation, unlike everything else here.",

        f"text.autoconfig.{MOD_ID}.option.dripstoneCopper": "Copper amount in dripstone caves",
        f"text.autoconfig.{MOD_ID}.option.dripstoneCopper.@Tooltip[0]":
            "Dripstone caves get a second, larger copper vein on top of the usual one, and no",
        f"text.autoconfig.{MOD_ID}.option.dripstoneCopper.@Tooltip[1]":
            "other biome does - roughly three times the copper anywhere else, in vanilla.",
        f"text.autoconfig.{MOD_ID}.option.dripstoneCopper.@Tooltip[2]":
            "0 gives dripstone caves exactly the same copper as every other biome.",

        f"text.autoconfig.{MOD_ID}.option.oreVeins": "Restyle large ore veins",
        f"text.autoconfig.{MOD_ID}.option.oreVeins.@Tooltip[0]":
            "The big copper and iron veins are packed with granite and tuff. This makes their ore",
        f"text.autoconfig.{MOD_ID}.option.oreVeins.@Tooltip[1]":
            "match that filler. Cosmetic only - the amount of ore is identical either way.",

        f"text.autoconfig.{MOD_ID}.option.geology": "Geology (removes ore)",
        f"text.autoconfig.{MOD_ID}.option.geology.@Tooltip[0]":
            "Keeps the game's own ores out of rock they could never form in, such as coal in granite",
        f"text.autoconfig.{MOD_ID}.option.geology.@Tooltip[1]":
            "or diamond in diorite: that ore stays plain rock, so there is less of it. Off by default.",
        f"text.autoconfig.{MOD_ID}.option.geology.@Tooltip[2]":
            "Ores from other mods always follow this rule. Applies to new chunks, from the next world load.",

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

        f"text.autoconfig.{MOD_ID}.option.extremeReactors": "Extreme Reactors: variants",
        f"text.autoconfig.{MOD_ID}.option.extremeReactors.@Tooltip":
            "Generate host-matched yellorite ore. Does nothing unless Extreme Reactors is installed.",

        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether": "Extreme Reactors: nether variants (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether.@Tooltip[0]":
            "Puts benitoite in basalt and blackstone. Extreme Reactors generates it in netherrack",
        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether.@Tooltip[1]":
            "only, so this ADDS ore, thinned by the Nether tab's rarity and vein size.",
        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether.@Tooltip[2]":
            "Turn off to leave the Nether exactly as Extreme Reactors generates it.",

        f"text.autoconfig.{MOD_ID}.option.techReborn": "Tech Reborn: variants",
        f"text.autoconfig.{MOD_ID}.option.techReborn.@Tooltip":
            "Generate host-matched Tech Reborn ore. Does nothing unless Tech Reborn is installed.",

        f"text.autoconfig.{MOD_ID}.option.techRebornNether": "Tech Reborn: nether variants (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.techRebornNether.@Tooltip[0]":
            "Puts cinnabar, pyrite and sphalerite in basalt and blackstone. Tech Reborn generates them",
        f"text.autoconfig.{MOD_ID}.option.techRebornNether.@Tooltip[1]":
            "in netherrack only, so this ADDS ore, thinned by the Nether tab's rarity and vein size.",
        f"text.autoconfig.{MOD_ID}.option.techRebornNether.@Tooltip[2]":
            "Turn off to leave the Nether exactly as Tech Reborn generates it.",
    })
    # One switch per stone another mod places, in the Modded Stones category (placed.switch_lang).
    lang.update(placed.switch_lang(HOSTS, STONE_MODS))
    assert_no_dashes(lang.items(), "lang entries")
    write_json(os.path.join(root, "lang", "en_us.json"), lang)

    # Animation metadata for the overlays that need it. Written next to the texture, which is where
    # the vanilla sprite loader looks; nothing else has to know.
    textures = os.path.join(root, "textures", "block")
    for overlay, animation in ANIMATED_OVERLAYS.items():
        if not texture_path(textures, f"{overlay}_overlay.png"):
            print(f"  !! {overlay}_overlay.png is missing, so its animation metadata was skipped")
            continue
        write_texture_json(textures, f"{overlay}_overlay.png.mcmeta", {"animation": animation})
    print(f"  {count} blockstates, {count} block models, {count} item models, "
          f"{len(ANIMATED_OVERLAYS)} animated overlays")
    print(f"  {len(lang)} lang entries")


def generate_data():
    """Loot tables and tags. Loot is TRANSFORMED from vanilla's own tables, never reconstructed."""

    # Every loot table of ours is written here, so one this run does not write is a variant that no
    # longer exists: cleared first, as 26.x does, so a host or ore taken out leaves nothing behind.
    trees = [os.path.join(data_dir(MOD_ID), "loot_table")] + [
        os.path.join(conditional_data_dir(m, MOD_ID), "loot_table") for m in ("fabric", "neoforge", "forge")]
    # The cooking recipes beside them (parity.cooking_copies), cleared the same way.
    trees += [os.path.join(os.path.dirname(tree), "recipe") for tree in list(trees)]
    for tree in trees:
        if os.path.isdir(tree):
            shutil.rmtree(tree)

    if not os.path.exists(CLIENT_JAR):
        sys.exit(f"Client jar not found at {CLIENT_JAR} - needed to copy vanilla loot tables")

    ours = data_dir(MOD_ID)
    mc = data_dir("minecraft")
    conv = data_dir("c")
    mod_ore_tags, modded_tool_tags, mod_own_tool_tags = read_mod_tags(MOD_JARS, ORE_DEFS)

    mineable = []
    tool_tags = {}
    foreign_tool_tags = {}          # a source mod's OWN needs_* tags, mirrored for our variants
    conv_block = {}
    conv_item = {}
    ores_in_ground = {}
    copied_tags = {}    # (kind, tag) -> entries: every other tag the source ore is in (parity.py)
    tags_of_sources = parity.SourceTags([CLIENT_JAR] + sorted(set(MOD_JARS.values())))
    entry_mod = {}      # a modded tag entry's id -> the mod that variant belongs to

    with zipfile.ZipFile(CLIENT_JAR) as jar:

        # Read the real vanilla tool tags once, then mirror membership per variant. NOT hardcoded
        # per ore, because it is not uniform by ore: overworld gold_ore is in needs_iron_tool but
        # nether_gold_ore is in none of them (wooden pickaxe), and coal is in none either.
        # A modded ore's tier comes from ITS jar (read_mod_tags, nested references resolved): zinc is
        # needs_iron_tool via Create's own data, and Powah lists its tiers as #c:ores/uraninite.
        vanilla = jar_tags(jar, "block")
        vanilla_tool_tags = {tag: vanilla.get(f"minecraft:{tag}", set()) for tag in TOOL_TAGS}
        for host, host_cfg, ore, vanilla, source_tier in variants():
                name = variant_name(host, ore)
                our_id = f"{MOD_ID}:{name}"
                mod = ore.get("mod")
                vanilla_id = f"{mod}:{vanilla}" if mod else f"minecraft:{vanilla}"
                gate = gate_of(host_cfg, ore)

                # --- loot table -------------------------------------------------------------
                if mod is None:
                    # Read vanilla's table and swap only the identity bits. Ore loot is NOT uniform:
                    # copper is uniform 2-5, lapis 4-9, redstone 4-5 with uniform_bonus_count rather
                    # than ore_drops. Copying the real table is the only way to guarantee parity.
                    with jar.open(f"data/minecraft/loot_table/blocks/{vanilla}.json") as handle:
                        table = json.load(handle)
                    silk_touch_to(table, vanilla_id, our_id, name, BAND)
                    # Non-Silk-Touch drops run the source ore's own table, so pack edits to it carry over.
                    table = defer_to_source(table, vanilla_id, our_id, "value")
                    table["random_sequence"] = f"{MOD_ID}:blocks/{name}"
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
                    mod_jar_path = MOD_JARS.get(mod)
                    if not mod_jar_path or not os.path.exists(mod_jar_path):
                        raise SystemExit(
                            f"  !! cannot generate the loot table for {name}: the {mod} jar is "
                            f"required to transform its own table and was not found at "
                            f"{mod_jar_path}. Set the matching *_JAR environment variable."
                        )
                    with zipfile.ZipFile(mod_jar_path) as mod_zip:
                        loot_path = f"data/{mod}/loot_table/blocks/{vanilla}.json"
                        try:
                            with mod_zip.open(loot_path) as handle:
                                table = json.load(handle)
                        except KeyError:
                            raise SystemExit(f"  !! {mod} jar has no {loot_path} (needed by {name})")
                    silk_touch_to(table, vanilla_id, our_id, name, BAND)
                    # Non-Silk-Touch drops run the source ore's own table, so pack edits to it carry over.
                    table = defer_to_source(table, vanilla_id, our_id, "value")
                    table["random_sequence"] = f"{MOD_ID}:blocks/{name}"
                # The source ore's own smelting and blasting recipes, taking the variant: written beside
                # its loot table, under the same conditions, so it exists exactly where the variant does.
                recipes = parity.cooking_copies(CLIENT_JAR if mod is None else MOD_JARS[mod], vanilla_id, our_id, name)
                if gate:
                    # All three loaders' conditions keep it inert without the mods of its gate (the
                    # one that places its stone, the ore's own); each loader ignores the other two
                    # keys. NEVER neoforge:item_exists - removed at 26.2. A variant in a stone another
                    # mod places tests for its own block, which exists only with all of them.
                    conditions = {
                        "fabric:load_conditions": [
                            {"condition": "fabric:registry_contains", "registry": "minecraft:block",
                             "values": [our_id if host_cfg["placed_by"] else vanilla_id]}
                        ],
                        "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": m} for m in gate],
                        FORGE_CONDITION_KEY: {"type": "forge:mod_loaded", "modid": gate[0]},
                    }
                    table = {**conditions, **table}
                    modules = loot_modules(gate)
                    if "forge" in modules and len(gate) > 1:
                        sys.exit(f"{name}: Forge's condition here names one mod, and {gate} are two")
                    # Conditional table: goes to the loaders that can host every mod of its gate.
                    for module in modules:
                        write_json(os.path.join(conditional_data_dir(module, MOD_ID),
                                                "loot_table", "blocks", f"{name}.json"), table)
                        for stem, recipe in recipes.items():
                            write_json(os.path.join(conditional_data_dir(module, MOD_ID), "recipe", f"{stem}.json"),
                                       {**conditions, **recipe})
                else:
                    write_json(os.path.join(ours, "loot_table", "blocks", f"{name}.json"), table)
                    for stem, recipe in recipes.items():
                        write_json(os.path.join(ours, "recipe", f"{stem}.json"), recipe)

                # --- tags -------------------------------------------------------------------
                # A modded variant's block only exists when its mod is loaded, so its tag entries
                # are optional objects - a plain string would log a tag error without the mod.
                entry = {"id": our_id, "required": False} if gate else our_id
                if mod:
                    entry_mod[our_id] = mod
                mineable.append(entry)
                source_tags = modded_tool_tags if mod else vanilla_tool_tags
                for tag, members in source_tags.items():
                    if vanilla_id in members:
                        tool_tags.setdefault(tag, []).append(entry)
                if mod:
                    for tag_key, members in mod_own_tool_tags.items():
                        if vanilla_id in members:
                            foreign_tool_tags.setdefault(tag_key, []).append(entry)
                conv_block.setdefault(ore["name"], []).append(entry)
                conv_item.setdefault(ore["name"], []).append(entry)
                # Every other tag the source ore is in, as reviewed in source_tags.json: piglins guard a
                # gold variant, the drills of Tech Reborn and Mythic Metals mine it. Not for an ore its
                # own mod keeps out of every convention tag ("untagged").
                if not ore.get("untagged", False):
                    parity.add_tag_entries(copied_tags, tags_of_sources.tags_for(vanilla_id), entry)
                # TAG PARITY with the ore we stand in for: every c:ores/<x> tag its counterpart is in,
                # read from that mod's own jar. The name-keyed tag above stays, so nothing a published
                # release put into a tag is ever taken back out, but on its own it was WRONG for every
                # prefixed name: energized_tin sat in c:ores/energized_tin and never c:ores/tin, so a
                # machine matching c:ores/tin refused a silk-touched variant. It also misses ores the
                # source mod lists twice (Extreme Reactors' yellorite is c:ores/uranium as well).
                if mod:
                    for kind, target in (("block", conv_block), ("item", conv_item)):
                        for tag_name in sorted(mod_ore_tags[kind].get(vanilla_id, ())):
                            if tag_name != ore["name"]:
                                target.setdefault(tag_name, []).append(entry)
                # c:ores_in_ground/<stone|deepslate|netherrack> - keyed on the ore we stand in for,
                # so consumers treat a variant exactly like its counterpart.
                ground = {"stone": "stone", "deepslate": "deepslate", "nether": "netherrack"}[source_tier]
                ores_in_ground.setdefault(ground, []).append(entry)

    # Tags MERGE with vanilla's by default (no "replace": true), so these add to the existing lists
    # rather than clobbering them. Getting this wrong would unregister 417 vanilla pickaxe entries.
    write_json(os.path.join(mc, "tags", "block", "mineable", "pickaxe.json"), {"values": mineable})
    for tag, values in tool_tags.items():
        write_json(os.path.join(mc, "tags", "block", f"{tag}.json"), {"values": values})
    # The source mods' own tier tags. These merge with that mod's file, and every entry is optional,
    # so the file is inert on an instance without the mod.
    for (namespace, tag), values in foreign_tool_tags.items():
        write_json(os.path.join(data_dir(namespace), "tags", "block", f"{tag}.json"),
                   {"values": values})

    all_ids = sorted(mineable, key=lambda e: e["id"] if isinstance(e, dict) else e)
    write_json(os.path.join(conv, "tags", "block", "ores.json"), {"values": all_ids})
    write_json(os.path.join(conv, "tags", "item", "ores.json"), {"values": all_ids})
    tags_of_sources.check()
    for (kind, tag), values in sorted(copied_tags.items()):
        namespace, path = tag.split(":", 1)
        if namespace == "c":
            # A convention tag goes the way the c:ores/<x> tags go (per-mod packs on Fabric).
            (conv_block if kind == "block" else conv_item)[path] = values
        else:
            write_json(os.path.join(data_dir(namespace), "tags", kind, f"{path}.json"), {"values": values})
    write_material_tags(conv, conv_block, conv_item, entry_mod)
    for ground, values in ores_in_ground.items():
        write_json(
            os.path.join(conv, "tags", "block", "ores_in_ground", f"{ground}.json"),
            {"values": values},
        )
    # LushCavesInjector points the Lush Caves clay and moss patches at these: the vanilla tag plus
    # every ore. The vanilla tags themselves stay untouched, because bone meal on moss reads
    # #moss_replaceable and must not start eating ore.
    ours = data_dir(MOD_ID)
    for name, vanilla_tag in (("lush_clay_replaceable", "#minecraft:lush_ground_replaceable"),
                              ("lush_moss_replaceable", "#minecraft:moss_replaceable")):
        write_json(os.path.join(ours, "tags", "block", f"{name}.json"),
                   {"values": [vanilla_tag, {"id": "#c:ores", "required": False}]})

    print(f"  {len(mineable)} loot tables")
    print(f"  tags: mineable/pickaxe, {', '.join(sorted(tool_tags))}, "
          f"c:ores (+{len(conv_block)} per-ore), c:ores_in_ground ({', '.join(sorted(ores_in_ground))})")


def generate_textures():
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is required for --textures. Run this with 'py -3.14'.")

    if not os.path.exists(CLIENT_JAR):
        sys.exit(f"Client jar not found at {CLIENT_JAR}")

    # Into the shared pool: every band's models read the overlays from there.
    band_textures = os.path.join(assets_dir(), "textures", "block")
    out_dir = POOL
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


OVERWORLD_HOSTS = ["granite", "diorite", "andesite", "tuff", "dripstone"]
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
    for host, host_cfg, ore, _vanilla, _tier in variants():
        if host_cfg["placed_by"]:
            continue
        entry = grouped.setdefault(ore.get("mod"), {}).setdefault(id(ore), (ore, {}))
        entry[1][host] = variant_name(host, ore)

    order = [None] + [m for m in MODS if m in grouped]
    unknown = [m for m in grouped if m is not None and m not in MODS]
    if unknown:
        raise SystemExit(f"ORE_DEFS names mod(s) missing from MODS: {sorted(unknown)}")

    own = sum(1 for _h, c, _o, _s, _t in variants() if not c["placed_by"])
    lines = [f"**{own} blocks** in the game's own rock, in the `{MOD_ID}` namespace.", ""]
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
    for _host, cfg, ore, _v, _t in variants():
        if cfg["placed_by"]:
            continue
        per_mod[ore.get("mod")] = per_mod.get(ore.get("mod"), 0) + 1
    vanilla = per_mod.pop(None, 0)

    rows = []
    for loader in ("fabric", "neoforge"):
        total = vanilla
        available = []
        for mod, count in per_mod.items():
            # Honest availability, not the inert loot routing: a mod with no in-range build on this
            # loader contributes no blocks a player can see, even though its (gated) data ships.
            if loader in IN_RANGE_AVAILABILITY.get(mod, ()):
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
    overlays = all_overlay_keys()
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
    path = os.path.join(repo_root(), "README-%s.md" % BAND)
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    sections = {
        "block-list": _block_list(),
        "modded-stone-list": placed.modded_stone_list(HOSTS, STONE_MODS, MODS),
        "overlay-list": _overlay_list(),
        "credits": _credits(),
    }
    assert_no_dashes(((name, line) for name, lines in sections.items() for line in lines),
                     "README lines")
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
          f"{len(all_overlay_keys())} overlays, "
          f"{len({o.get('mod') for o in ORE_DEFS} - {None})} mods credited")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--textures",
        action="store_true",
        help="also re-extract the overlay PNGs (DESTRUCTIVE: overwrites hand-cleaned art)",
    )
    args = parser.parse_args()

    print("Generating client assets...")
    generate_json()
    print("Generating loot tables and tags...")
    generate_data()
    # Ids an earlier release registered and this one no longer builds: placeholders drawn as their stone.
    print(f"  retired ids: {retired.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), "retired_ids.json"), HOSTS, assets_dir(), resources_dir(), item_definitions=True)} placeholders")
    # Every variant's id for the Java side, and the shipped ids 6.0.0 renamed (aliased on load).
    print(f"  renamed ids: {renamed.write(HOSTS, list(variants()), os.path.join(os.path.dirname(os.path.abspath(__file__)), "retired_ids.json"), resources_dir())} aliased")
    print("Updating README...")
    generate_readme()
    print("Generating the Java tables...")
    cases = placed.write_java(HOSTS, os.path.dirname(HOST_TABLE), os.path.join(repo_root(), "cloth-config", "src", BAND, "java", "com", "chillpavz", MOD_ID, "config",
                     "SeamlessOresConfigData.java"), STONE_LOADERS)
    print(f"  Java: modded pairs for {cases} stones, the shared geology rule, {len(HOSTS)} host switches")

    if args.textures:
        print("Extracting overlay textures...")
        generate_textures()
    else:
        print("Skipped textures (pass --textures to regenerate; it overwrites hand edits).")


if __name__ == "__main__":
    main()
