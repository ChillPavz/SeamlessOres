package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.SeamlessOresConfigScreenFactory;
import net.minecraftforge.client.ConfigScreenHandler;
import net.minecraftforge.fml.ModLoadingContext;

/**
 * Client-only: wires the config screen into Forge's mod-list "Config" button. Kept in its own class
 * so its client-only references are never loaded on a dedicated server (see the Dist guard in
 * {@link SeamlessOresForge}).
 *
 * <p>The screen itself is Cloth Config's, generated from the same annotated data class Fabric and
 * NeoForge use, rather than the hand written one this module used to carry. Official cloth has no
 * Forge build at this version, but the unofficial cloth-config-forge port does.
 *
 * <p>Use the {@code BiFunction<Minecraft, Screen, Screen>} form of the factory only if you ever
 * backport below Forge 47 - the shorter {@code Function<Screen, Screen>} constructor used here does
 * not exist there.
 */
final class SeamlessOresConfigScreenRegistrar {

    private SeamlessOresConfigScreenRegistrar() {
    }

    static void register() {
        ModLoadingContext.get().registerExtensionPoint(ConfigScreenHandler.ConfigScreenFactory.class,
                () -> new ConfigScreenHandler.ConfigScreenFactory(
                        SeamlessOresConfigScreenFactory::create));
    }
}
