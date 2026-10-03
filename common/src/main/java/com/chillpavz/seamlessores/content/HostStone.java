package com.chillpavz.seamlessores.content;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.material.MapColor;

import java.util.List;
import java.util.Objects;
import java.util.stream.Stream;

/**
 * A stone that ore can sit in but which has no matching ore texture in vanilla.
 *
 * @param name     id prefix for our variants, e.g. {@code granite} -> {@code granite_iron_ore}
 * @param block    the vanilla stone itself; the worldgen target tests against this
 * @param tier     which vanilla ore this stone receives, see {@link OreTier}
 * @param mapColor the host stone's map colour, so variants read correctly on a map
 * @param sound    the host stone's sound, so variants sound like what they are made of
 */
public record HostStone(String name, Block block, OreTier tier, MapColor mapColor, SoundType sound) {

    // Stone and deepslate are deliberately absent: vanilla already ships matching ores for both.
    // Calcite is absent because it appears in no replaceables tag, so ore never generates in it.
    // Smooth basalt likewise - its only block tag is sculk_replaceable, and it essentially only
    // occurs in amethyst geodes, so a smooth basalt ore would have nowhere to live.
    public static final HostStone GRANITE =
            new HostStone("granite", Blocks.GRANITE, OreTier.STONE, MapColor.DIRT, SoundType.STONE);
    public static final HostStone DIORITE =
            new HostStone("diorite", Blocks.DIORITE, OreTier.STONE, MapColor.QUARTZ, SoundType.STONE);
    public static final HostStone ANDESITE =
            new HostStone("andesite", Blocks.ANDESITE, OreTier.STONE, MapColor.STONE, SoundType.STONE);
    // Vanilla puts deepslate-textured ore in tuff, the most visible seam in the game. From 26.3 tuff is
    // height specific (deepslate ore below y=8, stone ore above y=0) and natural tuff barely reaches
    // above 0. The worldgen injection keeps vanilla's own test, so this variant follows the deepslate half.
    public static final HostStone TUFF =
            new HostStone("tuff", Blocks.TUFF, OreTier.DEEPSLATE, MapColor.TERRACOTTA_GRAY, SoundType.TUFF);
    // Ore never generates IN dripstone. The dripstone cluster converts the cave shell after the ores
    // and skips them, so its variants are swapped in there instead of by the ore features. One variant
    // per ore covers both tiers: the caves straddle y=0, so deepslate ore gets wrapped as well.
    public static final HostStone DRIPSTONE =
            new HostStone("dripstone", Blocks.DRIPSTONE_BLOCK, OreTier.DRIPSTONE, MapColor.TERRACOTTA_BROWN,
                    SoundType.DRIPSTONE_BLOCK);

    // Nether hosts. These are the two stones in base_stone_nether besides netherrack itself.
    // Their variants ADD ore - see OreTier.NETHER - so their worldgen injection is config-gated.
    public static final HostStone BASALT =
            new HostStone("basalt", Blocks.BASALT, OreTier.NETHER, MapColor.COLOR_BLACK, SoundType.BASALT);
    public static final HostStone BLACKSTONE =
            new HostStone("blackstone", Blocks.BLACKSTONE, OreTier.NETHER, MapColor.COLOR_BLACK, SoundType.STONE);

    // Cinnabar exists from 26.2 only, and this jar also runs on 26.1, where the block (and its sound)
    // is not in the game. So it is read from the registry by id and is NULL there; ALL leaves it out,
    // and no cinnabar variant is ever built. Vanilla blocks are registered before any mod loads.
    // Its variants ADD ore - see OreTier.CINNABAR.
    public static final HostStone CINNABAR = optional("cinnabar", "cinnabar", OreTier.CINNABAR, MapColor.COLOR_RED);

    public static final List<HostStone> ALL =
            Stream.of(GRANITE, DIORITE, ANDESITE, TUFF, DRIPSTONE, CINNABAR, BASALT, BLACKSTONE)
                    .filter(Objects::nonNull)
                    .toList();

    /** A host whose block only some Minecraft versions have; null where it is absent. */
    private static HostStone optional(String name, String blockId, OreTier tier, MapColor mapColor) {
        return BuiltInRegistries.BLOCK.getOptional(Identifier.withDefaultNamespace(blockId))
                .map(block -> new HostStone(name, block, tier, mapColor, block.defaultBlockState().getSoundType()))
                .orElse(null);
    }
}
