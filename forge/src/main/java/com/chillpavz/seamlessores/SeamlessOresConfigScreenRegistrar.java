package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.SeamlessOresConfigScreenFactory;
import net.minecraft.client.gui.screens.Screen;
import net.minecraftforge.client.ConfigScreenHandler;
import net.minecraftforge.fml.ModLoadingContext;

/**
 * Client-only: wires the Cloth Config screen into Forge's mod-list "Config" button. Kept in its own
 * class so its client-only references are never loaded on a dedicated server (see the Dist guard in
 * {@link SeamlessOresForge}).
 *
 * <p>Use the {@code BiFunction<Minecraft, Screen, Screen>} constructor instead if this is ever
 * backported below Forge 47 - the shorter {@code Function<Screen, Screen>} form used here does not
 * exist there.
 */
final class SeamlessOresConfigScreenRegistrar {

    private SeamlessOresConfigScreenRegistrar() {
    }

    static void register() {
        ModLoadingContext.get().registerExtensionPoint(ConfigScreenHandler.ConfigScreenFactory.class,
                () -> new ConfigScreenHandler.ConfigScreenFactory(
                        (Screen parent) -> SeamlessOresConfigScreenFactory.create(parent)));
    }
}
