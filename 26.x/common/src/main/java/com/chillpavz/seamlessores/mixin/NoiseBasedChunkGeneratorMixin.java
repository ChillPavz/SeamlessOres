package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.levelgen.NoiseBasedChunkGenerator;
import net.minecraft.world.level.levelgen.NoiseChunk;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

/**
 * Keeps the large copper and iron veins out of the Sulfur Caves on 26.2. See {@link SulfurCaves}.
 *
 * <p>Up to 26.2 the veins are placed by the noise fill, and the surface pass that draws the sulfur and
 * cinnabar bands afterwards only rewrites the default block, so a vein's blocks stay standing inside
 * the bands. Here a vein block bound for the biome becomes the default block before it is stored,
 * and the bands then treat it like the rest of the cave. The hook is the last call that sees each
 * block with its position, the same on 26.1.x and 26.2. From 26.3 the veins are material rules and
 * the era code wraps them instead; {@link SeamlessOresMixinPlugin} skips this there.
 * {@code require = 0}: a miss leaves the veins as vanilla builds them.
 *
 * <p>PRIORITY 1200, above C2ME's OpenCL acceleration (1100), which overwrites {@code doFill} (GitHub issue #5).
 * Mixin refuses, fatally and whatever {@code require} says, to inject into a method a mixin of HIGHER priority has
 * overwritten; it allows it from above. From above, the call wrapped here is not in the replacement, the
 * {@code require = 0} miss applies, and the game starts; {@link com.chillpavz.seamlessores.worldgen.NoiseFillReplacement}
 * says once, at world start, that the veins are not kept out while the acceleration is on.
 */
@Mixin(value = NoiseBasedChunkGenerator.class, priority = 1200)
public abstract class NoiseBasedChunkGeneratorMixin {


    @WrapOperation(method = "doFill",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/NoiseBasedChunkGenerator;debugPreliminarySurfaceLevel(Lnet/minecraft/world/level/levelgen/NoiseChunk;IIILnet/minecraft/world/level/block/state/BlockState;)Lnet/minecraft/world/level/block/state/BlockState;"),
            require = 0)
    private BlockState seamlessores$keepVeinsOutOfSulfurCaves(NoiseBasedChunkGenerator self, NoiseChunk noise,
                                                              int x, int y, int z, BlockState state,
                                                              Operation<BlockState> original,
                                                              @Local(argsOnly = true) ChunkAccess chunk) {
        if (SulfurCaves.keepsVeinOut(chunk, state, x, y, z)) {
            state = self.generatorSettings().value().defaultBlock();
        }
        return original.call(self, noise, x, y, z, state);
    }
}
