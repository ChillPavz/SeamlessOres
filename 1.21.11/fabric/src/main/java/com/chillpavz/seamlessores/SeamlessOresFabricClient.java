package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.BlockRenderLayerMap;
import net.minecraft.client.renderer.chunk.ChunkSectionLayer;
import net.minecraft.world.level.block.Block;

/**
 * Puts every variant on the CUTOUT chunk layer.
 *
 * <p><b>Required at 1.21.11, and the one place this branch genuinely diverges from 26.x.</b> From
 * 26.1 the chunk layer is derived from the texture's own alpha - {@code NativeImage
 * .computeTransparency} feeding {@code ChunkSectionLayer.byTransparency} - so nothing has to be
 * declared and no per-loader API exists. Neither method exists here. 1.21.11 still routes through
 * {@code ItemBlockRenderTypes}, whose {@code TYPE_BY_BLOCK} map is private and whose default is
 * {@code SOLID}, so an undeclared block draws its overlay's transparent pixels as opaque and
 * NOTHING is logged.
 *
 * <p>This covers Fabric only. NeoForge and Forge both read a {@code "render_type"} field off the
 * block model JSON instead, which the asset generator writes; they ignore this class, and Fabric
 * ignores that field. Both halves are needed.
 *
 * <p>Client-only by construction: it is reached through the {@code client} entrypoint, so a
 * dedicated server never loads it or the rendering classes it names.
 */
public class SeamlessOresFabricClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {

        // Runs after the main initializer, so every variant is registered by now.
        Block[] blocks = SeamlessOresContent.blocks().values().toArray(new Block[0]);
        if (blocks.length == 0) {
            return;
        }
        BlockRenderLayerMap.putBlocks(ChunkSectionLayer.CUTOUT, blocks);
        Constants.LOG.debug("Set CUTOUT render layer on {} ore variants", blocks.length);
    }
}
