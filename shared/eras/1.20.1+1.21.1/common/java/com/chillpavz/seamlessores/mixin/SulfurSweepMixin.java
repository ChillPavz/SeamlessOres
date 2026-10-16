package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGenerator;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * The Sulfur Caves' last pass over the chunk's own vein blocks, after its features. See
 * {@link SulfurCaves}. {@code require = 0}: a miss only leaves the odd vein block at the biome's edge.
 */
@Mixin(ChunkGenerator.class)
public abstract class SulfurSweepMixin {

    @Inject(method = "applyBiomeDecoration", at = @At("TAIL"), require = 0)
    private void seamlessores$sweepSulfurCaveVeinEdges(WorldGenLevel level, ChunkAccess chunk,
                                                       StructureManager structures, CallbackInfo ci) {
        SulfurCaves.sweepVeinEdges(level, chunk);
    }
}
