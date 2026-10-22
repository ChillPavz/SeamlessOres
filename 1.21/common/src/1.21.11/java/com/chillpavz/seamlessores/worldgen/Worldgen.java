package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.content.SourceDrift;
import net.minecraft.core.RegistryAccess;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** Everything worldgen patches once the server's registries are loaded and before any chunk is generated. */
public final class Worldgen {

    private static final WorldgenEra ERA = new BandWorldgen();

    private static final Set<String> DISABLED = ConcurrentHashMap.newKeySet();

    private Worldgen() {
    }

    /** The ore targets (both sides), the large veins, the dripstone shell swap and the Lush Caves patches. */
    public static void onServerStarting(RegistryAccess registries) {
        // Hardness, blast resistance and experience are fixed when our blocks are built: say so once if a
        // source ore has since changed (a mod update, a modpack script).
        run("Source drift", SourceDrift::check);
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
        // The dripstone shell swap and the Lush Caves patches run after the ore pass, as on 26.x.
        run("Dripstone shells", DripstoneShell::prepare);
        run("Walled-in ore", WalledInOre::prepare);
        run("Lush Caves", () -> LushCavesInjector.inject(registries, ERA));
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
