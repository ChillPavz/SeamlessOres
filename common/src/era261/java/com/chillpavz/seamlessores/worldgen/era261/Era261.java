package com.chillpavz.seamlessores.worldgen.era261;

import com.chillpavz.seamlessores.worldgen.WorldgenEra;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.placement.CountPlacement;

import java.util.function.BiConsumer;

/**
 * Minecraft 26.1, 26.1.1, 26.1.2 and 26.2: feature types are {@code Feature} instances in
 * {@code FEATURE}, and the count placement keeps its provider in a field the access widener opens.
 * Loaded by name from {@code Worldgen}; never named in shared code.
 */
public final class Era261 implements WorldgenEra {

    @Override
    public String name() {
        return "Era261";
    }

    @Override
    public ResourceKey<? extends Registry<?>> featureTypeRegistry() {
        return Registries.FEATURE;
    }

    @Override
    public Registry<?> builtInFeatureTypes() {
        return BuiltInRegistries.FEATURE;
    }

    @Override
    public void registerFeatureTypes(BiConsumer<Identifier, Object> sink) {
        BastionSafeOreFeature.register(sink::accept);
        NetherGemFeature.register(sink::accept);
    }

    @Override
    public void injectOreTargets(RegistryAccess registries) {
        OreTargetInjector.inject(registries);
    }

    @Override
    public int maxCount(CountPlacement placement) {
        // A plain class here with a private final IntProvider field, opened by the access widener and
        // transformer. Its count(RandomSource, BlockPos) method is something else entirely.
        return placement.count.maxInclusive();
    }
}
