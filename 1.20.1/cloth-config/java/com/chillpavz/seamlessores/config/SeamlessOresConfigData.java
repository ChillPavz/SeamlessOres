package com.chillpavz.seamlessores.config;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import me.shedaniel.autoconfig.AutoConfig;
import me.shedaniel.autoconfig.ConfigData;
import me.shedaniel.autoconfig.annotation.Config;
import me.shedaniel.autoconfig.annotation.ConfigEntry;
import me.shedaniel.autoconfig.serializer.GsonConfigSerializer;
import net.minecraft.world.InteractionResult;

/**
 * Cloth Config data class.
 *
 * <p><b>One copy, compiled by both loader modules</b> (cloth-config/java, wired in
 * multiloader-loader.gradle). It cannot live in {@code common} because cloth-config is a loader
 * dependency and common compiles against vanilla only. The values are pushed into
 * {@link SeamlessOresConfig}, which is where the worldgen code reads them.
 *
 * <p>All three loaders use cloth here. Only the 1.21.11 branch hand-writes a Forge screen, because
 * that is the one version with no official cloth Forge build — cloth ships one at 1.21.x and 1.20.x
 * alike, so do NOT copy 1.21.11's screen backwards into this branch.
 *
 * <p>Everything here gates <i>generation</i>, never registration — see {@link SeamlessOresConfig}.
 * A disabled mod's blocks still exist, in the creative tab and in every tag; they simply stop being
 * injected into worldgen. That is what makes a client and a server unable to disagree.
 */
@Config(name = Constants.MOD_ID)
public class SeamlessOresConfigData implements ConfigData {

    // Category ORDER is field declaration order: AutoConfig walks the declared fields and creates
    // each category the first time it sees one. So Overworld and Nether come first because they are
    // declared first, and the per-mod categories that follow are in ALPHABETICAL order by their
    // display name. Keep it that way when adding a mod - the sort is by the English name in
    // en_us.json, not by mod id, so "Create: New Age" sorts before "Create: TFMG" and
    // "Silent Gear" before "Silent's Gems" (space sorts before apostrophe).
    //
    // Which of them are SHOWN is decided at runtime by SeamlessOresConfigScreenFactory, which drops
    // the category of any mod that is not installed. Nothing is removed from the config FILE, so a
    // setting survives uninstalling and reinstalling a mod.

    // --- Overworld ------------------------------------------------------------------------------

    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip
    public boolean granite = true;

    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip
    public boolean diorite = true;

    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip
    public boolean andesite = true;

    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip
    public boolean tuff = true;

    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip
    public boolean dripstone = true;

    // Removes the ore it touches rather than restyling it; see SeamlessOresConfig.lushCaves.
    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean lushCaves = true;

    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean oreVeins = true;

    // Removes ore: an ore that could never form in granite, diorite, andesite or tuff stays that
    // rock instead. Off by default; see SeamlessOresConfig.geology.
    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean geology = false;


    // Copper. The ONLY overworld settings that change how much ore there is rather than how it
    // looks - see SeamlessOresConfig and the store page. 100 is vanilla exactly.
    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip(count = 3)
    @ConfigEntry.BoundedDiscrete(min = 25, max = 100)
    public int overworldCopper = 75;

    @ConfigEntry.Category("overworld")
    @ConfigEntry.Gui.Tooltip(count = 3)
    @ConfigEntry.BoundedDiscrete(min = 0, max = 100)
    public int dripstoneCopper = 50;

    // --- Sulfur Caves (Vanilla Backport) -----------------------------------------------------------
    // The screen factory hides the tab when Vanilla Backport is not installed.

    // ADDS ore, like basalt and blackstone: see OreTier.CINNABAR.
    @ConfigEntry.Category("sulfur_caves")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean cinnabar = true;

    // Percent of the default amount; see SeamlessOresConfig.cinnabarAmount.
    @ConfigEntry.Category("sulfur_caves")
    @ConfigEntry.Gui.Tooltip(count = 2)
    @ConfigEntry.BoundedDiscrete(min = 0, max = 300)
    public int cinnabarAmount = 100;

    // Removes ore as well; see SeamlessOresConfig.sulfurCaves.
    @ConfigEntry.Category("sulfur_caves")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean sulfurCaves = true;

    // --- Nether ---------------------------------------------------------------------------------

    /** Adds gold and quartz where vanilla has none - see the tooltip. */
    @ConfigEntry.Category("nether")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean basalt = true;

    /** Adds gold and quartz where vanilla has none - see the tooltip. */
    @ConfigEntry.Category("nether")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean blackstone = true;

    @ConfigEntry.Category("nether")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean bastionSafeNether = true;

    @ConfigEntry.Category("nether")
    @ConfigEntry.Gui.Tooltip(count = 3)
    @ConfigEntry.BoundedDiscrete(min = 1, max = 10)
    public int netherOreRarity = 2;

    @ConfigEntry.Category("nether")
    @ConfigEntry.Gui.Tooltip(count = 3)
    @ConfigEntry.BoundedDiscrete(min = 25, max = 100)
    public int netherVeinSize = 80;

    // --- Modded Stones ----------------------------------------------------------------------------
    // One switch per stone that another mod adds (Blockus, Create, Twigs and so on), for the ores that
    // end up inside it. The screen factory hides the tab when none of those mods is installed.

    // BEGIN GENERATED modded stone switches (tools/generate_assets.py, from the host table)
    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean minecraftBlackstone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean blockusLimestone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean blockusMarble = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean blockusBluestone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean blockusViridite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean createAsurine = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean createCrimsite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean createLimestone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean createOchrum = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean createScorchia = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean createScoria = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean createVeridium = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean minecraftCalcite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean minecraftSmoothBasalt = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean tfmgBauxite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean tfmgGalena = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean tfmgLignite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean twigsRhyolite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean twigsSchist = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean twigsBloodstone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean bornInChaosV1BlackArgillite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean embellishcraftBasalt = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean embellishcraftSlate = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean embellishcraftMarble = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean embellishcraftGneiss = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean embellishcraftJade = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean embellishcraftLarvikite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean quarkLimestone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean quarkJasper = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean quarkShale = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean forbiddenArcanusDarkstone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean meadowLimestone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicupgradesAquamarineSchist = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicupgradesCitrineSchist = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicupgradesPeridotSchist = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicupgradesTopazSchist = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicupgradesSapphireSchist = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicupgradesJadeSchist = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean promenadeAsphalt = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean promenadeBlunite = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean spawnReefstone = true;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean biomeswevegoneDacite = false;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean biomeswevegoneWhiteDacite = false;

    @ConfigEntry.Category("modded_stones")
    @ConfigEntry.Gui.Tooltip
    public boolean biomeswevegoneRedRock = false;
    // END GENERATED modded stone switches

    // --- Cobblemon ------------------------------------------------------------------------------

    @ConfigEntry.Category("cobblemon")
    @ConfigEntry.Gui.Tooltip
    public boolean cobblemon = true;

    @ConfigEntry.Category("cobblemon")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean cobblemonNether = true;

    // --- Create ---------------------------------------------------------------------------------

    @ConfigEntry.Category("create")
    @ConfigEntry.Gui.Tooltip
    public boolean createZinc = true;

    @ConfigEntry.Category("create")
    @ConfigEntry.Gui.Tooltip(count = 3)
    @ConfigEntry.BoundedDiscrete(min = 6, max = 12)
    public int zincVeinSize = 10;

    // --- Create: New Age ------------------------------------------------------------------------

    @ConfigEntry.Category("create_new_age")
    @ConfigEntry.Gui.Tooltip
    public boolean createNewAge = true;

    // --- Create: TFMG ---------------------------------------------------------------------------

    @ConfigEntry.Category("tfmg")
    @ConfigEntry.Gui.Tooltip
    public boolean tfmg = true;

    // --- Dense Mekanism -------------------------------------------------------------------------

    @ConfigEntry.Category("dense_mekanism")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean denseMekanism = true;

    // --- Energized Power ------------------------------------------------------------------------

    @ConfigEntry.Category("energized_power")
    @ConfigEntry.Gui.Tooltip
    public boolean energizedPower = true;

    // --- Exp Ores -------------------------------------------------------------------------------

    @ConfigEntry.Category("exp_ores")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean expOres = true;

    // --- Extreme Reactors -----------------------------------------------------------------------

    @ConfigEntry.Category("extreme_reactors")
    @ConfigEntry.Gui.Tooltip
    public boolean extremeReactors = true;

    @ConfigEntry.Category("extreme_reactors")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean extremeReactorsNether = true;

    // --- Ice and Fire ---------------------------------------------------------------------------

    @ConfigEntry.Category("ice_and_fire")
    @ConfigEntry.Gui.Tooltip
    public boolean iceAndFire = true;

    // --- Modern Industrialization ---------------------------------------------------------------

    @ConfigEntry.Category("modern_industrialization")
    @ConfigEntry.Gui.Tooltip
    public boolean modernIndustrialization = true;

    // --- Mystical Agriculture -------------------------------------------------------------------

    @ConfigEntry.Category("mystical_agriculture")
    @ConfigEntry.Gui.Tooltip
    public boolean mysticalAgriculture = true;

    // --- Mythic Metals --------------------------------------------------------------------------

    @ConfigEntry.Category("mythic_metals")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicMetals = true;

    // --- Mythic Upgrades ------------------------------------------------------------------------

    @ConfigEntry.Category("mythic_upgrades")
    @ConfigEntry.Gui.Tooltip
    public boolean mythicUpgrades = true;

    @ConfigEntry.Category("mythic_upgrades")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean netherGems = true;

    @ConfigEntry.Category("mythic_upgrades")
    @ConfigEntry.Gui.Tooltip(count = 2)
    @ConfigEntry.BoundedDiscrete(min = 3, max = 6)
    public int netherGemSize = 4;

    // --- Occultism ------------------------------------------------------------------------------

    @ConfigEntry.Category("occultism")
    @ConfigEntry.Gui.Tooltip
    public boolean occultism = true;

    // --- Immersive Engineering ------------------------------------------------------------------

    @ConfigEntry.Category("immersive_engineering")
    @ConfigEntry.Gui.Tooltip
    public boolean immersiveEngineering = true;

    // --- Malum ----------------------------------------------------------------------------------

    @ConfigEntry.Category("malum")
    @ConfigEntry.Gui.Tooltip
    public boolean malum = true;

    // --- Mekanism -------------------------------------------------------------------------------

    @ConfigEntry.Category("mekanism")
    @ConfigEntry.Gui.Tooltip
    public boolean mekanism = true;

    // --- Oreganized -----------------------------------------------------------------------------

    @ConfigEntry.Category("oreganized")
    @ConfigEntry.Gui.Tooltip
    public boolean oreganized = true;

    // --- Powah ----------------------------------------------------------------------------------

    @ConfigEntry.Category("powah")
    @ConfigEntry.Gui.Tooltip
    public boolean powah = true;

    // --- Silent Gear ----------------------------------------------------------------------------

    @ConfigEntry.Category("silent_gear")
    @ConfigEntry.Gui.Tooltip
    public boolean silentGear = true;

    // --- Silent's Gems --------------------------------------------------------------------------
    // The one mod that gets more than a single switch, because its two halves are different kinds
    // of change. The overworld gems restyle ore that already generates in granite, diorite,
    // andesite and tuff - balance-neutral. The eight generating nether gems target c:netherracks
    // only, so our basalt and blackstone variants ADD ore, exactly as our own gold and quartz do,
    // and they therefore need the same two dials. Both default to the global nether values so the
    // shipped behaviour is consistent rather than arbitrary.

    @ConfigEntry.Category("silents_gems")
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean silentGems = true;

    @ConfigEntry.Category("silents_gems")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean silentGemsNether = true;

    @ConfigEntry.Category("silents_gems")
    @ConfigEntry.Gui.Tooltip(count = 2)
    @ConfigEntry.BoundedDiscrete(min = 1, max = 10)
    public int silentGemsNetherRarity = 2;

    @ConfigEntry.Category("silents_gems")
    @ConfigEntry.Gui.Tooltip(count = 2)
    @ConfigEntry.BoundedDiscrete(min = 25, max = 100)
    public int silentGemsNetherVeinSize = 80;

    // --- Born in Chaos -------------------------------------------------------------------------

    @ConfigEntry.Category("born_in_chaos")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean bornInChaosInfectedDiamond = false;

    // --- Tech Reborn ----------------------------------------------------------------------------

    @ConfigEntry.Category("tech_reborn")
    @ConfigEntry.Gui.Tooltip
    public boolean techReborn = true;

    @ConfigEntry.Category("tech_reborn")
    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean techRebornNether = true;

    // --- Things ---------------------------------------------------------------------------------

    @ConfigEntry.Category("things")
    @ConfigEntry.Gui.Tooltip
    public boolean things = true;

    // --- Bigger Reactors -----------------------------------------------------------------------------

    @ConfigEntry.Category("bigger_reactors")
    @ConfigEntry.Gui.Tooltip
    public boolean biggerReactors = true;


    /** Registers the config and wires it to the common holder. Safe on client and dedicated server. */
    public static void register() {
        AutoConfig.register(SeamlessOresConfigData.class, GsonConfigSerializer::new);
        AutoConfig.getConfigHolder(SeamlessOresConfigData.class).registerSaveListener((holder, data) -> {
            data.push();
            return InteractionResult.SUCCESS;
        });
        AutoConfig.getConfigHolder(SeamlessOresConfigData.class).getConfig().push();
    }

    /**
     * Copies these values into the loader-agnostic holder that worldgen reads.
     *
     * <p>Assigned BY NAME into {@link SeamlessOresConfig.Values} rather than passed positionally.
     * With two dozen settings, half of them {@code boolean} and half {@code int}, a positional call
     * lets any two neighbours be transposed and still compile — and the symptom would be a silently
     * wrong worldgen dial, which is the least visible kind of bug this mod can have.
     */
    public void push() {
        final SeamlessOresConfig.Values values = new SeamlessOresConfig.Values();

        values.lushCaves = lushCaves;
        // BEGIN GENERATED host switches (tools/generate_assets.py, from the host table)
        values.hosts.put("granite", granite);
        values.hosts.put("diorite", diorite);
        values.hosts.put("andesite", andesite);
        values.hosts.put("tuff", tuff);
        values.hosts.put("dripstone", dripstone);
        values.hosts.put("cinnabar", cinnabar);
        values.hosts.put("basalt", basalt);
        values.hosts.put("blackstone", blackstone);
        values.hosts.put("minecraft_blackstone", minecraftBlackstone);
        values.hosts.put("blockus_limestone", blockusLimestone);
        values.hosts.put("blockus_marble", blockusMarble);
        values.hosts.put("blockus_bluestone", blockusBluestone);
        values.hosts.put("blockus_viridite", blockusViridite);
        values.hosts.put("create_asurine", createAsurine);
        values.hosts.put("create_crimsite", createCrimsite);
        values.hosts.put("create_limestone", createLimestone);
        values.hosts.put("create_ochrum", createOchrum);
        values.hosts.put("create_scorchia", createScorchia);
        values.hosts.put("create_scoria", createScoria);
        values.hosts.put("create_veridium", createVeridium);
        values.hosts.put("minecraft_calcite", minecraftCalcite);
        values.hosts.put("minecraft_smooth_basalt", minecraftSmoothBasalt);
        values.hosts.put("tfmg_bauxite", tfmgBauxite);
        values.hosts.put("tfmg_galena", tfmgGalena);
        values.hosts.put("tfmg_lignite", tfmgLignite);
        values.hosts.put("twigs_rhyolite", twigsRhyolite);
        values.hosts.put("twigs_schist", twigsSchist);
        values.hosts.put("twigs_bloodstone", twigsBloodstone);
        values.hosts.put("born_in_chaos_v1_black_argillite", bornInChaosV1BlackArgillite);
        values.hosts.put("embellishcraft_basalt", embellishcraftBasalt);
        values.hosts.put("embellishcraft_slate", embellishcraftSlate);
        values.hosts.put("embellishcraft_marble", embellishcraftMarble);
        values.hosts.put("embellishcraft_gneiss", embellishcraftGneiss);
        values.hosts.put("embellishcraft_jade", embellishcraftJade);
        values.hosts.put("embellishcraft_larvikite", embellishcraftLarvikite);
        values.hosts.put("quark_limestone", quarkLimestone);
        values.hosts.put("quark_jasper", quarkJasper);
        values.hosts.put("quark_shale", quarkShale);
        values.hosts.put("forbidden_arcanus_darkstone", forbiddenArcanusDarkstone);
        values.hosts.put("meadow_limestone", meadowLimestone);
        values.hosts.put("mythicupgrades_aquamarine_schist", mythicupgradesAquamarineSchist);
        values.hosts.put("mythicupgrades_citrine_schist", mythicupgradesCitrineSchist);
        values.hosts.put("mythicupgrades_peridot_schist", mythicupgradesPeridotSchist);
        values.hosts.put("mythicupgrades_topaz_schist", mythicupgradesTopazSchist);
        values.hosts.put("mythicupgrades_sapphire_schist", mythicupgradesSapphireSchist);
        values.hosts.put("mythicupgrades_jade_schist", mythicupgradesJadeSchist);
        values.hosts.put("promenade_asphalt", promenadeAsphalt);
        values.hosts.put("promenade_blunite", promenadeBlunite);
        values.hosts.put("spawn_reefstone", spawnReefstone);
        values.hosts.put("biomeswevegone_dacite", biomeswevegoneDacite);
        values.hosts.put("biomeswevegone_white_dacite", biomeswevegoneWhiteDacite);
        values.hosts.put("biomeswevegone_red_rock", biomeswevegoneRedRock);
        // END GENERATED host switches
        values.oreVeins = oreVeins;
        values.geology = geology;
        values.sulfurCaves = sulfurCaves;
        values.cinnabarAmount = cinnabarAmount;

        values.bastionSafeNether = bastionSafeNether;
        values.netherOreRarity = netherOreRarity;
        values.netherVeinSize = netherVeinSize;

        values.overworldCopper = overworldCopper;
        values.dripstoneCopper = dripstoneCopper;
        values.createZinc = createZinc;
        values.zincVeinSize = zincVeinSize;

        values.mythicUpgrades = mythicUpgrades;
        values.netherGems = netherGems;
        values.netherGemSize = netherGemSize;

        values.mythicMetals = mythicMetals;

        values.silentGems = silentGems;
        values.silentGemsNether = silentGemsNether;
        values.silentGemsNetherRarity = silentGemsNetherRarity;
        values.silentGemsNetherVeinSize = silentGemsNetherVeinSize;

        values.denseMekanism = denseMekanism;
        values.powah = powah;
        values.tfmg = tfmg;
        values.energizedPower = energizedPower;
        values.expOres = expOres;
        values.iceAndFire = iceAndFire;
        values.techReborn = techReborn;
        values.techRebornNether = techRebornNether;
        values.bornInChaosInfectedDiamond = bornInChaosInfectedDiamond;
        values.extremeReactorsNether = extremeReactorsNether;
        values.cobblemon = cobblemon;
        values.cobblemonNether = cobblemonNether;
        values.modernIndustrialization = modernIndustrialization;
        values.occultism = occultism;
        values.immersiveEngineering = immersiveEngineering;
        values.mekanism = mekanism;
        values.oreganized = oreganized;
        values.malum = malum;
        values.extremeReactors = extremeReactors;
        values.mysticalAgriculture = mysticalAgriculture;
        values.things = things;
        values.silentGear = silentGear;
        values.createNewAge = createNewAge;
        values.biggerReactors = biggerReactors;

        SeamlessOresConfig.apply(values);
    }
}
