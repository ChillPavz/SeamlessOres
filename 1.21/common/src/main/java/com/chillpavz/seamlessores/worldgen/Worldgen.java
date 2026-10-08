package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.RegistryAccess;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** Everything worldgen patches once the server's registries are loaded and before any chunk is generated. */
public final class Worldgen {

    private static final WorldgenEra ERA = new BandWorldgen();

    private static final Set<String> DISABLED = ConcurrentHashMap.newKeySet();

    private Worldgen() {
    }

    /** The ore targets (both sides) and the large veins. */
    public static void onServerStarting(RegistryAccess registries) {
        run(OreSideInjector.NAME, () -> OreSideInjector.inject(registries, ERA));
        run(StoneSideInjector.NAME, () -> StoneSideInjector.inject(registries, ERA));
        // Copper is thinned separately, and NOT from here. It edits placement COUNTS by rebinding a
        // placed feature to a new instance, which has to happen before ChunkGenerator builds its
        // feature-order table or chunk decoration dies on an index of -1. It therefore runs from
        // ChunkGeneratorMixin at the head of validate(); this only reports a thinning that should have
        // happened and did not. See CopperDensityInjector and ChunkGeneratorMixin.
        CopperDensityInjector.warnIfNeverRan();
        // The large copper and iron veins come from OreVeinifier during noise generation, invisible to
        // the ore features.
        run("Ore veins", VeinOreInjector::inject);
    }

    /**
     * Runs one injector, fenced off: if it throws, the world loads without that part of the mod for this
     * session and the log says so once. A cosmetic mod must never be the reason a world does not open.
     */
    private static void run(String name, Runnable injector) {
        if (DISABLED.contains(name)) {
            return;
        }
        try {
            injector.run();
        } catch (Throwable t) {
            DISABLED.add(name);
            Constants.LOG.error("{} injection failed and is disabled for this session;"
                    + " ore keeps its usual look in new chunks", name, t);
        }
    }
}
