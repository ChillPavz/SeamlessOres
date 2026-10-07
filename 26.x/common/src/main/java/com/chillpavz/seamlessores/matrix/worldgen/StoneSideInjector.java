package com.chillpavz.seamlessores.matrix.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.matrix.MatrixConfig;
import com.chillpavz.seamlessores.matrix.content.HostStone;
import com.chillpavz.seamlessores.matrix.content.MatrixContent;
import com.chillpavz.seamlessores.matrix.content.OreKind;
import com.chillpavz.seamlessores.matrix.content.Variant;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Restyles ore that a stone swallowed, by extending the STONE's feature.
 *
 * <h2>Why the stone side</h2>
 * Modded stones are added through biome modifiers and Fabric's biome API, which append, so their blobs
 * are placed after the ores; Create's strata come later still. A blob replaces the rock around an ore
 * and leaves the ore, still wearing stone or deepslate, inside it. That seam is what this fixes.
 *
 * <p>For every ore kind the stone swallows, one rule is put in front of the stone feature's own
 * targets: where the blob meets any form of that ore, it places that ore in this stone. Everywhere
 * else the blob does what it always did. The same positions hold ore, in the same number: one for one,
 * no ore added or removed.
 *
 * <p>The forms of an ore are its own blocks (stone and deepslate), Seamless Ores' variants of it when
 * that mod is installed (a limestone blob placed over granite leaves Seamless Ores' granite iron inside
 * limestone), and our variants of it in the other hosts (limestone over marble does the same to ours).
 */
public final class StoneSideInjector {

    static final String NAME = "Stone side";

    private StoneSideInjector() {}

    public static void inject(RegistryAccess registries) {

        final Map<Block, Variant> ours = MatrixContent.byBlock();
        // Which host each stone block is, and which of our blocks each host has per ore.
        final Map<Block, HostStone> hostOf = new IdentityHashMap<>();
        final Map<HostStone, Map<OreKind, Block>> variantsOf = new LinkedHashMap<>();
        ours.forEach((block, variant) -> {
            final Block stone = variant.host().block();
            if (stone == null || !MatrixConfig.isEnabled(variant.host())) {
                return;
            }
            hostOf.put(stone, variant.host());
            variantsOf.computeIfAbsent(variant.host(), h -> new EnumMap<>(OreKind.class)).put(variant.ore(), block);
        });
        // Stones that swallow an ore which never forms in them: the geology rule turns it into stone.
        for (HostStone host : HostStone.ALL) {
            final Block stone = host.isLoaded() && !host.refused().isEmpty() && MatrixConfig.isEnabled(host)
                    ? host.block() : null;
            if (stone != null) {
                hostOf.put(stone, host);
                variantsOf.computeIfAbsent(host, h -> new EnumMap<>(OreKind.class));
            }
        }
        if (hostOf.isEmpty()) {
            Constants.LOG.info("{}: no supported stone is installed and switched on, nothing to do", NAME);
            return;
        }

        int patched = 0;
        int added = 0;
        for (OreSite site : OreSites.find(registries)) {
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
            if (OreSites.placesAny(site.targets(), ours)) {
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
            variantsOf.get(host).forEach((kind, block) ->
                    rules.add(new OreSite.Swallow(formsOf(kind, block, variantsOf), block)));
            for (OreKind kind : host.refused()) {
                if (kind.isLoaded()) {
                    rules.add(new OreSite.Swallow(formsOf(kind, null, variantsOf), host.block()));
                }
            }
            if (rules.isEmpty()) {
                continue;
            }
            site.prepend(rules);
            patched++;
            added += rules.size();
            Constants.LOG.info("{}: {} ({}) now converts {} ores", NAME, site.name(), host, rules.size());
        }
        Constants.LOG.info("{}: prepended {} ore targets across {} stone features", NAME, added, patched);
    }

    /** Every block that is this kind of ore, other than the variant it becomes. */
    private static List<Block> formsOf(OreKind kind, Block becomes, Map<HostStone, Map<OreKind, Block>> variantsOf) {
        final List<Block> forms = new ArrayList<>();
        kind.forms().forEach(id -> addIfPresent(forms, id));
        kind.seamlessOresForms().forEach(id -> addIfPresent(forms, id));
        for (Map<OreKind, Block> other : variantsOf.values()) {
            final Block block = other.get(kind);
            if (block != null && block != becomes) {
                forms.add(block);
            }
        }
        return forms;
    }

    private static void addIfPresent(List<Block> forms, Identifier id) {
        BuiltInRegistries.BLOCK.getOptional(id).ifPresent(forms::add);
    }
}
