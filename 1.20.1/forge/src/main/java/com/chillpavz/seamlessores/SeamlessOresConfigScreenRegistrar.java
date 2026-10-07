package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.SeamlessOresConfigScreenFactory;
import net.minecraft.client.Minecraft;
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
        // Use the BiFunction<Minecraft, Screen, Screen> constructor, NOT the shorter
        // Function<Screen, Screen> one. The short form does not exist on Forge 46 (1.20), which
        // this jar also supports, NOR on NeoForge 47.1.x, which is the other loader this jar is
        // tagged for. It crashed exactly there, the moment the mods list tried to build the config
        // button:
        //   NoSuchMethodError: ConfigScreenHandler$ConfigScreenFactory.<init>(java.util.function.Function)
        // Nothing fails at startup, because the extension point is only resolved when the screen is
        // opened - so this is invisible until someone clicks Config. The BiFunction form is present
        // on every one of them.
        ModLoadingContext.get().registerExtensionPoint(ConfigScreenHandler.ConfigScreenFactory.class,
                () -> new ConfigScreenHandler.ConfigScreenFactory(
                        (Minecraft minecraft, Screen parent) ->
                                SeamlessOresConfigScreenFactory.create(parent)));
    }
}
