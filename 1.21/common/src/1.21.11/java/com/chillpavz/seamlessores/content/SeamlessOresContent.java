package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
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
            // A mod's stone exists while the mod that places it is installed.
            if (!host.present()) {
                continue;
            }
            for (OreType ore : host.ores()) {
                // Modded ores exist only when their mod is loaded. This is the settled derived-
                // registration design: both sides have the mod or neither, so the block sets always
                // agree and a mismatch kick is structurally impossible. NEVER gate this on config.
                if (ore.isLoaded()) {
                    variants.add(new OreVariant(host, ore));
                }
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
    public static void registerBlocks(BiConsumer<Identifier, Block> sink) {

        for (OreVariant variant : VARIANTS) {
            final Block block = createBlock(variant);
            BLOCKS.put(variant, block);
            sink.accept(variant.id(), block);
        }
        final Map<Block, OreVariant> reverse = new java.util.IdentityHashMap<>(BLOCKS.size());
        BLOCKS.forEach((variant, block) -> reverse.put(block, variant));
        byBlock = Map.copyOf(reverse);
        Constants.LOG.info("Registered {} ore variants on {} host stones", BLOCKS.size(),
                VARIANTS.stream().map(OreVariant::host).distinct().count());
    }

    /** Must run after {@link #registerBlocks}; each block needs its paired item to exist in-inventory. */
    public static void registerItems(BiConsumer<Identifier, Item> sink) {

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
                    Identifier.fromNamespaceAndPath(Constants.MOD_ID, "ores"));

    public static void registerCreativeTab(BiConsumer<Identifier, CreativeModeTab> sink) {
        final CreativeModeTab tab = CreativeModeTab.builder(CreativeModeTab.Row.TOP, 0)
                .title(Component.translatable("itemGroup." + Constants.MOD_ID + ".ores"))
                .icon(SeamlessOresContent::tabIcon)
                .build();
        sink.accept(TAB.identifier(), tab);
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

    private static Block createBlock(OreVariant variant) {
        // The properties source is always a vanilla block, so it is safe to resolve here (vanilla
        // registers before any mod), and ofLegacyCopy carries its hardness, blast resistance and the
        // correct-tool flag, so mining cannot drift from the ore the variant stands in for. A modded
        // ore's own block may not be registered yet, so it is never read: it takes the vanilla ore
        // convention for its tier, unless its own mod sets a strength, read from that mod's jar.
        final OreType.Strength own = variant.ore().strength();
        final BlockBehaviour.Properties properties = BlockBehaviour.Properties
                .ofLegacyCopy(BuiltInRegistries.BLOCK.getOptional(variant.propertiesSource()).orElseThrow());
        if (own != null) {
            properties.strength(variant.deepslate() ? own.deepHardness() : own.hardness(),
                    variant.deepslate() ? own.deepResistance() : own.resistance());
        }
        // Only the map colour (and, in the block, the sound) follows the HOST stone - vanilla varies
        // those by host rock too (deepslate ores use MapColor.DEEPSLATE), and they have no balance effect.
        properties.mapColor(variant.host().mapColor());

        // From 1.21.2 a block Properties carries an id that MUST be set before construction, or the
        // constructor throws "Block id not set" (an NPE). It matches the registry id used below.
        // Safe here because every block built in this loop is registered immediately, so no
        // unregistered intrusive holder is ever left behind.
        properties.setId(variant.blockKey());

        return variant.ore().redstoneLike()
                ? new HostedRedStoneOreBlock(variant.host(), properties)
                : new HostedOreBlock(variant, variant.ore().xpFor(variant.host()), properties);
    }
}
