package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.BiConsumer;

/**
 * Places Mythic Upgrades' ruby and sapphire in basalt deltas, as scattered single blocks.
 *
 * <h2>Why this feature exists at all</h2>
 * Everything else in this mod restyles ore that was already going to be there, by extending the
 * target list of an existing feature. This one genuinely adds generation, because there is nothing
 * to extend: Mythic Upgrades restricts ruby and sapphire ORE to its own {@code mythic_rifts} biome,
 * so our basalt and blackstone variants had nowhere to appear.
 *
 * <p>It is defensible rather than arbitrary: Mythic Upgrades already injects its ruby and sapphire
 * <i>geodes</i> into every Nether biome via {@code #minecraft:is_nether}, so scattering a few rare
 * veins in deltas extends that intent instead of contradicting it.
 *
 * <h2>Why it delegates to SCATTERED_ORE rather than ORE</h2>
 * Copied from ancient debris, which is the closest thing vanilla has to "a rare prize you dig for":
 * {@code minecraft:scattered_ore} places individual blocks spread around the origin instead of a
 * blob, which is exactly why debris turns up as isolated pieces. Same {@code size} 3 and the same
 * {@code discard_chance_on_air_exposure} of 1.0, so it never appears on an exposed face.
 *
 * <p>Because only air counts as exposure and lava does not, these generate freely beneath lava the
 * way ancient debris does.
 *
 * <p>No bastion guard is needed here: bastions cannot generate in basalt deltas at all, verified
 * from {@code #minecraft:has_structure/bastion_remnant}, which lists only crimson forest, nether
 * wastes, soul sand valley and warped forest.
 */
public class NetherGemFeature extends Feature<OreConfiguration> {

    public static final Identifier ID =
            Identifier.fromNamespaceAndPath(Constants.MOD_ID, "nether_gem");

    private static final String MOD_NAMESPACE = Constants.MOD_ID;

    private static NetherGemFeature instance;

    public NetherGemFeature() {
        super(OreConfiguration.CODEC);
    }

    /** Registered through the caller's own registry path, exactly like the blocks and items. */
    public static void register(BiConsumer<Identifier, Feature<?>> sink) {
        if (instance == null) {
            instance = new NetherGemFeature();
            sink.accept(ID, instance);
        }
    }

    @Override
    public boolean place(FeaturePlaceContext<OreConfiguration> context) {
        if (!SeamlessOresConfig.netherGems) {
            return false;
        }

        // Respect the per-host toggles, so switching basalt off really does stop basalt gems. The
        // feature is data-driven and carries both hosts, so the filtering happens here rather than
        // in the injector, which never sees this feature.
        final List<OreConfiguration.TargetBlockState> enabled = new ArrayList<>();
        for (OreConfiguration.TargetBlockState target : context.config().targetStates) {
            final Identifier id = BuiltInRegistries.BLOCK.getKey(target.state.getBlock());
            if (id == null) {
                continue;
            }
            // Only OUR blocks carry a host prefix. The netherrack target is Mythic Upgrades' own
            // block, so it has no host toggle and always stays in - that entry is what gives these
            // the same coverage as ancient debris, which targets the whole base_stone_nether tag.
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
        // The configured size is the real scattered_ore size: how many separate blocks land around
        // the origin. 3 is ancient debris' own value.
        final int size = Math.max(1, SeamlessOresConfig.netherGemSize);
        if (enabled.size() == context.config().targetStates.size() && size == context.config().size) {
            return Feature.SCATTERED_ORE.place(context);
        }
        return Feature.SCATTERED_ORE.place(new FeaturePlaceContext<>(
                Optional.empty(), context.level(), context.chunkGenerator(), context.random(),
                context.origin(),
                new OreConfiguration(enabled, size, context.config().discardChanceOnAirExposure)));
    }
}
