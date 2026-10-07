package com.chillpavz.seamlessores.worldgen.era261;

import com.chillpavz.seamlessores.worldgen.WorldgenEra;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.serialization.JsonOps;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.placement.CountPlacement;

import java.util.Optional;
import java.util.function.BiConsumer;
import java.util.function.UnaryOperator;

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
        CinnabarOreFeature.register(sink::accept);
    }

    @Override
    public void injectOreTargets(RegistryAccess registries) {
        OreTargetInjector.inject(registries);
        VeinOreInjector.shareWithSulfurCaves();
    }

    @Override
    public int maxCount(CountPlacement placement) {
        // A plain class here with a private final IntProvider field, opened by the access widener and
        // transformer. Its count(RandomSource, BlockPos) method is something else entirely.
        return placement.count.maxInclusive();
    }

    @Override
    @SuppressWarnings({"unchecked", "rawtypes"})
    public boolean rewriteFeature(RegistryAccess registries, Identifier id, UnaryOperator<JsonObject> edit) {
        final Optional<Holder.Reference<ConfiguredFeature<?, ?>>> holder =
                registries.lookupOrThrow(Registries.CONFIGURED_FEATURE).get(id);
        if (holder.isEmpty()) {
            return false;
        }
        final RegistryOps<JsonElement> ops = RegistryOps.create(JsonOps.INSTANCE, registries);
        final JsonElement json = ConfiguredFeature.DIRECT_CODEC.encodeStart(ops, holder.get().value()).getOrThrow();
        if (!json.isJsonObject()) {
            return false;
        }
        final JsonObject edited = edit.apply(json.getAsJsonObject().deepCopy());
        if (edited == null) {
            return false;
        }
        final ConfiguredFeature<?, ?> rebuilt = ConfiguredFeature.DIRECT_CODEC.parse(ops, edited).getOrThrow();
        // Rebinding the holder rather than the placed feature: the feature-order table indexes placed
        // feature instances, which stay the same objects, so nothing indexed goes stale.
        ((Holder.Reference) holder.get()).bindValue(rebuilt);
        return true;
    }
}
