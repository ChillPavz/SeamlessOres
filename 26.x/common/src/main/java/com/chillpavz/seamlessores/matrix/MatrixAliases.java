package com.chillpavz.seamlessores.matrix;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.matrix.content.HostStone;
import com.chillpavz.seamlessores.matrix.content.MatrixContent;
import com.chillpavz.seamlessores.matrix.content.OreKind;
import com.chillpavz.seamlessores.matrix.content.Variant;
import net.minecraft.resources.Identifier;

import java.util.ArrayList;
import java.util.List;
import java.util.function.BiConsumer;

/**
 * The ids Seamless Ores: Matrix 1.0.0 registered, mapped to what stands for them now, so a world or an
 * inventory that held them converts on load instead of losing the blocks.
 *
 * <p>Matrix named a variant {@code seamlessoresmatrix:<host>_<ore>_ore}. A pair we still build keeps its
 * path under our namespace (the dripstone ones are our dripstone variants). A pair the geology rule
 * refuses now has no block: its old id becomes the plain ore it stood in for, stone or deepslate form by
 * the host's strength, so no mined ore is lost (owner's choice; a few seams stay in old chunks).
 *
 * <p>Every block id is also an item id, so the same table serves both registries. Only used while the
 * old mod is absent: an alias may not shadow an id that is still registered.
 */
public final class MatrixAliases {

    private MatrixAliases() {}

    /** One old id and its new target; {@code modded}: the target is another mod's block, which may register after us. */
    public record Alias(Identifier old, Identifier target, boolean modded) {}

    /** Every alias for the installed mod set. Call after our blocks are registered. */
    public static List<Alias> all() {
        final List<Alias> aliases = new ArrayList<>();
        for (Variant variant : MatrixContent.blocks().keySet()) {
            aliases.add(new Alias(oldId(variant.host(), variant.ore()), variant.id(), false));
        }
        for (HostStone host : HostStone.ALL) {
            if (!host.isLoaded()) {
                continue;
            }
            for (OreKind ore : host.refused()) {
                if (ore.isLoaded()) {
                    final List<Identifier> forms = ore.forms();
                    final Identifier plain = host.strength() == HostStone.Strength.DEEPSLATE && forms.size() > 1
                            ? forms.get(1) : forms.getFirst();
                    aliases.add(new Alias(oldId(host, ore), plain, ore.modId() != null));
                }
            }
        }
        return aliases;
    }

    private static Identifier oldId(HostStone host, OreKind ore) {
        return Identifier.fromNamespaceAndPath(MatrixPresence.OLD_MOD_ID, host.name() + "_" + ore.id() + "_ore");
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
