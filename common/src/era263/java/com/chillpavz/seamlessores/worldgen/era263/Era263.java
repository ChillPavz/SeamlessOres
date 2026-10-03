package com.chillpavz.seamlessores.worldgen.era263;

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
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.placement.CountPlacement;

import java.util.Optional;
import java.util.function.BiConsumer;
import java.util.function.UnaryOperator;

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

    @Override
    @SuppressWarnings({"unchecked", "rawtypes"})
    public boolean rewriteFeature(RegistryAccess registries, Identifier id, UnaryOperator<JsonObject> edit) {
        final Optional<Holder.Reference<Feature>> holder =
                registries.lookupOrThrow(Registries.FEATURE).get(id);
        if (holder.isEmpty()) {
            return false;
        }
        final RegistryOps<JsonElement> ops = RegistryOps.create(JsonOps.INSTANCE, registries);
        final JsonElement json = Feature.DIRECT_CODEC.encodeStart(ops, holder.get().value()).getOrThrow();
        if (!json.isJsonObject()) {
            return false;
        }
        final JsonObject edited = edit.apply(json.getAsJsonObject().deepCopy());
        if (edited == null) {
            return false;
        }
        final Feature rebuilt = Feature.DIRECT_CODEC.parse(ops, edited).getOrThrow();
        // Rebinding the holder rather than the placed feature: the feature-order table indexes placed
        // feature instances, which stay the same objects, so nothing indexed goes stale.
        ((Holder.Reference) holder.get()).bindValue(rebuilt);
        return true;
    }
}
