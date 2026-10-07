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
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.WorldGenLevel;
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
 * Keeps ore out of the Sulfur Caves' sulfur and cinnabar (26.2 and up).
 *
 * <h2>The two ways ore gets in</h2>
 * The caves are filled by noise in bands: cinnabar, sulfur, cinnabar, with plain stone wherever the
 * noise falls between them, including a thin sheet between each cinnabar and sulfur band.
 * <ul>
 *   <li><b>The large copper and iron veins.</b> They are built before the bands are drawn and win
 *       over them, so a copper vein crossing the caves leaves its granite, copper ore and raw copper
 *       blocks standing inside the sulfur, and an iron vein its tuff and iron. Inside the biome the
 *       vein is now not built at all, so the bands fill that space as they fill the rest of the
 *       cave: a material-rule condition from 26.3, a hook in the noise fill on 26.2. That test is
 *       per block, so a vein just outside the biome can still meet bands drawn one block inside
 *       it; after each chunk is decorated, vein ore or raw ore touching sulfur or cinnabar
 *       becomes the sulfur or cinnabar it touches most, like the Lush Caves' clay and moss.</li>
 *   <li><b>Sulfur laid after the ore.</b> A sulfur spring's root column or a sulfur pool's rim is
 *       written by whichever chunk decorates it, which can be a neighbour that runs after this
 *       chunk's ores. When worldgen writes sulfur or cinnabar, a known ore on a face of it in the same
 *       chunk becomes that sulfur or cinnabar.</li>
 *   <li><b>Ore features</b> (every vanilla and modded {@code minecraft:ore} and scattered ore). They
 *       target stone, so they reach the stone sheets and pockets between the bands. An ore block is
 *       now not placed where it would touch a block in {@code #seamlessores:keeps_ore_out}.</li>
 * </ul>
 *
 * <p><b>This removes ore</b>, like the Lush Caves pass, and is gated by its own switch. Nothing is
 * restyled and nothing is added: sulfur and cinnabar stay bare, which is the look the biome has.
 * On 26.1.x the biome does not exist and the tag is empty, so every check here ends at once.
 */
public final class SulfurCaves {

    private SulfurCaves() {
    }

    /** Blocks no ore may touch: sulfur and cinnabar, each {@code required: false}. */
    public static final TagKey<Block> KEEPS_ORE_OUT =
            TagKey.create(Registries.BLOCK, Identifier.fromNamespaceAndPath(Constants.MOD_ID, "keeps_ore_out"));

    /** Named by id: the 26.1.x side of the jar has no constant for it. */
    public static final ResourceKey<Biome> BIOME =
            ResourceKey.create(Registries.BIOME, Identifier.withDefaultNamespace("sulfur_caves"));

    private static final Direction[] DIRECTIONS = Direction.values();

    private static volatile boolean active;

    /** Every block the large veins place (ore, raw block, filler): the 26.2 noise fill hook. */
    private static volatile Set<Block> veinBlocks = Set.of();

    /** A vein's ore and raw block, to that vein's filler: the edge sweep. */
    private static volatile Map<Block, BlockState> veinFiller = Map.of();

    /** Every ore this mod knows, to the stone it stands in: sulfur laid beside it afterwards. */
    private static volatile Map<Block, BlockState> oreHost = Map.of();

    private static final AtomicBoolean ORE_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean VEIN_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean EDGE_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean LATE_ANNOUNCED = new AtomicBoolean();

    /**
     * Set while this class writes a block itself. Without it the sulfur we write would trigger the
     * write hook again and walk every connected ore block: a stack overflow on a large vein.
     */
    private static final ThreadLocal<Boolean> WRITING = ThreadLocal.withInitial(() -> false);

    /** At most this many connected ore blocks become sulfur or cinnabar from one start. */
    private static final int FLOOD_LIMIT = 64;

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
                            && next.getY() >= level.getMinY() && next.getY() <= level.getMaxY()
                            && isKnownOre(level.getBlockState(next).getBlock()) && seen.add(next)) {
                        queue.add(next);
                    }
                }
            }
        } finally {
            WRITING.set(false);
        }
    }

    /** Implemented on the worldgen region by a mixin: may this position be written right now. */
    public interface WriteZone {
        boolean seamlessores$canWrite(BlockPos pos);
    }

    /** The sweep's own chunk, which its decoration may always write. */
    private static Predicate<BlockPos> inChunk(ChunkAccess chunk) {
        final int cx = chunk.getPos().x();
        final int cz = chunk.getPos().z();
        return p -> SectionPos.blockToSectionCoord(p.getX()) == cx && SectionPos.blockToSectionCoord(p.getZ()) == cz;
    }

    private static boolean isKnownOre(Block block) {
        return oreHost.containsKey(block) || veinFiller.containsKey(block);
    }

    /** Server start, after the ore targets: on only when the switch is on and the biome exists. */
    public static void prepare(RegistryAccess registries) {
        final boolean biome = registries.lookupOrThrow(Registries.BIOME).get(BIOME).isPresent();
        active = SeamlessOresConfig.sulfurCaves && biome;
        veinBlocks = Set.of();
        veinFiller = Map.of();
        oreHost = active ? hosts() : Map.of();
        if (biome) {
            Constants.LOG.info("Worldgen: Sulfur Caves keep ore out of sulfur and cinnabar: {}",
                    active ? "on" : "off (config)");
        }
    }

    /** Our variants to their host, and each supported ore's stone and deepslate block to that rock. */
    private static Map<Block, BlockState> hosts() {
        final Map<Block, BlockState> table = new HashMap<>();
        SeamlessOresContent.blocks().forEach((variant, block) -> {
            if (variant.host().tier() == OreTier.CINNABAR) {
                return;     // ore that belongs in cinnabar is left beside it
            }
            table.put(block, variant.host().block().defaultBlockState());
            put(table, variant.ore().stoneOre(), Blocks.STONE.defaultBlockState());
            put(table, variant.ore().deepslateOre(), Blocks.DEEPSLATE.defaultBlockState());
        });
        return Map.copyOf(table);
    }

    private static void put(Map<Block, BlockState> table, Identifier id, BlockState host) {
        if (id != null) {
            BuiltInRegistries.BLOCK.getOptional(id).ifPresent(block -> table.putIfAbsent(block, host));
        }
    }

    /**
     * Worldgen is about to write {@code state} at {@code pos}. If it is sulfur or cinnabar, a known
     * ore on any face of it that the region may write becomes the same block. The ore is often in the
     * NEIGHBOURING chunk: the sulfur is the later write, made while decorating the chunk beside it.
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
            final Block block = level.getBlockState(neighbour).getBlock();
            if (isKnownOre(block)) {
                flood(level, neighbour.immutable(), state.getBlock().defaultBlockState(), writable);
                if (LATE_ANNOUNCED.compareAndSet(false, true)) {
                    Constants.LOG.info("Worldgen: first ore cleared beside sulfur laid after it at {}",
                            neighbour.immutable());
                }
            }
        }
    }

    /**
     * The sulfur or cinnabar most of this block's faces touch (sulfur on a tie), or null when it
     * touches neither: what an ore stranded there becomes, so the band reads as one material.
     */
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

    public static boolean active() {
        return active;
    }

    /** One large vein, as the running era builds it. Server start, after the vein ore is restyled. */
    public static void addVein(BlockState ore, BlockState raw, BlockState filler) {
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

    /**
     * True when an ore block about to be placed at {@code pos} would touch sulfur or cinnabar on any
     * face. Asked only after the feature has already decided to place ore there. An ore that REPLACES
     * cinnabar is one of our cinnabar features at work, and is let through.
     */
    public static boolean keepsOreOut(BlockState replaced, Function<BlockPos, BlockState> level, BlockPos pos) {
        if (!active || replaced.is(KEEPS_ORE_OUT)) {
            return false;
        }
        return touches(level, pos);
    }

    private static boolean touches(Function<BlockPos, BlockState> level, BlockPos pos) {
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
     * After a chunk's own decoration: vein ore or raw ore touching sulfur or cinnabar becomes the
     * sulfur or cinnabar it touches most. Only sections whose palette holds a vein ore are read, so
     * every other section costs one palette check.
     */
    public static void sweepVeinEdges(WorldGenLevel level, ChunkAccess chunk) {
        final Map<Block, BlockState> fillers = veinFiller;
        if (!active || fillers.isEmpty()) {
            return;
        }
        // The region's own write zone when there is one: the vein's ore often runs on into the next
        // chunk, and stopping the flood at the border would leave that part against the new sulfur.
        final Predicate<BlockPos> writable = level instanceof WriteZone zone ? zone::seamlessores$canWrite : inChunk(chunk);
        final LevelChunkSection[] sections = chunk.getSections();
        final int minX = chunk.getPos().getMinBlockX();
        final int minZ = chunk.getPos().getMinBlockZ();
        final BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int i = 0; i < sections.length; i++) {
            final LevelChunkSection section = sections[i];
            // Not gated on the section's own biomes: the bands are drawn through a jittered biome
            // lookup, so they can reach a section whose biomes never include the Sulfur Caves.
            if (section.hasOnlyAir()
                    || !section.getStates().maybeHas(state -> fillers.containsKey(state.getBlock()))) {
                continue;
            }
            final int minY = SectionPos.sectionToBlockCoord(chunk.getSectionYFromSectionIndex(i));
            for (int y = 0; y < 16; y++) {
                for (int z = 0; z < 16; z++) {
                    for (int x = 0; x < 16; x++) {
                        if (!fillers.containsKey(section.getBlockState(x, y, z).getBlock())) {
                            continue;
                        }
                        pos.set(minX + x, minY + y, minZ + z);
                        final BlockState cover = cover(level, pos);
                        if (cover != null) {
                            flood(level, pos.immutable(), cover, writable);
                            if (EDGE_ANNOUNCED.compareAndSet(false, true)) {
                                Constants.LOG.info("Worldgen: first vein edge cleared beside sulfur or cinnabar at {}",
                                        pos.immutable());
                            }
                        }
                    }
                }
            }
        }
    }

    /**
     * True when the noise fill is about to place a vein block inside the Sulfur Caves (26.2). Checks
     * every biome cell the surface pass could read for this block, because that pass jitters its
     * biome lookup by up to one cell: a vein block left where the bands were drawn would stand in
     * them exactly as before.
     */
    public static boolean keepsVeinOut(ChunkAccess chunk, BlockState state, int x, int y, int z) {
        if (!active || state == null || !veinBlocks.contains(state.getBlock())) {
            return false;
        }
        // The chunk only answers for its own cells (it wraps the rest), so a cell past its edge is
        // read from the nearest one inside it.
        final int minQx = chunk.getPos().getMinBlockX() >> 2;
        final int minQz = chunk.getPos().getMinBlockZ() >> 2;
        final int qx = (x - 2) >> 2;
        final int qy = (y - 2) >> 2;
        final int qz = (z - 2) >> 2;
        for (int dx = 0; dx <= 1; dx++) {
            for (int dy = 0; dy <= 1; dy++) {
                for (int dz = 0; dz <= 1; dz++) {
                    final int cx = Math.clamp(qx + dx, minQx, minQx + 3);
                    final int cz = Math.clamp(qz + dz, minQz, minQz + 3);
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
