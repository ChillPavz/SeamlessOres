package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.server.level.WorldGenRegion;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Sees every block a feature writes during worldgen, so sulfur or cinnabar laid next to an ore that
 * was already there can clear it. See {@link SulfurCaves}. One tag test per write while the Sulfur
 * Caves exist and the switch is on. {@code require = 0}: a miss leaves the odd ore beside late sulfur.
 * At 1.20.1 the region's write reach is a plain field; from 1.21 it is its generation step's.
 */
@Mixin(WorldGenRegion.class)
public abstract class SulfurRegionMixin implements SulfurCaves.WriteZone {

    @Shadow @Final private int writeRadiusCutoff;

    @Inject(method = "setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;II)Z",
            at = @At("HEAD"), require = 0)
    private void seamlessores$clearOreBesideLateSulfur(BlockPos pos, BlockState state, int flags, int recursionLeft,
                                                       CallbackInfoReturnable<Boolean> cir) {
        if (SulfurCaves.active()) {
            SulfurCaves.beforeWorldgenWrite((WorldGenRegion) (Object) this, pos, state, this::seamlessores$canWrite);
        }
    }

    /** The region's own write test, without the error it logs when the answer is no. */
    @Override
    public boolean seamlessores$canWrite(BlockPos target) {
        final ChunkPos center = ((WorldGenRegion) (Object) this).getCenter();
        return Math.abs(SectionPos.blockToSectionCoord(target.getX()) - center.x) <= this.writeRadiusCutoff
                && Math.abs(SectionPos.blockToSectionCoord(target.getZ()) - center.z) <= this.writeRadiusCutoff;
    }
}
