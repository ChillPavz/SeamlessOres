package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.UniformInt;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Stream;

import java.util.List;
import java.util.Map;
import java.util.Set;

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
 * quartz never pairs with granite and iron never pairs with basalt. <b>This is also what stops us
 * inventing ore for third-party mods:</b> an ore that targets only
 * {@code stone_ore_replaceables} gets a null {@code deepslateOre}, so it produces granite, diorite
 * and andesite variants but no tuff one, because it never generates in tuff to begin with.
 *
 * @param name             id suffix in the game's own rock, e.g. {@code iron} -> {@code granite_iron_ore}.
 *                         Unique per host only: Nether gold is also {@code gold}, because no such rock
 *                         takes both
 * @param key              unique across the table, the id suffix in a stone another mod places (one of
 *                         those can take both golds: {@code create_scoria_nether_gold_ore}) and the key
 *                         of the geology rule. The overlay key, except for Silent's Gems' Nether gems,
 *                         which share their overworld gem's art
 * @param overlay          texture key, {@code seamlessores:block/<overlay>_overlay}. Separate from
 *                         {@code name} because overworld and nether gold are different <i>textures</i>
 * @param deepslateOverlay overlay for DEEPSLATE-tier hosts when the mod draws that tier
 *                         differently, or null to reuse {@code overlay}. Only Mythic Metals'
 *                         unobtainium needs it: its deepslate ore is animated and its stone one is not
 * @param requiredModId    mod that must be loaded for this ore's variants to exist, or null for
 *                         vanilla. The registered block set stays derived: both sides have the mod or
 *                         neither, so client and server always agree
 * @param stoneOre         id of the ore this stands in for in stone-tier hosts, or null
 * @param deepslateOre     id for deepslate-tier hosts, or null
 * @param netherOre        id for nether-tier hosts, or null
 * @param xp               experience dropped on break, for stone and nether tiers
 * @param deepslateXp      experience for DEEPSLATE-tier hosts, or null to reuse {@code xp}. Only
 *                         Mythic Metals' morkite needs it: 1-2 in stone but 1-3 in deepslate
 * @param redstoneLike     redstone ore is a {@code RedStoneOreBlock} (lit state, random ticks), not a
 *                         plain {@code DropExperienceBlock}, and handles its own xp internally
 * @param skipHosts        host names to leave alone because the ore's own mod already ships a
 *                         seamless variant for them. Ours would otherwise take that host over: the
 *                         injector prepends its targets, so it would win against the mod's own entry
 * @param strength         hardness and blast resistance where the ore's own mod sets them, or null for
 *                         the vanilla ore convention, which the vanilla block a variant copies carries
 * @param endOre           id of the ore's End form, or null. No host of the game's own takes it (the End
 *                         has only end stone); it pairs with the End stones other mods place, which
 *                         take it as "the first form the ore has"
 */
public record OreType(String name, String key, String overlay, String deepslateOverlay, String requiredModId,
                      ResourceLocation stoneOre, ResourceLocation deepslateOre, ResourceLocation netherOre,
                      IntProvider xp, IntProvider deepslateXp, boolean redstoneLike,
                      Set<String> skipHosts, Strength strength, ResourceLocation endOre) {

    private static final IntProvider NONE = ConstantInt.of(0);

    /** Hardness and blast resistance in a stone or Nether host, then in a deepslate-tier one. */
    public record Strength(float hardness, float resistance, float deepHardness, float deepResistance) {}

    /** An ore keyed by its overlay, at the vanilla ore strength. */
    private static OreType ore(String name, String overlay, String deepslateOverlay, String requiredModId,
                               ResourceLocation stoneOre, ResourceLocation deepslateOre, ResourceLocation netherOre,
                               IntProvider xp, IntProvider deepslateXp, boolean redstoneLike,
                               Set<String> skipHosts) {
        return new OreType(name, overlay, overlay, deepslateOverlay, requiredModId, stoneOre, deepslateOre,
                netherOre, xp, deepslateXp, redstoneLike, skipHosts, null, null);
    }

    /** The same ore with the strength its own mod sets, read from that mod's jar. */
    private OreType withStrength(float hardness, float resistance, float deepHardness, float deepResistance) {
        return new OreType(name, key, overlay, deepslateOverlay, requiredModId, stoneOre, deepslateOre, netherOre,
                xp, deepslateXp, redstoneLike, skipHosts,
                new Strength(hardness, resistance, deepHardness, deepResistance), endOre);
    }

    /** An ore with no deepslate form: stone tier only, or Nether only. */
    private OreType withStrength(float hardness, float resistance) {
        return withStrength(hardness, resistance, hardness, resistance);
    }

    /** The same ore under another key. */
    private OreType withKey(String key) {
        return new OreType(name, key, overlay, deepslateOverlay, requiredModId, stoneOre, deepslateOre, netherOre,
                xp, deepslateXp, redstoneLike, skipHosts, strength, endOre);
    }

    /** The same ore, given no variant in the named hosts (see {@code skipHosts}). */
    private OreType skipping(String... hosts) {
        return new OreType(name, key, overlay, deepslateOverlay, requiredModId, stoneOre, deepslateOre, netherOre,
                xp, deepslateXp, redstoneLike, Set.of(hosts), strength, endOre);
    }

    private static ResourceLocation mc(String path) {
        return ResourceLocation.withDefaultNamespace(path);
    }

    private static ResourceLocation of(String namespace, String path) {
        return ResourceLocation.fromNamespaceAndPath(namespace, path);
    }

    private static OreType overworld(String name, IntProvider xp) {
        return ore(name, name, null, null,
                mc(name + "_ore"), mc("deepslate_" + name + "_ore"), null, xp, null, false, Set.of());
    }

    private static OreType nether(String name, String overlay, String oreId, IntProvider xp) {
        return ore(name, overlay, null, null, null, null, mc(oreId), xp, null, false, Set.of());
    }

    // XP values verified against Blocks.java in the decompiled source. Vanilla uses the SAME
    // value for a stone ore and its deepslate counterpart, so host rock never changes xp - do not
    // "improve" on this without reading the mechanics section of the maintainer notes first.
    public static final OreType COAL = overworld("coal", UniformInt.of(0, 2));
    public static final OreType IRON = overworld("iron", ConstantInt.of(0));
    public static final OreType COPPER = overworld("copper", ConstantInt.of(0));
    public static final OreType GOLD = overworld("gold", ConstantInt.of(0));
    public static final OreType LAPIS = overworld("lapis", UniformInt.of(2, 5));
    public static final OreType DIAMOND = overworld("diamond", UniformInt.of(3, 7));
    // No dripstone emerald: emerald generates in the mountains only, where dripstone caves never reach.
    public static final OreType EMERALD = overworld("emerald", UniformInt.of(3, 7)).skipping("dripstone");
    public static final OreType REDSTONE = ore("redstone", "redstone", null, null,
            mc("redstone_ore"), mc("deepslate_redstone_ore"), null, ConstantInt.of(0), null, true, Set.of());

    // Nether. NETHER_GOLD is separate from GOLD despite the same block-name suffix: different
    // overlay textures (gold over stone vs over netherrack), and they never share a host.
    public static final OreType NETHER_GOLD = nether("gold", "nether_gold", "nether_gold_ore", UniformInt.of(0, 1));
    public static final OreType QUARTZ = nether("quartz", "quartz", "nether_quartz_ore", UniformInt.of(2, 5));

    /**
     * The first modded ore, and the proof of the data-driven design. Facts verified against the real
     * Create jar (mod id {@code create}): blocks {@code create:zinc_ore} /
     * {@code create:deepslate_zinc_ore}; loot drops {@code create:raw_zinc} in the vanilla iron
     * shape; worldgen is a plain {@code minecraft:ore} feature on the SAME two replaceables tags as
     * vanilla — so our injection restyles existing zinc generation, balance-neutral; tool tier is
     * {@code needs_iron_tool} (NOT stone, unlike iron/copper). XP 0 by raw-metal convention.
     */
    public static final OreType ZINC = ore("zinc", "zinc", null, "create",
            of("create", "zinc_ore"), of("create", "deepslate_zinc_ore"),
            null, ConstantInt.of(0), null, false, Set.of());

    // --- Mythic Upgrades (mod id mythicupgrades, MIT) -------------------------------------------
    // The five overworld ores target the SAME replaceables tags as vanilla, so injecting them is a
    // pure restyle at zero balance cost. Ruby and sapphire are block_match netherrack only, so their
    // basalt/blackstone variants ADD ore, the same caveat as our nether gold and quartz, and ride
    // the same host toggles and bastion protection. Ametrine and jade are End ores (end_stone only).
    // Ametrine has an End form for one host: Mythic Upgrades' own jade schist, laid over the ametrine
    // its End biome placed first. Jade has none: nothing places a stone over it.
    private static OreType mythic(String name, IntProvider xp) {
        return ore(name, name, null, "mythicupgrades",
                of("mythicupgrades", name + "_ore"), of("mythicupgrades", "deepslate_" + name + "_ore"),
                null, xp, null, false, Set.of());
    }

    private static OreType mythicEnd(String name, IntProvider xp) {
        return new OreType(name, name, name, null, "mythicupgrades", null, null, null, xp, null, false,
                Set.of(), null, of("mythicupgrades", name + "_ore"));
    }

    private static OreType mythicNether(String name, IntProvider xp) {
        return ore(name, name, null, "mythicupgrades", null, null,
                of("mythicupgrades", name + "_ore"), xp, null, false, Set.of());
    }

    public static final OreType AQUAMARINE = mythic("aquamarine", UniformInt.of(6, 14));
    public static final OreType CITRINE = mythic("citrine", UniformInt.of(6, 14));
    public static final OreType PERIDOT = mythic("peridot", UniformInt.of(6, 14));
    public static final OreType TOPAZ = mythic("topaz", UniformInt.of(6, 14));
    public static final OreType NECOIUM = mythic("necoium", ConstantInt.of(0));
    public static final OreType RUBY = mythicNether("ruby", UniformInt.of(4, 10));
    public static final OreType SAPPHIRE = mythicNether("sapphire", UniformInt.of(4, 10));
    // XP 6-14, hardness 3.0 and blast resistance 9.0 (end stone's), read from MythicBlocks on every band.
    public static final OreType AMETRINE = mythicEnd("ametrine", UniformInt.of(6, 14)).withStrength(3.0F, 9.0F);

    // --- Mythic Metals (mod id mythicmetals, MIT) -----------------------------------------------
    // Every fact here was read out of the real jar; see the mapping table in the maintainer notes.
    //
    // THE RULE THAT STOPS US INVENTING ORE: ten of these target stone_ore_replaceables ONLY, so they
    // generate in granite, diorite and andesite but NEVER in tuff, which lives in
    // deepslate_ore_replaceables. Those get a null deepslateOre and so produce three variants, not
    // four. Giving them a tuff variant would add ore that does not exist.
    //
    // XP: only morkite, stormyx and unobtainium drop any at all - the rest are registered through
    // MythicBlocks' createOre overload that takes no experience provider. Morkite is also the reason
    // deepslateXp exists: 1-2 in stone but 1-3 in deepslate.
    private static OreType mmBoth(String name, IntProvider xp, IntProvider deepslateXp) {
        return ore(name, name, null, "mythicmetals",
                of("mythicmetals", name + "_ore"), of("mythicmetals", "deepslate_" + name + "_ore"),
                null, xp, deepslateXp, false, Set.of());
    }

    /** Stone tier only: generates in granite, diorite and andesite, never in tuff. */
    private static OreType mmStone(String name) {
        return ore(name, name, null, "mythicmetals",
                of("mythicmetals", name + "_ore"), null, null, NONE, null, false, Set.of());
    }

    private static OreType mmNether(String name, String overlay, String oreId, IntProvider xp,
                                    Set<String> skipHosts) {
        return ore(name, overlay, null, "mythicmetals", null, null,
                of("mythicmetals", oreId), xp, null, false, skipHosts);
    }

    // Both tiers: granite, diorite, andesite and tuff.
    public static final OreType ADAMANTITE = mmBoth("adamantite", NONE, null)
            .withStrength(4.0F, 5.0F, 6.0F, 12.0F);
    public static final OreType CARMOT = mmBoth("carmot", NONE, null)
            .withStrength(5.5F, 6.5F, 6.5F, 12.0F);
    public static final OreType MORKITE = mmBoth("morkite", UniformInt.of(1, 2), UniformInt.of(1, 3))
            .withStrength(3.0F, 4.0F, 3.0F, 4.0F);
    public static final OreType MYTHRIL = mmBoth("mythril", NONE, null)
            .withStrength(5.0F, 6.0F, 5.5F, 6.5F);
    public static final OreType PROMETHEUM = mmBoth("prometheum", NONE, null)
            .withStrength(5.0F, 6.0F, 6.0F, 7.0F);
    public static final OreType RUNITE = mmBoth("runite", NONE, null)
            .withStrength(8.0F, 9.0F, 9.0F, 10.0F);
    /** Unobtainium's DEEPSLATE ore is animated (4 frames) while its stone one is a still image. */
    public static final OreType UNOBTAINIUM = ore("unobtainium", "unobtainium",
            "unobtainium_deepslate", "mythicmetals",
            of("mythicmetals", "unobtainium_ore"), of("mythicmetals", "deepslate_unobtainium_ore"),
            null, NONE, UniformInt.of(4, 7), false, Set.of())
            .withStrength(16.0F, 13000.0F, 21.0F, 14000.0F);

    // Stone tier only.
    public static final OreType AQUARIUM = mmStone("aquarium")
            .withStrength(4.0F, 5.0F);
    public static final OreType BANGLUM = mmStone("banglum")
            .withStrength(5.0F, 5.5F);
    public static final OreType KYBER = mmStone("kyber")
            .withStrength(3.0F, 4.0F);
    public static final OreType MANGANESE = mmStone("manganese")
            .withStrength(3.0F, 4.0F);
    public static final OreType OSMIUM = mmStone("osmium")
            .withStrength(4.0F, 5.0F);
    public static final OreType PLATINUM = mmStone("platinum")
            .withStrength(3.5F, 4.5F);
    public static final OreType QUADRILLUM = mmStone("quadrillum")
            .withStrength(3.5F, 4.5F);
    public static final OreType SILVER = mmStone("silver")
            .withStrength(2.5F, 3.5F);
    public static final OreType STARRITE = mmStone("starrite")
            .withStrength(5.0F, 6.0F);
    public static final OreType TIN = mmStone("tin")
            .withStrength(2.0F, 3.0F);
    /**
     * Orichalcum targets both replaceables tags, but Mythic Metals ships its OWN
     * {@code tuff_orichalcum_ore} through an explicit {@code block_match tuff} target that sits
     * ahead of its deepslate tag entry. Tuff is therefore already seamless, and a variant of ours
     * would take that host away from it, because the injector prepends. So tuff is skipped, while
     * the deepslate form is still this ore wherever another mod's stone swallows it.
     */
    public static final OreType ORICHALCUM = mmBoth("orichalcum", NONE, null).skipping("tuff")
            .withStrength(5.5F, 6.5F);

    // Nether. Like our own gold and quartz these ADD ore, so they ride the basalt and blackstone
    // host toggles and the bastion protection. BANGLUM's nether form reuses the plain name for the
    // same reason NETHER_GOLD does: the host already disambiguates, since the overworld form only
    // pairs with stone-tier hosts and this one only with nether hosts.
    public static final OreType NETHER_BANGLUM =
            mmNether("banglum", "nether_banglum", "nether_banglum_ore", NONE, Set.of())
            .withStrength(5.0F, 5.5F);
    public static final OreType MIDAS_GOLD = mmNether("midas_gold", "midas_gold", "midas_gold_ore", NONE, Set.of())
            .withStrength(4.0F, 5.0F);
    public static final OreType PALLADIUM = mmNether("palladium", "palladium", "palladium_ore", NONE, Set.of())
            .withStrength(5.0F, 6.0F);
    /** Mythic Metals already ships {@code blackstone_stormyx_ore}, so we only add the basalt one. */
    public static final OreType STORMYX =
            mmNether("stormyx", "stormyx", "stormyx_ore", UniformInt.of(2, 4), Set.of("blackstone"))
            .withStrength(5.0F, 6.0F);

    // --- Silent's Gems (mod id silentgems, MIT) -------------------------------------------------
    // Every gem targets BOTH replaceables tags, so all four host stones apply and injecting them is
    // a pure restyle. Loot is the plain vanilla shape (silk touch returns the block, otherwise the
    // gem with the ore_drops fortune formula), so the generator transforms their tables directly.
    //
    // XP was read out of the jar rather than assumed, and generalising would have been wrong twice:
    // GemOreBlock's constructor hardcodes UniformInt.of(1, 5) for the twenty gems, but silver is
    // ConstantInt.of(0) and chaos is UniformInt.of(3, 7), each built by its own factory method.
    //
    // NAME PREFIXES ARE LOAD BEARING. Our block id is <host>_<name>_ore, and five of these ores
    // share a name with one we already ship: aquamarine, citrine, peridot and topaz collide with
    // Mythic Upgrades, and silver with Mythic Metals. With both mods installed the same id would be
    // registered twice. Those five carry a `silents_` prefix; the rest keep the plain name.
    // Ruby and sapphire need NO prefix even though Mythic Upgrades has both: theirs are netherrack
    // only, so they never share a host with these (and from 6.0.0 an id carries the ore's mod). Different hosts,
    // no clash. The overlay key follows the name, so the prefixed five need their own art files.
    private static OreType silentGem(String name, IntProvider xp) {
        final String plain = name.startsWith("silents_") ? name.substring("silents_".length()) : name;
        return ore(name, name, null, "silentgems",
                of("silentgems", plain + "_ore"), of("silentgems", "deepslate_" + plain + "_ore"),
                null, xp, null, false, Set.of());
    }

    private static final IntProvider GEM_XP = UniformInt.of(1, 5);

    public static final OreType SG_ALEXANDRITE = silentGem("alexandrite", GEM_XP);
    public static final OreType SG_AMMOLITE = silentGem("ammolite", GEM_XP);
    public static final OreType SG_BLACK_DIAMOND = silentGem("black_diamond", GEM_XP);
    public static final OreType SG_CARNELIAN = silentGem("carnelian", GEM_XP);
    public static final OreType SG_GARNET = silentGem("garnet", GEM_XP);
    public static final OreType SG_HELIODOR = silentGem("heliodor", GEM_XP);
    public static final OreType SG_IOLITE = silentGem("iolite", GEM_XP);
    public static final OreType SG_KYANITE = silentGem("kyanite", GEM_XP);
    public static final OreType SG_MOLDAVITE = silentGem("moldavite", GEM_XP);
    public static final OreType SG_PEARL = silentGem("pearl", GEM_XP);
    public static final OreType SG_ROSE_QUARTZ = silentGem("rose_quartz", GEM_XP);
    // Same block names as Mythic Upgrades' nether ruby and sapphire, but their own art: the overlay
    // key differs, or both mods' variants would share one texture.
    public static final OreType SG_RUBY = ore("ruby", "silents_ruby", null, "silentgems",
            of("silentgems", "ruby_ore"), of("silentgems", "deepslate_ruby_ore"), null, GEM_XP, null, false, Set.of());
    public static final OreType SG_SAPPHIRE = ore("sapphire", "silents_sapphire", null, "silentgems",
            of("silentgems", "sapphire_ore"), of("silentgems", "deepslate_sapphire_ore"), null, GEM_XP, null, false, Set.of());
    public static final OreType SG_TANZANITE = silentGem("tanzanite", GEM_XP);
    public static final OreType SG_TURQUOISE = silentGem("turquoise", GEM_XP);
    public static final OreType SG_WHITE_DIAMOND = silentGem("white_diamond", GEM_XP);
    // Prefixed to avoid a block id clash, see above.
    public static final OreType SG_AQUAMARINE = silentGem("silents_aquamarine", GEM_XP);
    public static final OreType SG_CITRINE = silentGem("silents_citrine", GEM_XP);
    public static final OreType SG_PERIDOT = silentGem("silents_peridot", GEM_XP);
    public static final OreType SG_TOPAZ = silentGem("silents_topaz", GEM_XP);
    /** A metal, not a gem: drops raw_silver and gives no experience. */
    public static final OreType SG_SILVER = silentGem("silents_silver", NONE);
    /** Chaos drops chaos_essence and is the only one of these with its own experience range. */
    public static final OreType SG_CHAOS = silentGem("chaos", UniformInt.of(3, 7))
            .withStrength(5.0F, 3.0F, 6.0F, 3.0F);

    // --- Seven more third-party mods ------------------------------------------------------------
    // All target both replaceables tags (so all four hosts) except Create: New Age's thorium, which
    // is stone tier only. XP was read from each jar rather than assumed, and "it is a metal so it
    // gives nothing" would have been wrong for two of them:
    //   Dense Mekanism  fluorite UniformInt(1, 4), the other four nothing
    //   Powah           all three uraninite grades ConstantInt(0)
    //   Energized Power ConstantInt(0)
    //   TFMG, Things, Create: New Age  no DropExperienceBlock anywhere in the jar, so nothing
    //   Silent Gear     bort UniformInt(3, 7)  <- INFERRED, not proven; see the maintainer notes
    //
    // Loot is TRANSFORMED from each mod's own tables (the generator entries carry no raw_drop),
    // because Dense Mekanism and Powah both use set_count and a hand-built vanilla-shape table
    // would change their yields. Same call as Mythic Metals.
    private static OreType modded(String name, String modId, String namespace, String plain,
                                  IntProvider xp) {
        return ore(name, name, null, modId,
                of(namespace, plain + "_ore"), of(namespace, "deepslate_" + plain + "_ore"),
                null, xp, null, false, Set.of());
    }

    // Dense Mekanism. Its blocks are dense_<ore>_ore / dense_deepslate_<ore>_ore, so the plain name
    // does not follow the usual pattern and each is spelled out.
    private static OreType dmek(String ore, IntProvider xp) {
        return ore("dense_" + ore, "dense_" + ore, null, "densemekanism",
                of("densemekanism", "dense_" + ore + "_ore"),
                of("densemekanism", "dense_deepslate_" + ore + "_ore"),
                null, xp, null, false, Set.of());
    }

    public static final OreType DENSE_FLUORITE = dmek("fluorite", UniformInt.of(1, 4))
            .withStrength(5.0F, 9.0F, 6.0F, 9.0F);
    public static final OreType DENSE_LEAD = dmek("lead", NONE)
            .withStrength(5.0F, 9.0F, 6.0F, 9.0F);
    public static final OreType DENSE_OSMIUM = dmek("osmium", NONE)
            .withStrength(7.5F, 12.0F, 8.5F, 12.0F);
    public static final OreType DENSE_TIN = dmek("tin", NONE)
            .withStrength(5.0F, 6.0F, 6.0F, 6.0F);
    public static final OreType DENSE_URANIUM = dmek("uranium", NONE)
            .withStrength(5.0F, 9.0F, 6.0F, 9.0F);

    // Powah. Three grades of the same ore, named uraninite_ore_poor / _dense in the mod.
    private static OreType powah(String name, String plain) {
        return ore(name, name, null, "powah",
                of("powah", plain), of("powah", "deepslate_" + plain), null, NONE, null, false, Set.of());
    }

    public static final OreType URANINITE = powah("uraninite", "uraninite_ore")
            .withStrength(3.2F, 8.0F, 4.5F, 3.0F);
    public static final OreType URANINITE_POOR = powah("uraninite_poor", "uraninite_ore_poor")
            .withStrength(3.0F, 8.0F, 4.5F, 3.0F);
    public static final OreType URANINITE_DENSE = powah("uraninite_dense", "uraninite_ore_dense")
            .withStrength(4.0F, 8.0F, 4.5F, 3.0F);

    // Create: The Factory Must Grow. Its bauxite, galena, lignite and fireclay are NOT ores, they
    // are striated deposit blocks placed by create:layered_ore, so only these three apply.
    public static final OreType TFMG_LEAD = modded("lead", "tfmg", "tfmg", "lead", NONE);
    public static final OreType TFMG_LITHIUM = modded("lithium", "tfmg", "tfmg", "lithium", NONE);
    public static final OreType TFMG_NICKEL = modded("nickel", "tfmg", "tfmg", "nickel", NONE);

    /** Prefixed: plain {@code tin} is already Mythic Metals', and both are stone-tier hosts. */
    public static final OreType ENERGIZED_TIN =
            modded("energized_tin", "energizedpower", "energizedpower", "tin", NONE);

    public static final OreType GLEAMING = modded("gleaming", "things", "things", "gleaming", NONE);
    public static final OreType BORT =
            modded("bort", "silentgear", "silentgear", "bort", UniformInt.of(3, 7))
            .withStrength(4.0F, 10.0F, 4.0F, 10.0F);

    /**
     * Create: New Age targets {@code stone_ore_replaceables} only, so thorium generates in granite,
     * diorite and andesite but never tuff. Its magnetite_block is excluded: a whole-block deposit at
     * 15 veins per chunk, not an ore with blobs on a host stone.
     */
    public static final OreType THORIUM = ore("thorium", "thorium", null, "create_new_age",
            of("create_new_age", "thorium_ore"), null, null, NONE, null, false, Set.of())
            .withStrength(3.5F, 3.5F);

    // Silent's Gems in the NETHER. Like our own gold and quartz these ADD ore, because the mod
    // targets c:netherracks only, so they ride the basalt and blackstone host toggles, the nether
    // rarity and vein-size dials, and the bastion protection.
    //
    // ONLY EIGHT OF THE TWENTY-ONE NETHER GEMS ARE HERE, and that is the whole point: the other
    // thirteen (ammolite, aquamarine, garnet, heliodor, kyanite, opal, peridot, rose_quartz, ruby,
    // sapphire, topaz, turquoise, white_diamond) have count 0 AND size 0 in their placed features,
    // so they are registered but place nothing. Giving those a variant would invent ore outright.
    // A feature can target the right tag and still be inert - check the placement counts too.
    //
    // These reuse the overworld overlay rather than needing new art: measured against the mod's own
    // nether textures, the existing masks land 96-100% on the gem pixels, because Silent's Gems
    // draws the same blobs on netherrack that it draws on stone.
    //
    // Air exposure is INHERITED from the mod's feature (discard 0.0, so they do show on exposed
    // faces). That is deliberate: we extend their target list rather than adding a feature, and a
    // gem visible in a netherrack wall should still be visible when the wall is basalt. Contrast
    // Mythic Upgrades' ruby and sapphire, which are genuinely new veins through NetherGemFeature at
    // discard 1.0, copied from ancient debris.
    private static OreType silentNether(String name, String plain) {
        return ore(name, name, null, "silentgems", null, null,
                of("silentgems", "nether_" + plain + "_ore"), GEM_XP, null, false, Set.of())
                .withKey("nether_" + name);
    }

    public static final OreType SG_N_ALEXANDRITE = silentNether("alexandrite", "alexandrite")
            .withStrength(4.0F, 4.0F);
    public static final OreType SG_N_BLACK_DIAMOND = silentNether("black_diamond", "black_diamond")
            .withStrength(4.0F, 4.0F);
    public static final OreType SG_N_CARNELIAN = silentNether("carnelian", "carnelian")
            .withStrength(4.0F, 4.0F);
    public static final OreType SG_N_CITRINE = silentNether("silents_citrine", "citrine")
            .withStrength(4.0F, 4.0F);
    public static final OreType SG_N_IOLITE = silentNether("iolite", "iolite")
            .withStrength(4.0F, 4.0F);
    public static final OreType SG_N_MOLDAVITE = silentNether("moldavite", "moldavite")
            .withStrength(4.0F, 4.0F);
    public static final OreType SG_N_PEARL = silentNether("pearl", "pearl")
            .withStrength(4.0F, 4.0F);
    // --- Ice and Fire Community Edition (mod id iceandfire, LGPL-3.0). NeoForge only at 1.21.1 ----
    // The same PREFIXED ids as 1.20.1 (Silent's Gems has its own sapphire and silver). Sapphire has no
    // deepslate tier (its feature targets stone_ore_replaceables only). Read from IafBlocks 2.1.4:
    // silver 3.0/3.0 with 2 experience (CE's change; the 1.20.1 build drops none), sapphire 4.0/3.0
    // with 3 to 7. The deepslate silver ore has specks of its own, so its own overlay.
    public static final OreType IAF_SAPPHIRE = ore(
            "iceandfire_sapphire", "iceandfire_sapphire", null, "iceandfire",
            of("iceandfire", "sapphire_ore"), null, null,
            UniformInt.of(3, 7), null, false, Set.of())
            .withStrength(4.0F, 3.0F);
    public static final OreType IAF_SILVER = ore(
            "iceandfire_silver", "iceandfire_silver", "iceandfire_deepslate_silver", "iceandfire",
            of("iceandfire", "silver_ore"), of("iceandfire", "deepslate_silver_ore"), null,
            ConstantInt.of(2), null, false, Set.of())
            .withStrength(3.0F, 3.0F, 3.0F, 3.0F);
    public static final OreType SG_N_TANZANITE = silentNether("tanzanite", "tanzanite")
            .withStrength(4.0F, 4.0F);

    // --- Tech Reborn (Fabric only at 1.21.1) ------------------------------------------------------
    // XP read from TR's OreDistribution enum, which hands each ore block its range: ruby and sapphire
    // 2-6, every other ore 0. There is no uranium at 1.21.1. Prefixed where the plain name is taken,
    // and bauxite because Modern Industrialization has one too.
    public static final OreType TR_BAUXITE = modded("techreborn_bauxite", "techreborn", "techreborn", "bauxite", NONE);
    public static final OreType TR_GALENA = modded("galena", "techreborn", "techreborn", "galena", NONE);
    public static final OreType TR_IRIDIUM = modded("iridium", "techreborn", "techreborn", "iridium", NONE);
    public static final OreType TR_LEAD = modded("techreborn_lead", "techreborn", "techreborn", "lead", NONE);
    public static final OreType TR_RUBY =
            modded("techreborn_ruby", "techreborn", "techreborn", "ruby", UniformInt.of(2, 6));
    public static final OreType TR_SAPPHIRE =
            modded("techreborn_sapphire", "techreborn", "techreborn", "sapphire", UniformInt.of(2, 6));
    public static final OreType TR_SILVER = modded("techreborn_silver", "techreborn", "techreborn", "silver", NONE);
    public static final OreType TR_TIN = modded("techreborn_tin", "techreborn", "techreborn", "tin", NONE);

    // --- Modern Industrialization (NeoForge only at 1.21.1) ----------------------------------------
    // XP read from MIMaterials: bauxite and monazite 1-4, salt 1-3, lignite coal 0-2. The rest take
    // OrePart's default, UniformInt.of(0, 0).
    /**
     * Modern Industrialization builds each ore as a full copy of its host rock ({@code stone} or
     * {@code deepslate}) and then raises only the hardness, by 1.5: the vanilla ore hardness, the
     * rock's blast resistance of 6.0. Read from this version's jar; its 1.20.1 build sets 3.0.
     */
    private static OreType mi(String name, String plain, IntProvider xp) {
        return modded(name, "modern_industrialization", "modern_industrialization", plain, xp)
                .withStrength(3.0F, 6.0F, 4.5F, 6.0F);
    }

    public static final OreType MI_ANTIMONY = mi("antimony", "antimony", NONE);
    public static final OreType MI_BAUXITE = mi("mi_bauxite", "bauxite", UniformInt.of(1, 4));
    public static final OreType MI_LEAD = mi("mi_lead", "lead", NONE);
    public static final OreType MI_LIGNITE_COAL = mi("lignite_coal", "lignite_coal", UniformInt.of(0, 2));
    public static final OreType MI_MONAZITE = mi("monazite", "monazite", UniformInt.of(1, 4));
    public static final OreType MI_NICKEL = mi("mi_nickel", "nickel", NONE);
    public static final OreType MI_SALT = mi("salt", "salt", UniformInt.of(1, 3));
    public static final OreType MI_TIN = mi("mi_tin", "tin", NONE);
    public static final OreType MI_TUNGSTEN = mi("tungsten", "tungsten", NONE);
    public static final OreType MI_URANIUM = mi("uranium", "uranium", NONE);

    /**
     * Occultism puts the tier word LAST ({@code silver_ore_deepslate}), so this cannot use
     * {@link #modded}. Its silver ore is a plain {@code Block}: no experience.
     */
    public static final OreType OCCULTISM_SILVER = ore("occultism_silver", "occultism_silver", null,
            "occultism", of("occultism", "silver_ore"), of("occultism", "silver_ore_deepslate"),
            null, NONE, null, false, Set.of())
            .withStrength(3.0F, 3.0F, 3.0F, 3.0F);

    /** Extreme Reactors registers yellorite with an xp range of 0, 0. Its overlay animates. */
    public static final OreType YELLORITE = modded("yellorite", "bigreactors", "bigreactors", "yellorite", NONE);

    /** Mystical Agriculture: Cucumber's BaseOreBlock with 2-5 on both tiers. */
    public static final OreType INFERIUM =
            modded("inferium", "mysticalagriculture", "mysticalagriculture", "inferium", UniformInt.of(2, 5));
    public static final OreType PROSPERITY =
            modded("prosperity", "mysticalagriculture", "mysticalagriculture", "prosperity", UniformInt.of(2, 5));

    // --- Immersive Engineering (NeoForge only at 1.21.1) --------------------------------------
    // Five ores, and every one of its features targets stone_ore_replaceables AND
    // deepslate_ore_replaceables, so each gets all four overworld hosts and none of them invents ore.
    //
    // This cannot use modded(): IE puts the tier word FIRST (ore_lead, deepslate_ore_lead), the
    // opposite of Occultism's trailing one. Its ore blocks are plain Blocks with no experience
    // provider, so no XP, and their properties are vanilla's own (3.0/3.0 in stone, 4.5/3.0 in
    // deepslate), read from IEBlocks$Metals rather than assumed.
    //
    // Lead, nickel, silver and uranium are prefixed because those names are already taken on this
    // branch. Aluminum is free and is prefixed anyway, so that all five line up with the pack's
    // family keys and with the one overlay file the mod and the pack share. Block ids are a one-way
    // door, so these names are now fixed.
    //
    // ITS FEATURES ARE NOT minecraft:ore. They are immersiveengineering:ie_ore, whose config is IE's
    // own record rather than an OreConfiguration, which is why the band worldgen has a foreign
    // config path - see ForeignOreTargets. Art used with BluSunrize's permission (14 Sept 2026);
    // crediting Immersive Engineering and BluSunrize is a condition of it.
    private static OreType immersiveEngineering(String name, String metal) {
        return ore(name, name, null, "immersiveengineering",
                of("immersiveengineering", "ore_" + metal),
                of("immersiveengineering", "deepslate_ore_" + metal),
                null, NONE, null, false, Set.of());
    }

    public static final OreType IE_ALUMINUM = immersiveEngineering("ie_aluminum", "aluminum");
    public static final OreType IE_LEAD = immersiveEngineering("ie_lead", "lead");
    public static final OreType IE_NICKEL = immersiveEngineering("ie_nickel", "nickel");
    public static final OreType IE_SILVER = immersiveEngineering("ie_silver", "silver");
    public static final OreType IE_URANIUM = immersiveEngineering("ie_uranium", "uranium");

    // Mekanism (MIT, Aidan C. Brady). Five ores, all five on stone_ore_replaceables plus
    // deepslate_ore_replaceables, so every overworld host is a pure restyle.
    //
    // ITS FEATURES ARE NOT minecraft:ore either: mekanism:ore, configured by its own record
    // ResizableOreFeatureConfig, so it goes through the same ForeignOreTargets path IE needed.
    // Read from its jar rather than assumed: BlockOre is strength(3, 3) and the deepslate form
    // 4.5 / 3, which is exactly the convention createBlock bakes, so no STRENGTH_OVERRIDES entry.
    // Tool tier is stone for all ten blocks. XP is the one place they differ from each other:
    // OreType carries minExp/maxExp and only FLUORITE passes any, 1 to 4.
    private static OreType mekanism(String name, String ore, IntProvider xp) {
        return ore(name, name, null, "mekanism",
                of("mekanism", ore + "_ore"), of("mekanism", "deepslate_" + ore + "_ore"),
                null, xp, null, false, Set.of());
    }

    public static final OreType MEK_FLUORITE = mekanism("mek_fluorite", "fluorite", UniformInt.of(1, 4));
    public static final OreType MEK_LEAD = mekanism("mek_lead", "lead", NONE);
    public static final OreType MEK_OSMIUM = mekanism("mek_osmium", "osmium", NONE);
    public static final OreType MEK_TIN = mekanism("mek_tin", "tin", NONE);
    public static final OreType MEK_URANIUM = mekanism("mek_uranium", "uranium", NONE);

    // --- Oreganized ------------------------------------------------------------------------------
    // Lead and silver, both on the replaceables tags, so a pure restyle. Its ore blocks copy gold
    // ore (3/3, 4.5/3 in deepslate) with no experience, which is the convention, so no override.
    // Prefixed because lead and silver are taken on this branch; the overlay is shared with the pack.
    public static final OreType OREGANIZED_LEAD = modded("oreganized_lead", "oreganized", "oreganized", "lead", NONE);
    public static final OreType OREGANIZED_SILVER = modded("oreganized_silver", "oreganized", "oreganized", "silver", NONE);

    // --- Malum, 1.21.1 (NeoForge, Malum 1.8.2) --------------------------------------------------------
    // Its ore art is used with SammySemicolon's permission (8 Oct 2026; the jar says All Rights
    // Reserved), credited in the README as Immersive Engineering is. Read from the jars: every feature
    // below is plain minecraft:ore on the vanilla replaceables tags (blazing quartz on
    // base_stone_nether), so all of it is a pure restyle. Cthonic gold has NO variant: its own feature
    // reads its first target to decide whether to grow clusters (see the maintainer notes).
    // Strength from MalumBlockProperties (stone / deepslate, resistance 3 throughout); no
    // needs_*_tool tags, so any pickaxe, as the vanilla convention our variants copy.
    private static OreType malum(String name, String overlay, String stoneId, String deepslateId, IntProvider xp,
                                 IntProvider deepslateXp) {
        return ore(name, overlay, null, "malum", of("malum", stoneId), of("malum", deepslateId), null,
                xp, deepslateXp, false, Set.of());
    }

    /** Soulstone: a DropExperienceBlock of UniformInt.of(14, 18) on both tiers. */
    public static final OreType MALUM_SOULSTONE =
            malum("soulstone", "soulstone", "soulstone_ore", "deepslate_soulstone_ore", UniformInt.of(14, 18), null)
                    .withStrength(5.0F, 3.0F, 7.0F, 3.0F);
    /** Natural quartz; its deepslate form is deepslate_quartz_ore. One overlay serves both tiers. */
    public static final OreType MALUM_NATURAL_QUARTZ =
            malum("natural_quartz", "natural_quartz", "natural_quartz_ore", "deepslate_quartz_ore",
                    UniformInt.of(1, 4), UniformInt.of(2, 5))
                    .withStrength(4.0F, 3.0F, 6.0F, 3.0F);
    /** Brilliance: brilliant_stone and brilliant_deepslate. The overlay is the ore's own glow layer. */
    public static final OreType MALUM_BRILLIANCE =
            malum("brilliance", "brilliant", "brilliant_stone", "brilliant_deepslate",
                    UniformInt.of(14, 18), UniformInt.of(16, 26))
                    .withStrength(3.0F, 3.0F, 5.0F, 3.0F);
    /**
     * Blazing quartz: Nether only, and its feature already targets base_stone_nether, so basalt and
     * blackstone are a restyle like the overworld hosts (no ore added). Light 6, as the ore.
     */
    public static final OreType MALUM_BLAZING_QUARTZ =
            ore("blazing_quartz", "blazing_quartz", null, "malum", null, null, of("malum", "blazing_quartz_ore"),
                    UniformInt.of(4, 7), null, false, Set.of())
                    .withStrength(3.0F, 3.0F);

    // --- Nether ores that ADD ore (Sept 2026) -----------------------------------------------------
    // Each targets netherrack only, so basalt and blackstone variants put ore where the mod places
    // none. Behind the owning mod's own nether switch and thinned by netherOreRarity, like our gold
    // and quartz.
    private static OreType netherOnlyModded(String name, String modId, String oreId, IntProvider xp) {
        return ore(name, name, null, modId, null, null, of(modId, oreId), xp, null, false, Set.of());
    }

    /** Tech Reborn's three: OreDistribution passes them no experience. */
    public static final OreType TR_CINNABAR = netherOnlyModded("cinnabar", "techreborn", "cinnabar_ore", NONE);
    public static final OreType TR_PYRITE = netherOnlyModded("pyrite", "techreborn", "pyrite_ore", NONE);
    public static final OreType TR_SPHALERITE = netherOnlyModded("sphalerite", "techreborn", "sphalerite_ore", NONE);

    /** Extreme Reactors registers benitoite through the two-argument registerOreBlock, which passes 3, 5. */
    public static final OreType BENITOITE =
            netherOnlyModded("benitoite", "bigreactors", "benitoite_ore", UniformInt.of(3, 5));

    /**
     * Silent's Gems' opal: a {@code GemOreBlock} like every other gem, so {@link #GEM_XP}. It is
     * TRANSLUCENT, painted at partial opacity over each rock, so every host carries its own
     * precomposited overlay (the generator's {@code host_overlays}). Its nether feature places
     * nothing (size 0, count 0), so there are no basalt or blackstone variants.
     */
    public static final OreType SG_OPAL = silentGem("opal", GEM_XP);

    // --- Cobblemon (Fabric and NeoForge at 1.21.1) --------------------------------------------------
    // Every evolution stone ore comes from Cobblemon's evolutionStoneOre helpers: a DropExperienceBlock
    // with UniformInt.of(1, 2), stone and deepslate alike, and the nether fire stone the same. Fire
    // stone is the one type carrying all three tiers, because its nether ore shares the art.
    private static final IntProvider COBBLEMON_XP = UniformInt.of(1, 2);

    // Five of them also give off light: the lightLevel argument of those same helpers, identical on
    // stone and deepslate, and the nether fire stone sets 10 directly. A variant that did not match
    // would go dark the moment it replaced Cobblemon's ore.
    private static final Map<String, Integer> LIGHT = Map.of(
            "dawn_stone", 7, "fire_stone", 10, "shiny_stone", 12, "sun_stone", 2, "thunder_stone", 6,
            "blazing_quartz", 6);

    /** Block light the counterpart ore emits: 0 for almost every ore, and the same on every tier. */
    public int lightEmission() {
        return LIGHT.getOrDefault(name, 0);
    }

    private static OreType cobblemon(String plain) {
        return modded(plain, "cobblemon", "cobblemon", plain, COBBLEMON_XP);
    }

    public static final OreType CB_DAWN_STONE = cobblemon("dawn_stone");
    public static final OreType CB_DUSK_STONE = cobblemon("dusk_stone");
    public static final OreType CB_ICE_STONE = cobblemon("ice_stone");
    public static final OreType CB_LEAF_STONE = cobblemon("leaf_stone");
    // Cobblemon ships its own dripstone_moon_stone_ore, so ours would take that host over.
    public static final OreType CB_MOON_STONE = cobblemon("moon_stone").skipping("dripstone");
    public static final OreType CB_SHINY_STONE = cobblemon("shiny_stone");
    public static final OreType CB_SUN_STONE = cobblemon("sun_stone");
    public static final OreType CB_THUNDER_STONE = cobblemon("thunder_stone");
    public static final OreType CB_WATER_STONE = cobblemon("water_stone");
    public static final OreType CB_FIRE_STONE = ore("fire_stone", "fire_stone", null, "cobblemon",
            of("cobblemon", "fire_stone_ore"), of("cobblemon", "deepslate_fire_stone_ore"),
            of("cobblemon", "nether_fire_stone_ore"), COBBLEMON_XP, null, false, Set.of());

    // --- Born in Chaos (mod id born_in_chaos_v1, All Rights Reserved; its author's permission, 20 Oct 2026) ---
    // Infected diamond: a trap that looks exactly like diamond ore (its models draw the game's own diamond
    // textures, so its overlay is ours) and drops nothing; breaking it spawns a Diamond Thermite (TrapOreBlock).
    // Only the deepslate form is declared: by the geology rule tuff is the one game rock that keeps diamond.
    // Its feature matches deepslate only, so the tuff variant ADDS ore, behind a switch that is off by
    // default (addsOre). Strength 4.5/3.0, read from InfectedDeepslateDiamondOreBlock.
    public static final OreType INFECTED_DIAMOND = ore("infected_diamond", "diamond", null, "born_in_chaos_v1",
            null, of("born_in_chaos_v1", "infected_deepslate_diamond_ore"), null, NONE, null, false, Set.of())
            .withKey("infected_diamond").withStrength(4.5F, 3.0F);

    // --- Create Propulsion: Simulated (mod id createpropulsion, MIT): platinum, iron convention, no XP. NeoForge at 1.21.1 ---
    public static final OreType CP_PLATINUM = ore(
            "createpropulsion_platinum", "createpropulsion_platinum", null, "createpropulsion",
            of("createpropulsion", "platinum_ore"), of("createpropulsion", "deepslate_platinum_ore"), null,
            NONE, null, false, Set.of());

    // --- Hazen 'N Stuff (mod id hazennstuff, PolyForm Shield 1.0.0): strength 3.0, 2 to 4 XP; zenalite generates in the End only; solar core has no overlay yet, so no variant. NeoForge at 1.21.1 ---
    public static final OreType HNS_CHLOROPHYTE = ore(
            "chlorophyte", "chlorophyte", null, "hazennstuff",
            of("hazennstuff", "chlorophyte_ore"), null, null,
            UniformInt.of(2, 4), null, false, Set.of())
            .withStrength(3.0F, 3.0F, 3.0F, 3.0F);
    public static final OreType HNS_DREADSTONE = ore(
            "dreadstone", "dreadstone", null, "hazennstuff",
            null, of("hazennstuff", "dreadstone_ore"), null,
            UniformInt.of(2, 4), null, false, Set.of())
            .withStrength(3.0F, 3.0F, 3.0F, 3.0F);

    // --- Actually Additions (mod id actuallyadditions, MIT): black quartz, stone's properties at 1.5 hardness, 10.0 blast resistance, no XP. NeoForge at 1.21.1 ---
    public static final OreType AA_BLACK_QUARTZ = ore(
            "black_quartz", "black_quartz", null, "actuallyadditions",
            of("actuallyadditions", "black_quartz_ore"), null, null,
            NONE, null, false, Set.of())
            .withStrength(1.5F, 10.0F, 1.5F, 10.0F);

    // --- Superb Warfare (mod id superbwarfare, GPL-3.0): 3.0 hardness, 5.0 blast resistance (8.0 deep), no XP ---
    public static final OreType SW_GALENA = ore(
            "superbwarfare_galena", "superbwarfare_galena", null, "superbwarfare",
            of("superbwarfare", "galena_ore"), of("superbwarfare", "deepslate_galena_ore"), null,
            NONE, null, false, Set.of())
            .withStrength(3.0F, 5.0F, 3.0F, 8.0F);
    public static final OreType SW_SCHEELITE = ore(
            "superbwarfare_scheelite", "superbwarfare_scheelite", null, "superbwarfare",
            of("superbwarfare", "scheelite_ore"), of("superbwarfare", "deepslate_scheelite_ore"), null,
            NONE, null, false, Set.of())
            .withStrength(3.0F, 5.0F, 3.0F, 8.0F);
    public static final OreType SW_SILVER = ore(
            "superbwarfare_silver", "superbwarfare_silver", null, "superbwarfare",
            of("superbwarfare", "silver_ore"), of("superbwarfare", "deepslate_silver_ore"), null,
            NONE, null, false, Set.of())
            .withStrength(3.0F, 5.0F, 3.0F, 8.0F);

    // --- Epic Paladins (mod id epicpaladins, LGPL-3.0): diamond ore's properties at strength 4.0, 3 to 7 XP; jade is End only (no host) ---
    public static final OreType EP_ARCLIGHT = ore(
            "arclight", "arclight", null, "epicpaladins",
            of("epicpaladins", "arclight_ore"), of("epicpaladins", "deepslate_arclight_ore"), null,
            UniformInt.of(3, 7), null, false, Set.of())
            .withStrength(4.0F, 4.0F, 4.0F, 4.0F);
    public static final OreType EP_BLOODSTONE = ore(
            "epicpaladins_bloodstone", "epicpaladins_bloodstone", null, "epicpaladins",
            of("epicpaladins", "bloodstone_ore"), of("epicpaladins", "deepslate_bloodstone_ore"), null,
            UniformInt.of(3, 7), null, false, Set.of())
            .withStrength(4.0F, 4.0F, 4.0F, 4.0F);
    public static final OreType EP_CRYORIUM = ore(
            "cryorium", "cryorium", null, "epicpaladins",
            of("epicpaladins", "cryorium_ore"), of("epicpaladins", "deepslate_cryorium_ore"), null,
            UniformInt.of(3, 7), null, false, Set.of())
            .withStrength(4.0F, 4.0F, 4.0F, 4.0F);
    public static final OreType EP_MOONLIGHT = ore(
            "moonlight", "moonlight", null, "epicpaladins",
            null, null, of("epicpaladins", "moonlight_ore"),
            UniformInt.of(3, 7), null, false, Set.of())
            .withStrength(4.0F, 4.0F);

    // --- RFTools Base (mod id rftoolsbase, MIT): dimensional shard, 3.0 hardness, 5.0 blast resistance, no XP ---
    public static final OreType RFT_SHARD = ore(
            "dimensional_shard", "dimensional_shard", null, "rftoolsbase",
            of("rftoolsbase", "dimensionalshard_overworld"), null, null,
            NONE, null, false, Set.of())
            .withStrength(3.0F, 5.0F, 3.0F, 5.0F);
    public static final OreType RFT_NETHER_SHARD = ore(
            "nether_dimensional_shard", "dimensional_shard", null, "rftoolsbase",
            null, null, of("rftoolsbase", "dimensionalshard_nether"),
            NONE, null, false, Set.of())
            .withKey("nether_dimensional_shard")
            .withStrength(3.0F, 5.0F);

    public static final List<OreType> ALL =
            List.of(COAL, IRON, COPPER, GOLD, LAPIS, DIAMOND, EMERALD, REDSTONE, NETHER_GOLD, QUARTZ,
                    ZINC,
                    AQUAMARINE, CITRINE, PERIDOT, TOPAZ, NECOIUM, RUBY, SAPPHIRE, AMETRINE,
                    ADAMANTITE, CARMOT, MORKITE, MYTHRIL, PROMETHEUM, RUNITE, UNOBTAINIUM,
                    AQUARIUM, BANGLUM, KYBER, MANGANESE, OSMIUM, PLATINUM, QUADRILLUM, SILVER,
                    STARRITE, TIN, ORICHALCUM,
                    NETHER_BANGLUM, MIDAS_GOLD, PALLADIUM, STORMYX,
                    SG_ALEXANDRITE, SG_AMMOLITE, SG_BLACK_DIAMOND, SG_CARNELIAN, SG_GARNET,
                    SG_HELIODOR, SG_IOLITE, SG_KYANITE, SG_MOLDAVITE, SG_PEARL, SG_ROSE_QUARTZ,
                    SG_RUBY, SG_SAPPHIRE, SG_TANZANITE, SG_TURQUOISE, SG_WHITE_DIAMOND,
                    SG_AQUAMARINE, SG_CITRINE, SG_PERIDOT, SG_TOPAZ, SG_SILVER, SG_CHAOS,
                    DENSE_FLUORITE, DENSE_LEAD, DENSE_OSMIUM, DENSE_TIN, DENSE_URANIUM,
                    URANINITE, URANINITE_POOR, URANINITE_DENSE,
                    TFMG_LEAD, TFMG_LITHIUM, TFMG_NICKEL,
                    ENERGIZED_TIN, GLEAMING, BORT, THORIUM,
                    SG_N_ALEXANDRITE, SG_N_BLACK_DIAMOND, SG_N_CARNELIAN, SG_N_CITRINE,
                    SG_N_IOLITE, SG_N_MOLDAVITE, SG_N_PEARL, SG_N_TANZANITE,
                    IAF_SAPPHIRE, IAF_SILVER,
                    TR_BAUXITE, TR_GALENA, TR_IRIDIUM, TR_LEAD, TR_RUBY, TR_SAPPHIRE, TR_SILVER, TR_TIN,
                    MI_ANTIMONY, MI_BAUXITE, MI_LEAD, MI_LIGNITE_COAL, MI_MONAZITE, MI_NICKEL, MI_SALT,
                    MI_TIN, MI_TUNGSTEN, MI_URANIUM,
                    OCCULTISM_SILVER, YELLORITE, INFERIUM, PROSPERITY,
                    IE_ALUMINUM, IE_LEAD, IE_NICKEL, IE_SILVER, IE_URANIUM,
                    MEK_FLUORITE, MEK_LEAD, MEK_OSMIUM, MEK_TIN, MEK_URANIUM,
                    OREGANIZED_LEAD, OREGANIZED_SILVER,
                    MALUM_SOULSTONE, MALUM_NATURAL_QUARTZ, MALUM_BRILLIANCE, MALUM_BLAZING_QUARTZ,
                    TR_CINNABAR, TR_PYRITE, TR_SPHALERITE, BENITOITE, SG_OPAL,
                    CB_DAWN_STONE, CB_DUSK_STONE, CB_FIRE_STONE, CB_ICE_STONE, CB_LEAF_STONE, CB_MOON_STONE, CB_SHINY_STONE, CB_SUN_STONE, CB_THUNDER_STONE, CB_WATER_STONE,
                    INFECTED_DIAMOND,
                    CP_PLATINUM,
                    HNS_CHLOROPHYTE, HNS_DREADSTONE,
                    AA_BLACK_QUARTZ,
                    SW_GALENA, SW_SCHEELITE, SW_SILVER,
                    EP_ARCLIGHT, EP_BLOODSTONE, EP_CRYORIUM, EP_MOONLIGHT,
                    RFT_SHARD, RFT_NETHER_SHARD);

    private static final Map<String, OreType> BY_KEY = byKey();

    private static Map<String, OreType> byKey() {
        final Map<String, OreType> byKey = new HashMap<>();
        for (OreType ore : ALL) {
            // The generator refuses a duplicate key; this only guards a hand edit it never saw.
            if (byKey.putIfAbsent(ore.key(), ore) != null) {
                Constants.LOG.error("Two ores share the key {}; the second is left out of the modded stones", ore.key());
            }
        }
        return Map.copyOf(byKey);
    }

    /** The ore with this {@link #key()}, or null. */
    public static OreType byKey(String key) {
        return BY_KEY.get(key);
    }

    /**
     * Ores whose variants in the game's own rock ADD ore: their own feature matches no such rock, so the
     * variant is added wherever a vein reaches it, behind the ore's mod's adds-ore switch, off by default.
     */
    private static final Set<String> ADDS_ORE = Set.of("infected_diamond");

    /** Whether this ore's variants in the game's own rock add ore (see ADDS_ORE). */
    public boolean addsOre() {
        return ADDS_ORE.contains(key);
    }

    /** Whether this ore exists in this game: always for vanilla's, only with its mod for a modded one. */
    public boolean isLoaded() {
        return requiredModId == null || Services.PLATFORM.isModLoaded(requiredModId);
    }

    /** Every block that IS this ore before a stone swallows it: stone form, deepslate form, Nether form. */
    public List<ResourceLocation> forms() {
        return Stream.of(stoneOre, deepslateOre, netherOre, endOre).filter(Objects::nonNull).toList();
    }

    /**
     * The form of this ore that the game's own rock of the given host's tier receives, which its variant
     * stands in for; <b>null</b> if that rock takes no such ore, which is what decides the pairing there.
     */
    public ResourceLocation formIn(HostStone host) {
        if (skipHosts.contains(host.name())) {
            return null;
        }
        return switch (host.tier()) {
            case STONE -> stoneOre;
            case DEEPSLATE -> deepslateOre;
            case NETHER -> netherOre;
            // The ore a dripstone shell wraps is whatever generated there, stone or deepslate; the
            // variant stands in for the stone one, whose drops and xp the deepslate one shares.
            case DRIPSTONE -> stoneOre;
            // Only the ores that belong in cinnabar (Vanilla Backport's); each stands in for its stone
            // ore, or for its Nether ore where the mod has no other (Tech Reborn's pyrite and sphalerite).
            case CINNABAR -> cinnabarFamily().contains(this) ? (stoneOre != null ? stoneOre : netherOre) : null;
        };
    }

    /**
     * What gets a cinnabar variant: the ores that really form beside cinnabar in hot spring
     * deposits, gold and silver, iron (as pyrite), the zinc and lead sulfides, and redstone, whose
     * red the game already pairs with cinnabar. 26.2 and up's family, plus the silver, lead and
     * antimony (stibnite) of the mods only this band has. Matched by TYPE, not
     * by name: Nether gold is also named "gold". Built lazily because it names constants declared above.
     */
    private static Set<OreType> cinnabarFamily;

    private static final Object CINNABAR_LOCK = new Object();

    private static Set<OreType> cinnabarFamily() {
        synchronized (CINNABAR_LOCK) {
            if (cinnabarFamily == null) {
                cinnabarFamily = Set.of(GOLD, IRON, REDSTONE, ZINC, TR_GALENA, TR_LEAD, TR_SILVER,
                        OCCULTISM_SILVER, SG_SILVER, TR_PYRITE, TR_SPHALERITE,
                        SILVER, IAF_SILVER, IE_LEAD, IE_SILVER, OREGANIZED_LEAD, OREGANIZED_SILVER,
                        MI_LEAD, MI_ANTIMONY, MEK_LEAD, DENSE_LEAD, TFMG_LEAD, SW_GALENA, SW_SILVER);
            }
            return cinnabarFamily;
        }
    }

    /**
     * Whether this ore does something of its own while it sits in the world or is mined, which its
     * variants hand to the block they stand in for (see HostedOreBlock): Mythic Metals' banglum, which
     * can blow up.
     */
    public boolean keepsBehaviour() {
        return KEEPS_BEHAVIOUR.contains(key);
    }

    private static final Set<String> KEEPS_BEHAVIOUR = Set.of("banglum", "nether_banglum");

    /** Experience for this host, honouring a per-tier override. */
    public IntProvider xpFor(HostStone host) {
        return host.tier() == OreTier.DEEPSLATE && deepslateXp != null ? deepslateXp : xp;
    }
}
