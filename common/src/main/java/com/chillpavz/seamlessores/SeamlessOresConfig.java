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

    /**
     * Ordinary overworld copper, as a percentage of vanilla's vein count.
     *
     * <p>Vanilla runs {@code ore_copper} at 16 attempts per chunk of size 10, in every biome. This
     * scales the COUNT rather than the size, on the same reasoning as {@link #netherOreRarity}: a
     * vein you find should still be worth mining out, so it is better to have fewer of them than to
     * make every one small.
     *
     * <p><b>This changes VANILLA generation and is not a restyle</b> - the first setting in the mod
     * that touches overworld ore amounts, so it has to be disclosed on the store page exactly like
     * {@link #netherVeinSize}. 100 leaves vanilla completely untouched.
     */
    public static int overworldCopper = 75;

    /**
     * Dripstone-cave copper, as a percentage of vanilla's vein count.
     *
     * <p>Separate from {@link #overworldCopper} because it is a different feature and a much bigger
     * outlier. {@code ore_copper_large} is 16 attempts per chunk at size 20 and appears in
     * <b>dripstone caves and nowhere else</b> - one biome of 64 - on top of the ordinary copper
     * every biome gets. That is roughly three times the copper of anywhere else, which is why
     * dripstone caves read as solid copper.
     *
     * <p>0 removes the large veins entirely, leaving dripstone caves with exactly the same copper as
     * every other biome. 100 leaves vanilla untouched.
     */
    public static int dripstoneCopper = 25;

    /** Whether Create's zinc variants generate. */
    public static boolean createZinc = true;

    /** Whether Mythic Upgrades variants generate. */
    public static boolean mythicUpgrades = true;

    /** Whether Mythic Metals variants generate. */
    public static boolean mythicMetals = true;

    /** Whether Silent's Gems OVERWORLD variants generate. Balance-neutral: a pure restyle. */
    public static boolean silentGems = true;

    /**
     * Whether Silent's Gems NETHER variants generate — a separate switch from {@link #silentGems}
     * because the two are not the same kind of change.
     *
     * <p>Silent's Gems targets {@code c:netherracks} only, so its eight generating nether gems never
     * appear in basalt or blackstone in that mod alone. Our variants therefore <b>ADD</b> ore there,
     * exactly as our own gold and quartz do, while the overworld gems are a pure restyle of ore that
     * already generates. Two different balance stories deserve two different switches.
     */
    public static boolean silentGemsNether = true;

    /** Whether Dense Mekanism variants generate. Pure restyle. */
    public static boolean denseMekanism = true;

    /** Whether Powah variants generate. Pure restyle. */
    public static boolean powah = true;

    /** Whether Create: The Factory Must Grow variants generate. Pure restyle. */
    public static boolean tfmg = true;

    /** Whether Energized Power variants generate. Pure restyle. */
    public static boolean energizedPower = true;

    /** Whether Exp Ores variants generate. Pure restyle, in the Nether too. */
    public static boolean expOres = true;

    /** Whether Ice and Fire variants generate. Pure restyle. */
    public static boolean iceAndFire = true;

    /** Whether Things variants generate. Pure restyle. */
    public static boolean things = true;

    /** Whether Silent Gear variants generate. Pure restyle. */
    public static boolean silentGear = true;

    /** Whether Create: New Age variants generate. Pure restyle. */
    public static boolean createNewAge = true;

    /**
     * Whether a third-party ore's variants may be injected into worldgen.
     *
     * <p>Keyed on mod id rather than a single flag, because the injector used to gate EVERY modded
     * ore on the zinc toggle, which was fine while zinc was the only one and silently wrong the
     * moment a second mod arrived. A mod with no toggle of its own defaults to enabled.
     *
     * <p><b>{@code netherHost} exists for Silent's Gems alone</b>, which is the one mod whose
     * overworld and nether variants differ in kind: the overworld ones restyle ore that already
     * generates, the nether ones add ore that does not. Every other mod ignores the flag. Passing it
     * rather than splitting the mod id keeps {@code OreType} free of a distinction only the config
     * cares about.
     *
     * <p>This gates GENERATION only. Registration stays derived from the loaded mod set, so a client
     * and a server always register the same blocks whatever their configs say.
     */
    public static boolean isModOreEnabled(String modId, boolean netherHost) {
        return switch (modId) {
            case "create" -> createZinc;
            case "mythicupgrades" -> mythicUpgrades;
            case "mythicmetals" -> mythicMetals;
            case "silentgems" -> netherHost ? silentGemsNether : silentGems;
            case "densemekanism" -> denseMekanism;
            case "powah" -> powah;
            case "tfmg" -> tfmg;
            case "energizedpower" -> energizedPower;
            case "expores" -> expOres;
            case "iceandfire" -> iceAndFire;
            case "things" -> things;
            case "silentgear" -> silentGear;
            case "create_new_age" -> createNewAge;
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
    public static int zincVeinSize = 10;

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
     * Vein size for the nether ore features we patch, as a percentage of vanilla's own value.
     *
     * <p>Separate from {@link #netherOreRarity}, which controls HOW MANY veins convert. This one
     * controls how big each one is: gold is size 10 and quartz 14 in vanilla, so 60 gives 6 and 8.
     *
     * <p><b>Unlike the rarity dial, this one does touch vanilla ore.</b> A delta is netherrack below
     * its thin basalt crust, so a good share of what you dig through down there is vanilla's own
     * netherrack gold and quartz, and size is a property of the whole feature rather than of our
     * added targets. 100 leaves everything exactly as vanilla.
     */
    public static int netherVeinSize = 80;

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
    public static int netherOreRarity = 2;

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
     * How many ruby or sapphire blocks {@code scattered_ore} scatters per attempt.
     *
     * <p>Expressed as the REAL size rather than a multiplier, so the numbers mean something: 3 is
     * ancient debris' own value exactly, and 6 is double it. Tested at 6 and it was far too much,
     * so the default sits just above debris parity — 4 reads as "a little better than debris",
     * which is what a rarer, deeper gem should feel like.
     */
    public static int netherGemSize = 4;

    /**
     * {@link #netherOreRarity}, but for Silent's Gems' nether gems.
     *
     * <p>They add ore on exactly the same terms as our gold and quartz, so they get the same dial —
     * but a separate copy of it, because eight gems and two common ores are not worth balancing
     * together. Defaults to the same value as the global one so the shipped behaviour is consistent
     * rather than arbitrary.
     */
    public static int silentGemsNetherRarity = 2;

    /** {@link #netherVeinSize}, but for Silent's Gems' nether gems. See {@link #silentGemsNetherRarity}. */
    public static int silentGemsNetherVeinSize = 80;

    /**
     * Which rarity dial governs a nether variant, by the mod that owns the ore.
     *
     * @param modId owning mod id, or {@code null} for a vanilla ore (gold and quartz)
     * @return one in this many veins converts; 1 means every vein, i.e. no thinning
     */
    public static int netherRarityFor(String modId) {
        if (modId == null) {
            return netherOreRarity;                 // our own gold and quartz
        }
        if ("silentgems".equals(modId)) {
            return silentGemsNetherRarity;
        }
        // Everything else - Mythic Upgrades' ruby and sapphire, Mythic Metals' four - is exempt.
        // Ruby and sapphire already have their own far rarer placement through NetherGemFeature, and
        // stacking a second thinning on top of that puts them near one in a hundred chunks.
        return 1;
    }

    /** Which vein-size dial governs a nether feature, as a percentage of the feature's own size. */
    public static int netherVeinSizeFor(String modId) {
        return "silentgems".equals(modId) ? silentGemsNetherVeinSize : netherVeinSize;
    }

    /**
     * Every value a loader's config layer pushes in, by NAME.
     *
     * <p>This replaced a positional {@code apply(...)}. With eleven settings that was merely ugly;
     * at twenty-four it is a bug waiting to happen, because any two adjacent parameters of the same
     * type can be swapped and still compile — and the symptom would be a silently wrong worldgen
     * dial, which is the hardest class of bug to notice in this mod.
     *
     * <p>The host booleans live here rather than being turned into a {@code Set} by each loader, so
     * that derivation exists once instead of being copy-pasted into all three modules.
     */
    public static final class Values {
        public boolean granite = true;
        public boolean diorite = true;
        public boolean andesite = true;
        public boolean tuff = true;
        public boolean basalt = true;
        public boolean blackstone = true;
        public boolean oreVeins = true;
        public boolean bastionSafeNether = true;
        public int netherOreRarity = 2;
        public int netherVeinSize = 80;
        public boolean netherGems = true;
        public int netherGemSize = 4;
        public int overworldCopper = 75;
        public int dripstoneCopper = 25;
        public boolean createZinc = true;
        public int zincVeinSize = 10;
        public boolean mythicUpgrades = true;
        public boolean mythicMetals = true;
        public boolean silentGems = true;
        public boolean silentGemsNether = true;
        public int silentGemsNetherRarity = 2;
        public int silentGemsNetherVeinSize = 80;
        public boolean denseMekanism = true;
        public boolean powah = true;
        public boolean tfmg = true;
        public boolean energizedPower = true;
        public boolean expOres = true;
        public boolean iceAndFire = true;
        public boolean things = true;
        public boolean silentGear = true;
        public boolean createNewAge = true;
    }

    /** Called by each loader's config layer whenever the config loads or is saved. */
    public static void apply(Values values) {
        final Set<String> disabled = new java.util.HashSet<>();
        if (!values.granite) disabled.add("granite");
        if (!values.diorite) disabled.add("diorite");
        if (!values.andesite) disabled.add("andesite");
        if (!values.tuff) disabled.add("tuff");
        if (!values.basalt) disabled.add("basalt");
        if (!values.blackstone) disabled.add("blackstone");
        disabledHosts = Set.copyOf(disabled);

        oreVeins = values.oreVeins;
        bastionSafeNether = values.bastionSafeNether;
        netherOreRarity = values.netherOreRarity;
        netherVeinSize = values.netherVeinSize;
        netherGems = values.netherGems;
        netherGemSize = values.netherGemSize;
        overworldCopper = values.overworldCopper;
        dripstoneCopper = values.dripstoneCopper;
        createZinc = values.createZinc;
        zincVeinSize = values.zincVeinSize;
        mythicUpgrades = values.mythicUpgrades;
        mythicMetals = values.mythicMetals;
        silentGems = values.silentGems;
        silentGemsNether = values.silentGemsNether;
        silentGemsNetherRarity = values.silentGemsNetherRarity;
        silentGemsNetherVeinSize = values.silentGemsNetherVeinSize;
        denseMekanism = values.denseMekanism;
        powah = values.powah;
        tfmg = values.tfmg;
        energizedPower = values.energizedPower;
        expOres = values.expOres;
        iceAndFire = values.iceAndFire;
        things = values.things;
        silentGear = values.silentGear;
        createNewAge = values.createNewAge;

        Constants.LOG.debug("Config applied: disabled hosts={}, oreVeins={}, createZinc={}, "
                        + "zincVeinSize={}, bastionSafeNether={}, mythicUpgrades={}, mythicMetals={}, "
                        + "silentGems={}/{} (rarity {}, vein {}%)",
                disabledHosts, oreVeins, createZinc, zincVeinSize, bastionSafeNether, mythicUpgrades,
                mythicMetals, silentGems, silentGemsNether, silentGemsNetherRarity,
                silentGemsNetherVeinSize);
    }

    public static boolean isHostEnabled(String hostName) {
        return !disabledHosts.contains(hostName);
    }
}
