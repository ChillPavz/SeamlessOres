package com.chillpavz.seamlessores.matrix.content;

import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.material.MapColor;

import java.util.Collections;
import java.util.EnumSet;
import java.util.List;
import java.util.Set;

import static com.chillpavz.seamlessores.matrix.content.OreKind.COAL;
import static com.chillpavz.seamlessores.matrix.content.OreKind.COPPER;
import static com.chillpavz.seamlessores.matrix.content.OreKind.DIAMOND;
import static com.chillpavz.seamlessores.matrix.content.OreKind.EMERALD;
import static com.chillpavz.seamlessores.matrix.content.OreKind.GOLD;
import static com.chillpavz.seamlessores.matrix.content.OreKind.IRON;
import static com.chillpavz.seamlessores.matrix.content.OreKind.LAPIS;
import static com.chillpavz.seamlessores.matrix.content.OreKind.NETHER_GOLD;
import static com.chillpavz.seamlessores.matrix.content.OreKind.QUARTZ;
import static com.chillpavz.seamlessores.matrix.content.OreKind.REDSTONE;
import static com.chillpavz.seamlessores.matrix.content.OreKind.ZINC;

/**
 * A stone that ore ends up inside, because the stone is placed after the ore (or the ore into it).
 *
 * <p>Declared by id, never by Block reference: the stone belongs to another mod, which may register
 * after us, and this mod never compiles against it. The block itself is looked up when it is first
 * needed, which is always after every mod has registered.
 *
 * <p>A host exists while the mod that PLACES it is installed. That is the stone's own mod, except for
 * the vanilla stones in Create's strata: minecraft:calcite is a host only because Create lays it down
 * in bands, so it hangs on Create. Its id keeps the stone's namespace (minecraft_calcite_iron_ore),
 * because the look belongs to the stone, not to whoever placed it.
 *
 * <p>{@code ores} is the measured pair list, not a taste call: every ore that reaches this stone's
 * height band in its biome at a rate above the floor. A missing pair is a visible bug, because the
 * stone swallows that ore regardless. A variant of a modded ore (zinc) also needs that ore's mod, so
 * listing zinc costs nothing where Create is absent. Written here: the vanilla ores and zinc. Every
 * other ore mod's pairs are measured by the pair model and generated into {@link ModdedPairs}; a host
 * takes both.
 *
 * <p>tools/matrix/generate_matrix.py PARSES this table, and so does Seamless Glowing Ores' pack generator:
 * keep each host one constructor expression whose first line holds the namespace AND the path, with the ores as {@code EnumSet.of(...)} (or {@code EnumSet.noneOf(OreKind.class)}) and an optional {@code .placedBy("mod")}.
 */
public final class HostStone {

    /** Which ore strength a variant takes: the stone ore's or the deepslate ore's. */
    public enum Strength { STONE, DEEPSLATE }

    // --- Blockus: Fabric only, every 26.x band. Map colours read from BlockusBlocks. Limestone,
    // marble and bluestone copy stone's properties and viridite copies deepslate's, which is what the
    // ore strength follows.
    public static final HostStone BLOCKUS_LIMESTONE = new HostStone("blockus", "limestone",
            Strength.STONE, MapColor.WOOD,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone BLOCKUS_MARBLE = new HostStone("blockus", "marble",
            Strength.STONE, MapColor.QUARTZ,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone BLOCKUS_BLUESTONE = new HostStone("blockus", "bluestone",
            Strength.STONE, MapColor.COLOR_CYAN,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    // Deep and deep dark only: no coal, no emerald, and copper falls just under the floor.
    public static final HostStone BLOCKUS_VIRIDITE = new HostStone("blockus", "viridite",
            Strength.DEEPSLATE, MapColor.PLANT,
            EnumSet.of(IRON, GOLD, REDSTONE, LAPIS, DIAMOND, ZINC));

    // --- Create (Create Fly, Fabric, 26.1.2 and 26.2). Its strata are one layered feature per
    // dimension; the overworld one also lays down three vanilla stones. Scoria and smooth basalt are in
    // BOTH strata, so they take the overworld ores and the two nether ones; scorchia only the nether.
    // Map colours and hardness of every host below were read back from the running 26.2 game
    // (harness SOM_HOST); every host under 3.0 hardness takes the stone ore's strength.
    public static final HostStone CREATE_ASURINE = new HostStone("create", "asurine",
            Strength.STONE, MapColor.COLOR_BLUE,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone CREATE_CRIMSITE = new HostStone("create", "crimsite",
            Strength.STONE, MapColor.COLOR_RED,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone CREATE_LIMESTONE = new HostStone("create", "limestone",
            Strength.STONE, MapColor.SAND,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone CREATE_OCHRUM = new HostStone("create", "ochrum",
            Strength.STONE, MapColor.TERRACOTTA_YELLOW,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone CREATE_SCORCHIA = new HostStone("create", "scorchia",
            Strength.STONE, MapColor.TERRACOTTA_GRAY,
            EnumSet.of(NETHER_GOLD, QUARTZ));
    public static final HostStone CREATE_SCORIA = new HostStone("create", "scoria",
            Strength.STONE, MapColor.COLOR_BROWN,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC, NETHER_GOLD, QUARTZ));
    public static final HostStone CREATE_VERIDIUM = new HostStone("create", "veridium",
            Strength.STONE, MapColor.WARPED_NYLIUM,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone MINECRAFT_CALCITE = new HostStone("minecraft", "calcite",
            Strength.STONE, MapColor.TERRACOTTA_WHITE,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC)).placedBy("create");
    public static final HostStone MINECRAFT_DRIPSTONE_BLOCK = new HostStone("minecraft", "dripstone_block",
            Strength.STONE, MapColor.TERRACOTTA_BROWN,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC)).placedBy("create");
    public static final HostStone MINECRAFT_SMOOTH_BASALT = new HostStone("minecraft", "smooth_basalt",
            Strength.STONE, MapColor.COLOR_BLACK,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC, NETHER_GOLD, QUARTZ))
            .placedBy("create");

    // --- Forbidden and Arcanus: NeoForge, 26.1.2 (beta). The bottom 13 blocks of the overworld.
    // Hardness 4.5 and map colour read back from the running 26.1.2 game.
    public static final HostStone FORBIDDEN_ARCANUS_DARKSTONE = new HostStone("forbidden_arcanus", "darkstone",
            Strength.DEEPSLATE, MapColor.STONE,
            EnumSet.of(IRON, GOLD, REDSTONE, LAPIS, DIAMOND));

    // --- Mythic Upgrades: both loaders, 26.2 and 26.3. Its own two cave biomes, which list no emerald; not in any
    // ore replaceables tag, and zinc is placed after them, so zinc never reaches them.
    public static final HostStone MYTHICUPGRADES_AQUAMARINE_SCHIST = new HostStone("mythicupgrades", "aquamarine_schist",
            Strength.STONE, MapColor.COLOR_LIGHT_BLUE,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND));
    public static final HostStone MYTHICUPGRADES_CITRINE_SCHIST = new HostStone("mythicupgrades", "citrine_schist",
            Strength.STONE, MapColor.COLOR_YELLOW,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND));
    public static final HostStone MYTHICUPGRADES_PERIDOT_SCHIST = new HostStone("mythicupgrades", "peridot_schist",
            Strength.STONE, MapColor.COLOR_LIGHT_GREEN,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND));
    public static final HostStone MYTHICUPGRADES_TOPAZ_SCHIST = new HostStone("mythicupgrades", "topaz_schist",
            Strength.STONE, MapColor.COLOR_ORANGE,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND));

    // The nether rifts (its own nether biome). No vanilla ore reaches it: vanilla's nether ores run a
    // step later. It swallows Mythic Upgrades' own ruby ore, which its biome places before it.
    // Hardness 1.5 and map colour read from MythicBlocks.
    public static final HostStone MYTHICUPGRADES_SAPPHIRE_SCHIST = new HostStone("mythicupgrades", "sapphire_schist",
            Strength.STONE, MapColor.LAPIS,
            EnumSet.noneOf(OreKind.class));

    // --- Promenade: Fabric, 26.1.x and 26.2. Both in stone_ore_replaceables, so later ore lands in them.
    public static final HostStone PROMENADE_ASPHALT = new HostStone("promenade", "asphalt",
            Strength.STONE, MapColor.DEEPSLATE,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));
    public static final HostStone PROMENADE_BLUNITE = new HostStone("promenade", "blunite",
            Strength.STONE, MapColor.TERRACOTTA_CYAN,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC));

    // --- Wilder Wild: Fabric every band, NeoForge from 26.2. Only in its magmatic caves biome, which
    // lists no emerald. Map colour and hardness (4.5, so the deepslate ore strength) read from the
    // running game.
    public static final HostStone WILDERWILD_GABBRO = new HostStone("wilderwild", "gabbro",
            Strength.DEEPSLATE, MapColor.TERRACOTTA_BROWN,
            EnumSet.of(COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND, ZINC));

    /** Registration and creative tab order: by mod, as the config screen lists them. */
    public static final List<HostStone> ALL = List.of(
            BLOCKUS_LIMESTONE, BLOCKUS_MARBLE, BLOCKUS_BLUESTONE, BLOCKUS_VIRIDITE,
            CREATE_ASURINE, CREATE_CRIMSITE, CREATE_LIMESTONE, CREATE_OCHRUM, CREATE_SCORCHIA, CREATE_SCORIA,
            CREATE_VERIDIUM, MINECRAFT_CALCITE, MINECRAFT_DRIPSTONE_BLOCK, MINECRAFT_SMOOTH_BASALT,
            FORBIDDEN_ARCANUS_DARKSTONE,
            MYTHICUPGRADES_AQUAMARINE_SCHIST, MYTHICUPGRADES_CITRINE_SCHIST, MYTHICUPGRADES_PERIDOT_SCHIST,
            MYTHICUPGRADES_TOPAZ_SCHIST, MYTHICUPGRADES_SAPPHIRE_SCHIST,
            PROMENADE_ASPHALT, PROMENADE_BLUNITE,
            WILDERWILD_GABBRO);

    private final String namespace;
    private final String path;
    private final String modId;
    private final Strength strength;
    private final MapColor mapColor;
    private final Set<OreKind> ores;
    private final Set<OreKind> refused;
    private volatile Block block;

    private HostStone(String namespace, String path, Strength strength, MapColor mapColor, Set<OreKind> ores) {
        this(namespace, path, namespace, strength, mapColor, ores);
    }

    private HostStone(String namespace, String path, String modId, Strength strength, MapColor mapColor,
                      Set<OreKind> ores) {
        this.namespace = namespace;
        this.path = path;
        this.modId = modId;
        this.strength = strength;
        this.mapColor = mapColor;
        // An EnumSet, not Set.copyOf: that one's iteration order changes from run to run, and this
        // order is the registration and creative tab order.
        final EnumSet<OreKind> all = EnumSet.noneOf(OreKind.class);
        all.addAll(ores);
        all.addAll(ModdedPairs.of(namespace + ":" + path));
        // The fixed geology rule: an ore that never forms in this rock gets no variant here, and
        // worldgen turns it into the stone instead (see MatrixGeology).
        final EnumSet<OreKind> refused = EnumSet.noneOf(OreKind.class);
        for (OreKind ore : all) {
            if (MatrixGeology.refuses(namespace + "_" + path, ore.id())) {
                refused.add(ore);
            }
        }
        all.removeAll(refused);
        this.ores = Collections.unmodifiableSet(all);
        this.refused = Collections.unmodifiableSet(refused);
    }

    /** The same stone, present only while {@code modId} is installed: it is that mod that places it. */
    private HostStone placedBy(String modId) {
        final EnumSet<OreKind> swallowed = EnumSet.noneOf(OreKind.class);
        swallowed.addAll(ores);
        swallowed.addAll(refused);
        return new HostStone(namespace, path, modId, strength, mapColor, swallowed);
    }

    /** The mod whose presence makes this a host, and whose config category it sits in. */
    public String modId() {
        return modId;
    }

    public Identifier id() {
        return Identifier.fromNamespaceAndPath(namespace, path);
    }

    /** Id prefix for our variants. Carries the namespace, because Create and Blockus both have a limestone. */
    public String name() {
        return namespace + "_" + path;
    }

    public Strength strength() {
        return strength;
    }

    public MapColor mapColor() {
        return mapColor;
    }

    /** The ores this stone swallows that get a variant here. */
    public Set<OreKind> ores() {
        return ores;
    }

    /** The ores this stone swallows that never form in it: worldgen turns them into the stone. */
    public Set<OreKind> refused() {
        return refused;
    }

    /** Vanilla rock that a mod places (Create's calcite and smooth basalt), as opposed to a mod's own. */
    public boolean vanilla() {
        return "minecraft".equals(namespace);
    }

    public boolean isLoaded() {
        return Services.PLATFORM.isModLoaded(modId);
    }

    /**
     * The stone itself, or null if its mod is absent or the id does not resolve. Only call once every
     * mod has registered, i.e. never during our own registration.
     */
    public Block block() {
        Block found = block;
        if (found == null) {
            found = BuiltInRegistries.BLOCK.getOptional(id()).orElse(null);
            block = found;
        }
        return found;
    }

    @Override
    public String toString() {
        return id().toString();
    }
}
