package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.LevelChunkSection;

import java.util.IdentityHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Restyles the ore a host stone walls in where no ore feature could: rock laid at NOISE time, after the
 * ore that is already there. Run at the end of each chunk's decoration ({@code ChunkSweepMixin}).
 *
 * <h2>Why the ore features cannot do it</h2>
 * Terralith lays most of its deep blackstone through its surface rules, over the deepslate and tuff, and
 * the large iron vein is laid by the noise too. Neither passes through an ore feature, so no target list
 * ever sees that ore: it keeps the look of the rock it was made in (tuff iron ore) inside blackstone.
 *
 * <h2>What it does, and why the ore total stays the same</h2>
 * In each section whose palette holds both a host stone and a known ore, every such ore whose stone
 * neighbours are mostly one host stone (strictly more faces of that stone than of any other solid
 * block; other ore counts for neither) becomes that stone's variant of the same ore, or the stone itself
 * where the fixed geology rule refuses the pair, exactly as the stone-side injector does for the stones
 * laid by ore features. One block for one block.
 */
public final class WalledInOre {

    private WalledInOre() {
    }

    /** Host stone block -> (ore block in any rock -> what it becomes there). Empty: no-op. */
    private static volatile Map<Block, Map<Block, BlockState>> sweeps = Map.of();
    /** Every ore block any table above names: the cheap test per block. */
    private static volatile Map<Block, Boolean> known = Map.of();

    private static final AtomicBoolean ANNOUNCED = new AtomicBoolean();

    /**
     * Builds the tables. Server start, after the injectors, where every mod's blocks exist and the
     * config is loaded; the switches gate generation only, never registration.
     */
    public static void prepare() {
        final Map<Block, Map<Block, BlockState>> table = new IdentityHashMap<>();
        final Map<Block, Boolean> all = new IdentityHashMap<>();
        final Map<OreVariant, Block> ours = SeamlessOresContent.blocks();
        for (HostStone host : HostStone.ALL) {
            final Block stone = host.present() ? host.block() : null;
            if (stone == null || host.swallows().isEmpty() || !SeamlessOresConfig.isHostEnabled(host.name())) {
                continue;
            }
            final Map<Block, BlockState> into = new IdentityHashMap<>();
            for (OreType ore : host.swallows()) {
                if (ore.requiredModId() != null && !SeamlessOresConfig.isModOreEnabled(ore.requiredModId(), false)) {
                    continue;
                }
                final Block variant = ours.get(new OreVariant(host, ore));
                final BlockState becomes = host.refused().contains(ore) ? stone.defaultBlockState()
                        : variant != null ? variant.defaultBlockState() : null;
                if (becomes == null) {
                    continue;
                }
                for (var form : ore.forms()) {
                    BuiltInRegistries.BLOCK.getOptional(form).ifPresent(block -> into.put(block, becomes));
                }
                // Our own variants of the same ore in the game's rock (the iron vein's tuff iron ore).
                ours.forEach((other, block) -> {
                    final OreTier tier = other.host().tier();
                    if (other.ore() == ore && other.host() != host
                            && (tier == OreTier.STONE || tier == OreTier.DEEPSLATE)) {
                        into.put(block, becomes);
                    }
                });
            }
            if (!into.isEmpty()) {
                table.put(stone, into);
                into.keySet().forEach(block -> all.put(block, Boolean.TRUE));
            }
        }
        sweeps = table.isEmpty() ? Map.of() : Map.copyOf(table);
        known = all.isEmpty() ? Map.of() : Map.copyOf(all);
        Constants.LOG.info("Worldgen: ore walled in by {} host stones is restyled at the end of decoration ({} ore blocks)",
                sweeps.size(), known.size());
    }

    /**
     * The end of one chunk's decoration: ore that rock laid at NOISE time walls in. Terralith's surface
     * rules lay most of its deep blackstone that way, over the deepslate and tuff around the large iron
     * vein, which is laid at noise time too, so neither a target list nor a feature hook ever sees it.
     * Only sections whose palette holds both a host stone and a known ore are walked.
     */
    public static void sweepChunk(LevelAccessor level, ChunkAccess chunk) {
        final Map<Block, Map<Block, BlockState>> table = sweeps;
        if (table.isEmpty()) {
            return;
        }
        try {
            final LevelChunkSection[] sections = chunk.getSections();
            final int x0 = chunk.getPos().getMinBlockX();
            final int z0 = chunk.getPos().getMinBlockZ();
            final BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
            for (int i = 0; i < sections.length; i++) {
                final LevelChunkSection section = sections[i];
                if (section == null || section.hasOnlyAir()
                        || !section.getStates().maybeHas(state -> table.containsKey(state.getBlock()))
                        || !section.getStates().maybeHas(state -> known.containsKey(state.getBlock()))) {
                    continue;
                }
                final int y0 = chunk.getSectionYFromSectionIndex(i) << 4;
                for (int y = 0; y < 16; y++) {
                    for (int z = 0; z < 16; z++) {
                        for (int x = 0; x < 16; x++) {
                            final Block ore = section.getBlockState(x, y, z).getBlock();
                            if (known.containsKey(ore)) {
                                restyle(level, pos.set(x0 + x, y0 + y, z0 + z).immutable(), ore);
                            }
                        }
                    }
                }
            }
        } catch (RuntimeException e) {
            failed(e);
        }
    }

    /**
     * One ore block: if its stone neighbours are mostly one host stone (strictly more faces of it than of
     * any other solid block; other ore counts for neither), it becomes that stone's form of the ore.
     */
    private static void restyle(LevelAccessor level, BlockPos pos, Block ore) {
        final Map<Block, Map<Block, BlockState>> table = sweeps;
        Block best = null;
        int bestCount = 0;
        int other = 0;
        final Map<Block, Integer> counts = new IdentityHashMap<>();
        for (Direction direction : Direction.values()) {
            final BlockState next = level.getBlockState(pos.relative(direction));
            final Block block = next.getBlock();
            if (table.containsKey(block)) {
                final int count = counts.merge(block, 1, Integer::sum);
                if (count > bestCount) {
                    bestCount = count;
                    best = block;
                }
            } else if (!known.containsKey(block) && SeamlessOresContent.variantOf(block) == null
                    && !next.isAir() && next.getFluidState().isEmpty()) {
                other++;
            }
        }
        if (best == null || bestCount <= other) {
            return;
        }
        final BlockState becomes = table.get(best).get(ore);
        if (becomes != null) {
            level.setBlock(pos, becomes, Block.UPDATE_CLIENTS);
            if (ANNOUNCED.compareAndSet(false, true)) {
                Constants.LOG.info("Worldgen: first ore restyled where a host stone walls it in, {} at {}",
                        BuiltInRegistries.BLOCK.getKey(becomes.getBlock()), pos);
            }
        }
    }

    private static final AtomicBoolean FAILED = new AtomicBoolean();

    /** A restyle is never worth a broken chunk: leave the rest as generated, say so once. */
    private static void failed(RuntimeException e) {
        if (FAILED.compareAndSet(false, true)) {
            Constants.LOG.warn("Worldgen: could not restyle ore walled in by a host stone; left as generated", e);
        }
    }
}
