"""The geology rule: which ore never forms in which host rock.

FIXED, for the stones other mods place (Blockus' limestone, Create's strata, ...): a refused pair is
never built, and worldgen turns that ore into the stone wherever the stone swallows it, so no seam can
appear. Not configurable: nothing registry-side may depend on config. The strict reading, plus a lore
rule for Create's four invented stones (the owner's choice: "be very strict, the more we cut the better"),
and a lore rule for Cobblemon's evolution stones (COBBLEMON_KEEPS, COBBLEMON_LORE).

THE GAME'S OWN ROCK (granite, diorite, andesite, tuff, dripstone, and the Nether's basalt and blackstone),
by the same strict reading (ROCK, below). A MODDED ore refused there is FIXED like the above: never built
(an id an earlier release built is retired, RetiredBlocks), and worldgen keeps the rock. A VANILLA ore
refused there is OPTIONAL: the "Geology (removes ore)" option, default off; every vanilla block stays
registered, and with the option on the rock stays rock where the ore would have gone (owner, 20 Oct 2026).

Host keys are HostStone.name(), ore keys OreType.key(). Every band's tools/generate_assets.py writes the
one shared/java OreGeology.java from this file (write_java), and reads it for the blocks it generates.
"""

import os

# --- FIXED: the stones other mods place ------------------------------------------------------------

# Exempt, never judged for REAL ores: dripstone block (a speleothem; invented ores follow their lore's
# dripstone). The invented stones are classed below CLASSES, by what their own mods make them.
CLASSES = {
    # sedimentary carbonate; Spawn's reefstone is reef limestone
    "LIME": ["blockus_limestone", "create_limestone", "meadow_limestone", "spawn_reefstone",
             "regions_unexplored_chalk", "quark_limestone"],
    "CALC": ["minecraft_calcite"],
    # sedimentary hydrocarbon: asphalt, and TFMG's lignite (brown coal)
    "ASPH": ["promenade_asphalt", "tfmg_lignite"],
    "MARB": ["blockus_marble", "embellishcraft_marble"],
    # metamorphic pelite
    # EmbellishCraft's slate is the same pelite at low grade
    "SCH": ["mythicupgrades_%s_schist" % g for g in ("aquamarine", "citrine", "peridot", "topaz")] + ["twigs_schist",
                                                                                                    "embellishcraft_slate"],
    # mafic intrusive; bluestone read as dolerite
    "PLUT": ["wilderwild_gabbro", "blockus_bluestone"],
    # mafic volcanic
    # mafic volcanic; deep blackstone is the blackstone Terralith lays in its caves
    "VOLC": ["minecraft_smooth_basalt", "create_scoria", "minecraft_blackstone", "embellishcraft_basalt"],
    # felsic volcanic: Twigs' rhyolite
    "FELS": ["twigs_rhyolite", "biomeswevegone_dacite", "biomeswevegone_white_dacite"],
    # residual laterite: TFMG's bauxite, the weathering crust aluminium is mined from
    "LATE": ["tfmg_bauxite"],
    # massive sulphide: TFMG's galena, a lead-zinc ore body as rock
    "SULF": ["tfmg_galena"],
    # black shale and argillite (organic-rich sedimentary pelite): Born in Chaos' black argillite
    "SHAL": ["born_in_chaos_v1_black_argillite", "regions_unexplored_argillite", "quark_shale"],
    # serpentinite and the jadeitite / nephrite that forms from it (owner, 21 Oct 2026): EmbellishCraft's jade
    "SERP": ["embellishcraft_jade"],
    # chert and jasper, silica sedimentary (owner, 22 Oct 2026): Quark's jasper. Banded iron formation
    # (jaspilite) and the sea-floor exhalative beds: iron, manganese, copper, lead-zinc, gold, and fiction.
    "CHRT": ["quark_jasper"],
    # red-bed sandstone (owner, 22 Oct 2026): Oh The Biomes We've Gone's red rock. Hematite-cemented continental
    # sandstone: iron, red-bed copper, roll-front uranium and vanadium (Colorado Plateau), lead-zinc, gold, salt.
    "RBED": ["biomeswevegone_red_rock"],
}
# INVENTED STONES ARE JUDGED TOO (owner, 22 Oct 2026; so-fiction-lore-rule): each is read as the rock its own
# mod frames it as. Create's scorchia is black-dyed scoria and Twigs' bloodstone lies in the basalt deltas
# (volcanic); Forbidden and Arcanus' darkstone floors the world at bedrock and Promenade calls blunite an
# "igneous rock" (plutonic, as bluestone); Blockus' viridite is a dark green deep rock (serpentinite); Mythic
# Upgrades names its Nether rift stones schist. Create's four strata keep their LORE, the End's gem schist its own.
for _host, _class in {"create_scorchia": "VOLC", "twigs_bloodstone": "VOLC", "forbidden_arcanus_darkstone": "PLUT",
                      "promenade_blunite": "PLUT", "blockus_viridite": "SERP",
                      "mythicupgrades_ruby_schist": "SCH", "mythicupgrades_sapphire_schist": "SCH"}.items():
    CLASSES[_class].append(_host)
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
    (["emerald"], _hosts("ASPH", "PLUT", "VOLC", "FELS", "LATE", "SULF", "SERP", "CHRT", "RBED")),
    # Lazurite rock is lazurite with calcite: marble and calcite only.
    (["lapis"], _hosts("LIME", "ASPH", "SCH", "PLUT", "VOLC", "FELS", "LATE", "SULF", "SHAL", "SERP", "CHRT", "RBED")),
    # A kimberlite pipe, which none of these is.
    # Born in Chaos' infected diamond is diamond, whatever lives in it.
    (["diamond", "bort", "white_diamond", "black_diamond", "infected_diamond"], _hosts(*ALL)),
    # Topaz rhyolite (Thomas Range, Utah) is THE topaz host; nothing else here.
    (["topaz", "silents_topaz"], _all_but("FELS")),
    # Black (smoky) quartz grows in granite pegmatite and in schist veins (Actually Additions).
    (["black_quartz"], _all_but("FELS", "PLUT", "SCH")),
    # Amethyst lines geodes in lava and rhyolite, and veins in granite and carbonate (Ores Above Diamonds).
    (["amethyst", "nether_amethyst"], _all_but("VOLC", "FELS", "PLUT", "LIME")),
    # Jade (jadeite, nephrite) forms from serpentinite and in high-pressure schist (Sullys, Epic Paladins).
    (["sullysmod_jade", "epicpaladins_jade"], _all_but("SERP", "SCH")),
    # Titanium (ilmenite, rutile): mafic intrusions and lava, rutile schist, placer sands in red beds.
    (["tankdefenses_titanium"], _all_but("PLUT", "VOLC", "SCH", "RBED")),
    # Native sulphur: volcanic fumaroles, and the caps of salt domes over carbonate and sulphide (Scorched Guns).
    (["scguns_sulfur", "scguns_nether_sulfur"], _all_but("VOLC", "FELS", "LIME", "SULF")),
    # Sal ammoniac: fumaroles, and burning coal seams in shale and asphalt (Theurgy).
    (["sal_ammoniac"], _all_but("VOLC", "FELS", "ASPH", "SHAL")),
    # Lead, zinc and antimony: carbonate, shale, schist and epithermal veins in volcanics; never in a
    # mafic intrusion, never in a weathering crust. Massive sulphide is their own rock.
    (["zinc", "galena", "techreborn_lead", "lead", "mi_lead", "ie_lead", "mek_lead", "dense_lead",
      "oreganized_lead", "antimony", "embers_lead", "superbwarfare_galena"], _hosts("PLUT", "LATE", "SERP")),
    # Manganese also forms in laterite.
    (["manganese"], _hosts("PLUT", "SERP", "RBED")),
    # Carbonate replacement tin, and rhyolite-hosted tin (Durango).
    (["tin", "energized_tin", "techreborn_tin", "mi_tin", "mek_tin", "dense_tin"],
     _all_but("LIME", "MARB", "FELS")),
    # Beryl in mica schist.
    (["aquamarine", "silents_aquamarine", "heliodor"], _all_but("SCH")),
    # Olivine: mafic rock only, and the serpentinite it alters to.
    (["peridot", "silents_peridot"], _all_but("PLUT", "VOLC", "SERP")),
    # Corundum never coexists with free quartz: marble (Mogok), schist, basalt sapphire.
    (["techreborn_ruby", "techreborn_sapphire", "silents_ruby", "silents_sapphire", "iceandfire_sapphire"],
     _all_but("MARB", "SCH", "VOLC")),
    # Platinum group and nickel: mafic intrusions (Noril'sk, Bushveld, Sudbury) and serpentinite (laterite
    # nickel, placer platinum).
    (["platinum", "iridium", "osmium", "mi_iridium", "mek_osmium", "dense_osmium",
      "nickel", "mi_nickel", "ie_nickel", "createpropulsion_platinum"], _all_but("PLUT", "SERP")),
    # Uranium: asphaltite, carbonate, schist and rhyolite caldera uranium are real; not in mafic rock,
    # not in a laterite, not in a lead-zinc body. Extreme Reactors' yellorite is its uranium ore.
    (["techreborn_uranium", "uranium", "ie_uranium", "mek_uranium", "dense_uranium", "yellorite",
      "uraninite", "uraninite_poor", "uraninite_dense", "biggerreactors_uranium"],
     _hosts("PLUT", "VOLC", "LATE", "SULF", "SERP", "CHRT")),
    # Rock salt is an evaporite, laid down with carbonate and in red beds.
    (["salt", "expandeddelight_salt"], _all_but("LIME", "RBED")),
    # Fluorite: Mississippi Valley carbonate, skarn marble, calcite veins, rhyolite (Mexico), lead-zinc gangue.
    (["dense_fluorite", "mek_fluorite"], _hosts("ASPH", "SCH", "PLUT", "VOLC", "LATE", "SHAL", "SERP", "CHRT", "RBED")),
    # Scheelite skarn at limestone and marble contacts, and scheelite in schist.
    (["tungsten", "superbwarfare_scheelite"], _all_but("LIME", "MARB", "SCH")),
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
    (["opal", "black_opal", "nether_black_opal"], _all_but("FELS", "LATE")),
    # Carnelian (chalcedony) fills vesicles in lava.
    (["carnelian", "epicpaladins_bloodstone"], _all_but("VOLC", "FELS")),
    # Ammolite is fossil shell (the Bearpaw shale); pearl is reef; moldavite (tektite) lies in sediments.
    (["ammolite"], _all_but("LIME", "SHAL")),
    (["pearl"], _all_but("LIME")),
    (["moldavite"], _all_but("LIME", "CALC", "ASPH", "LATE")),
    # Benitoite: only in hydrothermally altered serpentinite (San Benito County).
    (["benitoite"], _all_but("SERP")),
]

# ore -> hosts it is refused in
STRICT = {key: hosts for keys, hosts in FAMILIES for key in keys}
if len(STRICT) != sum(len(keys) for keys, _hosts_ in FAMILIES):
    raise SystemExit("geology.py: an ore key is in two families")

# Cobblemon's ten evolution stones (owner, 16 Oct 2026): each is kept only in the rock classes its real
# counterpart or its idea belongs to; the stones in no class (invented, exempt, the Nether ones) keep
# only those that fit their own lore (ore lore x stone lore). Written as refusals in STRICT, so the rule
# is one table. The reasons, stone by stone, are in the maintainer notes (so-wave-2026-10-build).
COBBLEMON_KEEPS = {
    "fire_stone": ["VOLC", "FELS", "SULF"],             # volcanic heat, hot sulphide
    "water_stone": ["LIME", "CALC", "MARB"],            # water-laid carbonate
    "thunder_stone": ["SULF", "PLUT", "SCH"],           # metal-rich, deep crust
    "leaf_stone": ["ASPH", "LIME", "LATE", "SHAL"],     # organic sediment, fossils, soil crust
    "moon_stone": ["PLUT", "FELS", "SCH"],              # real moonstone: feldspar in plutonic rock, schist
    "sun_stone": ["VOLC", "FELS"],                      # real sunstone: feldspar in lava (Oregon)
    "ice_stone": ["MARB", "SCH", "CALC"],               # white, glassy, cold-looking
    "dawn_stone": ["MARB", "CALC", "FELS"],             # pale and pink
    "dusk_stone": ["PLUT", "VOLC", "ASPH", "SHAL"],     # dark rock
    "shiny_stone": ["MARB", "CALC", "SCH"],             # sparkle: sugary marble, calcite, mica
}
# The stones in no class, by their own lore: which evolution stones they keep.
COBBLEMON_LORE = {
    "create_asurine": ["water_stone", "ice_stone"],          # blue crystal
    "create_crimsite": ["fire_stone"],                       # crimson
    "create_ochrum": ["sun_stone", "thunder_stone"],         # ochre, gold
    "create_veridium": ["leaf_stone"],                       # green
    "forbidden_arcanus_darkstone": ["dusk_stone", "moon_stone"],   # dark, arcane, the deepest rock
    "blockus_viridite": ["leaf_stone", "dusk_stone"],        # green, of the deep dark
    "promenade_blunite": ["water_stone", "ice_stone"],       # blue-grey
    "create_scorchia": ["fire_stone", "dusk_stone"],         # scorched lava rock
    "twigs_bloodstone": ["fire_stone"],                      # red, of the Nether
    "mythicupgrades_sapphire_schist": ["water_stone", "ice_stone"],   # sapphire blue
    "mythicupgrades_ruby_schist": ["fire_stone"],            # ruby red
}
_CLASSED = [h for hosts in CLASSES.values() for h in hosts]
for _stone, _kept in COBBLEMON_KEEPS.items():
    if _stone in STRICT:
        raise SystemExit(f"geology.py: {_stone} is in a family and in the Cobblemon rule")
    STRICT[_stone] = [h for h in _CLASSED if h not in COBBLEMON_LORE and not any(h in CLASSES[c] for c in _kept)] + \
        [h for h, kept in COBBLEMON_LORE.items() if _stone not in kept]

# Invented ores. Each is judged by its LORE (FICTION_LORE below; the Cobblemon stones above), never left to
# form anywhere (owner, 22 Oct 2026).
FICTION = set("redstone adamantite aquarium banglum carmot kyber midas_gold morkite mythril necoium "
              "nether_banglum orichalcum palladium prometheum quadrillum runite starrite stormyx "
              "unobtainium chaos prosperity inferium gleaming experience nether_experience soulstone "
              "brilliant blazing_quartz dawn_stone dusk_stone fire_stone ice_stone leaf_stone moon_stone "
              "shiny_stone sun_stone thunder_stone water_stone "
              # the 24 ore mods of 22 Oct 2026
              "arclight cryorium moonlight chlorophyte dreadstone zenalite solar_core cheese oratchalcum "
              "ratlantean_gem dimensional_shard nether_dimensional_shard heart_crystal power_crystal arcmetal "
              "plasteel solarmetal voidmetal dark anthralite vehement_coal enderite enderium".split())

# Create's four invented stones each keep only the ore Create ties them to (owner), plus the invented ores
# whose lore matches (FICTION_LORE).
LORE = {"create_asurine": "zinc", "create_crimsite": "iron", "create_ochrum": "gold",
        "create_veridium": "copper"}

# THE END (owner, 21 Oct 2026). End stone and every End rock are fiction, and so are most End ores, so the
# End is judged by lore, not by CLASSES: a crystalline End stone keeps gems (and fiction); a volcanic-looking
# one (brimstone, sulphuric rock, void basalt, corrode stone) keeps metal and fire ores, added with its first
# host; the game's own rocks in an End biome follow their Overworld class.
END_GEM_STONES = ["mythicupgrades_jade_schist"]
GEMS = set("ametrine jade aquamarine citrine peridot topaz ruby sapphire diamond emerald lapis quartz "
           "alexandrite ammolite black_diamond carnelian garnet heliodor iolite kyanite moldavite opal pearl "
           "rose_quartz tanzanite turquoise white_diamond silents_aquamarine silents_citrine silents_peridot "
           "silents_ruby silents_sapphire silents_topaz techreborn_ruby techreborn_sapphire "
           "iceandfire_sapphire epicpaladins_jade amethyst black_opal".split())


# Stones other mods place that are judged exactly as one of the game's rocks (owner, 21 Oct 2026). A refusal
# is fixed here, vanilla ore included, as for every stone another mod places.
ROCK_AS = {"embellishcraft_gneiss": "granite", "embellishcraft_larvikite": "diorite"}


# INVENTED ORES BY LORE (owner, 22 Oct 2026; the table and each mod's own words are in so-fiction-lore-rule).
# ore -> (classes kept, the game's rocks kept, invented stones kept beyond their class). Every other classed
# host, Create stratum, End gem stone and game rock refuses it. Rocks: G granite, D diorite, A andesite,
# T tuff, Dr dripstone, B basalt, Bs blackstone.
_ROCK_CODE = {"G": "granite", "D": "diorite", "A": "andesite", "T": "tuff", "Dr": "dripstone",
              "B": "basalt", "Bs": "blackstone"}
_NETHER_FIRE = ("VOLC", "B Bs", "")
_DARK = "forbidden_arcanus_darkstone"
FICTION_LORE = {
    # Mythic Metals, from its advancement lines
    "adamantite": ("PLUT SCH", "G D T", "create_crimsite " + _DARK),  # "the deepest part of the deepslate caves"
    "aquarium": ("LIME CHRT SHAL VOLC", "A", "create_asurine"),    # under the oceans: sea-floor rock
    "banglum": ("SULF VOLC LIME ASPH", "A T", ""),                 # "highly volatile", explosive: sulphur, nitre
    "nether_banglum": ("SULF VOLC LIME ASPH", "B Bs", ""),
    "carmot": ("SULF SCH", "G D", "create_crimsite"),              # "Alchemical Miracle", transmutation
    "kyber": ("CALC VOLC FELS", "A Dr", "create_asurine"),         # "hidden inside Amethyst Geodes", calcite
    "midas_gold": ("SULF FELS SCH VOLC", "B Bs", "create_ochrum"), # King Midas, Nether gold
    "morkite": ("PLUT SCH VOLC", "G T", "create_asurine"),         # a deep mining crystal, teal
    "mythril": ("PLUT SCH MARB", "G D T", "create_asurine"),       # "hallowed", dwarven, silver-blue
    "orichalcum": ("VOLC SHAL CHRT", "A T", "create_veridium"),    # Atlantis bronze; the mod puts it in tuff and smooth basalt
    "palladium": _NETHER_FIRE,                                     # under the Nether's lava ocean
    "prometheum": ("ASPH LIME SHAL LATE", "T", "create_veridium"), # jungles and lush caves, regrowth
    "quadrillum": ("PLUT SULF", "G D", "create_crimsite"),         # industrial: durasteel
    "runite": ("SCH MARB PLUT", "G D", _DARK),                     # runes, hidden in the walls; runic darkstone
    "starrite": ("CALC MARB", "D G", "mythicupgrades_jade_schist"), # "Fallen Stardrops", calcite of the mountains
    "stormyx": _NETHER_FIRE,                                       # "The Nether Diamond", in blackstone
    "unobtainium": ("", "T", _DARK),                               # "How Did You Get This?": the deepest rock only
    "necoium": ("SCH", "G T", "create_crimsite"),                  # the mineral of Mythic Upgrades' schist caves
    "chaos": ("VOLC FELS SULF", "A T", ""),                        # raw magic, entropy
    "inferium": ("ASPH LIME SHAL LATE", "T", "create_veridium"),   # life force, growth
    "prosperity": ("SULF SCH FELS", "G D", "create_ochrum"),       # abundance, rich veins
    "gleaming": ("MARB SCH CALC", "T D", ""),                      # "where the stones meet": contact rock
    "experience": ("SHAL LIME", "T Dr", "create_veridium"),        # remains and memory, as brilliance
    "nether_experience": ("SHAL LIME VOLC", "B Bs", ""),
    "soulstone": ("SHAL ASPH PLUT", "T G", _DARK),                 # "more in the arcane than the physical"
    "brilliant": ("SHAL LIME", "T Dr", "create_veridium"),         # condensed experience, "where a soul faded away"
    "blazing_quartz": _NETHER_FIRE,                                # the Nether's coal-like fuel
    "redstone": ("SULF PLUT SCH VOLC FELS", "G D A T", "create_crimsite"),   # power that glows; vanilla: the option
    # Epic Paladins
    "arclight": ("FELS PLUT SCH", "G D", "create_ochrum"),         # holy radiance, amber
    "cryorium": ("MARB CALC SCH", "D", ""),                        # cryo, frost
    "moonlight": _NETHER_FIRE,                                     # moon glow in the Nether's rock
    # Hazen 'N Stuff
    "chlorophyte": ("ASPH SHAL LIME LATE", "T", "create_veridium"),  # the jungle ore, in mud
    "dreadstone": ("PLUT VOLC SHAL", "T", "create_crimsite " + _DARK),  # dread, deep, dark red
    "zenalite": ("MARB CALC", "D", "mythicupgrades_jade_schist"),  # dormant until a star wakes it
    "solar_core": ("VOLC FELS", "B Bs", ""),                       # the sun, in the Nether
    # Rats (Ratlantis only: no variant, lore for completeness)
    "cheese": ("LIME CALC", "Dr D", ""),                           # holes, like karst
    "oratchalcum": ("VOLC SHAL CHRT", "A T", ""),                  # Atlantis bronze, as orichalcum
    "ratlantean_gem": ("LIME CHRT", "D", ""),                      # the gem of a sunken civilisation
    # RFTools Base
    "dimensional_shard": ("SCH MARB FELS PLUT", "G D", ""),       # "in various dimensions": crystalline rock
    "nether_dimensional_shard": ("SCH MARB FELS PLUT VOLC", "B Bs", ""),
    # Scaling Health
    "heart_crystal": ("FELS VOLC CALC", "G Dr", "create_crimsite"),  # life, a red crystal
    "power_crystal": ("SULF PLUT SCH", "G D", "create_asurine"),   # strength, a blue crystal (blunite is PLUT)
    # SilentCompat, by their Silent Gear traits
    "arcmetal": ("SULF PLUT SCH FELS", "G D", ""),                 # electric arc, mountain tops
    "plasteel": ("PLUT SULF", "T", ""),                            # a dense alloy of the deepslate
    "solarmetal": ("", "B Bs", ""),                                # takes the place of the Nether's lava
    "voidmetal": ("PLUT VOLC SERP", "T", _DARK),                   # the void, magnetic, deep
    # EvilCraft
    "dark": ("PLUT VOLC SHAL ASPH", "A T", _DARK),                 # "a very obscure presence"
    # Scorched Guns
    "anthralite": ("ASPH SHAL LIME", "T", ""),                     # gunmetal of the coal measures
    "vehement_coal": _NETHER_FIRE,                                 # "an intensely hot fuel"
    # The End: no host keeps them yet
    "enderite": ("", "", ""),
    "enderium": ("", "", ""),
}
if set(FICTION) - set(FICTION_LORE) - set(COBBLEMON_KEEPS):
    raise SystemExit(f"geology.py: invented ores with no lore: {sorted(set(FICTION) - set(FICTION_LORE) - set(COBBLEMON_KEEPS))}")
_LORE_ROCK = {}     # ore -> the game's rocks it refuses, for ROCK below
for _ore, (_classes, _rocks, _stones) in FICTION_LORE.items():
    if _ore in STRICT:
        raise SystemExit(f"geology.py: {_ore} is in a family and in the lore table")
    _keep_classes, _keep_stones = _classes.split(), _stones.split()
    STRICT[_ore] = [h for c in ALL if c not in _keep_classes for h in CLASSES[c] if h not in _keep_stones] + \
        [h for h in LORE if h not in _keep_stones] + \
        [h for h in END_GEM_STONES if h not in _keep_stones] + \
        ([] if "Dr" in _rocks.split() else ["minecraft_dripstone_block"])
    _LORE_ROCK[_ore] = [r for code, r in _ROCK_CODE.items() if code not in _rocks.split()]


def fixed(host, ore):
    """Whether this ore never forms in this host, for good: no variant, and worldgen makes it stone. The
    stones other mods place, and modded ores in the game's own rock (rock_fixed, below)."""
    if host in GAME_ROCK:
        return rock_fixed(host, ore)
    if host in STRICT.get(ore, ()):
        return True
    if host in END_GEM_STONES:
        return ore not in GEMS and ore not in FICTION
    if host in ROCK_AS:
        return _rock_refuses(ROCK_AS[host], ore)
    keep = LORE.get(host)
    return keep is not None and ore != keep and ore not in FICTION


# --- THE GAME'S OWN ROCK -------------------------------------------------------------------------

# The game's own ores: their refusals in the game's own rock are behind the option, never fixed.
VANILLA_ORES = {"coal", "iron", "copper", "gold", "redstone", "lapis", "diamond", "emerald", "nether_gold", "quartz"}

# Granite: felsic plutonic. Diorite: intermediate plutonic. Andesite: intermediate volcanic. Tuff: volcanic
# ash. Dripstone: cave calcite (a speleothem). Basalt and blackstone: the Nether's mafic lava rock.
_G, _D, _A, _T = "granite", "diorite", "andesite", "tuff"
FOUR = [_G, _D, _A, _T]
NETHER_ROCK = ["basalt", "blackstone"]
GAME_ROCK = set(FOUR + ["dripstone"] + NETHER_ROCK)

# Ore -> which of the four rocks it never forms in. Absent: it forms in all four (iron, copper, gold,
# silver, the lead-zinc family, uranium, bauxite, citrine, fiction).
_FOUR_ROCK = [
    # Coal needs a swamp: never in a pluton or a lava flow; ash falls on coal swamps, so tuff keeps it.
    (["coal", "lignite_coal"], [_G, _D, _A]),
    # Kimberlite only; its crater is pyroclastic, so tuff keeps it (the kimberlite tuff decision).
    (["diamond", "bort", "white_diamond", "black_diamond", "infected_diamond"], [_G, _D, _A]),
    # Beryl (emerald) and lazurite form at granite contacts: plutonic rock keeps them, lava and ash do not.
    (["emerald", "lapis"], [_A, _T]),
    # Granite pegmatite and greisen minerals: granite only.
    (["topaz", "silents_topaz", "tin", "energized_tin", "techreborn_tin", "mi_tin", "mek_tin", "dense_tin",
      "aquamarine", "silents_aquamarine", "heliodor", "monazite", "thorium", "garnet"], [_D, _A, _T]),
    # Wolframite in granite, scheelite skarn at diorite contacts.
    (["tungsten", "superbwarfare_scheelite"], [_A, _T]),
    # Smoky quartz: granite pegmatite only.
    (["black_quartz"], [_D, _A, _T]),
    # Amethyst geodes in lava and ash, veins in granite; never in diorite.
    (["amethyst"], [_D]),
    # Ilmenite and rutile: intermediate rock keeps them (diorite, andesite).
    (["tankdefenses_titanium"], [_G, _T]),
    # Fumarole minerals: andesite and tuff keep them.
    (["scguns_sulfur", "sal_ammoniac"], [_G, _D]),
    # Spodumene pegmatite (granite) and caldera lithium clays (tuff).
    (["lithium"], [_D, _A]),
    # Fluorite: granite greisen, rhyolitic tuff.
    (["dense_fluorite", "mek_fluorite"], [_D, _A]),
    # Olivine and corundum never coexist with these; nickel and the platinum group are ultramafic; salt is
    # an evaporite; the rest are metamorphic, biogenic or impact minerals.
    (["peridot", "silents_peridot", "techreborn_ruby", "techreborn_sapphire", "silents_ruby", "silents_sapphire",
      "iceandfire_sapphire", "platinum", "iridium", "osmium", "mi_iridium", "mek_osmium", "dense_osmium",
      "nickel", "mi_nickel", "ie_nickel", "salt", "kyanite", "iolite", "alexandrite", "rose_quartz",
      "createpropulsion_platinum", "expandeddelight_salt", "sullysmod_jade",
      "tanzanite", "ammolite", "pearl", "moldavite"], FOUR),
    # Turquoise is supergene, over altered volcanics: lava and ash keep it.
    (["turquoise"], [_G, _D]),
    # Opal: in rhyolitic tuff (Ethiopia).
    (["opal", "black_opal"], [_G, _D, _A]),
    # Carnelian fills vesicles in lava and ash.
    (["carnelian", "epicpaladins_bloodstone"], [_G, _D]),
]

# Dripstone KEEPS only what precipitates in limestone caves or fills karst cavities, and refuses the rest:
# goethite, malachite and azurite speleothems; Mississippi Valley lead-zinc and fluorite; cave manganese
# crusts; karst bauxite; karst uranium (Tyuya-Muyun); halite speleothems.
DRIPSTONE_KEEPS = set(
    "iron copper manganese salt dense_fluorite mek_fluorite mi_bauxite techreborn_bauxite ie_aluminum "
    "zinc galena techreborn_lead lead mi_lead ie_lead mek_lead dense_lead oreganized_lead antimony "
    "techreborn_uranium uranium ie_uranium mek_uranium dense_uranium yellorite uraninite uraninite_poor "
    "uraninite_dense biggerreactors_uranium embers_lead superbwarfare_galena expandeddelight_salt "
    "tankdefenses_aluminum".split())

# Basalt and blackstone: real minerals by the mafic volcanic reading (FAMILIES' VOLC). Every invented
# Nether ore fits fire, lava or the piglins' gold and keeps both (lore, owner's rule of 20 Oct 2026).
_NETHER_REFUSED = ["nether_black_diamond", "nether_iolite", "nether_alexandrite", "nether_tanzanite",
                   "nether_moldavite", "nether_pearl", "benitoite", "nether_black_opal"]

# Cobblemon's evolution stones by the lore of COBBLEMON_KEEPS: granite (pink, plutonic, moonstone
# pegmatites, metal-rich crust, mica sparkle), diorite (white, plutonic), andesite (grey lava), tuff
# (volcanic ash, which buries forests whole), dripstone (cave calcite, CALC), the Nether rock (VOLC).
_COBBLEMON_ROCK_KEEPS = {
    "granite": ["moon_stone", "dawn_stone", "thunder_stone", "shiny_stone"],
    "diorite": ["moon_stone", "ice_stone", "thunder_stone"],
    "andesite": ["fire_stone", "sun_stone", "dusk_stone"],
    "tuff": ["fire_stone", "sun_stone", "dusk_stone", "leaf_stone"],
    "dripstone": [s for s, k in COBBLEMON_KEEPS.items() if "CALC" in k],
    "basalt": [s for s, k in COBBLEMON_KEEPS.items() if "VOLC" in k],
    "blackstone": [s for s, k in COBBLEMON_KEEPS.items() if "VOLC" in k],
}

# ore -> the game's own rocks other than dripstone it never forms in (dripstone: DRIPSTONE_KEEPS)
ROCK = {}
for _keys, _rocks in _FOUR_ROCK:
    for _k in _keys:
        if _k in ROCK:
            raise SystemExit(f"geology.py: {_k} is twice in the four-rock table")
        ROCK[_k] = list(_rocks)
for _k in _NETHER_REFUSED:
    ROCK.setdefault(_k, []).extend(NETHER_ROCK)
for _ore, _rocks in _LORE_ROCK.items():
    if _ore in ROCK:
        raise SystemExit(f"geology.py: {_ore} is in the four-rock table and in the lore table")
    ROCK[_ore] = list(_rocks)
for _stone in COBBLEMON_KEEPS:
    if _stone in ROCK:
        raise SystemExit(f"geology.py: {_stone} is already in ROCK")
    ROCK[_stone] = [rock for rock, kept in _COBBLEMON_ROCK_KEEPS.items() if _stone not in kept]


def _rock_refuses(host, ore):
    if host == "dripstone" and ore not in FICTION:
        return ore not in DRIPSTONE_KEEPS
    return host in ROCK.get(ore, ())


def rock_fixed(host, ore):
    """Whether a MODDED ore never forms in this rock of the game's own: no variant, worldgen keeps the rock."""
    return host in GAME_ROCK and ore not in VANILLA_ORES and _rock_refuses(host, ore)


def optional(host, ore):
    """Whether the geology option, when on, refuses this VANILLA ore in this rock of the game's own."""
    return host in GAME_ROCK and ore in VANILLA_ORES and _rock_refuses(host, ore)


def note_absent(keys, hosts):
    """Prints the ores and stones this rule names that a band does not have. The rule serves every
    band, so most bands lack some; the list is printed, not refused, so a misspelt key still shows."""
    ores = set(STRICT) | set(ROCK)
    stones = set(h for hs in STRICT.values() for h in hs) | set(LORE) | set(END_GEM_STONES) | set(ROCK_AS)
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


def _set(values):
    return ", ".join('"%s"' % v for v in sorted(values))


def java():
    """OreGeology.java: this rule, written as Java. Minecraft-free and the same for every band, so it
    lives once in shared/java; a band asks it by host name and ore key and never lists its own."""
    return JAVA % (_map_of_sets(STRICT, " " * 12),
                   ",\n".join('            Map.entry("%s", "%s")' % kv for kv in LORE.items()),
                   _set(FICTION), _map_of_sets(ROCK, " " * 12), _set(DRIPSTONE_KEEPS), _set(COBBLEMON_KEEPS),
                   _set(VANILLA_ORES), _set(GAME_ROCK), _set(END_GEM_STONES), _set(GEMS),
                   ",\n".join('            Map.entry("%s", "%s")' % kv for kv in ROCK_AS.items()))


def write_java(write_text):
    """Writes shared/java's OreGeology.java with the caller's writer (assetgen.write_text: LF)."""
    write_text(SHARED_JAVA, java())


JAVA = '''package com.chillpavz.seamlessores.content;

import java.util.Map;
import java.util.Set;

/**
 * The geology rule: the ores that never form in a host rock.
 *
 * <p><b>Fixed</b>, for the stones other mods place: a refused pair is never registered, and worldgen
 * turns that ore into the stone wherever the stone swallows it, so no seam can appear. Never
 * configurable: the registered block set must not depend on config. The strict reading, plus a lore
 * rule for Create's four invented stones: each keeps only the ore Create ties it to, and fiction; and the
 * End's lore: a crystalline End stone keeps gems and fiction.
 *
 * <p><b>The game's own rock</b> (granite, diorite, andesite, tuff, dripstone, basalt, blackstone), by the
 * same strict reading: a MODDED ore refused there is fixed too (never registered, the rock stays rock); a
 * VANILLA ore refused there is <b>optional</b>, the geology option, off by default because it REMOVES ore.
 * Every vanilla block stays registered; with the option on, where the ore would have gone the rock stays.
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

    /** Invented ores: judged by their lore (in STRICT and ROCK), dripstone included. */
    private static final Set<String> FICTION = Set.of(%s);

    /** Ore key -> the game's own rocks, dripstone aside, it never forms in. */
    private static final Map<String, Set<String>> ROCK = Map.ofEntries(
%s);

    /** The only real ores dripstone, a cave calcite, keeps. */
    private static final Set<String> DRIPSTONE_KEEPS = Set.of(%s);

    /** Cobblemon's evolution stones: judged in dripstone by their lore (ROCK), not by DRIPSTONE_KEEPS. */
    private static final Set<String> COBBLEMON = Set.of(%s);

    /** The game's own ores: their refusals in the game's own rock are the option's, never fixed. */
    private static final Set<String> VANILLA_ORES = Set.of(%s);

    private static final Set<String> GAME_ROCK = Set.of(%s);

    /** The End's crystalline stones: they keep gems, and fiction, only. */
    private static final Set<String> END_GEM_STONES = Set.of(%s);

    private static final Set<String> GEMS = Set.of(%s);

    /** Stones other mods place that are judged as one of the game's rocks (gneiss as granite). */
    private static final Map<String, String> ROCK_AS = Map.ofEntries(
%s);

    private static boolean rockRefuses(String host, String ore) {
        if ("dripstone".equals(host) && !FICTION.contains(ore)) {
            return !DRIPSTONE_KEEPS.contains(ore);
        }
        return ROCK.getOrDefault(ore, Set.of()).contains(host);
    }

    /** Whether this ore never forms in this host, for good: no variant, worldgen makes it the stone. */
    public static boolean fixed(String host, String ore) {
        if (GAME_ROCK.contains(host)) {
            return !VANILLA_ORES.contains(ore) && rockRefuses(host, ore);
        }
        if (STRICT.getOrDefault(ore, Set.of()).contains(host)) {
            return true;
        }
        if (END_GEM_STONES.contains(host)) {
            return !GEMS.contains(ore) && !FICTION.contains(ore);
        }
        if (ROCK_AS.containsKey(host)) {
            return rockRefuses(ROCK_AS.get(host), ore);
        }
        final String keep = LORE.get(host);
        return keep != null && !keep.equals(ore) && !FICTION.contains(ore);
    }

    /** Whether the geology option, when on, refuses this VANILLA ore in this rock of the game's own. */
    public static boolean optional(String host, String ore) {
        return GAME_ROCK.contains(host) && VANILLA_ORES.contains(ore) && rockRefuses(host, ore);
    }
}
'''


