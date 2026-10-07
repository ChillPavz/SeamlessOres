package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.content.OreVariant;
import net.minecraft.resources.Identifier;

import java.util.List;
import java.util.Map;

/**
 * Which features each cinnabar ore mirrors.
 *
 * <p>A cinnabar ore gets one feature per feature of the ore it stands in for, copied from that
 * feature exactly (vein size, veins per chunk, height range, air exposure); only the target becomes
 * cinnabar, the biome the Sulfur Caves, and the vein count is tripled for the amount slider (see
 * {@code CinnabarOreFeature}). The generator reads the values out of each game and mod jar; this table
 * only names the sources. KEEP IN SYNC WITH CINNABAR_SOURCES in tools/generate_assets.py.
 *
 * <p>Gold's badlands-only extra feature is left out on purpose: it applies in badlands only.
 */
public final class CinnabarVeins {

    private CinnabarVeins() {
    }

    /** Ore name to the placed features it mirrors, by path in that ore's own namespace. */
    public static final Map<String, List<String>> SOURCES = Map.ofEntries(
            Map.entry("gold", List.of("ore_gold", "ore_gold_lower")),
            Map.entry("iron", List.of("ore_iron_upper", "ore_iron_middle", "ore_iron_small")),
            Map.entry("redstone", List.of("ore_redstone", "ore_redstone_lower")),
            Map.entry("zinc", List.of("zinc_ore")),
            Map.entry("galena", List.of("galena_ore")),
            Map.entry("techreborn_lead", List.of("lead_ore")),
            Map.entry("techreborn_silver", List.of("silver_ore")),
            Map.entry("pyrite", List.of("pyrite_ore")),
            Map.entry("sphalerite", List.of("sphalerite_ore")),
            Map.entry("occultism_silver", List.of("ore_silver", "ore_silver_deepslate")),
            Map.entry("silents_silver", List.of("silver_ore")));

    /** Our placed features for one cinnabar variant, e.g. {@code seamlessores:cinnabar_gold_ore_gold}. */
    public static List<Identifier> placedFeatures(OreVariant variant) {
        final String ore = variant.ore().name();
        return SOURCES.getOrDefault(ore, List.of()).stream()
                .map(source -> Identifier.fromNamespaceAndPath(Constants.MOD_ID, "cinnabar_" + ore + "_" + source))
                .toList();
    }
}
