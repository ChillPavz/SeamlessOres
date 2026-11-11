package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.util.Mth;
import net.minecraft.world.level.levelgen.OreVeinifier;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.LevelChunkSection;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Function;
import java.util.function.Predicate;

/**
 * Keeps ore out of the Sulfur Caves' sulfur and cinnabar, where Vanilla Backport adds the biome
 * (1.21.1 and 1.20.1). The same rule and the same mechanism as the 26.2 and 26.3 game's own biome.
 *
 * <h2>The ways ore gets in</h2>
 * Vanilla Backport draws the caves the way the game does from 26.2: its surface rules lay cinnabar,
 * sulfur and cinnabar in bands by noise, with plain stone wherever the noise falls between them.
 * <ul>
 *   <li><b>The large copper and iron veins.</b> They come from the noise fill, before the bands, and
 *       the bands only rewrite the default block, so a vein crossing the caves leaves its ore, raw
 *       blocks and filler standing in the sulfur. Inside the biome the vein block becomes the default
 *       block before it is stored ({@code NoiseFillMixin}), and the bands fill it like the rest of the
 *       cave. That test is per block, so a vein just outside can still meet bands drawn one block
 *       inside; after each chunk is decorated, vein ore or raw ore touching sulfur or cinnabar becomes
 *       the sulfur or cinnabar it touches most.</li>
 *   <li><b>Sulfur laid after the ore</b>, by whichever chunk decorates a spring's roots or a pool's
 *       rim: a known ore on a face of it becomes that sulfur or cinnabar ({@code WorldGenRegionMixin}).</li>
 *   <li><b>Ore features</b>, which reach the stone sheets between the bands: an ore block is not placed
 *       where it would touch a block in {@code #seamlessores:keeps_ore_out} ({@code OreFeatureMixin}).</li>
 * </ul>
 *
 * <p><b>This removes ore</b>, and has its own switch. Without the biome (no Vanilla Backport, or its
 * caves switched off) every check here ends at once.
 */
public final class SulfurCaves {

    private SulfurCaves() {
    }

    /** Blocks no ore may touch: sulfur and cinnabar, each {@code required: false}. */
    public static final TagKey<Block> KEEPS_ORE_OUT =
            TagKey.create(Registries.BLOCK, ResourceLocation.tryParse(Constants.MOD_ID + ":keeps_ore_out"));

    /** Named by id: the game itself has no such biome before 26.2. */
    public static final ResourceKey<Biome> BIOME =
            ResourceKey.create(Registries.BIOME, ResourceLocation.tryParse("minecraft:sulfur_caves"));

    private static final Direction[] DIRECTIONS = Direction.values();

    private static volatile boolean active;

    /** Every block the large veins place (ore, raw block, filler): the noise fill hook. */
    private static volatile Set<Block> veinBlocks = Set.of();

    /** A vein's ore and raw block, to that vein's filler: the edge sweep. */
    private static volatile Map<Block, BlockState> veinFiller = Map.of();

    /** Every ore this mod knows: our variants, and each supported ore's own blocks. */
    private static volatile Set<Block> knownOre = Set.of();

    private static final AtomicBoolean ORE_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean VEIN_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean EDGE_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean LATE_ANNOUNCED = new AtomicBoolean();

    /** Set while this class writes a block itself, so our own sulfur never re-enters the write hook. */
    private static final ThreadLocal<Boolean> WRITING = ThreadLocal.withInitial(() -> false);

    /** At most this many connected ore blocks become sulfur or cinnabar from one start. */
    private static final int FLOOD_LIMIT = 64;

    /** Implemented on the worldgen region by a mixin: may this position be written right now. */
    public interface WriteZone {
        boolean seamlessores$canWrite(BlockPos pos);
    }

    /** Server start, before the injectors: on only when the switch is on and the biome exists. */
    public static void prepare(RegistryAccess registries) {
        final boolean biome = registries.registryOrThrow(Registries.BIOME).containsKey(BIOME);
        active = SeamlessOresConfig.sulfurCaves && biome;
        veinBlocks = Set.of();
        veinFiller = Map.of();
        knownOre = Set.of();
        if (biome) {
            Constants.LOG.info("Worldgen: Sulfur Caves keep ore out of sulfur and cinnabar: {}",
                    active ? "on" : "off (config)");
        }
        NoiseFillReplacement.note(active);
    }

    /**
     * Server start, after the injectors: the ore table, and the two large veins as they now stand. The
     * vein's raw block and filler are fixed in the game's code, so they are named here.
     */
    public static void afterInjectors() {
        if (!active) {
            return;
        }
        final Set<Block> table = new HashSet<>();
        SeamlessOresContent.blocks().forEach((variant, block) -> {
            if (variant.host().tier() == OreTier.CINNABAR) {
                return;     // ore that belongs in cinnabar is left beside it
            }
            table.add(block);
            for (ResourceLocation form : variant.ore().forms()) {
                BuiltInRegistries.BLOCK.getOptional(form).ifPresent(table::add);
            }
        });
        knownOre = Set.copyOf(table);
        addVein(OreVeinifier.VeinType.COPPER.ore, Blocks.RAW_COPPER_BLOCK.defaultBlockState(), Blocks.GRANITE.defaultBlockState());
        addVein(OreVeinifier.VeinType.IRON.ore, Blocks.RAW_IRON_BLOCK.defaultBlockState(), Blocks.TUFF.defaultBlockState());
    }

    private static void addVein(BlockState ore, BlockState raw, BlockState filler) {
        final Set<Block> blocks = new HashSet<>(veinBlocks);
        blocks.add(ore.getBlock());
        blocks.add(raw.getBlock());
        blocks.add(filler.getBlock());
        veinBlocks = Set.copyOf(blocks);
        final Map<Block, BlockState> fillers = new HashMap<>(veinFiller);
        fillers.put(ore.getBlock(), filler);
        fillers.put(raw.getBlock(), filler);
        veinFiller = Map.copyOf(fillers);
    }

    public static boolean active() {
        return active;
    }

    private static boolean isKnownOre(Block block) {
        return knownOre.contains(block) || veinFiller.containsKey(block);
    }

    /**
     * Turns {@code start} and the known ore connected to it, where {@code writable} allows, into
     * {@code cover}. One block at a time would leave the next ore of the same blob against the new
     * sulfur.
     */
    private static void flood(WorldGenLevel level, BlockPos start, BlockState cover, Predicate<BlockPos> writable) {
        final ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        final Set<BlockPos> seen = new HashSet<>();
        queue.add(start.immutable());
        seen.add(start.immutable());
        int done = 0;
        WRITING.set(true);
        try {
            while (!queue.isEmpty() && done < FLOOD_LIMIT) {
                final BlockPos pos = queue.poll();
                level.setBlock(pos, cover, 2);
                done++;
                for (Direction direction : DIRECTIONS) {
                    final BlockPos next = pos.relative(direction);
                    if (writable.test(next)
                            && next.getY() >= level.getMinBuildHeight() && next.getY() < level.getMaxBuildHeight()
                            && isKnownOre(level.getBlockState(next).getBlock()) && seen.add(next)) {
                        queue.add(next);
                    }
                }
            }
        } finally {
            WRITING.set(false);
        }
    }

    /** The sweep's own chunk, which its decoration may always write. */
    private static Predicate<BlockPos> inChunk(ChunkAccess chunk) {
        final int cx = chunk.getPos().x;
        final int cz = chunk.getPos().z;
        return p -> SectionPos.blockToSectionCoord(p.getX()) == cx && SectionPos.blockToSectionCoord(p.getZ()) == cz;
    }

    /**
     * Worldgen is about to write {@code state} at {@code pos}. If it is sulfur or cinnabar, a known
     * ore on any face of it that the region may write becomes the same block.
     */
    public static void beforeWorldgenWrite(WorldGenLevel level, BlockPos pos, BlockState state,
                                           Predicate<BlockPos> writable) {
        if (!active || WRITING.get() || !state.is(KEEPS_ORE_OUT)) {
            return;
        }
        final BlockPos.MutableBlockPos neighbour = new BlockPos.MutableBlockPos();
        for (Direction direction : DIRECTIONS) {
            neighbour.setWithOffset(pos, direction);
            if (!writable.test(neighbour)) {
                continue;
            }
            if (isKnownOre(level.getBlockState(neighbour).getBlock())) {
                flood(level, neighbour.immutable(), state.getBlock().defaultBlockState(), writable);
                if (LATE_ANNOUNCED.compareAndSet(false, true)) {
                    Constants.LOG.info("Worldgen: first ore cleared beside sulfur laid after it at {}",
                            neighbour.immutable());
                }
            }
        }
    }

    /** The sulfur or cinnabar most of this block's faces touch (sulfur on a tie), or null for neither. */
    private static BlockState cover(WorldGenLevel level, BlockPos pos) {
        final BlockPos.MutableBlockPos neighbour = new BlockPos.MutableBlockPos();
        BlockState best = null;
        int bestCount = 0;
        final Map<Block, Integer> counts = new HashMap<>(2);
        for (Direction direction : DIRECTIONS) {
            final BlockState state = level.getBlockState(neighbour.setWithOffset(pos, direction));
            if (!state.is(KEEPS_ORE_OUT)) {
                continue;
            }
            final int count = counts.merge(state.getBlock(), 1, Integer::sum);
            if (count > bestCount || (count == bestCount && isSulfur(state))) {
                best = state.getBlock().defaultBlockState();
                bestCount = count;
            }
        }
        return best;
    }

    private static boolean isSulfur(BlockState state) {
        return "sulfur".equals(BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath());
    }

    /**
     * True when an ore block about to be placed at {@code pos} would touch sulfur or cinnabar on any
     * face. An ore that REPLACES cinnabar is one of our cinnabar features at work, and is let through.
     */
    public static boolean keepsOreOut(BlockState replaced, Function<BlockPos, BlockState> level, BlockPos pos) {
        if (!active || replaced.is(KEEPS_ORE_OUT)) {
            return false;
        }
        final BlockPos.MutableBlockPos neighbour = new BlockPos.MutableBlockPos();
        for (Direction direction : DIRECTIONS) {
            if (level.apply(neighbour.setWithOffset(pos, direction)).is(KEEPS_ORE_OUT)) {
                if (ORE_ANNOUNCED.compareAndSet(false, true)) {
                    Constants.LOG.info("Worldgen: first ore kept out of sulfur or cinnabar at {}", pos.immutable());
                }
                return true;
            }
        }
        return false;
    }

    /**
     * After a chunk's own decoration: vein ore, raw ore or any known ore touching sulfur or cinnabar
     * becomes the sulfur or cinnabar it touches most. Only sections whose palette holds one are read.
     * The known ores are here for the mods whose ore features are not the game's (Mekanism's
     * {@code mekanism:ore}, Immersive Engineering's {@code ie_ore}): the {@code OreFeature} hook never
     * sees them, so their ore against sulfur is caught here instead. Such a feature also writes into the
     * chunks around its own, which may have been swept already, so the region's other chunks are read
     * too, but only their sections that hold sulfur or cinnabar (or sit beside one that does).
     */
    public static void sweepVeinEdges(WorldGenLevel level, ChunkAccess chunk) {
        final Map<Block, BlockState> fillers = veinFiller;
        final Set<Block> ores = knownOre;
        if (!active || (fillers.isEmpty() && ores.isEmpty())) {
            return;
        }
        final Predicate<Block> swept = block -> fillers.containsKey(block) || ores.contains(block);
        // The region's own write zone: the vein's ore often runs on into the next chunk.
        final boolean region = level instanceof WriteZone;
        final Predicate<BlockPos> writable = region ? ((WriteZone) level)::seamlessores$canWrite : inChunk(chunk);
        final int cx = chunk.getPos().x;
        final int cz = chunk.getPos().z;
        final int reach = region ? 1 : 0;
        for (int dx = -reach; dx <= reach; dx++) {
            for (int dz = -reach; dz <= reach; dz++) {
                final boolean own = dx == 0 && dz == 0;
                final ChunkAccess target;
                try {
                    target = own ? chunk : level.getChunk(cx + dx, cz + dz);
                } catch (RuntimeException outsideRegion) {
                    continue;
                }
                sweepChunk(level, target, swept, writable, !own);
            }
        }
    }

    private static void sweepChunk(WorldGenLevel level, ChunkAccess chunk, Predicate<Block> swept,
                                   Predicate<BlockPos> writable, boolean onlyBesideCover) {
        final LevelChunkSection[] sections = chunk.getSections();
        final int minX = chunk.getPos().getMinBlockX();
        final int minZ = chunk.getPos().getMinBlockZ();
        final BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int i = 0; i < sections.length; i++) {
            final LevelChunkSection section = sections[i];
            // Not gated on the section's own biomes: the bands are drawn through a jittered biome lookup.
            if (section.hasOnlyAir()
                    || !section.getStates().maybeHas(state -> swept.test(state.getBlock()))
                    || (onlyBesideCover && !holdsCover(sections, i - 1) && !holdsCover(sections, i)
                        && !holdsCover(sections, i + 1))) {
                continue;
            }
            final int minY = SectionPos.sectionToBlockCoord(chunk.getSectionYFromSectionIndex(i));
            for (int y = 0; y < 16; y++) {
                for (int z = 0; z < 16; z++) {
                    for (int x = 0; x < 16; x++) {
                        if (!swept.test(section.getBlockState(x, y, z).getBlock())) {
                            continue;
                        }
                        pos.set(minX + x, minY + y, minZ + z);
                        if (!writable.test(pos)) {
                            continue;
                        }
                        final BlockState cover = cover(level, pos);
                        if (cover != null) {
                            flood(level, pos.immutable(), cover, writable);
                            if (EDGE_ANNOUNCED.compareAndSet(false, true)) {
                                Constants.LOG.info("Worldgen: first ore edge cleared beside sulfur or cinnabar at {}",
                                        pos.immutable());
                            }
                        }
                    }
                }
            }
        }
    }

    /** Whether the section at this index exists and its palette may hold sulfur or cinnabar. */
    private static boolean holdsCover(LevelChunkSection[] sections, int i) {
        return i >= 0 && i < sections.length && !sections[i].hasOnlyAir()
                && sections[i].getStates().maybeHas(state -> state.is(KEEPS_ORE_OUT));
    }

    /**
     * True when the noise fill is about to place a vein block inside the Sulfur Caves. Checks every
     * biome cell the surface pass could read for this block, because it jitters its biome lookup by
     * up to one cell.
     */
    public static boolean keepsVeinOut(ChunkAccess chunk, BlockState state, int x, int y, int z) {
        if (!active || chunk == null || state == null || !veinBlocks.contains(state.getBlock())) {
            return false;
        }
        // The chunk only answers for its own cells, so a cell past its edge is read from the nearest one.
        final int minQx = chunk.getPos().getMinBlockX() >> 2;
        final int minQz = chunk.getPos().getMinBlockZ() >> 2;
        final int qx = (x - 2) >> 2;
        final int qy = (y - 2) >> 2;
        final int qz = (z - 2) >> 2;
        for (int dx = 0; dx <= 1; dx++) {
            for (int dy = 0; dy <= 1; dy++) {
                for (int dz = 0; dz <= 1; dz++) {
                    final int cx = Mth.clamp(qx + dx, minQx, minQx + 3);
                    final int cz = Mth.clamp(qz + dz, minQz, minQz + 3);
                    if (chunk.getNoiseBiome(cx, qy + dy, cz).is(BIOME)) {
                        if (VEIN_ANNOUNCED.compareAndSet(false, true)) {
                            Constants.LOG.info("Worldgen: first vein block kept out of the Sulfur Caves at {} {} {}",
                                    x, y, z);
                        }
                        return true;
                    }
                }
            }
        }
        return false;
    }
}
