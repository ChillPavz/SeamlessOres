package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.AbstractOreFeature;
import net.minecraft.world.level.levelgen.feature.BlockReplacement;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.ScatteredOreFeature;

import java.util.ArrayList;
import java.util.List;
import java.util.function.BiConsumer;

/**
 * Places Mythic Upgrades' ruby and sapphire in basalt deltas, as scattered single blocks.
 *
 * <h2>Why this feature exists at all</h2>
 * Everything else in this mod restyles ore that was already going to be there. This one genuinely adds
 * generation, because there is nothing to extend: Mythic Upgrades restricts ruby and sapphire ORE to
 * its own {@code mythic_rifts} biome, so our basalt and blackstone variants had nowhere to appear. It
 * extends that mod's own intent, since it already injects ruby and sapphire geodes into every Nether
 * biome.
 *
 * <h2>Why it delegates to scattered ore</h2>
 * Copied from ancient debris, vanilla's "rare prize you dig for": single blocks spread around the
 * origin rather than a blob, the same size 3 and the same discard chance of 1.0, so it never appears on
 * an exposed face. From 26.3 the feature carries its own replacements; this filters them by the host
 * toggles and hands the rest to a {@link ScatteredOreFeature}.
 *
 * <p>No bastion guard is needed: bastions cannot generate in basalt deltas at all.
 */
public class NetherGemFeature extends AbstractOreFeature {

    public static final Identifier ID = Identifier.fromNamespaceAndPath(Constants.MOD_ID, "nether_gem");

    public static final MapCodec<NetherGemFeature> CODEC = makeCodec(NetherGemFeature::new);

    private static final String MOD_NAMESPACE = Constants.MOD_ID;

    private static boolean registered;

    /** The feature as declared, for the common case where no toggle or dial changes anything. */
    private final ScatteredOreFeature asDeclared;

    public NetherGemFeature(List<BlockReplacement> targets, int size, float discardChanceOnAirExposure) {
        super(targets, size, discardChanceOnAirExposure);
        this.asDeclared = new ScatteredOreFeature(targets, size, discardChanceOnAirExposure);
    }

    /** Registered through the caller's own registry path, as a feature TYPE, like the blocks and items. */
    public static void register(BiConsumer<Identifier, MapCodec<? extends Feature>> sink) {
        if (!registered) {
            registered = true;
            sink.accept(ID, CODEC);
        }
    }

    @Override
    public MapCodec<NetherGemFeature> codec() {
        return CODEC;
    }

    @Override
    public boolean place(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin) {
        if (!SeamlessOresConfig.netherGems) {
            return false;
        }

        // Respect the per-host toggles, so switching basalt off really does stop basalt gems. The
        // feature is data-driven and carries both hosts, so the filtering happens here.
        final List<BlockReplacement> enabled = new ArrayList<>();
        for (BlockReplacement target : targetStates()) {
            final Identifier id = BuiltInRegistries.BLOCK.getKey(target.state().getBlock());
            if (id == null) {
                continue;
            }
            // Only OUR blocks carry a host prefix. The netherrack target is Mythic Upgrades' own block,
            // so it has no host toggle and always stays in.
            final boolean mine = MOD_NAMESPACE.equals(id.getNamespace());
            final String host = !mine ? null
                    : id.getPath().startsWith("blackstone_") ? "blackstone"
                    : id.getPath().startsWith("basalt_") ? "basalt" : null;
            if (host == null || SeamlessOresConfig.isHostEnabled(host)) {
                enabled.add(target);
            }
        }
        if (enabled.isEmpty()) {
            return false;
        }
        // The configured size is the real scattered size: how many separate blocks land around the
        // origin. 3 is ancient debris' own value.
        final int size = Math.max(1, SeamlessOresConfig.netherGemSize);
        if (enabled.size() == targetStates().size() && size == size()) {
            return asDeclared.place(level, generator, random, origin);
        }
        return new ScatteredOreFeature(enabled, size, discardChanceOnAirExposure())
                .place(level, generator, random, origin);
    }
}
