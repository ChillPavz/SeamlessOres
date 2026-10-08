package com.chillpavz.seamlessores.worldgen;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.ArrayList;
import java.util.List;

/**
 * Minecraft 1.21.4: a feature's ore targets live in its configuration, so the CONFIGURED feature is
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
            }
        }
        return sites;
    }

    @Override
    public boolean receives(RuleTest original, Block stone) {
        return OreTargets.receives(original, stone);
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
            return holder.key().location().toString();
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
