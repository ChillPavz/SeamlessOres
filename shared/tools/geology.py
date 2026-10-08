"""The geology rule: which ore never forms in which host rock. One rule, two tables, by kind of host.

FIXED, for the stones other mods place (Blockus' limestone, Create's strata, ...): a refused pair is
never built, and worldgen turns that ore into the stone wherever the stone swallows it, so no seam can
appear. Not configurable: nothing registry-side may depend on config. The strict reading, plus a lore
rule for Create's four invented stones (the owner's choice: "be very strict, the more we cut the better").

OPTIONAL, for the game's own granite, diorite, andesite and tuff: the "Geology (removes ore)" option,
default off. Every block stays registered; with the option on, the rock stays rock where the ore would
have gone. The lenient reading: only what geology rules out plainly.

Host keys are HostStone.name(), ore keys OreType.key(). Every band's tools/generate_assets.py writes the
one shared/java OreGeology.java from this file (write_java), and reads it for the blocks it generates.
"""

import os

# --- FIXED: the stones other mods place ------------------------------------------------------------

CLASSES = {
    "LIME": ["blockus_limestone", "create_limestone"],
    "CALC": ["minecraft_calcite"],
    "ASPH": ["promenade_asphalt"],
    "MARB": ["blockus_marble"],
    "SCH": ["mythicupgrades_%s_schist" % g for g in ("aquamarine", "citrine", "peridot", "topaz")],
    "PLUT": ["wilderwild_gabbro", "blockus_bluestone"],
    "VOLC": ["minecraft_smooth_basalt", "create_scoria"],
}
ALL = list(CLASSES)


def _hosts(*classes):
    return [h for c in classes for h in CLASSES[c]]


_TIN = _hosts("CALC", "ASPH", "SCH", "PLUT", "VOLC")
_BERYL = _hosts("LIME", "CALC", "ASPH", "MARB", "PLUT", "VOLC")
_PERIDOT = _hosts("LIME", "CALC", "ASPH", "MARB", "SCH")
_CORUNDUM = _hosts("LIME", "CALC", "ASPH", "PLUT")
_PGM = _hosts("LIME", "CALC", "ASPH", "MARB", "SCH", "VOLC")

# ore -> hosts it is refused in
STRICT = {
    "coal": _hosts("CALC", "MARB", "SCH", "PLUT", "VOLC"),
    "emerald": _hosts("ASPH", "PLUT", "VOLC"),
    "lapis": _hosts("LIME", "ASPH", "SCH", "PLUT", "VOLC"),
    "diamond": _hosts(*ALL), "bort": _hosts(*ALL),
    "topaz": _hosts(*ALL), "silents_topaz": _hosts(*ALL),
    "zinc": _hosts("PLUT"), "galena": _hosts("PLUT"), "techreborn_lead": _hosts("PLUT"),
    "manganese": _hosts("PLUT"),
    "tin": _TIN, "energized_tin": _TIN, "techreborn_tin": _TIN,
    "aquamarine": _BERYL, "silents_aquamarine": _BERYL, "heliodor": _BERYL,
    "peridot": _PERIDOT, "silents_peridot": _PERIDOT,
    "techreborn_ruby": _CORUNDUM, "techreborn_sapphire": _CORUNDUM,
    "platinum": _PGM, "iridium": _PGM, "osmium": _PGM,
    "techreborn_uranium": _hosts("PLUT", "VOLC"),
}

# Invented ores and rock are never judged; nor is anything on an exempt host or in the Nether.
FICTION = set("redstone adamantite aquarium banglum carmot kyber midas_gold morkite mythril necoium "
              "nether_banglum orichalcum palladium prometheum quadrillum runite starrite stormyx "
              "unobtainium chaos prosperity".split())

# Create's four invented stones each keep only the ore Create ties them to, plus fiction (owner).
LORE = {"create_asurine": "zinc", "create_crimsite": "iron", "create_ochrum": "gold",
        "create_veridium": "copper"}


def fixed(host, ore):
    """Whether a stone another mod places never holds this ore: no variant, and worldgen makes it stone."""
    if host in STRICT.get(ore, ()):
        return True
    keep = LORE.get(host)
    return keep is not None and ore != keep and ore not in FICTION


# --- OPTIONAL: the game's own rock ---------------------------------------------------------------

_PLUTONIC = ["granite", "diorite"]
_IGNEOUS = ["granite", "diorite", "andesite"]
_GRANITE = ["granite"]

# ore -> hosts it is refused in, with the option on
LENIENT = {
    # Coal needs a swamp; granite and diorite never had one. Ash falls on coal swamps, so tuff keeps
    # it, and andesite rarely (lava over a coal basin).
    "coal": _PLUTONIC,
    # Diamond needs a kimberlite pipe. Its crater is pyroclastic, so tuff keeps it.
    "diamond": _IGNEOUS, "white_diamond": _IGNEOUS, "black_diamond": _IGNEOUS, "bort": _IGNEOUS,
    # Ammolite is fossil shell; tuff keeps it (found beside ash beds).
    "ammolite": _IGNEOUS,
    # Corundum and olivine never coexist with free quartz.
    "silents_ruby": _GRANITE, "silents_sapphire": _GRANITE,
    "techreborn_ruby": _GRANITE, "techreborn_sapphire": _GRANITE,
    "peridot": _GRANITE, "silents_peridot": _GRANITE,
    # Nickel and the platinum group are mafic to ultramafic.
    "nickel": _GRANITE, "platinum": _GRANITE, "iridium": _GRANITE, "osmium": _GRANITE,
    "dense_osmium": _GRANITE,
}


def optional(host, ore):
    """Whether the geology option, when on, refuses this ore in this rock of the game's own."""
    return host in LENIENT.get(ore, ())


def note_absent(keys, hosts):
    """Prints the ores and stones this rule names that a band does not have. The rule serves every
    band, so most bands lack some; the list is printed, not refused, so a misspelt key still shows."""
    ores = set(STRICT) | set(LENIENT)
    stones = set(h for hs in STRICT.values() for h in hs) | set(LORE) | set(h for hs in LENIENT.values() for h in hs)
    absent_ores, absent_stones = sorted(ores - set(keys)), sorted(stones - set(hosts))
    if absent_ores or absent_stones:
        print(f"  geology rule, not in this band: {len(absent_ores)} ores {absent_ores},"
              f" {len(absent_stones)} stones {absent_stones}")


SHARED_JAVA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "java", "com",
                           "chillpavz", "seamlessores", "content", "OreGeology.java")


def _map_of_sets(rule, indent):
    rows = ['%sMap.entry("%s", Set.of(%s))' % (indent, key, ", ".join('"%s"' % v for v in values))
            for key, values in rule.items()]
    return ",\n".join(rows)


def java():
    """OreGeology.java: this rule, written as Java. Minecraft-free and the same for every band, so it
    lives once in shared/java; a band asks it by host name and ore key and never lists its own."""
    return JAVA % (_map_of_sets(STRICT, " " * 12),
                   ",\n".join('            Map.entry("%s", "%s")' % kv for kv in LORE.items()),
                   ", ".join('"%s"' % f for f in sorted(FICTION)),
                   _map_of_sets(LENIENT, " " * 12))


def write_java(write_text):
    """Writes shared/java's OreGeology.java with the caller's writer (assetgen.write_text: LF)."""
    write_text(SHARED_JAVA, java())


JAVA = '''package com.chillpavz.seamlessores.content;

import java.util.Map;
import java.util.Set;

/**
 * The geology rule: the ores that never form in a host rock. One rule, two tables, by kind of host.
 *
 * <p><b>Fixed</b>, for the stones other mods place: a refused pair is never registered, and worldgen
 * turns that ore into the stone wherever the stone swallows it, so no seam can appear. Never
 * configurable: the registered block set must not depend on config. The strict reading, plus a lore
 * rule for Create's four invented stones: each keeps only the ore Create ties it to, and fiction.
 *
 * <p><b>Optional</b>, for the game's own granite, diorite, andesite and tuff: the geology option, off
 * by default because it REMOVES ore. Every block stays registered; with the option on, where the ore
 * feature would have placed a refused ore the rock stays rock.
 *
 * <p>Asked by host name ({@code HostStone.name()}) and ore key ({@code OreType.key()}), so it is the same
 * in every band, whatever ores and stones a band has.
 *
 * <p>GENERATED by shared/tools/geology.py, which gives the reasons. Do not edit.
 */
public final class OreGeology {

    private OreGeology() {}

    /** Ore key -> the stones other mods place that it never forms in. */
    private static final Map<String, Set<String>> STRICT = Map.ofEntries(
%s);

    /** Create's invented stones -> the one real ore each keeps. */
    private static final Map<String, String> LORE = Map.ofEntries(
%s);

    /** Invented ores, never judged by geology. */
    private static final Set<String> FICTION = Set.of(%s);

    /** Ore key -> the game's own rocks the geology option refuses it in. */
    private static final Map<String, Set<String>> LENIENT = Map.ofEntries(
%s);

    /** Whether this ore never forms in this stone another mod places: no variant, worldgen makes it stone. */
    public static boolean fixed(String host, String ore) {
        if (STRICT.getOrDefault(ore, Set.of()).contains(host)) {
            return true;
        }
        final String keep = LORE.get(host);
        return keep != null && !keep.equals(ore) && !FICTION.contains(ore);
    }

    /** Whether the geology option, when on, refuses this ore in this rock of the game's own. */
    public static boolean optional(String host, String ore) {
        return LENIENT.getOrDefault(ore, Set.of()).contains(host);
    }
}
'''
