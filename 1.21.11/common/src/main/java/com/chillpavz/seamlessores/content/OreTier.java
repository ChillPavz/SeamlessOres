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
 */
public enum OreTier {
    STONE,
    DEEPSLATE,
    NETHER
}
