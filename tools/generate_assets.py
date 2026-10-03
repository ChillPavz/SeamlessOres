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

MOD_ID = "seamlessores"

# Classic Forge's datapack condition key. SINGULAR, and it takes ONE object rather than an array -
# it is ICondition.DEFAULT_FIELD, verified as "forge:condition" in forge 52 and 61 alike. Spelled
# differently again on 1.20.x Forge (unnamespaced "conditions", array), so re-verify against the
# real jar before carrying this to an older branch.
FORGE_CONDITION_KEY = "forge:condition"

# Colour-distance (summed per-channel) above which a pixel counts as ore rather than shaded stone.
# 0 keeps 141/256 px for iron and hazes over granite; 60 keeps 76 and looks right; 90 eats real blobs.
THRESHOLD = 60

# ONE JAR SERVES 26.1, 26.1.1, 26.1.2, 26.2 AND 26.3, so every loot table exists once per Minecraft
# version, read from THAT version's client jar and THAT version's build of each mod, and written into a
# pack overlay folder that pack.mcmeta enables by data format (mc26.1, mc26.2, mc26.3). Everything else
# this script writes (blockstates, models, lang, tags) is the same on every version and goes in the base.
# A profile is one version's jars, plus which mods a player can actually get there.
#
# Machine-specific defaults. A mod with no build at a version keeps the newest older jar: its variants
# never register there and its tables stay inert behind their conditions, so it lights up with no code
# change once a build appears (after its jar is re-read here).
REFS = "../references/jars/"
CLIENT_JARS = {
    "26.1": "~/.gradle/caches/neoformruntime/artifacts/minecraft_26.1.2_client.jar",
    "26.2": "~/.gradle/caches/neoformruntime/artifacts/minecraft_26.2_client.jar",
    "26.3": "~/.gradle/caches/neoformruntime/artifacts/minecraft_26.3_client.jar",
}

# Jars that are the same for every version: mods with no 26.x build at all (densemekanism, tfmg, things,
# create_new_age), and the 26.1.2-only mods (Silent's Gems, Silent Gear, Powah, Mystical Agriculture,
# Mythic Metals), whose 26.1.2 build is the only one there is.
#
# Mythic Metals: THE 26.1.2 BUILD. 0.26.0+26.1.2 (14 Sept 2026) has the same 36 ore blocks, ids,
# features and loot as 0.24.6+1.21, but NOT the same tool tags: 0.26.0 fills all three vanilla tiers
# plus two tags of its own (needs_copper_tools, needs_netherite_tool) that feed vanilla's
# incorrect_for_<tool> lists. Read from the old jar, our variants would be minable a tier or more too
# cheaply next to the mod's own ore.
COMMON_JARS = {
    "densemekanism": REFS + "densemekanism-1.21.1-1.2.jar",
    "tfmg": REFS + "tfmg-1.2.2.jar",
    "things": REFS + "things-0.4.2+1.21.jar",
    "create_new_age": REFS + "create-new-age-1.2.0+neoforge-mc1.21.1.jar",
    "silentgems": REFS + "silentgems-26.1.2-neoforge-5.1.4.jar",
    "silentgear": REFS + "silent-gear-26.1.2-neoforge-4.2.2.jar",
    "powah": REFS + "26.1.2-Powah-7.0.4-alpha.jar",
    "mysticalagriculture": REFS + "MysticalAgriculture-26.1.2-9.0.9.jar",
    "mythicmetals": REFS + "26.1.2-mythicmetals-0.26.0+26.1.2.jar",
}

PROFILES = {
    # 26.1, 26.1.1 and 26.1.2 (data formats up to 106). Tech Reborn 6.0.5 is one file for all three;
    # Occultism's 26.1 and 26.1.2 files ship identical silver loot, tags and art. Mythic Upgrades has no
    # 26.1 build: its 26.2 jar stands in, inert.
    "26.1": {
        "overlay": "mc26.1",
        "formats": (15, 106),
        "jars": {
            "create": REFS + "26.1.2-create-fly-26.1.2-6.0.9-4.jar",
            "mythicupgrades": REFS + "mythicupgrades-fabric-26.2-5.1.1.jar",
            "energizedpower": REFS + "26.1.2-energizedpower-3.0.0+26.1.x-neoforge.jar",
            "techreborn": REFS + "26.1.x-TechReborn-6.0.5.jar",
            "occultism": REFS + "occultism-26.1.2-neoforge-1.251.0.jar",
        },
        # Which supported mods a player can ACTUALLY get here, and on which loader (Modrinth API, re-
        # queried 1 Oct 2026; never from a project's "loaders" array, which is the union over every
        # file it ever shipped). Drives the README's honest per-version counts.
        #
        # AN ADD-ON'S AVAILABILITY IS THE INTERSECTION OF ITS OWN BUILD AND ITS REQUIRED PARENT'S:
        # Silent's Gems needs Silent Gear, which needs Silent Lib, and all three are on NeoForge here.
        "available": {
            "create": ("fabric",),
            "mythicmetals": ("fabric",),
            "silentgems": ("neoforge",),
            "silentgear": ("neoforge",),
            "powah": ("neoforge",),
            "energizedpower": ("fabric", "neoforge"),
            "techreborn": ("fabric",),
            "occultism": ("neoforge",),
            "mysticalagriculture": ("neoforge",),
        },
    },
    # 26.2 (data formats 107 to 120). Tech Reborn CHANGED ITS LOOT at 6.1.1: galena and bauxite drop
    # themselves on 6.0.5 and fortune-affected dust (silk touch for the ore) here, which is why 26.1 and
    # 26.2 are two overlays and not one. Mythic Upgrades 5.1.1 carries the same loot as 5.1.0.
    "26.2": {
        "overlay": "mc26.2",
        "formats": (107, 120),
        "jars": {
            "create": REFS + "26.2-create-fly-26.2-rc-2-6.0.9-1.jar",
            "mythicupgrades": REFS + "mythicupgrades-fabric-26.2-5.1.1.jar",
            "energizedpower": REFS + "energizedpower-3.0.0+26.2.x-neoforge.jar",
            "techreborn": REFS + "26.2-TechReborn-6.1.1.jar",
            "occultism": REFS + "occultism-26.2-neoforge-1.253.1.jar",
        },
        "available": {
            "create": ("fabric",),
            "mythicupgrades": ("fabric", "neoforge"),
            "energizedpower": ("fabric", "neoforge"),
            "techreborn": ("fabric",),
            "occultism": ("neoforge",),
        },
    },
    # 26.3 (data formats 121 and up): a new loot format, silk touch as a single "condition" (see
    # is_silk_touch_branch). Every mod with a 26.3 build is re-read from it:
    #   Tech Reborn 6.2.0 (Fabric; worldgen moved to feature/, loot reformatted, XP and strength
    #     byte-identical to 6.1.1).
    #   Energized Power 3.0.1+26.3.x, read from the FABRIC file: the two loaders' tin loot differs only
    #     in the NeoForge one carrying a random_sequence, which this script rewrites per variant anyway.
    #   Occultism 1.256.0 (NeoForge): worldgen moved to feature/ and loot reformatted; silver is still a
    #     plain Block at vanilla strength on the vanilla replaceables tags. Iesnium stays out.
    #   Mythic Upgrades 5.1.1 (28 Sept 2026, Fabric and NeoForge, NeoForge 26.3.0.26+). MythicBlocks
    #     disassembles identically to the 26.2 build and every ore texture is byte-identical; its loot
    #     tables are the 26.3 format and identical between the two loader files. Its five overworld
    #     ores still target the vanilla replaceables tags and ruby and sapphire still block_match
    #     netherrack, so nothing but the loot changes for us.
    # Create Fly has no 26.3 build; its 26.2 jar stands in, inert.
    "26.3": {
        "overlay": "mc26.3",
        "formats": (121, 999),
        "jars": {
            "create": REFS + "26.2-create-fly-26.2-rc-2-6.0.9-1.jar",
            "mythicupgrades": REFS + "mythicupgrades-fabric-26.3-5.1.1.jar",
            "energizedpower": REFS + "energizedpower-3.0.1+26.3.x-fabric.jar",
            "techreborn": REFS + "26.3-TechReborn-6.2.0.jar",
            "occultism": REFS + "occultism-26.3-neoforge-1.256.0.jar",
        },
        "available": {
            "mythicupgrades": ("fabric", "neoforge"),
            "energizedpower": ("fabric", "neoforge"),
            "techreborn": ("fabric",),
            "occultism": ("neoforge",),
        },
    },
}

CLIENT_JAR = None
CURRENT_PROFILE = None
MOD_JARS = {}
IN_RANGE_AVAILABILITY = {}


def use_profile(version):
    """Points CLIENT_JAR, MOD_JARS and IN_RANGE_AVAILABILITY at one Minecraft version's jars."""
    global CLIENT_JAR, MOD_JARS, IN_RANGE_AVAILABILITY, CURRENT_PROFILE
    CURRENT_PROFILE = version
    profile = PROFILES[version]
    CLIENT_JAR = os.path.expanduser(CLIENT_JARS[version])
    MOD_JARS = {**COMMON_JARS, **profile["jars"]}
    IN_RANGE_AVAILABILITY = profile["available"]


# Textures and anything else that is not per version read the 26.1 profile, which carries every ore.
use_profile("26.1")
# Source of the zinc overlay texture (Create Fly, mod id 'create'; CC0 plus the original Create MIT).
CREATE_JAR = MOD_JARS["create"]

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
    # Dripstone: no ore feature targets it. Its variants are swapped in where the dripstone cluster's
    # shell wraps an ore (DripstoneShell), so each stands in for the STONE-tier ore. Mirrors
    # OreTier.DRIPSTONE and OreType.vanillaFor.
    "dripstone":  {"tier": "dripstone", "ore_tier": "stone",
                   "side": "minecraft:block/dripstone_block", "end": "minecraft:block/dripstone_block"},
    # Cinnabar (26.2 and up): variants ADD ore, placed by our own rare features in the Sulfur Caves
    # (generate_cinnabar_worldgen), never by the injectors. Only CINNABAR_FAMILY gets one. "since"
    # keeps its loot out of the 26.1 profile, where the block does not exist. Mirrors
    # OreTier.CINNABAR, HostStone.CINNABAR and OreType.vanillaFor.
    "cinnabar":   {"tier": "cinnabar", "since": "26.2",
                   "side": "minecraft:block/cinnabar", "end": "minecraft:block/cinnabar"},
    "basalt":     {"tier": "nether",    "side": "minecraft:block/basalt_side", "end": "minecraft:block/basalt_top"},
    "blackstone": {"tier": "nether",    "side": "minecraft:block/blackstone",  "end": "minecraft:block/blackstone_top"},
}

# The ores that get a cinnabar variant, by OVERLAY key: Nether gold is also named "gold", its overlay
# is not. KEEP IN SYNC WITH OreType.cinnabarFamily().
CINNABAR_FAMILY = {"gold", "iron", "redstone", "zinc", "galena", "techreborn_lead", "techreborn_silver",
                   "occultism_silver", "silents_silver", "pyrite", "sphalerite"}

# Per cinnabar vein: (attempts per chunk, vein size). The attempts are THREE TIMES the default count:
# CinnabarOreFeature keeps each with probability cinnabarAmount / 300, so the config slider runs from
# none (0) through the default (100, e.g. iron 6 veins a chunk) to triple (300). Anything not listed
# uses DEFAULT. Attempts outside the Sulfur Caves are dropped by the biome filter. The default was
# raised about 50 percent after the owner's first look in game (3 Oct 2026).
CINNABAR_VEINS = {"iron": (18, 8), "gold": (14, 6), "redstone": (14, 6),
                  "techreborn_silver": (9, 5), "occultism_silver": (9, 5), "silents_silver": (9, 5)}
CINNABAR_VEIN_DEFAULT = (14, 6)

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
    "techreborn":     {"display": "Tech Reborn",       "category": "tech_reborn",
                       "licence": "MIT",          "author": "Team Reborn, modmuss50, drcrazy"},
    "occultism":      {"display": "Occultism",         "category": "occultism",
                       "licence": "MIT",          "author": "Kli Kli"},
    "mysticalagriculture": {"display": "Mystical Agriculture", "category": "mystical_agriculture",
                       "licence": "MIT",          "author": "BlakeBr0"},
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
    # No dripstone emerald: emerald generates only in mountain biomes, which never hold dripstone caves.
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
    # Tech Reborn (Fabric only at 26.1.x). Its nine overworld ores all target the vanilla replaceables
    # tags: a pure restyle. Uranium exists from 26.x and is prefixed, because the plain name is Modern
    # Industrialization's on the branches that carry it. The four end stone ores are not covered.
    # Prefixed where the plain name is already taken; the names match every other branch.
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
    {"name": "techreborn_uranium", "overlay": "techreborn_uranium", "source": "uranium_ore", "base": "stone",
     "mod": "techreborn",
     "tiers": {"stone": "uranium_ore", "deepslate": "deepslate_uranium_ore"}},
    # Occultism: silver only. Its tier word comes LAST (silver_ore_deepslate). Iesnium is a hidden ore
    # that only shows its texture once uncovered, so it gets no variants.
    {"name": "occultism_silver", "overlay": "occultism_silver", "source": "silver_ore", "base": "stone",
     "mod": "occultism",
     "tiers": {"stone": "silver_ore", "deepslate": "silver_ore_deepslate"}},
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
    # Mystical Agriculture: inferium and prosperity, both on the replaceables tags. Soulium sits on
    # its own soulstone.
    {"name": "inferium", "overlay": "inferium", "source": "inferium_ore", "base": "stone",
     "mod": "mysticalagriculture",
     "tiers": {"stone": "inferium_ore", "deepslate": "deepslate_inferium_ore"}},
    {"name": "prosperity", "overlay": "prosperity", "source": "prosperity_ore", "base": "stone",
     "mod": "mysticalagriculture",
     "tiers": {"stone": "prosperity_ore", "deepslate": "deepslate_prosperity_ore"}},
    # Silent's Gems opal is TRANSLUCENT: painted at partial opacity over each rock, so it takes the
    # colour of the rock behind it. One overlay per host, precomposited from the solved layer (see
    # the pack's solve_translucent_ore.py). Its nether feature places nothing (size 0, count 0).
    {"name": "opal", "overlay": "opal", "source": "opal_ore", "base": "stone",
     "mod": "silentgems", "raw_drop": "silentgems:opal",
     "host_overlays": {"granite": "opal_granite", "diorite": "opal_diorite", "andesite": "opal_andesite", "tuff": "opal_tuff",
                       "dripstone": "opal_dripstone"},
     "tiers": {"stone": "opal_ore", "deepslate": "deepslate_opal_ore"}},
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
# VERIFIED PER MINECRAFT VERSION on the Modrinth API for 26.1.2, never from the project-level
# "loaders" array (that is the union across every file a project ever shipped and lies per version):
#   create         fabric only      (Create Fly, mod id 'create')
#   silentgems     neoforge only    (needs silentgear, which needs silent-lib; both are on neoforge here)
#   silentgear     neoforge only
#   powah          neoforge only    (its cloth_config, guideme and jei deps all resolve here)
#   energizedpower fabric + neoforge
#   techreborn          fabric only      (added Sept 2026)
#   occultism           neoforge only    (added Sept 2026)
#   mysticalagriculture neoforge only    (added Sept 2026; 26.1.2 only, needs Cucumber, also 26.1.2)
#
# There is no forge module on this branch, so nothing is ever written to one.
#
# The other six (mythicupgrades, mythicmetals, densemekanism, tfmg, things, create_new_age) have NO
# 26.1.2 build. Their variants never register here and their data is inert. They keep their earlier
# routing so the derived registration lights them up with no code change if a build appears.
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
    "techreborn": ("fabric",),
    "occultism": ("neoforge",),
    "mysticalagriculture": ("neoforge",),
}
DEFAULT_CONDITIONAL_LOOT_MODULES = ("fabric", "neoforge")

def conditional_data_dir(module, namespace):
    return os.path.join(repo_root(), module, "src", "main", "resources", "data", namespace)


def fabric_pack_data_dir(mod, namespace):
    """Data folder of the Fabric built-in pack that loads only alongside `mod` (write_material_tags)."""
    return os.path.join(repo_root(), "fabric", "src", "main", "resources", "resourcepacks", mod, "data", namespace)


def write_material_tags(conv, conv_block, conv_item, entry_mod):
    """Write the per-material c:ores/<x> tags so that none exists in a Fabric world lacking its mods.

    FABRIC'S tags_populated CONDITION ASKS WHETHER A TAG EXISTS, NOT WHETHER ANYTHING IS IN IT: it
    fails only when the named tag is missing. A c:ores/nickel file whose only entries are optional
    TFMG variants therefore "populated" c:ores/nickel in a world without TFMG, recipes gated on it
    loaded with an ingredient that matches nothing, and Alloy Forgery crashed on world load reading
    the first ingredient of one (reported on 1.21.4). Fabric applies no resource conditions to tag
    files, so such a tag simply must not exist there: each mod's entries go in a built-in data pack of
    their own (fabric/.../resourcepacks/<mod>/), which SeamlessOresFabric registers only when that mod
    is loaded, and entries for a mod with no Fabric build are left out. Every other loader keeps
    exactly the file it always had. A material with no modded entries stays shared.
    """
    fabric_c = conditional_data_dir("fabric", "c")
    full_c = [conditional_data_dir(module, "c") for module in ("neoforge", "forge")
              if os.path.isdir(os.path.join(repo_root(), module))]
    packs = os.path.join(repo_root(), "fabric", "src", "main", "resources", "resourcepacks")
    # These trees are written only here, so clearing them is what keeps a renamed tag from lingering.
    for stale in [packs, os.path.join(fabric_c, "tags")] + [os.path.join(d, "tags") for d in full_c]:
        if os.path.isdir(stale):
            shutil.rmtree(stale)
    for kind, table in (("block", conv_block), ("item", conv_item)):
        for ore, values in table.items():
            rel = os.path.join("tags", kind, "ores", f"{ore}.json")
            shared = os.path.join(conv, rel)
            # A mod's entries go to that mod's conditional pack; an optional entry that belongs to
            # no mod (a cinnabar variant, absent on 26.1) is shared like a plain one.
            modded = [v for v in values if isinstance(v, dict) and v["id"] in entry_mod]
            if not modded:
                write_json(shared, {"values": values})
                continue
            if os.path.exists(shared):
                os.remove(shared)
            for d in full_c:
                write_json(os.path.join(d, rel), {"values": values})
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
            if host_cfg["tier"] == "cinnabar":
                if ore["overlay"] not in CINNABAR_FAMILY:
                    continue
                # Stands in for the stone ore, or the Nether one where the mod has no other.
                vanilla = ore["tiers"].get("stone") or ore["tiers"].get("nether")
            else:
                vanilla = ore["tiers"].get(host_cfg.get("ore_tier", host_cfg["tier"]))
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


# When set, write_json records into this dict instead of writing: main() runs the data step once per
# Minecraft version and then decides what goes in the base and what into that version's overlay.
CAPTURE = None


def write_json(path, data):
    if CAPTURE is not None:
        CAPTURE[os.path.normpath(path)] = data
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def host_exists_in(host_cfg, version):
    """Whether the host's block exists on that profile's Minecraft version (cinnabar: 26.2 up)."""
    since = host_cfg.get("since")
    return since is None or version_key(version) >= version_key(since)


def variant_name(host, ore):
    return f"{host}_{ore}_ore"


# Display-name overrides where the id fragment is not the vanilla display word. Vanilla calls the
# block "Lapis Lazuli Ore" (id lapis_ore) - "Granite Lapis Ore" would be the exact naming
# inconsistency users reported on the incumbent. Quartz stays "Quartz" (no "Nether" prefix: that
# prefix distinguishes an overworld quartz that does not exist, and ours is already host-prefixed).
# Prefixes that disambiguate a clashing ore name read as the mod, not as a made-up word.
DISPLAY_NAMES = {"lapis": "Lapis Lazuli", "techreborn": "Tech Reborn", "mi": "MI"}


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
            # NO render_type FIELD FROM 26.1. The chunk layer is DERIVED from the texture's own
            # alpha (SpriteContents.computeTransparency feeding ChunkSectionLayer.byTransparency),
            # so there is nothing to declare and no per-loader API to call. Below 26.1 both halves
            # are needed instead: the field here for NeoForge and Forge, and a Fabric client
            # initializer calling BlockRenderLayerMap.
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
                    "textures": textures,
                    "elements": [
                        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": cube_faces("#side", "#end")},
                        {"from": [0, 0, 0], "to": [16, 16, 16],
                         "faces": cube_faces("#overlay", "#overlay_end" if "overlay_end" in textures else None)},
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
        f"text.autoconfig.{MOD_ID}.category.occultism": "Occultism",
        f"text.autoconfig.{MOD_ID}.category.tech_reborn": "Tech Reborn",
        f"text.autoconfig.{MOD_ID}.category.mystical_agriculture": "Mystical Agriculture",

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
        f"text.autoconfig.{MOD_ID}.category.sulfur_caves": "Sulfur Caves",
        f"text.autoconfig.{MOD_ID}.option.cinnabar": "Cinnabar ores (adds ore)",
        f"text.autoconfig.{MOD_ID}.option.cinnabar.@Tooltip[0]":
            "Gold, silver, iron, redstone and sulfide ores inside the Sulfur Caves' cinnabar,",
        f"text.autoconfig.{MOD_ID}.option.cinnabar.@Tooltip[1]":
            "where vanilla puts none.",
        f"text.autoconfig.{MOD_ID}.option.cinnabarAmount": "Cinnabar ore amount (percent)",
        f"text.autoconfig.{MOD_ID}.option.cinnabarAmount.@Tooltip[0]":
            "How much cinnabar ore forms, in percent of the default. 0 places none,",
        f"text.autoconfig.{MOD_ID}.option.cinnabarAmount.@Tooltip[1]":
            "300 places three times as much. Applies to newly generated chunks.",
        f"text.autoconfig.{MOD_ID}.option.lushCaves": "Lush Caves clay and moss (removes ore)",
        f"text.autoconfig.{MOD_ID}.option.lushCaves.@Tooltip[0]":
            "Ore left bare in a Lush Caves clay floor or moss carpet becomes clay or moss, so a",
        f"text.autoconfig.{MOD_ID}.option.lushCaves.@Tooltip[1]":
            "little ore is removed there. Bone meal on moss works exactly as in vanilla.",
        f"text.autoconfig.{MOD_ID}.option.sulfurCaves": "Sulfur Caves stay bare (removes ore)",
        f"text.autoconfig.{MOD_ID}.option.sulfurCaves.@Tooltip[0]":
            "No ore in or against the sulfur and cinnabar of the Sulfur Caves, including the large",
        f"text.autoconfig.{MOD_ID}.option.sulfurCaves.@Tooltip[1]":
            "copper and iron veins there.",

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

        f"text.autoconfig.{MOD_ID}.option.mysticalAgriculture": "Mystical Agriculture: variants",
        f"text.autoconfig.{MOD_ID}.option.mysticalAgriculture.@Tooltip":
            "Generate host-matched inferium and prosperity ore. Does nothing unless the mod is installed.",
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


def is_silk_touch_branch(child):
    """Whether a loot entry is the silk-touch branch, which drops the block itself.

    Three spellings, and 26.3 introduced two of them. Up to 26.2 an entry carries a "conditions" LIST
    holding a minecraft:match_tool. From 26.3 it carries a single "condition": vanilla, Energized Power
    and Mythic Upgrades name the shared predicate as a string ("minecraft:tool/can_silk_touch"), Tech
    Reborn writes the match_tool object inline. Missing any of them silently makes a silk-touched
    variant drop the source mod's block instead of ours.
    """
    if any(cond.get("condition") == "minecraft:match_tool" for cond in child.get("conditions", [])):
        return True
    condition = child.get("condition")
    if isinstance(condition, str):
        return condition.endswith("can_silk_touch")
    if isinstance(condition, dict):
        return condition.get("type") == "minecraft:match_tool"
    return False


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
    foreign_tool_tags = {}          # a source mod's OWN needs_* tags, mirrored for our variants
    conv_block = {}
    conv_item = {}
    ores_in_ground = {}
    entry_mod = {}      # a modded tag entry's id -> the mod that variant belongs to

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
        mod_own_tool_tags = {}          # (namespace, tag path) -> the blocks that mod lists there
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
                # A mod can also gate ITS OWN tools with tags in its own namespace and feed those
                # into vanilla's incorrect_for_<tool> composition, which is a tier requirement by
                # another route. Mythic Metals 0.26.0 does exactly that: needs_copper_tools carries
                # five of its ores and needs_netherite_tool two more, so a variant left out of them
                # is minable a tier too cheaply next to the block it stands in for. Read whatever
                # the jar has rather than naming the two, and mirror membership the same way.
                for member in mod_jar_zip.namelist():
                    match = re.match(r"^data/([^/]+)/tags/block/(needs_[^/]+)\.json$", member)
                    if not match or match.group(1) == "minecraft":
                        continue
                    try:
                        listed = json.loads(mod_jar_zip.read(member)).get("values", [])
                    except ValueError:
                        continue
                    mod_own_tool_tags.setdefault((match.group(1), match.group(2)), set()).update(
                        str(v["id"] if isinstance(v, dict) else v) for v in listed)
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
                                if is_silk_touch_branch(child):
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
                            f"{mod_jar_path}. Fix its path in PROFILES or COMMON_JARS."
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
                                if is_silk_touch_branch(child):
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

                if not host_exists_in(host_cfg, CURRENT_PROFILE):
                    pass    # no such block on this version: a table naming its item would not load
                elif mod:
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
                # Cinnabar variants do not exist on 26.1, so theirs are optional as well.
                entry = {"id": our_id, "required": False} if mod or host_cfg.get("since") else our_id
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
                # Cinnabar has no ground tag of its own, and is neither stone nor netherrack.
                if host_cfg["tier"] != "cinnabar":
                    ground = {"stone": "stone", "deepslate": "deepslate", "nether": "netherrack"}[
                        host_cfg.get("ore_tier", host_cfg["tier"])]
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
    # SulfurCaves: no ore feature places a block touching one of these. Both are 26.2+ blocks, so each
    # entry is optional and the tag is empty on 26.1.x.
    write_json(os.path.join(ours, "tags", "block", "keeps_ore_out.json"),
               {"values": [{"id": "minecraft:sulfur", "required": False},
                           {"id": "minecraft:cinnabar", "required": False}]})

    if foreign_tool_tags:
        print("  source mods' own tier tags mirrored: "
              + ", ".join(f"{ns}:{tag} ({len(v)})" for (ns, tag), v in sorted(foreign_tool_tags.items())))
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


OVERWORLD_HOSTS = ["granite", "diorite", "andesite", "tuff", "dripstone", "cinnabar"]
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
    """How many blocks a player can actually reach, per Minecraft version and loader.

    Derived rather than written down because it is the single most version-specific fact in this
    README: which mods have a build for a given loader flips between Minecraft versions, and a number
    copied from one version to another is wrong without looking wrong.
    """
    per_version = {}
    for version in PROFILES:
        counts = {}
        for _host, cfg, ore, _v in variants():
            if host_exists_in(cfg, version):
                counts[ore.get("mod")] = counts.get(ore.get("mod"), 0) + 1
        per_version[version] = counts

    lines = [
        "A variant is registered only when the mod that owns its ore is installed, so how many of",
        "these you can actually see depends on which mods have a build for your loader at your",
        "Minecraft version:",
        "",
        "| Minecraft | Loader | Blocks | Supported mods available here |",
        "|---|---|---|---|",
    ]
    # Spelled out rather than capitalize()d: that would give "Neoforge".
    display = {"fabric": "Fabric", "neoforge": "NeoForge", "forge": "Forge"}
    label = {"26.1": "26.1 to 26.1.2", "26.2": "26.2", "26.3": "26.3"}
    for version, profile in PROFILES.items():
        per_mod = dict(per_version[version])
        vanilla = per_mod.pop(None, 0)
        for loader in ("fabric", "neoforge"):
            total = vanilla
            available = []
            for mod, count in per_mod.items():
                # Honest availability, not the inert loot routing: a mod with no build for this
                # version and loader contributes no blocks a player can see, though its gated data ships.
                if loader in profile["available"].get(mod, ()):
                    total += count
                    available.append(MODS[mod]["display"])
            names = ", ".join(sorted(available)) if available else "none at this Minecraft version"
            lines.append(f"| {label[version]} | {display[loader]} | {total} | {names} |")
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


def overlay_path(path, overlay):
    """<module>/src/main/resources/data/... -> <module>/src/main/resources/<overlay>/data/..."""
    marker = os.path.join("src", "main", "resources", "data") + os.sep
    head, sep, tail = path.partition(marker)
    assert sep, path
    return os.path.join(head, "src", "main", "resources", overlay, "data", tail)


def is_loot(path):
    return (os.sep + "loot_table" + os.sep) in path


def generate_cinnabar_worldgen():
    """One rare vein per cinnabar variant, in the Sulfur Caves only, for 26.2 and 26.3.

    Every file goes in the mc26.2 and mc26.3 overlays, so 26.1, which has no cinnabar and no Sulfur
    Caves, never reads one: a worldgen file naming an absent block is a hard crash, not a skip. A
    modded variant's files carry that mod's load conditions as well. NeoForge attaches them with a
    biome modifier each; Fabric does it in code (SeamlessOresFabric).
    """
    common = os.path.join(repo_root(), "common", "src", "main", "resources")
    neoforge = os.path.join(repo_root(), "neoforge", "src", "main", "resources")
    overlays = {"mc26.2": "configured_feature", "mc26.3": "feature"}
    for overlay in overlays:
        for root, sub in ((common, "worldgen"), (neoforge, "neoforge")):
            folder = os.path.join(root, overlay, "data", MOD_ID, sub)
            if os.path.isdir(folder):
                for dirpath, _dirs, files in os.walk(folder):
                    for f in files:
                        if f.startswith("cinnabar_"):
                            os.remove(os.path.join(dirpath, f))
    count = 0
    for host, host_cfg, ore, _vanilla in variants():
        if host_cfg["tier"] != "cinnabar":
            continue
        block = f"{MOD_ID}:{variant_name(host, ore['name'])}"
        key = f"cinnabar_{ore['name']}"
        veins, size = CINNABAR_VEINS.get(ore["overlay"], CINNABAR_VEIN_DEFAULT)
        mod = ore.get("mod")
        conditions = {}
        if mod:
            conditions = {
                "fabric:load_conditions": [{"condition": "fabric:registry_contains",
                                            "registry": "minecraft:block", "values": [block]}],
                "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": mod}],
            }
        target = {"predicate_type": "minecraft:block_match", "block": "minecraft:cinnabar"}
        old = {"type": f"{MOD_ID}:cinnabar_ore",
               "config": {"size": size, "discard_chance_on_air_exposure": 0.0,
                          "targets": [{"target": target, "state": {"Name": block}}]}, **conditions}
        new = {"type": f"{MOD_ID}:cinnabar_ore", "size": size, "discard_chance_on_air_exposure": 0.0,
               "targets": [{"target": target, "state": block}], **conditions}
        placed = {"feature": f"{MOD_ID}:{key}",
                  "placement": [
                      {"type": "minecraft:count", "count": veins},
                      {"type": "minecraft:in_square"},
                      {"type": "minecraft:height_range",
                       "height": {"type": "minecraft:uniform",
                                  "min_inclusive": {"above_bottom": 0},
                                  "max_inclusive": {"absolute": 96}}},
                      {"type": "minecraft:biome"}],
                  **conditions}
        modifier = {"type": "neoforge:add_features", "biomes": "minecraft:sulfur_caves",
                    "features": f"{MOD_ID}:{key}", "step": "underground_ores"}
        if mod:
            modifier["neoforge:conditions"] = conditions["neoforge:conditions"]
        for overlay, kind in overlays.items():
            data = os.path.join(common, overlay, "data", MOD_ID, "worldgen")
            write_json(os.path.join(data, kind, f"{key}.json"), old if kind == "configured_feature" else new)
            write_json(os.path.join(data, "placed_feature", f"{key}.json"), placed)
            write_json(os.path.join(neoforge, overlay, "data", MOD_ID, "neoforge", "biome_modifier",
                                    f"{key}.json"), modifier)
        count += 1
    print(f"  cinnabar: {count} veins, Sulfur Caves only, mc26.2 and mc26.3 overlays")


def generate_versioned_data():
    """Runs the data step once per profile and routes what it wrote.

    Loot tables go into that version's overlay folder, in whichever module the run put them (common
    for vanilla ores, fabric / neoforge for a mod's conditional tables). Everything else must come out
    the same for every version, because it goes in the base and every version reads it; the run stops
    if it does not, rather than let one version's tags silently win.
    """
    global CAPTURE
    runs = {}
    for version in PROFILES:
        use_profile(version)
        print(f"  [{version}] client {os.path.basename(CLIENT_JAR)}")
        CAPTURE = {}
        try:
            generate_data()
        finally:
            runs[version], CAPTURE = CAPTURE, None
    use_profile("26.1")

    base = {}
    for version, written in runs.items():
        for path, data in written.items():
            if is_loot(path):
                continue
            if path in base and base[path][1] != data:
                sys.exit(f"  !! {os.path.relpath(path, repo_root())} differs between {base[path][0]} and "
                         f"{version}; it cannot go in the base. Route it per version.")
            base.setdefault(path, (version, data))

    # Clear every loot tree this script owns, base and overlays, so a renamed variant cannot linger.
    for module in ("common", "fabric", "neoforge"):
        resources = os.path.join(repo_root(), module, "src", "main", "resources")
        for folder in [""] + [profile["overlay"] for profile in PROFILES.values()]:
            loot = os.path.join(resources, folder, "data", MOD_ID, "loot_table")
            if os.path.isdir(loot):
                shutil.rmtree(loot)

    for path, (_version, data) in base.items():
        write_json(path, data)
    for version, written in runs.items():
        overlay = PROFILES[version]["overlay"]
        tables = [p for p in written if is_loot(p)]
        for path in tables:
            write_json(overlay_path(path, overlay), written[path])
        print(f"  [{version}] {len(tables)} loot tables -> {overlay}/")


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
    print("Generating loot tables and tags, once per Minecraft version...")
    generate_versioned_data()
    generate_cinnabar_worldgen()
    print("Updating README...")
    generate_readme()

    if args.textures:
        print("Extracting overlay textures...")
        generate_textures()
    else:
        print("Skipped textures (pass --textures to regenerate; it overwrites hand edits).")


if __name__ == "__main__":
    main()
