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

    /** The ore targets (both sides), the large veins, the dripstone shell swap and the Lush Caves patches. */
    public static void onServerStarting(RegistryAccess registries) {
        // Vanilla Backport's Sulfur Caves first: the ore side asks whether they are on.
        run("Sulfur Caves", () -> SulfurCaves.prepare(registries));
        run(OreSideInjector.NAME, () -> OreSideInjector.inject(registries, ERA));
        run(StoneSideInjector.NAME, () -> StoneSideInjector.inject(registries, ERA));
        // Copper is thinned separately: it edits placement COUNTS on placed features rather than
        // what a feature places, so it is about amounts rather than appearance.
        //
        // IT RUNS FROM HERE ON THIS BAND, and that is version specific. Thinning rebinds a placed
        // feature to a new instance, which is only safe before ChunkGenerator's feature-order table
        // indexes the old one. At 1.20.1 that table is built lazily at the first chunk decoration,
        // so server start is early enough. The newer bands force it during level load, from
        // ChunkGenerator.validate(), and there the thinning has to move into a mixin at the head of
        // that method - a method 1.20.1 does not have at all. See CopperDensityInjector.
        run("Copper", () -> CopperDensityInjector.thinAtServerStart(registries));
        // The large copper and iron veins come from OreVeinifier during noise generation, invisible to
        // the ore features.
        run("Ore veins", VeinOreInjector::inject);
        // After the veins are restyled: the Sulfur Caves keep the veins as they now stand out.
        run("Sulfur Caves", SulfurCaves::afterInjectors);
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
