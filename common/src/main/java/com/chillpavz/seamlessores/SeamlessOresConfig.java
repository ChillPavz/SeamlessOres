package com.chillpavz.seamlessores;

import java.util.Set;

/**
 * Plain values holder that worldgen reads.
 *
 * <p>This lives in {@code common} deliberately and holds no library types. Cloth Config's annotated
 * {@code @Config} class cannot live here — loader dependencies are not on common's classpath — so
 * each loader module owns its own annotated copy and pushes the values in here through
 * {@link #apply}. Keep the two loader copies identical.
 *
 * <p><b>Config affects worldgen only, never registration.</b> The registered block set is derived
 * from the loaded mod set so a client and a server always agree; if config could add or remove
 * blocks, a mismatch would kick players on join. Disabling something here only means it never
 * generates — the blocks still exist, in the creative tab and in every tag.
 *
 * <p>Changes take effect the next time a world loads, because the injection runs at server start.
 * Already-generated chunks never change either way.
 */
public final class SeamlessOresConfig {

    private SeamlessOresConfig() {}

    /** Host stones whose variants are switched off, by {@code HostStone.name()}. */
    private static Set<String> disabledHosts = Set.of();

    /**
     * Whether the large copper/iron vein ores are restyled (see {@code VeinOreInjector}).
     * Balance-neutral either way; purely a look.
     */
    public static boolean oreVeins = true;

    /** Whether Create's zinc variants generate. */
    public static boolean createZinc = true;

    /** Whether Mythic Upgrades variants generate. */
    public static boolean mythicUpgrades = true;

    /**
     * Whether a third-party ore's variants may be injected into worldgen.
     *
     * <p>Keyed on mod id rather than a single flag, because the injector used to gate EVERY modded
     * ore on the zinc toggle, which was fine while zinc was the only one and silently wrong the
     * moment a second mod arrived. A mod with no toggle of its own defaults to enabled.
     *
     * <p>This gates GENERATION only. Registration stays derived from the loaded mod set, so a client
     * and a server always register the same blocks whatever their configs say.
     */
    public static boolean isModOreEnabled(String modId) {
        return switch (modId) {
            case "create" -> createZinc;
            case "mythicupgrades" -> mythicUpgrades;
            default -> true;
        };
    }

    /** Create's own value for its zinc feature; {@link #zincVeinSize} of this means "unchanged". */
    public static final int CREATE_ZINC_VEIN_SIZE = 12;

    /**
     * Vein size for Create's zinc feature. {@value #CREATE_ZINC_VEIN_SIZE} is Create's own value, so
     * setting it there is a true no-op and nothing is rebound.
     *
     * <p><b>This is the one setting in the mod that changes ANOTHER MOD'S balance</b>, so it is worth
     * being clear about why it exists. Create's zinc is 8 attempts per chunk at size 12 across
     * y −63..70 with a <i>uniform</i> height distribution — there is no depth at which it peaks, so
     * it is equally common everywhere and finding it never reads as a discovery. Create's own config
     * offers only a single {@code disable} flag that removes all of its worldgen, so there is no
     * gentler dial available anywhere else.
     *
     * <p>Note this is NOT compensating for our zinc variants: those are a pure restyle (Create's
     * feature already targets the same replaceables tags we do), so the amount of zinc with our mod
     * installed is identical to Create alone. Only its appearance is more varied.
     */
    public static int zincVeinSize = CREATE_ZINC_VEIN_SIZE;

    /**
     * Keep the nether variants out of bastion remnants.
     *
     * <p>Bastions are built largely from the two blocks we convert — plain {@code blackstone} appears
     * in 125 of vanilla's 167 bastion structure files and {@code basalt} in 103 — and structures are
     * placed at the {@code surface_structures} step, which runs BEFORE {@code underground_ores}. So
     * without this, an ore feature can turn a bastion's own walls and floors into gold or quartz ore
     * and invite players to mine the structure apart. Vanilla never does this because its nether ore
     * features match {@code netherrack} only.
     */
    public static boolean bastionSafeNether = true;

    /**
     * How many basalt/blackstone vein attempts produce ore: one in this many. 1 converts every
     * vein, which is what shipped in 1.0.0.
     *
     * <p>Basalt deltas use denser features than the rest of the Nether - {@code ore_gold_deltas} is
     * count 20 against {@code ore_gold_nether}'s 10, and quartz is 32 against 16 - and a delta is
     * almost entirely basalt and blackstone, so nearly all 52 attempts per chunk converted. Against
     * ancient debris at 2 attempts of about 5 blocks, that is roughly a hundredfold difference, and
     * it read as scenery rather than as a find.
     *
     * <p>Declining a vein places NOTHING, because vanilla's targets are netherrack-only and a delta
     * has no netherrack. That is precisely vanilla's own behaviour there, so this dial only ever
     * removes ore WE added and never touches netherrack gold or quartz anywhere in the Nether.
     *
     * <p>Deliberately reduces the NUMBER of veins rather than their size: a vein you find is then
     * still worth mining out.
     *
     * <p>Default raised from 5 to 8 after testing. The ore concentrates BELOW the lava sea because
     * that is where a delta is solid: above it the biome is mostly open air and lava, so most vein
     * attempts there place little or nothing, while every attempt in the solid rock below succeeds.
     * Digging is therefore exactly where the density is felt. At 8 a chunk holds roughly 25 gold and
     * 56 quartz against 130 at rarity 5.
     */
    public static int netherOreRarity = 8;

    /**
     * Whether ruby and sapphire generate in basalt deltas.
     *
     * <p><b>This is the only thing in the mod that adds generation with no existing feature to
     * extend.</b> Mythic Upgrades restricts ruby and sapphire ore to its own {@code mythic_rifts}
     * biome, so without this our basalt and blackstone variants have nowhere to appear at all. It is
     * defensible because that mod already puts its ruby and sapphire GEODES in every Nether biome,
     * so this extends its intent rather than contradicting it - but it is still an addition, and it
     * gets its own switch for that reason.
     *
     * <p>Checked inside {@code NetherGemFeature}, not by the injector, because the feature arrives
     * through biome injection which the injector never sees.
     */
    public static boolean netherGems = true;

    /**
     * How much ruby and sapphire a delta chunk gets: {@code 3 x} this many blocks per attempt.
     *
     * <p>1 is ancient debris' own size of 3. {@code scattered_ore} places that many INDIVIDUAL
     * blocks spread around the origin rather than a blob, so raising this makes finds both larger
     * and more frequent, the way stumbling on two or three debris does.
     */
    public static int netherGemDensity = 2;

    /** Called by each loader's config layer whenever the config loads or is saved. */
    public static void apply(Set<String> newDisabledHosts, boolean newOreVeins, boolean newCreateZinc,
                             int newZincVeinSize, boolean newBastionSafeNether,
                             boolean newMythicUpgrades, int newNetherOreRarity, boolean newNetherGems, int newNetherGemDensity) {
        disabledHosts = Set.copyOf(newDisabledHosts);
        oreVeins = newOreVeins;
        createZinc = newCreateZinc;
        zincVeinSize = newZincVeinSize;
        bastionSafeNether = newBastionSafeNether;
        mythicUpgrades = newMythicUpgrades;
        netherOreRarity = newNetherOreRarity;
        netherGems = newNetherGems;
        netherGemDensity = newNetherGemDensity;
        Constants.LOG.debug("Config applied: disabled hosts={}, oreVeins={}, createZinc={}, "
                        + "zincVeinSize={}, bastionSafeNether={}, mythicUpgrades={}",
                disabledHosts, oreVeins, createZinc, zincVeinSize, bastionSafeNether, mythicUpgrades);
    }

    public static boolean isHostEnabled(String hostName) {
        return !disabledHosts.contains(hostName);
    }
}
