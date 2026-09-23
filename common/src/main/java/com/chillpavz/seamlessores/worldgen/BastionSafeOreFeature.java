package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.AbstractOreFeature;
import net.minecraft.world.level.levelgen.feature.BlockReplacement;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.OreFeature;
import net.minecraft.world.level.levelgen.structure.Structure;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BiConsumer;

/**
 * A drop-in stand-in for {@code minecraft:ore} that declines to convert blocks inside a bastion.
 *
 * <h2>The problem this exists for</h2>
 * Bastion remnants are built out of the very blocks the Nether variants replace: plain
 * {@code blackstone} appears in 125 of vanilla's 167 bastion structure files and {@code basalt} in
 * 103. Structures are placed at the {@code surface_structures} step, before {@code underground_ores},
 * so a bastion's blocks are already in the world when the ore feature runs, and an ore feature that
 * matches blackstone would turn its walls and floors into gold ore. Vanilla never hits this because
 * its nether features match netherrack only: the problem is created by our own added targets.
 *
 * <h2>How it avoids reimplementing vanilla</h2>
 * It does NOT copy the vein algorithm. From 26.3 a feature carries its own replacements, so this holds
 * two {@link OreFeature}s built from the same numbers: one with every replacement, one with only the
 * host mod's own (ours stripped). Inside a bastion, or on a vein the rarity dial skips, it places the
 * second, so the position still becomes ordinary netherrack ore exactly as it would without this mod;
 * everywhere else it places the first.
 *
 * <p>The check is per placement rather than per block, tested at the vein's origin against real
 * structure piece bounding boxes. Nether veins are size 10-14, so this is accurate to within a couple
 * of blocks at a bastion's outer edge, for one lookup per vein.
 */
public class BastionSafeOreFeature extends AbstractOreFeature {

    /** Registered under our own namespace as a feature TYPE; see {@link #register}. */
    public static final Identifier ID = Identifier.fromNamespaceAndPath(Constants.MOD_ID, "bastion_safe_ore");

    public static final MapCodec<BastionSafeOreFeature> CODEC = makeCodec(BastionSafeOreFeature::new);

    private static final ResourceKey<Structure> BASTION_REMNANT =
            ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath("minecraft", "bastion_remnant"));

    /** Guards the one time diagnostic in {@link #place}. */
    private static final AtomicBoolean REPORTED = new AtomicBoolean();

    private static boolean registered;

    private final OreFeature everything;
    /** Null when there is nothing of ours to strip, so the full feature serves every case. */
    private final OreFeature vanillaOnly;

    public BastionSafeOreFeature(List<BlockReplacement> targets, int size, float discardChanceOnAirExposure) {
        super(targets, size, discardChanceOnAirExposure);
        this.everything = new OreFeature(targets, size, discardChanceOnAirExposure);
        final List<BlockReplacement> kept = withoutOurTargets(targets);
        this.vanillaOnly = kept.isEmpty() || kept.size() == targets.size()
                ? null
                : new OreFeature(kept, size, discardChanceOnAirExposure);
    }

    /**
     * Registers the codec through the caller's own registry path, exactly like the blocks and items:
     * NeoForge only accepts registrations from inside {@code RegisterEvent}. From 26.3 a feature TYPE
     * is its codec, in {@code FEATURE_TYPE}.
     */
    public static void register(BiConsumer<Identifier, MapCodec<? extends Feature>> sink) {
        if (!registered) {
            registered = true;
            sink.accept(ID, CODEC);
        }
    }

    @Override
    public MapCodec<BastionSafeOreFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        final boolean blocked =
                (SeamlessOresConfig.bastionSafeNether && insideBastion(level, origin))
                        || !rarityAllows(origin);
        if (!blocked || vanillaOnly == null) {
            return everything.place(level, generator, random, origin);
        }
        // One line the first time this fires, because "the guard matched everything" is otherwise a
        // completely silent failure: no variants generate and nothing is logged.
        if (REPORTED.compareAndSet(false, true)) {
            Constants.LOG.info("Bastion protection: first vein redirected at {} (expected only inside"
                    + " a bastion remnant, or on a vein the rarity setting skips)", origin);
        }
        return vanillaOnly.place(level, generator, random, origin);
    }

    /**
     * Whether this vein is one of the {@code 1 in netherOreRarity} that actually converts.
     *
     * <p>Hashed from the position rather than drawn from the RandomSource: the vein shape is drawn
     * from that same stream, and taking a number from it would move vanilla's own netherrack ore.
     */
    private boolean rarityAllows(BlockPos origin) {
        final int rarity = rarity();
        if (rarity <= 1) {
            return true;
        }
        long hash = origin.asLong() * 0x9E3779B97F4A7C15L;
        hash ^= hash >>> 32;
        return Math.floorMod(hash, rarity) == 0L;
    }

    /**
     * The strictest rarity dial that applies to any of our Nether blocks in this feature, or 1. Read
     * live, so a changed setting applies to the next world without rebuilding anything.
     */
    private int rarity() {
        int rarity = 1;
        for (BlockReplacement target : targetStates()) {
            final OreVariant variant = SeamlessOresContent.variantOf(target.state().getBlock());
            if (variant == null || variant.host().tier() != OreTier.NETHER) {
                continue;
            }
            rarity = Math.max(rarity, SeamlessOresConfig.netherRarityFor(variant.ore().requiredModId()));
        }
        return rarity;
    }

    private static boolean insideBastion(WorldGenLevel level, BlockPos origin) {
        try {
            net.minecraft.world.level.StructureManager structures = level.getLevel().structureManager();
            // forWorldGenRegion scopes the lookup to the region being generated, which keeps this off
            // the live ServerLevel while a chunk is still being built.
            if (level instanceof net.minecraft.server.level.WorldGenRegion region) {
                structures = structures.forWorldGenRegion(region);
            }
            // MUST be isValid(), NOT a null check: nothing matching returns INVALID_START, never null.
            return structures.getStructureWithPieceAt(origin, holder -> holder.is(BASTION_REMNANT)).isValid();
        } catch (RuntimeException failure) {
            // A structure lookup must never take worldgen down with it.
            Constants.LOG.debug("Bastion lookup failed at {}", origin, failure);
            return false;
        }
    }

    /** Drops the replacements whose result is one of our blocks, leaving the host mod's own. */
    private static List<BlockReplacement> withoutOurTargets(List<BlockReplacement> targets) {
        final List<BlockReplacement> kept = new ArrayList<>(targets.size());
        for (BlockReplacement target : targets) {
            if (SeamlessOresContent.variantOf(target.state().getBlock()) == null) {
                kept.add(target);
            }
        }
        return kept;
    }
}
