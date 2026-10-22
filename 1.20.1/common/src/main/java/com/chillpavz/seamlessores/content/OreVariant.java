package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;

/** One host stone x ore pairing, e.g. granite + iron -> {@code seamlessores:granite_iron_ore}. */
public record OreVariant(HostStone host, OreType ore) {

    /**
     * e.g. {@code granite_iron_ore}, {@code create_limestone_techreborn_silver_ore}: the id rule of 6.0.0
     * (stone, then ore, each with its mod in front unless it is the game's), read from the jar's ids.json
     * ({@link VariantIds}), which the generator writes. Ids earlier releases shipped are aliased to these.
     */
    public String path() {
        return VariantIds.path(host.name(), ore.key(),
                host.name() + "_" + (host.placedBy() == null ? ore.name() : ore.key()) + "_ore");
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

    /**
     * The ore block this variant stands in for: its drops, experience and tool tier. In the game's own
     * rock, the form that rock's tier receives. A stone another mod places swallows every form; it takes
     * its own tier's form where the ore has one, else the first the ore has (a Nether ore in scoria).
     */
    public ResourceLocation source() {
        final ResourceLocation own = ore.formIn(host);
        return own != null || host.placedBy() == null ? own : ore.forms().get(0);
    }

    /**
     * The block {@link #source()} names, or null. Only once every mod has registered, i.e. at server
     * start or in the world, never during our own registration.
     */
    public Block sourceBlock() {
        final ResourceLocation source = source();
        return source == null ? null : BuiltInRegistries.BLOCK.getOptional(source).orElse(null);
    }

    /** Whether this variant takes the deepslate form's strength and experience. */
    public boolean deepslate() {
        return host.tier() == OreTier.DEEPSLATE;
    }

    /**
     * The vanilla block whose properties the variant copies: the ore itself for a vanilla ore, else the
     * vanilla ore convention of the source's tier, which the ore's own mod follows unless {@link
     * OreType#strength()} says otherwise. Always vanilla, so it is registered before we are; a modded
     * ore's own block may not be.
     */
    public ResourceLocation propertiesSource() {
        if (ore.requiredModId() == null) {
            return source();
        }
        if (source().equals(ore.netherOre())) {
            return new ResourceLocation("minecraft", "nether_quartz_ore");
        }
        return new ResourceLocation("minecraft", deepslate() ? "deepslate_iron_ore" : "iron_ore");
    }
}
