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
    "~/.gradle/caches/neoformruntime/artifacts/minecraft_1.21.1_client.jar"
)

# Create (Create Fly, mod id 'create') jar - source of the zinc loot table shape and the zinc ore
# texture the overlay is derived from. Machine-specific default, override with the CREATE_JAR env
# var. Licence: the jar ships CC0 at root plus the original Create MIT - deriving the overlay is
# fine; keep the attribution line in the README. When the jar is missing, zinc JSON still generates
# (the loot shape is baked below, verified identical to vanilla iron_ore's) but the texture step
# skips zinc.
CREATE_JAR = os.environ.get(
    "CREATE_JAR",
    os.path.expanduser(
        "~/AppData/Roaming/ModrinthApp/profiles/NeoForge 1.21.1/mods/create-1.21.1-6.0.10.jar"
    ),
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
    "../references/jars/silentgems-26.1.2-neoforge-5.1.4.jar")

MYTHIC_METALS_JAR = os.environ.get(
    "MYTHIC_METALS_JAR",
    os.path.expanduser(
        "~/AppData/Roaming/ModrinthApp/profiles/Fabric 1.21.1/mods/mythicmetals-0.24.6+1.21.jar"
    ),
)

# Every third-party jar we read, keyed by the mod id used in the ORES table below. A missing jar is
# a warning rather than an error: the JSON still generates, only the texture step is skipped.
DENSEMEKANISM_JAR = os.environ.get("DENSEMEKANISM_JAR", "../references/jars/densemekanism-1.21.1-1.2.jar")

POWAH_JAR = os.environ.get("POWAH_JAR", "../references/jars/Powah-7.0.4-alpha.jar")

TFMG_JAR = os.environ.get("TFMG_JAR", "../references/jars/tfmg-1.2.2.jar")

ENERGIZEDPOWER_JAR = os.environ.get("ENERGIZEDPOWER_JAR", "../references/jars/energizedpower-3.0.0+26.2.x-neoforge.jar")

THINGS_JAR = os.environ.get("THINGS_JAR", "../references/jars/things-0.4.2+1.21.jar")

SILENTGEAR_JAR = os.environ.get("SILENTGEAR_JAR", "../references/jars/silent-gear-26.1.2-neoforge-4.2.2.jar")

CREATE_NEW_AGE_JAR = os.environ.get("CREATE_NEW_AGE_JAR", "../references/jars/create-new-age-1.2.0+neoforge-mc1.21.1.jar")

TECHREBORN_JAR = os.environ.get("TECHREBORN_JAR", "../references/jars/1.21.1-TechReborn-5.11.19.jar")
MODERN_INDUSTRIALIZATION_JAR = os.environ.get("MODERN_INDUSTRIALIZATION_JAR",
                                              "../references/jars/Modern-Industrialization-2.5.6.jar")
OCCULTISM_JAR = os.environ.get("OCCULTISM_JAR", "../references/jars/occultism-1.21.1-neoforge-1.224.3.jar")
EXTREME_REACTORS_JAR = os.environ.get("EXTREME_REACTORS_JAR", "../references/jars/ExtremeReactors2-1.21.1-2.4.9.jar")
MYSTICAL_AGRICULTURE_JAR = os.environ.get("MYSTICAL_AGRICULTURE_JAR",
                                          "../references/jars/1.21.1-MysticalAgriculture-1.21.1-8.0.28.jar")
# Cobblemon 1.7.3 and 1.8.0 (both 1.21.1) ship identical ore features, loot tables and tags;
# checked side by side, so either jar serves.
COBBLEMON_JAR = os.environ.get("COBBLEMON_JAR", "../references/jars/Cobblemon-neoforge-1.7.3+1.21.1.jar")
# Immersive Engineering. IE REDREW nickel and uranium after 1.20.1, so the overlays must come
# from THIS band's own jar rather than the newest one; the two eras are different art.
# Its ore art is used with BluSunrize's permission (14 Sept 2026), on the stated condition that
# Immersive Engineering and BluSunrize are credited. See the README credits table.
IMMERSIVE_ENGINEERING_JAR = os.environ.get("IMMERSIVE_ENGINEERING_JAR",
                                          "../references/jars/ImmersiveEngineering-1.21.1-12.4.2-194.jar")
# Mekanism (MIT, Copyright (c) 2017-2025 Aidan C. Brady, read from the repo's own LICENSE rather
# than a platform label). Five ores. ITS FEATURE IS NOT minecraft:ore either: mekanism:ore, whose
# config is its own record, which is the second mod to need the ForeignOreTargets path.
# Mekanism DRAWS TIN DIFFERENTLY on 1.20.1, so the overlay for that branch is the pack's
# old_tin_overlay.png; every other overlay is the same drawing on both bands.
MEKANISM_JAR = os.environ.get("MEKANISM_JAR", "../references/jars/Mekanism-1.21.1-10.7.19.85.jar")
MOD_JARS = {"create_new_age": CREATE_NEW_AGE_JAR,
            "mekanism": MEKANISM_JAR,
            "immersiveengineering": IMMERSIVE_ENGINEERING_JAR,
            "cobblemon": COBBLEMON_JAR,
            "techreborn": TECHREBORN_JAR,
            "modern_industrialization": MODERN_INDUSTRIALIZATION_JAR,
            "occultism": OCCULTISM_JAR,
            "bigreactors": EXTREME_REACTORS_JAR,
            "mysticalagriculture": MYSTICAL_AGRICULTURE_JAR,
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
    "modern_industrialization": {"display": "Modern Industrialization", "category": "modern_industrialization",
                       "licence": "MIT",          "author": "Azerococo, Technici4n"},
    "occultism":      {"display": "Occultism",         "category": "occultism",
                       "licence": "MIT",          "author": "Kli Kli"},
    "bigreactors":    {"display": "Extreme Reactors",  "category": "extreme_reactors",
                       "licence": "MIT",          "author": "ZeroNoRyouki"},
    "mysticalagriculture": {"display": "Mystical Agriculture", "category": "mystical_agriculture",
                       "licence": "MIT",          "author": "BlakeBr0"},
    "immersiveengineering": {"display": "Immersive Engineering", "category": "immersive_engineering",
                       "licence": "Blu's License of Common Sense",
                       "author": "BluSunrize, Damien A.W. Hazard",
                       "link": "https://modrinth.com/mod/immersiveengineering"},
    "mekanism":       {"display": "Mekanism",         "category": "mekanism",
                       "licence": "MIT",          "author": "Aidan C. Brady",
                       "link": "https://modrinth.com/mod/mekanism"},
    "cobblemon":      {"display": "Cobblemon",         "category": "cobblemon",
                       "licence": "MPL-2.0",      "author": "The Cobblemon Team"},
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
    # Tech Reborn (Fabric only at 1.21.1). Its eight overworld ores all target the vanilla
    # replaceables tags: a pure restyle. Uranium does not exist here yet; cinnabar, pyrite and
    # sphalerite (netherrack only, they would ADD ore) and the four end stone ores are not covered.
    # Prefixed where the plain name is already taken, or shared with Modern Industrialization.
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
    # Modern Industrialization (NeoForge only at 1.21.1). Ten ores, all on the replaceables tags.
    {"name": "antimony", "overlay": "antimony", "source": "antimony_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "antimony_ore", "deepslate": "deepslate_antimony_ore"}},
    {"name": "mi_bauxite", "overlay": "mi_bauxite", "source": "bauxite_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "bauxite_ore", "deepslate": "deepslate_bauxite_ore"}},
    {"name": "mi_lead", "overlay": "mi_lead", "source": "lead_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "lead_ore", "deepslate": "deepslate_lead_ore"}},
    {"name": "lignite_coal", "overlay": "lignite_coal", "source": "lignite_coal_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "lignite_coal_ore", "deepslate": "deepslate_lignite_coal_ore"}},
    {"name": "monazite", "overlay": "monazite", "source": "monazite_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "monazite_ore", "deepslate": "deepslate_monazite_ore"}},
    {"name": "mi_nickel", "overlay": "mi_nickel", "source": "nickel_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "nickel_ore", "deepslate": "deepslate_nickel_ore"}},
    {"name": "salt", "overlay": "salt", "source": "salt_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "salt_ore", "deepslate": "deepslate_salt_ore"}},
    {"name": "mi_tin", "overlay": "mi_tin", "source": "tin_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "tin_ore", "deepslate": "deepslate_tin_ore"}},
    {"name": "tungsten", "overlay": "tungsten", "source": "tungsten_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "tungsten_ore", "deepslate": "deepslate_tungsten_ore"}},
    {"name": "uranium", "overlay": "uranium", "source": "uranium_ore", "base": "stone",
     "mod": "modern_industrialization",
     "tiers": {"stone": "uranium_ore", "deepslate": "deepslate_uranium_ore"}},
    # Occultism: silver only. Its tier word comes LAST (silver_ore_deepslate). Iesnium is not
    # host plus blobs, so it has nothing to be seamless with.
    {"name": "occultism_silver", "overlay": "occultism_silver", "source": "silver_ore", "base": "stone",
     "mod": "occultism",
     "tiers": {"stone": "silver_ore", "deepslate": "silver_ore_deepslate"}},
    # Extreme Reactors: yellorite, animated (see ANIMATED_OVERLAYS). Benitoite would ADD nether ore
    # and anglesite is end stone, so neither is covered.
    {"name": "yellorite", "overlay": "yellorite", "source": "yellorite_ore", "base": "stone",
     "mod": "bigreactors",
     "tiers": {"stone": "yellorite_ore", "deepslate": "deepslate_yellorite_ore"}},
    # Mystical Agriculture: inferium and prosperity. Soulium sits on its own soulstone.
    {"name": "inferium", "overlay": "inferium", "source": "inferium_ore", "base": "stone",
     "mod": "mysticalagriculture",
     "tiers": {"stone": "inferium_ore", "deepslate": "deepslate_inferium_ore"}},
    {"name": "prosperity", "overlay": "prosperity", "source": "prosperity_ore", "base": "stone",
     "mod": "mysticalagriculture",
     "tiers": {"stone": "prosperity_ore", "deepslate": "deepslate_prosperity_ore"}},
    # Immersive Engineering (NeoForge only at 1.21.1). Five ores, and every one of its
    # features targets stone_ore_replaceables plus deepslate_ore_replaceables, so all four
    # overworld hosts are a pure restyle and no ore is invented. Read from its own configured
    # features, which are JSON in the jar even though the feature TYPE is its own.
    #
    # Two things here are unlike every other mod we cover: IE puts the tier word FIRST
    # (ore_lead, deepslate_ore_lead), and its ore textures live in a metal/ subfolder, which is
    # what texture_dir is for. Lead, nickel, silver and uranium are prefixed because those names
    # are already taken on this branch. Aluminum is free, but it is prefixed too: the pack's family
    # keys are ie_<metal> for all five, and the overlay art is ONE file shared by the mod and the
    # pack, so a bare name would leave the pack's drift check unable to find it.
    {"name": "ie_aluminum", "overlay": "ie_aluminum", "source": "ore_aluminum", "base": "stone",
     "mod": "immersiveengineering", "texture_dir": "metal",
     "tiers": {"stone": "ore_aluminum", "deepslate": "deepslate_ore_aluminum"}},
    {"name": "ie_lead", "overlay": "ie_lead", "source": "ore_lead", "base": "stone",
     "mod": "immersiveengineering", "texture_dir": "metal",
     "tiers": {"stone": "ore_lead", "deepslate": "deepslate_ore_lead"}},
    {"name": "ie_nickel", "overlay": "ie_nickel", "source": "ore_nickel", "base": "stone",
     "mod": "immersiveengineering", "texture_dir": "metal",
     "tiers": {"stone": "ore_nickel", "deepslate": "deepslate_ore_nickel"}},
    {"name": "ie_silver", "overlay": "ie_silver", "source": "ore_silver", "base": "stone",
     "mod": "immersiveengineering", "texture_dir": "metal",
     "tiers": {"stone": "ore_silver", "deepslate": "deepslate_ore_silver"}},
    {"name": "ie_uranium", "overlay": "ie_uranium", "source": "ore_uranium", "base": "stone",
     "mod": "immersiveengineering", "texture_dir": "metal",
     "tiers": {"stone": "ore_uranium", "deepslate": "deepslate_ore_uranium"}},
    # Mekanism (NeoForge at 1.21.1, Forge and NeoForge at 1.20.1). Five ores, every one of them
    # targeting stone_ore_replaceables AND deepslate_ore_replaceables, so all four overworld hosts
    # are a pure restyle and no ore is invented. Prefixed mek_ for all five: osmium, tin, lead and
    # uranium are names another supported mod already holds, and fluorite is prefixed too so the
    # family reads as one set and matches the pack's own mek_<ore> keys, which is what lets one
    # overlay file serve both the mod and the pack.
    #
    # NO raw_drop: the loot is transformed from Mekanism's own tables, because fluorite uses
    # set_count (2 to 4) and a hand-built vanilla-shape table would quietly change its yield.
    {"name": "mek_fluorite", "overlay": "mek_fluorite", "source": "fluorite_ore", "base": "stone",
     "mod": "mekanism",
     "tiers": {"stone": "fluorite_ore", "deepslate": "deepslate_fluorite_ore"}},
    {"name": "mek_lead", "overlay": "mek_lead", "source": "lead_ore", "base": "stone",
     "mod": "mekanism",
     "tiers": {"stone": "lead_ore", "deepslate": "deepslate_lead_ore"}},
    {"name": "mek_osmium", "overlay": "mek_osmium", "source": "osmium_ore", "base": "stone",
     "mod": "mekanism",
     "tiers": {"stone": "osmium_ore", "deepslate": "deepslate_osmium_ore"}},
    {"name": "mek_tin", "overlay": "mek_tin", "source": "tin_ore", "base": "stone",
     "mod": "mekanism",
     "tiers": {"stone": "tin_ore", "deepslate": "deepslate_tin_ore"}},
    {"name": "mek_uranium", "overlay": "mek_uranium", "source": "uranium_ore", "base": "stone",
     "mod": "mekanism",
     "tiers": {"stone": "uranium_ore", "deepslate": "deepslate_uranium_ore"}},
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
    # Cobblemon (Fabric and NeoForge at 1.21.1). Each stone has a TRANSLUCENT edge ring over the rock,
    # so, like opal, every host gets its own precomposited overlay (host_overlays, set below the
    # table). Fire stone also has a netherrack-only ore that shares the same art, so it is one entry
    # carrying all three tiers. Dripstone moon stone and terracotta sun stone sit on rocks that are
    # not our hosts.
    {"name": "dawn_stone", "overlay": "dawn_stone", "source": "dawn_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "dawn_stone_ore", "deepslate": "deepslate_dawn_stone_ore"}},
    {"name": "dusk_stone", "overlay": "dusk_stone", "source": "dusk_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "dusk_stone_ore", "deepslate": "deepslate_dusk_stone_ore"}},
    {"name": "fire_stone", "overlay": "fire_stone", "source": "fire_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "fire_stone_ore", "deepslate": "deepslate_fire_stone_ore", "nether": "nether_fire_stone_ore"}},
    {"name": "ice_stone", "overlay": "ice_stone", "source": "ice_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "ice_stone_ore", "deepslate": "deepslate_ice_stone_ore"}},
    {"name": "leaf_stone", "overlay": "leaf_stone", "source": "leaf_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "leaf_stone_ore", "deepslate": "deepslate_leaf_stone_ore"}},
    {"name": "moon_stone", "overlay": "moon_stone", "source": "moon_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "moon_stone_ore", "deepslate": "deepslate_moon_stone_ore"}},
    {"name": "shiny_stone", "overlay": "shiny_stone", "source": "shiny_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "shiny_stone_ore", "deepslate": "deepslate_shiny_stone_ore"}},
    {"name": "sun_stone", "overlay": "sun_stone", "source": "sun_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "sun_stone_ore", "deepslate": "deepslate_sun_stone_ore"}},
    {"name": "thunder_stone", "overlay": "thunder_stone", "source": "thunder_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "thunder_stone_ore", "deepslate": "deepslate_thunder_stone_ore"}},
    {"name": "water_stone", "overlay": "water_stone", "source": "water_stone_ore", "base": "stone",
     "mod": "cobblemon",
     "tiers": {"stone": "water_stone_ore", "deepslate": "deepslate_water_stone_ore"}},
    # Silent's Gems opal is TRANSLUCENT: painted at partial opacity over each rock, so it takes the
    # colour of the rock behind it. One overlay per host, precomposited from the solved layer (see
    # the pack's solve_translucent_ore.py). Its nether feature places nothing (size 0, count 0).
    {"name": "opal", "overlay": "opal", "source": "opal_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:opal",
     "host_overlays": {"granite": "opal_granite", "diorite": "opal_diorite", "andesite": "opal_andesite", "tuff": "opal_tuff"},
     "tiers": {"stone": "opal_ore", "deepslate": "deepslate_opal_ore"}},
]

# Cobblemon's per-host overlays, precomposited from the solved edge ring (the pack's
# solve_cobblemon_translucency.py). Basalt and blackstone draw a different texture on their end faces,
# and the ring blends into whatever is behind it, so those two take a (side, end) pair.
for _ore in ORE_DEFS:
    if _ore.get("mod") == "cobblemon":
        _stone = _ore["name"]
        _ore["host_overlays"] = {h: f"{_stone}_{h}" for h in ("granite", "diorite", "andesite", "tuff")}
        if "nether" in _ore["tiers"]:
            _ore["host_overlays"].update(basalt=(f"{_stone}_basalt_side", f"{_stone}_basalt_top"),
                                         blackstone=(f"{_stone}_blackstone", f"{_stone}_blackstone_top"))

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
    # VERIFIED PER MINECRAFT VERSION, not from the project-level "loaders" array. That array is the
    # UNION across every file a project has ever shipped, so a mod with a Forge build at 1.20.1
    # still reports "forge" when its 1.21.1 file is NeoForge only. Trusting it put 143 conditional
    # loot tables into the Forge jar that can never fire, and Forge 52 ignores loot conditions, so
    # each would have logged a parse error on every world load.
    #
    # Query per version instead:
    #   /v2/project/<slug>/version?game_versions=["1.21.1"]  -> union of that file set's loaders
    #
    # At 1.21.1 NOTHING we gate on ships for Forge, so the Forge jar carries only vanilla tables.
    "create": ("neoforge",),
    "mythicupgrades": ("fabric", "neoforge"),
    "mythicmetals": ("fabric",),
    "silentgems": ("neoforge",),
    "densemekanism": ("neoforge",),   # no 1.21.1 file on Modrinth at all; the jar is neoforge.mods.toml
    "powah": ("neoforge",),
    "tfmg": ("neoforge",),
    "energizedpower": ("fabric", "neoforge"),
    "things": ("fabric",),
    "silentgear": ("neoforge",),
    "create_new_age": ("neoforge",),
    # Added Sept 2026, each queried per version for 1.21.1 on the Modrinth API:
    "techreborn": ("fabric",),
    "modern_industrialization": ("neoforge",),   # its 1.20.1 build is Fabric; the loader flips
    "occultism": ("neoforge",),
    "bigreactors": ("neoforge",),
    "mysticalagriculture": ("neoforge",),
    # Immersive Engineering, queried per version on the Modrinth API AND on CurseForge:
    # 1.20.1 Forge and NeoForge, 1.20.4 NeoForge, 1.21.1 NeoForge. Never Fabric, and nothing
    # above 1.21.1, which is why only two of our six bands carry it at all.
    "immersiveengineering": ("neoforge",),
    # Mekanism, queried per version on the Modrinth API and counted on BOTH platforms (Modrinth
    # 3.7M, CurseForge 175.4M): 1.20.1 Forge and NeoForge, 1.20.4 NeoForge, 1.21 and 1.21.1
    # NeoForge. Never Fabric, and nothing above 1.21.1, so the same two bands as IE carry it.
    "mekanism": ("neoforge",),
    "cobblemon": ("fabric", "neoforge"),
}
DEFAULT_CONDITIONAL_LOOT_MODULES = ("fabric", "neoforge")


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


def overlay_for(ore, host_cfg, face="side"):
    """Overlay key for this host, honouring a per-tier override. Mirrors OreType.overlayFor."""
    # host_overlays: a TRANSLUCENT ore (Silent's Gems' opal, Cobblemon) takes the colour of the rock
    # behind it, so each host needs its own precomposited overlay; ours render CUTOUT, which cannot do
    # partial alpha. A (side, end) pair serves a host whose end faces use another texture. Generator
    # only, because the Java side never reads overlay keys: the models carry them.
    host = next((h for h, c in HOSTS.items() if c is host_cfg), None)
    if host in ore.get("host_overlays", {}):
        chosen = ore["host_overlays"][host]
        if isinstance(chosen, tuple):
            return chosen[0] if face == "side" else chosen[1]
        return chosen
    if host_cfg["tier"] == "deepslate" and ore.get("deepslate_overlay"):
        return ore["deepslate_overlay"]
    return ore["overlay"]


def all_overlay_keys():
    """Every overlay texture key a model references, end-face overlays included."""
    return sorted({overlay_for(o, c, face) for _h, c, o, _v in variants() for face in ("side", "end")})


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
# Prefixes that disambiguate a clashing ore name read as the mod, not as a made-up word.
# Word parts that do not capitalise into the name a player should read. "mi" and "ie" are the two
# mods whose full names are far too long for a block name (Modern Industrialization, Immersive
# Engineering), so their prefixed ores read as the abbreviation their communities already use.
DISPLAY_NAMES = {"lapis": "Lapis Lazuli", "techreborn": "Tech Reborn", "mi": "MI", "ie": "IE"}


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
            textures = {
                "particle": host_cfg["side"],
                "side": host_cfg["side"],
                "end": host_cfg["end"],
                "overlay": f"{MOD_ID}:block/{overlay_for(ore, host_cfg)}_overlay",
            }
            end_overlay = overlay_for(ore, host_cfg, "end")
            if end_overlay != overlay_for(ore, host_cfg):
                textures["overlay_end"] = f"{MOD_ID}:block/{end_overlay}_overlay"
            write_json(
                os.path.join(root, "models", "block", f"{name}.json"),
                {
                    "parent": "minecraft:block/block",
                    "render_type": "minecraft:cutout",
                    "textures": textures,
                    "elements": [
                        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": cube_faces("#side", "#end")},
                        {"from": [0, 0, 0], "to": [16, 16, 16],
                         "faces": cube_faces("#overlay", "#overlay_end" if "overlay_end" in textures else None)},
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
        f"text.autoconfig.{MOD_ID}.category.things": "Things",
        f"text.autoconfig.{MOD_ID}.category.silent_gear": "Silent Gear",
        f"text.autoconfig.{MOD_ID}.category.create_new_age": "Create: New Age",
        f"text.autoconfig.{MOD_ID}.category.extreme_reactors": "Extreme Reactors",
        f"text.autoconfig.{MOD_ID}.category.modern_industrialization": "Modern Industrialization",
        f"text.autoconfig.{MOD_ID}.category.mystical_agriculture": "Mystical Agriculture",
        f"text.autoconfig.{MOD_ID}.category.occultism": "Occultism",
        f"text.autoconfig.{MOD_ID}.category.tech_reborn": "Tech Reborn",
        f"text.autoconfig.{MOD_ID}.category.immersive_engineering": "Immersive Engineering",
        f"text.autoconfig.{MOD_ID}.category.mekanism": "Mekanism",
        f"text.autoconfig.{MOD_ID}.category.cobblemon": "Cobblemon",

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
            "Mekanism's own ore has its own setting, above.",

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

        f"text.autoconfig.{MOD_ID}.option.modernIndustrialization": "Modern Industrialization: variants",
        f"text.autoconfig.{MOD_ID}.option.modernIndustrialization.@Tooltip":
            "Generate host-matched Modern Industrialization ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.mysticalAgriculture": "Mystical Agriculture: variants",
        f"text.autoconfig.{MOD_ID}.option.mysticalAgriculture.@Tooltip":
            "Generate host-matched inferium and prosperity ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.occultism": "Occultism: variants",
        f"text.autoconfig.{MOD_ID}.option.occultism.@Tooltip":
            "Generate host-matched silver ore. Does nothing unless Occultism is installed.",

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

        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether": "Extreme Reactors: nether variants (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether.@Tooltip[0]":
            "Puts benitoite in basalt and blackstone. Extreme Reactors generates it in netherrack",
        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether.@Tooltip[1]":
            "only, so this ADDS ore, thinned by the Nether tab's rarity and vein size.",
        f"text.autoconfig.{MOD_ID}.option.extremeReactorsNether.@Tooltip[2]":
            "Turn off to leave the Nether exactly as Extreme Reactors generates it.",

        f"text.autoconfig.{MOD_ID}.option.mekanism": "Mekanism: variants",
        f"text.autoconfig.{MOD_ID}.option.mekanism.@Tooltip":
            "Generate host-matched Mekanism ore (osmium, tin, lead, uranium and fluorite). Does"
            " nothing unless Mekanism is installed.",
        f"text.autoconfig.{MOD_ID}.option.immersiveEngineering": "Immersive Engineering: variants",
        f"text.autoconfig.{MOD_ID}.option.immersiveEngineering.@Tooltip":
            "Generate host-matched aluminum, lead, nickel, silver and uranium ore. Does nothing"
            " unless Immersive Engineering is installed.",

        f"text.autoconfig.{MOD_ID}.option.cobblemon": "Cobblemon: variants",
        f"text.autoconfig.{MOD_ID}.option.cobblemon.@Tooltip":
            "Generate host-matched evolution stone ore. Does nothing unless Cobblemon is installed.",

        f"text.autoconfig.{MOD_ID}.option.cobblemonNether": "Cobblemon: nether variants (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.cobblemonNether.@Tooltip[0]":
            "Puts fire stone ore in basalt and blackstone. Cobblemon generates it in netherrack",
        f"text.autoconfig.{MOD_ID}.option.cobblemonNether.@Tooltip[1]":
            "only, so this ADDS ore, thinned by the Nether tab's rarity and vein size.",
        f"text.autoconfig.{MOD_ID}.option.cobblemonNether.@Tooltip[2]":
            "Turn off to leave the Nether exactly as Cobblemon generates it.",
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


def read_mod_ore_tags():
    """Block and item id -> every c:ores/<x> tag it is in, read from each supported mod's own jar.

    Nested references are resolved inside the jar: Silent's Gems points c:ores/<gem> at its own
    #silentgems:ores/<gem>. A missing jar contributes nothing; the loot step already fails loudly
    for that case, so it cannot slip through silently.
    """
    out = {"block": {}, "item": {}}
    for mod_jar in MOD_JARS.values():
        if not mod_jar or not os.path.exists(mod_jar):
            continue
        with zipfile.ZipFile(mod_jar) as z:
            for kind in ("block", "item"):
                tags = {}
                for n in z.namelist():
                    m = re.match(rf"^data/([^/]+)/tags/{kind}s?/(.+)\.json$", n)
                    if m:
                        values = json.loads(z.read(n)).get("values", [])
                        tags[f"{m.group(1)}:{m.group(2)}"] = [
                            v["id"] if isinstance(v, dict) else v for v in values]

                def resolve(tag, seen):
                    members = set()
                    for value in tags.get(tag, []):
                        if value.startswith("#"):
                            if value[1:] not in seen:
                                members |= resolve(value[1:], seen | {value[1:]})
                        else:
                            members.add(value)
                    return members

                for tag in tags:
                    if tag.startswith("c:ores/"):
                        for member in resolve(tag, {tag}):
                            out[kind].setdefault(member, set()).add(tag[len("c:ores/"):])
    return out


def generate_data():
    """Loot tables and tags. Loot is TRANSFORMED from vanilla's own tables, never reconstructed."""

    if not os.path.exists(CLIENT_JAR):
        sys.exit(f"Client jar not found at {CLIENT_JAR} - needed to copy vanilla loot tables")

    ours = data_dir(MOD_ID)
    mc = data_dir("minecraft")
    conv = data_dir("c")
    mod_ore_tags = read_mod_ore_tags()

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
        needed[ore["overlay"]] = (ore["source"], ore["base"], ore.get("mod"), ore.get("texture_dir", ""))

    # The scratch file a source texture is written to. NAMESPACED BY MOD, because a source file name
    # is NOT unique across mods: Tech Reborn and Occultism both ship silver_ore.png, and Tech Reborn
    # and Modern Industrialization both ship lead_ore.png and tin_ore.png. Keyed on the bare file
    # name, the second jar read silently overwrote the first and BOTH overlays were then derived
    # from whichever mod happened to be read last. The basename is taken because a source may carry
    # a subfolder (Immersive Engineering keeps its ore art under block/metal/).
    def scratch(source, mod):
        return f"{mod}__{os.path.basename(source)}.png" if mod else f"{source}.png"

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(CLIENT_JAR) as jar:
            wanted = ({f"{s}.png" for s, _, m, _d in needed.values() if not m}
                      | {f"{b}.png" for _, b, _, _d in needed.values()})
            for filename in sorted(wanted):
                member = f"assets/minecraft/textures/block/{filename}"
                with jar.open(member) as src, open(os.path.join(tmp, filename), "wb") as dst:
                    dst.write(src.read())
        modded_sources = {(s, m, d) for s, _, m, d in needed.values() if m}
        for needed_mod in sorted({m for _s, m, _d in modded_sources}):
            if not os.path.exists(MOD_JARS.get(needed_mod, "")):
                continue
            with zipfile.ZipFile(MOD_JARS[needed_mod]) as create_jar:
                for source, mod, subdir in sorted(e for e in modded_sources if e[1] == needed_mod):
                    folder = f"{subdir}/" if subdir else ""
                    member = f"assets/{mod}/textures/block/{folder}{source}.png"
                    try:
                        data = create_jar.read(member)
                    except KeyError:
                        # Not every source is a plain sprite in its mod's jar. Cobblemon draws its
                        # evolution stone ores from elsewhere and their overlays are precomposited by
                        # hand anyway, so a miss here is a skip and a line, not a dead run.
                        print(f"  !! {member} is not in the {mod} jar - skipped")
                        continue
                    with open(os.path.join(tmp, scratch(source, mod)), "wb") as dst:
                        dst.write(data)

        for overlay_name, (source, base_name, _mod, _subdir) in sorted(needed.items()):
            # NEVER overwrite an overlay that already exists. Most of them have been hand cleaned
            # after extraction, and silently replacing that work with a fresh machine diff is a
            # one-way loss - the old behaviour made --textures a destructive flag nobody could run
            # safely. Delete the PNG to force a re-extraction of that one. (Carried over from the
            # 1.20.1 branch, which got this guard first.)
            if os.path.exists(os.path.join(out_dir, f"{overlay_name}_overlay.png")):
                continue
            if not os.path.exists(os.path.join(tmp, scratch(source, _mod))):
                continue                    # its source was not in the jar; already reported above
            base = Image.open(os.path.join(tmp, f"{base_name}.png")).convert("RGBA")
            ore_img = Image.open(os.path.join(tmp, scratch(source, _mod))).convert("RGBA")
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
        # A mod whose permission was given on the condition of a credit WITH A LINK BACK carries
        # a 'link'; its name is then rendered as one. Immersive Engineering is the case this exists
        # for, and the condition is binding, so do not drop the link when editing this table.
        name = f"[{info['display']}]({info['link']})" if info.get("link") else info["display"]
        lines.append(f"| {name} | {info['author'] or '-'} | {info['licence']} |")
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
    print("Updating README...")
    generate_readme()

    if args.textures:
        print("Extracting overlay textures...")
        generate_textures()
    else:
        print("Skipped textures (pass --textures to regenerate; it overwrites hand edits).")


if __name__ == "__main__":
    main()
