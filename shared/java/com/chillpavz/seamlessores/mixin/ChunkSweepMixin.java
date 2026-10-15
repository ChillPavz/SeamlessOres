package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.WalledInOre;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGenerator;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * At the end of each chunk's decoration, restyles the ore a host stone laid at noise time walls in
 * (Terralith's deep blackstone around the iron vein). See {@link WalledInOre#sweepChunk}. The same
 * signature on every band; {@code require = 0}: a miss leaves the seam, it must not stop the game.
 */
@Mixin(ChunkGenerator.class)
public abstract class ChunkSweepMixin {

    @Inject(method = "applyBiomeDecoration", at = @At("TAIL"), require = 0)
    private void seamlessores$sweepWalledInOre(WorldGenLevel level, ChunkAccess chunk, StructureManager structures,
                                               CallbackInfo ci) {
        WalledInOre.sweepChunk(level, chunk);
    }
}
