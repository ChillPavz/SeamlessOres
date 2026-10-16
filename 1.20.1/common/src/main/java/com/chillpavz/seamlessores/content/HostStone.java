package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
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
 *       the ore that generates in them, by tier (see {@link OreTier}); dripstone, basalt and
 *       blackstone each have a mechanism of their own. Which ores pair is derived from the ore table.</li>
 *   <li><b>A stone another mod places</b>: Blockus' limestone, Create's strata, Twigs' rhyolite.
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
 * <p>tools/&lt;band&gt;/generate_assets.py PARSES this table, and so does Seamless Glowing Ores' pack
 * generator: keep each host one expression of the shape {@code vanilla("path", OreTier.X, MapColor.Y)}
 * (with an optional second id path) or {@code placed("namespace", "path", OreTier.X, MapColor.Y, ORE, ...)},
 * optionally followed by {@code .placedBy("mod")}, {@code .swallowing("mod", ORE, ...)} or {@code .backportedBy("mod")}.
 */
public final class HostStone {

    // --- The game's own rock ---------------------------------------------------------------------
    // Stone and deepslate are absent: vanilla ships matching ores for both.
    public static final HostStone GRANITE = vanilla("granite", OreTier.STONE, MapColor.DIRT);
    public static final HostStone DIORITE = vanilla("diorite", OreTier.STONE, MapColor.QUARTZ);
    public static final HostStone ANDESITE = vanilla("andesite", OreTier.STONE, MapColor.STONE);
    // Tuff sits in deepslate_ore_replaceables, so vanilla currently puts deepslate-textured ore in it.
    // That is the most visible seam in the game and the clearest single win for this mod.
    public static final HostStone TUFF = vanilla("tuff", OreTier.DEEPSLATE, MapColor.TERRACOTTA_GRAY);
    // Ore never generates IN dripstone. The dripstone cluster converts the cave shell after the ores
    // and skips them, so its variants are swapped in there instead of by the ore features. One variant
    // per ore covers both tiers: the caves straddle y=0, so deepslate ore gets wrapped as well.
    // Create's strata lay dripstone too, in the mountains as well, and swallow these ores there.
    public static final HostStone DRIPSTONE = vanilla("dripstone", "dripstone_block", OreTier.DRIPSTONE,
            MapColor.TERRACOTTA_BROWN)
            .swallowing("create", COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    // Cinnabar is the game's own rock from 26.2; on this band Vanilla Backport adds it under the same id,
    // in its Sulfur Caves, so the host exists only with that mod (an id test alone would also match
    // another mod's minecraft:cinnabar). Its variants ADD ore, see OreTier.CINNABAR.
    public static final HostStone CINNABAR = vanilla("cinnabar", OreTier.CINNABAR, MapColor.COLOR_RED)
            .backportedBy("vanillabackport");
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
    // under 3.0 hardness takes the stone ore's, the rest the deepslate ore's. Which of the game's ores
    // each one swallows is measured for this band by the pair model (references/tools/som-grid).

    // Blockus (Fabric). Map colours read from BlockusBlocks. Limestone, marble and bluestone copy stone's
    // properties and viridite copies deepslate's; viridite lies deep and in the deep dark: no coal, no emerald.
    public static final HostStone BLOCKUS_LIMESTONE = placed("blockus", "limestone", OreTier.STONE, MapColor.WOOD,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone BLOCKUS_MARBLE = placed("blockus", "marble", OreTier.STONE, MapColor.QUARTZ,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone BLOCKUS_BLUESTONE = placed("blockus", "bluestone", OreTier.STONE, MapColor.COLOR_CYAN,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone BLOCKUS_VIRIDITE = placed("blockus", "viridite", OreTier.DEEPSLATE, MapColor.PLANT,
            IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND, ZINC);

    // Create. Its strata are one layered feature per dimension, which also lays down three of the game's
    // stones. Scoria and smooth basalt are in BOTH strata, so they take the overworld ores and the two
    // Nether ones; scorchia only the Nether. Map colours and hardness as read on 26.x.
    public static final HostStone CREATE_ASURINE = placed("create", "asurine", OreTier.STONE, MapColor.COLOR_BLUE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_CRIMSITE = placed("create", "crimsite", OreTier.STONE, MapColor.COLOR_RED,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_LIMESTONE = placed("create", "limestone", OreTier.STONE, MapColor.SAND,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_OCHRUM = placed("create", "ochrum", OreTier.STONE, MapColor.TERRACOTTA_YELLOW,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone CREATE_SCORCHIA = placed("create", "scorchia", OreTier.STONE,
            MapColor.TERRACOTTA_GRAY,
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

    // Create: TFMG lays strata of its own with Create's layered feature, 1 in 18 chunks from y -30 to 70.
    // Bauxite copies deepslate's properties, galena and lignite calcite's, all at hardness 1.25 or under
    // (TFMGPaletteStoneTypes, TFMGBlocks): stone tier.
    public static final HostStone TFMG_BAUXITE = placed("tfmg", "bauxite", OreTier.STONE, MapColor.DEEPSLATE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone TFMG_GALENA = placed("tfmg", "galena", OreTier.STONE, MapColor.TERRACOTTA_WHITE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone TFMG_LIGNITE = placed("tfmg", "lignite", OreTier.STONE, MapColor.TERRACOTTA_WHITE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);

    // Twigs: rhyolite (a pillar, hardness 1.5) low in the overworld, schist (1.0) in mountains, bloodstone
    // (1.0) in three Nether biomes. Map colours from their DyeColor in TwigsBlocks.
    public static final HostStone TWIGS_RHYOLITE = placed("twigs", "rhyolite", OreTier.STONE, MapColor.COLOR_BROWN,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone TWIGS_SCHIST = placed("twigs", "schist", OreTier.STONE, MapColor.SNOW,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone TWIGS_BLOODSTONE = placed("twigs", "bloodstone", OreTier.STONE, MapColor.COLOR_GRAY,
            NETHER_GOLD, QUARTZ);

    // Forbidden and Arcanus: the bottom 13 blocks of the overworld. Darkstone copies stone at
    // hardness 4.5 (ModBlocks), so it takes the deepslate ore's form.
    public static final HostStone FORBIDDEN_ARCANUS_DARKSTONE = placed("forbidden_arcanus", "darkstone",
            OreTier.DEEPSLATE, MapColor.STONE,
            IRON, GOLD, REDSTONE, LAPIS, DIAMOND, ZINC);

    // Meadow: limestone in the Meadow biome, laid after every ore. Meadow already puts its own alpine ores
    // in it for the game's ores it covers, so only the others are paired here. Copies stone.
    public static final HostStone MEADOW_LIMESTONE = placed("meadow", "limestone", OreTier.STONE, MapColor.STONE,
            ZINC);

    // Mythic Upgrades: its own two cave biomes, which list no emerald; not in any ore replaceables tag,
    // and zinc is placed after them, so zinc never reaches them. Sapphire schist is its Nether rifts
    // stone, where it swallows only Mythic Upgrades' own ruby ore.
    public static final HostStone MYTHICUPGRADES_AQUAMARINE_SCHIST = placed("mythicupgrades", "aquamarine_schist",
            OreTier.STONE, MapColor.COLOR_LIGHT_BLUE,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    public static final HostStone MYTHICUPGRADES_CITRINE_SCHIST = placed("mythicupgrades", "citrine_schist",
            OreTier.STONE, MapColor.COLOR_YELLOW,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    public static final HostStone MYTHICUPGRADES_PERIDOT_SCHIST = placed("mythicupgrades", "peridot_schist",
            OreTier.STONE, MapColor.COLOR_LIGHT_GREEN,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    public static final HostStone MYTHICUPGRADES_TOPAZ_SCHIST = placed("mythicupgrades", "topaz_schist", OreTier.STONE,
            MapColor.COLOR_ORANGE,
            COAL, IRON, COPPER, GOLD, REDSTONE, LAPIS, DIAMOND);
    public static final HostStone MYTHICUPGRADES_SAPPHIRE_SCHIST = placed("mythicupgrades", "sapphire_schist",
            OreTier.STONE, MapColor.LAPIS);

    // Promenade (Fabric). Both in stone_ore_replaceables, so later ore lands in them.
    public static final HostStone PROMENADE_ASPHALT = placed("promenade", "asphalt", OreTier.STONE, MapColor.DEEPSLATE,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);
    public static final HostStone PROMENADE_BLUNITE = placed("promenade", "blunite", OreTier.STONE,
            MapColor.TERRACOTTA_CYAN,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);

    // Spawn: reefstone under the oceans, y 10 to 63. Hardness 1.0 (SpawnBlocks).
    public static final HostStone SPAWN_REEFSTONE = placed("spawn", "reefstone", OreTier.STONE,
            MapColor.TERRACOTTA_GRAY,
            COAL, IRON, COPPER, GOLD, REDSTONE, EMERALD, LAPIS, DIAMOND, ZINC);

    /**
     * Registration order: the game's own rock first, then the stones other mods place, by mod, as the
     * config screen lists them.
     */
    public static final List<HostStone> ALL = List.of(
            GRANITE, DIORITE, ANDESITE, TUFF, DRIPSTONE, CINNABAR, BASALT, BLACKSTONE, MINECRAFT_BLACKSTONE,
            BLOCKUS_LIMESTONE, BLOCKUS_MARBLE, BLOCKUS_BLUESTONE, BLOCKUS_VIRIDITE, CREATE_ASURINE, CREATE_CRIMSITE,
            CREATE_LIMESTONE, CREATE_OCHRUM, CREATE_SCORCHIA, CREATE_SCORIA, CREATE_VERIDIUM, MINECRAFT_CALCITE,
            MINECRAFT_SMOOTH_BASALT, TFMG_BAUXITE, TFMG_GALENA, TFMG_LIGNITE, TWIGS_RHYOLITE, TWIGS_SCHIST,
            TWIGS_BLOODSTONE, FORBIDDEN_ARCANUS_DARKSTONE, MEADOW_LIMESTONE, MYTHICUPGRADES_AQUAMARINE_SCHIST,
            MYTHICUPGRADES_CITRINE_SCHIST, MYTHICUPGRADES_PERIDOT_SCHIST, MYTHICUPGRADES_TOPAZ_SCHIST,
            MYTHICUPGRADES_SAPPHIRE_SCHIST, PROMENADE_ASPHALT, PROMENADE_BLUNITE, SPAWN_REEFSTONE);

    private final String name;
    private final ResourceLocation id;
    private final OreTier tier;
    private final MapColor mapColor;
    private final String placedBy;
    private final String swallowedBy;
    private final List<OreType> swallows;
    private final List<OreType> refused;
    private volatile Block block;
    /** The mod that adds this game rock to this band, or null: see {@link #backportedBy}. */
    private String backportedBy;

    private HostStone(String name, ResourceLocation id, OreTier tier, MapColor mapColor, String placedBy,
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
        return new HostStone(name, new ResourceLocation("minecraft", path), tier, mapColor, null, null, List.of());
    }

    /**
     * A stone the mod {@code namespace} places, around the listed ores and the measured modded ones.
     * Its name carries the namespace, because two mods may each have a limestone.
     */
    private static HostStone placed(String namespace, String path, OreTier tier, MapColor mapColor, OreType... ores) {
        return new HostStone(namespace + "_" + path, new ResourceLocation(namespace, path), tier,
                mapColor, namespace, namespace, List.of(ores));
    }

    /** The same stone, present only while {@code modId} is installed: it is that mod that places it. */
    private HostStone placedBy(String modId) {
        return new HostStone(name, id, tier, mapColor, modId, modId, swallows);
    }

    /**
     * The same rock, which only {@code modId} adds to this Minecraft (a later game block, backported): it
     * exists, and its variants with it, only while that mod is installed. The block may be registered
     * after ours, so its presence is never read from the block registry.
     */
    private HostStone backportedBy(String modId) {
        this.backportedBy = modId;
        return this;
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
    public ResourceLocation id() {
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

    /** True for the game's own blocks, including vanilla rock another mod lays down: the Vanilla Stones tab. */
    public boolean vanillaRock() {
        return "minecraft".equals(id.getNamespace());
    }

    /**
     * Whether this host exists in this game: a mod's stone while the mod that places it is installed, the
     * game's own rock while this Minecraft has the block. Vanilla blocks are registered before any mod,
     * so this is safe to ask during our own registration.
     */
    public boolean present() {
        if (backportedBy != null) {
            return Services.PLATFORM.isModLoaded(backportedBy);
        }
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
