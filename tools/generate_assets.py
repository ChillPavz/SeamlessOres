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
FORGE_CONDITION_KEY = "forge:condition"

# Colour-distance (summed per-channel) above which a pixel counts as ore rather than shaded stone.
# 0 keeps 141/256 px for iron and hazes over granite; 60 keeps 76 and looks right; 90 eats real blobs.
THRESHOLD = 60

CLIENT_JAR = os.path.expanduser(
    "~/.gradle/caches/neoformruntime/artifacts/minecraft_1.21.11_client.jar"
)

# Create (Create Fly, mod id 'create') jar - source of the zinc loot table shape and the zinc ore
# texture the overlay is derived from. Machine-specific default, override with the CREATE_JAR env
# var. Licence: the jar ships CC0 at root plus the original Create MIT - deriving the overlay is
# fine; keep the attribution line in the README. When the jar is missing, zinc JSON still generates
# (the loot shape is baked below, verified identical to vanilla iron_ore's) but the texture step
# skips zinc.
CREATE_JAR = os.environ.get(
    "CREATE_JAR",
    "../jars/1.21.11-create-fly-1.21.11-6.0.9-5.jar",
)

# Mythic Upgrades (mod id 'mythicupgrades', MIT, 26.2 on all four loaders). Source of its ore
# textures and the facts behind the entries below. Override with MYTHIC_UPGRADES_JAR.
MYTHIC_UPGRADES_JAR = os.environ.get(
    "MYTHIC_UPGRADES_JAR",
    os.path.expanduser(
        "~/AppData/Roaming/ModrinthApp/profiles/Fabric 1.21.1/mods/mythicupgrades-fabric-1.21.1-5.1.0.jar"
    ),
)

# Mythic Metals (mod id 'mythicmetals', MIT). Fabric only on every version it has ever shipped, so
# its variants only ever register there. Source of its ore textures, loot tables and tool tags.
SILENT_GEMS_JAR = os.environ.get(
    "SILENT_GEMS_JAR",
    "../jars/1.21.11-silentgems-1.21.11-neoforge-5.1.3.jar")

MYTHIC_METALS_JAR = os.environ.get(
    "MYTHIC_METALS_JAR",
    # The in-range build. Mythic Metals ships Fabric only and stops at 1.21.4; its ore set, loot
    # tables and textures are byte-identical to the 0.24.6+1.21 build the other branches read.
    "../jars/mythicmetals-0.24.6+1.21.jar",
)

# Every third-party jar we read, keyed by the mod id used in the ORES table below. A missing jar is
# a warning rather than an error: the JSON still generates, only the texture step is skipped.
DENSEMEKANISM_JAR = os.environ.get("DENSEMEKANISM_JAR", "../jars/densemekanism-1.21.1-1.2.jar")

POWAH_JAR = os.environ.get("POWAH_JAR", "../jars/Powah-7.0.4-alpha.jar")

TFMG_JAR = os.environ.get("TFMG_JAR", "../jars/1.21.11-tfmg-1.2.0.jar")

ENERGIZEDPOWER_JAR = os.environ.get("ENERGIZEDPOWER_JAR", "../jars/1.21.11-energizedpower-1.21.11-2.15.14-neoforge.jar")

THINGS_JAR = os.environ.get("THINGS_JAR", "../jars/things-0.4.2+1.21.jar")

SILENTGEAR_JAR = os.environ.get("SILENTGEAR_JAR", "../jars/1.21.11-silent-gear-1.21.11-neoforge-4.1.6.1.jar")

CREATE_NEW_AGE_JAR = os.environ.get("CREATE_NEW_AGE_JAR", "../jars/create-new-age-1.2.0+neoforge-mc1.21.1.jar")

MOD_JARS = {"create_new_age": CREATE_NEW_AGE_JAR,
            "silentgear": SILENTGEAR_JAR,
            "things": THINGS_JAR,
            "energizedpower": ENERGIZEDPOWER_JAR,
            "tfmg": TFMG_JAR,
            "powah": POWAH_JAR,
            "densemekanism": DENSEMEKANISM_JAR,
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
# same as animating a Fusion connecting sheet, which crashes the game on load.
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
    {"name": "ruby",                    "overlay": "ruby",                    "source": "ruby_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:ruby",
     "tiers": {"stone": "ruby_ore", "deepslate": "deepslate_ruby_ore"}},
    {"name": "sapphire",                "overlay": "sapphire",                "source": "sapphire_ore", "base": "stone",
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
# WHY IT MATTERS: at Forge 61 a loot table IS gated by "forge:condition" (it is a datapack registry
# by then, going through the patched RegistryDataLoader), so a table naming an absent mod is skipped
# quietly on every loader here. A table written to a loader the mod cannot run on is therefore
# harmless. But a table MISSING from a loader the mod CAN run on means our variants register there
# and drop NOTHING - silent and serious. So route each mod's conditional loot to the loader(s) it
# actually ships for.
#
# VERIFIED PER MINECRAFT VERSION on the Modrinth API for 1.21.11, never from the project-level
# "loaders" array (that is the union across every file a project ever shipped and lies per version):
#   create         fabric only      (Create Fly, mod id 'create')
#   silentgems     neoforge only
#   silentgear     neoforge only
#   tfmg           neoforge only    (slug 'create-tfmg')
#   energizedpower fabric + neoforge
#
# NOTHING ships for classic Forge at 1.21.11, so the Forge jar carries only the vanilla tables.
#
# The other six (mythicupgrades, mythicmetals, densemekanism, powah, things, create_new_age) have NO
# 1.21.11 build at all - most went from 1.21.1 straight to 26.x. Their variants never register here
# and their data is inert. They are kept with their 1.21.1-era routing so the derived registration
# lights them up with no code change if a build ever appears. Re-query per version on any bump.
CONDITIONAL_LOOT_MODULES_BY_MOD = {
    "create": ("fabric",),
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
}
DEFAULT_CONDITIONAL_LOOT_MODULES = ("fabric", "neoforge")

# Which supported mods a player can ACTUALLY see at 1.21.11, and on which loader. This drives the
# README's honest per-loader block count and its "supported mods available here" list, so it must
# reflect real availability rather than the inert loot routing above. Verified on the Modrinth API.
# Re-query on any bump.
#
# AN ADD-ON'S AVAILABILITY IS THE INTERSECTION OF ITS OWN BUILD AND ITS REQUIRED PARENT'S, so a
# per-mod query is not enough on its own. TFMG is the case here: it ships a NeoForge 1.21.11 build,
# but its own neoforge.mods.toml declares create [6.0.6,) as REQUIRED, and the only Create at
# 1.21.11 is Create Fly, which is Fabric and Quilt only. So TFMG cannot load on NeoForge here and
# its twelve variants are unreachable, however its own listing reads. Its conditional loot tables
# still ship (gated on tfmg being loaded, therefore inert) so that it lights up on its own if a
# NeoForge Create ever appears.
IN_RANGE_AVAILABILITY = {
    "create": ("fabric",),
    "silentgems": ("neoforge",),
    "silentgear": ("neoforge",),
    "energizedpower": ("fabric", "neoforge"),
}


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


# House style: this project does not use U+2014 EM DASH or U+2013 EN DASH in player-facing text.
# Ordinary hyphens are fine.
DASHES = ("\u2014", "\u2013")


def assert_no_dashes(strings, what):
    """Fails the run if any generated string carries an em or en dash.

    Everything this generator writes is read by a player: the config screen's labels and tooltips,
    every block name, and the README. Checking by eye does not scale to a few hundred lang entries
    and would have to be redone on every branch, so it is asserted instead. Ordinary hyphens are
    fine and untouched; the rule is only about the two long dashes.
    """
    bad = [(key, text) for key, text in strings if any(d in text for d in DASHES)]
    if bad:
        report = "\n".join("    {}\n      {}".format(k, t) for k, t in bad)
        raise SystemExit(
            "  !! {} {} contain an em or en dash, which must not reach players:\n{}\n"
            "     Replace them with a comma, a colon, a full stop, brackets or a plain hyphen."
            .format(len(bad), what, report))


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
    })
    assert_no_dashes(lang.items(), "lang entries")
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


def generate_data():
    """Loot tables and tags. Loot is TRANSFORMED from vanilla's own tables, never reconstructed."""

    if not os.path.exists(CLIENT_JAR):
        sys.exit(f"Client jar not found at {CLIENT_JAR} - needed to copy vanilla loot tables")

    ours = data_dir(MOD_ID)
    mc = data_dir("minecraft")
    conv = data_dir("c")

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
            with jar.open(f"data/minecraft/tags/block/{tag}.json") as handle:
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
                        with mod_jar_zip.open(f"data/minecraft/tags/block/{tag}.json") as handle:
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
                    with jar.open(f"data/minecraft/loot_table/blocks/{vanilla}.json") as handle:
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
                    for pool in table.get("pools", []):
                        for entry in pool.get("entries", []):
                            for child in entry.get("children", []):
                                if any(
                                    cond.get("condition") == "minecraft:match_tool"
                                    for cond in child.get("conditions", [])
                                ):
                                    # Silk-touch branch drops the block itself - ours.
                                    child["name"] = our_id
                    table["random_sequence"] = f"{MOD_ID}:blocks/{name}"
                    # All three loaders' conditions keep it inert when the mod is absent; each
                    # loader ignores the other two keys. NEVER neoforge:item_exists - removed at 26.2.
                    conditions = {
                        "fabric:load_conditions": [
                            {"condition": "fabric:registry_contains",
                             "registry": "minecraft:block", "values": [vanilla_id]}
                        ],
                        "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": mod}],
                        FORGE_CONDITION_KEY: {"type": "forge:mod_loaded", "modid": mod},
                    }
                    table = {**conditions, **table}

                if mod:
                    # Conditional table: goes to the loaders that can host that mod, not to common.
                    for module in CONDITIONAL_LOOT_MODULES_BY_MOD.get(
                            mod, DEFAULT_CONDITIONAL_LOOT_MODULES):
                        write_json(os.path.join(conditional_data_dir(module, MOD_ID),
                                                "loot_table", "blocks", f"{name}.json"), table)
                else:
                    write_json(os.path.join(ours, "loot_table", "blocks", f"{name}.json"), table)

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
    write_json(os.path.join(mc, "tags", "block", "mineable", "pickaxe.json"), {"values": mineable})
    for tag, values in tool_tags.items():
        write_json(os.path.join(mc, "tags", "block", f"{tag}.json"), {"values": values})

    all_ids = sorted(mineable, key=lambda e: e["id"] if isinstance(e, dict) else e)
    write_json(os.path.join(conv, "tags", "block", "ores.json"), {"values": all_ids})
    write_json(os.path.join(conv, "tags", "item", "ores.json"), {"values": all_ids})
    for ore, values in conv_block.items():
        write_json(os.path.join(conv, "tags", "block", "ores", f"{ore}.json"), {"values": values})
    for ore, values in conv_item.items():
        write_json(os.path.join(conv, "tags", "item", "ores", f"{ore}.json"), {"values": values})
    for ground, values in ores_in_ground.items():
        write_json(
            os.path.join(conv, "tags", "block", "ores_in_ground", f"{ground}.json"),
            {"values": values},
        )

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
          f"{len({overlay_for(o, c) for _h, c, o, _v in variants()})} overlays, "
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
    print("Updating README...")
    generate_readme()

    if args.textures:
        print("Extracting overlay textures...")
        generate_textures()
    else:
        print("Skipped textures (pass --textures to regenerate; it overwrites hand edits).")


if __name__ == "__main__":
    main()
