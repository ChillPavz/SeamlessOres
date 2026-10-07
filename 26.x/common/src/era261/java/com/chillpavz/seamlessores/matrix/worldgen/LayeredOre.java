package com.chillpavz.seamlessores.matrix.worldgen;

import net.minecraft.core.Holder;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;

import java.util.ArrayList;
import java.util.List;

/**
 * Create's strata: one {@code create:layered_ore} feature per dimension, read and rebuilt by
 * reflection, because this mod never compiles against Create.
 *
 * <p>Its configuration is a list of layer patterns; each pattern a list of layers; each layer a list of
 * block lists, of which one is rolled per layer. A block list is exactly an ore target list (the same
 * {@code OreConfiguration.TargetBlockState}, first match wins, checked in LayeredOreFeature.place), so
 * each one is an {@link OreSite} of its own: the one that lays down scoria gets the scoria rules.
 *
 * <p>Matched by class NAME, not package, so Create for NeoForge would be recognised too. Every field
 * and constructor used is public; the shapes were read from the Create Fly 26.1.2 and 26.2 jars:
 * {@code LayeredOreConfiguration(List layerPatterns, int size, float discardChanceOnAirExposure)},
 * {@code LayerPattern(List layers)},
 * {@code LayerPattern.Layer(List<List<TargetBlockState>> targets, int minSize, int maxSize, int weight)}.
 * Plain final fields, so the lists read here are the ones rebuilt, not fresh copies.
 */
final class LayeredOre {

    private LayeredOre() {}

    static boolean is(Object config) {
        return config.getClass().getSimpleName().equals("LayeredOreConfiguration");
    }

    /** One site per block list of every layer, in order. */
    static List<OreSite> sites(Holder.Reference<ConfiguredFeature<?, ?>> holder) throws ReflectiveOperationException {
        final Object config = holder.value().config();
        final List<OreSite> sites = new ArrayList<>();
        final List<?> patterns = (List<?>) field(config, "layerPatterns");
        for (int p = 0; p < patterns.size(); p++) {
            final List<?> layers = (List<?>) field(patterns.get(p), "layers");
            for (int l = 0; l < layers.size(); l++) {
                final List<?> lists = (List<?>) field(layers.get(l), "targets");
                for (int b = 0; b < lists.size(); b++) {
                    sites.add(new LayerSite(holder, p, l, b, targetsAt(config, p, l, b)));
                }
            }
        }
        return sites;
    }

    @SuppressWarnings("unchecked")
    private static List<OreConfiguration.TargetBlockState> targetsAt(Object config, int p, int l, int b)
            throws ReflectiveOperationException {
        final Object pattern = ((List<?>) field(config, "layerPatterns")).get(p);
        final Object layer = ((List<?>) field(pattern, "layers")).get(l);
        return (List<OreConfiguration.TargetBlockState>) ((List<?>) field(layer, "targets")).get(b);
    }

    /**
     * The whole configuration rebuilt with {@code extra} in front of one block list. Everything else is
     * carried over as it is, so two sites of the same feature can be patched one after the other.
     */
    private static Object rebuilt(Object config, int p, int l, int b, List<OreConfiguration.TargetBlockState> extra)
            throws ReflectiveOperationException {
        final List<Object> patterns = new ArrayList<>((List<?>) field(config, "layerPatterns"));
        final Object pattern = patterns.get(p);
        final List<Object> layers = new ArrayList<>((List<?>) field(pattern, "layers"));
        final Object layer = layers.get(l);
        final List<Object> lists = new ArrayList<>((List<?>) field(layer, "targets"));
        final List<Object> merged = new ArrayList<>(extra);
        merged.addAll((List<?>) lists.get(b));
        lists.set(b, List.copyOf(merged));

        layers.set(l, layer.getClass().getConstructor(List.class, int.class, int.class, int.class).newInstance(
                List.copyOf(lists), field(layer, "minSize"), field(layer, "maxSize"), field(layer, "weight")));
        patterns.set(p, pattern.getClass().getConstructor(List.class).newInstance(List.copyOf(layers)));
        return config.getClass().getConstructor(List.class, int.class, float.class).newInstance(
                List.copyOf(patterns), field(config, "size"), field(config, "discardChanceOnAirExposure"));
    }

    private static Object field(Object owner, String name) throws ReflectiveOperationException {
        return owner.getClass().getField(name).get(owner);
    }

    private record LayerSite(Holder.Reference<ConfiguredFeature<?, ?>> holder, int pattern, int layer, int list,
                             List<OreConfiguration.TargetBlockState> own) implements OreSite {

        @Override
        public String name() {
            return holder.key().identifier() + " layer " + pattern + "." + layer + "." + list;
        }

        @Override
        public List<Target> targets() {
            return own.stream().map(t -> new Target(t.target, t.state)).toList();
        }

        @Override
        public boolean rebuildable(String injector) {
            return true;
        }

        /** Reads the CURRENT configuration, so a site patched before this one in the same feature is kept. */
        @Override
        public void prepend(List<Rule> rules) {
            try {
                final Object config = rebuilt(holder.value().config(), pattern, layer, list, Era261.targetsOf(rules));
                Era261.rebind(holder, (FeatureConfiguration) config);
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException("could not rebuild " + name(), e);
            }
        }
    }
}
