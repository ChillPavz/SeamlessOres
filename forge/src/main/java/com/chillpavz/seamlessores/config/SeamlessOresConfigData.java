package com.chillpavz.seamlessores.config;

import java.util.HashSet;
import java.util.Set;

import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraftforge.common.ForgeConfigSpec;

/**
 * Forge config model.
 *
 * <p>Cloth Config has no Forge build past 1.21.3, so unlike the Fabric and NeoForge modules this
 * one is built on Forge's own {@link ForgeConfigSpec} (classic Forge kept that name; only NeoForge
 * renamed it to {@code ModConfigSpec}). Same fifteen options, same bounds and same four categories
 * as the Cloth screen, pushed into the shared {@link SeamlessOresConfig} by {@link #applyToRuntime}.
 *
 * <p>Unlike Ore Detector Reborn, nothing here is needed before registration: every value gates
 * worldgen, which runs at server start, long after a COMMON config has loaded. So Forge's missing
 * {@code STARTUP} config type costs us nothing on this mod and there is no early file-read hack.
 *
 * <p><b>Keep the option names, defaults and bounds identical to the two Cloth copies</b>
 * ({@code fabric/}, {@code neoforge/}) - all three write into the same holder and the store page
 * documents one set of numbers.
 */
public final class SeamlessOresConfigData {

    public static final ForgeConfigSpec SPEC;

    // --- overworld ---------------------------------------------------------------------------
    static final ForgeConfigSpec.BooleanValue GRANITE;
    static final ForgeConfigSpec.BooleanValue DIORITE;
    static final ForgeConfigSpec.BooleanValue ANDESITE;
    static final ForgeConfigSpec.BooleanValue TUFF;
    static final ForgeConfigSpec.BooleanValue ORE_VEINS;

    // --- nether ------------------------------------------------------------------------------
    static final ForgeConfigSpec.BooleanValue BASALT;
    static final ForgeConfigSpec.BooleanValue BLACKSTONE;
    static final ForgeConfigSpec.BooleanValue BASTION_SAFE_NETHER;
    static final ForgeConfigSpec.IntValue NETHER_ORE_RARITY;
    static final ForgeConfigSpec.IntValue NETHER_VEIN_SIZE;

    // --- create ------------------------------------------------------------------------------
    static final ForgeConfigSpec.BooleanValue CREATE_ZINC;
    static final ForgeConfigSpec.IntValue ZINC_VEIN_SIZE;

    // --- mythic upgrades ---------------------------------------------------------------------
    static final ForgeConfigSpec.BooleanValue MYTHIC_UPGRADES;
    static final ForgeConfigSpec.BooleanValue NETHER_GEMS;
    static final ForgeConfigSpec.IntValue NETHER_GEM_SIZE;

    public static final int NETHER_ORE_RARITY_MIN = 1;
    public static final int NETHER_ORE_RARITY_MAX = 10;
    public static final int NETHER_ORE_RARITY_DEFAULT = 2;
    public static final int NETHER_VEIN_SIZE_MIN = 25;
    public static final int NETHER_VEIN_SIZE_MAX = 100;
    public static final int NETHER_VEIN_SIZE_DEFAULT = 80;
    public static final int ZINC_VEIN_SIZE_MIN = 6;
    public static final int ZINC_VEIN_SIZE_MAX = 12;
    public static final int ZINC_VEIN_SIZE_DEFAULT = 10;
    public static final int NETHER_GEM_SIZE_MIN = 3;
    public static final int NETHER_GEM_SIZE_MAX = 6;
    public static final int NETHER_GEM_SIZE_DEFAULT = 4;

    static {
        ForgeConfigSpec.Builder builder = new ForgeConfigSpec.Builder();
        builder.comment("Seamless Ores",
                "Everything here gates WORLDGEN, never registration - the blocks always exist, in the",
                "creative tab and in every tag, so a client and a server can never disagree about what",
                "is registered. A change takes effect the next time a world is loaded; already-generated",
                "chunks keep whatever they got.");

        builder.comment("Host stones that already contain ore in vanilla. Purely a restyle: the amount",
                "of ore in the world is unchanged.").push("overworld");
        GRANITE = builder
                .comment("Generate granite-backed ore where granite would already contain ore.")
                .define("granite", true);
        DIORITE = builder
                .comment("Generate diorite-backed ore where diorite would already contain ore.")
                .define("diorite", true);
        ANDESITE = builder
                .comment("Generate andesite-backed ore where andesite would already contain ore.")
                .define("andesite", true);
        TUFF = builder
                .comment("Generate tuff-backed ore instead of the deepslate-textured ore vanilla puts in tuff.")
                .define("tuff", true);
        ORE_VEINS = builder
                .comment("The big copper and iron veins are packed with granite and tuff. This makes their",
                        "ore match that filler. Cosmetic only - the amount of ore is identical either way.")
                .define("oreVeins", true);
        builder.pop();

        builder.comment("Basalt and blackstone hold NO gold or quartz in vanilla, so these two host",
                "stones ADD ore rather than restyling it. Turn both off to restore vanilla generation",
                "exactly.").push("nether");
        BASALT = builder
                .comment("Puts gold and quartz in basalt. Vanilla generates NEITHER there, so this ADDS",
                        "ore - most noticeably in basalt deltas. Turn off for vanilla amounts.")
                .define("basalt", true);
        BLACKSTONE = builder
                .comment("Puts gold and quartz in blackstone. Vanilla generates NEITHER there, so this",
                        "ADDS ore. Turn off for vanilla amounts.")
                .define("blackstone", true);
        BASTION_SAFE_NETHER = builder
                .comment("Keep basalt and blackstone ore out of bastion remnants. Bastions are built from",
                        "those blocks, so without this their walls can turn into ore and invite you to",
                        "mine the structure apart.")
                .define("bastionSafeNether", true);
        NETHER_ORE_RARITY = builder
                .comment("One in this many basalt or blackstone veins becomes ore. 1 converts every vein.",
                        "Basalt deltas run twice the usual gold and quartz, and are almost all basalt, so",
                        "without this nearly every vein there converted. Vanilla ore is unaffected.")
                .defineInRange("netherOreRarity", NETHER_ORE_RARITY_DEFAULT,
                        NETHER_ORE_RARITY_MIN, NETHER_ORE_RARITY_MAX);
        NETHER_VEIN_SIZE = builder
                .comment("How big each nether gold or quartz vein is, as a percent of vanilla. 100 is",
                        "vanilla. Below its thin basalt crust a delta is netherrack, so some of what you",
                        "dig through there is vanilla's own ore. Unlike the rarity setting, this affects",
                        "that too.")
                .defineInRange("netherVeinSize", NETHER_VEIN_SIZE_DEFAULT,
                        NETHER_VEIN_SIZE_MIN, NETHER_VEIN_SIZE_MAX);
        builder.pop();

        builder.comment("Create is Fabric-only at 1.21.11 (it ships as Create Fly), so these two do",
                "nothing on this loader today. They are kept so the config file matches the other",
                "loaders and lights up on its own if Create ever ships for Forge.").push("create");
        CREATE_ZINC = builder
                .comment("Generate host-matched zinc ore. Does nothing unless Create is installed.")
                .define("createZinc", true);
        ZINC_VEIN_SIZE = builder
                .comment("How large each zinc vein is. Create's own value is 12; lower means less zinc.",
                        "Create spreads zinc evenly from Y -63 to 70, so it is equally common everywhere.",
                        "Set this to 12 to leave Create's generation completely untouched.")
                .defineInRange("zincVeinSize", ZINC_VEIN_SIZE_DEFAULT,
                        ZINC_VEIN_SIZE_MIN, ZINC_VEIN_SIZE_MAX);
        builder.pop();

        builder.comment("Mythic Upgrades has no 1.21.11 build at all, so these do nothing on this",
                "version. Kept for the same reason as the Create section.").push("mythic_upgrades");
        MYTHIC_UPGRADES = builder
                .comment("Generate host-matched Mythic Upgrades ore. Does nothing unless the mod is installed.")
                .define("mythicUpgrades", true);
        NETHER_GEMS = builder
                .comment("Scatter Mythic Upgrades ruby and sapphire through basalt deltas, as rarely as",
                        "ancient debris. Ruby sits around Y 28, sapphire around Y 12, never surface exposed.")
                .define("netherGems", true);
        NETHER_GEM_SIZE = builder
                .comment("How many gems each find holds. 3 matches ancient debris exactly, 6 is double.",
                        "Higher values make finds both larger and easier to come across.")
                .defineInRange("netherGemSize", NETHER_GEM_SIZE_DEFAULT,
                        NETHER_GEM_SIZE_MIN, NETHER_GEM_SIZE_MAX);
        builder.pop();

        SPEC = builder.build();
    }

    private SeamlessOresConfigData() {
    }

    /** Persists the config file. Saving any one value writes the whole spec, so one call is enough. */
    public static void save() {
        GRANITE.save();
    }

    /** Copies the spec's values into the loader-agnostic holder that worldgen reads. */
    public static void applyToRuntime() {
        final Set<String> disabled = new HashSet<>();
        if (!GRANITE.get()) disabled.add("granite");
        if (!DIORITE.get()) disabled.add("diorite");
        if (!ANDESITE.get()) disabled.add("andesite");
        if (!TUFF.get()) disabled.add("tuff");
        if (!BASALT.get()) disabled.add("basalt");
        if (!BLACKSTONE.get()) disabled.add("blackstone");
        SeamlessOresConfig.apply(disabled, ORE_VEINS.get(), CREATE_ZINC.get(), ZINC_VEIN_SIZE.get(),
                BASTION_SAFE_NETHER.get(), MYTHIC_UPGRADES.get(), NETHER_ORE_RARITY.get(),
                NETHER_GEMS.get(), NETHER_GEM_SIZE.get(), NETHER_VEIN_SIZE.get());
    }
}
