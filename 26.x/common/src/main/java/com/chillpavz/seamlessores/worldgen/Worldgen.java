package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.google.gson.JsonObject;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.placement.CountPlacement;

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
     * generated: the ore targets and veins, the dripstone shell swap, and the Lush Caves patches.
     * The Sulfur Caves switch is read first, because the era's vein pass asks it.
     */
    public static void onServerStarting(RegistryAccess registries) {
        SulfurCaves.prepare(registries);
        era().injectOreTargets(registries);
        DripstoneShell.prepare();
        LushCavesInjector.inject(registries, era());
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
        public void injectOreTargets(RegistryAccess registries) {
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
