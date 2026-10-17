"""Cinnabar ores where Vanilla Backport adds the Sulfur Caves (1.21.1 and 1.20.1): the generator side.

Each cinnabar ore MIRRORS the features of the ore it stands in for: one cinnabar feature per source
feature, with that feature's own vein size, veins per chunk, height range and air exposure, read out of
the game or mod jar of this band. Only the target (cinnabar), the biome (Sulfur Caves) and the vein count
change: the count is TRIPLED, and CinnabarOreFeature keeps each vein with probability cinnabarAmount /
300, so the slider's 100 is exactly the source's count (the 26.x rule, owner 3 Oct 2026).

The configured feature names our ore by id and no block else (CinnabarOreFeature takes cinnabar from the
host table at run time), so no file here names minecraft:cinnabar: without Vanilla Backport the block
does not exist, and a worldgen file naming an absent block is a hard crash. KEEP IN SYNC WITH
CinnabarVeins.SOURCES (shared/eras/1.20.1+1.21.1).
"""
import json
import os
import sys
import zipfile

from assetgen import write_json

MOD_ID = "seamlessores"

# The ores that get a cinnabar variant, by OVERLAY key: Nether gold is also named "gold", its overlay is
# not. KEEP IN SYNC WITH OreType.cinnabarFamily(). 26.2 and up's family, plus the silver, lead and
# antimony of the mods only these bands have (owner, 17 Oct 2026): what forms beside cinnabar in a hot
# spring deposit (gold, silver, pyrite, the lead and zinc sulfides, stibnite), whichever mod it comes from.
FAMILY = {"gold", "iron", "redstone", "zinc", "galena", "techreborn_lead", "techreborn_silver",
          "occultism_silver", "silents_silver", "pyrite", "sphalerite",
          "silver", "iceandfire_silver", "ie_lead", "ie_silver", "oreganized_lead", "oreganized_silver",
          "mi_lead", "antimony", "mek_lead", "dense_lead", "lead"}

# Ore name -> (namespace, [placed feature paths]). Gold's badlands-only extra feature is left out.
SOURCES = {
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
    "silver": ("mythicmetals", ["ore_silver"]),
    "iceandfire_silver": ("iceandfire", ["silver_ore"]),
    "ie_lead": ("immersiveengineering", ["lead"]),
    "ie_silver": ("immersiveengineering", ["silver"]),
    "oreganized_lead": ("oreganized", ["lead_ore", "lead_ore_extra"]),
    "oreganized_silver": ("oreganized", ["silver_ore", "silver_ore_extra"]),
    "mi_lead": ("modern_industrialization", ["ore_generator_lead"]),
    "antimony": ("modern_industrialization", ["ore_generator_antimony"]),
    "mek_lead": ("mekanism", ["ore_lead_normal"]),
    "dense_lead": ("densemekanism", ["dense_lead"]),
    "lead": ("tfmg", ["lead_ore"]),
}

# Modern Industrialization has a stone and a deepslate feature over the SAME height range, each placing
# only in its own rock, so at any height one of them applies: mirroring both would double it in cinnabar.
# Only the stone one is mirrored (Occultism's and Oreganized's pairs cover different heights, so both stay).


def _trapezoid(low, high):
    return {"type": "minecraft:trapezoid", "min_inclusive": low, "max_inclusive": high}


# The sources whose vein size, count and height live in the mod's CODE (its own feature types, read
# from its config defaults), not in a configured feature: (size, discard chance, count, height), read
# from the class files and the same at 1.20.1 and 1.21.1. Immersive Engineering: IEServerConfig.Ores
# .VeinType (lead size 8, -32..80, 12 a chunk; silver size 9, -48..32, 10 a chunk, a quarter discarded
# on air). Mekanism: OreType LEAD "normal" (8 a chunk, a quarter discarded, size 9, bottom-24..64).
IN_CODE = {
    ("immersiveengineering", "lead"): (8, 0.0, 12, _trapezoid({"absolute": -32}, {"absolute": 80})),
    ("immersiveengineering", "silver"): (9, 0.25, 10, _trapezoid({"absolute": -48}, {"absolute": 32})),
    ("mekanism", "ore_lead_normal"): (9, 0.25, 8, _trapezoid({"above_bottom": -24}, {"absolute": 64})),
}

# A source whose jar carries no such feature (its worldgen is in code) gets this stand in.
FALLBACK = {"size": 5, "discard": 0.0, "count": 3,
            "height": {"type": "minecraft:uniform", "min_inclusive": {"above_bottom": 0},
                       "max_inclusive": {"absolute": 96}}}
SLIDER_FACTOR = 3
# The game's own cap on a placement count (CountPlacement, 0 to 256): a vein whose tripled count would pass
# it keeps its own count and factor 1, so the slider tops out at 100 for that one (iron_upper: 90).
COUNT_MAX = 256

# The tag the game rock's biome is attached by on each loader's biome modifier: Vanilla Backport puts
# its Sulfur Caves in c:is_cave on NeoForge 1.21.1 and in forge:is_cave on Forge 1.20.1. The feature
# tests the biome itself, so the other cave biomes in the tag place nothing.
KEEPS_ORE_OUT = {"values": [{"id": "minecraft:sulfur", "required": False},
                            {"id": "minecraft:cinnabar", "required": False}]}


def count_max(count):
    """The largest value a placement count provider can give."""
    if isinstance(count, int):
        return count
    if isinstance(count, dict) and count.get("type") == "minecraft:uniform":
        return count.get("value", count)["max_inclusive"]     # 1.20.1 nests the range under value
    sys.exit(f"  !! cannot read count provider {count}: add it to count_max")


def scaled_count(count, factor):
    """A placement count provider times factor: a constant, or a uniform range scaled at both ends."""
    if isinstance(count, int):
        return count * factor
    if isinstance(count, dict) and count.get("type") == "minecraft:uniform":
        if "value" in count:     # 1.20.1 nests the range under value
            return {**count, "value": scaled_count({"type": count["type"], **count["value"]}, factor)}
        return {**count, "min_inclusive": count["min_inclusive"] * factor,
                "max_inclusive": count["max_inclusive"] * factor}
    sys.exit(f"  !! cannot scale count provider {count}: add it to scaled_count")


def read_source(jar_path, namespace, path):
    """(feature size, discard chance, placement list) of one source placed feature, or None."""
    if not jar_path or not os.path.exists(jar_path):
        return None
    with zipfile.ZipFile(jar_path) as jar:
        try:
            source = json.loads(jar.read(f"data/{namespace}/worldgen/placed_feature/{path}.json"))
        except KeyError:
            return None
        feature_ns, feature_path = source["feature"].split(":", 1)
        try:
            feature = json.loads(jar.read(f"data/{feature_ns}/worldgen/configured_feature/{feature_path}.json"))
        except KeyError:
            return None
    config = feature.get("config", feature)
    return config["size"], config.get("discard_chance_on_air_exposure", 0.0), source["placement"]


def _clear(folder):
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            if f.startswith("cinnabar_"):
                os.remove(os.path.join(folder, f))


def write(variants, name_of, gate_of, jars, data_dir, modifier_dir_of, modifier_type, biome_tag, conditions_key,
          tags_dir=("tags", "block")):
    """Every cinnabar variant's mirrored veins, and one biome modifier each (NeoForge or Forge).

    variants: (host, host cfg, ore def, source form, tier); jars: namespace -> jar path (the game's own
    under "minecraft"); data_dir: our data/seamlessores; modifier_dir_of(gate): the loader's
    biome_modifier folder for a variant of that gate (1.20.1 Forge: the gate's own built-in datapack);
    conditions_key: the loader's key for load conditions on a biome modifier, or None; tags_dir: the
    band's block tag folder (plural at 1.20.1). Returns [(variant name, placed feature id)] and a report.
    """
    _clear(os.path.join(data_dir, "worldgen", "configured_feature"))
    _clear(os.path.join(data_dir, "worldgen", "placed_feature"))
    cleared = set()
    written = []
    report = []
    for host, host_cfg, ore, _source, _tier in variants:
        if host_cfg["tier"] != "cinnabar":
            continue
        name = name_of(host, ore)
        gate = gate_of(host_cfg, ore)
        modifier_dir = modifier_dir_of(gate)     # None: the loader carries none of this gate's mods
        if modifier_dir is not None and modifier_dir not in cleared:
            _clear(modifier_dir)
            cleared.add(modifier_dir)
        namespace, sources = SOURCES[ore["name"]]
        for source in sources:
            key = f"cinnabar_{ore['name']}_{source}"
            in_code = IN_CODE.get((namespace, source))
            found = None if in_code else read_source(jars.get(namespace), namespace, source)
            if in_code:
                size, discard, count, height = in_code
                placement = [{"type": "minecraft:count", "count": count},
                             {"type": "minecraft:in_square"},
                             {"type": "minecraft:height_range", "height": height},
                             {"type": "minecraft:biome"}]
                report.append(f"{key}: size {size}, discard {discard}, {count}, {json.dumps(height)} (from code)")
            elif found is None:
                if namespace == "minecraft":
                    sys.exit(f"  !! {namespace}:{source} not found in the game jar")
                fb = FALLBACK
                size, discard = fb["size"], fb["discard"]
                placement = [{"type": "minecraft:count", "count": fb["count"]},
                             {"type": "minecraft:in_square"},
                             {"type": "minecraft:height_range", "height": fb["height"]},
                             {"type": "minecraft:biome"}]
                report.append(f"{key}: stand-in (no {namespace}:{source} in its jar)")
            else:
                size, discard, placement = found
                report.append(f"{key}: size {size}, discard {discard}, "
                              + ", ".join(json.dumps(p.get("count", p.get("height")))
                                          for p in placement if p["type"] in ("minecraft:count", "minecraft:height_range")))
            # A mod's own placement filter (Create's config_filter) names a type that exists only with that
            # mod, and would break every world without it: dropped, and CinnabarOreFeature tests our
            # switch for that mod instead.
            dropped = [p["type"] for p in placement if not p["type"].startswith("minecraft:")]
            if dropped:
                report.append(f"    {key}: dropped {dropped}, gated by our own switch for {namespace}")
            placement = [dict(p) for p in placement if p["type"].startswith("minecraft:")]
            counts = [p for p in placement if p.get("type") == "minecraft:count"]
            if not counts:
                sys.exit(f"  !! {namespace}:{source} has no count modifier to scale")
            factor = SLIDER_FACTOR if all(count_max(p["count"]) * SLIDER_FACTOR <= COUNT_MAX for p in counts) else 1
            if factor == 1:
                report.append(f"    {key}: count would pass {COUNT_MAX} tripled, kept at factor 1")
            for p in counts:
                p["count"] = scaled_count(p["count"], factor)
            if not any(p.get("type") == "minecraft:biome" for p in placement):
                placement.append({"type": "minecraft:biome"})
            write_json(os.path.join(data_dir, "worldgen", "configured_feature", f"{key}.json"),
                       {"type": f"{MOD_ID}:cinnabar_ore",
                        "config": {"size": size, "discard_chance_on_air_exposure": discard,
                                   "ore": f"{MOD_ID}:{name}", "factor": factor}})
            write_json(os.path.join(data_dir, "worldgen", "placed_feature", f"{key}.json"),
                       {"feature": f"{MOD_ID}:{key}", "placement": placement})
            modifier = {"type": modifier_type, "biomes": biome_tag, "features": f"{MOD_ID}:{key}",
                        "step": "underground_ores"}
            if conditions_key:
                modifier[conditions_key] = [{"type": "neoforge:mod_loaded", "modid": m} for m in gate]
            if modifier_dir is not None:
                write_json(os.path.join(modifier_dir, f"{key}.json"), modifier)
            written.append((name, f"{MOD_ID}:{key}"))
    write_json(os.path.join(data_dir, *tags_dir, "keeps_ore_out.json"), KEEPS_ORE_OUT)
    return written, report
