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
 * <p><b>This file is triplicated VERBATIM in the fabric, neoforge and forge modules, and all three
 * must stay byte-identical.</b> It cannot live in {@code common} because cloth-config is a loader
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
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean oreVeins = true;


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

    // --- Ice and Fire ---------------------------------------------------------------------------

    @ConfigEntry.Category("ice_and_fire")
    @ConfigEntry.Gui.Tooltip
    public boolean iceAndFire = true;

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

    // --- Things ---------------------------------------------------------------------------------

    @ConfigEntry.Category("things")
    @ConfigEntry.Gui.Tooltip
    public boolean things = true;


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

        values.granite = granite;
        values.diorite = diorite;
        values.andesite = andesite;
        values.tuff = tuff;
        values.basalt = basalt;
        values.blackstone = blackstone;
        values.oreVeins = oreVeins;

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
        values.things = things;
        values.silentGear = silentGear;
        values.createNewAge = createNewAge;

        SeamlessOresConfig.apply(values);
    }
}
