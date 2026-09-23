package com.chillpavz.seamlessores.mixin;

import com.chillpavz.seamlessores.worldgen.CopperDensityInjector;
import net.minecraft.core.Holder;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeGenerationSettings;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.chunk.ChunkGenerator;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.function.Function;

/**
 * Thins vanilla's copper in the one window where it is safe to: just before the feature-order table
 * is built.
 *
 * <h2>Why this is a mixin and not another server-start hook</h2>
 * {@link CopperDensityInjector} lowers copper's vein count by rebinding the registry entry to a
 * <b>new</b> {@code PlacedFeature}, because {@code PlacedFeature} is a record and its placement list
 * cannot be edited in place. That is fine as long as nothing has already indexed the old instance.
 *
 * <p>Something has. {@code ChunkGenerator} holds {@code featuresPerStep}, a memoized
 * {@code Supplier} of {@code FeatureSorter.StepFeatureData}, and each of those is a list of placed
 * features plus a {@code ToIntFunction} mapping a placed feature back to its index in that list. At
 * 26.3 that mapping is backed by a <b>{@code Reference2IntMap}</b>, so it is keyed on the placed
 * feature's <b>object identity</b>. Rebinding the holder afterwards leaves the table holding the old
 * instance while the biome now dereferences the new one, the lookup misses, the map returns its
 * default of -1, and {@code applyBiomeDecoration} does {@code features.get(-1)}:
 *
 * <pre>
 * net.minecraft.ReportedException: Biome decoration
 * Caused by: java.lang.IndexOutOfBoundsException: Index -1 out of bounds for length 34
 *     at ChunkGenerator.applyBiomeDecoration(ChunkGenerator.java:390)
 * </pre>
 *
 * <p><b>The trigger is adding the mod to a world created without it</b>, on the shipped defaults
 * (copper 75, dripstone 50). {@code ChunkGenerator.validate()} exists only to force that supplier,
 * and for an existing world it runs while the level is being read, i.e. before the server-start hook
 * the injectors used to run from. A world created with the mod already present orders the two the
 * other way round, which is why this never showed up in testing.
 * Reproduced on Fabric 26.3 (`_tools/client-harness/envs/26.3/harness-so-control-fabric.log`).
 *
 * <p>So the thinning moves to the head of {@code validate()}. The table is then built from the
 * instances we already put in place, and no stale entry can exist. Nothing else this mod does needs
 * it: {@code OreTargetInjector} rebinds {@code Holder<Feature>} values, which leaves the owning
 * {@code PlacedFeature} instance untouched, and {@code VeinOreInjector} works on
 * {@code Registries.MATERIAL_RULE}, which the feature table never sees.
 *
 * <p><b>Do not move this back to server start on any branch.</b> 26.1.2 and 26.2 have the same
 * {@code StepFeatureData} shape and the same {@code features.get(index)}, so the mechanism is there
 * too; only the map is {@code Object2IntMap}, and a value lookup misses just as surely because the
 * whole point of the rebind is that the count differs.
 */
@Mixin(ChunkGenerator.class)
public abstract class ChunkGeneratorMixin {

    @Shadow @Final protected BiomeSource biomeSource;

    /**
     * The generator's own settings lookup rather than {@code Biome#getGenerationSettings}, because
     * this is the exact function {@code FeatureSorter} is about to be handed: on NeoForge biome
     * modifiers replace a biome's generation settings through it, so reading the biome directly
     * would thin a list the table is not built from.
     */
    @Shadow @Final private Function<Holder<Biome>, BiomeGenerationSettings> generationSettingsGetter;

    /**
     * Runs for every dimension's generator, and more than once per session. The injector is
     * idempotent per placed-feature instance, so the repeats are no-ops rather than compounding
     * thinning; see {@code CopperDensityInjector}.
     */
    @Inject(method = "validate", at = @At("HEAD"))
    private void seamlessores$thinCopperBeforeFeatureTable(CallbackInfo ci) {
        CopperDensityInjector.thinBeforeFeatureTable(this.biomeSource, this.generationSettingsGetter);
    }
}
