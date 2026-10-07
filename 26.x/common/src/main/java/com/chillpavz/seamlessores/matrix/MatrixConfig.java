package com.chillpavz.seamlessores.matrix;

import com.chillpavz.seamlessores.Constants;

import com.chillpavz.seamlessores.matrix.content.HostStone;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Plain values holder that worldgen reads.
 *
 * <p>Lives in {@code common} and holds no library types. Cloth Config's annotated class cannot live
 * here, because loader dependencies are not on common's classpath, so each loader module owns its
 * own annotated copy and pushes the values in here through {@link #apply}. Keep the two loader
 * copies identical.
 *
 * <p><b>Config affects worldgen only, never registration.</b> The registered block set is derived
 * from the loaded mod set so a client and a server always agree; if config could add or remove
 * blocks, a mismatch would kick players on join. Switching a stone off only means its variants never
 * generate: the blocks still exist, in the creative tab and in every tag.
 *
 * <p>Changes take effect the next time a world loads, because the injection runs at server start.
 * Already-generated chunks never change either way.
 */
public final class MatrixConfig {

    private MatrixConfig() {}

    /** Host stones whose variants are switched off, by {@link HostStone#name()}. */
    private static volatile Set<String> disabledHosts = Set.of();

    /**
     * Takes one switch per host stone, keyed by {@link HostStone#name()}. The loader's config class is
     * generated from the host table, so every host has one; a host without a switch stays on and the
     * log says so, which means the generator was not re-run after the table changed.
     */
    public static void apply(Map<String, Boolean> switches) {
        final Set<String> off = new HashSet<>();
        final List<String> missing = new ArrayList<>();
        for (HostStone host : HostStone.ALL) {
            final Boolean enabled = switches.get(host.name());
            if (enabled == null) {
                missing.add(host.name());
            } else if (!enabled) {
                off.add(host.name());
            }
        }
        disabledHosts = Set.copyOf(off);
        if (!missing.isEmpty()) {
            Constants.LOG.warn("Config: no switch for {}, generated as normal", missing);
        }
        if (!off.isEmpty()) {
            Constants.LOG.info("Config: generation switched off for {}", off);
        }
    }

    /** Whether this stone's variants are generated. */
    public static boolean isEnabled(HostStone host) {
        return !disabledHosts.contains(host.name());
    }
}
