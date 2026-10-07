package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.DripstoneShell;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.LevelAccessor;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Lets the dripstone cluster's shell take the ore it wraps, on 26.1.x. See {@link DripstoneShell}.
 *
 * <p>{@code DripstoneUtils} is gone from 26.2 (see {@link SpeleothemUtilsMixin}), hence the string
 * target and {@code @Pseudo}. {@code require = 0}: a missed injection leaves vanilla's seam, it must
 * not stop the game.
 */
@Pseudo
@Mixin(targets = "net.minecraft.world.level.levelgen.feature.DripstoneUtils")
public abstract class DripstoneUtilsMixin {

    @Inject(method = "placeDripstoneBlockIfPossible(Lnet/minecraft/world/level/LevelAccessor;Lnet/minecraft/core/BlockPos;)Z",
            at = @At("HEAD"), cancellable = true, require = 0)
    private static void seamlessores$dripstoneOre(LevelAccessor level, BlockPos pos,
                                                  CallbackInfoReturnable<Boolean> cir) {
        if (DripstoneShell.swap(level, pos)) {
            cir.setReturnValue(false);
        }
    }
}
