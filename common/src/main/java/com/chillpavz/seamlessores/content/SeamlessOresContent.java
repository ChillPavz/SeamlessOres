package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.RedStoneOreBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;

import java.util.ArrayList;
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

    /**
     * The vanilla "Natural Blocks" tab, where players already look for ores.
     * <p>
     * Built by id rather than referenced directly: {@code CreativeModeTabs.NATURAL_BLOCKS} is
     * {@code private}, so it cannot be used from outside vanilla.
     */
    public static final ResourceKey<CreativeModeTab> NATURAL_BLOCKS =
            ResourceKey.create(Registries.CREATIVE_MODE_TAB, ResourceLocation.withDefaultNamespace("natural_blocks"));

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
            // No useBlockDescriptionPrefix()/setId() at 1.21.1: neither exists on Item.Properties
            // yet. A BlockItem already takes its description id from its block, and the id comes
            // from the registry call below rather than from the properties.
            final Item item = new BlockItem(block, new Item.Properties());
            ITEMS.put(variant, item);
            sink.accept(variant.id(), item);
        });
    }

    /** Items in creative-tab order. Empty until {@link #registerItems} has run. */
    public static List<Item> creativeTabItems() {
        return List.copyOf(ITEMS.values());
    }

    private static Block createBlock(OreVariant variant) {

        final BlockBehaviour.Properties properties;
        if (variant.ore().requiredModId() == null) {
            // Vanilla equivalent: safe to resolve here (vanilla registers before any mod), and
            // ofLegacyCopy carries hardness, blast resistance and the correct-tool flag straight off
            // the ore we stand in for, so mining behaviour cannot drift from parity.
            properties = BlockBehaviour.Properties.ofLegacyCopy(
                    BuiltInRegistries.BLOCK.get(variant.vanillaEquivalentId()));
        } else {
            // Modded equivalent: its block may not be registered yet - registration order between
            // unrelated mods is deliberately not relied on. Bake the vanilla ore convention by tier
            // instead (stone ores 3.0/3.0, deepslate ores 4.5/3.0), which Create's zinc follows.
            final float hardness = variant.host().tier() == OreTier.DEEPSLATE ? 4.5F : 3.0F;
            properties = BlockBehaviour.Properties.of()
                    .requiresCorrectToolForDrops()
                    .strength(hardness, 3.0F);
        }
        // Only map colour and sound follow the HOST stone - vanilla varies those by host rock too
        // (deepslate ores use MapColor.DEEPSLATE), and they have no balance effect.
        properties.mapColor(variant.host().mapColor())
                .sound(variant.host().sound());

        return variant.ore().redstoneLike()
                ? new RedStoneOreBlock(properties)
                : new DropExperienceBlock(variant.ore().xp(), properties);
    }
}
