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

# Every third-party jar we read, keyed by the mod id used in the ORES table below. A missing jar is
# a warning rather than an error: the JSON still generates, only the texture step is skipped.
MOD_JARS = {"create": CREATE_JAR, "mythicupgrades": MYTHIC_UPGRADES_JAR}

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
CONDITIONAL_LOOT_MODULES = ("fabric", "neoforge")


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
            vanilla = ore["tiers"].get(host_cfg["tier"])
            if vanilla is not None:
                yield host, host_cfg, ore, vanilla


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
                        "overlay": f"{MOD_ID}:block/{ore['overlay']}_overlay",
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
        f"text.autoconfig.{MOD_ID}.title": "Seamless Ores",

        # Category tabs. Split by dimension first, then by mod, so a Create or Mythic Upgrades
        # player finds everything about that mod in one place.
        f"text.autoconfig.{MOD_ID}.category.overworld": "Overworld",
        f"text.autoconfig.{MOD_ID}.category.nether": "Nether",
        f"text.autoconfig.{MOD_ID}.category.create": "Create",
        f"text.autoconfig.{MOD_ID}.category.mythic_upgrades": "Mythic Upgrades",

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
    })
    write_json(os.path.join(root, "lang", "en_us.json"), lang)

    print(f"  {count} blockstates, {count} block models, {count} item models")
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
                    # Third-party ore: build OUR OWN table in the vanilla iron_ore shape (verified
                    # identical to Create's own zinc table) rather than transforming their file.
                    # Both loaders' conditions keep it inert when the mod is absent; each loader
                    # ignores the other's key. NEVER neoforge:item_exists - removed at 26.2.
                    table = {
                        "fabric:load_conditions": [
                            {"condition": "fabric:registry_contains",
                             "registry": "minecraft:item", "values": [ore["raw_drop"]]}
                        ],
                        "neoforge:conditions": [
                            {"type": "neoforge:mod_loaded", "modid": mod}
                        ],
                        # Classic Forge is SINGULAR and takes ONE object. Forge honours it on
                        # datapack registries, which is what a loot table is from 1.21 onward.
                        FORGE_CONDITION_KEY: {"type": "forge:mod_loaded", "modid": mod},
                        "type": "minecraft:block",
                        "pools": [{
                            "rolls": 1.0,
                            "entries": [{
                                "type": "minecraft:alternatives",
                                "children": [
                                    {"type": "minecraft:item",
                                     "conditions": [{
                                         "condition": "minecraft:match_tool",
                                         "predicate": {"predicates": {"minecraft:enchantments": [
                                             {"enchantments": "minecraft:silk_touch",
                                              "levels": {"min": 1}}]}}
                                     }],
                                     "name": our_id},
                                    {"type": "minecraft:item",
                                     "functions": [
                                         {"enchantment": "minecraft:fortune",
                                          "formula": "minecraft:ore_drops",
                                          "function": "minecraft:apply_bonus"},
                                         {"function": "minecraft:explosion_decay"}
                                     ],
                                     "name": ore["raw_drop"]}
                                ]
                            }]
                        }],
                        "random_sequence": f"{MOD_ID}:blocks/{name}",
                    }

                if mod:
                    # Conditional table: goes to the loaders that can host that mod, not to common.
                    for module in CONDITIONAL_LOOT_MODULES:
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

    if args.textures:
        print("Extracting overlay textures...")
        generate_textures()
    else:
        print("Skipped textures (pass --textures to regenerate; it overwrites hand edits).")


if __name__ == "__main__":
    main()
