package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.Block;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Restyles ore that a stone swallowed, by extending the STONE's feature.
 *
 * <h2>Why the stone side</h2>
 * The stones other mods add are placed through biome modifiers and Fabric's biome API, which append, so
 * their blobs come after the ores; Create's strata later still. A blob replaces the rock around an ore and
 * leaves the ore, still wearing stone or deepslate, inside it. That seam is what this fixes. The
 * opposite order, ore placed into a stone already there, is the ore side's ({@link OreSideInjector}).
 *
 * <p>For every ore the stone swallows, one rule is put in front of the stone feature's own targets: where
 * the blob meets any form of that ore, it places that ore in this stone, or the stone itself where the
 * geology rule refuses the pair. Everywhere else the blob does what it always did. The same positions
 * hold ore, in the same number: one for one, no ore added (only, for a refused pair, removed).
 *
 * <p>The forms of an ore are its own blocks (stone, deepslate, Nether), and our variants of it in every
 * other host: a limestone blob placed over granite leaves our granite iron inside limestone, and one
 * placed over marble our marble iron.
 */
public final class StoneSideInjector {

    static final String NAME = "Stone side";

    private StoneSideInjector() {}

    public static void inject(RegistryAccess registries, WorldgenEra era) {
        final Map<OreVariant, Block> ours = SeamlessOresContent.blocks();
        // Every variant of each ore, whichever host: all of them are a form a blob can swallow.
        final Map<OreType, List<Block>> variantsOf = new IdentityHashMap<>();
        ours.forEach((variant, block) -> variantsOf.computeIfAbsent(variant.ore(), o -> new ArrayList<>()).add(block));
        // Which host each stone block is.
        final Map<Block, HostStone> hostOf = new IdentityHashMap<>();
        for (HostStone host : HostStone.ALL) {
            final Block stone = host.present() && !host.swallows().isEmpty() ? host.block() : null;
            if (stone != null && SeamlessOresConfig.isHostEnabled(host.name())) {
                hostOf.put(stone, host);
            }
        }
        if (hostOf.isEmpty()) {
            Constants.LOG.info("{}: no stone that swallows ore is installed and switched on, nothing to do", NAME);
            return;
        }

        int patched = 0;
        int added = 0;
        for (OreSite site : era.oreSites(registries)) {
            final Set<HostStone> hosts = new LinkedHashSet<>();
            for (OreSite.Target target : site.targets()) {
                final HostStone host = hostOf.get(target.state().getBlock());
                if (host != null) {
                    hosts.add(host);
                }
            }
            if (hosts.isEmpty() || !site.rebuildable(NAME)) {
                continue;
            }
            if (OreSideInjector.placesOurs(site)) {
                continue;   // already done, e.g. a second world opened in the same session
            }
            final HostStone host = hosts.iterator().next();
            if (hosts.size() > 1) {
                // Which stone a swallowed ore should take would depend on which target placed the
                // stone at that position, which a block match cannot see. No known feature does this.
                Constants.LOG.warn("{}: {} places {} stones, using {} for all of them",
                        NAME, site.name(), hosts.size(), host);
            }
            final List<OreSite.Rule> rules = new ArrayList<>();
            for (OreType ore : host.swallows()) {
                final Block becomes = host.refused().contains(ore) ? host.block() : ours.get(new OreVariant(host, ore));
                if (becomes != null && ore.isLoaded() && OreSideInjector.enabled(host, ore, false)) {
                    rules.add(new OreSite.Swallow(formsOf(ore, becomes, variantsOf), becomes));
                }
            }
            if (rules.isEmpty()) {
                continue;
            }
            site.rebuild(rules, site.size(), false);
            patched++;
            added += rules.size();
            Constants.LOG.info("{}: {} ({}) now converts {} ores", NAME, site.name(), host, rules.size());
        }
        Constants.LOG.info("{}: prepended {} ore targets across {} stone features", NAME, added, patched);
    }

    /** Every block that is this ore, other than the one it becomes. */
    private static List<Block> formsOf(OreType ore, Block becomes, Map<OreType, List<Block>> variantsOf) {
        final List<Block> forms = new ArrayList<>();
        for (var id : ore.forms()) {
            BuiltInRegistries.BLOCK.getOptional(id).ifPresent(forms::add);
        }
        for (Block variant : variantsOf.getOrDefault(ore, List.of())) {
            if (variant != becomes) {
                forms.add(variant);
            }
        }
        return forms;
    }
}
