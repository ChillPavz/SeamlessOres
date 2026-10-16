package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.OreFeature;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.function.Function;

/**
 * Stops an ore feature placing ore against sulfur or cinnabar in Vanilla Backport's Sulfur Caves. See
 * {@link SulfurCaves}. {@code OreFeature.canPlaceOre} is the one check both the ore and the scattered
 * ore feature make for every block, so only a {@code true} answer is checked: six block reads per ore
 * block actually placed, none while the biome is absent. {@code require = 0}: a miss leaves the ore.
 */
@Mixin(OreFeature.class)
public abstract class SulfurOreFeatureMixin {

    @Inject(method = "canPlaceOre", at = @At("RETURN"), cancellable = true, require = 0)
    private static void seamlessores$keepOutOfSulfur(BlockState replaced, Function<BlockPos, BlockState> level,
                                                     RandomSource random, OreConfiguration config,
                                                     OreConfiguration.TargetBlockState target,
                                                     BlockPos.MutableBlockPos pos, CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValueZ() && SulfurCaves.keepsOreOut(replaced, level, pos)) {
            cir.setReturnValue(false);
        }
    }
}
