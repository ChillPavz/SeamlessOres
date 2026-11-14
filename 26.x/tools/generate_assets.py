#!/usr/bin/env python3
"""
Generates everything about Seamless Ores' blocks that is data: blockstates, two-layer block models,
item model definitions, the lang file, loot tables, tags, the README's block lists, the Java tables
(ModdedPairs, OreGeology, the config switches) and (optionally) the ore overlay textures.

One table of ores (ORE_DEFS, mirroring OreType.java) and one of hosts (READ from HostStone.java):
the game's own rock, where the pairs follow from each ore's tiers, and the stones other mods place,
where they are measured (modded_pairs.json) and cut by the geology rule (geology.py).

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

# The machinery every band shares (models, loot, tags, the host table, the texture pool, geology).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "shared", "tools"))
import assetgen  # noqa: E402
import parity  # noqa: E402
import placed  # noqa: E402
import renamed  # noqa: E402
import retired  # noqa: E402
from assetgen import (MOD_ID, TOOL_TAGS, assert_no_dashes, jar_tags, look_models,  # noqa: E402
                      read_mod_tags, defer_to_source, silk_touch_to, texture_path, title, write_json,
                      write_texture_json)

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
# The Seamless Ores project folder's references/jars: this file is
# <project>/seamlessores-monolith/26.x/tools/generate_assets.py.
REFS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))), "references", "jars") + os.sep
CLIENT_JARS = {
    "26.1": "~/.gradle/caches/neoformruntime/artifacts/minecraft_26.1.2_client.jar",
    "26.2": "~/.gradle/caches/neoformruntime/artifacts/minecraft_26.2_client.jar",
    "26.3": "~/.gradle/caches/neoformruntime/artifacts/minecraft_26.3_client.jar",
}

# Jars that are the same for every version: mods with no 26.x build at all (densemekanism, tfmg, things,
# create_new_age), and the 26.1.2-only mods (Mystical Agriculture, Mythic Metals), whose 26.1.2
# build is the only one there is. Powah's 26.1.2 jar is the default; the 26.2 profile names its own. Silent's Gems and Silent Gear also have 26.2 builds (the 26.2 profile).
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
            # Ice and Fire Community Edition 2.2-beta.4, its only 26.x build (a beta, owner 17 Oct 2026).
            "iceandfire": REFS + "26.1.2-iceandfire-ce-2.2-beta.4.jar",
            "theurgy": REFS + "theurgy-26.1.2-neoforge-1.116.0.jar",
            "evilcraft": REFS + "evilcraft-26.1.2-neoforge-1.2.108-1172.jar",
            "betternether": REFS + "better-nether-26.101.2.jar",
            "denseores": REFS + "denseores-neoforge-1.4.1.jar",
            "railcraft": REFS + "railcraft-reborn-26.1.2-1.4.9.jar",
            "bronze": REFS + "bronze-neoforge-2.3.0+26.1.jar",
            "oritech": REFS + "oritech-2.0.0-exp12.jar",
            "thesilverage": REFS + "thesilverage-neoforge-26.1.2-1.4.0.jar",
            "theleadage": REFS + "theleadage-neoforge-26.1.2-1.2.1.jar",
            "gemsandcrystals": REFS + "gemsandcrystals-1.6.0-neoforge+26.1.2.jar",
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
            # CurseForge only (Ice and Fire CE is not on Modrinth); 26.1.2 NeoForge, needs Jupiter and Uranus.
            "iceandfire": ("neoforge",),
            "theurgy": ("neoforge",),
            "evilcraft": ("neoforge",),
            "betternether": ("fabric",),
            "denseores": ("fabric", "neoforge"),
            "railcraft": ('neoforge',),
            "bronze": ('fabric', 'neoforge'),
            "oritech": ('neoforge',),
            "thesilverage": ('fabric', 'neoforge'),
            "theleadage": ('fabric', 'neoforge'),
            "gemsandcrystals": ('fabric', 'neoforge'),
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
            "iceandfire": REFS + "26.1.2-iceandfire-ce-2.2-beta.4.jar",   # no 26.2 build: stands in, inert
            "railcraft": REFS + "railcraft-reborn-26.1.2-1.4.9.jar",   # no 26.2 build: stands in, inert
            # Silent's Gems 5.2.0 and Silent Gear 4.3.0 (NeoForge, 20 Oct 2026; Silent Lib 12.0.0): the same
            # ore blocks, worldgen and tool tags as their 26.1.2 builds; the loot only drops bonus_rolls.
            "silentgems": REFS + "silentgems-26.2-neoforge-5.2.0.jar",
            "silentgear": REFS + "silent-gear-26.2-neoforge-4.3.0.jar",
            "theurgy": REFS + "theurgy-26.2-neoforge-1.118.1.jar",
            "evilcraft": REFS + "evilcraft-26.2-neoforge-1.2.98-1108.jar",
            "betternether": REFS + "better-nether-26.201.4.jar",
            "denseores": REFS + "denseores-neoforge-26.2-1.4.1.jar",
            "bronze": REFS + "bronze-neoforge-2.3.0+26.1.jar",   # no 26.2 build: stands in, inert
            "oritech": REFS + "oritech-2.0.0-exp12.jar",   # no 26.2 build: stands in, inert
            # Powah 8.0.1-alpha (NeoForge, 10 Nov 2026): the same ore blocks, worldgen and tags as 7.0.4 on
            # 26.1.2; the loot only drops bonus_rolls and a count of 1.
            "powah": REFS + "26.2-Powah-8.0.1-alpha.jar",
            "thesilverage": REFS + "thesilverage-neoforge-26.2-1.4.0.jar",
            "theleadage": REFS + "theleadage-neoforge-26.2-1.2.1.jar",
            "gemsandcrystals": REFS + "gemsandcrystals-1.6.0-neoforge+26.2.jar",
        },
        "available": {
            "create": ("fabric",),
            "powah": ("neoforge",),
            "mythicupgrades": ("fabric", "neoforge"),
            "energizedpower": ("fabric", "neoforge"),
            "techreborn": ("fabric",),
            "occultism": ("neoforge",),
            "silentgems": ("neoforge",),
            "silentgear": ("neoforge",),
            "theurgy": ("neoforge",),
            "evilcraft": ("neoforge",),
            "betternether": ("fabric",),
            "denseores": ("fabric", "neoforge"),
            "thesilverage": ('fabric', 'neoforge'),
            "theleadage": ('fabric', 'neoforge'),
            "gemsandcrystals": ('fabric', 'neoforge'),
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
            "iceandfire": REFS + "26.1.2-iceandfire-ce-2.2-beta.4.jar",   # no 26.3 build: stands in, inert
            "railcraft": REFS + "railcraft-reborn-26.1.2-1.4.9.jar",   # no 26.3 build: stands in, inert
            "denseores": REFS + "denseores-neoforge-26.2-1.4.1.jar",       # no 26.3 build: stands in, inert
            "theurgy": REFS + "theurgy-26.3-neoforge-1.120.0.jar",
            "evilcraft": REFS + "evilcraft-26.3-neoforge-1.2.98-1170.jar",
            "betternether": REFS + "better-nether-26.301.2.jar",
            "bronze": REFS + "bronze-neoforge-2.3.0+26.1.jar",   # no 26.3 build: stands in, inert
            "oritech": REFS + "oritech-2.0.0-exp12.jar",   # no 26.3 build: stands in, inert
            # Powah 9.0.0-alpha (NeoForge, 11 Nov 2026): the same ore blocks, tags and features as 7.0.4 (26.3 writes
            # features flat under worldgen/feature); the loot only drops default fields.
            "powah": REFS + "26.3-Powah-9.0.0-alpha.jar",
            "thesilverage": REFS + "thesilverage-neoforge-26.3-1.4.0.jar",
            "theleadage": REFS + "theleadage-neoforge-26.3-1.2.1.jar",
            "gemsandcrystals": REFS + "gemsandcrystals-1.6.0-neoforge+26.3.jar",
        },
        "available": {
            "powah": ("neoforge",),
            "mythicupgrades": ("fabric", "neoforge"),
            "energizedpower": ("fabric", "neoforge"),
            "techreborn": ("fabric",),
            "occultism": ("neoforge",),
            "theurgy": ("neoforge",),
            "evilcraft": ("neoforge",),
            "betternether": ("fabric",),
            "thesilverage": ('fabric', 'neoforge'),
            "theleadage": ('fabric', 'neoforge'),
            "gemsandcrystals": ('fabric', 'neoforge'),
        },
    },
}

CLIENT_JAR = None
CURRENT_PROFILE = None
MOD_JARS = {}
IN_RANGE_AVAILABILITY = {}


_SOURCE_TAGS = None


def all_source_tags():
    """Every tag of every profile's jars at once (parity.SourceTags). One union, not one per version:
    tags go in the base every version reads, and an entry for a variant or a tag a version lacks is
    inert there (optional entry; a tag nothing reads)."""
    global _SOURCE_TAGS
    if _SOURCE_TAGS is None:
        jars = [os.path.expanduser(j) for j in CLIENT_JARS.values()] + list(COMMON_JARS.values())
        for profile in PROFILES.values():
            jars += profile["jars"].values()
        _SOURCE_TAGS = parity.SourceTags(sorted(set(jars)))
    return _SOURCE_TAGS


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

# How each host stone is drawn, which only this script needs: the host table itself (which stones,
# which tier, which ores) is READ from HostStone.java (placed.Hosts), so the blocks that register and
# the files generated here cannot drift apart. A host with several looks must be mirrored exactly, or
# its ore is the one tile that never varies. Read from each stone's own blockstate and models.
#   single:          one texture on every face.
#   column:          a side texture and an end texture: basalt AND blackstone are cube_column blocks in
#                    vanilla, and the side sprite on all six faces makes our tops mismatch the stone.
#   mirrored_turned: Wilder Wild gabbro, four random models: plain, mirrored, and each turned 180.
#   textures4:       Create's natural stones, four random models, each its own texture (<prefix>0 to 3).
HOST_LOOK = {
    "minecraft:granite": ("single", "minecraft:block/granite"),
    "minecraft:diorite": ("single", "minecraft:block/diorite"),
    "minecraft:andesite": ("single", "minecraft:block/andesite"),
    "minecraft:tuff": ("single", "minecraft:block/tuff"),
    "minecraft:dripstone_block": ("single", "minecraft:block/dripstone_block"),
    "minecraft:cinnabar": ("single", "minecraft:block/cinnabar"),
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
    "forbidden_arcanus:darkstone": ("single", "forbidden_arcanus:block/darkstone"),
    "mythicupgrades:aquamarine_schist": ("single", "mythicupgrades:block/aquamarine_schist"),
    "mythicupgrades:citrine_schist": ("single", "mythicupgrades:block/citrine_schist"),
    "mythicupgrades:peridot_schist": ("single", "mythicupgrades:block/peridot_schist"),
    "mythicupgrades:topaz_schist": ("single", "mythicupgrades:block/topaz_schist"),
    "mythicupgrades:sapphire_schist": ("single", "mythicupgrades:block/sapphire_schist"),
    "mythicupgrades:jade_schist": ("single", "mythicupgrades:block/jade_schist"),
    "promenade:asphalt": ("single", "promenade:block/asphalt"),
    "promenade:blunite": ("single", "promenade:block/blunite"),
    "regions_unexplored:mossy_stone": ("moss_mirrored_turned", "minecraft:block/stone", "seamlessores:block/regions_unexplored_mossy_stone_moss"),
    "regions_unexplored:argillite": ("mirrored_turned", "regions_unexplored:block/argillite"),
    "regions_unexplored:chalk": ("single", "regions_unexplored:block/chalk"),
    "wilderwild:gabbro": ("mirrored_turned", "wilderwild:block/gabbro"),
    "yungscavebiomes:ancient_sandstone": ("bottom_top", "yungscavebiomes:block/ancient_sandstone", "yungscavebiomes:block/ancient_sandstone_top", "yungscavebiomes:block/ancient_sandstone_bottom"),
    "natures_spirit:chert": ("column", "natures_spirit:block/chert", "natures_spirit:block/chert_top"),
    "natures_spirit:travertine": ("single", "natures_spirit:block/travertine"),
    "natures_spirit:white_chalk": ("single", "natures_spirit:block/white_chalk"),
    "natures_spirit:pink_sandstone": ("bottom_top", "natures_spirit:block/pink_sandstone", "natures_spirit:block/pink_sandstone_top", "natures_spirit:block/pink_sandstone_bottom"),
    "betterend:flavolite": ("single", "betterend:block/flavolite"),
    "betterend:violecite": ("single", "betterend:block/violecite"),
    "betterend:sulphuric_rock": ("turned4", "betterend:block/sulphuric_rock", "betterend:block/sulphuric_rock_top"),
    "betterend:brimstone": ("single", "betterend:block/inactive_brimstone"),
    "betterend:umbralith": ("weighted", [("betterend:block/umbralith", 10), ("betterend:block/umbralith_2", 10), ("betterend:block/umbralith_6", 10), ("betterend:block/umbralith_7", 10), ("betterend:block/umbralith_3", 1), ("betterend:block/umbralith_4", 1), ("betterend:block/umbralith_5", 1)]),
    "betterend:azure_jadestone": ("single", "betterend:block/azure_jadestone"),
    "betterend:sandy_jadestone": ("single", "betterend:block/sandy_jadestone"),
    "betterend:virid_jadestone": ("single", "betterend:block/virid_jadestone"),
}

# A host block that only some Minecraft versions have: its loot stays out of the earlier profiles.
HOST_SINCE = {"minecraft:cinnabar": "26.2"}

# The mods that PLACE a host stone, for the README and the config screen. Where each exists at 26.x,
# measured with references/tools/som-grid/availability.py.
STONE_MODS = {
    # Deep blackstone: the game's rock, laid by Terralith's caves (the mod or its datapack).
    "minecraft": {"display": "Terralith", "bands": "its mod or datapack, every 26.x version, both loaders"},
    "blockus": {"display": "Blockus", "bands": "Fabric, 26.1.x to 26.3"},
    "create": {"display": "Create", "bands": "Create Fly, Fabric, 26.1.2 and 26.2"},
    "forbidden_arcanus": {"display": "Forbidden and Arcanus", "bands": "NeoForge, 26.1.2"},
    "mythicupgrades": {"display": "Mythic Upgrades", "bands": "Fabric and NeoForge, 26.2 and 26.3"},
    "promenade": {"display": "Promenade", "bands": "Fabric on every 26.x version, NeoForge on 26.3"},
    "regions_unexplored": {"display": "Regions Unexplored", "bands": "Fabric and NeoForge, 26.1.x"},
    "wilderwild": {"display": "Wilder Wild", "bands": "Fabric 26.1.x to 26.3, NeoForge 26.2 and 26.3"},
    "yungscavebiomes": {"display": "YUNG's Cave Biomes", "bands": "Fabric and NeoForge, 26.1.x"},
    "natures_spirit": {"display": "Nature's Spirit", "bands": "Fabric and NeoForge, 26.1.x"},
    "betterend": {"display": "BetterEnd", "bands": "Fabric, 26.1.x to 26.3"},
}

# The ores that get a cinnabar variant, by OVERLAY key: Nether gold is also named "gold", its overlay
# is not. KEEP IN SYNC WITH OreType.cinnabarFamily().
CINNABAR_FAMILY = {"gold", "iron", "redstone", "zinc", "galena", "techreborn_lead", "techreborn_silver",
                   "occultism_silver", "silents_silver", "pyrite", "sphalerite"}

# Each cinnabar ore MIRRORS the features of the ore it stands in for: one cinnabar feature per source
# feature, with that feature's own vein size, veins per chunk, height range and air exposure, read out
# of the game or mod jar for each version (generate_cinnabar_worldgen). Only the target (cinnabar), the
# biome (Sulfur Caves) and the vein count change: the count is TRIPLED, and CinnabarOreFeature keeps
# each vein with probability cinnabarAmount / 300, so the slider's 100 is exactly the source's count.
# (owner, 3 Oct 2026: "mirror their original values"). Gold's badlands-only extra feature is left out.
# KEEP IN SYNC WITH CinnabarVeins.SOURCES. Values: (namespace, [placed feature paths]).
CINNABAR_SOURCES = {
    "gold": ("minecraft", ["ore_gold", "ore_gold_lower"]),
    "iron": ("minecraft", ["ore_iron_upper", "ore_iron_middle", "ore_iron_small"]),
    "redstone": ("minecraft", ["ore_redstone", "ore_redstone_lower"]),
    "zinc": ("create", ["zinc_ore"]),
    "galena": ("techreborn", ["galena_ore"]),
    "techreborn_lead": ("techreborn", ["lead_ore"]),
    "techreborn_silver": ("techreborn", ["silver_ore"]),
    "pyrite": ("techreborn", ["pyrite_ore"]),
    "sphalerite": ("techreborn", ["sphalerite_ore"]),
    "occultism_silver": ("occultism", ["ore_silver", "ore_silver_deepslate"]),
    "silents_silver": ("silentgear", ["silver_ore"]),
}
# Silent Gear has no 26.2 or 26.3 build, so its cinnabar silver never loads; it gets this stand in.
CINNABAR_FALLBACK = {"size": 5, "discard": 0.0, "count": 3,
                     "height": {"type": "minecraft:uniform", "min_inclusive": {"above_bottom": 0},
                                "max_inclusive": {"absolute": 96}}}
CINNABAR_SLIDER_FACTOR = 3

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
    "iceandfire":     {"display": "Ice and Fire",      "category": "ice_and_fire",
                       "licence": "LGPL-3.0",     "author": "Alexthe666, the Community Edition by IAFEnvoy"},
    "mysticalagriculture": {"display": "Mystical Agriculture", "category": "mystical_agriculture",
                       "licence": "MIT",          "author": "BlakeBr0"},
    "theurgy": {"display": "Theurgy", "category": "theurgy",
                       "licence": "CC BY-SA 4.0 (art)", "author": "Kli Kli"},
    "evilcraft": {"display": "EvilCraft", "category": "evilcraft",
                       "licence": "CC BY 4.0 (art)", "author": "rubensworks"},
    "betternether": {"display": "BetterNether", "category": "betternether",
                       "licence": "MIT", "author": "quiqueck, paulevs"},
    "denseores": {"display": "Dense Ores", "category": "dense_ores",
                       "licence": "AGPL-3.0 (art, as its Modrinth page)", "author": "NewJumperr"},
    "railcraft": {"display": "Railcraft Reborn", "category": "railcraftreborn",
                       "licence": "Railcraft Reborn License", "author": "Sm0keySa1m0n, Edivad99",
                       "notice_links": ("https://github.com/railcraft-reborn/railcraft",)},
    "bronze": {"display": "Bronze", "category": "bronze",
                       "licence": "GPL-3.0", "author": "Khazoda"},
    "oritech": {"display": "Oritech", "category": "oritech",
                       "licence": "CC-BY-4.0", "author": "Rearth"},
    "thesilverage": {"display": "The Silver Age", "category": "thesilverage",
                       "licence": "MIT", "author": "PhantomWing"},
    "theleadage": {"display": "The Lead Age", "category": "theleadage",
                       "licence": "MIT", "author": "PhantomWing"},
    "gemsandcrystals": {"display": "Gems and Crystals", "category": "gemsandcrystals",
                       "licence": "MIT", "author": "Coliwogg"},
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
    # Dripstone emerald too: Create's strata put dripstone blocks in the mountains, over the
    # emerald they swallow.
    {"name": "emerald",  "overlay": "emerald",  "source": "emerald_ore",  "base": "stone",
     "tiers": {"stone": "emerald_ore", "deepslate": "deepslate_emerald_ore"}},
    {"name": "redstone", "overlay": "redstone", "source": "redstone_ore", "base": "stone",
     "tiers": {"stone": "redstone_ore", "deepslate": "deepslate_redstone_ore"}},
    # Nether. These ADD ore - vanilla's nether features match netherrack only - so their worldgen
    # injection is config-gated in OreSideInjector. Registration and assets are unconditional.
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
    # Jade has no variant: nothing places a stone over it in the End (ametrine, below, has one).
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
    # Ametrine: an End ore (end_stone only), so its one form is the End one and no game rock takes it.
    # Its only host is Mythic Upgrades' own jade schist, laid over the ametrine its End biome placed first.
    {"name": "ametrine",   "overlay": "ametrine",   "source": "ametrine_ore",   "base": "end_stone",
     "mod": "mythicupgrades", "raw_drop": "mythicupgrades:ametrine",
     "tiers": {"end": "ametrine_ore"}},

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
    # 96-100% on the gem pixels, because the same blobs are drawn on netherrack as on stone. So the
    # overlay cannot be their key, as it is everyone else's: theirs is spelled out.
    {"name": "alexandrite", "key": "nether_alexandrite", "overlay": "alexandrite", "source": "nether_alexandrite_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_alexandrite_ore"}},
    {"name": "black_diamond", "key": "nether_black_diamond", "overlay": "black_diamond", "source": "nether_black_diamond_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_black_diamond_ore"}},
    {"name": "carnelian", "key": "nether_carnelian", "overlay": "carnelian", "source": "nether_carnelian_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_carnelian_ore"}},
    {"name": "silents_citrine", "key": "nether_silents_citrine", "overlay": "silents_citrine", "source": "nether_citrine_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_citrine_ore"}},
    {"name": "iolite", "key": "nether_iolite", "overlay": "iolite", "source": "nether_iolite_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_iolite_ore"}},
    {"name": "moldavite", "key": "nether_moldavite", "overlay": "moldavite", "source": "nether_moldavite_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_moldavite_ore"}},
    {"name": "pearl", "key": "nether_pearl", "overlay": "pearl", "source": "nether_pearl_ore", "base": "netherrack",
     "mod": "silentgems",
     "tiers": {"nether": "nether_pearl_ore"}},
    {"name": "tanzanite", "key": "nether_tanzanite", "overlay": "tanzanite", "source": "nether_tanzanite_ore", "base": "netherrack",
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
    # Ice and Fire Community Edition (mod id iceandfire, LGPL-3.0), 26.1.2 NeoForge only (2.2-beta.4).
    # The same PREFIXED ids as the older bands. The overlays are the owner's, drawn from CE's own specks;
    # the deepslate silver ore has specks of its own. Sapphire targets stone_ore_replaceables only.
    {"name": "iceandfire_sapphire", "overlay": "iceandfire_sapphire", "source": "sapphire_ore",
     "base": "stone", "mod": "iceandfire",
     "tiers": {"stone": "sapphire_ore"}},
    {"name": "iceandfire_silver", "overlay": "iceandfire_silver", "deepslate_overlay": "iceandfire_deepslate_silver",
     "source": "silver_ore", "base": "stone", "mod": "iceandfire",
     "tiers": {"stone": "silver_ore", "deepslate": "deepslate_silver_ore"}},
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
                       "dripstone": "opal_dripstone", "forbidden_arcanus_darkstone": "opal_darkstone"},
     "tiers": {"stone": "opal_ore", "deepslate": "deepslate_opal_ore"}},
    # --- Theurgy (mod id theurgy; its art is CC BY-SA 4.0): sal ammoniac, iron convention, 2 to 5 XP ---
    {"name": "sal_ammoniac", "overlay": "sal_ammoniac", "source": "sal_ammoniac_ore", "base": "stone",
     "mod": "theurgy",
     "tiers": {"stone": "sal_ammoniac_ore", "deepslate": "deepslate_sal_ammoniac_ore"}},
    # --- EvilCraft (mod id evilcraft; its images are CC BY 4.0): dark ore glows when touched and drops 1 to 5 XP, as redstone ore does; 3.0 ---
    {"name": "dark", "overlay": "dark", "source": "dark_ore", "base": "stone",
     "mod": "evilcraft",
     "tiers": {"stone": "dark_ore", "deepslate": "dark_ore_deepslate"}},
    # --- BetterNether (mod id betternether; MIT): cincinnasite, nether lapis, redstone and ruby, all in netherrack ---
    {"name": "betternether_cincinnasite", "overlay": "betternether_cincinnasite", "source": "cincinnasite_ore", "base": "netherrack",
     "mod": "betternether",
     "tiers": {"nether": "cincinnasite_ore"}},
    {"name": "betternether_nether_lapis", "overlay": "betternether_nether_lapis", "source": "nether_lapis_ore", "base": "netherrack",
     "mod": "betternether",
     "tiers": {"nether": "nether_lapis_ore"}},
    {"name": "betternether_nether_redstone", "overlay": "betternether_nether_redstone", "source": "nether_redstone_ore", "base": "netherrack",
     "mod": "betternether",
     "tiers": {"nether": "nether_redstone_ore"}},
    {"name": "betternether_nether_ruby", "overlay": "betternether_nether_ruby", "source": "nether_ruby_ore", "base": "netherrack",
     "mod": "betternether",
     "tiers": {"nether": "nether_ruby_ore"}},
    # --- Dense Ores (mod id denseores; art shipped under AGPL-3.0, its Modrinth licence): the game's ores, denser ---
    {"name": "denseores_coal", "overlay": "denseores_coal", "deepslate_overlay": "denseores_coal_deepslate", "source": "dense_coal_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_coal_ore", "deepslate": "dense_deepslate_coal_ore"}},
    {"name": "denseores_copper", "overlay": "denseores_copper", "source": "dense_copper_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_copper_ore", "deepslate": "dense_deepslate_copper_ore"}},
    {"name": "denseores_iron", "overlay": "denseores_iron", "source": "dense_iron_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_iron_ore", "deepslate": "dense_deepslate_iron_ore"}},
    {"name": "denseores_gold", "overlay": "denseores_gold", "source": "dense_gold_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_gold_ore", "deepslate": "dense_deepslate_gold_ore"}},
    {"name": "denseores_lapis", "overlay": "denseores_lapis", "source": "dense_lapis_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_lapis_ore", "deepslate": "dense_deepslate_lapis_ore"}},
    {"name": "denseores_redstone", "overlay": "denseores_redstone", "source": "dense_redstone_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_redstone_ore", "deepslate": "dense_deepslate_redstone_ore"}},
    {"name": "denseores_diamond", "overlay": "denseores_diamond", "source": "dense_diamond_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_diamond_ore", "deepslate": "dense_deepslate_diamond_ore"}},
    {"name": "denseores_emerald", "overlay": "denseores_emerald", "source": "dense_emerald_ore", "base": "stone",
     "mod": "denseores",
     "tiers": {"stone": "dense_emerald_ore", "deepslate": "dense_deepslate_emerald_ore"}},
    {"name": "denseores_nether_gold", "overlay": "denseores_nether_gold", "source": "dense_nether_gold_ore", "base": "netherrack",
     "mod": "denseores",
     "tiers": {"nether": "dense_nether_gold_ore"}},
    {"name": "denseores_nether_quartz", "overlay": "denseores_nether_quartz", "source": "dense_nether_quartz_ore", "base": "netherrack",
     "mod": "denseores",
     "tiers": {"nether": "dense_nether_quartz_ore"}},
    {"name": "denseores_ancient_nether", "overlay": "denseores_ancient_nether", "source": "ancient_nether_ore", "base": "netherrack",
     "mod": "denseores",
     "tiers": {"nether": "ancient_nether_ore"}},
    # End forms of the ores above (25 Oct 2026): End-only types, keyed apart, for the End stones
    # other mods lay. Facts per form in references/tools/ore-mod-adder/add_end_forms.py.
    {"name": "techreborn_peridot", "key": "techreborn_peridot", "overlay": "techreborn_peridot", "source": "peridot_ore", "base": "end_stone",
     "mod": "techreborn", "tiers": {"end": "peridot_ore"}},
    {"name": "sheldonite", "key": "sheldonite", "overlay": "sheldonite", "source": "sheldonite_ore", "base": "end_stone",
     "mod": "techreborn", "tiers": {"end": "sheldonite_ore"}},
    {"name": "sodalite", "key": "sodalite", "overlay": "sodalite", "source": "sodalite_ore", "base": "end_stone",
     "mod": "techreborn", "tiers": {"end": "sodalite_ore"}},
    {"name": "techreborn_tungsten", "key": "techreborn_tungsten", "overlay": "techreborn_tungsten", "source": "tungsten_ore", "base": "end_stone",
     "mod": "techreborn", "tiers": {"end": "tungsten_ore"}},
    {"name": "jade", "key": "jade", "overlay": "jade", "source": "jade_ore", "base": "end_stone",
     "mod": "mythicupgrades", "tiers": {"end": "jade_ore"}},
    {"name": "end_starrite", "key": "end_starrite", "overlay": "starrite", "source": "end_stone_starrite_ore", "base": "end_stone",
     "mod": "mythicmetals", "tiers": {"end": "end_stone_starrite_ore"}},
    # --- Railcraft Reborn (mod id railcraft, its own licence: art may be used alongside it with attribution and a link): firestone and saltpeter are disks, so no variants. Forge at 1.20.1, NeoForge at 1.21.1 and 26.1 ---
    {"name": "railcraft_lead", "overlay": "railcraft_lead", "source": "lead_ore", "base": "stone",
     "mod": "railcraft",
     "tiers": {"stone": "lead_ore", "deepslate": "deepslate_lead_ore"}},
    {"name": "railcraft_nickel", "overlay": "railcraft_nickel", "source": "nickel_ore", "base": "stone",
     "mod": "railcraft",
     "tiers": {"stone": "nickel_ore", "deepslate": "deepslate_nickel_ore"}},
    {"name": "railcraft_silver", "overlay": "railcraft_silver", "source": "silver_ore", "base": "stone",
     "mod": "railcraft",
     "tiers": {"stone": "silver_ore", "deepslate": "deepslate_silver_ore"}},
    {"name": "railcraft_sulfur", "overlay": "railcraft_sulfur", "source": "sulfur_ore", "base": "stone",
     "mod": "railcraft",
     "tiers": {"stone": "sulfur_ore", "deepslate": "deepslate_sulfur_ore"}},
    {"name": "railcraft_tin", "overlay": "railcraft_tin", "source": "tin_ore", "base": "stone",
     "mod": "railcraft",
     "tiers": {"stone": "tin_ore", "deepslate": "deepslate_tin_ore"}},
    {"name": "railcraft_zinc", "overlay": "railcraft_zinc", "source": "zinc_ore", "base": "stone",
     "mod": "railcraft",
     "tiers": {"stone": "zinc_ore", "deepslate": "deepslate_zinc_ore"}},
    # --- Bronze (mod id bronze, GPL-3.0): tin. Fabric at 1.20.1; Fabric and NeoForge at 1.21.1, 1.21.11 and 26.1 ---
    {"name": "bronze_tin", "overlay": "bronze_tin", "deepslate_overlay": "bronze_tin_deepslate", "source": "tin_ore_block", "base": "stone",
     "mod": "bronze",
     "tiers": {"stone": "tin_ore_block", "deepslate": "deepslate_tin_ore_block"}},
    # --- Oritech (mod id oritech, CC BY 4.0): nickel, platinum in deepslate and end stone; its uranium is a patch feature, so no variants. Fabric and NeoForge at 1.21.1, NeoForge at 26.1 ---
    {"name": "oritech_nickel", "overlay": "oritech_nickel", "source": "nickel_ore", "base": "stone",
     "mod": "oritech",
     "tiers": {"stone": "nickel_ore", "deepslate": "deepslate_nickel_ore"}},
    {"name": "oritech_platinum", "overlay": "oritech_platinum", "source": "deepslate_platinum_ore", "base": "deepslate",
     "mod": "oritech",
     "tiers": {"deepslate": "deepslate_platinum_ore"}},
    {"name": "oritech_end_platinum", "overlay": "oritech_end_platinum", "source": "endstone_platinum_ore", "base": "end_stone",
     "mod": "oritech",
     "tiers": {"end": "endstone_platinum_ore"}},
    # --- The Silver Age (mod id thesilverage, MIT): silver, a copy of gold ore, no XP; drawn apart in deepslate. Fabric and Forge at 1.20.1, Fabric and NeoForge from 1.21.1 ---
    {"name": "thesilverage_silver", "overlay": "thesilverage_silver", "deepslate_overlay": "thesilverage_silver_deepslate", "source": "silver_ore", "base": "stone",
     "mod": "thesilverage",
     "tiers": {"stone": "silver_ore", "deepslate": "deepslate_silver_ore"}},
    # --- The Lead Age (mod id theleadage, MIT): lead, a copy of iron ore. Fabric and Forge at 1.20.1, Fabric and NeoForge from 1.21.1 ---
    {"name": "theleadage_lead", "overlay": "theleadage_lead", "source": "lead_ore", "base": "stone",
     "mod": "theleadage",
     "tiers": {"stone": "lead_ore", "deepslate": "deepslate_lead_ore"}},
    # --- Gems and Crystals (mod id gemsandcrystals, MIT): five gems, 3 to 7 XP. Forge at 1.20.1, Fabric and NeoForge from 1.21.1 ---
    {"name": "gemsandcrystals_amethyst", "overlay": "gemsandcrystals_amethyst", "source": "amethyst_ore", "base": "stone",
     "mod": "gemsandcrystals",
     "tiers": {"stone": "amethyst_ore", "deepslate": "deepslate_amethyst_ore"}},
    {"name": "gemsandcrystals_quartz", "overlay": "gemsandcrystals_quartz", "source": "quartz_ore", "base": "stone",
     "mod": "gemsandcrystals",
     "tiers": {"stone": "quartz_ore", "deepslate": "deepslate_quartz_ore"}},
    {"name": "gemsandcrystals_ruby", "overlay": "gemsandcrystals_ruby", "source": "ruby_ore", "base": "stone",
     "mod": "gemsandcrystals",
     "tiers": {"stone": "ruby_ore", "deepslate": "deepslate_ruby_ore"}},
    {"name": "gemsandcrystals_sapphire", "overlay": "gemsandcrystals_sapphire", "source": "sapphire_ore", "base": "stone",
     "mod": "gemsandcrystals",
     "tiers": {"stone": "sapphire_ore", "deepslate": "deepslate_sapphire_ore"}},
    {"name": "gemsandcrystals_topaz", "overlay": "gemsandcrystals_topaz", "source": "topaz_ore", "base": "stone",
     "mod": "gemsandcrystals",
     "tiers": {"stone": "topaz_ore", "deepslate": "deepslate_topaz_ore"}},
]

# A translucent ore takes the colour of the rock behind it: a host with no hand-made overlay of its own gets
# one painted over its stone (placed.translucent_overlays), from the layer the pack's solver recovered.
for _ore in ORE_DEFS:
    if _ore["overlay"] == "opal":
        _ore["translucent"] = os.path.join(os.path.dirname(assetgen.POOL), "layers", "opal_translucent_layer.png")

# Every ore has a KEY, unique across the table: the id part in a stone another mod places (one of those
# takes both golds: create_scoria_nether_gold_ore) and the geology rule's key. The overlay, unless set.
# Mirrors OreType.key(). The host table is READ from HostStone.java (shared/tools/placed.py), so the
# blocks that register and the files generated here cannot drift apart; which other mods' ores each
# stone another mod places swallows is measured by the pair model (references/tools/som-grid) from the
# real jars, in modded_pairs.json.
HOST_TABLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common", "src", "main",
                          "java", "com", "chillpavz", MOD_ID, "content", "HostStone.java")
HOSTS = placed.Hosts(HOST_TABLE, ORE_DEFS, os.path.join(os.path.dirname(os.path.abspath(__file__)), "modded_pairs.json"),
                     HOST_LOOK, since=HOST_SINCE)
ORE_BY_KEY = HOSTS.ore_by_key


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
#   iceandfire          neoforge only    (Ice and Fire CE 2.2-beta.4, 26.1.2 only, CurseForge; Oct 2026)
#
# There is no forge module on this branch, so nothing is ever written to one, and no table carries
# Forge's condition key.
#
# The other six (mythicupgrades, mythicmetals, densemekanism, tfmg, things, create_new_age) have NO
# 26.1.2 build. Their variants never register here and their data is inert. They keep their earlier
# routing so the derived registration lights them up with no code change if a build appears.
#
# The mods that place a host stone route the same way, and a variant's table goes only to the loaders
# that carry its stone's mod AND its ore's (loot_modules): blockus Fabric only, forbidden_arcanus
# NeoForge only, promenade (NeoForge from 6.0.0 on 26.3) and wilderwild both (STONE_MODS).
CONDITIONAL_LOOT_MODULES_BY_MOD = {
    "minecraft": ("fabric", "neoforge"),   # deep blackstone (Terralith): the game's rock, every loader
    "blockus": ("fabric",),
    "forbidden_arcanus": ("neoforge",),
    "promenade": ("fabric", "neoforge"),
    "regions_unexplored": ("fabric", "neoforge"),   # Regions Unexplored: Fabric and NeoForge
    "wilderwild": ("fabric", "neoforge"),
    "yungscavebiomes": ('fabric', 'neoforge'),   # YUNG's Cave Biomes: Fabric and NeoForge
    "natures_spirit": ('fabric', 'neoforge'),   # Nature's Spirit: Fabric and NeoForge
    "betterend": ('fabric',),   # BetterEnd: Fabric
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
    "iceandfire": ("neoforge",),
    "theurgy": ("neoforge",),
    "evilcraft": ("neoforge",),
    "betternether": ("fabric",),
    "denseores": ("fabric", "neoforge"),
    "railcraft": ('neoforge',),
    "bronze": ('fabric', 'neoforge'),
    "oritech": ('neoforge',),
    "thesilverage": ('fabric', 'neoforge'),
    "theleadage": ('fabric', 'neoforge'),
    "gemsandcrystals": ('fabric', 'neoforge'),
}
DEFAULT_CONDITIONAL_LOOT_MODULES = ("fabric", "neoforge")


def loot_modules(gate):
    """The loader modules every mod of a variant's gate ships for."""
    modules = [m for m in DEFAULT_CONDITIONAL_LOOT_MODULES
               if m in placed.loot_modules(gate, CONDITIONAL_LOOT_MODULES_BY_MOD, DEFAULT_CONDITIONAL_LOOT_MODULES)]
    if not modules:
        sys.exit(f"no loader carries every mod of {gate}")
    return modules


# The loaders each stone mod's variants register on (ModdedPairs.shipsHere): exactly those its loot goes to.
STONE_LOADERS = {c["placed_by"]: tuple(CONDITIONAL_LOOT_MODULES_BY_MOD.get(c["placed_by"], DEFAULT_CONDITIONAL_LOOT_MODULES))
                 for c in HOSTS.placed()}


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
            # An ore name is c:ores/<name>; a key with a slash is a whole path (c:ore_rates/dense).
            rel = os.path.join("tags", kind, *(ore.split("/") if "/" in ore else ("ores", ore))) + ".json"
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
    """Every (host, host config, ore def, source form, source tier) that actually exists (placed.py)."""
    return HOSTS.variants(CINNABAR_FAMILY)


def overlay_for(ore, host_cfg, face="side"):
    return HOSTS.overlay_for(ore, host_cfg, face)


def all_overlay_keys():
    return HOSTS.overlay_keys(CINNABAR_FAMILY)

def version_key(version):
    return tuple(int(part) for part in version.split("."))


def host_exists_in(host_cfg, version):
    """Whether the host's block exists on that profile's Minecraft version (cinnabar: 26.2 up)."""
    since = host_cfg.get("since")
    return since is None or version_key(version) >= version_key(since)


def variant_name(host, ore):
    return HOSTS.name_of(host, ore)


def block_title(host, ore):
    return HOSTS.title_of(host, ore)


def generate_json():
    root = assets_dir()
    count = 0
    # Every file of these folders is written here, so one this run does not write is a variant that no
    # longer exists: cleared first, so a host or ore taken out of the tables leaves nothing behind.
    for sub in (("blockstates",), ("models", "block"), ("items",)):
        folder = os.path.join(root, *sub)
        for name in os.listdir(folder) if os.path.isdir(folder) else []:
            if name.endswith(".json"):
                os.remove(os.path.join(folder, name))
    # A translucent ore on a host with no hand-made overlay (deep blackstone) gets one painted over that
    # stone, read from the newest client jar.
    painted = placed.translucent_overlays(HOSTS, os.path.join(root, "textures", "block"),
                                          {"minecraft": os.path.expanduser(CLIENT_JARS["26.3"])})
    if painted:
        print(f"  {painted} translucent overlays painted over the stones that have none drawn")

    models = os.path.join(root, "models", "block")
    for host, host_cfg, ore, _source, _tier in variants():
        name = variant_name(host, ore)
        base = f"{MOD_ID}:block/{name}"
        overlay, overlay_end = overlay_for(ore, host_cfg), overlay_for(ore, host_cfg, "end")
        side, end, look = host_cfg["side"], host_cfg["end"], host_cfg["look"]

        # Blockstate and models, in the host's look. No render_type from 26.1: the layer is derived.
        state, block_models = look_models(name, look, side, end, overlay, overlay_end, moss=host_cfg["moss"],
                                          bottom=host_cfg["bottom"])
        for model_name, model in block_models.items():
            write_json(os.path.join(models, f"{model_name}.json"), model)
        write_json(os.path.join(root, "blockstates", f"{name}.json"), state)

        # Item model definition. The assets/<ns>/items/ DEFINITION layer arrives at 1.21.4, so
        # a block item is given its look with an items/ file pointing straight at the block
        # model. Vanilla ships no models/item/ file for a block item, so neither do we; writing
        # one here would be dead weight.
        write_json(
            os.path.join(root, "items", f"{name}.json"),
            {"model": {"type": "minecraft:model", "model": base}},
        )
        count += 1

    lang = {f"block.{MOD_ID}.{variant_name(host, ore)}": block_title(host, ore)
            for host, _cfg, ore, _s, _t in variants()}
    # Cloth Config / AutoConfig screen strings. The key shapes are fixed by AutoConfig:
    # text.autoconfig.<modid>.title / .option.<field> / .option.<field>.@Tooltip
    # A @Tooltip(count = n) needs n indexed keys instead of the bare one.
    lang.update({
        # Our own creative tabs, so several hundred variants stop burying vanilla's Natural Blocks.
        f"itemGroup.{MOD_ID}.ores": "Seamless Ores: Vanilla Stones",
        f"itemGroup.{MOD_ID}.modded_stones": "Seamless Ores: Modded Stones",
        f"text.autoconfig.{MOD_ID}.title": "Seamless Ores",

        # Category tabs. Split by dimension first, then by mod, so a Create or Mythic Upgrades
        # player finds everything about that mod in one place.
        f"text.autoconfig.{MOD_ID}.category.gemsandcrystals": "Gems and Crystals",
        f"text.autoconfig.{MOD_ID}.category.theleadage": "The Lead Age",
        f"text.autoconfig.{MOD_ID}.category.thesilverage": "The Silver Age",
        f"text.autoconfig.{MOD_ID}.category.oritech": "Oritech",
        f"text.autoconfig.{MOD_ID}.category.bronze": "Bronze",
        f"text.autoconfig.{MOD_ID}.category.railcraftreborn": "Railcraft Reborn",
        f"text.autoconfig.{MOD_ID}.category.dense_ores": "Dense Ores",
        f"text.autoconfig.{MOD_ID}.category.betternether": "BetterNether",
        f"text.autoconfig.{MOD_ID}.category.evilcraft": "EvilCraft",
        f"text.autoconfig.{MOD_ID}.category.theurgy": "Theurgy",
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
        f"text.autoconfig.{MOD_ID}.category.ice_and_fire": "Ice and Fire",
        f"text.autoconfig.{MOD_ID}.category.tech_reborn": "Tech Reborn",
        f"text.autoconfig.{MOD_ID}.category.mystical_agriculture": "Mystical Agriculture",

        f"text.autoconfig.{MOD_ID}.option.gemsAndCrystals": "Gems and Crystals: variants",
        f"text.autoconfig.{MOD_ID}.option.gemsAndCrystals.@Tooltip":
            "Generate host-matched amethyst, quartz, ruby, sapphire and topaz ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.theLeadAge": "The Lead Age: variants",
        f"text.autoconfig.{MOD_ID}.option.theLeadAge.@Tooltip":
            "Generate host-matched lead ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.theSilverAge": "The Silver Age: variants",
        f"text.autoconfig.{MOD_ID}.option.theSilverAge.@Tooltip":
            "Generate host-matched silver ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.oritech": "Oritech: variants",
        f"text.autoconfig.{MOD_ID}.option.oritech.@Tooltip":
            "Generate host-matched nickel and platinum ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.bronze": "Bronze: variants",
        f"text.autoconfig.{MOD_ID}.option.bronze.@Tooltip":
            "Generate host-matched tin ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.railcraftReborn": "Railcraft Reborn: variants",
        f"text.autoconfig.{MOD_ID}.option.railcraftReborn.@Tooltip":
            "Generate host-matched lead, nickel, silver, sulfur, tin and zinc ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.denseOres": "Dense Ores: variants",
        f"text.autoconfig.{MOD_ID}.option.denseOres.@Tooltip":
            "Generate host-matched Dense Ores ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.betterNether": "BetterNether: variants",
        f"text.autoconfig.{MOD_ID}.option.betterNether.@Tooltip":
            "Generate host-matched BetterNether ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.evilCraft": "EvilCraft: variants",
        f"text.autoconfig.{MOD_ID}.option.evilCraft.@Tooltip":
            "Generate host-matched dark ore. Does nothing unless the mod is installed.",

        f"text.autoconfig.{MOD_ID}.option.theurgy": "Theurgy: variants",
        f"text.autoconfig.{MOD_ID}.option.theurgy.@Tooltip":
            "Generate host-matched sal ammoniac ore. Does nothing unless the mod is installed.",

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
        f"text.autoconfig.{MOD_ID}.category.client": "Client",
        f"text.autoconfig.{MOD_ID}.option.showUpdateNote": "One-time update note in chat",
        f"text.autoconfig.{MOD_ID}.option.showUpdateNote.@Tooltip[0]":
            "A short note in chat, once, the first time a world is joined after an update that adds",
        f"text.autoconfig.{MOD_ID}.option.showUpdateNote.@Tooltip[1]":
            "something new. Turn it off to never see it, for example in a modpack.",
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

        f"text.autoconfig.{MOD_ID}.option.occultism": "Occultism: variants",
        f"text.autoconfig.{MOD_ID}.option.occultism.@Tooltip":
            "Generate host-matched silver ore. Does nothing unless Occultism is installed.",

        f"text.autoconfig.{MOD_ID}.option.iceAndFire": "Ice and Fire: variants",
        f"text.autoconfig.{MOD_ID}.option.iceAndFire.@Tooltip":
            "Generate host-matched sapphire and silver ore. Does nothing unless the mod is installed.",

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
    # One switch per stone another mod places, in the Modded Stones category (placed.switch_lang).
    lang.update(placed.switch_lang(HOSTS, STONE_MODS))
    assert_no_dashes(lang.items(), "lang entries")
    write_json(os.path.join(root, "lang", "en_us.json"), lang)

    # Every overlay a model names must ship: only the owner's art does, so a missing one is a
    # missing texture in game, not something to derive here. The art is in shared/textures; this band
    # keeps a copy only where its drawing differs (assetgen.texture_path).
    textures = os.path.join(root, "textures", "block")
    missing = [o for o in all_overlay_keys() if not texture_path(textures, f"{o}_overlay.png")]
    if missing:
        sys.exit(f"  !! no overlay texture for {missing}")

    # Animation metadata for the overlays that need it. It ships next to the texture, which is where
    # the vanilla sprite loader looks; nothing else has to know.
    for overlay, animation in ANIMATED_OVERLAYS.items():
        if not texture_path(textures, f"{overlay}_overlay.png"):
            print(f"  !! {overlay}_overlay.png is missing, so its animation metadata was skipped")
            continue
        write_texture_json(textures, f"{overlay}_overlay.png.mcmeta", {"animation": animation})
    print(f"  {count} blockstates, {count} block models, {count} item models, "
          f"{len(ANIMATED_OVERLAYS)} animated overlays")
    print(f"  {len(lang)} lang entries")


gate_of = placed.gate_of

# The defaults 26.2 filled in for a cooking recipe without "cookingtime"; 26.3 requires the field.
COOKING_TIME = {"minecraft:smelting": 200, "minecraft:blasting": 100, "minecraft:smoking": 100,
                "minecraft:campfire_cooking": 600}


def in_profile_format(table, recipes, name, jar_path):
    """Puts a variant's loot table and cooking recipes in the format of the profile being written.

    A mod with no build for a profile is read from an older jar standing in for it (see PROFILES), and
    that jar speaks its own game's format. 26.3 renamed what we copy: a loot entry's "conditions" list
    became one "condition", and a cooking recipe's "cookingtime" lost its default. 26.3 SKIPS the old
    key without a word, so a Silk Touch child without its condition always wins and the variant drops
    itself; and it REJECTS a recipe without cookingtime, so the variant cannot be smelted. Both shipped
    in 6.0.1. Our tables only ever carry the Silk Touch condition (every other drop defers to the
    source's own table), so that is the one spelling converted; anything else stops the run."""
    if version_key(CURRENT_PROFILE) < (26, 3):
        return

    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        if "functions" in node:
            sys.exit(f"  !! {name} ({CURRENT_PROFILE}): a loot table copied from {os.path.basename(jar_path)} "
                     f"carries \"functions\", which 26.3 calls \"modifier\" with a new shape; not converted")
        if "conditions" in node:
            conditions = node.pop("conditions")
            if not (len(conditions) == 1 and conditions[0].get("condition") == "minecraft:match_tool"
                    and "silk_touch" in json.dumps(conditions[0])):
                sys.exit(f"  !! {name} ({CURRENT_PROFILE}): loot conditions {conditions} from "
                         f"{os.path.basename(jar_path)} are not the one Silk Touch test; not converted")
            node["condition"] = "minecraft:tool/can_silk_touch"
        for value in node.values():
            visit(value)

    visit(table.get("pools", []))
    for recipe in recipes.values():
        if "cookingtime" not in recipe:
            recipe["cookingtime"] = COOKING_TIME[recipe["type"]]


def check_overlay_formats():
    """Stops the run if a written loot table or recipe is in a format its Minecraft version ignores or
    rejects. Every one of these fails in silence or with a log line nobody reads, never at build time."""
    bad = []
    for module in ("common", "fabric", "neoforge"):
        resources = os.path.join(repo_root(), module, "src", "main", "resources")
        for version, profile in PROFILES.items():
            root = os.path.join(resources, profile["overlay"], "data", MOD_ID)
            for dirpath, _dirs, files in os.walk(root):
                for file in files:
                    path = os.path.join(dirpath, file)
                    text = open(path, encoding="utf-8").read()
                    data = json.loads(text)
                    where = os.path.relpath(path, repo_root())
                    if (os.sep + "recipe" + os.sep) in path:
                        ingredient = data.get("ingredient")
                        if isinstance(ingredient, dict) or (isinstance(ingredient, list)
                                                            and any(isinstance(i, dict) for i in ingredient)):
                            bad.append(f"{where}: ingredient object (1.21.2 on reads only an id, a tag or a list)")
                        if version_key(version) >= (26, 3) and data.get("type") in COOKING_TIME                                 and "cookingtime" not in data:
                            bad.append(f"{where}: no cookingtime (required from 26.3)")
                    elif version_key(version) >= (26, 3) and re.search(r'"(conditions|functions)"', text):
                        bad.append(f"{where}: \"conditions\" or \"functions\" (26.3 reads \"condition\" and \"modifier\")")
    if bad:
        sys.exit(f"  !! {len(bad)} data files in a format their version does not read, first: " + "; ".join(bad[:5]))
    print("  overlay formats checked: every loot table and recipe in its version's format")


def generate_data():
    """Loot tables and tags. Loot is TRANSFORMED from vanilla's own tables, never reconstructed."""

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
    entry_mod = {}      # a modded tag entry's id -> the mod that variant belongs to
    copied_tags = {}    # (kind, tag) -> entries: every other tag the source ore is in (parity.py)
    tags_of_sources = all_source_tags()

    with zipfile.ZipFile(CLIENT_JAR) as jar:

        # Read the real vanilla tool tags once, then mirror membership per variant. NOT hardcoded
        # per ore, because it is not uniform by ore: overworld gold_ore is in needs_iron_tool but
        # nether_gold_ore is in none of them (wooden pickaxe), and coal is in none either. A modded
        # ore's tier comes from ITS jar (read_mod_tags): zinc is needs_iron_tool via Create's own data,
        # and hardcoding would have guessed stone-tool wrong.
        vanilla = jar_tags(jar, "block")
        vanilla_tool_tags = {tag: vanilla.get(f"minecraft:{tag}", set()) for tag in TOOL_TAGS}
        for host, host_cfg, ore, source, source_tier in variants():
                name = variant_name(host, ore)
                our_id = f"{MOD_ID}:{name}"
                mod = ore.get("mod")
                source_id = f"{mod}:{source}" if mod else f"minecraft:{source}"
                gate = gate_of(host_cfg, ore)

                # --- loot table -------------------------------------------------------------
                # TRANSFORMED FROM THE ORE'S OWN TABLE, never written by hand: vanilla's from the client
                # jar, a mod's from that mod's jar. Ore loot is not uniform (copper 2-5, lapis 4-9,
                # redstone uniform_bonus_count; Mythic Metals' set_count 1-2 plus rare secondary drops,
                # Dense Mekanism and Powah set_count), so copying the real table is the only way to
                # guarantee parity. Hard error rather than a fallback if the jar is missing: silently
                # shipping a table with the wrong yield is exactly the class of bug this project keeps
                # finding, and a generator run is a dev-time step where failing loudly is free.
                jar_path = CLIENT_JAR if mod is None else MOD_JARS.get(mod)
                if not jar_path or not os.path.exists(jar_path):
                    raise SystemExit(f"  !! cannot generate the loot table for {name}: the {mod} jar is "
                                     f"required to transform its own table and was not found at {jar_path}."
                                     f" Fix its path in PROFILES or COMMON_JARS.")
                loot_path = f"data/{source_id.split(':')[0]}/loot_table/blocks/{source}.json"
                with zipfile.ZipFile(jar_path) as source_jar:
                    try:
                        with source_jar.open(loot_path) as handle:
                            table = json.load(handle)
                    except KeyError:
                        raise SystemExit(f"  !! {os.path.basename(jar_path)} has no {loot_path} (needed by {name})")
                # The source ore's own smelting and blasting recipes, taking the variant: written beside
                # its loot table, under the same conditions, so it exists exactly where the variant does.
                recipes = parity.cooking_copies(jar_path, source_id, our_id, name, item_strings=True)
                silk_touch_to(table, source_id, our_id, name, CURRENT_PROFILE)
                # Non-Silk-Touch drops run the source ore's own table, so pack edits to it carry over.
                table = defer_to_source(table, source_id, our_id, "value")
                table["random_sequence"] = f"{MOD_ID}:blocks/{name}"
                in_profile_format(table, recipes, name, jar_path)

                if not host_exists_in(host_cfg, CURRENT_PROFILE):
                    pass    # no such block on this version: a table naming its item would not load
                elif gate:
                    # From 26.3 loot tables are a datapack REGISTRY, and a table naming an item that is
                    # not registered fails registry loading: the world does not open. A variant exists
                    # only with the mods in its gate, so its table carries each loader's condition for
                    # exactly that, and each loader ignores the other's key. NEVER neoforge:item_exists:
                    # removed at 26.2. Written only to the loaders every mod of the gate ships for.
                    conditions = {
                        "fabric:load_conditions": [{"condition": "fabric:registry_contains",
                                                    "registry": "minecraft:block", "values": [our_id]}],
                        "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": m} for m in gate],
                    }
                    for module in loot_modules(gate):
                        write_json(os.path.join(conditional_data_dir(module, MOD_ID),
                                                "loot_table", "blocks", f"{name}.json"), {**conditions, **table})
                        for stem, recipe in recipes.items():
                            write_json(os.path.join(conditional_data_dir(module, MOD_ID), "recipe", f"{stem}.json"),
                                       {**conditions, **recipe})
                else:
                    write_json(os.path.join(ours, "loot_table", "blocks", f"{name}.json"), table)
                    for stem, recipe in recipes.items():
                        write_json(os.path.join(ours, "recipe", f"{stem}.json"), recipe)

                # --- tags -------------------------------------------------------------------
                # A variant that needs a mod, or a block only some versions have, may be absent, so its
                # tag entries are optional objects: a plain string would log a tag error without it.
                entry = {"id": our_id, "required": False} if gate or host_cfg.get("since") else our_id
                if mod:
                    entry_mod[our_id] = mod
                mineable.append(entry)
                source_tags = modded_tool_tags if mod else vanilla_tool_tags
                for tag, members in source_tags.items():
                    if source_id in members:
                        tool_tags.setdefault(tag, []).append(entry)
                # A mod's own tier tag can list the game's ores too (Silent Gear puts gold and redstone ore in
                # silentgear:needs_copper_tool), so it applies to every variant, as it does to the ore it stands in for.
                for tag_key, members in mod_own_tool_tags.items():
                    if source_id in members:
                        foreign_tool_tags.setdefault(tag_key, []).append(entry)
                conv_block.setdefault(ore["name"], []).append(entry)
                conv_item.setdefault(ore["name"], []).append(entry)
                # Every other tag the source ore is in, as reviewed in source_tags.json: piglins guard a
                # gold variant, the drills of Tech Reborn and Mythic Metals mine it, and from 26.3 it
                # blocks motion and fluids and suffocates (tags, no longer block properties).
                parity.add_tag_entries(copied_tags, tags_of_sources.tags_for(source_id), entry)
                # TAG PARITY with the ore we stand in for: every c:ores/<x> tag its counterpart is in,
                # read from that mod's own jar. The name-keyed tag above stays, so nothing a published
                # release put into a tag is ever taken back out, but on its own it was WRONG for every
                # prefixed name: energized_tin sat in c:ores/energized_tin and never c:ores/tin, so a
                # machine matching c:ores/tin refused a silk-touched variant. It also misses ores the
                # source mod lists twice (Extreme Reactors' yellorite is c:ores/uranium as well).
                if mod:
                    for kind, target in (("block", conv_block), ("item", conv_item)):
                        for tag_name in sorted(mod_ore_tags[kind].get(source_id, ())):
                            if tag_name != ore["name"]:
                                target.setdefault(tag_name, []).append(entry)
                # c:ores_in_ground/<stone|deepslate|netherrack> - keyed on the form we stand in for,
                # so consumers treat a variant exactly like its counterpart.
                # Cinnabar has no ground tag of its own, and is neither stone nor netherrack.
                if host_cfg["tier"] != "cinnabar":
                    # An End form has no ground tag: the convention names only stone, deepslate and netherrack.
                    ground = {"stone": "stone", "deepslate": "deepslate", "nether": "netherrack"}.get(source_tier)
                    if ground:
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

    # Into the shared pool: every band's models read the overlays from there.
    out_dir = assetgen.POOL
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
    # source mod id (None = vanilla) -> list of (ore def, {host: block id}), in ORE_DEFS order. The
    # game's own rock only; the stones other mods place have a section of their own.
    grouped = {}
    for host, host_cfg, ore, _source, _tier in variants():
        if host_cfg["placed_by"]:
            continue
        entry = grouped.setdefault(ore.get("mod"), {}).setdefault(id(ore), (ore, {}))
        entry[1][host] = variant_name(host, ore)

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
        for _host, cfg, ore, _s, _t in variants():
            if not cfg["placed_by"] and host_exists_in(cfg, version):
                counts[ore.get("mod")] = counts.get(ore.get("mod"), 0) + 1
        per_version[version] = counts

    lines = [
        "A variant is registered only when the mod that owns its ore is installed, so how many of",
        "these (in the game's own rock) you can actually see depends on which mods have a build for",
        "your loader at your Minecraft version:",
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


def _modded_stone_list():
    return placed.modded_stone_list(HOSTS, STONE_MODS, MODS, CINNABAR_FAMILY)

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
        "modded-stone-list": _modded_stone_list(),
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
    """A file written once per Minecraft version: a loot table, or a cooking recipe beside it."""
    return (os.sep + "loot_table" + os.sep) in path or (os.sep + MOD_ID + os.sep + "recipe" + os.sep) in path


def scaled_count(count, factor):
    """A placement count provider times factor: a constant, or a uniform range scaled at both ends."""
    if isinstance(count, int):
        return count * factor
    if isinstance(count, dict) and count.get("type") == "minecraft:uniform":
        return {**count, "min_inclusive": count["min_inclusive"] * factor,
                "max_inclusive": count["max_inclusive"] * factor}
    sys.exit(f"  !! cannot scale count provider {count}: add it to scaled_count")


def read_source(version, namespace, path):
    """(feature size, discard chance, placement list) of one source placed feature, or None."""
    jar_path = os.path.expanduser(CLIENT_JARS[version]) if namespace == "minecraft" else \
        {**COMMON_JARS, **PROFILES[version]["jars"]}.get(namespace)
    if not jar_path or not os.path.exists(jar_path):
        return None
    with zipfile.ZipFile(jar_path) as jar:
        try:
            source = json.loads(jar.read(f"data/{namespace}/worldgen/placed_feature/{path}.json"))
        except KeyError:
            return None
        feature_ns, feature_path = source["feature"].split(":", 1)
        folder = "feature" if version_key(version) >= version_key("26.3") else "configured_feature"
        try:
            feature = json.loads(jar.read(f"data/{feature_ns}/worldgen/{folder}/{feature_path}.json"))
        except KeyError:
            return None     # a jar built for another version (Silent Gear: 26.1 only)
    config = feature.get("config", feature)
    return config["size"], config.get("discard_chance_on_air_exposure", 0.0), source["placement"]


def generate_cinnabar_worldgen():
    """Cinnabar veins that mirror each source ore's own features, Sulfur Caves only, 26.2 and 26.3.

    Every file goes in the mc26.2 and mc26.3 overlays, each read from that version's jars, so 26.1,
    which has no cinnabar and no Sulfur Caves, never reads one: a worldgen file naming an absent block
    is a hard crash, not a skip. A modded variant's files carry that mod's load conditions as well.
    NeoForge attaches them with a biome modifier each; Fabric in code, from CinnabarVeins.
    """
    common = os.path.join(repo_root(), "common", "src", "main", "resources")
    neoforge = os.path.join(repo_root(), "neoforge", "src", "main", "resources")
    overlays = {"mc26.2": ("26.2", "configured_feature"), "mc26.3": ("26.3", "feature")}
    for overlay in overlays:
        for root, sub in ((common, "worldgen"), (neoforge, "neoforge")):
            folder = os.path.join(root, overlay, "data", MOD_ID, sub)
            if os.path.isdir(folder):
                for dirpath, _dirs, files in os.walk(folder):
                    for f in files:
                        if f.startswith("cinnabar_"):
                            os.remove(os.path.join(dirpath, f))
    count = 0
    report = []
    for host, host_cfg, ore, _source, _tier in variants():
        if host_cfg["tier"] != "cinnabar":
            continue
        block = f"{MOD_ID}:{variant_name(host, ore)}"
        mod = ore.get("mod")
        conditions = {}
        if mod:
            conditions = {
                "fabric:load_conditions": [{"condition": "fabric:registry_contains",
                                            "registry": "minecraft:block", "values": [block]}],
                "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": mod}],
            }
        target = {"predicate_type": "minecraft:block_match", "block": "minecraft:cinnabar"}
        namespace, sources = CINNABAR_SOURCES[ore["name"]]
        for overlay, (version, kind) in overlays.items():
            for source in sources:
                key = f"cinnabar_{ore['name']}_{source}"
                found = read_source(version, namespace, source)
                if found is None:
                    if mod is None:
                        sys.exit(f"  !! {namespace}:{source} not found in the {version} jar")
                    fb = CINNABAR_FALLBACK
                    size, discard = fb["size"], fb["discard"]
                    placement = [{"type": "minecraft:count", "count": fb["count"]},
                                 {"type": "minecraft:in_square"},
                                 {"type": "minecraft:height_range", "height": fb["height"]},
                                 {"type": "minecraft:biome"}]
                else:
                    size, discard, placement = found
                placement = [dict(p) for p in placement]
                counted = False
                for p in placement:
                    if p.get("type") == "minecraft:count":
                        p["count"] = scaled_count(p["count"], CINNABAR_SLIDER_FACTOR)
                        counted = True
                if not counted:
                    sys.exit(f"  !! {namespace}:{source} has no count modifier to scale")
                if not any(p.get("type") == "minecraft:biome" for p in placement):
                    placement.append({"type": "minecraft:biome"})
                if overlay == "mc26.3":
                    report.append(f"{key}: size {size}, discard {discard}, "
                                  + ", ".join(json.dumps(p.get("count", p.get("height")))
                                              for p in placement if p["type"] in ("minecraft:count", "minecraft:height_range")))
                feature = ({"type": f"{MOD_ID}:cinnabar_ore",
                            "config": {"size": size, "discard_chance_on_air_exposure": discard,
                                       "targets": [{"target": target, "state": {"Name": block}}]}}
                           if kind == "configured_feature" else
                           {"type": f"{MOD_ID}:cinnabar_ore", "size": size,
                            "discard_chance_on_air_exposure": discard,
                            "targets": [{"target": target, "state": block}]})
                data = os.path.join(common, overlay, "data", MOD_ID, "worldgen")
                write_json(os.path.join(data, kind, f"{key}.json"), {**feature, **conditions})
                write_json(os.path.join(data, "placed_feature", f"{key}.json"),
                           {"feature": f"{MOD_ID}:{key}", "placement": placement, **conditions})
                modifier = {"type": "neoforge:add_features", "biomes": "minecraft:sulfur_caves",
                            "features": f"{MOD_ID}:{key}", "step": "underground_ores"}
                if mod:
                    modifier["neoforge:conditions"] = conditions["neoforge:conditions"]
                write_json(os.path.join(neoforge, overlay, "data", MOD_ID, "neoforge", "biome_modifier",
                                        f"{key}.json"), modifier)
                count += 1
    print(f"  cinnabar: {count} mirrored veins over mc26.2 and mc26.3, Sulfur Caves only")
    for line in report:
        print("    " + line)


def generate_versioned_data():
    """Runs the data step once per profile and routes what it wrote.

    Loot tables go into that version's overlay folder, in whichever module the run put them (common
    for vanilla ores, fabric / neoforge for a mod's conditional tables). Everything else must come out
    the same for every version, because it goes in the base and every version reads it; the run stops
    if it does not, rather than let one version's tags silently win.
    """
    runs = {}
    for version in PROFILES:
        use_profile(version)
        print(f"  [{version}] client {os.path.basename(CLIENT_JAR)}")
        assetgen.CAPTURE = {}
        try:
            generate_data()
        finally:
            runs[version], assetgen.CAPTURE = assetgen.CAPTURE, None
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
            for tree in ("loot_table", "recipe"):
                loot = os.path.join(resources, folder, "data", MOD_ID, tree)
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
    check_overlay_formats()


def generate_java():
    """The Java that is data: the measured modded pairs, the geology tables, and the config switches.

    ModdedPairs from modded_pairs.json; shared/java's OreGeology from geology.py, the rule itself; and in
    SeamlessOresConfigData (cloth-config/java, compiled by both loaders) a switch per stone another mod
    places (the game's own rock has hand-written ones, with their own wording) and the push of every
    host's switch.
    """
    config = os.path.join(repo_root(), "cloth-config", "java", "com", "chillpavz", MOD_ID, "config",
                          "SeamlessOresConfigData.java")
    cases = placed.write_java(HOSTS, os.path.dirname(HOST_TABLE), config, STONE_LOADERS)
    print(f"  Java: modded pairs for {cases} stones, the shared geology rule, {len(HOSTS)} host switches")


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
    # Ids an earlier release registered and this one no longer builds: placeholders drawn as their stone.
    print(f"  retired ids: {retired.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), "retired_ids.json"), HOSTS, assets_dir(), resources_dir(), item_definitions=True)} placeholders")
    # Every variant's id for the Java side, and the shipped ids 6.0.0 renamed (aliased on load).
    print(f"  renamed ids: {renamed.write(HOSTS, list(variants()), os.path.join(os.path.dirname(os.path.abspath(__file__)), "retired_ids.json"), resources_dir())} aliased")
    print("Updating README...")
    generate_readme()
    print(f"  THIRD_PARTY_ART.txt: {assetgen.write_art_notice(os.path.join(resources_dir(), 'THIRD_PARTY_ART.txt'), ORE_DEFS, MODS)} mods")

    print("Generating the Java tables...")
    generate_java()

    if args.textures:
        print("Extracting overlay textures...")
        generate_textures()
    else:
        print("Skipped textures (pass --textures to regenerate; it overwrites hand edits).")


if __name__ == "__main__":
    main()
