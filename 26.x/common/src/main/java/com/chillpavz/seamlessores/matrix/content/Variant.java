package com.chillpavz.seamlessores.matrix.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.resources.Identifier;

/** One host stone x ore pairing, e.g. limestone + iron -> {@code blockus_limestone_iron_ore}. */
public record Variant(HostStone host, OreKind ore) {

    public String path() {
        // Dripstone is a Seamless Ores host in its own right: these are its blocks, borrowed.
        return borrowed() ? "dripstone_" + ore.id() + "_ore" : host.name() + "_" + ore.id() + "_ore";
    }

    /** True when the block is one of Seamless Ores' own vanilla-stone variants rather than ours. */
    public boolean borrowed() {
        return host == HostStone.MINECRAFT_DRIPSTONE_BLOCK;
    }

    public Identifier id() {
        return Identifier.fromNamespaceAndPath(Constants.MOD_ID, path());
    }

    /** The vanilla block whose strength this variant takes. */
    public Identifier strengthSource() {
        return ore.strengthSource(host.strength());
    }
}
