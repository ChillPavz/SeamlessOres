package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.platform.Services;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.serialization.JsonOps;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceLocation;
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
 * Minecraft 1.21.1: a feature's ore targets live in its configuration, so the CONFIGURED feature is
 * rebuilt, around the very same Feature instance, and rebound in {@code Registries.CONFIGURED_FEATURE}.
 * Rebinding never touches a placed feature, so the feature-order table stays valid.
 */
final class BandWorldgen implements WorldgenEra {

    @Override
    public List<OreSite> oreSites(RegistryAccess registries) {
        final Registry<ConfiguredFeature<?, ?>> features = registries.registryOrThrow(Registries.CONFIGURED_FEATURE);
        final List<OreSite> sites = new ArrayList<>();
        int foreign = 0;
        // Collected first: the injectors rebind while iterating.
        for (Holder.Reference<ConfiguredFeature<?, ?>> holder : features.holders().toList()) {
            final FeatureConfiguration config = holder.value().config();
            if (config instanceof OreConfiguration) {
                sites.add(new OreConfigurationSite(holder));
            } else if (LayeredOre.is(config)) {
                // Create's strata, and TFMG's on Create's feature: a site per block list of every layer.
                LayeredOre.addSites(holder, holder.key().location().toString(), sites);
            } else if (rebuildsForeign(config)) {
                // Another mod's own configuration type around vanilla's target list: Immersive
                // Engineering's and Mekanism's. See ForeignOreTargets for what is accepted there.
                sites.add(new ForeignSite(holder));
                foreign++;
            }
        }
        // Immersive Engineering's ore features are not minecraft:ore, and ForeignOreTargets keys on the
        // name of its config class. If the mod is installed, its variants are switched on and NOTHING of
        // its could be read, that support has silently stopped working - an upstream rename would do it -
        // and its blocks would exist but never generate. Say so once. Sabotage test: take IE's class name
        // out of ForeignOreTargets.SUPPORTED.
        if (foreign == 0
                && Services.PLATFORM.isModLoaded("immersiveengineering")
                && SeamlessOresConfig.isModOreEnabled("immersiveengineering", false)) {
            Constants.LOG.warn("Worldgen: Immersive Engineering is installed but none of its ore "
                    + "features could be extended, so its seamless variants will not generate. "
                    + "Everything else is unaffected.");
        }
        return sites;
    }

    /**
     * Whether a foreign configuration can be read AND rebuilt: a dry run with its own list, so a site
     * whose rebuild would fail is never offered (it logs once, in ForeignOreTargets, and stays as it is).
     */
    private static boolean rebuildsForeign(FeatureConfiguration config) {
        final List<OreConfiguration.TargetBlockState> own = ForeignOreTargets.read(config);
        return own != null && ForeignOreTargets.withTargets(config, own) != null;
    }

    @Override
    public boolean receives(RuleTest original, Block stone) {
        return OreTargets.receives(original, stone);
    }

    @Override
    @SuppressWarnings({"unchecked", "rawtypes"})
    public boolean rewriteFeature(RegistryAccess registries, String path, UnaryOperator<JsonObject> edit) {
        final Optional<Holder.Reference<ConfiguredFeature<?, ?>>> holder =
                registries.registryOrThrow(Registries.CONFIGURED_FEATURE).getHolder(ResourceLocation.withDefaultNamespace(path));
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

    /** The same target list kept in another mod's configuration type (see ForeignOreTargets). */
    private record ForeignSite(Holder.Reference<ConfiguredFeature<?, ?>> holder) implements OreSite {

        @Override
        public String name() {
            return holder.key().location().toString();
        }

        @Override
        public List<Target> targets() {
            final List<OreConfiguration.TargetBlockState> own = ForeignOreTargets.read(holder.value().config());
            return own == null ? List.of() : own.stream().map(t -> new Target(t.target, t.state)).toList();
        }

        /** The mod computes its own size from its server config; never resized here. */
        @Override
        public int size() {
            return 0;
        }

        @Override
        public boolean rebuildable(String injector) {
            return true;
        }

        @Override
        public boolean foreign() {
            return true;
        }

        /** Only the rules apply: the size is the mod's, and no foreign ore we support reaches the Nether. */
        @Override
        public void rebuild(List<Rule> rules, int size, boolean bastionSafe) {
            final FeatureConfiguration config = holder.value().config();
            final List<OreConfiguration.TargetBlockState> merged = OreTargets.targetsOf(rules);
            final List<OreConfiguration.TargetBlockState> own = ForeignOreTargets.read(config);
            if (own == null) {
                return;
            }
            merged.addAll(own);
            final FeatureConfiguration replacement = ForeignOreTargets.withTargets(config, List.copyOf(merged));
            if (replacement != null) {
                rebind(holder, holder.value().feature(), replacement);
            }   // else logged once in there; the feature is left exactly as it was
        }
    }
}
