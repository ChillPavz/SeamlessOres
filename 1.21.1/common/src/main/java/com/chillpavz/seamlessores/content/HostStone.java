package com.chillpavz.seamlessores.content;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.material.MapColor;

import java.util.List;

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
    // Tuff sits in deepslate_ore_replaceables, so vanilla currently puts deepslate-textured ore in it.
    // That is the most visible seam in the game and the clearest single win for this mod.
    public static final HostStone TUFF =
            new HostStone("tuff", Blocks.TUFF, OreTier.DEEPSLATE, MapColor.TERRACOTTA_GRAY, SoundType.TUFF);

    // Nether hosts. These are the two stones in base_stone_nether besides netherrack itself.
    // Their variants ADD ore - see OreTier.NETHER - so their worldgen injection is config-gated.
    public static final HostStone BASALT =
            new HostStone("basalt", Blocks.BASALT, OreTier.NETHER, MapColor.COLOR_BLACK, SoundType.BASALT);
    public static final HostStone BLACKSTONE =
            new HostStone("blackstone", Blocks.BLACKSTONE, OreTier.NETHER, MapColor.COLOR_BLACK, SoundType.STONE);

    public static final List<HostStone> ALL = List.of(GRANITE, DIORITE, ANDESITE, TUFF, BASALT, BLACKSTONE);
}
