package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Map;
import java.util.Set;

/**
 * The geology option: ores that could never form in granite, diorite, andesite or tuff.
 *
 * <p>With the option on, such an ore is refused in that rock: where the ore feature would have put it,
 * the rock stays rock. That REMOVES ore, so the option is off by default. Worldgen only; every block
 * stays registered. The lenient rule set: only what geology rules out plainly, keyed by
 * {@link OreType#name()}; a name this band does not have simply never matches.
 */
public final class OreGeology {

    private OreGeology() {}

    private static final Set<String> PLUTONIC = Set.of("granite", "diorite");
    private static final Set<String> IGNEOUS = Set.of("granite", "diorite", "andesite");
    private static final Set<String> ALL = Set.of("granite", "diorite", "andesite", "tuff");
    private static final Set<String> GRANITE = Set.of("granite");

    private static final Map<String, Set<String>> REFUSED = Map.ofEntries(
            // Coal needs a swamp; granite and diorite never had one. Ash falls on coal swamps, so tuff
            // keeps it, and andesite rarely (lava over a coal basin).
            Map.entry("coal", PLUTONIC),
            Map.entry("lignite_coal", PLUTONIC),
            // Diamond needs a kimberlite pipe. Its crater is pyroclastic, so tuff keeps it.
            Map.entry("diamond", IGNEOUS),
            Map.entry("white_diamond", IGNEOUS),
            Map.entry("black_diamond", IGNEOUS),
            Map.entry("bort", IGNEOUS),
            // Salt is an evaporite: sedimentary only.
            Map.entry("salt", ALL),
            // Ammolite is fossil shell; tuff keeps it (found beside ash beds).
            Map.entry("ammolite", IGNEOUS),
            // Corundum and olivine never coexist with free quartz.
            Map.entry("ruby", GRANITE),
            Map.entry("sapphire", GRANITE),
            Map.entry("techreborn_ruby", GRANITE),
            Map.entry("techreborn_sapphire", GRANITE),
            Map.entry("peridot", GRANITE),
            Map.entry("silents_peridot", GRANITE),
            // Nickel and the platinum group are mafic to ultramafic.
            Map.entry("nickel", GRANITE),
            Map.entry("mi_nickel", GRANITE),
            Map.entry("ie_nickel", GRANITE),
            Map.entry("platinum", GRANITE),
            Map.entry("iridium", GRANITE),
            Map.entry("mi_iridium", GRANITE),
            Map.entry("osmium", GRANITE),
            Map.entry("dense_osmium", GRANITE),
            Map.entry("mek_osmium", GRANITE));

    /**
     * What an ore target for {@code variant} places: our block, or, with the option on and the pair
     * refused, the host rock itself (the ore is removed).
     */
    public static BlockState placed(OreVariant variant, Block ours) {
        return SeamlessOresConfig.geology && refuses(variant.host().name(), variant.ore().name())
                ? variant.host().block().defaultBlockState()
                : ours.defaultBlockState();
    }

    /** Whether the option, when on, refuses this ore in this host. */
    public static boolean refuses(String host, String ore) {
        return REFUSED.getOrDefault(ore, Set.of()).contains(host);
    }
}
