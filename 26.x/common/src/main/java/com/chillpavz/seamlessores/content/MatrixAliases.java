package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.resources.Identifier;

import java.util.ArrayList;
import java.util.List;
import java.util.function.BiConsumer;

/**
 * The ores in modded stones were a separate mod until 4.x, Seamless Ores: Matrix. Its ids are mapped to
 * what stands for them now, so a world or an inventory that held them converts on load instead of
 * losing the blocks.
 *
 * <p>Matrix named a variant {@code seamlessoresmatrix:<stone namespace>_<stone path>_<ore key>_ore}, for
 * every ore each of its stones swallows (dripstone included, under Create). A pair we build maps straight
 * to its variant's id (6.0.0's id rule, {@link VariantIds}; 5.x kept Matrix's name), or to our dripstone
 * variant. A pair the geology rule refuses has no block:
 * its old id becomes the plain ore it stood in for, so no mined ore is lost (owner's choice; a few
 * seams stay in old chunks).
 *
 * <p>Every block id is also an item id, so the same table serves both registries. Only used while the
 * old mod is absent: an alias may not shadow an id that is still registered. While it is installed it
 * keeps placing its ores under its own ids, and ours stand down (see the worldgen injectors). Never a
 * hard incompatibility.
 */
public final class MatrixAliases {

    public static final String OLD_MOD_ID = "seamlessoresmatrix";

    private MatrixAliases() {}

    /** One old id and its new target; {@code modded}: the target is another mod's block, which may register after us. */
    public record Alias(Identifier old, Identifier target, boolean modded) {}

    /** Whether the retired Seamless Ores: Matrix is still installed next to us. */
    public static boolean oldModInstalled() {
        return Services.PLATFORM.isModLoaded(OLD_MOD_ID);
    }

    /** Every alias for the installed mod set. Call after our blocks are registered. */
    public static List<Alias> all() {
        final List<Alias> aliases = new ArrayList<>();
        for (OreVariant variant : SeamlessOresContent.blocks().keySet()) {
            if (variant.host().swallows().contains(variant.ore())) {
                aliases.add(new Alias(oldId(variant.host(), variant.ore()), variant.id(), false));
            }
        }
        for (HostStone host : HostStone.ALL) {
            if (!host.present()) {
                continue;
            }
            for (OreType ore : host.refused()) {
                if (ore.isLoaded()) {
                    // The form of the host's own tier, as a variant would have stood in for.
                    final OreVariant refused = new OreVariant(host, ore);
                    aliases.add(new Alias(oldId(host, ore), refused.source(), ore.requiredModId() != null));
                }
            }
        }
        return aliases;
    }

    private static Identifier oldId(HostStone host, OreType ore) {
        return Identifier.fromNamespaceAndPath(OLD_MOD_ID,
                host.id().getNamespace() + "_" + host.id().getPath() + "_" + ore.key() + "_ore");
    }

    /**
     * Adds every alias through {@code add} (old, target), once per registry, each fenced off: a loader
     * that refuses one leaves that id unconverted and says so once.
     */
    public static void addAll(List<Alias> aliases, BiConsumer<Identifier, Identifier> add, String registry) {
        int added = 0;
        int failed = 0;
        for (Alias alias : aliases) {
            try {
                add.accept(alias.old(), alias.target());
                added++;
            } catch (RuntimeException e) {
                if (failed++ == 0) {
                    Constants.LOG.warn("Could not map the old Matrix id {} to {} in {}; old blocks with"
                            + " that id will be lost", alias.old(), alias.target(), registry, e);
                }
            }
        }
        Constants.LOG.info("Mapped {} Seamless Ores: Matrix ids to their new {} ({} failed)", added, registry, failed);
    }
}
