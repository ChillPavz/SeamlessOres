package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.Structure;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

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
    public static final Identifier ID = Identifier.fromNamespaceAndPath(Constants.MOD_ID, "bastion_safe_ore");

    private static final ResourceKey<Structure> BASTION_REMNANT =
            ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath("minecraft", "bastion_remnant"));

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
    public static void register(java.util.function.BiConsumer<Identifier, Feature<?>> sink) {
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

        if (!SeamlessOresConfig.bastionSafeNether || !insideBastion(context)) {
            return Feature.ORE.place(context);
        }

        final List<OreConfiguration.TargetBlockState> vanillaOnly = withoutOurTargets(config.targetStates);
        if (vanillaOnly.isEmpty() || vanillaOnly.size() == config.targetStates.size()) {
            return Feature.ORE.place(context);
        }
        return Feature.ORE.place(new FeaturePlaceContext<>(
                Optional.empty(), context.level(), context.chunkGenerator(), context.random(),
                context.origin(),
                new OreConfiguration(vanillaOnly, config.size, config.discardChanceOnAirExposure)));
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
            return structures.getStructureWithPieceAt(
                    context.origin(), holder -> holder.is(BASTION_REMNANT)) != null;
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

        final Set<Block> ours = Set.copyOf(SeamlessOresContent.blocks().values());
        final List<OreConfiguration.TargetBlockState> kept = new ArrayList<>(targets.size());
        for (OreConfiguration.TargetBlockState target : targets) {
            if (!ours.contains(target.state.getBlock())) {
                kept.add(target);
            }
        }
        return kept;
    }
}
