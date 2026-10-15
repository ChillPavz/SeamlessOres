"""The generator machinery every band shares: what does not depend on a Minecraft version.

Each band's tools/generate_assets.py keeps its own data (the jars it reads, the ore table, the
profiles) and imports this for the rest:

    sys.path.insert(0, <repo>/shared/tools)
    import assetgen
    from assetgen import write_json, block_model, ...

Nothing here may name a band, a Minecraft version or a jar. What changes between bands is a
parameter (the model's render_type, which the game derives itself from 26.1 on).
"""

import json
import os
import re
import sys
import zipfile

MOD_ID = "seamlessores"

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Every third-party jar lives in the umbrella folder's jar library, never in a project.
JARS = os.path.join(os.path.dirname(os.path.dirname(REPO)), "Assets", "Jars")


_LIBRARY = None


def library():
    """File name -> path for every jar in the library, whatever category folder it is filed in. A
    folder named `env` holds per-environment copies under fixed names, and a folder whose name starts
    with a dot is an index of links to the same files; neither is walked."""
    global _LIBRARY
    if _LIBRARY is None:
        found, twice = {}, set()
        for folder, dirs, files in os.walk(JARS):
            dirs[:] = [d for d in dirs if d != "env" and not d.startswith(".")]
            for name in files:
                if name in found:
                    twice.add(name)
                found[name] = os.path.join(folder, name)
        if twice:
            sys.exit(f"the jar library holds these names twice: {sorted(twice)}")
        _LIBRARY = found
    return _LIBRARY


def jar(file_name, env=None):
    """A jar from the library, found by its file name in any of its folders, or the path in the
    environment variable `env` when that is set. A name the library does not hold is returned as a
    path in its root, so the miss is reported under that name."""
    override = os.environ.get(env) if env else None
    if override:
        return override
    name = os.path.basename(file_name.replace("\\", "/"))
    return library().get(name) or os.path.join(JARS, file_name)


def era_file(module_dir, band, rel):
    """The one copy of a source file a band compiles: src/main/<rel>, or src/<era>/<rel> for an era folder
    whose name, split on '+', holds the band (as multiloader-common.gradle picks them). None if absent."""
    src = os.path.join(module_dir, "src")
    folders = ["main"] + sorted(f for f in os.listdir(src) if f != "main" and band in f.split("+"))
    found = [os.path.join(src, f, rel) for f in folders if os.path.exists(os.path.join(src, f, rel))]
    if len(found) > 1:
        sys.exit(f"{rel} exists twice for {band}: {found}")
    return found[0] if found else None


# --- Writing ---------------------------------------------------------------------------------------

# When set, write_json records into this dict instead of writing: a band that runs its data step once
# per Minecraft version captures each run, then decides what goes in the base and what into that
# version's overlay. Set it as assetgen.CAPTURE.
CAPTURE = None


def write_json(path, data):
    if CAPTURE is not None:
        CAPTURE[os.path.normpath(path)] = data
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # LF on every platform: the jar carries these bytes, and the repository stores LF.
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# House style: this project does not use U+2014 EM DASH or U+2013 EN DASH in player-facing text.
# Ordinary hyphens are fine.
DASHES = ("—", "–")


def assert_no_dashes(strings, what):
    """Fails the run if any generated string carries an em or en dash.

    Everything the generators write is read by a player: the config screen's labels and tooltips,
    every block name, and the README. Checking by eye does not scale to a few hundred lang entries
    and would have to be redone on every band, so it is asserted instead. Ordinary hyphens are
    fine and untouched; the rule is only about the two long dashes.
    """
    bad = [(key, text) for key, text in strings if any(d in text for d in DASHES)]
    if bad:
        report = "\n".join("    {}\n      {}".format(k, t) for k, t in bad)
        raise SystemExit(
            "  !! {} {} contain an em or en dash, which must not reach players:\n{}\n"
            "     Replace them with a comma, a colon, a full stop, brackets or a plain hyphen."
            .format(len(bad), what, report))


# --- Names -----------------------------------------------------------------------------------------

# Display-name overrides where the id fragment is not the vanilla display word. Vanilla calls the
# block "Lapis Lazuli Ore" (id lapis_ore) - "Granite Lapis Ore" would be the exact naming
# inconsistency users reported on the incumbent. Quartz stays "Quartz" (no "Nether" prefix: that
# prefix distinguishes an overworld quartz that does not exist, and ours is already host-prefixed).
DISPLAY_NAMES = {"lapis": "Lapis Lazuli"}
# A block's name never carries a mod's name (owner, 8 Oct 2026): "Granite Aquamarine Ore" whichever
# mod the aquamarine is from. These prefixes only keep ids apart; tooltips name the mod.
MOD_PREFIXES = ("silents_", "techreborn_", "energized_", "occultism_", "mi_", "ie_", "mek_", "oreganized_")
# A stone whose display name is not its id path, title-cased.
STONE_NAMES = {"dripstone_block": "Dripstone"}


def title(name):
    for prefix in MOD_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
    return " ".join(DISPLAY_NAMES.get(part, part.capitalize()) for part in name.split("_"))


def stone_name(path):
    return STONE_NAMES.get(path) or title(path)


# --- Models ----------------------------------------------------------------------------------------

FACES = ["down", "up", "north", "south", "west", "east"]


def faces(ref, end_ref=None, mirrored=False):
    """Full-cube faces: ref on the four sides, end_ref (default the same) on up and down."""
    return {side: {"uv": [16, 0, 0, 16] if mirrored else [0, 0, 16, 16],
                   "texture": end_ref if end_ref and side in ("up", "down") else ref, "cullface": side}
            for side in FACES}


def block_model(side, end, overlay, overlay_end, mirrored=False, render_type=None):
    """Two coincident full cubes, following vanilla's own grass_block pattern: the stone, then the ore.

    The base is opaque so it lands on the solid layer; the overlay has alpha and must land on cutout,
    or its transparent pixels are drawn opaque. FROM 26.1 there is no render_type field: the chunk
    layer is DERIVED from the texture's own alpha (SpriteContents.computeTransparency feeding
    ChunkSectionLayer.byTransparency). At 1.21.11 and below the layer is declared, and a band passes
    render_type. Only the stone layer is mirrored in a mirrored model: it has to match the host tile
    beside it exactly, while the ore art reads the same either way.
    """
    textures = {"particle": side, "side": side, "end": end, "overlay": f"{MOD_ID}:block/{overlay}_overlay"}
    if overlay_end != overlay:
        textures["overlay_end"] = f"{MOD_ID}:block/{overlay_end}_overlay"
    model = {"parent": "minecraft:block/block"}
    if render_type:
        model["render_type"] = render_type
    model["textures"] = textures
    model["elements"] = [
        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": faces("#side", "#end", mirrored)},
        {"from": [0, 0, 0], "to": [16, 16, 16],
         "faces": faces("#overlay", "#overlay_end" if "overlay_end" in textures else None)},
    ]
    return model


LOOKS = ("single", "column", "turned", "mirrored_turned", "textures4")


def look_models(name, look, side, end, overlay, overlay_end, render_type=None, overlays=None):
    """(blockstate, {model file name: model}) for one variant in a host of the given look.

    single / column: one model (a column's end faces are just another texture).
    turned: the host picks itself as is or turned 180 (Meadow's limestone on 1.20.1); one model, turned
    in the blockstate, which turns the ore with it.
    mirrored_turned: the host picks among itself mirrored and turned (Wilder Wild's gabbro), so ours
    does the same, or a vein shows as the one tile that never turns.
    textures4: the host picks one of four natural textures per block (Create's strata); ours picks the
    same way. The item points at the plain model, which is the first texture.
    overlays: {model suffix: (overlay, overlay_end)} where each model needs its own (a translucent ore,
    precomposited over the rock that model shows); otherwise every model takes overlay and overlay_end.
    Redstone needs no lit variant: vanilla's own redstone_ore blockstate is a single model too, the lit
    state only changes light emission.
    """
    base = f"{MOD_ID}:block/{name}"

    def model(s, e, mirrored=False, suffix=""):
        o, oe = overlays[suffix] if overlays else (overlay, overlay_end)
        return block_model(s, e, o, oe, mirrored=mirrored, render_type=render_type)

    if look in ("single", "column"):
        return {"variants": {"": {"model": base}}}, {name: model(side, end)}
    if look == "turned":
        return {"variants": {"": [{"model": base}, {"model": base, "y": 180}]}}, {name: model(side, end)}
    if look == "mirrored_turned":
        state = {"variants": {"": [{"model": base}, {"model": base + "_mirrored"},
                                   {"model": base, "y": 180}, {"model": base + "_mirrored", "y": 180}]}}
        return state, {name: model(side, end),
                       f"{name}_mirrored": model(side, end, mirrored=True, suffix="_mirrored")}
    if look == "textures4":
        state = {"variants": {"": [{"model": f"{base}_{i}"} for i in range(4)]}}
        models = {f"{name}_{i}": model(f"{side}{i}", f"{end}{i}", suffix=f"_{i}") for i in range(4)}
        models[name] = model(f"{side}0", f"{end}0")
        return state, models
    sys.exit(f"{name}: unknown look {look}")


# --- Texture pool ----------------------------------------------------------------------------------

# Every overlay lives once, here. A band ships the ones its models name (shared/gradle/texture-pool.gradle
# copies them at build time) and keeps its own copy only where its art differs, under the same name.
POOL = os.path.join(REPO, "shared", "textures", "block")


def texture_path(band_textures, file_name):
    """Where a band's texture file is: its own copy (an override) if it has one, else the pool's.
    None if neither has it."""
    for folder in (band_textures, POOL):
        path = os.path.join(folder, file_name)
        if os.path.exists(path):
            return path
    return None


def write_texture_json(band_textures, file_name, data):
    """Writes a texture's JSON side file (an animation .mcmeta) where the build will find it.

    Into the pool when the pool has none or the same bytes, and any band copy is removed (the build
    refuses a band copy identical to the pool's); into the band as an override when the pool holds a
    different one. CAPTURE does not apply: textures are the same on every Minecraft version of a band.
    """
    text = json.dumps(data, indent=2) + "\n"
    pooled = os.path.join(POOL, file_name)
    own = os.path.join(band_textures, file_name)
    if not os.path.exists(pooled) or open(pooled, encoding="utf-8", newline="").read() == text:
        target = pooled
        if os.path.exists(own):
            os.remove(own)
    else:
        target = own
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# --- Reading jars ----------------------------------------------------------------------------------

def jar_tags(jar, kind):
    """tag id -> members of every tag of this kind ("block" or "item") in an open jar, with nested
    references (#tag) resolved inside the jar. Powah's needs_iron_tool is nothing but #c:ores/uraninite
    and Silent's Gems points c:ores/<gem> at #silentgems:ores/<gem>: an unresolved reader sees neither."""
    tags = {}
    for n in jar.namelist():
        m = re.match(rf"^data/([^/]+)/tags/{kind}s?/(.+)\.json$", n)
        if m:
            try:
                values = json.loads(jar.read(n)).get("values", [])
            except ValueError:
                continue
            tags[f"{m.group(1)}:{m.group(2)}"] = [v["id"] if isinstance(v, dict) else v for v in values]

    def resolve(tag, seen):
        members = set()
        for value in tags.get(tag, []):
            if value.startswith("#"):
                if value[1:] not in seen:
                    members |= resolve(value[1:], seen | {value[1:]})
            else:
                members.add(value)
        return members

    return {tag: resolve(tag, {tag}) for tag in tags}


TOOL_TAGS = ["needs_stone_tool", "needs_iron_tool", "needs_diamond_tool"]


def read_mod_tags(mod_jars, ore_defs):
    """What each supported mod's own jar says about its ores, for tag parity.

    Returns (ore_tags, tool_tags, own_tool_tags): block and item id -> every c:ores/<material> tag it is
    in; vanilla tier tag (needs_iron_tool...) -> the blocks the mods put in it; and (namespace, tag) ->
    the blocks of a mod's OWN needs_* tag. Mythic Metals 0.26.0 feeds needs_copper_tools and
    needs_netherite_tool into vanilla's incorrect_for_<tool> lists, a tier requirement by another route,
    so a variant left out of them would mine a tier too cheaply. Read whatever the jar has rather than
    naming them. A missing jar is reported, and its ores fall back to needs_iron_tool.
    """
    ore_tags = {"block": {}, "item": {}}
    tool_tags = {}
    own_tool_tags = {}
    for mod_id, mod_jar in mod_jars.items():
        if not mod_jar or not os.path.exists(mod_jar):
            print(f"  !! {mod_id} jar not found ({mod_jar}) - its tool tags fall back to needs_iron_tool")
            for ore in ore_defs:
                if ore.get("mod") == mod_id:
                    tool_tags.setdefault("needs_iron_tool", set()).update(
                        f"{mod_id}:{tier_ore}" for tier_ore in ore["tiers"].values())
            continue
        with zipfile.ZipFile(mod_jar) as jar:
            for kind in ("block", "item"):
                for tag, members in jar_tags(jar, kind).items():
                    namespace, path = tag.split(":", 1)
                    if namespace == "c" and path.startswith("ores/"):
                        for member in members:
                            ore_tags[kind].setdefault(member, set()).add(path[len("ores/"):])
                    elif kind == "block" and namespace == "minecraft" and path in TOOL_TAGS:
                        tool_tags.setdefault(path, set()).update(members)
                    elif kind == "block" and namespace != "minecraft" and re.fullmatch(r"needs_[^/]+", path):
                        own_tool_tags.setdefault((namespace, path), set()).update(members)
    return ore_tags, tool_tags, own_tool_tags


# --- Loot ------------------------------------------------------------------------------------------

def is_silk_touch_branch(node):
    """Whether a loot entry or pool carries a Silk Touch condition (not an inverted one).

    Three spellings, and 26.3 introduced two of them. Up to 26.2 a "conditions" LIST holding a
    minecraft:match_tool. From 26.3 a single "condition": vanilla, Energized Power and Mythic Upgrades
    name the shared predicate as a string ("minecraft:tool/can_silk_touch"), Tech Reborn writes the
    match_tool object inline. Missing any of them silently makes a silk-touched variant drop the source
    mod's block instead of ours.
    """
    condition = node.get("condition")
    if isinstance(condition, str):
        return condition.endswith("can_silk_touch")
    if isinstance(condition, dict):
        return condition.get("type") == "minecraft:match_tool" and "silk_touch" in json.dumps(condition)
    return any(c.get("condition") == "minecraft:match_tool" and "silk_touch" in json.dumps(c)
               for c in node.get("conditions", []))


def silk_touch_to(table, source, our_id, name, where):
    """Points every drop of the ore's own block that Silk Touch guards at our block instead.

    The guard sits on the entry in vanilla's tables (an alternatives child) and on the whole pool in Tech
    Reborn's. Exactly one such drop is expected. An ore that always drops itself (Tech Reborn 6.0.5's
    bauxite) has none: our variant then drops that mod's own ore, the item every recipe for it expects.
    Anything else is a table shape nobody has checked, and stops the run. `where` names the run in
    that message (the Minecraft version being read).
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
    if swapped != 1 and not (swapped == 0 and f'"name": "{source}"' in json.dumps(table)):
        sys.exit(f"  !! {name} ({where}): expected one silk touch drop of {source}, found {swapped}")


# --- The host table --------------------------------------------------------------------------------

def parse_host_table(path):
    """Every host stone declared in a band's HostStone.java, in HostStone.ALL order.

    Each is a dict: const (the Java constant), name (the id prefix of its variants), ns and path (its
    block id), tier (OreTier, lower case), placed_by (the mod that places it; None for the game's own
    rock), swallowed_by (the mod whose feature lays it over ore), listed (the ore keys written in the
    table, lower case). The band adds what is its own data: looks, measured pairs, geology.
    """
    text = open(path, encoding="utf-8").read()
    decls = re.findall(r'public static final HostStone (\w+) = (vanilla|placed)\((.*?)\)((?:\s*\.\w+\([^)]*\))*);',
                       text, re.S)
    hosts = []
    for const, kind, args, chain in decls:
        parts = [a.strip() for a in args.split(",")]
        strings = [a.strip('"') for a in parts if a.startswith('"')]
        tier = next(a for a in parts if a.startswith("OreTier.")).split(".", 1)[1].lower()
        listed = [a.lower() for a in parts if re.fullmatch(r"[A-Z_]+", a)]
        if kind == "vanilla":
            name, ns, block, placed_by = strings[0], "minecraft", strings[-1], None
        else:
            ns, block = strings
            name, placed_by = f"{ns}_{block}", ns
        swallowed_by = placed_by
        for call, call_args in re.findall(r"\.(\w+)\(([^)]*)\)", chain):
            words = [a.strip() for a in call_args.split(",")]
            if call == "placedBy":
                placed_by = swallowed_by = words[0].strip('"')
            elif call == "swallowing":
                swallowed_by = words[0].strip('"')
                listed = [a.lower() for a in words[1:]]
            else:
                sys.exit(f"{const}: unknown call .{call}()")
        hosts.append({"const": const, "name": name, "ns": ns, "path": block, "tier": tier,
                      "placed_by": placed_by, "swallowed_by": swallowed_by, "listed": listed})
    declared = len(re.findall(r"public static final HostStone \w+ =", text))
    if len(hosts) != declared:
        sys.exit(f"parsed {len(hosts)} of {declared} hosts in {path}: keep each one the shape"
                 ' vanilla("name"[, "path"], OreTier.X, MapColor.Y) or placed("ns", "path", OreTier.X, MapColor.Y,'
                 ' ORE, ...), optionally .placedBy("mod") or .swallowing("mod", ORE, ...)')
    order = re.search(r"List<HostStone> ALL = List\.of\((.*?)\);", text, re.S).group(1)
    if [c.strip() for c in order.split(",")] != [h["const"] for h in hosts]:
        sys.exit("HostStone.ALL must list every host, in declaration order")
    return hosts


def replace_block(text, begin, end, body, where):
    """`text` with what lies between the `begin` and `end` marker lines replaced by `body`."""
    if begin not in text or end not in text:
        sys.exit(f"{where} has no '{begin.strip()}' markers")
    head, rest = text.split(begin, 1)
    _old, tail = rest.split(end, 1)
    return f"{head}{begin}{body}{end}{tail}"


def camel(name):
    """A host name as its config field: blockus_limestone -> blockusLimestone."""
    first, *rest = name.split("_")
    return first + "".join(word.capitalize() for word in rest)


def write_host_switches(config_java, host_names):
    """The push of every host's switch into SeamlessOresConfig.Values.hosts, in the Cloth Config class,
    from the host table, so a host added to HostStone.java cannot lack its switch."""
    text = open(config_java, encoding="utf-8").read()
    push = "".join(f'        values.hosts.put("{h}", {camel(h)});\n' for h in host_names)
    write_text(config_java, replace_block(
        text, "        // BEGIN GENERATED host switches (tools/generate_assets.py, from the host table)\n",
        "        // END GENERATED host switches", push, config_java))
