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

# Exempt, never judged: dripstone block (a speleothem), the Nether stones (scorchia, Twigs' bloodstone,
# Mythic Upgrades' sapphire schist) and the invented ones (Forbidden and Arcanus' darkstone, Blockus'
# viridite, Promenade's blunite).
CLASSES = {
    # sedimentary carbonate; Spawn's reefstone is reef limestone
    "LIME": ["blockus_limestone", "create_limestone", "meadow_limestone", "spawn_reefstone"],
    "CALC": ["minecraft_calcite"],
    # sedimentary hydrocarbon: asphalt, and TFMG's lignite (brown coal)
    "ASPH": ["promenade_asphalt", "tfmg_lignite"],
    "MARB": ["blockus_marble"],
    # metamorphic pelite
    "SCH": ["mythicupgrades_%s_schist" % g for g in ("aquamarine", "citrine", "peridot", "topaz")] + ["twigs_schist"],
    # mafic intrusive; bluestone read as dolerite
    "PLUT": ["wilderwild_gabbro", "blockus_bluestone"],
    # mafic volcanic
    # mafic volcanic; deep blackstone is the blackstone Terralith lays in its caves
    "VOLC": ["minecraft_smooth_basalt", "create_scoria", "minecraft_blackstone"],
    # felsic volcanic: Twigs' rhyolite
    "FELS": ["twigs_rhyolite"],
    # residual laterite: TFMG's bauxite, the weathering crust aluminium is mined from
    "LATE": ["tfmg_bauxite"],
    # massive sulphide: TFMG's galena, a lead-zinc ore body as rock
    "SULF": ["tfmg_galena"],
    # black shale and argillite (organic-rich sedimentary pelite): Born in Chaos' black argillite
    "SHAL": ["born_in_chaos_v1_black_argillite"],
}
ALL = list(CLASSES)


def _hosts(*classes):
    return [h for c in classes for h in CLASSES[c]]


def _all_but(*kept):
    return _hosts(*(c for c in ALL if c not in kept))


# Each family: the ore keys of one mineral, whatever mod they come from, and the hosts it is refused
# in. The reason is on each line; som-geology-rules in the maintainer notes holds the full table.
FAMILIES = [
    # Coal needs a swamp: limestone (coal measures sit on carbonate platforms), the hydrocarbons, and the
    # black shale the seams lie between keep it.
    (["coal", "lignite_coal"], _all_but("LIME", "ASPH", "SHAL")),
    # Colombian emerald is in black shale and carbonate; schist emerald is the classic pegmatite contact.
    (["emerald"], _hosts("ASPH", "PLUT", "VOLC", "FELS", "LATE", "SULF")),
    # Lazurite rock is lazurite with calcite: marble and calcite only.
    (["lapis"], _hosts("LIME", "ASPH", "SCH", "PLUT", "VOLC", "FELS", "LATE", "SULF", "SHAL")),
    # A kimberlite pipe, which none of these is.
    (["diamond", "bort", "white_diamond", "black_diamond"], _hosts(*ALL)),
    # Topaz rhyolite (Thomas Range, Utah) is THE topaz host; nothing else here.
    (["topaz", "silents_topaz"], _all_but("FELS")),
    # Lead, zinc and antimony: carbonate, shale, schist and epithermal veins in volcanics; never in a
    # mafic intrusion, never in a weathering crust. Massive sulphide is their own rock.
    (["zinc", "galena", "techreborn_lead", "lead", "mi_lead", "ie_lead", "mek_lead", "dense_lead",
      "oreganized_lead", "antimony"], _hosts("PLUT", "LATE")),
    # Manganese also forms in laterite.
    (["manganese"], _hosts("PLUT")),
    # Carbonate replacement tin, and rhyolite-hosted tin (Durango).
    (["tin", "energized_tin", "techreborn_tin", "mi_tin", "mek_tin", "dense_tin"],
     _all_but("LIME", "MARB", "FELS")),
    # Beryl in mica schist.
    (["aquamarine", "silents_aquamarine", "heliodor"], _all_but("SCH")),
    # Olivine: mafic rock only.
    (["peridot", "silents_peridot"], _all_but("PLUT", "VOLC")),
    # Corundum never coexists with free quartz: marble (Mogok), schist, basalt sapphire.
    (["techreborn_ruby", "techreborn_sapphire", "silents_ruby", "silents_sapphire", "iceandfire_sapphire"],
     _all_but("MARB", "SCH", "VOLC")),
    # Platinum group and nickel: mafic intrusions (Noril'sk, Bushveld, Sudbury).
    (["platinum", "iridium", "osmium", "mi_iridium", "mek_osmium", "dense_osmium",
      "nickel", "mi_nickel", "ie_nickel"], _all_but("PLUT")),
    # Uranium: asphaltite, carbonate, schist and rhyolite caldera uranium are real; not in mafic rock,
    # not in a laterite, not in a lead-zinc body. Extreme Reactors' yellorite is its uranium ore.
    (["techreborn_uranium", "uranium", "ie_uranium", "mek_uranium", "dense_uranium", "yellorite",
      "uraninite", "uraninite_poor", "uraninite_dense"], _hosts("PLUT", "VOLC", "LATE", "SULF")),
    # Rock salt is an evaporite, laid down with carbonate.
    (["salt"], _all_but("LIME")),
    # Fluorite: Mississippi Valley carbonate, skarn marble, calcite veins, rhyolite (Mexico), lead-zinc gangue.
    (["dense_fluorite", "mek_fluorite"], _hosts("ASPH", "SCH", "PLUT", "VOLC", "LATE", "SHAL")),
    # Scheelite skarn at limestone and marble contacts, and scheelite in schist.
    (["tungsten"], _all_but("LIME", "MARB", "SCH")),
    # Monazite and thorium: metamorphic monazite in pelitic schist.
    (["monazite", "thorium"], _all_but("SCH")),
    # Lithium: clays from rhyolite (Thacker Pass) and spodumene pegmatite in schist belts.
    (["lithium"], _all_but("FELS", "SCH")),
    # Garnet: schist, skarn marble, rhyolite (spessartine).
    (["garnet"], _all_but("SCH", "MARB", "FELS")),
    # Kyanite, cordierite (iolite), chrysoberyl (alexandrite) and rose quartz pegmatite: pelitic schist.
    (["kyanite", "iolite", "alexandrite", "rose_quartz"], _all_but("SCH")),
    # Tanzanite (zoisite): Merelani's graphitic schist and marble.
    (["tanzanite"], _all_but("SCH", "MARB")),
    # Turquoise: supergene, over altered volcanics and sulphides, in the weathering profile.
    (["turquoise"], _all_but("FELS", "LATE", "SULF")),
    # Opal: rhyolite fire opal, and the deep weathering profile (Australia).
    (["opal"], _all_but("FELS", "LATE")),
    # Carnelian (chalcedony) fills vesicles in lava.
    (["carnelian"], _all_but("VOLC", "FELS")),
    # Ammolite is fossil shell (the Bearpaw shale); pearl is reef; moldavite (tektite) lies in sediments.
    (["ammolite"], _all_but("LIME", "SHAL")),
    (["pearl"], _all_but("LIME")),
    (["moldavite"], _all_but("LIME", "CALC", "ASPH", "LATE")),
]

# ore -> hosts it is refused in
STRICT = {key: hosts for keys, hosts in FAMILIES for key in keys}
if len(STRICT) != sum(len(keys) for keys, _hosts_ in FAMILIES):
    raise SystemExit("geology.py: an ore key is in two families")

# Invented ores and rock are never judged; nor is anything on an exempt host or in the Nether.
FICTION = set("redstone adamantite aquarium banglum carmot kyber midas_gold morkite mythril necoium "
              "nether_banglum orichalcum palladium prometheum quadrillum runite starrite stormyx "
              "unobtainium chaos prosperity inferium gleaming experience nether_experience soulstone "
              "brilliant blazing_quartz dawn_stone dusk_stone fire_stone ice_stone leaf_stone moon_stone "
              "shiny_stone sun_stone thunder_stone water_stone".split())

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
    "coal": _PLUTONIC, "lignite_coal": _PLUTONIC,
    # Salt is an evaporite: sedimentary only, so none of the four keeps it.
    "salt": ["granite", "diorite", "andesite", "tuff"],
    # Diamond needs a kimberlite pipe. Its crater is pyroclastic, so tuff keeps it.
    "diamond": _IGNEOUS, "white_diamond": _IGNEOUS, "black_diamond": _IGNEOUS, "bort": _IGNEOUS,
    # Ammolite is fossil shell; tuff keeps it (found beside ash beds).
    "ammolite": _IGNEOUS,
    # Corundum and olivine never coexist with free quartz.
    "silents_ruby": _GRANITE, "silents_sapphire": _GRANITE,
    "techreborn_ruby": _GRANITE, "techreborn_sapphire": _GRANITE, "iceandfire_sapphire": _GRANITE,
    "peridot": _GRANITE, "silents_peridot": _GRANITE,
    # Nickel and the platinum group are mafic to ultramafic.
    "nickel": _GRANITE, "mi_nickel": _GRANITE, "ie_nickel": _GRANITE,
    "platinum": _GRANITE, "iridium": _GRANITE, "mi_iridium": _GRANITE,
    "osmium": _GRANITE, "dense_osmium": _GRANITE, "mek_osmium": _GRANITE,
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
