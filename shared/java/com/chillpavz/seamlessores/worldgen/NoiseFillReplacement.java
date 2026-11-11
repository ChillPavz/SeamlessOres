package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;

import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Says once when the Sulfur Caves vein hook cannot work because another mod replaces the noise fill.
 *
 * <p>C2ME's OpenCL acceleration add-on overwrites {@code NoiseBasedChunkGenerator.doFill} (GitHub issue #5). The vein
 * hook applies above it in priority, so the game starts, but the call it hooks is not in the replacement, and the
 * large veins are then not kept out of the Sulfur Caves. Whether the acceleration is switched on is the add-on's own
 * setting, so the line says "while it is on". Looked up by name, never loaded with initialisation.
 */
public final class NoiseFillReplacement {

    private static final String C2ME_OPENCL = "com.ishland.c2me.opts.accel.opencl.MixinPlugin";
    private static final AtomicBoolean SAID = new AtomicBoolean();

    private NoiseFillReplacement() {}

    /** Called where the Sulfur Caves handling reports itself; {@code active}: it is on in this world. */
    public static void note(boolean active) {
        if (!active || !present() || !SAID.compareAndSet(false, true)) {
            return;
        }
        Constants.LOG.info("Worldgen: C2ME's OpenCL acceleration is installed; while it is on, it replaces the noise "
                + "fill and the large ore veins are not kept out of the Sulfur Caves (everything else is unchanged)");
    }

    private static boolean present() {
        for (ClassLoader loader : new ClassLoader[] {NoiseFillReplacement.class.getClassLoader(),
                Thread.currentThread().getContextClassLoader()}) {
            if (loader == null) {
                continue;
            }
            try {
                Class.forName(C2ME_OPENCL, false, loader);
                return true;
            } catch (ClassNotFoundException | LinkageError absent) {
                // not visible from this loader
            }
        }
        return false;
    }
}
