package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.BiConsumer;

/**
 * A plain ore vein into Vanilla Backport's cinnabar, placed only while the cinnabar host is switched
 * on and only in its Sulfur Caves. These veins ADD ore (see {@code OreTier.CINNABAR}), so they need a
 * switch, and a data-driven {@code minecraft:ore} cannot read one.
 *
 * <p>The configuration names the ore by id and takes cinnabar from the host table at run time, so no
 * data file names {@code minecraft:cinnabar}: without Vanilla Backport the block does not exist, and a
 * worldgen file naming an absent block is a hard crash, not a skip. The features are attached to the
 * cave biomes by tag (NeoForge, Forge) or by key (Fabric), so the biome is tested here. Everything else
 * is vanilla's ore feature.
 */
public class CinnabarOreFeature extends Feature<CinnabarOreFeature.Config> {

    public static final ResourceLocation ID = ResourceLocation.tryParse(Constants.MOD_ID + ":cinnabar_ore");

    /**
     * Vanilla's ore configuration minus its targets: the vein's size and air exposure, and our ore.
     * {@code factor}: how many times the default count the data attempts (3; 1 where three times would
     * pass the game's cap of 256 on a placement count), so the slider keeps amount / (100 x factor).
     */
    public record Config(int size, float discardChanceOnAirExposure, ResourceLocation ore, int factor)
            implements FeatureConfiguration {
        public static final Codec<Config> CODEC = RecordCodecBuilder.create(instance -> instance.group(
                Codec.intRange(0, 64).fieldOf("size").forGetter(Config::size),
                Codec.floatRange(0.0F, 1.0F).fieldOf("discard_chance_on_air_exposure").forGetter(Config::discardChanceOnAirExposure),
                ResourceLocation.CODEC.fieldOf("ore").forGetter(Config::ore),
                Codec.intRange(1, 3).optionalFieldOf("factor", 3).forGetter(Config::factor)
        ).apply(instance, Config::new));
    }

    /** What a configuration resolves to: vanilla's ore configuration, and the mod whose switch gates it. */
    private record Resolved(OreConfiguration ore, String modId) {
    }

    private static CinnabarOreFeature instance;

    /** The vanilla configuration each one stands for, built on first use (every block exists by then). */
    private static final Map<Config, Optional<Resolved>> RESOLVED = new ConcurrentHashMap<>();

    public CinnabarOreFeature() {
        super(Config.CODEC);
    }

    public static void register(BiConsumer<ResourceLocation, Feature<?>> sink) {
        if (instance == null) {
            instance = new CinnabarOreFeature();
            sink.accept(ID, instance);
        }
    }

    @Override
    public boolean place(FeaturePlaceContext<Config> context) {
        // The data attempts each vein at three times the default count; the slider keeps a share.
        if (!HostStone.CINNABAR.present() || !SeamlessOresConfig.isHostEnabled("cinnabar")
                || context.random().nextInt(100 * context.config().factor()) >= SeamlessOresConfig.cinnabarAmount
                || !context.level().getBiome(context.origin()).is(SulfurCaves.BIOME)) {
            return false;
        }
        final Optional<Resolved> resolved = RESOLVED.computeIfAbsent(context.config(), CinnabarOreFeature::resolve);
        // A modded ore follows our own switch for its mod, which stands in for that mod's own placement
        // filter (Create's config_filter), left out of the data because it exists only with the mod.
        if (resolved.isEmpty() || (resolved.get().modId() != null
                && !SeamlessOresConfig.isModOreEnabled(resolved.get().modId(), false))) {
            return false;
        }
        return Feature.ORE.place(new FeaturePlaceContext<>(Optional.empty(), context.level(),
                context.chunkGenerator(), context.random(), context.origin(), resolved.get().ore()));
    }

    private static Optional<Resolved> resolve(Config config) {
        final Block cinnabar = HostStone.CINNABAR.present() ? HostStone.CINNABAR.block() : null;
        final Block ore = BuiltInRegistries.BLOCK.getOptional(config.ore()).orElse(null);
        final OreVariant variant = ore == null ? null : SeamlessOresContent.variantOf(ore);
        if (cinnabar == null || variant == null) {
            return Optional.empty();
        }
        return Optional.of(new Resolved(new OreConfiguration(List.of(OreConfiguration.target(new BlockMatchTest(cinnabar),
                ore.defaultBlockState())), config.size(), config.discardChanceOnAirExposure()),
                variant.ore().requiredModId()));
    }
}
