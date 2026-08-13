package com.chillpavz.seamlessores.content;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.UniformInt;

import java.util.List;
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
 * @param name             id suffix, e.g. {@code iron} -> {@code granite_iron_ore}
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
 */
public record OreType(String name, String overlay, String deepslateOverlay, String requiredModId,
                      ResourceLocation stoneOre, ResourceLocation deepslateOre, ResourceLocation netherOre,
                      IntProvider xp, IntProvider deepslateXp, boolean redstoneLike,
                      Set<String> skipHosts) {

    private static final IntProvider NONE = ConstantInt.of(0);

    private static ResourceLocation mc(String path) {
        return new ResourceLocation(path);
    }

    private static ResourceLocation of(String namespace, String path) {
        return new ResourceLocation(namespace, path);
    }

    private static OreType overworld(String name, IntProvider xp) {
        return new OreType(name, name, null, null,
                mc(name + "_ore"), mc("deepslate_" + name + "_ore"), null, xp, null, false, Set.of());
    }

    private static OreType nether(String name, String overlay, String oreId, IntProvider xp) {
        return new OreType(name, overlay, null, null, null, null, mc(oreId), xp, null, false, Set.of());
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
    public static final OreType EMERALD = overworld("emerald", UniformInt.of(3, 7));
    public static final OreType REDSTONE = new OreType("redstone", "redstone", null, null,
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
    public static final OreType ZINC = new OreType("zinc", "zinc", null, "create",
            of("create", "zinc_ore"), of("create", "deepslate_zinc_ore"),
            null, ConstantInt.of(0), null, false, Set.of());

    // --- Mythic Upgrades (mod id mythicupgrades, MIT) -------------------------------------------
    // The five overworld ores target the SAME replaceables tags as vanilla, so injecting them is a
    // pure restyle at zero balance cost. Ruby and sapphire are block_match netherrack only, so their
    // basalt/blackstone variants ADD ore, the same caveat as our nether gold and quartz, and ride
    // the same host toggles and bastion protection. Ametrine and jade are deliberately absent:
    // end_stone only, and the End has no second stone type to be seamless with.
    private static OreType mythic(String name, IntProvider xp) {
        return new OreType(name, name, null, "mythicupgrades",
                of("mythicupgrades", name + "_ore"), of("mythicupgrades", "deepslate_" + name + "_ore"),
                null, xp, null, false, Set.of());
    }

    private static OreType mythicNether(String name, IntProvider xp) {
        return new OreType(name, name, null, "mythicupgrades", null, null,
                of("mythicupgrades", name + "_ore"), xp, null, false, Set.of());
    }

    public static final OreType AQUAMARINE = mythic("aquamarine", UniformInt.of(6, 14));
    public static final OreType CITRINE = mythic("citrine", UniformInt.of(6, 14));
    public static final OreType PERIDOT = mythic("peridot", UniformInt.of(6, 14));
    public static final OreType TOPAZ = mythic("topaz", UniformInt.of(6, 14));
    public static final OreType NECOIUM = mythic("necoium", ConstantInt.of(0));
    public static final OreType RUBY = mythicNether("ruby", UniformInt.of(4, 10));
    public static final OreType SAPPHIRE = mythicNether("sapphire", UniformInt.of(4, 10));

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
        return new OreType(name, name, null, "mythicmetals",
                of("mythicmetals", name + "_ore"), of("mythicmetals", "deepslate_" + name + "_ore"),
                null, xp, deepslateXp, false, Set.of());
    }

    /** Stone tier only: generates in granite, diorite and andesite, never in tuff. */
    private static OreType mmStone(String name) {
        return new OreType(name, name, null, "mythicmetals",
                of("mythicmetals", name + "_ore"), null, null, NONE, null, false, Set.of());
    }

    private static OreType mmNether(String name, String overlay, String oreId, IntProvider xp,
                                    Set<String> skipHosts) {
        return new OreType(name, overlay, null, "mythicmetals", null, null,
                of("mythicmetals", oreId), xp, null, false, skipHosts);
    }

    // Both tiers: granite, diorite, andesite and tuff.
    public static final OreType ADAMANTITE = mmBoth("adamantite", NONE, null);
    public static final OreType CARMOT = mmBoth("carmot", NONE, null);
    public static final OreType MORKITE = mmBoth("morkite", UniformInt.of(1, 2), UniformInt.of(1, 3));
    public static final OreType MYTHRIL = mmBoth("mythril", NONE, null);
    public static final OreType PROMETHEUM = mmBoth("prometheum", NONE, null);
    public static final OreType RUNITE = mmBoth("runite", NONE, null);
    /** Unobtainium's DEEPSLATE ore is animated (4 frames) while its stone one is a still image. */
    public static final OreType UNOBTAINIUM = new OreType("unobtainium", "unobtainium",
            "unobtainium_deepslate", "mythicmetals",
            of("mythicmetals", "unobtainium_ore"), of("mythicmetals", "deepslate_unobtainium_ore"),
            null, NONE, UniformInt.of(4, 7), false, Set.of());

    // Stone tier only.
    public static final OreType AQUARIUM = mmStone("aquarium");
    public static final OreType BANGLUM = mmStone("banglum");
    public static final OreType KYBER = mmStone("kyber");
    public static final OreType MANGANESE = mmStone("manganese");
    public static final OreType OSMIUM = mmStone("osmium");
    public static final OreType PLATINUM = mmStone("platinum");
    public static final OreType QUADRILLUM = mmStone("quadrillum");
    public static final OreType SILVER = mmStone("silver");
    public static final OreType STARRITE = mmStone("starrite");
    public static final OreType TIN = mmStone("tin");
    /**
     * Orichalcum targets both replaceables tags, but Mythic Metals ships its OWN
     * {@code tuff_orichalcum_ore} through an explicit {@code block_match tuff} target that sits
     * ahead of its deepslate tag entry. Tuff is therefore already seamless, and a variant of ours
     * would take that host away from it, because the injector prepends. Stone tier only.
     */
    public static final OreType ORICHALCUM = mmStone("orichalcum");

    // Nether. Like our own gold and quartz these ADD ore, so they ride the basalt and blackstone
    // host toggles and the bastion protection. BANGLUM's nether form reuses the plain name for the
    // same reason NETHER_GOLD does: the host already disambiguates, since the overworld form only
    // pairs with stone-tier hosts and this one only with nether hosts.
    public static final OreType NETHER_BANGLUM =
            mmNether("banglum", "nether_banglum", "nether_banglum_ore", NONE, Set.of());
    public static final OreType MIDAS_GOLD = mmNether("midas_gold", "midas_gold", "midas_gold_ore", NONE, Set.of());
    public static final OreType PALLADIUM = mmNether("palladium", "palladium", "palladium_ore", NONE, Set.of());
    /** Mythic Metals already ships {@code blackstone_stormyx_ore}, so we only add the basalt one. */
    public static final OreType STORMYX =
            mmNether("stormyx", "stormyx", "stormyx_ore", UniformInt.of(2, 4), Set.of("blackstone"));

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
    // only, so they produce basalt_ruby_ore while these produce granite_ruby_ore. Different hosts,
    // no clash. The overlay key follows the name, so the prefixed five need their own art files.
    private static OreType silentGem(String name, IntProvider xp) {
        final String plain = name.startsWith("silents_") ? name.substring("silents_".length()) : name;
        return new OreType(name, name, null, "silentgems",
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
    public static final OreType SG_RUBY = silentGem("ruby", GEM_XP);
    public static final OreType SG_SAPPHIRE = silentGem("sapphire", GEM_XP);
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
    public static final OreType SG_CHAOS = silentGem("chaos", UniformInt.of(3, 7));

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
        return new OreType(name, name, null, modId,
                of(namespace, plain + "_ore"), of(namespace, "deepslate_" + plain + "_ore"),
                null, xp, null, false, Set.of());
    }

    // Dense Mekanism. Its blocks are dense_<ore>_ore / dense_deepslate_<ore>_ore, so the plain name
    // does not follow the usual pattern and each is spelled out.
    private static OreType dmek(String ore, IntProvider xp) {
        return new OreType("dense_" + ore, "dense_" + ore, null, "densemekanism",
                of("densemekanism", "dense_" + ore + "_ore"),
                of("densemekanism", "dense_deepslate_" + ore + "_ore"),
                null, xp, null, false, Set.of());
    }

    public static final OreType DENSE_FLUORITE = dmek("fluorite", UniformInt.of(1, 4));
    public static final OreType DENSE_LEAD = dmek("lead", NONE);
    public static final OreType DENSE_OSMIUM = dmek("osmium", NONE);
    public static final OreType DENSE_TIN = dmek("tin", NONE);
    public static final OreType DENSE_URANIUM = dmek("uranium", NONE);

    // Powah. Three grades of the same ore, named uraninite_ore_poor / _dense in the mod.
    private static OreType powah(String name, String plain) {
        return new OreType(name, name, null, "powah",
                of("powah", plain), of("powah", "deepslate_" + plain), null, NONE, null, false, Set.of());
    }

    public static final OreType URANINITE = powah("uraninite", "uraninite_ore");
    public static final OreType URANINITE_POOR = powah("uraninite_poor", "uraninite_ore_poor");
    public static final OreType URANINITE_DENSE = powah("uraninite_dense", "uraninite_ore_dense");

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
            modded("bort", "silentgear", "silentgear", "bort", UniformInt.of(3, 7));

    /**
     * Create: New Age targets {@code stone_ore_replaceables} only, so thorium generates in granite,
     * diorite and andesite but never tuff. Its magnetite_block is excluded: a whole-block deposit at
     * 15 veins per chunk, not an ore with blobs on a host stone.
     */
    public static final OreType THORIUM = new OreType("thorium", "thorium", null, "create_new_age",
            of("create_new_age", "thorium_ore"), null, null, NONE, null, false, Set.of());

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
        return new OreType(name, name, null, "silentgems", null, null,
                of("silentgems", "nether_" + plain + "_ore"), GEM_XP, null, false, Set.of());
    }

    public static final OreType SG_N_ALEXANDRITE = silentNether("alexandrite", "alexandrite");
    public static final OreType SG_N_BLACK_DIAMOND = silentNether("black_diamond", "black_diamond");
    public static final OreType SG_N_CARNELIAN = silentNether("carnelian", "carnelian");
    public static final OreType SG_N_CITRINE = silentNether("silents_citrine", "citrine");
    public static final OreType SG_N_IOLITE = silentNether("iolite", "iolite");
    public static final OreType SG_N_MOLDAVITE = silentNether("moldavite", "moldavite");
    public static final OreType SG_N_PEARL = silentNether("pearl", "pearl");
    public static final OreType SG_N_TANZANITE = silentNether("tanzanite", "tanzanite");

    public static final List<OreType> ALL =
            List.of(COAL, IRON, COPPER, GOLD, LAPIS, DIAMOND, EMERALD, REDSTONE, NETHER_GOLD, QUARTZ,
                    ZINC,
                    AQUAMARINE, CITRINE, PERIDOT, TOPAZ, NECOIUM, RUBY, SAPPHIRE,
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
                    SG_N_IOLITE, SG_N_MOLDAVITE, SG_N_PEARL, SG_N_TANZANITE);

    /** The id of the ore this type stands in for in the given host, or <b>null</b> if no pairing. */
    public ResourceLocation vanillaFor(HostStone host) {
        if (skipHosts.contains(host.name())) {
            return null;
        }
        return switch (host.tier()) {
            case STONE -> stoneOre;
            case DEEPSLATE -> deepslateOre;
            case NETHER -> netherOre;
        };
    }

    /** Overlay texture key for this host, honouring a per-tier override. */
    public String overlayFor(HostStone host) {
        return host.tier() == OreTier.DEEPSLATE && deepslateOverlay != null ? deepslateOverlay : overlay;
    }

    /** Experience for this host, honouring a per-tier override. */
    public IntProvider xpFor(HostStone host) {
        return host.tier() == OreTier.DEEPSLATE && deepslateXp != null ? deepslateXp : xp;
    }
}
