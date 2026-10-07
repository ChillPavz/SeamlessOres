package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.Structure;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * A drop-in stand-in for {@code minecraft:ore} that declines to convert blocks inside a bastion.
 *
 * <h2>The problem this exists for</h2>
 * Bastion remnants are built out of the very blocks the nether variants replace: plain
 * {@code blackstone} appears in 125 of vanilla's 167 bastion structure files and {@code basalt} in
 * 103. Structures are placed at the {@code surface_structures} generation step, which runs BEFORE
 * {@code underground_ores} — verified from {@code GenerationStep.Decoration}, where they are steps 5
 * and 7. So the bastion's blocks are already in the world when the ore feature runs, and an ore
 * feature that matches blackstone will happily turn a bastion's walls and floors into gold ore.
 *
 * <p>Vanilla never hits this because {@code ore_nether_gold} and {@code ore_quartz} match
 * {@code minecraft:netherrack} only — the problem is created by our own added targets, so it is ours
 * to fix. Left alone it invites players to strip-mine the structure, which is the opposite of what a
 * bastion is for.
 *
 * <h2>How it avoids reimplementing vanilla</h2>
 * This does NOT copy {@code OreFeature}'s vein algorithm. It decides which target list to use and
 * then delegates to {@link Feature#ORE} with a rebuilt {@link FeaturePlaceContext}. Inside a bastion
 * it passes vanilla's own targets only, so the position still becomes ordinary netherrack-backed ore
 * exactly as it would without this mod; everywhere else it passes the full list untouched.
 *
 * <p>The check is per feature placement rather than per block, tested at the vein's origin against
 * {@code getStructureWithPieceAt} (which tests real piece bounding boxes, not the structure's whole
 * area). Nether ore veins are {@code size} 10-14, so this is accurate to within a couple of blocks
 * at a bastion's outer edge, and it costs one lookup per vein instead of one per block.
 */
public class BastionSafeOreFeature extends Feature<OreConfiguration> {

    /** Registered under our own namespace; see {@link #register}. */
    public static final ResourceLocation ID = new ResourceLocation(Constants.MOD_ID, "bastion_safe_ore");

    private static final ResourceKey<Structure> BASTION_REMNANT =
            ResourceKey.create(Registries.STRUCTURE, new ResourceLocation("minecraft", "bastion_remnant"));

    /** Guards the one time diagnostic in {@link #place}. */
    private static final java.util.concurrent.atomic.AtomicBoolean REPORTED =
            new java.util.concurrent.atomic.AtomicBoolean();

    /** Set once at registration so the injector can build ConfiguredFeatures against it. */
    private static BastionSafeOreFeature instance;

    public BastionSafeOreFeature() {
        super(OreConfiguration.CODEC);
    }

    /**
     * Registers the feature through the caller's own registry path, exactly like the blocks and
     * items - NeoForge only accepts registrations from inside {@code RegisterEvent}, so this cannot
     * simply write to {@code BuiltInRegistries} itself.
     *
     * <p>It uses {@code OreConfiguration.CODEC}, so a ConfiguredFeature built on it serialises and
     * deserialises exactly like a vanilla ore feature.
     */
    public static void register(java.util.function.BiConsumer<ResourceLocation, Feature<?>> sink) {
        if (instance == null) {
            instance = new BastionSafeOreFeature();
            sink.accept(ID, instance);
        }
    }

    public static BastionSafeOreFeature get() {
        return instance;
    }

    @Override
    public boolean place(FeaturePlaceContext<OreConfiguration> context) {
        final OreConfiguration config = context.config();

        final boolean blocked =
                (SeamlessOresConfig.bastionSafeNether && insideBastion(context))
                        || !rarityAllows(context, config);
        if (!blocked) {
            return Feature.ORE.place(context);
        }

        final List<OreConfiguration.TargetBlockState> vanillaOnly = withoutOurTargets(config.targetStates);
        if (vanillaOnly.isEmpty() || vanillaOnly.size() == config.targetStates.size()) {
            return Feature.ORE.place(context);
        }

        // One line the first time this fires, because "the guard matched everything" is otherwise a
        // completely silent failure: no variants generate and nothing is logged. If this appears the
        // moment you enter the Nether, at a position nowhere near a bastion, the check is wrong.
        if (REPORTED.compareAndSet(false, true)) {
            Constants.LOG.info("Bastion protection: first vein redirected at {} (expected only inside"
                    + " a bastion remnant)", context.origin());
        }
        return Feature.ORE.place(new FeaturePlaceContext<>(
                Optional.empty(), context.level(), context.chunkGenerator(), context.random(),
                context.origin(),
                new OreConfiguration(vanillaOnly, config.size, config.discardChanceOnAirExposure)));
    }

    /**
     * Whether this vein is one of the {@code 1 in netherOreRarity} that actually converts.
     *
     * <h2>Why the roll is hashed from the position rather than taken from the RandomSource</h2>
     * {@code context.random()} is the same stream {@code OreFeature} then uses to shape the vein.
     * Drawing a number from it would shift every subsequent value and move vanilla's own netherrack
     * gold and quartz, quietly breaking the one property we still hold in the Nether. Hashing the
     * origin instead is deterministic, stable for a given seed, and leaves the stream untouched.
     *
     * <h2>Why ruby and sapphire are exempt</h2>
     * They get their own, far rarer placement. Stacking this on top would put them near 1 in 100
     * chunks, which stops being rare and starts being invisible.
     */
    private static boolean rarityAllows(FeaturePlaceContext<OreConfiguration> context,
                                        OreConfiguration config) {
        final int rarity = rarityFor(config);
        if (rarity <= 1) {
            return true;
        }
        long hash = context.origin().asLong() * 0x9E3779B97F4A7C15L;
        hash ^= hash >>> 32;
        return Math.floorMod(hash, rarity) == 0L;
    }

    /**
     * The rarity dial that governs this feature: the strictest one applying to any of our nether
     * blocks in its target list, or 1 (no thinning) if none applies.
     *
     * <p>Which dial that is depends on who owns the ore — our own gold and quartz answer to
     * {@code netherOreRarity}, Silent's Gems' nether gems to their own copy of it, and everything
     * else is exempt. See {@link SeamlessOresConfig#netherRarityFor}.
     *
     * <p>Resolved through the variant rather than by testing the block id for a {@code _gold_ore} /
     * {@code _quartz_ore} suffix, which is what this used to do. The suffix test could not tell our
     * gold from Mythic Metals' {@code basalt_midas_gold_ore}, which also ends in {@code _gold_ore}
     * and is meant to be exempt — so it was already thinning a mod it was never meant to touch.
     */
    private static int rarityFor(OreConfiguration config) {
        int rarity = 1;
        for (OreConfiguration.TargetBlockState target : config.targetStates) {
            final OreVariant variant = SeamlessOresContent.variantOf(target.state.getBlock());
            if (variant == null || variant.host().tier() != OreTier.NETHER) {
                continue;   // not ours, or an overworld host: never thinned
            }
            rarity = Math.max(rarity, SeamlessOresConfig.netherRarityFor(variant.ore().requiredModId()));
        }
        return rarity;
    }

    private static boolean insideBastion(FeaturePlaceContext<OreConfiguration> context) {
        try {
            net.minecraft.world.level.StructureManager structures =
                    context.level().getLevel().structureManager();
            // forWorldGenRegion scopes the lookup to the region currently being generated. That is
            // the API's own answer to "I need structures from inside a feature", and it is what
            // keeps this off the live ServerLevel while a chunk is still being built.
            if (context.level() instanceof net.minecraft.server.level.WorldGenRegion region) {
                structures = structures.forWorldGenRegion(region);
            }
            // MUST be isValid(), NOT a null check. getStructureWithPieceAt returns
            // StructureStart.INVALID_START when nothing matches and never returns null, so `!= null`
            // is always true. That shipped once and silently disabled every nether variant in the
            // world: each vein was treated as being inside a bastion and fell back to vanilla's
            // targets, so no basalt or blackstone ore generated anywhere, with nothing in the log.
            // 1.20.1 has a direct ResourceKey overload; the Predicate<Holder<Structure>> form the
            // newer branches use does not exist here. Same lookup, same semantics.
            return structures.getStructureWithPieceAt(context.origin(), BASTION_REMNANT).isValid();
        } catch (RuntimeException failure) {
            // A structure lookup must never take worldgen down with it. Failing open just means the
            // old behaviour for this one vein.
            Constants.LOG.debug("Bastion lookup failed at {}", context.origin(), failure);
            return false;
        }
    }

    /** Drops the targets whose result is one of our blocks, leaving the host mod's own entries. */
    private static List<OreConfiguration.TargetBlockState> withoutOurTargets(
            List<OreConfiguration.TargetBlockState> targets) {

        final List<OreConfiguration.TargetBlockState> kept = new ArrayList<>(targets.size());
        for (OreConfiguration.TargetBlockState target : targets) {
            if (SeamlessOresContent.variantOf(target.state.getBlock()) == null) {
                kept.add(target);
            }
        }
        return kept;
    }
}
