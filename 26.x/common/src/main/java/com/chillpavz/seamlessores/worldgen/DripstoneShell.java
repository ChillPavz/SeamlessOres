package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

import java.util.IdentityHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Swaps a dripstone variant in for ore that a dripstone cluster wraps.
 *
 * <h2>Why this is not a target in the ore features</h2>
 * The dripstone cluster runs in {@code underground_decoration}, one step AFTER the ores, and turns the
 * cave shell into dripstone block by block through the base-block placement in
 * {@code DripstoneUtils} (26.1.x) / {@code SpeleothemUtils} (26.2 and up). That placement only
 * replaces {@code #dripstone_replaceable_blocks}, the base overworld stones, so every ore in the shell
 * is skipped and left standing as stone ore inside a dripstone wall. When the ore feature ran there
 * was no dripstone yet, so no target list could ever have chosen a dripstone variant.
 *
 * <h2>Why the ore total and the cluster's shape stay exactly vanilla</h2>
 * The swap is 1:1, an ore that already exists becomes the dripstone variant of the same ore, and
 * the placement then still reports "not placed", which is what vanilla reports for an ore. The
 * cluster stops growing that column at the ore exactly as it would have, so every other block it
 * places is the one vanilla places.
 */
public final class DripstoneShell {

    private DripstoneShell() {
    }

    /** Ore block, in any rock it generates in, to the dripstone variant of that ore. Empty: no-op. */
    private static volatile Map<Block, BlockState> swaps = Map.of();

    private static final AtomicBoolean ANNOUNCED = new AtomicBoolean();

    /**
     * Builds the swap table. Server start, where every mod's blocks exist and the config is loaded;
     * the toggles gate generation only, never registration.
     */
    public static void prepare() {
        final Map<OreType, BlockState> dripstoneOf = new IdentityHashMap<>();
        SeamlessOresContent.blocks().forEach((variant, block) -> {
            if (variant.host() == HostStone.DRIPSTONE && enabled(variant)) {
                dripstoneOf.put(variant.ore(), block.defaultBlockState());
            }
        });

        final Map<Block, BlockState> table = new IdentityHashMap<>();
        dripstoneOf.forEach((ore, dripstone) -> {
            put(table, ore.stoneOre(), dripstone);
            put(table, ore.deepslateOre(), dripstone);
        });
        // Our own granite, diorite, andesite and tuff variants sit in those walls as well.
        SeamlessOresContent.blocks().forEach((variant, block) -> {
            final OreTier tier = variant.host().tier();
            final BlockState dripstone = dripstoneOf.get(variant.ore());
            if (dripstone != null && (tier == OreTier.STONE || tier == OreTier.DEEPSLATE)) {
                table.put(block, dripstone);
            }
        });

        swaps = table.isEmpty() ? Map.of() : Map.copyOf(table);
        Constants.LOG.info("Worldgen: dripstone shells restyle {} ore blocks into {} dripstone variants",
                swaps.size(), dripstoneOf.size());
    }

    private static boolean enabled(OreVariant variant) {
        if (!SeamlessOresConfig.isHostEnabled(variant.host().name())) {
            return false;
        }
        return variant.ore().requiredModId() == null
                || SeamlessOresConfig.isModOreEnabled(variant.ore().requiredModId(), false);
    }

    private static void put(Map<Block, BlockState> table, Identifier id, BlockState dripstone) {
        if (id != null) {
            BuiltInRegistries.BLOCK.getOptional(id).ifPresent(block -> table.put(block, dripstone));
        }
    }

    /**
     * Called by the dripstone base-block placement before it tests the block. True when the block at
     * {@code pos} was an ore and is now its dripstone variant; the caller then reports "not placed".
     */
    public static boolean swap(LevelAccessor level, BlockPos pos) {
        final Map<Block, BlockState> table = swaps;
        if (table.isEmpty()) {
            return false;
        }
        final BlockState dripstone = table.get(level.getBlockState(pos).getBlock());
        if (dripstone == null) {
            return false;
        }
        level.setBlock(pos, dripstone, Block.UPDATE_CLIENTS);
        if (ANNOUNCED.compareAndSet(false, true)) {
            Constants.LOG.info("Worldgen: first dripstone ore placed, {} at {}",
                    BuiltInRegistries.BLOCK.getKey(dripstone.getBlock()), pos);
        }
        return true;
    }
}
