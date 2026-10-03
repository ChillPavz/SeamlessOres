package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.server.level.WorldGenRegion;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.status.ChunkStep;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Sees every block a feature writes during worldgen, so sulfur or cinnabar laid next to an ore that
 * was already there (a neighbouring chunk's sulfur spring or pool, decorated later) can clear it. See
 * {@link SulfurCaves}. One tag test per write while the switch is on, nothing while it is off.
 * {@code require = 0}: a miss leaves the odd ore beside late sulfur.
 */
@Mixin(WorldGenRegion.class)
public abstract class WorldGenRegionMixin implements SulfurCaves.WriteZone {

    @Shadow @Final private ChunkStep generatingStep;

    @Inject(method = "setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;II)Z",
            at = @At("HEAD"), require = 0)
    private void seamlessores$clearOreBesideLateSulfur(BlockPos pos, BlockState state, int flags, int recursionLeft,
                                                       CallbackInfoReturnable<Boolean> cir) {
        final WorldGenRegion region = (WorldGenRegion) (Object) this;
        SulfurCaves.beforeWorldgenWrite(region, pos, state, this::seamlessores$canWrite);
    }

    /** The region's own write test, without the error it logs when the answer is no. */
    @Override
    public boolean seamlessores$canWrite(BlockPos target) {
        final ChunkPos center = ((WorldGenRegion) (Object) this).getCenter();
        final int radius = this.generatingStep.blockStateWriteRadius();
        return Math.abs(SectionPos.blockToSectionCoord(target.getX()) - center.x()) <= radius
                && Math.abs(SectionPos.blockToSectionCoord(target.getZ()) - center.z()) <= radius;
    }
}
