package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.RedStoneOreBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;

/**
 * The declaration table and the block/item factories built from it.
 *
 * <p><b>Why this is derived and never user-configurable.</b> Minecraft freezes its block registry
 * during startup, long before a world or datapack is read, so the set of registered blocks has to be
 * decided up front. If a client and a server disagreed on that set the client would be kicked on
 * join. We therefore derive the set deterministically - both sides compute the same list from the
 * same inputs, so a mismatch is structurally impossible rather than something we validate for.
 *
 * <p>Player-facing configuration belongs on the <i>worldgen</i> side instead: skipping a pairing
 * there means those blocks simply never generate, which is server-side only and cannot desync.
 */
public final class SeamlessOresContent {

    private SeamlessOresContent() {}

    private static final List<OreVariant> VARIANTS = buildVariants();

    /** Populated during registration; keeps the concrete blocks for models, loot and worldgen. */
    private static final Map<OreVariant, Block> BLOCKS = new LinkedHashMap<>();

    /** Populated during registration; iteration order is the creative tab order. */
    private static final Map<OreVariant, Item> ITEMS = new LinkedHashMap<>();

    private static List<OreVariant> buildVariants() {
        final List<OreVariant> variants = new ArrayList<>();
        for (HostStone host : HostStone.ALL) {
            for (OreType ore : OreType.ALL) {
                // A pairing only exists if the ore has a vanilla equivalent for this host's tier -
                // that is what keeps granite quartz and basalt iron from being invented.
                if (ore.vanillaFor(host) == null) {
                    continue;
                }
                // Modded ores exist only when their mod is loaded. This is the settled derived-
                // registration design: both sides have the mod or neither, so the block sets always
                // agree and a mismatch kick is structurally impossible. NEVER gate this on config.
                if (ore.requiredModId() != null && !Services.PLATFORM.isModLoaded(ore.requiredModId())) {
                    continue;
                }
                variants.add(new OreVariant(host, ore));
            }
        }
        return List.copyOf(variants);
    }

    public static List<OreVariant> variants() {
        return VARIANTS;
    }

    public static Map<OreVariant, Block> blocks() {
        return Map.copyOf(BLOCKS);
    }

    /**
     * Reverse of {@link #BLOCKS}, built once at the end of registration.
     *
     * <p>Worldgen asks "is this one of ours, and if so which variant" for every target of every ore
     * feature placement, on several threads at once. Scanning {@link #BLOCKS} for that was fine at
     * 40 blocks and is not at 295, and {@link #blocks()} copies the whole map on each call. Built
     * eagerly rather than lazily so there is no publication race to reason about.
     */
    private static Map<Block, OreVariant> byBlock = Map.of();

    /** The variant a block belongs to, or null if the block is not ours. */
    public static OreVariant variantOf(Block block) {
        return byBlock.get(block);
    }

    /**
     * Builds each block and hands it to the loader to register.
     *
     * <p>Blocks are constructed inside this call rather than in a static initialiser on purpose: a
     * block built with {@code setId} but never actually registered leaves an unregistered intrusive
     * holder, which crashes NeoForge. Building lazily keeps construction and registration together.
     */
    public static void registerBlocks(BiConsumer<ResourceLocation, Block> sink) {

        for (OreVariant variant : VARIANTS) {
            final Block block = createBlock(variant);
            BLOCKS.put(variant, block);
            sink.accept(variant.id(), block);
        }
        final Map<Block, OreVariant> reverse = new java.util.IdentityHashMap<>(BLOCKS.size());
        BLOCKS.forEach((variant, block) -> reverse.put(block, variant));
        byBlock = Map.copyOf(reverse);
        Constants.LOG.info("Registered {} ore variants", BLOCKS.size());
    }

    /** Must run after {@link #registerBlocks}; each block needs its paired item to exist in-inventory. */
    public static void registerItems(BiConsumer<ResourceLocation, Item> sink) {

        // Fail loudly rather than silently registering nothing. NeoForge dispatches RegisterEvent once
        // per registry, so if ITEM were ever handled before BLOCK we would produce zero items, the ores
        // would be unobtainable in creative, and nothing anywhere would report an error.
        if (BLOCKS.isEmpty()) {
            throw new IllegalStateException(
                    "registerItems() ran before registerBlocks() - no BlockItems would have been created");
        }

        BLOCKS.forEach((variant, block) -> {
            // From 1.21.2 an Item Properties also carries an id that must be set before construction,
            // exactly as the block does above. It matches the registry id used below, and the item
            // is registered immediately, so no intrusive holder is left unregistered.
            //
            // useBlockDescriptionPrefix() is REQUIRED alongside it: from 1.21.2 the translation key
            // comes from the Properties and defaults to "item.<namespace>.<path>", where BlockItem
            // used to delegate to its block. Without this the tooltip shows the raw key
            // "item.seamlessores.granite_iron_ore", because our generated lang has "block." keys.
            final Item item = new BlockItem(block, new Item.Properties()
                    .useBlockDescriptionPrefix()
                    .setId(ResourceKey.create(Registries.ITEM, variant.id())));
            ITEMS.put(variant, item);
            sink.accept(variant.id(), item);
        });
    }

    /**
     * Our own creative tab, so 295 ore variants stop burying vanilla's Natural Blocks.
     *
     * <p>Deliberately built with NO {@code displayItems} generator. {@code CreativeModeTab.Output}
     * is protected, so it cannot be populated from outside vanilla; instead each loader's existing
     * "modify tab contents" event fills it, which is the same code that used to target Natural
     * Blocks and is already proven on all three loaders.
     *
     * <p>Icon is basalt gold ore: a block only this mod adds, so the tab is recognisable at a
     * glance and never looks like a vanilla group.
     */
    public static final ResourceKey<CreativeModeTab> TAB =
            ResourceKey.create(Registries.CREATIVE_MODE_TAB,
                    ResourceLocation.fromNamespaceAndPath(Constants.MOD_ID, "ores"));

    public static void registerCreativeTab(BiConsumer<ResourceLocation, CreativeModeTab> sink) {
        final CreativeModeTab tab = CreativeModeTab.builder(CreativeModeTab.Row.TOP, 0)
                .title(Component.translatable("itemGroup." + Constants.MOD_ID + ".ores"))
                .icon(SeamlessOresContent::tabIcon)
                .build();
        sink.accept(TAB.location(), tab);
    }

    private static ItemStack tabIcon() {
        for (Map.Entry<OreVariant, Item> e : ITEMS.entrySet()) {
            final OreVariant v = e.getKey();
            if (v.host() == HostStone.BASALT && v.ore() == OreType.NETHER_GOLD) {
                return new ItemStack(e.getValue());
            }
        }
        // Basalt gold only exists if the basalt host is registered, which it always is, but a tab
        // with no icon would be an invisible failure - fall back to whatever we do have.
        return ITEMS.isEmpty() ? ItemStack.EMPTY : new ItemStack(ITEMS.values().iterator().next());
    }

    /**
     * Items in creative-tab order, <b>grouped by the mod they belong to</b>.
     *
     * <p>Registration order is host-major, which interleaves every mod's ores and makes 295 items
     * unreadable. Here vanilla comes first, then each mod's ores together in one run, so it is
     * obvious at a glance which ore came from where. Sorting only the display order leaves
     * registration untouched.
     */
    public static List<Item> creativeTabItems() {
        final List<Map.Entry<OreVariant, Item>> entries = new ArrayList<>(ITEMS.entrySet());
        final List<OreType> oreOrder = OreType.ALL;
        final List<HostStone> hostOrder = HostStone.ALL;
        entries.sort(Comparator
                // vanilla first (no required mod), then mods alphabetically
                .<Map.Entry<OreVariant, Item>, String>comparing(
                        e -> e.getKey().ore().requiredModId() == null
                                ? "" : e.getKey().ore().requiredModId())
                .thenComparingInt(e -> oreOrder.indexOf(e.getKey().ore()))
                .thenComparingInt(e -> hostOrder.indexOf(e.getKey().host())));
        final List<Item> items = new ArrayList<>(entries.size());
        for (Map.Entry<OreVariant, Item> e : entries) {
            items.add(e.getValue());
        }
        return items;
    }

    /** Hardness and blast resistance on a stone or Nether host, then on a deepslate-tier host. */
    private record Strength(float hardness, float resistance, float deepHardness, float deepResistance) {
    }

    /**
     * Ores whose own mod does not use the vanilla ore strength, with the values that mod sets. Baked
     * at the convention instead, a variant would mine faster than the block it stands in for, or
     * break in explosions the original survives. Every value is read from the mod's own jar:
     * <ul>
     *   <li>Mythic Metals sets a strength per metal, and most of its deepslate ores are tougher
     *       again.</li>
     *   <li>Silent's Gems' Nether gem ores are 4.0 all round; its chaos ore is 5.0, and 6.0 in
     *       deepslate, both with resistance 3.0.</li>
     *   <li>Powah's three uraninite ores are 3.0, 3.2 and 4.0 with resistance 8.0 in stone, while
     *       their deepslate forms follow the convention.</li>
     *   <li>Silent Gear's bort ore is 4.0 with resistance 10.0 in either rock.</li>
     *   <li>Create: New Age's thorium ore is 3.5 all round.</li>
     *   <li>Dense Mekanism copies the rock and then sets its own strength per ore.</li>
     * </ul>
     */
    private static final Map<OreType, Strength> STRENGTH_OVERRIDES = Map.ofEntries(
            strength(OreType.ADAMANTITE, 4.0F, 5.0F, 6.0F, 12.0F),
            strength(OreType.CARMOT, 5.5F, 6.5F, 6.5F, 12.0F),
            strength(OreType.MORKITE, 3.0F, 4.0F, 3.0F, 4.0F),
            strength(OreType.MYTHRIL, 5.0F, 6.0F, 5.5F, 6.5F),
            strength(OreType.PROMETHEUM, 5.0F, 6.0F, 6.0F, 7.0F),
            strength(OreType.RUNITE, 8.0F, 9.0F, 9.0F, 10.0F),
            strength(OreType.UNOBTAINIUM, 16.0F, 13000.0F, 21.0F, 14000.0F),
            strength(OreType.AQUARIUM, 4.0F, 5.0F),
            strength(OreType.BANGLUM, 5.0F, 5.5F),
            strength(OreType.KYBER, 3.0F, 4.0F),
            strength(OreType.MANGANESE, 3.0F, 4.0F),
            strength(OreType.ORICHALCUM, 5.5F, 6.5F),
            strength(OreType.OSMIUM, 4.0F, 5.0F),
            strength(OreType.PLATINUM, 3.5F, 4.5F),
            strength(OreType.QUADRILLUM, 3.5F, 4.5F),
            strength(OreType.SILVER, 2.5F, 3.5F),
            strength(OreType.STARRITE, 5.0F, 6.0F),
            strength(OreType.TIN, 2.0F, 3.0F),
            strength(OreType.NETHER_BANGLUM, 5.0F, 5.5F),
            strength(OreType.MIDAS_GOLD, 4.0F, 5.0F),
            strength(OreType.PALLADIUM, 5.0F, 6.0F),
            strength(OreType.STORMYX, 5.0F, 6.0F),
            strength(OreType.SG_CHAOS, 5.0F, 3.0F, 6.0F, 3.0F),
            strength(OreType.SG_N_ALEXANDRITE, 4.0F, 4.0F),
            strength(OreType.SG_N_BLACK_DIAMOND, 4.0F, 4.0F),
            strength(OreType.SG_N_CARNELIAN, 4.0F, 4.0F),
            strength(OreType.SG_N_CITRINE, 4.0F, 4.0F),
            strength(OreType.SG_N_IOLITE, 4.0F, 4.0F),
            strength(OreType.SG_N_MOLDAVITE, 4.0F, 4.0F),
            strength(OreType.SG_N_PEARL, 4.0F, 4.0F),
            strength(OreType.SG_N_TANZANITE, 4.0F, 4.0F),
            strength(OreType.URANINITE_POOR, 3.0F, 8.0F, 4.5F, 3.0F),
            strength(OreType.URANINITE, 3.2F, 8.0F, 4.5F, 3.0F),
            strength(OreType.URANINITE_DENSE, 4.0F, 8.0F, 4.5F, 3.0F),
            strength(OreType.BORT, 4.0F, 10.0F, 4.0F, 10.0F),
            strength(OreType.THORIUM, 3.5F, 3.5F),
            strength(OreType.DENSE_FLUORITE, 5.0F, 9.0F, 6.0F, 9.0F),
            strength(OreType.DENSE_LEAD, 5.0F, 9.0F, 6.0F, 9.0F),
            strength(OreType.DENSE_OSMIUM, 7.5F, 12.0F, 8.5F, 12.0F),
            strength(OreType.DENSE_TIN, 5.0F, 6.0F, 6.0F, 6.0F),
            strength(OreType.DENSE_URANIUM, 5.0F, 9.0F, 6.0F, 9.0F));

    private static Map.Entry<OreType, Strength> strength(OreType ore, float hardness, float resistance,
                                                         float deepHardness, float deepResistance) {
        return Map.entry(ore, new Strength(hardness, resistance, deepHardness, deepResistance));
    }

    /** An ore with no deepslate form: stone-tier only, or Nether only. */
    private static Map.Entry<OreType, Strength> strength(OreType ore, float hardness, float resistance) {
        return strength(ore, hardness, resistance, hardness, resistance);
    }

    private static Block createBlock(OreVariant variant) {

        final BlockBehaviour.Properties properties;
        if (variant.ore().requiredModId() == null) {
            // Vanilla equivalent: safe to resolve here (vanilla registers before any mod), and
            // ofLegacyCopy carries hardness, blast resistance and the correct-tool flag straight off
            // the ore we stand in for, so mining behaviour cannot drift from parity.
            properties = BlockBehaviour.Properties.ofLegacyCopy(
                    BuiltInRegistries.BLOCK.getValue(variant.vanillaEquivalentId()));
        } else {
            // Modded equivalent: its block may not be registered yet - registration order between
            // unrelated mods is deliberately not relied on. Bake the vanilla ore convention by tier
            // instead (stone ores 3.0/3.0, deepslate ores 4.5/3.0), which Create's zinc follows,
            // unless the mod's own jar says otherwise (STRENGTH_OVERRIDES).
            final boolean deep = variant.host().tier() == OreTier.DEEPSLATE;
            final Strength own = STRENGTH_OVERRIDES.get(variant.ore());
            final float hardness = own == null ? (deep ? 4.5F : 3.0F) : deep ? own.deepHardness() : own.hardness();
            final float resistance = own == null ? 3.0F : deep ? own.deepResistance() : own.resistance();
            properties = BlockBehaviour.Properties.of()
                    .requiresCorrectToolForDrops()
                    .strength(hardness, resistance);
        }
        // Only map colour and sound follow the HOST stone - vanilla varies those by host rock too
        // (deepslate ores use MapColor.DEEPSLATE), and they have no balance effect.
        properties.mapColor(variant.host().mapColor())
                .sound(variant.host().sound());

        // From 1.21.2 a block Properties carries an id that MUST be set before construction, or the
        // constructor throws "Block id not set" (an NPE). It matches the registry id used below.
        // Safe here because every block built in this loop is registered immediately, so no
        // unregistered intrusive holder is ever left behind.
        properties.setId(ResourceKey.create(Registries.BLOCK, variant.id()));

        if (SOURCE_BEHAVIOUR.contains(variant.ore())) {
            return new SourceBehaviourOreBlock(variant.ore().xpFor(variant.host()), properties,
                    variant.vanillaEquivalentId());
        }
        return variant.ore().redstoneLike()
                ? new RedStoneOreBlock(properties)
                : new DropExperienceBlock(variant.ore().xpFor(variant.host()), properties);
    }

    /**
     * Ores that do something of their own when mined, which their variants hand to the source block
     * (see {@link SourceBehaviourOreBlock}): Mythic Metals' banglum, which can blow up.
     */
    private static final java.util.Set<OreType> SOURCE_BEHAVIOUR = java.util.Set.of(
            OreType.BANGLUM, OreType.NETHER_BANGLUM);
}
