package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.material.MapColor;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import static com.chillpavz.seamlessores.content.OreType.COAL;
import static com.chillpavz.seamlessores.content.OreType.COPPER;
import static com.chillpavz.seamlessores.content.OreType.DIAMOND;
import static com.chillpavz.seamlessores.content.OreType.EMERALD;
import static com.chillpavz.seamlessores.content.OreType.GOLD;
import static com.chillpavz.seamlessores.content.OreType.IRON;
import static com.chillpavz.seamlessores.content.OreType.LAPIS;
import static com.chillpavz.seamlessores.content.OreType.NETHER_GOLD;
import static com.chillpavz.seamlessores.content.OreType.QUARTZ;
import static com.chillpavz.seamlessores.content.OreType.REDSTONE;
import static com.chillpavz.seamlessores.content.OreType.ZINC;

/**
 * A stone that ore sits in, where no ore of that look exists.
 *
 * <p>Declared by id, never by Block reference: a host may belong to another mod, which may register
 * after us, and this mod never compiles against it. The block is looked up when first needed, which is
 * always after every mod has registered (and for the game's own rock, at any time).
 *
 * <p>Two kinds of host, and the difference is where their ores come from:
 * <ul>
 *   <li><b>The game's own rock</b> ({@link #placedBy()} null): granite, diorite, andesite and tuff take
 *       the ore that generates in them, by tier (see {@link OreTier}); dripstone, cinnabar, basalt and
 *       blackstone each have a mechanism of their own. Which ores pair is derived from the ore table.</li>
 *   <li><b>A stone another mod places</b>: Blockus' limestone, Create's strata, Wilder Wild's gabbro.
 *       Such a stone is laid down AFTER the ores (or the ores into it), so it ends up around ore of
 *       every form, the "swallowed" ores. Which ones is measured, not derived: every ore that reaches
 *       the stone's height band in its biome at a rate above the floor. A missing pair is a visible
 *       bug, because the stone swallows that ore regardless. Its variants exist while the mod that
 *       places it is installed. That is the stone's own mod, except for the vanilla rock in Create's
 *       strata: calcite is such a host only because Create lays it down in bands, so it hangs on
 *       Create, and keeps its own namespace in its ids (minecraft_calcite_iron_ore).</li>
 * </ul>
 * Dripstone is both: the game's own rock with derived pairs, which Create's strata also lay over ore.
 *
 * <p>A swallowed ore that never forms in the stone (the fixed geology rule, {@link OreGeology}) gets no
 * variant there: worldgen turns it into the stone instead.
 *
 * <p>tools/generate_assets.py PARSES this table, and so does Seamless Glowing Ores' pack generator: keep
 * each host one expression of the shape {@code vanilla("path", OreTier.X, MapColor.Y)} (with an optional
 * second id path) or {@code placed("namespace", "path", OreTier.X, MapColor.Y, ORE, ...)}, optionally
 * followed by {@code .placedBy("mod")} or {@code .swallowing("mod", ORE, ...)}.
 */
public final class HostStone {

    // --- The game's own rock ---------------------------------------------------------------------
    // Stone and deepslate are absent: vanilla ships matching ores for both.
    public static final HostStone GRANITE = vanilla("granite", OreTier.STONE, MapColor.DIRT);
    public static final HostStone DIORITE = vanilla("diorite", OreTier.STONE, MapColor.QUARTZ);
    public static final HostStone ANDESITE = vanilla("andesite", OreTier.STONE, MapColor.STONE);
    // Vanilla puts deepslate-textured ore in tuff, the most visible seam in the game. From 26.3 tuff is
    // height specific (deepslate ore below y=8, stone ore above y=0) and natural tuff barely reaches
    // above 0. The worldgen injection keeps vanilla's own test, so this variant follows the deepslate half.
    public static final HostStone TUFF = vanilla("tuff", OreTier.DEEPSLATE, MapColor.TERRACOTTA_GRAY);
    // Ore never generates IN dripstone. The dripstone cluster converts the cave shell after the ores
    // and skips them, so its variants are swapped in there instead of by the ore features. One variant
    // per ore covers both tiers: the caves straddle y=0, so deepslate ore gets wrapped as well.
    // Create's strata lay dripstone too, in the mountains as well (hence a dripstone emerald), and
    // swallow these ores there.
    public static final HostStone DRIPSTONE = vanilla("dripstone", "dripstone_block", OreTier.DRIPSTONE,
            MapColor.TERRACOTTA_BROWN)
            .swallowing("create", COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    // Cinnabar exists from 26.2 only, and this jar also runs on 26.1, where the block is not in the
    // game: no cinnabar variant is built there (see present()). Its variants ADD ore, see OreTier.CINNABAR.
    public static final HostStone CINNABAR = vanilla("cinnabar", OreTier.CINNABAR, MapColor.COLOR_RED);
    // Nether hosts: the two stones in base_stone_nether besides netherrack itself. Their variants ADD
    // ore, see OreTier.NETHER, so their worldgen injection is config-gated.
    public static final HostStone BASALT = vanilla("basalt", OreTier.NETHER, MapColor.COLOR_BLACK);
    public static final HostStone BLACKSTONE = vanilla("blackstone", OreTier.NETHER, MapColor.COLOR_BLACK);
    // The same rock deep in the Overworld, a stone other worldgen places: Terralith (mod or datapack)
    // puts blackstone in deepslate_ore_replaceables and lays it in its thermal and mantle caves before
    // the ores, so ore lands in it. Measured and judged like any such stone (pairs, fixed geology rule),
    // but present in every game, because a datapack cannot be detected at registration: its variants
    // only generate where a pack lays the rock. Ids carry the namespace (minecraft_blackstone_gold_ore),
    // because blackstone_gold_ore is the Nether one.
    public static final HostStone MINECRAFT_BLACKSTONE = placed("minecraft", "blackstone", OreTier.DEEPSLATE,
            MapColor.COLOR_BLACK,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    // Calcite and smooth basalt are in no ore replaceables tag, so ore never generates in them on its
    // own; they are hosts only where Create lays them down, below.

    // --- Stones other mods place ------------------------------------------------------------------
    // The tier is the ore form a variant takes its strength, experience and drops from: every host
    // under 3.0 hardness takes the stone ore's, the rest the deepslate ore's.

    // Blockus: Fabric only, every 26.x band. Map colours read from BlockusBlocks. Limestone, marble and
    // bluestone copy stone's properties and viridite copies deepslate's.
    public static final HostStone BLOCKUS_LIMESTONE = placed("blockus", "limestone", OreTier.STONE, MapColor.WOOD,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone BLOCKUS_MARBLE = placed("blockus", "marble", OreTier.STONE, MapColor.QUARTZ,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone BLOCKUS_BLUESTONE = placed("blockus", "bluestone", OreTier.STONE, MapColor.COLOR_CYAN,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    // Deep and deep dark only: no coal, no emerald, and copper falls just under the floor.
    public static final HostStone BLOCKUS_VIRIDITE = placed("blockus", "viridite", OreTier.DEEPSLATE, MapColor.PLANT,
            IRON, GOLD, REDSTONE, LAPIS, DIAMOND, ZINC);

    // Create (Create Fly, Fabric, 26.1.2 and 26.2). Its strata are one layered feature per dimension;
    // the overworld one also lays down three vanilla stones. Scoria and smooth basalt are in BOTH
    // strata, so they take the overworld ores and the two nether ones; scorchia only the nether. Map
    // colours and hardness of every host below were read back from the running 26.2 game.
    public static final HostStone CREATE_ASURINE = placed("create", "asurine", OreTier.STONE, MapColor.COLOR_BLUE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_CRIMSITE = placed("create", "crimsite", OreTier.STONE, MapColor.COLOR_RED,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_LIMESTONE = placed("create", "limestone", OreTier.STONE, MapColor.SAND,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_OCHRUM = placed("create", "ochrum", OreTier.STONE, MapColor.TERRACOTTA_YELLOW,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_SCORCHIA = placed("create", "scorchia", OreTier.STONE, MapColor.TERRACOTTA_GRAY,
            NETHER_GOLD, QUARTZ);
    public static final HostStone CREATE_SCORIA = placed("create", "scoria", OreTier.STONE, MapColor.COLOR_BROWN,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC, NETHER_GOLD, QUARTZ);
    public static final HostStone CREATE_VERIDIUM = placed("create", "veridium", OreTier.STONE, MapColor.WARPED_NYLIUM,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone MINECRAFT_CALCITE = placed("minecraft", "calcite", OreTier.STONE,
            MapColor.TERRACOTTA_WHITE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC).placedBy("create");
    public static final HostStone MINECRAFT_SMOOTH_BASALT = placed("minecraft", "smooth_basalt", OreTier.STONE,
            MapColor.COLOR_BLACK,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC, NETHER_GOLD, QUARTZ).placedBy("create");

    // Forbidden and Arcanus: NeoForge, 26.1.2 (beta). The bottom 13 blocks of the overworld. Hardness 4.5
    // and map colour read back from the running 26.1.2 game.
    public static final HostStone FORBIDDEN_ARCANUS_DARKSTONE = placed("forbidden_arcanus", "darkstone",
            OreTier.DEEPSLATE, MapColor.STONE,
            IRON, GOLD, REDSTONE, LAPIS, DIAMOND);

    // Mythic Upgrades: both loaders, 26.2 and 26.3. Its own two cave biomes, which list no emerald; not
    // in any ore replaceables tag, and zinc is placed after them, so zinc never reaches them.
    public static final HostStone MYTHICUPGRADES_AQUAMARINE_SCHIST = placed("mythicupgrades", "aquamarine_schist",
            OreTier.STONE, MapColor.COLOR_LIGHT_BLUE,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    public static final HostStone MYTHICUPGRADES_CITRINE_SCHIST = placed("mythicupgrades", "citrine_schist",
            OreTier.STONE, MapColor.COLOR_YELLOW,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    public static final HostStone MYTHICUPGRADES_PERIDOT_SCHIST = placed("mythicupgrades", "peridot_schist",
            OreTier.STONE, MapColor.COLOR_LIGHT_GREEN,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    public static final HostStone MYTHICUPGRADES_TOPAZ_SCHIST = placed("mythicupgrades", "topaz_schist",
            OreTier.STONE, MapColor.COLOR_ORANGE,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    // The nether rifts (its own nether biome). No vanilla ore reaches it: vanilla's nether ores run a
    // step later. It swallows Mythic Upgrades' own ruby ore, which its biome places before it.
    // Hardness 1.5 and map colour read from MythicBlocks.
    public static final HostStone MYTHICUPGRADES_SAPPHIRE_SCHIST = placed("mythicupgrades", "sapphire_schist",
            OreTier.STONE, MapColor.LAPIS);

    // Promenade: Fabric on every 26.x version, NeoForge on 26.3 (6.0.0). Both in stone_ore_replaceables,
    // so later ore lands in them.
    public static final HostStone PROMENADE_ASPHALT = placed("promenade", "asphalt", OreTier.STONE, MapColor.DEEPSLATE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone PROMENADE_BLUNITE = placed("promenade", "blunite", OreTier.STONE,
            MapColor.TERRACOTTA_CYAN,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);

    // Wilder Wild: Fabric every band, NeoForge from 26.2. Only in its magmatic caves biome, which lists
    // no emerald. Map colour and hardness (4.5) read from the running game.
    public static final HostStone WILDERWILD_GABBRO = placed("wilderwild", "gabbro", OreTier.DEEPSLATE,
            MapColor.TERRACOTTA_BROWN,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND, ZINC);

    /**
     * Registration order: the game's own rock first, then the stones other mods place, by mod, as the
     * config screen lists them.
     */
    public static final List<HostStone> ALL = List.of(
            GRANITE, DIORITE, ANDESITE, TUFF, DRIPSTONE, CINNABAR, BASALT, BLACKSTONE, MINECRAFT_BLACKSTONE,
            BLOCKUS_LIMESTONE, BLOCKUS_MARBLE, BLOCKUS_BLUESTONE, BLOCKUS_VIRIDITE,
            CREATE_ASURINE, CREATE_CRIMSITE, CREATE_LIMESTONE, CREATE_OCHRUM, CREATE_SCORCHIA, CREATE_SCORIA,
            CREATE_VERIDIUM, MINECRAFT_CALCITE, MINECRAFT_SMOOTH_BASALT,
            FORBIDDEN_ARCANUS_DARKSTONE,
            MYTHICUPGRADES_AQUAMARINE_SCHIST, MYTHICUPGRADES_CITRINE_SCHIST, MYTHICUPGRADES_PERIDOT_SCHIST,
            MYTHICUPGRADES_TOPAZ_SCHIST, MYTHICUPGRADES_SAPPHIRE_SCHIST,
            PROMENADE_ASPHALT, PROMENADE_BLUNITE,
            WILDERWILD_GABBRO);

    private final String name;
    private final Identifier id;
    private final OreTier tier;
    private final MapColor mapColor;
    private final String placedBy;
    private final String swallowedBy;
    private final List<OreType> swallows;
    private final List<OreType> refused;
    private volatile Block block;

    private HostStone(String name, Identifier id, OreTier tier, MapColor mapColor, String placedBy,
                      String swallowedBy, List<OreType> listed) {
        this.name = name;
        this.id = id;
        this.tier = tier;
        this.mapColor = mapColor;
        this.placedBy = placedBy;
        this.swallowedBy = swallowedBy;
        // The listed ores and the measured modded ones, in ore table order: the registration and
        // creative tab order.
        final Set<OreType> all = new LinkedHashSet<>(listed);
        all.addAll(ModdedPairs.of(id.toString()));
        final List<OreType> swallows = new ArrayList<>();
        final List<OreType> refused = new ArrayList<>();
        for (OreType ore : OreType.ALL) {
            if (all.contains(ore)) {
                swallows.add(ore);
                if (OreGeology.fixed(name, ore.key())) {
                    refused.add(ore);
                }
            }
        }
        this.swallows = List.copyOf(swallows);
        this.refused = List.copyOf(refused);
    }

    /** The game's own rock, {@code minecraft:<name>}. */
    private static HostStone vanilla(String name, OreTier tier, MapColor mapColor) {
        return vanilla(name, name, tier, mapColor);
    }

    /** The game's own rock whose id path is not the name its variants carry (dripstone_block). */
    private static HostStone vanilla(String name, String path, OreTier tier, MapColor mapColor) {
        return new HostStone(name, Identifier.withDefaultNamespace(path), tier, mapColor, null, null, List.of());
    }

    /**
     * A stone the mod {@code namespace} places, around the listed ores and the measured modded ones.
     * Its name carries the namespace, because Create and Blockus both have a limestone.
     */
    private static HostStone placed(String namespace, String path, OreTier tier, MapColor mapColor, OreType... ores) {
        return new HostStone(namespace + "_" + path, Identifier.fromNamespaceAndPath(namespace, path), tier, mapColor,
                namespace, namespace, List.of(ores));
    }

    /** The same stone, present only while {@code modId} is installed: it is that mod that places it. */
    private HostStone placedBy(String modId) {
        return new HostStone(name, id, tier, mapColor, modId, modId, swallows);
    }

    /** The same rock, which {@code modId}'s stone feature also lays over the listed ores. */
    private HostStone swallowing(String modId, OreType... ores) {
        return new HostStone(name, id, tier, mapColor, placedBy, modId, List.of(ores));
    }

    /** Id prefix for our variants, e.g. {@code granite} or {@code blockus_limestone}. */
    public String name() {
        return name;
    }

    /** The stone's own block id. */
    public Identifier id() {
        return id;
    }

    public OreTier tier() {
        return tier;
    }

    public MapColor mapColor() {
        return mapColor;
    }

    /** The mod that places this stone, or null for the game's own rock. */
    public String placedBy() {
        return placedBy;
    }

    /** True for the game's own blocks, including the vanilla rock Create lays down: the Vanilla Stones tab. */
    public boolean vanillaRock() {
        return Identifier.DEFAULT_NAMESPACE.equals(id.getNamespace());
    }

    /**
     * Whether this host exists in this game: a mod's stone while the mod that places it is installed, the
     * game's own rock while this Minecraft has the block (cinnabar is 26.2 and up). Vanilla blocks are
     * registered before any mod, so this is safe to ask during our own registration.
     */
    public boolean present() {
        return placedBy == null
                ? BuiltInRegistries.BLOCK.containsKey(id)
                : Services.PLATFORM.isModLoaded(placedBy) && ModdedPairs.shipsHere(placedBy);
    }

    /**
     * The ores a mod's stone feature lays this rock over, refused ones included, while that mod is
     * installed; none otherwise.
     */
    public List<OreType> swallows() {
        return swallowedBy != null && Services.PLATFORM.isModLoaded(swallowedBy) ? swallows : List.of();
    }

    /** The swallowed ores that never form in this rock: worldgen turns them into the stone. */
    public List<OreType> refused() {
        return swallowedBy != null && Services.PLATFORM.isModLoaded(swallowedBy) ? refused : List.of();
    }

    /** The ores that have a variant in this host, in ore table order. Independent of what is installed. */
    public List<OreType> ores() {
        final List<OreType> ores = new ArrayList<>();
        for (OreType ore : OreType.ALL) {
            if (placedBy == null ? ore.formIn(this) != null : swallows.contains(ore) && !refused.contains(ore)) {
                ores.add(ore);
            }
        }
        return ores;
    }

    /**
     * The stone itself, or null if the id does not resolve. Only call once every mod has registered, i.e.
     * never during our own registration for a mod's stone.
     */
    public Block block() {
        Block found = block;
        if (found == null) {
            found = BuiltInRegistries.BLOCK.getOptional(id).orElse(null);
            block = found;
        }
        return found;
    }

    @Override
    public String toString() {
        return id.toString();
    }
}
