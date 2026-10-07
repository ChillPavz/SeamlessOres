package com.chillpavz.seamlessores.config;

import com.chillpavz.seamlessores.Constants;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.loading.FMLEnvironment;

/**
 * The only place on NeoForge that touches Cloth Config, so the rest of the mod can load without it.
 *
 * <p>Cloth is an <b>optional</b> NeoForge dependency on this branch, because it ships no NeoForge
 * build for this Minecraft version. Every Cloth type the mod names sits behind this class:
 * {@link SeamlessOresConfigData} implements Cloth's {@code ConfigData}, and
 * {@link SeamlessOresConfigScreenFactory} names its {@code ConfigBuilder}, so <b>merely loading
 * either class without Cloth on the classpath is a {@code NoClassDefFoundError}</b>. Keeping the
 * calls in a separate class means the guard in {@code SeamlessOresNeoForge} decides whether those
 * classes are ever resolved at all, rather than relying on how eagerly a particular JVM resolves a
 * constant-pool entry in a branch it does not take.
 *
 * <p><b>Nothing here may be referenced from outside an {@code isModLoaded("cloth_config")} guard.</b>
 * That is the whole contract of the file.
 *
 * <p>Without Cloth the mod runs on {@link com.chillpavz.seamlessores.SeamlessOresConfig}'s
 * compiled-in defaults, which are the shipped defaults, and has no config screen. Nothing else
 * changes: config only ever gates worldgen injection, never registration, so a client and a server
 * still agree on the block set whether either of them has Cloth or not.
 */
public final class ClothConfigBootstrap {

    /** Cloth's NeoForge mod id. On Fabric the same mod PROVIDES 'cloth-config2' instead. */
    public static final String MOD_ID = "cloth_config";

    private ClothConfigBootstrap() {}

    /**
     * Registers the config file and, on a client, the Config button.
     *
     * <p>Wrapped because a Cloth that is present but incompatible must not take the mod down with
     * it: the values then stay at their defaults and worldgen carries on, which is the same state as
     * having no Cloth at all. Logged once, at error, because a config screen silently going missing
     * is otherwise indistinguishable from us not shipping one.
     */
    public static void init(ModContainer container) {
        try {
            // Must run before worldgen, and before anything reads SeamlessOresConfig.
            SeamlessOresConfigData.register();

            // The screen is client-only and lives in its own class, so a dedicated server never
            // loads a class that references GUI types. FMLEnvironment.getDist() is a METHOD on 26.x.
            if (FMLEnvironment.getDist() == Dist.CLIENT) {
                SeamlessOresConfigScreen.register(container);
            }
        } catch (Throwable t) {
            Constants.LOG.error("Cloth Config is installed but could not be initialised, so Seamless"
                    + " Ores is running with its default settings and no config screen. Worldgen is"
                    + " unaffected.", t);
        }
    }
}
