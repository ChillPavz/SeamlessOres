package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.DripstoneShell;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderSet;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Lets the dripstone cluster's shell take the ore it wraps, from 26.2. See {@link DripstoneShell}.
 *
 * <p>{@code SpeleothemUtils} replaced {@code DripstoneUtils} at 26.2 and is shared with the sulfur
 * spikes, so only a dripstone base block is acted on. Named by string and {@code @Pseudo} because one
 * jar serves 26.1.x, where the class does not exist; {@link DripstoneUtilsMixin} covers that side.
 * {@code require = 0}: a missed injection leaves vanilla's seam, it must not stop the game.
 */
@Pseudo
@Mixin(targets = "net.minecraft.world.level.levelgen.feature.SpeleothemUtils")
public abstract class SpeleothemUtilsMixin {

    @Inject(method = "placeBaseBlockIfPossible(Lnet/minecraft/world/level/LevelAccessor;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/Block;Lnet/minecraft/core/HolderSet;)Z",
            at = @At("HEAD"), cancellable = true, require = 0)
    private static void seamlessores$dripstoneOre(LevelAccessor level, BlockPos pos, Block base,
                                                  HolderSet<Block> replaceable,
                                                  CallbackInfoReturnable<Boolean> cir) {
        if (base == Blocks.DRIPSTONE_BLOCK && DripstoneShell.swap(level, pos)) {
            cir.setReturnValue(false);
        }
    }
}
