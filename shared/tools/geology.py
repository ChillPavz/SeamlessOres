"""The geology rule: which ore never forms in which host rock. One rule, two tables, by kind of host.

FIXED, for the stones other mods place (Blockus' limestone, Create's strata, ...): a refused pair is
never built, and worldgen turns that ore into the stone wherever the stone swallows it, so no seam can
appear. Not configurable: nothing registry-side may depend on config. The strict reading, plus a lore
rule for Create's four invented stones (the owner's choice: "be very strict, the more we cut the better").

OPTIONAL, for the game's own granite, diorite, andesite and tuff: the "Geology (removes ore)" option,
default off. Every block stays registered; with the option on, the rock stays rock where the ore would
have gone. The lenient reading: only what geology rules out plainly.

Host keys are HostStone.name(), ore keys OreType.key(). A band's tools/generate_assets.py writes OreGeology.java
from this file, and reads it for the blocks it generates.
"""

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


def java(fixed_hosts, optional_hosts, ores):
    """OreGeology.java: both tables, among the given host names and ore keys, as lookups."""
    def table(hosts, rule):
        rows = []
        for host in hosts:
            refused = [o for o in ores if rule(host, o)]
            if refused:
                rows.append('            Map.entry("%s", Set.of(%s))' % (host, ", ".join('"%s"' % o for o in refused)))
        return ",\n".join(rows)
    return JAVA % (table(fixed_hosts, fixed), table(optional_hosts, optional))


JAVA = '''package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Map;
import java.util.Set;

/**
 * The geology rule: the ores that never form in a host rock. One rule, two tables, by kind of host.
 *
 * <p><b>Fixed</b>, for the stones other mods place: a refused pair is never registered, and worldgen
 * turns that ore into the stone wherever the stone swallows it, so no seam can appear. Never
 * configurable: the registered block set must not depend on config.
 *
 * <p><b>Optional</b>, for the game's own granite, diorite, andesite and tuff: the geology option, off
 * by default because it REMOVES ore. Every block stays registered; with the option on, where the ore
 * feature would have placed a refused ore the rock stays rock.
 *
 * <p>GENERATED by tools/generate_assets.py from shared/tools/geology.py, which gives the reasons. Do not edit.
 */
public final class OreGeology {

    private OreGeology() {}

    /** Host name ({@link HostStone#name()}) -> ore keys ({@link OreType#key()}) never built there. */
    private static final Map<String, Set<String>> FIXED = Map.ofEntries(
%s);

    /** Host name -> ore keys the geology option refuses there. */
    private static final Map<String, Set<String>> OPTIONAL = Map.ofEntries(
%s);

    /** Whether this ore never forms in this stone another mod places: no variant, worldgen makes it stone. */
    public static boolean fixed(String host, String ore) {
        return FIXED.getOrDefault(host, Set.of()).contains(ore);
    }

    /**
     * What an ore target for {@code variant} places: our block, or, with the option on and the pair
     * refused, the host rock itself (the ore is removed).
     */
    public static BlockState placed(OreVariant variant, Block ours) {
        return SeamlessOresConfig.geology
                && OPTIONAL.getOrDefault(variant.host().name(), Set.of()).contains(variant.ore().key())
                ? variant.host().block().defaultBlockState()
                : ours.defaultBlockState();
    }
}
'''
