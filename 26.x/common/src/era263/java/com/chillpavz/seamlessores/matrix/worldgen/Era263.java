package com.chillpavz.seamlessores.matrix.worldgen;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.AbstractOreFeature;
import net.minecraft.world.level.levelgen.feature.BlockReplacement;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.OreFeature;
import net.minecraft.world.level.levelgen.feature.ScatteredOreFeature;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 26.3's ore sites. From 26.3 an ore feature carries its own targets: there is no ConfiguredFeature,
 * and the feature itself is what gets rebuilt and rebound in {@code Registries.FEATURE}.
 *
 * <p>Loaded by name from {@link OreSites}, and only on 26.3.
 */
final class Era263 implements OreSites.Era {

    Era263() {}

    /** Mod subclasses already reported, so each is logged once per session rather than per world. */
    private static final Set<String> REPORTED = ConcurrentHashMap.newKeySet();

    /** Every ore feature, freshly read: the other injector may have rebound some since the last call. */
    @Override
    public List<OreSite> find(RegistryAccess registries) {
        final Registry<Feature> features = registries.lookupOrThrow(Registries.FEATURE);
        final List<OreSite> sites = new ArrayList<>();
        // Collected first: we rebind while iterating.
        for (Holder.Reference<Feature> holder : features.listElements().toList()) {
            if (holder.value() instanceof AbstractOreFeature ore) {
                sites.add(new FeatureSite(holder, ore));
            }
        }
        return sites;
    }

    /** 26.3 can say "the original target AND this stone" directly, so every pair is worth adding. */
    @Override
    public boolean receives(RuleTest original, Block stone) {
        return true;
    }

    private record FeatureSite(Holder.Reference<Feature> holder, AbstractOreFeature ore) implements OreSite {

        @Override
        public String name() {
            return holder.key().identifier().toString();
        }

        @Override
        public List<Target> targets() {
            return ore.targetStates().stream().map(r -> new Target(r.target(), r.state())).toList();
        }

        /**
         * True for exactly vanilla's two ore classes. A mod's own AbstractOreFeature subclass may carry
         * state or a constructor contract we cannot reproduce, so it is left alone, and said so once.
         */
        @Override
        public boolean rebuildable(String injector) {
            final Class<?> kind = ore.getClass();
            if (kind == OreFeature.class || kind == ScatteredOreFeature.class) {
                return true;
            }
            if (REPORTED.add(injector + " " + kind.getName())) {
                Constants.LOG.info("{}: left {} alone, it is not a vanilla ore feature", injector, kind.getName());
            }
            return false;
        }

        /**
         * Rebinds the holder to the same kind of feature with the rules in FRONT of its own targets.
         *
         * <p>Rebinding a {@code Holder<Feature>} is safe after the feature-order table exists: the
         * PlacedFeature that owns this holder is untouched, so the table's key still matches. Rebinding
         * a PlacedFeature would not be. Never do that from here.
         */
        @Override
        @SuppressWarnings({"unchecked", "rawtypes"})
        public void prepend(List<Rule> rules) {
            final List<BlockReplacement> merged = new ArrayList<>();
            for (Rule rule : rules) {
                merged.add(replacement(rule));
            }
            merged.addAll(ore.targetStates());
            final Feature rebuilt = ore.getClass() == ScatteredOreFeature.class
                    ? new ScatteredOreFeature(List.copyOf(merged), ore.size(), ore.discardChanceOnAirExposure())
                    : new OreFeature(List.copyOf(merged), ore.size(), ore.discardChanceOnAirExposure());
            // bindValue is protected in vanilla; opened by the access widener / access transformer.
            ((Holder.Reference) holder).bindValue(rebuilt);
        }

        private static BlockReplacement replacement(Rule rule) {
            return switch (rule) {
                case Swallow swallow -> {
                    final List<RuleTest> tests = swallow.forms().stream()
                            .<RuleTest>map(BlockMatchTest::new).toList();
                    yield new BlockReplacement(tests.size() == 1 ? tests.get(0) : RuleTest.anyOf(tests),
                            swallow.becomes().defaultBlockState());
                }
                case Receive receive -> new BlockReplacement(
                        RuleTest.allOf(receive.original(), new BlockMatchTest(receive.stone())),
                        receive.becomes().defaultBlockState());
            };
        }
    }
}
