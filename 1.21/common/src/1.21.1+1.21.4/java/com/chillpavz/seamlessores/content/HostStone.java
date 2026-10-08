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
 *   <li><b>A stone another mod places</b>. Such a stone is laid down AFTER the ores (or the ores into
 *       it), so it ends up around ore of every form, the "swallowed" ores. Which ones is measured, not
 *       derived: every ore that reaches the stone's height band in its biome at a rate above the floor.
 *       A missing pair is a visible bug, because the stone swallows that ore regardless. Its variants
 *       exist while the mod that places it is installed.</li>
 * </ul>
 *
 * <p>A swallowed ore that never forms in the stone (the fixed geology rule, {@link OreGeology}) gets no
 * variant there: worldgen turns it into the stone instead.
 *
 * <p>tools/&lt;band&gt;/generate_assets.py PARSES this table, and so does Seamless Glowing Ores' pack
 * generator: keep each host one expression of the shape {@code vanilla("path", OreTier.X, MapColor.Y)}
 * (with an optional second id path) or {@code placed("namespace", "path", OreTier.X, MapColor.Y, ORE, ...)},
 * optionally followed by {@code .placedBy("mod")} or {@code .swallowing("mod", ORE, ...)}.
 */
public final class HostStone {

    // --- The game's own rock ---------------------------------------------------------------------
    // Stone and deepslate are absent: vanilla ships matching ores for both. Calcite is absent because
    // it appears in no replaceables tag, so ore never generates in it. Smooth basalt likewise: its only
    // block tag is sculk_replaceable, and it essentially only occurs in amethyst geodes.
    public static final HostStone GRANITE = vanilla("granite", OreTier.STONE, MapColor.DIRT);
    public static final HostStone DIORITE = vanilla("diorite", OreTier.STONE, MapColor.QUARTZ);
    public static final HostStone ANDESITE = vanilla("andesite", OreTier.STONE, MapColor.STONE);
    // Tuff sits in deepslate_ore_replaceables, so vanilla currently puts deepslate-textured ore in it.
    // That is the most visible seam in the game and the clearest single win for this mod.
    public static final HostStone TUFF = vanilla("tuff", OreTier.DEEPSLATE, MapColor.TERRACOTTA_GRAY);
    // Ore never generates IN dripstone. The dripstone cluster converts the cave shell after the ores
    // and skips them, so its variants are swapped in there instead of by the ore features. One variant
    // per ore covers both tiers: the caves straddle y=0, so deepslate ore gets wrapped as well.
    public static final HostStone DRIPSTONE = vanilla("dripstone", "dripstone_block", OreTier.DRIPSTONE,
            MapColor.TERRACOTTA_BROWN);
    // Nether hosts: the two stones in base_stone_nether besides netherrack itself. Their variants ADD
    // ore, see OreTier.NETHER, so their worldgen injection is config-gated.
    public static final HostStone BASALT = vanilla("basalt", OreTier.NETHER, MapColor.COLOR_BLACK);
    public static final HostStone BLACKSTONE = vanilla("blackstone", OreTier.NETHER, MapColor.COLOR_BLACK);

    /**
     * Registration order: the game's own rock first, then the stones other mods place, by mod, as the
     * config screen lists them.
     */
    public static final List<HostStone> ALL = List.of(
            GRANITE, DIORITE, ANDESITE, TUFF, DRIPSTONE, BASALT, BLACKSTONE);

    private final String name;
    private final ResourceLocation id;
    private final OreTier tier;
    private final MapColor mapColor;
    private final String placedBy;
    private final String swallowedBy;
    private final List<OreType> swallows;
    private final List<OreType> refused;
    private volatile Block block;

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
        return new HostStone(name, ResourceLocation.withDefaultNamespace(path), tier, mapColor, null, null, List.of());
    }

    /**
     * A stone the mod {@code namespace} places, around the listed ores and the measured modded ones.
     * Its name carries the namespace, because two mods may each have a limestone.
     */
    private static HostStone placed(String namespace, String path, OreTier tier, MapColor mapColor, OreType... ores) {
        return new HostStone(namespace + "_" + path, ResourceLocation.fromNamespaceAndPath(namespace, path), tier,
                mapColor, namespace, namespace, List.of(ores));
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
        return placedBy == null
                ? BuiltInRegistries.BLOCK.containsKey(id)
                : Services.PLATFORM.isModLoaded(placedBy);
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
