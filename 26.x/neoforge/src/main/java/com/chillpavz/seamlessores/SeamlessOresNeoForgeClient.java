package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.client.MatrixMessage;
import net.minecraft.client.Minecraft;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.NeoForge;

/**
 * Client only, and loaded only behind the dist check in {@link SeamlessOresNeoForge}, so a dedicated
 * server never loads a class that names a client type.
 */
final class SeamlessOresNeoForgeClient {

    private SeamlessOresNeoForgeClient() {
    }

    static void init() {
        // A GAME bus event, like ServerAboutToStartEvent.
        NeoForge.EVENT_BUS.addListener(SeamlessOresNeoForgeClient::onClientTick);
    }

    private static void onClientTick(ClientTickEvent.Post event) {
        MatrixMessage.onClientTick(Minecraft.getInstance());
    }
}
