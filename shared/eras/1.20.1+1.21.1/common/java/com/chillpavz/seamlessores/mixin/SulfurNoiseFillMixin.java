package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.levelgen.NoiseBasedChunkGenerator;
import net.minecraft.world.level.levelgen.NoiseChunk;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.blending.Blender;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Keeps the large copper and iron veins out of Vanilla Backport's Sulfur Caves. See {@link SulfurCaves}.
 *
 * <p>The veins are placed by the noise fill, and the surface rules that draw the sulfur and cinnabar
 * bands afterwards only rewrite the default block, so a vein's blocks would stay standing inside the
 * bands. A vein block bound for the biome becomes the default block before it is stored, at the last
 * call that sees each block with its position. The chunk is a parameter of {@code doFill}, not of that
 * call, so it is held for the thread while the fill runs. {@code require = 0}: a miss leaves the veins.
 */
@Mixin(NoiseBasedChunkGenerator.class)
public abstract class SulfurNoiseFillMixin {

    @Unique
    private static final ThreadLocal<ChunkAccess> seamlessores$filling = new ThreadLocal<>();

    @Inject(method = "doFill", at = @At("HEAD"), require = 0)
    private void seamlessores$holdChunk(Blender blender, StructureManager structures, RandomState random,
                                        ChunkAccess chunk, int minCellY, int cellCountY,
                                        CallbackInfoReturnable<ChunkAccess> cir) {
        seamlessores$filling.set(SulfurCaves.active() ? chunk : null);
    }

    @ModifyArg(method = "doFill",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/NoiseBasedChunkGenerator;debugPreliminarySurfaceLevel(Lnet/minecraft/world/level/levelgen/NoiseChunk;IIILnet/minecraft/world/level/block/state/BlockState;)Lnet/minecraft/world/level/block/state/BlockState;"),
            index = 4, require = 0)
    private BlockState seamlessores$keepVeinsOutOfSulfurCaves(NoiseChunk noise, int x, int y, int z, BlockState state) {
        if (SulfurCaves.keepsVeinOut(seamlessores$filling.get(), state, x, y, z)) {
            return ((NoiseBasedChunkGenerator) (Object) this).generatorSettings().value().defaultBlock();
        }
        return state;
    }
}
