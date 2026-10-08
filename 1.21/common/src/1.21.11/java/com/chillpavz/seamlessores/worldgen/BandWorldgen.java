package com.chillpavz.seamlessores.worldgen;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.serialization.JsonOps;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.RegistryOps;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.UnaryOperator;

/**
 * Minecraft 1.21.11: a feature's ore targets live in its configuration, so the CONFIGURED feature is
 * rebuilt, around the very same Feature instance, and rebound in {@code Registries.CONFIGURED_FEATURE}.
 * Rebinding never touches a placed feature, so the feature-order table stays valid.
 */
final class BandWorldgen implements WorldgenEra {

    @Override
    public List<OreSite> oreSites(RegistryAccess registries) {
        final Registry<ConfiguredFeature<?, ?>> features = registries.lookupOrThrow(Registries.CONFIGURED_FEATURE);
        final List<OreSite> sites = new ArrayList<>();
        // Collected first: the injectors rebind while iterating.
        for (Holder.Reference<ConfiguredFeature<?, ?>> holder : features.listElements().toList()) {
            if (holder.value().config() instanceof OreConfiguration) {
                sites.add(new OreConfigurationSite(holder));
            } else if (LayeredOre.is(holder.value().config())) {
                // Create's strata: a site per block list of every layer.
                LayeredOre.addSites(holder, holder.key().identifier().toString(), sites);
            }
        }
        return sites;
    }

    @Override
    public boolean receives(RuleTest original, Block stone) {
        return OreTargets.receives(original, stone);
    }

    @Override
    @SuppressWarnings({"unchecked", "rawtypes"})
    public boolean rewriteFeature(RegistryAccess registries, String path, UnaryOperator<JsonObject> edit) {
        final Optional<Holder.Reference<ConfiguredFeature<?, ?>>> holder =
                registries.lookupOrThrow(Registries.CONFIGURED_FEATURE).get(Identifier.withDefaultNamespace(path));
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

    /**
     * Swaps the value behind a configured feature. {@code bindValue} is protected in vanilla and opened
     * by the access widener / transformer. Anything holding this holder, the placed features included,
     * reads through to the new value.
     */
    @SuppressWarnings({"unchecked", "rawtypes"})
    static void rebind(Holder.Reference<ConfiguredFeature<?, ?>> holder, Feature<?> feature, FeatureConfiguration config) {
        ((Holder.Reference) holder).bindValue(new ConfiguredFeature((Feature) feature, config));
    }

    /** Any feature configured with an OreConfiguration, vanilla's or a mod's: only the config is rebuilt. */
    private record OreConfigurationSite(Holder.Reference<ConfiguredFeature<?, ?>> holder) implements OreSite {

        private OreConfiguration config() {
            return (OreConfiguration) holder.value().config();
        }

        @Override
        public String name() {
            return holder.key().identifier().toString();
        }

        @Override
        public List<Target> targets() {
            return config().targetStates.stream().map(t -> new Target(t.target, t.state)).toList();
        }

        @Override
        public int size() {
            return config().size;
        }

        /** Always: the Feature instance is kept as it is, whoever wrote it, and only its config changes. */
        @Override
        public boolean rebuildable(String injector) {
            return true;
        }

        /**
         * A feature that gained a Nether host gets our stand-in for minecraft:ore, so it can decline to
         * convert a bastion's own blocks. It takes the same OreConfiguration and delegates straight back
         * to Feature.ORE everywhere else, so nothing about the distribution changes; see
         * BastionSafeOreFeature.
         */
        @Override
        public void rebuild(List<Rule> rules, int size, boolean bastionSafe) {
            final OreConfiguration current = config();
            final List<OreConfiguration.TargetBlockState> merged = OreTargets.targetsOf(rules);
            merged.addAll(current.targetStates);
            Feature<?> feature = holder.value().feature();
            if (bastionSafe && BastionSafeOreFeature.get() != null && feature == Feature.ORE) {
                feature = BastionSafeOreFeature.get();
            }
            rebind(holder, feature, new OreConfiguration(List.copyOf(merged), size, current.discardChanceOnAirExposure));
        }
    }
}
