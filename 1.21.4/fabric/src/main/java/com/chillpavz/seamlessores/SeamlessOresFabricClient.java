package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.fabricmc.api.ClientModInitializer;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.world.level.block.Block;

import java.lang.reflect.Method;

/**
 * Puts every variant on the cutout chunk layer.
 *
 * <p><b>Required below 26.1.</b> From 26.1 the layer is derived from the texture's own alpha
 * ({@code NativeImage.computeTransparency} feeding {@code ChunkSectionLayer.byTransparency}) and no
 * per-loader API exists. Neither method exists here: this range routes through
 * {@code ItemBlockRenderTypes}, whose map is private and whose default is solid, so an undeclared
 * block draws its overlay's transparent pixels opaque and NOTHING is logged.
 *
 * <p><b>Fabric's API for this MOVED at 1.21.6, in the middle of the range this jar declares</b>, so
 * both shapes are resolved reflectively and whichever is present wins:
 * <ul>
 *   <li>1.21.4 and 1.21.5: {@code api.blockrenderlayer.v1.BlockRenderLayerMap.INSTANCE
 *       .putBlocks(RenderType, Block...)} - an INSTANCE method taking a {@link RenderType}.</li>
 *   <li>1.21.6 and up: {@code api.client.rendering.v1.BlockRenderLayerMap.putBlocks(
 *       ChunkSectionLayer, Block...)} - a STATIC method taking a {@code ChunkSectionLayer}, a class
 *       that does not exist at 1.21.4 and so can never be named at compile time here.</li>
 * </ul>
 * Compiling against either one alone gives a {@code NoClassDefFoundError} on the other half of the
 * range, which is a hard crash before the main menu rather than a missing texture.
 *
 * <p>Covers Fabric only. NeoForge reads a {@code "render_type"} field off the block model JSON
 * instead, which the asset generator writes.
 */
public class SeamlessOresFabricClient implements ClientModInitializer {

    private static final String NEW_API = "net.fabricmc.fabric.api.client.rendering.v1.BlockRenderLayerMap";
    private static final String OLD_API = "net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap";

    @Override
    public void onInitializeClient() {

        // Runs after the main initializer, so every variant is registered by now.
        final Block[] blocks = SeamlessOresContent.blocks().values().toArray(new Block[0]);
        if (blocks.length == 0) {
            return;
        }

        // Cosmetic feature: degrade rather than crash. Losing it makes the ore overlays draw their
        // transparent pixels opaque, which looks wrong but is still a playable game.
        try {
            if (applyNewApi(blocks) || applyOldApi(blocks)) {
                Constants.LOG.debug("Set cutout render layer on {} ore variants", blocks.length);
                return;
            }
            Constants.LOG.error("No Fabric BlockRenderLayerMap found; ore overlays will draw opaque");
        } catch (Throwable t) {
            Constants.LOG.error("Could not set the cutout render layer; ore overlays will draw opaque", t);
        }
    }

    /** 1.21.6 and up. Static, and its layer argument is an enum this branch cannot compile against. */
    private static boolean applyNewApi(Block[] blocks) throws Exception {

        final Class<?> cls = findClass(NEW_API);
        if (cls == null) {
            return false;
        }
        for (Method m : cls.getMethods()) {
            final Class<?>[] params = m.getParameterTypes();
            if (!m.getName().equals("putBlocks") || params.length != 2
                    || params[1] != Block[].class || !params[0].isEnum()) {
                continue;
            }
            // Enum CONSTANT names survive obfuscation and remapping (verified against the real
            // 1.21.10 client jar), even though the fields themselves are renamed, so matching on
            // name() is safe where naming the class at compile time is not.
            for (Object constant : params[0].getEnumConstants()) {
                if (((Enum<?>) constant).name().equals("CUTOUT")) {
                    m.invoke(null, constant, blocks);
                    return true;
                }
            }
            return false;
        }
        return false;
    }

    /** 1.21.4 and 1.21.5. An instance method behind INSTANCE, taking a RenderType. */
    private static boolean applyOldApi(Block[] blocks) throws Exception {

        final Class<?> cls = findClass(OLD_API);
        if (cls == null) {
            return false;
        }
        final Object instance = cls.getField("INSTANCE").get(null);
        // RenderType survives the whole range, so this compile time reference always links; only
        // the Fabric class above decides which path is taken.
        cls.getMethod("putBlocks", RenderType.class, Block[].class)
                .invoke(instance, RenderType.cutout(), blocks);
        return true;
    }

    private static Class<?> findClass(String name) {

        try {
            return Class.forName(name);
        } catch (ClassNotFoundException e) {
            return null;
        }
    }
}
