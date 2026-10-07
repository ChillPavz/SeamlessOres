package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import com.llamalad7.mixinextras.sugar.Local;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.function.Function;

/**
 * The 26.3 side of {@link OreFeatureMixin}: there {@code canPlaceOre} is an instance method of
 * {@code AbstractOreFeature}, the parent of the ore and the scattered ore feature. Named by string and
 * {@code @Pseudo} because the class does not exist before 26.3.
 */
@Pseudo
@Mixin(targets = "net.minecraft.world.level.levelgen.feature.AbstractOreFeature")
public abstract class AbstractOreFeatureMixin {

    @Inject(method = "canPlaceOre", at = @At("RETURN"), cancellable = true, require = 0)
    private void seamlessores$keepOutOfSulfur(CallbackInfoReturnable<Boolean> cir,
                                              @Local(argsOnly = true) BlockState replaced,
                                              @Local(argsOnly = true) Function<BlockPos, BlockState> level,
                                              @Local(argsOnly = true) BlockPos.MutableBlockPos pos) {
        if (cir.getReturnValueZ() && SulfurCaves.keepsOreOut(replaced, level, pos)) {
            cir.setReturnValue(false);
        }
    }
}
