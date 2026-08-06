package com.chillpavz.seamlessores.config;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import me.shedaniel.autoconfig.AutoConfig;
import me.shedaniel.autoconfig.ConfigData;
import me.shedaniel.autoconfig.annotation.Config;
import me.shedaniel.autoconfig.annotation.ConfigEntry;
import me.shedaniel.autoconfig.serializer.GsonConfigSerializer;
import net.minecraft.world.InteractionResult;

import java.util.HashSet;
import java.util.Set;

/**
 * Cloth Config data class for NeoForge.
 *
 * <p><b>This file is duplicated verbatim in the fabric module and the two must stay identical.</b>
 * It cannot live in {@code common} because cloth-config is a loader dependency and common compiles
 * against vanilla only. The values are pushed into {@link SeamlessOresConfig}, which is where the
 * worldgen code reads them.
 *
 * <p>Everything here gates <i>generation</i>, never registration — see {@link SeamlessOresConfig}.
 */
@Config(name = Constants.MOD_ID)
public class SeamlessOresConfigData implements ConfigData {

    @ConfigEntry.Gui.Tooltip
    public boolean granite = true;

    @ConfigEntry.Gui.Tooltip
    public boolean diorite = true;

    @ConfigEntry.Gui.Tooltip
    public boolean andesite = true;

    @ConfigEntry.Gui.Tooltip
    public boolean tuff = true;

    /** Adds gold and quartz where vanilla has none — see the tooltip. */
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean basalt = true;

    /** Adds gold and quartz where vanilla has none — see the tooltip. */
    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean blackstone = true;

    @ConfigEntry.Gui.Tooltip(count = 2)
    public boolean oreVeins = true;

    @ConfigEntry.Gui.Tooltip
    public boolean createZinc = true;

    @ConfigEntry.Gui.Tooltip(count = 3)
    @ConfigEntry.BoundedDiscrete(min = 2, max = 12)
    public int zincVeinSize = 6;

    @ConfigEntry.Gui.Tooltip(count = 3)
    public boolean bastionSafeNether = true;

    @ConfigEntry.Gui.Tooltip
    public boolean mythicUpgrades = true;


    /** Registers the config and wires it to the common holder. Safe on client and dedicated server. */
    public static void register() {
        AutoConfig.register(SeamlessOresConfigData.class, GsonConfigSerializer::new);
        AutoConfig.getConfigHolder(SeamlessOresConfigData.class).registerSaveListener((holder, data) -> {
            data.push();
            return InteractionResult.SUCCESS;
        });
        AutoConfig.getConfigHolder(SeamlessOresConfigData.class).getConfig().push();
    }

    /** Copies these values into the loader-agnostic holder that worldgen reads. */
    public void push() {
        final Set<String> disabled = new HashSet<>();
        if (!granite) disabled.add("granite");
        if (!diorite) disabled.add("diorite");
        if (!andesite) disabled.add("andesite");
        if (!tuff) disabled.add("tuff");
        if (!basalt) disabled.add("basalt");
        if (!blackstone) disabled.add("blackstone");
        SeamlessOresConfig.apply(disabled, oreVeins, createZinc, zincVeinSize, bastionSafeNether, mythicUpgrades);
    }
}
