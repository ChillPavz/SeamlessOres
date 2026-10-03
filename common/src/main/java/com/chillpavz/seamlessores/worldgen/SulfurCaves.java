package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.LevelChunkSection;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Function;

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
 *       becomes the vein's own filler stone.</li>
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

    private static final AtomicBoolean ORE_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean VEIN_ANNOUNCED = new AtomicBoolean();
    private static final AtomicBoolean EDGE_ANNOUNCED = new AtomicBoolean();

    /** Server start, after the ore targets: on only when the switch is on and the biome exists. */
    public static void prepare(RegistryAccess registries) {
        final boolean biome = registries.lookupOrThrow(Registries.BIOME).get(BIOME).isPresent();
        active = SeamlessOresConfig.sulfurCaves && biome;
        veinBlocks = Set.of();
        veinFiller = Map.of();
        if (biome) {
            Constants.LOG.info("Worldgen: Sulfur Caves keep ore out of sulfur and cinnabar: {}",
                    active ? "on" : "off (config)");
        }
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
     * face. Asked only after the feature has already decided to place ore there.
     */
    public static boolean keepsOreOut(Function<BlockPos, BlockState> level, BlockPos pos) {
        if (!active) {
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
     * After a chunk's own decoration: vein ore or raw ore touching sulfur or cinnabar becomes the
     * vein's filler. Only sections whose biomes include the Sulfur Caves and whose palette holds a
     * vein ore are read, so every other chunk costs one palette check per section.
     */
    public static void sweepVeinEdges(WorldGenLevel level, ChunkAccess chunk) {
        final Map<Block, BlockState> fillers = veinFiller;
        if (!active || fillers.isEmpty()) {
            return;
        }
        final LevelChunkSection[] sections = chunk.getSections();
        final int minX = chunk.getPos().getMinBlockX();
        final int minZ = chunk.getPos().getMinBlockZ();
        final BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int i = 0; i < sections.length; i++) {
            final LevelChunkSection section = sections[i];
            if (section.hasOnlyAir()
                    || !section.getBiomes().maybeHas(biome -> biome.is(BIOME))
                    || !section.getStates().maybeHas(state -> fillers.containsKey(state.getBlock()))) {
                continue;
            }
            final int minY = SectionPos.sectionToBlockCoord(chunk.getSectionYFromSectionIndex(i));
            for (int y = 0; y < 16; y++) {
                for (int z = 0; z < 16; z++) {
                    for (int x = 0; x < 16; x++) {
                        final BlockState filler = fillers.get(section.getBlockState(x, y, z).getBlock());
                        if (filler == null) {
                            continue;
                        }
                        pos.set(minX + x, minY + y, minZ + z);
                        if (keepsOreOut(level::getBlockState, pos)) {
                            level.setBlock(pos, filler, 2);
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
