package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.content.MatrixAliases;
import com.google.gson.JsonObject;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.placement.CountPlacement;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.BiConsumer;
import java.util.function.UnaryOperator;

/**
 * Picks the {@link WorldgenEra} for the running game, once.
 *
 * <p>The probe is the field that 26.3 removed: {@code Registries.CONFIGURED_FEATURE} exists on 26.1,
 * 26.1.1, 26.1.2 and 26.2 and not on 26.3. The era class is then loaded by NAME, so neither era is
 * named in shared code and the other one is never linked.
 */
public final class Worldgen {

    private static final String PACKAGE = "com.chillpavz.seamlessores.worldgen.";

    private static WorldgenEra era;

    private static final Set<String> DISABLED = ConcurrentHashMap.newKeySet();

    private Worldgen() {
    }

    public static synchronized WorldgenEra era() {
        if (era == null) {
            final String name = hasConfiguredFeatures() ? "era261.Era261" : "era263.Era263";
            try {
                era = (WorldgenEra) Class.forName(PACKAGE + name).getDeclaredConstructor().newInstance();
            } catch (ReflectiveOperationException | LinkageError | ClassCastException e) {
                // Only a damaged jar gets here. Degrade: the blocks still register and drop, the
                // world generates exactly as vanilla, and the log says why once.
                Constants.LOG.error("Worldgen: {} could not be loaded for this Minecraft version, so no"
                        + " ore is restyled in new chunks", name, e);
                era = new Disabled();
            }
            Constants.LOG.info("Worldgen: {}", era.name());
        }
        return era;
    }

    /**
     * Everything worldgen patches once the server's registries are loaded and before any chunk is
     * generated: the ore targets (both sides) and veins, the dripstone shell swap, and the Lush Caves
     * patches. The Sulfur Caves switch is read first, because the era's vein pass asks it.
     */
    public static void onServerStarting(RegistryAccess registries) {
        SulfurCaves.prepare(registries);
        if (MatrixAliases.oldModInstalled()) {
            // The retired Seamless Ores: Matrix is still installed and places the ores it swallows in
            // modded stones under its own ids. Doing it twice would race the two for the same ore; its
            // blocks stay theirs until the player removes it, and the chat note asks them to.
            Constants.LOG.info("Seamless Ores: Matrix is installed, so it places the ores in modded"
                    + " stones and ours stand down. Remove it to let Seamless Ores take over.");
        }
        run(OreSideInjector.NAME, () -> OreSideInjector.inject(registries, era()));
        run(StoneSideInjector.NAME, () -> StoneSideInjector.inject(registries, era()));
        // Copper is thinned separately, and NOT from here. It edits placement COUNTS by rebinding a
        // placed feature to a new instance, which has to happen before ChunkGenerator builds its
        // feature-order table or chunk decoration dies on an index of -1. It therefore runs from
        // ChunkGeneratorMixin at the head of validate(); this only reports a thinning that should have
        // happened and did not. See CopperDensityInjector and ChunkGeneratorMixin.
        CopperDensityInjector.warnIfNeverRan();
        // The large copper and iron veins come from noise generation, invisible to the ore features.
        run("Ore veins", () -> era().injectVeins(registries));
        DripstoneShell.prepare();
        LushCavesInjector.inject(registries, era());
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

    private static boolean hasConfiguredFeatures() {
        try {
            Registries.class.getField("CONFIGURED_FEATURE");
            return true;
        } catch (NoSuchFieldException e) {
            return false;
        }
    }

    /** No worldgen at all: nothing registered, nothing injected, copper left at vanilla's count. */
    private static final class Disabled implements WorldgenEra {

        @Override
        public String name() {
            return "disabled";
        }

        @Override
        public ResourceKey<? extends Registry<?>> featureTypeRegistry() {
            return Registries.FEATURE;
        }

        @Override
        public Registry<?> builtInFeatureTypes() {
            return null;
        }

        @Override
        public void registerFeatureTypes(BiConsumer<Identifier, Object> sink) {
        }

        @Override
        public List<OreSite> oreSites(RegistryAccess registries) {
            return List.of();
        }

        @Override
        public boolean receives(RuleTest original, Block stone) {
            return false;
        }

        @Override
        public void injectVeins(RegistryAccess registries) {
        }

        @Override
        public int maxCount(CountPlacement placement) {
            return -1;
        }

        @Override
        public boolean rewriteFeature(RegistryAccess registries, Identifier id, UnaryOperator<JsonObject> edit) {
            return false;
        }
    }
}
