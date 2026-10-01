package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.client.MatrixMessage;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;

/**
 * Client only. Nothing here touches rendering: the chunk layer is derived from the texture's own alpha
 * from 26.1, so this entrypoint exists for the chat note alone.
 */
public class SeamlessOresFabricClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(MatrixMessage::onClientTick);
    }
}
