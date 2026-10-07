package com.chillpavz.seamlessores.matrix.worldgen;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.List;

/**
 * One ordered list of ore targets ({@code test -> state}, first match wins) inside some worldgen
 * feature, whatever the feature is and whichever Minecraft era it comes from.
 *
 * <p>The two injectors decide WHAT to add; {@code OreSites}, which each era supplies in its own source
 * folder, finds the sites and knows HOW to rebuild them. At 26.3 a site is a {@code Feature} holding
 * block replacements; before 26.3 it is a configured feature's {@code OreConfiguration}, or one block
 * list of one layer of Create's layered ore.
 */
public interface OreSite {

    /** For the log: the feature's id, and which layer for a layered one. */
    String name();

    /** The site's own targets, in order, as they were when the site was found. */
    List<Target> targets();

    /** False if this site's feature cannot be rebuilt. Says so in the log, once per kind. */
    boolean rebuildable(String injector);

    /** Puts {@code rules} in FRONT of the site's own targets. First match wins, so appending would never fire. */
    void prepend(List<Rule> rules);

    /** One target: where {@code test} matches, the feature places {@code state}. */
    record Target(RuleTest test, BlockState state) {}

    /** What to add, in era-neutral terms. Each era turns a rule into its own target type. */
    sealed interface Rule permits Swallow, Receive {}

    /** Stone side: where the stone's blob meets any of {@code forms}, place {@code becomes} instead. */
    record Swallow(List<Block> forms, Block becomes) implements Rule {}

    /**
     * Ore side: where {@code original} would place the ore AND the block is {@code stone}, place
     * {@code becomes} instead.
     */
    record Receive(RuleTest original, Block stone, Block becomes) implements Rule {}
}
