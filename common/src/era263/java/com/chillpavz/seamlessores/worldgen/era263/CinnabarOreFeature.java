package com.chillpavz.seamlessores.worldgen.era263;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.AbstractOreFeature;
import net.minecraft.world.level.levelgen.feature.BlockReplacement;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.OreFeature;

import java.util.List;
import java.util.function.BiConsumer;

/**
 * A plain ore vein that places only while the cinnabar host is switched on. See
 * {@code OreTier.CINNABAR}: these veins ADD ore to the Sulfur Caves' cinnabar, so they need a switch,
 * and a data-driven {@code minecraft:ore} cannot read one. Everything else is vanilla's ore feature.
 */
public class CinnabarOreFeature extends AbstractOreFeature {

    public static final Identifier ID = Identifier.fromNamespaceAndPath(Constants.MOD_ID, "cinnabar_ore");

    public static final MapCodec<CinnabarOreFeature> CODEC = makeCodec(CinnabarOreFeature::new);

    private static boolean registered;

    private final OreFeature ore;

    public CinnabarOreFeature(List<BlockReplacement> targets, int size, float discardChanceOnAirExposure) {
        super(targets, size, discardChanceOnAirExposure);
        this.ore = new OreFeature(targets, size, discardChanceOnAirExposure);
    }

    public static void register(BiConsumer<Identifier, MapCodec<? extends Feature>> sink) {
        if (!registered) {
            registered = true;
            sink.accept(ID, CODEC);
        }
    }

    @Override
    public MapCodec<CinnabarOreFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        return SeamlessOresConfig.isHostEnabled("cinnabar") && ore.place(level, generator, random, origin);
    }
}
