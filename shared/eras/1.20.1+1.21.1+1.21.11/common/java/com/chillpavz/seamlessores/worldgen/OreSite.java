package com.chillpavz.seamlessores.worldgen;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.List;

/**
 * One ordered list of ore targets ({@code test -> state}, first match wins) inside some worldgen
 * feature, whatever the feature is and whichever Minecraft era it comes from.
 *
 * <p>The two injectors decide WHAT to add; the band's worldgen ({@link WorldgenEra#oreSites}) finds the
 * sites and knows HOW to rebuild them: a configured feature's {@code OreConfiguration}, the same target
 * list inside another mod's own configuration type, or one block list of one layer of Create's layered
 * ore.
 */
public interface OreSite {

    /** For the log: the feature's id, and which layer for a layered one. */
    String name();

    /** The site's own targets, in order, as they were when the site was found. */
    List<Target> targets();

    /** The site's vein size. */
    int size();

    /** False if this site's feature cannot be rebuilt. Says so in the log, once per kind. */
    boolean rebuildable(String injector);

    /** True for a target list kept in another mod's own configuration type rather than vanilla's. */
    default boolean foreign() {
        return false;
    }

    /**
     * Rebuilds the site with {@code rules} in FRONT of its own targets (first match wins, so appending
     * would never fire) and the given vein size. {@code bastionSafe}: the feature becomes our stand-in
     * that keeps a bastion's own blocks, where it is the plain ore feature.
     */
    void rebuild(List<Rule> rules, int size, boolean bastionSafe);

    /** One target: where {@code test} matches, the feature places {@code state}. */
    record Target(RuleTest test, BlockState state) {}

    /** What to add, in era-neutral terms. Each era turns a rule into its own target type. */
    sealed interface Rule permits Swallow, Receive, Add {}

    /** Stone side: where the stone's blob meets any of {@code forms}, place {@code becomes} instead. */
    record Swallow(List<Block> forms, Block becomes) implements Rule {}

    /**
     * Ore side: where {@code original} would place the ore AND the block is {@code stone}, place
     * {@code becomes} instead. Restyles ore that already generates there; adds none.
     */
    record Receive(RuleTest original, Block stone, Block becomes) implements Rule {}

    /**
     * Ore side, ADDING ore: wherever the feature's vein reaches {@code stone}, place {@code becomes}.
     * For the Nether hosts, which no ore feature of the game's own targets.
     */
    record Add(Block stone, Block becomes) implements Rule {}
}
