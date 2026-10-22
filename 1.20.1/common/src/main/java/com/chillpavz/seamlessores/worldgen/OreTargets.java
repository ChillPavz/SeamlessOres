package com.chillpavz.seamlessores.worldgen;

import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.templatesystem.AlwaysTrueTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockStateMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.TagMatchTest;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** The ore target list, as these versions write it: the part of every band's worldgen that is the same. */
final class OreTargets {

    private OreTargets() {}

    /**
     * Other mods' rule tests whose answer depends on the block alone, read from their bytecode.
     * Electrodynamics' asks its own ore switch and then whether the block is in a tag.
     */
    private static final Set<String> BLOCK_ONLY_FOREIGN = Set.of("electrodynamics.common.world.ruletests.RuleTestOre");

    /** Seeded, and only handed to rule tests that never read it; see {@link #receives}. */
    private static final RandomSource UNUSED = RandomSource.create(0L);

    /**
     * Whether {@code original} would place its ore in {@code stone}, asked once, here, for the rule tests
     * whose answer depends on the block alone. A random test (a chance to match) is never evaluated, and
     * never added to.
     */
    static boolean receives(RuleTest original, Block stone) {
        final boolean blockOnly = original instanceof TagMatchTest || original instanceof BlockMatchTest
                || original instanceof BlockStateMatchTest || original instanceof AlwaysTrueTest
                || BLOCK_ONLY_FOREIGN.contains(original.getClass().getName());
        return blockOnly && original.test(stone.defaultBlockState(), UNUSED);
    }

    /**
     * Our rules as targets, in order. A swallow rule is one target per form of the ore (first match wins,
     * so the result is the same); an ore side rule is a block match on the stone, once per stone and
     * result: without the original test, two of them would be the same target.
     */
    static List<OreConfiguration.TargetBlockState> targetsOf(List<OreSite.Rule> rules) {
        final List<OreConfiguration.TargetBlockState> out = new ArrayList<>();
        final Set<List<Block>> matched = new HashSet<>();
        for (OreSite.Rule rule : rules) {
            if (rule instanceof OreSite.Swallow swallow) {
                for (Block form : swallow.forms()) {
                    out.add(OreConfiguration.target(new BlockMatchTest(form), swallow.becomes().defaultBlockState()));
                }
            } else if (rule instanceof OreSite.Receive receive) {
                stoneMatch(out, matched, receive.stone(), receive.becomes());
            } else if (rule instanceof OreSite.Add add) {
                stoneMatch(out, matched, add.stone(), add.becomes());
            }
        }
        return out;
    }

    private static void stoneMatch(List<OreConfiguration.TargetBlockState> out, Set<List<Block>> matched,
                                   Block stone, Block becomes) {
        if (matched.add(List.of(stone, becomes))) {
            out.add(OreConfiguration.target(new BlockMatchTest(stone), becomes.defaultBlockState()));
        }
    }
}
