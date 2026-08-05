package com.chillpavz.seamlessores.config;

// NOT AutoConfig: cloth 26.2 moved the screen entry point out to AutoConfigClient, so that the
// server-safe AutoConfig class no longer references GUI types. AutoConfig.getConfigScreen is gone.
import me.shedaniel.autoconfig.AutoConfigClient;
import net.neoforged.fml.ModContainer;
import net.neoforged.neoforge.client.gui.IConfigScreenFactory;

/**
 * Wires the Config button in NeoForge's mods list.
 *
 * <p><b>Client-only.</b> Kept in its own class on purpose: it references screen classes that do not
 * exist on a dedicated server, so it must only be touched behind a
 * {@code FMLEnvironment.getDist() == Dist.CLIENT} guard. Merging this into the mod's main class
 * would load those references on the server and crash it.
 */
public final class SeamlessOresConfigScreen {

    private SeamlessOresConfigScreen() {}

    public static void register(ModContainer container) {
        container.registerExtensionPoint(IConfigScreenFactory.class,
                (mod, parent) -> AutoConfigClient.getConfigScreen(SeamlessOresConfigData.class, parent).get());
    }
}
