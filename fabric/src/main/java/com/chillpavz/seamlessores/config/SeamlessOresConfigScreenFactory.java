package com.chillpavz.seamlessores.config;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.platform.Services;
import me.shedaniel.autoconfig.AutoConfig;
import me.shedaniel.autoconfig.gui.ConfigScreenProvider;
import me.shedaniel.clothconfig2.api.ConfigBuilder;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Supplier;

/**
 * Builds the config screen: cloth's SIDEBAR layout, showing only the mods actually installed.
 *
 * <p><b>This file is triplicated VERBATIM in the fabric, neoforge and forge modules, and all three
 * must stay byte-identical.</b> It cannot live in {@code common} because cloth-config is a loader
 * dependency. It is also <b>client-only</b> — it names {@code Screen}, which does not exist on a
 * dedicated server — so it must only ever be reached from a client-guarded hook, exactly like
 * NeoForge's {@code SeamlessOresConfigScreen}.
 *
 * <h2>Why the layout is switched</h2>
 * Cloth's default {@code ClothConfigScreen} lays the categories out as a horizontal tab strip. That
 * is fine for four or five categories and stops working at thirteen: the strip overflows, and its
 * two arrow buttons are <b>not</b> "previous/next tab" — read out of the real jar, the left one is
 * {@code tabsScroller.scrollTo(0)} and the right one {@code tabsScroller.scrollTo(getMaxScroll())},
 * i.e. jump-to-start and jump-to-end. They also only scroll the strip; neither selects anything. On
 * top of that each arrow is disabled while the strip is already at that end, so at the default
 * position the left arrow is greyed out and reads as missing. The practical result is that the
 * middle categories can only be reached by scrolling the strip by hand.
 *
 * <p>None of that is configurable, and changing it would mean mixing into another mod's GUI class —
 * fragile at the best of times and multiplied by every branch and loader we ship. Cloth already
 * ships the answer: {@code setGlobalized(true)} selects {@code GlobalizedClothConfigScreen}, which
 * replaces the strip with a vertically scrolling sidebar listing every category, plus a search
 * field. Nothing overflows, every category is one click away, and it is cloth's own supported
 * layout rather than our patch of theirs.
 *
 * <h2>Why this can hook in without reflection</h2>
 * {@code AutoConfig.getConfigScreen} does not merely return some {@code Supplier<Screen>}; it
 * returns the {@link ConfigScreenProvider} it just built (verified by disassembling the method). The
 * provider exposes a public {@code setBuildFunction}, which runs against the fully populated
 * {@code ConfigBuilder} just before {@code build()}. So both the layout and the category list can be
 * changed with no reflection, no access widening and no mixin.
 *
 * <p>The {@code instanceof} is a real guard rather than a formality: if a future cloth stops
 * returning the provider, this silently keeps the old tabbed screen with every category showing,
 * instead of throwing on the way to a config button. Degrade, never crash.
 */
public final class SeamlessOresConfigScreenFactory {

    private SeamlessOresConfigScreenFactory() {}

    /** AutoConfig's own key shape, so these match the categories it created. */
    private static final String CATEGORY_PREFIX = "text.autoconfig." + Constants.MOD_ID + ".category.";

    /**
     * Mod id -> the config category that mod owns.
     *
     * <p>Only third-party mods appear here. Overworld and Nether are vanilla and always shown.
     *
     * <p>Kept ordered for readability only; the screen's order comes from the field declaration
     * order in {@link SeamlessOresConfigData}, not from this map.
     */
    private static final Map<String, String> MOD_CATEGORIES = new LinkedHashMap<>();

    static {
        MOD_CATEGORIES.put("create", "create");
        MOD_CATEGORIES.put("create_new_age", "create_new_age");
        MOD_CATEGORIES.put("tfmg", "tfmg");
        MOD_CATEGORIES.put("densemekanism", "dense_mekanism");
        MOD_CATEGORIES.put("energizedpower", "energized_power");
        MOD_CATEGORIES.put("expores", "exp_ores");
        MOD_CATEGORIES.put("iceandfire", "ice_and_fire");
        MOD_CATEGORIES.put("mythicmetals", "mythic_metals");
        MOD_CATEGORIES.put("mythicupgrades", "mythic_upgrades");
        MOD_CATEGORIES.put("powah", "powah");
        MOD_CATEGORIES.put("silentgear", "silent_gear");
        MOD_CATEGORIES.put("silentgems", "silents_gems");
        MOD_CATEGORIES.put("things", "things");
    }

    /** The config screen to open, given whatever screen the player came from. */
    public static Screen create(Screen parent) {
        final Supplier<Screen> supplier = AutoConfig.getConfigScreen(SeamlessOresConfigData.class, parent);

        if (supplier instanceof ConfigScreenProvider<?> provider) {
            provider.setBuildFunction(builder -> {
                builder.setGlobalized(true);
                // Start the sidebar open, so every category name is readable straight away.
                // Collapsed it shows a thin strip, which reintroduces the problem this solves.
                builder.setGlobalizedExpanded(true);
                hideCategoriesOfAbsentMods(builder);
                return builder.build();
            });
        } else {
            Constants.LOG.warn("Cloth Config returned {} rather than a ConfigScreenProvider - "
                            + "falling back to its tabbed layout with every category showing",
                    supplier.getClass().getName());
        }

        return supplier.get();
    }

    /**
     * Drops the category of every supported mod that is not installed.
     *
     * <p>Purely a display decision, and deliberately so. The field stays on the data class, so the
     * value stays in the config FILE and keeps being pushed into the worldgen holder — uninstalling
     * a mod and putting it back does not silently reset how you had it configured. It also cannot
     * desync anything: the registered block set is derived from the loaded mod set on both sides,
     * and config only ever gates injection.
     *
     * <p>The mod list is taken from {@link OreType#ALL} rather than written out again here, so the
     * screen cannot drift from the ores that actually exist. A mod that owns an ore but has no
     * category mapped is reported rather than ignored: the failure mode otherwise is a category
     * that is simply always visible, which nobody would notice.
     */
    private static void hideCategoriesOfAbsentMods(ConfigBuilder builder) {
        for (OreType ore : OreType.ALL) {
            final String modId = ore.requiredModId();
            if (modId == null) {
                continue;                       // vanilla ore, no category of its own
            }
            final String category = MOD_CATEGORIES.get(modId);
            if (category == null) {
                Constants.LOG.warn("No config category mapped for mod '{}' - its options will always"
                        + " be shown. Add it to SeamlessOresConfigScreenFactory.MOD_CATEGORIES.", modId);
                continue;
            }
            if (!Services.PLATFORM.isModLoaded(modId)) {
                builder.removeCategoryIfExists(Component.translatable(CATEGORY_PREFIX + category));
            }
        }
    }
}
