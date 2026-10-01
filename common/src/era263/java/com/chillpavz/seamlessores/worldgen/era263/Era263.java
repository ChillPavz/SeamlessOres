package com.chillpavz.seamlessores.worldgen.era263;

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
 * Minecraft 26.3: a feature type is its codec, registered in {@code FEATURE_TYPE} (from 26.3
 * {@code FEATURE} holds the ore features themselves, as data), and the count placement is a record.
 * Loaded by name from {@code Worldgen}; never named in shared code.
 */
public final class Era263 implements WorldgenEra {

    @Override
    public String name() {
        return "Era263";
    }

    @Override
    public ResourceKey<? extends Registry<?>> featureTypeRegistry() {
        return Registries.FEATURE_TYPE;
    }

    @Override
    public Registry<?> builtInFeatureTypes() {
        return BuiltInRegistries.FEATURE_TYPE;
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
        return placement.count().maxInclusive();
    }
}
