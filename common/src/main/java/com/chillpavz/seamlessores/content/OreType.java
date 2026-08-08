package com.chillpavz.seamlessores.content;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.UniformInt;

import java.util.List;

/**
 * An ore we produce host-matched variants of.
 *
 * <p>Ores are declared by <b>ResourceLocation, not Block reference</b>, so third-party ores can be
 * declared without compiling against their mod. The ids resolve at two different times:
 * <ul>
 *   <li><b>Registration</b> (before other mods may have registered): vanilla ids are resolved for
 *       {@code ofLegacyCopy}; modded ores never resolve here — their block properties are baked by
 *       tier instead, because mod load order is not ours to rely on.</li>
 *   <li><b>Worldgen injection</b> (server start, every registry complete): all ids resolve.</li>
 * </ul>
 *
 * <p>An ore only applies to a host stone if it has a vanilla equivalent for that host's tier, so
 * quartz never pairs with granite and iron never pairs with basalt.
 *
 * @param name          id suffix, e.g. {@code iron} -> {@code granite_iron_ore}
 * @param overlay       texture key, {@code seamlessores:block/<overlay>_overlay}. Separate from
 *                      {@code name} because overworld and nether gold are different <i>textures</i>
 * @param requiredModId mod that must be loaded for this ore's variants to exist, or null for
 *                      vanilla. The registered block set stays derived: both sides have the mod or
 *                      neither, so client and server always agree
 * @param stoneOre      id of the ore this stands in for in stone-tier hosts, or null
 * @param deepslateOre  id for deepslate-tier hosts, or null
 * @param netherOre     id for nether-tier hosts, or null
 * @param xp            experience dropped on break; vanilla values read out of the 26.2 jar
 * @param redstoneLike  redstone ore is a {@code RedStoneOreBlock} (lit state, random ticks), not a
 *                      plain {@code DropExperienceBlock}, and handles its own xp internally
 */
public record OreType(String name, String overlay, String requiredModId,
                      ResourceLocation stoneOre, ResourceLocation deepslateOre, ResourceLocation netherOre,
                      IntProvider xp, boolean redstoneLike) {

    private static ResourceLocation mc(String path) {
        return ResourceLocation.withDefaultNamespace(path);
    }

    private static OreType overworld(String name, IntProvider xp) {
        return new OreType(name, name, null, mc(name + "_ore"), mc("deepslate_" + name + "_ore"), null, xp, false);
    }

    private static OreType nether(String name, String overlay, String oreId, IntProvider xp) {
        return new OreType(name, overlay, null, null, null, mc(oreId), xp, false);
    }

    // XP values verified against Blocks.java in the decompiled 26.2 source. Vanilla uses the SAME
    // value for a stone ore and its deepslate counterpart, so host rock never changes xp - do not
    // "improve" on this without reading the mechanics section of the maintainer notes first.
    public static final OreType COAL = overworld("coal", UniformInt.of(0, 2));
    public static final OreType IRON = overworld("iron", ConstantInt.of(0));
    public static final OreType COPPER = overworld("copper", ConstantInt.of(0));
    public static final OreType GOLD = overworld("gold", ConstantInt.of(0));
    public static final OreType LAPIS = overworld("lapis", UniformInt.of(2, 5));
    public static final OreType DIAMOND = overworld("diamond", UniformInt.of(3, 7));
    public static final OreType EMERALD = overworld("emerald", UniformInt.of(3, 7));
    public static final OreType REDSTONE = new OreType("redstone", "redstone", null,
            mc("redstone_ore"), mc("deepslate_redstone_ore"), null, ConstantInt.of(0), true);

    // Nether. NETHER_GOLD is separate from GOLD despite the same block-name suffix: different
    // overlay textures (gold over stone vs over netherrack), and they never share a host.
    public static final OreType NETHER_GOLD = nether("gold", "nether_gold", "nether_gold_ore", UniformInt.of(0, 1));
    public static final OreType QUARTZ = nether("quartz", "quartz", "nether_quartz_ore", UniformInt.of(2, 5));

    /**
     * The first modded ore, and the proof of the data-driven design. Facts verified against
     * create-fly-26.2-rc-2-6.0.9-1.jar (mod id {@code create}): blocks {@code create:zinc_ore} /
     * {@code create:deepslate_zinc_ore}; loot drops {@code create:raw_zinc} in the vanilla iron
     * shape; worldgen is a plain {@code minecraft:ore} feature on the SAME two replaceables tags as
     * vanilla — so our injection restyles existing zinc generation, balance-neutral; tool tier is
     * {@code needs_iron_tool} (NOT stone, unlike iron/copper). XP 0 by raw-metal convention.
     */
    public static final OreType ZINC = new OreType("zinc", "zinc", "create",
            ResourceLocation.fromNamespaceAndPath("create", "zinc_ore"),
            ResourceLocation.fromNamespaceAndPath("create", "deepslate_zinc_ore"),
            null, ConstantInt.of(0), false);

    /**
     * Mythic Upgrades (mod id {@code mythicupgrades}, MIT). All facts verified against
     * mythicupgrades-fabric-26.2-5.1.0.jar rather than assumed:
     * <ul>
     *   <li>The five overworld ores target the SAME {@code stone_ore_replaceables} /
     *       {@code deepslate_ore_replaceables} tags as vanilla, so injecting them is a pure restyle
     *       at zero balance cost, exactly like Create's zinc.</li>
     *   <li>Ruby and sapphire are {@code block_match minecraft:netherrack} only, so their
     *       basalt/blackstone variants ADD ore, the same caveat as our nether gold and quartz. They
     *       ride the same host toggles and the same bastion protection.</li>
     *   <li>Ametrine and jade are deliberately absent: they are {@code block_match end_stone}, and
     *       the End has no second stone type, so there is nothing to be seamless with.</li>
     *   <li>All twelve are {@code needs_iron_tool}, drop one item with the {@code ore_drops} fortune
     *       formula, and return the block on Silk Touch.</li>
     * </ul>
     */
    private static OreType mythic(String name, IntProvider xp) {
        return new OreType(name, name, "mythicupgrades",
                ResourceLocation.fromNamespaceAndPath("mythicupgrades", name + "_ore"),
                ResourceLocation.fromNamespaceAndPath("mythicupgrades", "deepslate_" + name + "_ore"),
                null, xp, false);
    }

    private static OreType mythicNether(String name, IntProvider xp) {
        return new OreType(name, name, "mythicupgrades", null, null,
                ResourceLocation.fromNamespaceAndPath("mythicupgrades", name + "_ore"), xp, false);
    }

    // XP read out of MythicBlocks: the four gems are UniformInt.of(6, 14), ruby and sapphire are
    // UniformInt.of(4, 10), and necoium has NO experience provider at all - it drops raw_necoium and
    // is a metal, so zero, matching the vanilla raw-metal convention.
    public static final OreType AQUAMARINE = mythic("aquamarine", UniformInt.of(6, 14));
    public static final OreType CITRINE = mythic("citrine", UniformInt.of(6, 14));
    public static final OreType PERIDOT = mythic("peridot", UniformInt.of(6, 14));
    public static final OreType TOPAZ = mythic("topaz", UniformInt.of(6, 14));
    public static final OreType NECOIUM = mythic("necoium", ConstantInt.of(0));
    public static final OreType RUBY = mythicNether("ruby", UniformInt.of(4, 10));
    public static final OreType SAPPHIRE = mythicNether("sapphire", UniformInt.of(4, 10));

    public static final List<OreType> ALL =
            List.of(COAL, IRON, COPPER, GOLD, LAPIS, DIAMOND, EMERALD, REDSTONE, NETHER_GOLD, QUARTZ,
                    ZINC,
                    AQUAMARINE, CITRINE, PERIDOT, TOPAZ, NECOIUM, RUBY, SAPPHIRE);

    /** The id of the ore this type stands in for in the given host, or <b>null</b> if no pairing. */
    public ResourceLocation vanillaFor(HostStone host) {
        return switch (host.tier()) {
            case STONE -> stoneOre;
            case DEEPSLATE -> deepslateOre;
            case NETHER -> netherOre;
        };
    }
}
