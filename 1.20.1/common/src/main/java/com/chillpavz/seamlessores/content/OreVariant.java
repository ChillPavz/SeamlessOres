package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;

/** One host stone x ore pairing, e.g. granite + iron -> {@code seamlessores:granite_iron_ore}. */
public record OreVariant(HostStone host, OreType ore) {

    /** e.g. {@code granite_iron_ore}. Mirrors vanilla's own {@code deepslate_iron_ore} convention. */
    public String path() {
        return host.name() + "_" + ore.name() + "_ore";
    }

    public ResourceLocation id() {
        return new ResourceLocation(Constants.MOD_ID, path());
    }

    public ResourceKey<Block> blockKey() {
        return ResourceKey.create(Registries.BLOCK, id());
    }

    public ResourceKey<Item> itemKey() {
        return ResourceKey.create(Registries.ITEM, id());
    }

    /** The id of the ore this variant stands in for. Never null for a variant that exists. */
    public ResourceLocation vanillaEquivalentId() {
        final ResourceLocation id = ore.vanillaFor(host);
        if (id == null) {
            throw new IllegalStateException("No vanilla equivalent for " + path());
        }
        return id;
    }

    /**
     * The block this variant stands in for, resolved from the live registry.
     *
     * <p>Only safe once every mod has registered — i.e. at worldgen injection time (server start),
     * never during our own registration, where a modded id (Create's zinc) may not exist yet.
     * Returns null if the id does not resolve, which for a gated variant cannot happen: the variant
     * is only built when its mod is loaded.
     */
    public Block vanillaEquivalent() {
        final Block block = BuiltInRegistries.BLOCK.getOptional(vanillaEquivalentId()).orElse(null);
        if (block == null) {
            Constants.LOG.warn("{} does not resolve - {} will not be injected", vanillaEquivalentId(), path());
        }
        return block;
    }
}
