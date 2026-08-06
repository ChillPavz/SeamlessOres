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

    /** Called by each loader's config layer whenever the config loads or is saved. */
    public static void apply(Set<String> newDisabledHosts, boolean newOreVeins, boolean newCreateZinc,
                             int newZincVeinSize, boolean newBastionSafeNether,
                             boolean newMythicUpgrades) {
        disabledHosts = Set.copyOf(newDisabledHosts);
        oreVeins = newOreVeins;
        createZinc = newCreateZinc;
        zincVeinSize = newZincVeinSize;
        bastionSafeNether = newBastionSafeNether;
        mythicUpgrades = newMythicUpgrades;
        Constants.LOG.debug("Config applied: disabled hosts={}, oreVeins={}, createZinc={}, "
                        + "zincVeinSize={}, bastionSafeNether={}, mythicUpgrades={}",
                disabledHosts, oreVeins, createZinc, zincVeinSize, bastionSafeNether, mythicUpgrades);
    }

    public static boolean isHostEnabled(String hostName) {
        return !disabledHosts.contains(hostName);
    }
}
