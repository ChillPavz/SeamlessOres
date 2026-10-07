package com.chillpavz.seamlessores.matrix.content;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;

import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;

/**
 * The variants, and the block and item factories built from them.
 *
 * <p><b>The set is derived from the installed mods, never from config.</b> A variant exists when the
 * mod that places its stone is loaded, and, for a modded ore, the ore's mod too. Client and server compute the same list from the same mod set, so they
 * cannot disagree about which blocks exist. Anything a player may switch off belongs to worldgen.
 */
public final class MatrixContent {

    private MatrixContent() {}

    private static final List<Variant> VARIANTS = buildVariants();

    private static final Map<Variant, Block> BLOCKS = new LinkedHashMap<>();
    private static final Map<Variant, Item> ITEMS = new LinkedHashMap<>();

    /**
     * The Modded Stones tab. Seamless Ores' own tab is the Vanilla Stones one, and our variants on
     * vanilla rock (calcite, smooth basalt) go there too.
     */
    public static final ResourceKey<CreativeModeTab> TAB = ResourceKey.create(Registries.CREATIVE_MODE_TAB,
            Identifier.fromNamespaceAndPath(Constants.MOD_ID, "modded_stones"));

    private static List<Variant> buildVariants() {
        final List<Variant> variants = new ArrayList<>();
        for (HostStone host : HostStone.ALL) {
            if (!host.isLoaded()) {
                continue;
            }
            for (OreKind ore : host.ores()) {
                // Zinc in limestone needs Create as well as Blockus; tin in it Tech Reborn.
                if (ore.isLoaded()) {
                    variants.add(new Variant(host, ore));
                }
            }
        }
        return List.copyOf(variants);
    }

    public static List<Variant> variants() {
        return VARIANTS;
    }

    /** Registered blocks, in registration order. Empty until registration has run. */
    public static Map<Variant, Block> blocks() {
        return Collections.unmodifiableMap(BLOCKS);
    }

    /**
     * Builds each block and hands it to the loader to register. Built here rather than in a static
     * initialiser: a block given an id but never registered leaves an unregistered intrusive holder,
     * which crashes NeoForge.
     */
    public static void registerBlocks(BiConsumer<Identifier, Block> sink) {
        for (Variant variant : VARIANTS) {
            if (variant.borrowed()) {
                // Seamless Ores registered this one already, from the same mod set, just before us.
                final Block block = SeamlessOresContent.registeredBlock(variant.id());
                if (block == null) {
                    Constants.LOG.warn("{} is not registered, so ore swallowed by {} keeps its own look",
                            variant.id(), variant.host());
                } else {
                    BLOCKS.put(variant, block);
                }
                continue;
            }
            final Block block = createBlock(variant);
            BLOCKS.put(variant, block);
            sink.accept(variant.id(), block);
        }
        Constants.LOG.info("Registered {} ore variants on {} host stones", BLOCKS.size(),
                VARIANTS.stream().map(Variant::host).distinct().count());
    }

    public static void registerItems(BiConsumer<Identifier, Item> sink) {
        // NeoForge fires RegisterEvent once per registry. If ITEM ever came before BLOCK this would
        // register nothing, in silence, so it fails loudly instead.
        if (BLOCKS.isEmpty() && !VARIANTS.isEmpty()) {
            throw new IllegalStateException("registerItems() ran before registerBlocks()");
        }
        BLOCKS.forEach((variant, block) -> {
            if (variant.borrowed()) {
                return;   // Seamless Ores registered its item, and shows it in its own tab
            }
            // useBlockDescriptionPrefix: from 1.21.2 the item's translation key comes from its
            // Properties, and without it the tooltip shows the raw item key.
            final Item item = new BlockItem(block, new Item.Properties()
                    .useBlockDescriptionPrefix()
                    .setId(ResourceKey.create(Registries.ITEM, variant.id())));
            ITEMS.put(variant, item);
            sink.accept(variant.id(), item);
        });
    }

    /**
     * The Modded Stones tab. Registered only when a modded stone is installed, which is decided by the
     * mod set alone, so client and server agree.
     */
    public static void registerCreativeTab(BiConsumer<Identifier, CreativeModeTab> sink) {
        if (VARIANTS.stream().noneMatch(v -> !v.host().vanilla())) {
            return;
        }
        final CreativeModeTab tab = CreativeModeTab.builder(CreativeModeTab.Row.TOP, 0)
                .title(Component.translatable("itemGroup." + Constants.MOD_ID + ".modded_stones"))
                .icon(() -> {
                    final List<Item> items = creativeTabItems(false);
                    return items.isEmpty() ? ItemStack.EMPTY : new ItemStack(items.getFirst());
                })
                .build();
        sink.accept(TAB.identifier(), tab);
    }

    /** Our items whose host is vanilla rock ({@code true}, for the Vanilla Stones tab) or a mod's. */
    public static List<Item> creativeTabItems(boolean vanillaHosts) {
        final List<Item> items = new ArrayList<>();
        ITEMS.forEach((variant, item) -> {
            if (variant.host().vanilla() == vanillaHosts) {
                items.add(item);
            }
        });
        return items;
    }

    /** Our blocks as an identity set, for "is this one of ours" checks during injection. */
    public static Map<Block, Variant> byBlock() {
        final Map<Block, Variant> reverse = new IdentityHashMap<>(BLOCKS.size());
        BLOCKS.forEach((variant, block) -> reverse.put(block, variant));
        return reverse;
    }

    private static Block createBlock(Variant variant) {
        // The strength source is always vanilla, so it is safe to resolve here (vanilla registers before
        // any mod), and ofLegacyCopy carries its hardness, blast resistance and tool requirement, so
        // mining cannot drift from the ore it replaces. Zinc copies gold ore, as Create's own zinc ore
        // does. A modded ore's own block may not be registered yet, so it is never read: a modded ore
        // takes the vanilla ore convention for its tier, which a stone or deepslate iron ore carries,
        // unless its mod sets its own strength, which Seamless Ores read from that mod's jar. Only the
        // map colour follows the stone.
        final HostStone.Strength tier = variant.host().strength();
        final BlockBehaviour.Properties properties = BlockBehaviour.Properties
                .ofLegacyCopy(BuiltInRegistries.BLOCK.getValue(variant.strengthSource()))
                .mapColor(variant.host().mapColor());
        final float[] own = variant.ore().ownStrength(tier);
        if (own != null) {
            properties.strength(own[0], own[1]);
        }
        properties.setId(ResourceKey.create(Registries.BLOCK, variant.id()));
        return variant.ore().redstoneLike()
                ? new HostedRedStoneOreBlock(variant.host(), properties)
                : new HostedOreBlock(variant.host(), variant.ore().xp(tier), properties);
    }
}
