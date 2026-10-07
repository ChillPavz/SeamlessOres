package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.world.level.block.Block;

/**
 * Puts every variant on the cutout chunk layer.
 *
 * <p><b>Required below 26.1.</b> From 26.1 the layer is derived from the texture's own alpha
 * ({@code NativeImage.computeTransparency} feeding {@code ChunkSectionLayer.byTransparency}) and no
 * per-loader API exists. Neither method exists here: 1.21.1 routes through
 * {@code ItemBlockRenderTypes}, whose {@code TYPE_BY_BLOCK} map is private and whose default is
 * solid, so an undeclared block draws its overlay's transparent pixels opaque and NOTHING is logged.
 *
 * <p>The API differs from the 1.21.11 branch in three ways, so do not copy that file here:
 * the package is {@code blockrenderlayer.v1} rather than {@code client.rendering.v1},
 * {@link BlockRenderLayerMap} is an interface reached through {@code INSTANCE} rather than a static
 * utility, and the layer type is {@link RenderType} rather than {@code ChunkSectionLayer}.
 *
 * <p>Covers Fabric only. NeoForge and Forge read a {@code "render_type"} field off the block model
 * JSON instead, which the asset generator writes.
 */
public class SeamlessOresFabricClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {

        // Runs after the main initializer, so every variant is registered by now.
        Block[] blocks = SeamlessOresContent.blocks().values().toArray(new Block[0]);
        if (blocks.length == 0) {
            return;
        }
        BlockRenderLayerMap.INSTANCE.putBlocks(RenderType.cutout(), blocks);
        Constants.LOG.debug("Set cutout render layer on {} ore variants", blocks.length);
    }
}
