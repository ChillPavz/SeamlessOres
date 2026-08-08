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
        return ResourceLocation.withDefaultNamespace(path);
    }

    private static ResourceLocation of(String namespace, String path) {
        return ResourceLocation.fromNamespaceAndPath(namespace, path);
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

    public static final List<OreType> ALL =
            List.of(COAL, IRON, COPPER, GOLD, LAPIS, DIAMOND, EMERALD, REDSTONE, NETHER_GOLD, QUARTZ,
                    ZINC,
                    AQUAMARINE, CITRINE, PERIDOT, TOPAZ, NECOIUM, RUBY, SAPPHIRE,
                    ADAMANTITE, CARMOT, MORKITE, MYTHRIL, PROMETHEUM, RUNITE, UNOBTAINIUM,
                    AQUARIUM, BANGLUM, KYBER, MANGANESE, OSMIUM, PLATINUM, QUADRILLUM, SILVER,
                    STARRITE, TIN, ORICHALCUM,
                    NETHER_BANGLUM, MIDAS_GOLD, PALLADIUM, STORMYX);

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
