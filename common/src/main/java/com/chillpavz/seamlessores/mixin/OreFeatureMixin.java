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
 * Stops an ore feature placing ore against sulfur or cinnabar, up to 26.2. See {@link SulfurCaves}.
 *
 * <p>{@code OreFeature.canPlaceOre} is the one check both the ore and the scattered ore feature make
 * for every block. It is static here and became an instance method of {@code AbstractOreFeature} at
 * 26.3, which {@link AbstractOreFeatureMixin} covers; {@link SeamlessOresMixinPlugin} applies only the
 * one the running game has. Only a {@code true} answer is checked, so the cost is six block reads per
 * ore block actually placed. The arguments are taken by type, because the configuration types in the
 * signature differ between the two eras. {@code require = 0}: a miss leaves vanilla's ore in place.
 */
@Pseudo
@Mixin(targets = "net.minecraft.world.level.levelgen.feature.OreFeature")
public abstract class OreFeatureMixin {

    @Inject(method = "canPlaceOre", at = @At("RETURN"), cancellable = true, require = 0)
    private static void seamlessores$keepOutOfSulfur(CallbackInfoReturnable<Boolean> cir,
                                                     @Local(argsOnly = true) Function<BlockPos, BlockState> level,
                                                     @Local(argsOnly = true) BlockPos.MutableBlockPos pos) {
        if (cir.getReturnValueZ() && SulfurCaves.keepsOreOut(level, pos)) {
            cir.setReturnValue(false);
        }
    }
}
