"""The host table and the stones other mods place, for every band's generator: one copy.

A band keeps its own data (the ore table, how each stone is drawn, its modded_pairs.json, which loaders
each mod ships for, the jars) and asks this for the rest: the hosts read from HostStone.java with the
measured pairs and the geology rule, the variants, their ids, titles and overlays, the mods each one
needs, the config switch strings, the README section, and the Java that is data. Nothing here may name
a band, a Minecraft version or a jar.

    from placed import Hosts
    HOSTS = Hosts(HOST_TABLE, ORE_DEFS, PAIRS_JSON, HOST_LOOK)
"""

import io
import json
import os
import sys
import zipfile

import geology
from assetgen import (MOD_ID, POOL, STONE_NAMES, camel, replace_block, stone_name, texture_path, title, write_text)


def index_ores(ore_defs):
    """Gives every ore its key (the overlay key unless it names one; mirrors OreType.key()) and returns
    key -> ore. Two ores of one key would make the measured pairs ambiguous."""
    by_key = {}
    for ore in ore_defs:
        ore.setdefault("key", ore["overlay"])
        if by_key.setdefault(ore["key"], ore) is not ore:
            sys.exit(f"two ores share the key {ore['key']}")
    return by_key


def forms_of(ore):
    """The ore's own block ids, stone then deepslate then Nether then End: how modded_pairs.json names a kind."""
    return [f"{ore.get('mod') or 'minecraft'}:{ore['tiers'][t]}" for t in ("stone", "deepslate", "nether", "end")
            if t in ore["tiers"]]


def tier_of(cfg, ore):
    """The ore form a variant stands in for (its drops, tool tier and id). A stone another mod places
    takes its own tier's form where the ore has one, else the first the ore has (a Nether ore in scoria);
    cinnabar the stone form, else the Nether one; the game's other rock its own tier's (which the ore may
    lack: then there is no variant)."""
    if cfg["placed_by"]:
        return cfg["ore_tier"] if cfg["ore_tier"] in ore["tiers"] else next(
            t for t in ("stone", "deepslate", "nether", "end") if t in ore["tiers"])
    if cfg["tier"] == "cinnabar":
        return "stone" if "stone" in ore["tiers"] else "nether"
    return cfg["ore_tier"]


def _shared_words(a, b):
    """The words two ids share, in order (longest common subsequence): what a mod's stone and deepslate
    forms have in common is the ore's name (brilliant_stone, brilliant_deepslate -> brilliant)."""
    table = [[[] for _ in range(len(b) + 1)] for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            table[i][j] = ([a[i]] + table[i + 1][j + 1] if a[i] == b[j]
                           else max(table[i + 1][j], table[i][j + 1], key=len))
    return table[0][0]


def _words(path):
    """A block path's words. "deepslate" and "ore" glued to the front of a word count as words of their
    own: Electrodynamics writes orealuminum and deepslateorealuminum."""
    out = []
    for word in path.split("_"):
        for prefix in ("deepslate", "ore"):
            if word.startswith(prefix) and len(word) > len(prefix) + 2 and word not in ("ores",):
                out.append(prefix)
                word = word[len(prefix):]
        out.append(word)
    return out


def id_of(cfg, ore, tier):
    """The id rule (owner, 22 Oct 2026): <stone>_<ore>_ore. Each half is its block's path, with any mod
    but the game's in front by its full id (create_limestone, mekanism_uranium); dripstone_block is
    dripstone. The ore half is the ore's name: a Nether or End form's own path, else the words the mod's
    stone and deepslate forms share, without "deepslate" and "ore", then _ore."""
    stone = "dripstone" if cfg["id"] == "minecraft:dripstone_block" else (
        cfg["path"] if cfg["ns"] == "minecraft" else f"{cfg['ns']}_{cfg['path']}")
    forms = ore["tiers"]
    if tier in ("stone", "deepslate") and "stone" in forms and "deepslate" in forms:
        words = _shared_words(_words(forms["stone"]), _words(forms["deepslate"]))
    else:
        words = _words(forms[tier])
    words = [w for w in words if w != "deepslate"]
    if "ore" in words:
        words.remove("ore")
    mod = ore.get("mod") or "minecraft"
    name = "_".join(words) if mod == "minecraft" else f"{mod}_{'_'.join(words)}"
    return f"{stone}_{name}_ore"


def load_pairs(path, ore_by_key):
    """modded_pairs.json, the pair model's measurement. Its "kinds" restate the ore table, so they are
    only checked against it: a kind the table does not have, or has with other forms, is an error."""
    with open(path, encoding="utf-8") as handle:
        pairs = json.load(handle)
    for key, kind in pairs["kinds"].items():
        ore = ore_by_key.get(key)
        if ore is None or forms_of(ore) != kind["forms"]:
            sys.exit(f"{path}: ore {key} is not the ore table's ({ore and forms_of(ore)} vs {kind['forms']})")
    return pairs


class Hosts(dict):
    """Every host stone, by name, in HostStone.ALL order, from the shared parser of HostStone.java with
    the band's data added: its look, the measured modded pairs, the fixed geology rule.

    swallows: the ore keys a mod's stone feature lays it over (listed in the table, plus the measured
    modded pairs); refused: those the fixed geology rule takes out.
    """

    def __init__(self, host_table, ore_defs, pairs_path, host_look, since=None):
        from assetgen import parse_host_table
        super().__init__()
        self.ore_defs = ore_defs
        self.ore_by_key = index_ores(ore_defs)
        self.pairs = load_pairs(pairs_path, self.ore_by_key)
        # The band's renamed_ids.json sits beside its modded_pairs.json: the pairs that keep a shipped id.
        self.renamed_path = os.path.join(os.path.dirname(pairs_path), "renamed_ids.json")
        self.kept = (json.load(open(self.renamed_path, encoding="utf-8"))["kept"]
                     if os.path.exists(self.renamed_path) else {})
        for decl in parse_host_table(host_table):
            name, placed_by, listed = decl["name"], decl["placed_by"], decl["listed"]
            host_id = f"{decl['ns']}:{decl['path']}"
            unknown = [o for o in listed if o not in self.ore_by_key]
            if unknown:
                sys.exit(f"{host_id} lists unknown ores {unknown}")
            listed = listed + list(self.pairs["hosts"].get(host_id, {}))
            swallows = [o["key"] for o in ore_defs if o["key"] in listed]
            if host_id not in host_look:
                sys.exit(f"{host_id} has no HOST_LOOK entry")
            look = host_look[host_id]
            tier = decl["tier"]
            self[name] = {"name": name, "id": host_id, "ns": decl["ns"], "path": decl["path"], "tier": tier,
                          "ore_tier": "stone" if tier in ("dripstone", "cinnabar") else tier,
                          "placed_by": placed_by, "swallowed_by": decl["swallowed_by"],
                          "backported_by": decl.get("backported_by"), "swallows": swallows,
                          "refused": [o for o in swallows if placed_by and geology.fixed(name, o)],
                          # A moss look's third entry is the moss texture, not an end face.
                          "look": look[0], "side": look[1],
                          "end": look[2] if len(look) > 2 and not look[0].startswith("moss") else look[1],
                          "moss": look[2] if look[0].startswith("moss") else None,
                          # bottom_top: (look, side, top, bottom), the down face its own texture.
                          "bottom": look[3] if look[0] == "bottom_top" else None,
                          "adds": host_id.replace(":", "_") in ADDS_ORE_HOSTS,
                          "since": (since or {}).get(host_id)}
        missing = set(self.pairs["hosts"]) - {h["id"] for h in self.values()}
        if missing:
            sys.exit(f"{pairs_path} has pairs for stones not in the host table: {sorted(missing)}")

    def placed(self):
        """The stones other mods place, in table order."""
        return [c for c in self.values() if c["placed_by"]]

    def variants(self, cinnabar_family=None):
        """Every (host, host config, ore def, source form, source tier) that actually exists.

        In the game's own rock a pairing exists only where the ore has a form for that host's tier, which
        is what keeps granite quartz and basalt iron from being invented; the variant stands in for that
        form. A stone another mod places pairs with every ore it swallows that the geology rule keeps,
        and stands in for every form of it; it takes its own tier's form for drops and tool tier where
        the ore has one, else the first the ore has (a Nether ore in scoria). Mirrors HostStone.ores()
        and OreVariant.source(). cinnabar_family: the overlay keys a cinnabar host takes (26.2 up).
        """
        for host, cfg in self.items():
            if cfg["placed_by"]:
                for ore in self.ore_defs:
                    if ore["key"] in cfg["swallows"] and ore["key"] not in cfg["refused"]:
                        tier = tier_of(cfg, ore)
                        yield host, cfg, ore, ore["tiers"][tier], tier
                continue
            for ore in self.ore_defs:
                # skip_hosts: the ore's own mod already ships a seamless variant for that stone, so ours
                # would take the host over (the injector prepends). Mirrors OreType.skipHosts.
                if host in ore.get("skip_hosts", ()):
                    continue
                # A modded ore the geology rule refuses in this rock of the game's own: never built (an id an
                # earlier release built is retired, retired.py). Mirrors HostStone.ores().
                if geology.fixed(host, ore["key"]):
                    continue
                # The family is named by overlay; an ore drawn with another's overlay (Basic Nether Ores' iron
                # wears the game's) is not that ore, as OreType's cinnabar family is by type.
                if cfg["tier"] == "cinnabar" and (ore["overlay"] not in (cinnabar_family or ())
                                                  or ore["key"] != ore["overlay"]):
                    continue
                tier = tier_of(cfg, ore)
                if tier in ore["tiers"]:
                    yield host, cfg, ore, ore["tiers"][tier], tier

    def name_of(self, host, ore):
        """The variant's block id path, by the id rule (6.0.0, id_of), unless renamed_ids.json keeps a
        shipped id for the pair. Java reads the result from ids.json (renamed.py), never recomputes it."""
        return self.kept.get(f"{host}|{ore['key']}") or id_of(self[host], ore, tier_of(self[host], ore))

    def legacy_name_of(self, host, ore):
        """The id this pair had up to 5.x: <host>_<ore>_ore, the ore by its name in the game's rock and by
        its key in a placed stone. Only seeds renamed_ids.json; nothing is named by it any more."""
        return f"{host}_{ore['key'] if self[host]['placed_by'] else ore['name']}_ore"

    def title_of(self, host, ore):
        """e.g. Granite Iron Ore, Limestone Iron Ore. The stone's own name, then the ore's (never its
        mod's), then Ore. `name_style` is a formatting code the source mod puts on its own ore's name
        (Born in Chaos names infected diamond in dark aqua, §3), so the variant reads like the ore."""
        cfg = self[host]
        return f"{ore.get('name_style', '')}{host_stone_name(cfg)} {title(ore['key'] if cfg['placed_by'] else ore['name'])} Ore"

    def overlay_for(self, ore, host_cfg, face="side", model=""):
        """Overlay key for this host and face, honouring a per-host or per-tier override. Mirrors
        OreType.overlayFor.

        host_overlays: a TRANSLUCENT ore (Silent's Gems' opal, Cobblemon) takes the colour of the rock
        behind it, so each host needs its own precomposited overlay; ours render CUTOUT, which cannot do
        partial alpha. A (side, end) pair serves a host whose end faces use another texture; a dict by
        model suffix ("", "_mirrored", "_0" to "_3") serves a host drawn several ways, where each look
        puts other rock behind the ore. Generator only: the Java side never reads overlay keys.
        """
        chosen = ore.get("host_overlays", {}).get(host_cfg["name"])
        if isinstance(chosen, dict):
            chosen = chosen[model]
        if chosen is not None:
            if isinstance(chosen, tuple):
                return chosen[0] if face == "side" else chosen[1]
            return chosen
        if host_cfg["tier"] == "deepslate" and ore.get("deepslate_overlay"):
            return ore["deepslate_overlay"]
        return ore["overlay"]

    def overlays_of(self, ore, host_cfg):
        """{model suffix: (side overlay, end overlay)} for assetgen.look_models."""
        suffixes = suffixes_of(host_cfg)
        return {s: (self.overlay_for(ore, host_cfg, "side", s), self.overlay_for(ore, host_cfg, "end", s))
                for s in suffixes}

    def overlay_keys(self, cinnabar_family=None):
        """Every overlay texture key a model references, end faces and every look included."""
        return sorted({key for _h, c, o, _s, _t in self.variants(cinnabar_family)
                       for pair in self.overlays_of(o, c).values() for key in pair})


# The models a look writes, by suffix: what look_models names them.
MODEL_SUFFIXES = {"single": ("",), "column": ("",), "bottom_top": ("",), "turned": ("",), "mirrored": ("", "_mirrored"),
                  "mirrored_turned": ("", "_mirrored"), "textures4": ("", "_0", "_1", "_2", "_3"),
                  "moss_mirrored": ("", "_mirrored"), "moss_mirrored_turned": ("", "_mirrored"), "turned4": ("",)}


def suffixes_of(cfg):
    """The models a host's look writes, by suffix; a weighted look writes one per texture."""
    if cfg["look"] == "weighted":
        return ("",) + tuple(f"_{i}" for i in range(len(cfg["side"])))
    return MODEL_SUFFIXES[cfg["look"]]

# Stones ore never forms in today (in no ore replaceables tag): a variant there ADDS ore, so its switch is
# Off by default (owner, 21 Oct 2026; the opt-in rule). Host names, the same on every band.
ADDS_ORE_HOSTS = {"regions_unexplored_argillite", "regions_unexplored_chalk", "biomeswevegone_dacite",
                  "biomeswevegone_white_dacite", "biomeswevegone_red_rock",
                  # Atmospheric's sandstones and travertines, Nature's Spirit's chert, chalk and pink sandstone:
                  # surface rules and cliffs laid before the ores, in no ore tag (24 Oct 2026).
                  "atmospheric_arid_sandstone", "atmospheric_red_arid_sandstone", "atmospheric_ivory_travertine",
                  "atmospheric_peach_travertine", "atmospheric_persimmon_travertine", "atmospheric_saffron_travertine",
                  "natures_spirit_chert", "natures_spirit_white_chalk", "natures_spirit_pink_sandstone",
                  # BetterEnd (25 Oct 2026): laid before the End's ores, in no ore tag.
                  "betterend_flavolite",
                  "betterend_violecite",
                  "betterend_sulphuric_rock",
                  "betterend_brimstone",
                  "betterend_umbralith",
                  "betterend_azure_jadestone",
                  "betterend_sandy_jadestone",
                  "betterend_virid_jadestone",
                  # The Outer End (25 Oct 2026): laid before the End's ores, in no ore tag.
                  "outer_end_violite",
                  "outer_end_rose_tangled_violite",
                  "outer_end_mint_tangled_violite",
                  "outer_end_cobalt_tangled_violite",
                  "outer_end_ancient_stone",
                  # Enlightend (25 Oct 2026): laid before the End's ores, in no ore tag.
                  "enlightened_end_palerock",
                  # Legendary Monsters (25 Oct 2026): laid before the End's ores, in no ore tag.
                  "legendary_monsters_enderstone"}


def gate_of(host_cfg, ore):
    """The mods a variant exists with: the one that places its stone (or adds the game rock to this band,
    Vanilla Backport's cinnabar), and the ore's own."""
    return list(dict.fromkeys(m for m in (host_cfg["placed_by"], host_cfg.get("backported_by"), ore.get("mod")) if m))


def loot_modules(gate, by_mod, default):
    """The loader modules every mod of a variant's gate ships for (by_mod, else `default`), in the first
    mod's order; empty when no loader carries them all."""
    modules = None
    for mod in gate:
        ships = by_mod.get(mod, default)
        modules = [m for m in (ships if modules is None else modules) if m in ships]
    return list(default) if modules is None else modules


# --- Translucent ores on the stones other mods place -------------------------------------------------

def texture_of(ref, jars):
    """The RGB image of a texture reference such as twigs:block/rhyolite, read from the jar of its
    namespace (jars: namespace -> jar path)."""
    from PIL import Image
    ns, path = ref.split(":", 1)
    if ns not in jars:
        sys.exit(f"no jar to read {ref} from: add the {ns} jar")
    with zipfile.ZipFile(jars[ns]) as jar:
        image = Image.open(io.BytesIO(jar.read(f"assets/{ns}/textures/{path}.png"))).convert("RGB")
    return image.crop((0, 0, 16, 16))


def composite(layer, rock, mirrored=False):
    """An opaque, cutout-safe overlay: the solved translucent layer (RGBA, colour and opacity per pixel)
    painted over the rock it sits on, C = a*O + (1 - a)*H, which is how the source mod drew it. In a
    mirrored model only the stone is mirrored, so the rock behind each overlay pixel is the mirror's."""
    from PIL import Image, ImageOps
    if mirrored:
        rock = ImageOps.mirror(rock)
    out = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for x in range(16):
        for y in range(16):
            r, g, b, a = layer.getpixel((x, y))
            if a:
                h = rock.getpixel((x, y))
                f = a / 255
                out.putpixel((x, y), tuple(round(f * o + (1 - f) * c) for o, c in zip((r, g, b), h)) + (255,))
    return out


def write_texture_png(band_textures, file_name, image):
    """Writes a texture where the build will find it: into the pool when the pool has none or the same
    pixels, else into the band as an override (a stone drawn differently in this band). Mirrors
    assetgen.write_texture_json."""
    from PIL import Image
    pooled = os.path.join(POOL, file_name)
    own = os.path.join(band_textures, file_name)
    same = os.path.exists(pooled) and list(Image.open(pooled).convert("RGBA").getdata()) == list(image.getdata())
    if not os.path.exists(pooled) or same:
        if not same:
            image.save(pooled)
        if os.path.exists(own):
            os.remove(own)
        return pooled
    os.makedirs(band_textures, exist_ok=True)
    image.save(own)
    return own


def translucent_overlays(hosts, band_textures, jars):
    """Gives each translucent ore (one with a "translucent" layer) its own overlay on every stone another
    mod places, one per look the stone has: per random texture, mirrored, and the end faces of a pillar.
    Keys <overlay>_<host>[_<suffix>][_end]; an override the band already wrote by hand is kept. Writes
    the files that are missing or stale; returns how many it wrote. jars: namespace -> jar path."""
    from PIL import Image
    written = 0
    rocks = {}
    for host, cfg, ore, _s, _t in list(hosts.variants()):
        layer_path = ore.get("translucent")
        if not layer_path:
            continue
        overrides = ore.setdefault("host_overlays", {})
        if host in overrides:
            continue
        if cfg["bottom"]:
            sys.exit(f"{host}: a translucent ore on a bottom_top stone needs a third overlay for the down face")
        layer = Image.open(layer_path).convert("RGBA")
        chosen = {}
        if cfg["look"] == "weighted":
            sys.exit(f"{host}: a translucent ore on a weighted stone needs an overlay per texture")
        for suffix in suffixes_of(cfg):
            index = suffix[1:] if cfg["look"] == "textures4" and suffix else ("0" if cfg["look"] == "textures4" else "")
            pair = []
            for face, ref in (("side", cfg["side"]), ("end", cfg["end"])):
                ref = ref + index
                key = f"{ore['overlay']}_{host}{'_' + index if index else ''}{'_mirrored' if suffix == '_mirrored' else ''}"
                if face == "end":
                    if cfg["end"] == cfg["side"]:
                        pair.append(pair[0])
                        continue
                    key += "_end"
                if ref not in rocks:
                    rocks[ref] = texture_of(ref, jars)
                image = composite(layer, rocks[ref], mirrored=suffix == "_mirrored")
                path = texture_path(band_textures, f"{key}_overlay.png")
                if not path or list(Image.open(path).convert("RGBA").getdata()) != list(image.getdata()):
                    write_texture_png(band_textures, f"{key}_overlay.png", image)
                    written += 1
                pair.append(key)
            chosen[suffix] = tuple(pair) if pair[0] != pair[1] else pair[0]
        overrides[host] = chosen if len(chosen) > 1 else chosen[""]
    return written


# --- Player-facing text ------------------------------------------------------------------------------

def host_stone_name(cfg):
    """A host's stone as players read it: by its name where one block hosts twice (deep blackstone,
    besides the Nether one), else by its block."""
    return STONE_NAMES.get(cfg["name"]) or stone_name(cfg["path"])


def switch_lang(hosts, stone_mods):
    """The Modded Stones category's strings: one switch per stone another mod places. Field names follow
    SeamlessOresConfigData: the host's name in camelCase. Create and Blockus both have a limestone, so a
    clashing stone name carries its mod here, where both switches sit in one list."""
    cfg = f"text.autoconfig.{MOD_ID}"
    lang = {f"{cfg}.category.modded_stones": "Modded Stones"}
    placed = hosts.placed()
    paths = [c["path"] for c in placed]
    for c in placed:
        field = camel(c["name"])
        display = stone_mods[c["placed_by"]]["display"]
        clash = f" ({display})" if paths.count(c["path"]) > 1 else ""
        lang[f"{cfg}.option.{field}"] = f"{host_stone_name(c)}{clash}"
        where = display if c["placed_by"] == c["ns"] else f"{display}'s layers of"
        if c.get("adds"):
            lang[f"{cfg}.option.{field}.@Tooltip"] = (
                f"Lets ore form in {where} {host_stone_name(c).lower()}, which ore never reaches otherwise, so"
                f" this ADDS ore. Off by default. Applies to newly generated chunks, from the next world load.")
            continue
        lang[f"{cfg}.option.{field}.@Tooltip"] = (
            f"Ore generated in {where} {host_stone_name(c).lower()} matches the stone. Off: it keeps"
            f" its own look. Applies to newly generated chunks, from the next world load.")
    return lang


def modded_stone_list(hosts, stone_mods, mods, cinnabar_family=None):
    """README lines: the ores in the stones other mods place, by the mod that places them. From the same
    host table the blocks register from, so the README cannot claim a block the jar does not have."""
    placed = hosts.placed()
    built = {}
    for host, cfg, ore, _s, _t in hosts.variants(cinnabar_family):
        if cfg["placed_by"]:
            built.setdefault(host, []).append(ore["key"])
    lines = [f"**{sum(len(v) for v in built.values())} blocks**, plus the dripstone ones listed above. Each exists"
             f" only when the mod that places its stone is installed, and one of another mod's ore only with that"
             f" mod as well. A block's id is `<stone>_<ore>_ore`, from the two columns below: `blockus_limestone`"
             f" and `iron` make `blockus_limestone_iron_ore`.", ""]
    for placer in dict.fromkeys(c["placed_by"] for c in placed):
        stones = [c for c in placed if c["placed_by"] == placer]
        # The game's own rock that a worldgen pack lays (deep blackstone) needs no mod id: a datapack works too.
        requires = "" if placer == "minecraft" else f", requires `{placer}`"
        lines.append(f"**{stone_mods[placer]['display']}{requires}** ({stone_mods[placer]['bands']})")
        lines.append("")
        lines.append("Stones: " + ", ".join(f"{host_stone_name(c)} `{c['name']}`" for c in stones))
        lines.append("")
        lines.append("| Ore | `<ore>` | Also requires | In |")
        lines.append("|---|---|---|---|")
        for ore in hosts.ore_defs:
            within = [host_stone_name(c) for c in stones if ore["key"] in built.get(c["name"], ())]
            if not within:
                continue
            mod = ore.get("mod")
            needs = f"{mods[mod]['display']} `{mod}`" if mod and mod != placer else ""
            where = "every stone" if len(within) == len(stones) and len(stones) > 1 else ", ".join(within)
            lines.append(f"| {title(ore['key'])} | `{ore['key']}` | {needs} | {where} |")
        lines.append("")
    return lines


# --- The Java that is data ---------------------------------------------------------------------------

def write_java(hosts, content_dir, config_java, stone_loaders):
    """ModdedPairs from modded_pairs.json (and the loaders each stone mod's variants register on,
    stone_loaders: mod -> the loader modules its loot ships to); shared/java's OreGeology from geology.py,
    the rule itself; and
    in SeamlessOresConfigData a switch per stone another mod places (the game's own rock has
    hand-written ones, with their own wording) and the push of every host's switch. Returns the number
    of stones with modded pairs."""
    geology.note_absent([o["key"] for o in hosts.ore_defs], list(hosts))

    cases = []
    for host, pairs in hosts.pairs["hosts"].items():
        listed = [o["key"] for o in hosts.ore_defs if o["key"] in pairs]
        cases.append(f'            case "{host}" -> keys({", ".join(chr(34) + k + chr(34) for k in listed)});')
    path = os.path.join(content_dir, "ModdedPairs.java")
    text = open(path, encoding="utf-8").read()
    text = replace_block(text, "        return switch (host) {\n", "            default -> List.of();",
                         "\n".join(cases) + "\n" if cases else "", path)
    # The loaders each stone mod's variants register on: those its loot ships to (stone_loaders).
    ships = []
    for mod in dict.fromkeys(c["placed_by"] for c in hosts.placed()):
        test = " || ".join(f'here.equals("{m}")' for m in stone_loaders[mod])
        ships.append(f'            case "{mod}" -> {test or "false"};')
    text = replace_block(text, "            // BEGIN GENERATED stone loaders (tools/generate_assets.py, from its loot routing)\n",
                         "            // END GENERATED stone loaders", "\n".join(ships) + "\n" if ships else "", path)
    # The stones that add ore (ADDS_ORE_HOSTS): the injector gives them a target of their own.
    adds = [c["id"] for c in hosts.placed() if c["adds"]]
    text = replace_block(text, "            // BEGIN GENERATED adds-ore stones (tools/generate_assets.py, from placed.ADDS_ORE_HOSTS)\n",
                         "            // END GENERATED adds-ore stones",
                         "".join(f'            case "{h}" -> true;\n' for h in adds), path)
    write_text(path, text)

    geology.write_java(write_text)

    fields, push = [], []
    for c in hosts.placed():
        fields += ['    @ConfigEntry.Category("modded_stones")', "    @ConfigEntry.Gui.Tooltip",
                   f"    public boolean {camel(c['name'])} = {'false' if c.get('adds') else 'true'};", ""]
    for c in hosts.values():
        push.append(f'        values.hosts.put("{c["name"]}", {camel(c["name"])});')
    text = open(config_java, encoding="utf-8").read()
    text = replace_block(text, "    // BEGIN GENERATED modded stone switches (tools/generate_assets.py, from the host table)\n",
                         "    // END GENERATED modded stone switches", "\n".join(fields), config_java)
    text = replace_block(text, "        // BEGIN GENERATED host switches (tools/generate_assets.py, from the host table)\n",
                         "        // END GENERATED host switches", "\n".join(push) + "\n", config_java)
    write_text(config_java, text)
    return len(cases)
