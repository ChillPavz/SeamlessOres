package com.chillpavz.seamlessores.matrix.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.matrix.MatrixConfig;
import com.chillpavz.seamlessores.matrix.content.HostStone;
import com.chillpavz.seamlessores.matrix.content.MatrixContent;
import com.chillpavz.seamlessores.matrix.content.OreKind;
import com.chillpavz.seamlessores.matrix.content.Variant;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.block.Block;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/**
 * Restyles ore placed INTO a stone that was already there, by extending the ORE's feature.
 *
 * <p>The mirror of {@link StoneSideInjector}. Several of the stones are in the ore replaceables tags
 * (Blockus limestone and marble and Promenade's two in the stone one, bluestone, viridite and gabbro in
 * the deepslate one), so any ore feature that runs AFTER such a stone places its plain ore inside it.
 * Create's zinc always does. Whether that happens depends on load order, so both sides are covered
 * and the result does not.
 *
 * <p>Each added rule fires only where the feature would have placed that very ore AND the block is
 * the stone, so it inherits every height rule the original has, including 26.3's height-specific tuff
 * split.
 */
public final class OreSideInjector {

    static final String NAME = "Ore side";

    private OreSideInjector() {}

    public static void inject(RegistryAccess registries) {

        final Map<Block, Variant> ours = MatrixContent.byBlock();
        // Which of our blocks stand in for each ore block, every form of it alike.
        final Map<Block, List<Map.Entry<Block, Block>>> byOre = new IdentityHashMap<>();
        ours.forEach((block, variant) -> {
            final Block stone = variant.host().block();
            if (stone == null || !MatrixConfig.isEnabled(variant.host())) {
                return;
            }
            for (var id : variant.ore().forms()) {
                BuiltInRegistries.BLOCK.getOptional(id).ifPresent(ore ->
                        byOre.computeIfAbsent(ore, o -> new ArrayList<>()).add(Map.entry(stone, block)));
            }
        });
        // An ore that never forms in a stone (the geology rule) becomes that stone instead.
        for (HostStone host : HostStone.ALL) {
            final Block stone = host.isLoaded() && MatrixConfig.isEnabled(host) ? host.block() : null;
            if (stone == null) {
                continue;
            }
            for (OreKind kind : host.refused()) {
                for (var id : kind.forms()) {
                    BuiltInRegistries.BLOCK.getOptional(id).ifPresent(ore ->
                            byOre.computeIfAbsent(ore, o -> new ArrayList<>()).add(Map.entry(stone, stone)));
                }
            }
        }
        if (byOre.isEmpty()) {
            Constants.LOG.info("{}: no supported stone is installed and switched on, nothing to do", NAME);
            return;
        }

        int patched = 0;
        int added = 0;
        for (OreSite site : OreSites.find(registries)) {
            final List<OreSite.Rule> rules = new ArrayList<>();
            for (OreSite.Target target : site.targets()) {
                for (Map.Entry<Block, Block> pair : byOre.getOrDefault(target.state().getBlock(), List.of())) {
                    if (OreSites.receives(target.test(), pair.getKey())) {
                        rules.add(new OreSite.Receive(target.test(), pair.getKey(), pair.getValue()));
                    }
                }
            }
            if (rules.isEmpty() || !site.rebuildable(NAME) || OreSites.placesAny(site.targets(), ours)) {
                continue;
            }
            site.prepend(rules);
            patched++;
            added += rules.size();
        }
        Constants.LOG.info("{}: added {} ore targets across {} ore features", NAME, added, patched);
    }
}
