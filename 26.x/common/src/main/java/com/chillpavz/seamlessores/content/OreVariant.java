package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;

/** One host stone x ore pairing, e.g. granite + iron -> {@code seamlessores:granite_iron_ore}. */
public record OreVariant(HostStone host, OreType ore) {

    /**
     * e.g. {@code granite_iron_ore}, mirroring vanilla's own {@code deepslate_iron_ore}. A stone another
     * mod places names the ore by its key ({@code create_scoria_nether_gold_ore}): it can take an
     * overworld and a Nether ore of one name, where the game's own rock takes one tier and keeps the
     * names its ids have always had.
     */
    public String path() {
        return host.name() + "_" + (host.placedBy() == null ? ore.name() : ore.key()) + "_ore";
    }

    public Identifier id() {
        return Identifier.fromNamespaceAndPath(Constants.MOD_ID, path());
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
    public Identifier source() {
        final Identifier own = ore.formIn(host);
        return own != null || host.placedBy() == null ? own : ore.forms().getFirst();
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
    public Identifier propertiesSource() {
        if (ore.requiredModId() == null) {
            return source();
        }
        if (source().equals(ore.netherOre())) {
            return Identifier.withDefaultNamespace("nether_quartz_ore");
        }
        return Identifier.withDefaultNamespace(deepslate() ? "deepslate_iron_ore" : "iron_ore");
    }
}
