package com.chillpavz.seamlessores.content;

/**
 * Which vanilla ore a host stone receives, which is what a variant stands in for.
 * <p>
 * Vanilla's overworld ore features target two block tags: {@code minecraft:stone_ore_replaceables}
 * ({@code stone, granite, diorite, andesite}) and {@code minecraft:deepslate_ore_replaceables}
 * ({@code deepslate, tuff}).
 * <p>
 * {@link #NETHER} is different in kind and it matters: {@code ore_nether_gold} and {@code ore_quartz}
 * target {@code block_match: minecraft:netherrack} <b>only</b>, so vanilla places no gold or quartz
 * in basalt or blackstone at all. Nether variants therefore <b>add</b> ore rather than restyling it,
 * which is why they are the one part of the mod behind a config toggle.
 * <p>
 * {@link #DRIPSTONE} is different again: no ore feature ever targets dripstone, so the injector gives
 * it no target at all. Vanilla's dripstone cluster lays its shell over the cave walls AFTER the ores
 * and skips every ore block, which leaves stone ore standing in a dripstone wall. A dripstone variant
 * is swapped in for that one ore at that moment (see {@code DripstoneShell}), so it stands in for the
 * stone-tier ore and never adds any.
 * <p>
 * {@link #CINNABAR} ADDS ore, like {@link #NETHER}: no vanilla feature targets cinnabar. A few rare
 * features of our own place the ores that really form beside cinnabar (gold, silver, iron as pyrite,
 * the zinc and lead sulfides) and redstone into the Sulfur Caves' cinnabar, from 26.2.
 */
public enum OreTier {
    STONE,
    DEEPSLATE,
    NETHER,
    DRIPSTONE,
    CINNABAR
}
