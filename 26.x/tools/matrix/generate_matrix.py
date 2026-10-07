#!/usr/bin/env python3
"""
Generates the Matrix ores: Seamless Ores' variants in the stones other mods add. Run by
tools/generate_assets.py after everything else, never on its own: the lang file and several tag files
are shared with the rest of the mod, and this adds to them rather than writing them.

Writes, from the host table in common/.../matrix/content/HostStone.java and tools/matrix/modded_pairs.json:
blockstates, two-layer block models, item model definitions, lang entries, the one overlay Seamless Ores
does not already ship, loot tables, tags, the generated Java (the modded OreKind constants, ModdedPairs,
MatrixGeology, the Modded Stones switches in both loaders' SeamlessOresConfigData) and the README list.

The host table is READ from HostStone.java, so the blocks that register and the files generated here
cannot drift apart. The vanilla ores and zinc are written in that table by hand; every other ore mod's
pairs come from modded_pairs.json, which the pair model writes from the real jars. The fixed geology
rule (geology.py) then removes the pairs that never form; Java reads the same rule from MatrixGeology,
which is generated here from it.

Dripstone is a Seamless Ores host in its own right, so the Matrix dripstone pairs are Seamless Ores'
own dripstone blocks: nothing is generated for them here.

Textures
--------
Only overlays ship, the owner's own art, shared with Seamless Ores and Seamless Glowing Ores. Every
ore's overlay is already in Seamless Ores' textures under its key; only translucent opal needs one
precomposited per host (opal_darkstone). Every host stone is referenced by its id and none of its
pixels ship: the stone's mod draws it.

Loot
----
Transformed from the ore's own tables, never written by hand: the silk-touch branch drops our block,
everything else is the ore's. One set per era, because the format changed at 26.3, each in a pack
overlay folder that pack.mcmeta enables by data format, so one jar serves every 26.x version:
  mc26.3   from the 26.3 client jar; silk touch is "condition": "minecraft:tool/can_silk_touch".
  era261   from the 26.1.2 client jar (it spells out defaults 26.2 leaves implicit, and loads on
           both); silk touch is a minecraft:match_tool condition.
  mc26.1, mc26.2   a table an ore mod changed between its 26.1.2 and 26.2 builds, one per version.
"""

import json
import os
import re
import shutil
import sys
import zipfile

import geology

MOD_ID = "seamlessores"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # the 26.x folder
SEAMLESS_ORES = os.path.dirname(os.path.dirname(ROOT))  # the Seamless Ores project folder
COMMON = os.path.join(ROOT, "common", "src", "main", "resources")
JAVA = os.path.join(ROOT, "common", "src", "main", "java", "com", "chillpavz", MOD_ID, "matrix")
CONTENT_JAVA = os.path.join(JAVA, "content")
HOST_TABLE = os.path.join(CONTENT_JAVA, "HostStone.java")
CONFIG_DATA = [os.path.join(ROOT, loader, "src", "main", "java", "com", "chillpavz", MOD_ID, "config",
                            "SeamlessOresConfigData.java") for loader in ("fabric", "neoforge")]
ARTIFACTS = os.path.expanduser("~/.gradle/caches/neoformruntime/artifacts")
JARS = os.path.join(SEAMLESS_ORES, "references", "jars")
# era -> the client jar its loot is read from, and the pack overlay folder it goes to
ERAS = {"263": os.path.join(ARTIFACTS, "minecraft_26.3_client.jar"),
        "261": os.path.join(ARTIFACTS, "minecraft_26.1.2_client.jar")}
ERA_FOLDERS = {"263": "mc26.3", "261": "era261"}
TEXTURES = os.path.join(COMMON, "assets", MOD_ID, "textures", "block")
MODDED_PAIRS = os.path.join(HERE, "modded_pairs.json")
FABRIC_PACKS = os.path.join(ROOT, "fabric", "src", "main", "resources", "resourcepacks")
NEOFORGE_DATA = os.path.join(ROOT, "neoforge", "src", "main", "resources", "data")
README = os.path.join(ROOT, "README.md")

# The host Seamless Ores generates itself.
BORROWED = {"minecraft:dripstone_block"}

# Each ore mod's jar per era, in references/jars: loot tables, tool tiers and c:ores tags come from it.
# era261 serves 26.1.x and 26.2 and reads a 26.1.2 jar where the mod has one (the format 26.2 also
# loads); a mod that exists only at 26.2 is read from its 26.2 jar. No 263 entry: no 26.3 release.
# A "262" entry is the mod's 26.2 jar where it also has a 26.1.2 one: a table that differs between the
# two goes to the mc26.1 and mc26.2 overlays instead of era261, so each version drops what its own mod does.
MOD_JARS = {
    "create": {"261": "26.1.2-create-fly-26.1.2-6.0.9-4.jar"},
    "energizedpower": {"261": "26.1.2-energizedpower-3.0.0+26.1.x-neoforge.jar",
                       "262": "energizedpower-3.0.0+26.2.x-neoforge.jar",
                       "263": "energizedpower-3.0.1+26.3.x-neoforge.jar"},
    "mysticalagriculture": {"261": "MysticalAgriculture-26.1.2-9.0.9.jar"},
    "mythicmetals": {"261": "26.1.2-mythicmetals-0.26.0+26.1.2.jar"},
    "mythicupgrades": {"261": "mythicupgrades-fabric-26.2-5.1.1.jar", "263": "mythicupgrades-fabric-26.3-5.1.1.jar"},
    "occultism": {"261": "occultism-26.1.2-neoforge-1.251.0.jar", "262": "occultism-26.2-neoforge-1.253.1.jar",
                  "263": "occultism-26.3-neoforge-1.256.0.jar"},
    "powah": {"261": "26.1.2-Powah-7.0.4-alpha.jar"},
    "silentgear": {"261": "silent-gear-26.1.2-neoforge-4.2.2.jar"},
    "silentgems": {"261": "silentgems-26.1.2-neoforge-5.1.4.jar"},
    "techreborn": {"261": "26.1.x-TechReborn-6.0.5.jar", "262": "26.2-TechReborn-6.1.1.jar",
                   "263": "26.3-TechReborn-6.2.0.jar"},
}
# A translucent ore (Silent's Gems' opal) cannot share one overlay: ours render cutout, so each host
# takes one precomposited onto that rock, made by the pack's solve_translucent_ore.py.
OVERLAYS = os.environ.get("OVERLAYS", os.path.join(SEAMLESS_ORES, "seamless-glowing-ores", "assets", "overlays"))
HOST_OVERLAYS = {("opal", "forbidden_arcanus:darkstone"):
                 ("opal_darkstone", "silent gems/opal_extracted/darkstone_opal_overlay.png")}

# Every ore kind, in OreKind order. mod: the ore's own mod (None for vanilla); forms: the ore blocks,
# stone form first; tag: the c:ores/<tag> it belongs in; name: how it reads in a block name.
# The modded ones follow from modded_pairs.json, in its order, which is the OreKind order.
ORES = {
    "coal": {}, "iron": {}, "copper": {}, "gold": {}, "redstone": {}, "emerald": {},
    "lapis": {"name": "Lapis Lazuli"}, "diamond": {},
    "zinc": {"mod": "create", "forms": ["create:zinc_ore", "create:deepslate_zinc_ore"]},
    "nether_gold": {"forms": ["minecraft:nether_gold_ore"], "tag": "gold"},
    "quartz": {"forms": ["minecraft:nether_quartz_ore"], "name": "Nether Quartz"},
}
# Words that do not title-case into the right name.
WORDS = {"techreborn": "Tech Reborn", "silents": "Silent's"}
MODDED = json.load(open(MODDED_PAIRS, encoding="utf-8"))
for _ore, _kind in MODDED["kinds"].items():
    if _ore in ORES:
        sys.exit(f"{_ore}: a modded kind reuses a hand-written ore's id")
    ORES[_ore] = {"mod": _kind["mod"], "forms": _kind["forms"], "kind": _kind,
                  "name": " ".join(WORDS.get(w, w.capitalize()) for w in _ore.split("_"))}
for _ore, _info in ORES.items():
    _info.setdefault("mod", None)
    _info.setdefault("forms", [f"minecraft:{_ore}_ore", f"minecraft:deepslate_{_ore}_ore"])
    _info.setdefault("tag", _ore)
    _info.setdefault("name", " ".join(w.capitalize() for w in _ore.split("_")))

TOOL_TAGS = ["needs_stone_tool", "needs_iron_tool", "needs_diamond_tool"]
FACES = ["down", "up", "north", "south", "west", "east"]

# Display names of the mods that place the hosts, for the config screen and the README.
MOD_NAMES = {"blockus": "Blockus", "create": "Create", "forbidden_arcanus": "Forbidden and Arcanus",
             "mythicupgrades": "Mythic Upgrades", "promenade": "Promenade", "wilderwild": "Wilder Wild"}
# Where each of those mods exists at 26.x, measured with references/tools/som-grid/availability.py.
MOD_BANDS = {"blockus": "Fabric, 26.1.x to 26.3", "create": "Create Fly, Fabric, 26.1.2 and 26.2",
             "forbidden_arcanus": "NeoForge, 26.1.2", "mythicupgrades": "Fabric and NeoForge, 26.2 and 26.3",
             "promenade": "Fabric, 26.1.x and 26.2",
             "wilderwild": "Fabric 26.1.x to 26.3, NeoForge 26.2 and 26.3"}
ORE_MOD_NAMES = {"create": "Create", "energizedpower": "Energized Power", "mysticalagriculture": "Mystical Agriculture",
                 "mythicmetals": "Mythic Metals", "mythicupgrades": "Mythic Upgrades", "occultism": "Occultism",
                 "powah": "Powah", "silentgear": "Silent Gear", "silentgems": "Silent's Gems",
                 "techreborn": "Tech Reborn"}

# How each host is drawn, read from the stone mod's own blockstate. A host with several looks must be
# mirrored exactly, or its ore is the one tile that never varies.
#   single:          one texture.
#   mirrored_turned: Wilder Wild gabbro, four random models: plain, mirrored, and each turned 180.
#   textures4:       Create's natural stones, four random models, each its own texture (<prefix>0 to 3).
HOST_LOOK = {
    "blockus:limestone": ("blockus:block/limestone", "single"),
    "blockus:marble": ("blockus:block/marble", "single"),
    "blockus:bluestone": ("blockus:block/bluestone", "single"),
    "blockus:viridite": ("blockus:block/viridite", "single"),
    "create:asurine": ("create:block/palettes/stone_types/natural/asurine_", "textures4"),
    "create:crimsite": ("create:block/palettes/stone_types/natural/crimsite_", "textures4"),
    "create:limestone": ("create:block/palettes/stone_types/limestone", "single"),
    "create:ochrum": ("create:block/palettes/stone_types/natural/ochrum_", "textures4"),
    "create:scorchia": ("create:block/palettes/stone_types/scorchia", "single"),
    "create:scoria": ("create:block/palettes/stone_types/scoria", "single"),
    "create:veridium": ("create:block/palettes/stone_types/natural/veridium_", "textures4"),
    "minecraft:calcite": ("minecraft:block/calcite", "single"),
    "minecraft:dripstone_block": ("minecraft:block/dripstone_block", "single"),
    "minecraft:smooth_basalt": ("minecraft:block/smooth_basalt", "single"),
    "forbidden_arcanus:darkstone": ("forbidden_arcanus:block/darkstone", "single"),
    "mythicupgrades:aquamarine_schist": ("mythicupgrades:block/aquamarine_schist", "single"),
    "mythicupgrades:citrine_schist": ("mythicupgrades:block/citrine_schist", "single"),
    "mythicupgrades:peridot_schist": ("mythicupgrades:block/peridot_schist", "single"),
    "mythicupgrades:topaz_schist": ("mythicupgrades:block/topaz_schist", "single"),
    "mythicupgrades:sapphire_schist": ("mythicupgrades:block/sapphire_schist", "single"),
    "promenade:asphalt": ("promenade:block/asphalt", "single"),
    "promenade:blunite": ("promenade:block/blunite", "single"),
    "wilderwild:gabbro": ("wilderwild:block/gabbro", "mirrored_turned"),
}

# A stone whose display name is not its id, title-cased.
STONE_NAMES = {"dripstone_block": "Dripstone"}


def read_hosts():
    """(namespace, path, placing mod, strength, [ores built], [ores refused]) per host, from HostStone.java."""
    text = open(HOST_TABLE, encoding="utf-8").read()
    pattern = re.compile(r'new HostStone\("(\w+)",\s*"(\w+)",\s*Strength\.(\w+),\s*MapColor\.\w+,\s*'
                         r'EnumSet\.(?:of\(([^)]*)\)|noneOf\(OreKind\.class\))\)(\s*\.placedBy\("(\w+)"\))?\s*;', re.S)
    hosts = []
    for ns, path, strength, ores, _p, placed in pattern.findall(text):
        listed = [o.strip().lower() for o in ores.split(",") if o.strip()]
        unknown = [o for o in listed if o not in ORES or "kind" in ORES[o]]
        if unknown:
            sys.exit(f"{ns}:{path} lists unknown ores {unknown}")
        listed += list(MODDED["hosts"].get(f"{ns}:{path}", {}))
        swallowed = [o for o in ORES if o in listed]
        built = [o for o in swallowed if not geology.refused(f"{ns}_{path}", o)]
        refused = [o for o in swallowed if geology.refused(f"{ns}_{path}", o)]
        hosts.append((ns, path, placed or ns, strength.lower(), built, refused))
    missing = set(MODDED["hosts"]) - {f"{h[0]}:{h[1]}" for h in hosts}
    if missing:
        sys.exit(f"modded_pairs.json has pairs for hosts not in the table: {sorted(missing)}")
    declared = len(re.findall(r"new HostStone\(\"", text))
    if len(hosts) != declared:
        sys.exit(f"parsed {len(hosts)} of {declared} hosts in {HOST_TABLE}: keep each one the shape"
                 f' new HostStone("ns", "path", Strength.X, MapColor.Y, EnumSet.of(...))[.placedBy("mod")];')
    return hosts


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def ours(entry_id):
    """Whether a tag entry or lang key names one of the blocks this script owns."""
    return any(entry_id.startswith(f"{MOD_ID}:{prefix}") for prefix in PREFIXES)


def merge_tag(path, values):
    """Adds our entries to a tag file the rest of the mod may also write.

    Entries of ours already in it (from an earlier run) are dropped first, so a pair taken out of the
    table leaves nothing behind and a second run changes nothing.
    """
    existing = []
    if os.path.exists(path):
        existing = [v for v in json.load(open(path, encoding="utf-8"))["values"]
                    if not ours(v["id"] if isinstance(v, dict) else v)]
    merged = existing + sorted(values, key=lambda e: e["id"])
    write_json(path, {"values": merged})


def faces(texture, mirrored=False):
    uv = [16, 0, 0, 16] if mirrored else [0, 0, 16, 16]
    return {side: {"uv": uv, "texture": texture, "cullface": side} for side in FACES}


def model(stone, ore, mirrored=False):
    """Two coincident cubes, like vanilla's grass block: the stone, then the ore overlay.

    No render_type: from 26.1 the chunk layer is derived from each texture's own alpha, so the
    overlay lands on cutout by itself. Only the stone layer is mirrored in the mirrored model: it has
    to match the host tile beside it exactly, while the ore art reads the same either way.
    """
    return {
        "parent": "minecraft:block/block",
        "textures": {"particle": stone, "stone": stone, "overlay": f"{MOD_ID}:block/{ore}_overlay"},
        "elements": [
            {"from": [0, 0, 0], "to": [16, 16, 16], "faces": faces("#stone", mirrored)},
            {"from": [0, 0, 0], "to": [16, 16, 16], "faces": faces("#overlay")},
        ],
    }


def is_silk_touch_branch(node):
    """Whether this entry or pool carries a Silk Touch condition (not an inverted one)."""
    condition = node.get("condition")
    if isinstance(condition, str):
        return condition.endswith("can_silk_touch")
    if isinstance(condition, dict):
        return condition.get("type") == "minecraft:match_tool" and "silk_touch" in json.dumps(condition)
    return any(c.get("condition") == "minecraft:match_tool" and "silk_touch" in json.dumps(c)
               for c in node.get("conditions", []))


def swap_silk_drops(table, source, our_id):
    """Point every drop of the ore's own block that Silk Touch guards at our block instead.

    The guard sits on the entry in vanilla's tables (an alternatives child) and on the whole pool in
    Tech Reborn's. Returns how many drops were swapped.
    """
    swapped = 0

    def visit(entry, guarded):
        nonlocal swapped
        guarded = guarded or is_silk_touch_branch(entry)
        if guarded and entry.get("name") == source:
            entry["name"] = our_id
            swapped += 1
        for child in entry.get("children", []):
            visit(child, guarded)

    for pool in table.get("pools", []):
        for entry in pool.get("entries", []):
            visit(entry, is_silk_touch_branch(pool))
    return swapped


def stone_name(path):
    return STONE_NAMES.get(path) or " ".join(w.capitalize() for w in path.split("_"))


def camel(*parts):
    words = "_".join(parts).split("_")
    return words[0] + "".join(w[:1].upper() + w[1:] for w in words[1:])


def ore_source(ore, strength):
    """The ore block whose loot and tool tier a variant takes: the deepslate form for a deepslate host."""
    forms = ORES[ore]["forms"]
    return forms[1] if strength == "deepslate" and len(forms) > 1 else forms[0]


def mod_jar(mod, era):
    """The ore mod's jar for this era, or None where it has no release in that era."""
    name = MOD_JARS[mod].get(era)
    return zipfile.ZipFile(os.path.join(JARS, name)) if name else None


def newest_jar(mod):
    return mod_jar(mod, "263") or mod_jar(mod, "261")


def loot_table(jars, era, ore, strength):
    """The ore's own table for this era, or None if the ore has none in that era."""
    ns, name = ore_source(ore, strength).split(":")
    mod = ORES[ore]["mod"]
    jar = jars[era] if mod is None else jars.get((mod, era))
    if jar is None:
        return None
    path = f"data/{ns}/loot_table/blocks/{name}.json"
    if path not in jar.namelist():
        sys.exit(f"{os.path.basename(jar.filename)} has no {path}")
    return json.load(jar.open(path))


def overlay_of(ore, host, strength):
    """(texture key, source file or None) of the overlay a variant wears; None: Seamless Ores ships it."""
    if (ore, host) in HOST_OVERLAYS:
        key, rel = HOST_OVERLAYS[(ore, host)]
        return key, os.path.join(OVERLAYS, rel)
    kind = ORES[ore].get("kind")
    if kind is not None and strength == "deepslate" and kind["deepslate_overlay"]:
        return kind["deepslate_overlay"], None
    return ore, None


def jar_tags(jar, kind):
    """tag id -> members of every tag of this kind in the jar, nested references resolved."""
    tags = {}
    for n in jar.namelist():
        m = re.match(rf"^data/([^/]+)/tags/{kind}s?/(.+)\.json$", n)
        if m:
            try:
                values = json.loads(jar.read(n)).get("values", [])
            except ValueError:
                continue
            tags[f"{m[1]}:{m[2]}"] = [v["id"] if isinstance(v, dict) else v for v in values]

    def resolve(tag, seen):
        out = set()
        for v in tags.get(tag, []):
            if v.startswith("#"):
                if v[1:] not in seen:
                    out |= resolve(v[1:], seen | {v[1:]})
            else:
                out.add(v)
        return out
    return {t: resolve(t, {t}) for t in tags}


def normalised(table):
    """A table with the defaults one format spells out and the other leaves implicit removed."""
    if isinstance(table, dict):
        return {k: normalised(v) for k, v in table.items() if k != "bonus_rolls"}
    if isinstance(table, list):
        return [normalised(v) for v in table]
    if isinstance(table, float) and table == int(table):
        return int(table)
    return table


def write_loot(table, source_id, our_id, name, gate, folders, era):
    """The ore's own table with its Silk Touch drop pointed at our block, gated on our block existing."""
    silk = swap_silk_drops(table, source_id, our_id)
    # An ore that always drops itself (Tech Reborn 6.0.5's bauxite) has no silk branch: our variant then
    # drops that mod's own ore, the item every recipe for it expects, as Seamless Ores' variants do.
    # Anything else is a table shape nobody has checked.
    drops_itself = f'"name": "{source_id}"' in json.dumps(table)
    if silk != 1 and not (silk == 0 and drops_itself):
        sys.exit(f"{source_id} ({era}): expected one silk touch drop of the ore, found {silk}")
    table["random_sequence"] = f"{MOD_ID}:blocks/{name}"
    table = {
        "fabric:load_conditions": [{"condition": "fabric:registry_contains",
                                    "registry": "minecraft:block", "values": [our_id]}],
        "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": m} for m in gate],
        **table,
    }
    for folder in folders:
        write_json(os.path.join(folder, MOD_ID, "loot_table", "blocks", f"{name}.json"), table)


def remove_ours(folder):
    """Deletes every file under folder whose name starts with one of our block prefixes."""
    if not os.path.isdir(folder):
        return
    for name in os.listdir(folder):
        if any(name.startswith(prefix) for prefix in PREFIXES):
            os.remove(os.path.join(folder, name))


PREFIXES = []


def main():
    hosts = read_hosts()
    for ns, path, *_rest in hosts:
        if f"{ns}:{path}" not in HOST_LOOK:
            sys.exit(f"{ns}:{path} has no HOST_LOOK entry")
    for jar in list(ERAS.values()) + [os.path.join(JARS, n) for m in MOD_JARS.values() for n in m.values()]:
        if not os.path.exists(jar):
            sys.exit(f"jar not found: {jar}")
    for ore, info in ORES.items():
        if info["mod"] and info["mod"] not in MOD_JARS:
            sys.exit(f"{ore}: no MOD_JARS entry for {info['mod']}")
    unknown = [o for o in geology.STRICT if o not in ORES] + [h for h in geology.LORE if not any(
        f"{ns}_{p}" == h for ns, p, *_r in hosts)]
    if unknown:
        sys.exit(f"geology.py names unknown keys: {unknown}")
    paths = [path for _ns, path, *_r in hosts]
    clashes = {p for p in paths if paths.count(p) > 1}
    own_hosts = [h for h in hosts if f"{h[0]}:{h[1]}" not in BORROWED]
    PREFIXES[:] = [f"{ns}_{path}_" for ns, path, *_r in own_hosts]

    assets = os.path.join(COMMON, "assets", MOD_ID)
    data = os.path.join(COMMON, "data")
    era_data = {era: os.path.join(COMMON, folder, "data") for era, folder in ERA_FOLDERS.items()}
    mc_data = {"26.1.2": os.path.join(COMMON, "mc26.1", "data"), "26.2": os.path.join(COMMON, "mc26.2", "data")}
    split = []
    # Our generated files are removed first, so a host or ore taken out of the table leaves no file.
    for sub in (("blockstates",), ("models", "block"), ("items",)):
        remove_ours(os.path.join(assets, *sub))
    for root in list(era_data.values()) + list(mc_data.values()):
        remove_ours(os.path.join(root, MOD_ID, "loot_table", "blocks"))

    lang = {f"itemGroup.{MOD_ID}.modded_stones": "Seamless Ores: Modded Stones"}
    mineable, tool_tags, foreign_tool_tags, conv, conv_modded = [], {}, {}, {}, {}
    overlays = {}           # texture key -> source file, for the ones Seamless Ores lacks
    count = 0

    jars = {era: zipfile.ZipFile(path) for era, path in ERAS.items()}
    for mod in MOD_JARS:
        for era in list(ERAS) + ["262"]:
            jars[(mod, era)] = mod_jar(mod, era)
    # Tool tiers from the ore's own mod: vanilla's tags for a vanilla ore, the mod's newest jar for its
    # own. A mod may also gate its ores with tags in its own namespace that feed vanilla's
    # incorrect_for_<tool> lists (Mythic Metals' needs_copper_tools and needs_netherite_tool): a variant
    # left out of them would mine a tier too cheaply, so their membership is mirrored too.
    tool_members = {tag: set(json.load(jars["263"].open(f"data/minecraft/tags/block/{tag}.json"))["values"])
                    for tag in TOOL_TAGS}
    own_tool_tags, ore_tags = {}, {}
    for mod in MOD_JARS:
        jar = newest_jar(mod)
        blocks = jar_tags(jar, "block")
        for tag, members in blocks.items():
            ns, tpath = tag.split(":", 1)
            if ns == "minecraft" and tpath in TOOL_TAGS:
                tool_members[tpath] |= members
            elif ns != "minecraft" and re.fullmatch(r"needs_[a-z_]+", tpath):
                own_tool_tags.setdefault(tag, set()).update(members)
        # c:ores/<material> parity: every such tag the ore we stand in for is in, read from its jar.
        for kind in ("block", "item"):
            for tag, members in jar_tags(jar, kind).items():
                if tag.startswith("c:ores/"):
                    for member in members:
                        ore_tags.setdefault((kind, member), set()).add(tag[len("c:ores/"):])

    for ns, path, placer, strength, kinds, _refused in own_hosts:
        stone, look = HOST_LOOK[f"{ns}:{path}"]
        for ore in kinds:
            info = ORES[ore]
            name = f"{ns}_{path}_{ore}_ore"
            our_id = f"{MOD_ID}:{name}"
            base = f"{MOD_ID}:block/{name}"
            texture, source = overlay_of(ore, f"{ns}:{path}", strength)
            overlays.setdefault(texture, source)

            models = os.path.join(assets, "models", "block")
            if look == "single":
                state = {"variants": {"": {"model": base}}}
                write_json(os.path.join(models, f"{name}.json"), model(stone, texture))
            elif look == "mirrored_turned":
                state = {"variants": {"": [{"model": base}, {"model": base + "_mirrored"},
                                           {"model": base, "y": 180}, {"model": base + "_mirrored", "y": 180}]}}
                write_json(os.path.join(models, f"{name}.json"), model(stone, texture))
                write_json(os.path.join(models, f"{name}_mirrored.json"), model(stone, texture, True))
            elif look == "textures4":
                # Create picks one of four natural textures per block; ours picks the same way, so a
                # vein does not show as the one repeated tile in a varied wall.
                state = {"variants": {"": [{"model": f"{base}_{i}"} for i in range(4)]}}
                for i in range(4):
                    write_json(os.path.join(models, f"{name}_{i}.json"), model(f"{stone}{i}", texture))
                # The item needs one model to point at.
                write_json(os.path.join(models, f"{name}.json"), model(f"{stone}0", texture))
            else:
                sys.exit(f"unknown look {look}")
            write_json(os.path.join(assets, "blockstates", f"{name}.json"), state)
            write_json(os.path.join(assets, "items", f"{name}.json"),
                       {"model": {"type": "minecraft:model", "model": base}})
            # Create and Blockus both have a limestone; a clashing stone name carries its mod.
            clash = f" ({MOD_NAMES[placer]})" if path in clashes else ""
            lang[f"block.{MOD_ID}.{name}"] = f"{stone_name(path)} {info['name']} Ore{clash}"

            # The strength source is also the loot source; the two tiers drop the same items.
            # From 26.3 loot tables are a datapack REGISTRY, and a table naming an item that is not
            # registered fails registry loading: the world does not open. A variant is only registered
            # when the mod that places its stone (and a modded ore's own mod) is installed, so every
            # table is gated on exactly that.
            gate = [placer] + ([info["mod"]] if info["mod"] and info["mod"] != placer else [])
            source_id = ore_source(ore, strength)
            for era in ERAS:
                table = loot_table(jars, era, ore, strength)
                if table is None:
                    continue
                targets = [era_data[era]]
                if era == "261" and info["mod"] and jars.get((info["mod"], "262")):
                    newer = loot_table(jars, "262", ore, strength)
                    if normalised(newer) != normalised(table):
                        write_loot(newer, source_id, our_id, name, gate, [mc_data["26.2"]], era)
                        targets = [mc_data["26.1.2"]]
                        split.append(name)
                write_loot(table, source_id, our_id, name, gate, targets, era)

            # Optional entries: a variant only exists when its mods are installed, and a required entry
            # naming an absent block fails the whole tag.
            entry = {"id": our_id, "required": False}
            mineable.append(entry)
            for tag, members in tool_members.items():
                if source_id in members:
                    tool_tags.setdefault(tag, []).append(entry)
            for tag, members in own_tool_tags.items():
                if source_id in members:
                    foreign_tool_tags.setdefault(tag, []).append(entry)
            if info["mod"] is None:
                conv.setdefault(info["tag"], []).append(entry)
            else:
                for kind in ("block", "item"):
                    materials = ore_tags.get((kind, source_id), set()) | ({info["tag"]} if ore == "zinc" else set())
                    # Parity: an ore its own mod keeps out of every c:ores/<material> tag stays out of
                    # them here too, and is still in c:ores itself.
                    for material in sorted(materials):
                        conv_modded.setdefault((info["mod"], kind, material), []).append(entry)
            count += 1

    # Config screen text. Field names follow SeamlessOresConfigData: the host's name in camelCase,
    # one per host stone, all in the Modded Stones category.
    cfg = f"text.autoconfig.{MOD_ID}"
    lang[f"{cfg}.category.modded_stones"] = "Modded Stones"
    for ns, path, placer, _strength, _kinds, _refused in hosts:
        field = camel(ns, path)
        clash = f" ({MOD_NAMES[placer]})" if path in clashes else ""
        lang[f"{cfg}.option.{field}"] = f"{stone_name(path)}{clash}"
        where = MOD_NAMES[placer] if placer == ns else f"{MOD_NAMES[placer]}'s layers of"
        lang[f"{cfg}.option.{field}.@Tooltip"] = (
            f"Ore generated in {where} {stone_name(path).lower()} matches the stone. Off: it keeps"
            f" its own look. Applies to newly generated chunks, from the next world load.")

    for key, value in lang.items():
        if any(ch in value for ch in (chr(0x2013), chr(0x2014))):
            sys.exit(f"dash in public text: {key}")
    lang_path = os.path.join(assets, "lang", "en_us.json")
    existing = json.load(open(lang_path, encoding="utf-8"))
    kept = {k: v for k, v in existing.items()
            if not (k.startswith(f"block.{MOD_ID}.") and any(k[len(f"block.{MOD_ID}."):].startswith(p) for p in PREFIXES))}
    for key in lang:
        if key in kept and kept[key] != lang[key]:
            sys.exit(f"lang key {key} is written by both generators with different text")
    # The rest of the mod's keys keep their order; ours follow, sorted.
    write_json(lang_path, {**{k: v for k, v in kept.items() if k not in lang}, **dict(sorted(lang.items()))})

    os.makedirs(TEXTURES, exist_ok=True)
    for texture, source in sorted(overlays.items()):
        target = os.path.join(TEXTURES, f"{texture}_overlay.png")
        if source is None:
            if not os.path.exists(target):
                sys.exit(f"Seamless Ores ships no {texture}_overlay.png")
            continue
        if not os.path.exists(source):
            sys.exit(f"overlay missing: {source}")
        shutil.copyfile(source, target)

    merge_tag(os.path.join(data, "minecraft", "tags", "block", "mineable", "pickaxe.json"), mineable)
    for tag, values in tool_tags.items():
        merge_tag(os.path.join(data, "minecraft", "tags", "block", f"{tag}.json"), values)
    # A mod's own tier tags merge with that mod's file; every entry is optional, so the file is inert
    # without the mod.
    for tag, values in foreign_tool_tags.items():
        ns, tpath = tag.split(":", 1)
        merge_tag(os.path.join(data, ns, "tags", "block", f"{tpath}.json"), values)
    for kind in ("block", "item"):
        merge_tag(os.path.join(data, "c", "tags", kind, "ores.json"), mineable)
        for tag, values in conv.items():
            merge_tag(os.path.join(data, "c", "tags", kind, "ores", f"{tag}.json"), values)
    write_modded_material_tags(conv_modded)

    write_java(hosts)
    write_config(hosts)
    write_readme(own_hosts, count)

    refused = sum(len(h[5]) for h in hosts)
    print(f"  Matrix: {count} variants on {len(own_hosts)} stones, plus the dripstone ones Seamless Ores"
          f" generates; {refused} pairs refused by geology; per-version loot for {len(split)} variants")


def write_modded_material_tags(conv_modded):
    """c:ores/<material> for a modded ore's variants: never in a Fabric world without that ore's mod.

    FABRIC'S tags_populated CONDITION ASKS WHETHER A TAG EXISTS, NOT WHETHER ANYTHING IS IN IT. A
    c:ores/tin file whose only entries are optional variants would therefore "populate" c:ores/tin in
    a world without any tin mod, recipes gated on it load with an ingredient that matches nothing, and
    some mods crash on that. Fabric applies no conditions to tag files, so on Fabric each ore mod's
    entries go in the built-in data pack of that mod (fabric/.../resourcepacks/<mod>/), which
    SeamlessOresFabric registers only when that mod is loaded. NeoForge gets plain files in its module.
    """
    for (mod, kind, material), values in sorted(conv_modded.items()):
        rel = os.path.join("tags", kind, "ores", f"{material}.json")
        merge_tag(os.path.join(FABRIC_PACKS, mod, "data", "c", rel), values)
        merge_tag(os.path.join(NEOFORGE_DATA, "c", rel), values)


def java_xp(xp):
    if xp is None:
        return "null"
    lo, hi = xp
    return f"ConstantInt.of({lo})" if lo == hi else f"UniformInt.of({lo}, {hi})"


def write_java(hosts):
    """The modded OreKind constants, ModdedPairs and MatrixGeology."""
    lines = []
    modded = [o for o in ORES if "kind" in ORES[o]]
    for ore in modded:
        k = ORES[ore]["kind"]
        strength = "null" if not k["strength"] else \
            "new float[] {" + ", ".join(f"{v:.1f}F" for v in k["strength"]) + "}"
        forms = ", ".join(f'"{f}"' for f in k["forms"])
        lines.append(f'    {ore.upper()}("{ore}", "{k["mod"]}", "{k["seamless_ores_name"]}", {str(k["nether"]).lower()},')
        lines.append(f'            {java_xp(k["xp"])}, {java_xp(k["deepslate_xp"])}, {strength},')
        lines.append(f'            {forms}),')
    path = os.path.join(CONTENT_JAVA, "OreKind.java")
    text = open(path, encoding="utf-8").read()
    # Every constant, hand-written or generated, ends with a comma; the enum's own ";" follows the block.
    text = replace_block(text, "    // BEGIN GENERATED modded kinds (tools/matrix/generate_matrix.py, from tools/matrix/modded_pairs.json)\n",
                         "    // END GENERATED modded kinds", "\n".join(lines) + "\n" if lines else "", path)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    cases = []
    for host, pairs in MODDED["hosts"].items():
        listed = [o for o in ORES if o in pairs]
        cases.append(f'            case "{host}" -> EnumSet.of({", ".join("OreKind." + o.upper() for o in listed)});')
    java = f"""package com.chillpavz.{MOD_ID}.matrix.content;

import java.util.EnumSet;
import java.util.Set;

/**
 * Which other mods' ores each host swallows, as measured by the pair model: every ore that reaches the
 * stone at a rate above the floor, in a band and on a loader where both mods exist. The geology rule
 * (MatrixGeology) then decides which of them get a variant.
 *
 * <p>GENERATED by tools/matrix/generate_matrix.py from tools/matrix/modded_pairs.json. Do not edit.
 */
final class ModdedPairs {{

    private ModdedPairs() {{}}

    /** The modded kinds the host with this id takes; none for a host with no modded pairs. */
    static Set<OreKind> of(String host) {{
        return switch (host) {{
{chr(10).join(cases)}
            default -> EnumSet.noneOf(OreKind.class);
        }};
    }}
}}
"""
    with open(os.path.join(CONTENT_JAVA, "ModdedPairs.java"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(java)

    with open(os.path.join(CONTENT_JAVA, "MatrixGeology.java"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(geology.java([f"{ns}_{p}" for ns, p, *_r in hosts], list(ORES)))


def write_config(hosts):
    """Writes the Modded Stones switches and their push into both loaders' SeamlessOresConfigData.

    The two copies must stay identical. One switch per host, in the host table's order (by the mod
    that places it, alphabetical by display name).
    """
    fields, push = [], []
    for ns, path, placer, _s, _k, _r in hosts:
        field = camel(ns, path)
        fields += [f'    @ConfigEntry.Category("modded_stones")', "    @ConfigEntry.Gui.Tooltip",
                   f"    public boolean {field} = true;", ""]
        push.append(f'        matrix.put("{ns}_{path}", {field});')
    texts = []
    for path in CONFIG_DATA:
        text = open(path, encoding="utf-8").read()
        text = replace_block(text, "    // BEGIN GENERATED matrix switches (tools/matrix/generate_matrix.py, from the Matrix host table)\n",
                             "    // END GENERATED matrix switches", "\n".join(fields), path)
        text = replace_block(text, "        // BEGIN GENERATED matrix push (tools/matrix/generate_matrix.py)\n",
                             "        // END GENERATED matrix push", "\n".join(push) + "\n", path)
        texts.append(text)
    if texts[0] != texts[1]:
        sys.exit("the two SeamlessOresConfigData copies differ outside the generated blocks; make them identical")
    for path, text in zip(CONFIG_DATA, texts):
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)


def replace_block(text, begin, end, body, where):
    if begin not in text or end not in text:
        sys.exit(f"{where} has no '{begin.strip()}' markers")
    head, rest = text.split(begin, 1)
    _old, tail = rest.split(end, 1)
    return f"{head}{begin}{body}{end}{tail}"


def write_readme(hosts, count):
    """Rewrites the generated Matrix block list in README.md, leaving the prose alone.

    The list comes from the same host table the blocks register from, so the README cannot claim a
    block the jar does not have. A missing marker is an error, not a skip.
    """
    text = open(README, encoding="utf-8").read()
    lines = [f"**{count} blocks**, plus the dripstone ones listed above. Each exists only when the mod "
             f"that places its stone is installed, and one of another mod's ore only with that mod as well. "
             f"A block's id is `<stone>_<ore>_ore`, from the two columns below: `blockus_limestone` and "
             f"`iron` make `blockus_limestone_iron_ore`.", ""]
    for placer in dict.fromkeys(h[2] for h in hosts):
        stones = [(ns, p, k) for ns, p, pl, _s, k, _r in hosts if pl == placer]
        lines.append(f"**{MOD_NAMES[placer]}, requires `{placer}`** ({MOD_BANDS[placer]})")
        lines.append("")
        lines.append("Stones: " + ", ".join(f"{stone_name(p)} `{ns}_{p}`" for ns, p, _k in stones))
        lines.append("")
        lines.append("| Ore | `<ore>` | Also requires | In |")
        lines.append("|---|---|---|---|")
        for ore in ORES:
            within = [stone_name(p) for _ns, p, k in stones if ore in k]
            if not within:
                continue
            mod = ORES[ore]["mod"]
            needs = f"{ORE_MOD_NAMES[mod]} `{mod}`" if mod and mod != placer else ""
            where = "every stone" if len(within) == len(stones) and len(stones) > 1 else ", ".join(within)
            lines.append(f"| {ORES[ore]['name']} | `{ore}` | {needs} | {where} |")
        lines.append("")
    text = replace_section(text, "matrix-block-list", "\n".join(lines).rstrip())
    if any(ch in text for ch in (chr(0x2013), chr(0x2014))):
        sys.exit("dash in README.md")
    with open(README, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def replace_section(text, name, body):
    begin, end = f"<!-- BEGIN GENERATED {name} -->", f"<!-- END GENERATED {name} -->"
    if begin not in text or end not in text:
        sys.exit(f"README.md has no {name} markers")
    head, rest = text.split(begin, 1)
    _old, tail = rest.split(end, 1)
    return f"{head}{begin}\n{body}\n{end}{tail}"


if __name__ == "__main__":
    sys.exit("Run tools/generate_assets.py: it runs this last, after the files this adds to.")
