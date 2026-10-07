package com.chillpavz.seamlessores.matrix.worldgen;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.templatesystem.AlwaysTrueTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockStateMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.TagMatchTest;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * The ore sites of 26.1.x and 26.2. Before 26.3 a feature's targets live in its configuration, so the
 * CONFIGURED feature is rebuilt, around the very same Feature instance, and rebound in
 * {@code Registries.CONFIGURED_FEATURE}. Rebinding never touches a placed feature, so the feature-order
 * table stays valid.
 *
 * <p>These versions have no any-of or all-of rule test, so the rules become plain block matches: a
 * swallow rule is one target per form of the ore (first match wins, so the result is the same), and a
 * receive rule is a block match on the stone, added only where the original target accepts that stone.
 *
 * <p>Loaded by name from {@link OreSites}, and only on these versions.
 */
final class Era261 implements OreSites.Era {

    Era261() {}

    /** Seeded, and only handed to rule tests that never read it; see {@link #receives}. */
    private static final RandomSource UNUSED = RandomSource.create(0L);

    private static final AtomicBoolean LAYERED_FAILED = new AtomicBoolean();

    /** Every ore site, freshly read: the other injector may have rebound some since the last call. */
    @Override
    public List<OreSite> find(RegistryAccess registries) {
        final Registry<ConfiguredFeature<?, ?>> features = registries.lookupOrThrow(Registries.CONFIGURED_FEATURE);
        final List<OreSite> sites = new ArrayList<>();
        // Collected first: we rebind while iterating.
        for (Holder.Reference<ConfiguredFeature<?, ?>> holder : features.listElements().toList()) {
            final Object config = holder.value().config();
            if (config instanceof OreConfiguration) {
                sites.add(new OreConfigurationSite(holder));
            } else if (LayeredOre.is(config) && !LAYERED_FAILED.get()) {
                // Fenced on its own: a Create that changed shape costs us its strata, not every other stone.
                try {
                    sites.addAll(LayeredOre.sites(holder));
                } catch (ReflectiveOperationException | RuntimeException e) {
                    LAYERED_FAILED.set(true);
                    Constants.LOG.error("Could not read Create's layered ore ({}); its strata keep vanilla-looking"
                            + " ore for this session", holder.key().identifier(), e);
                }
            }
        }
        return sites;
    }

    /**
     * Whether the ore side should add "this stone" next to {@code original}. Without an all-of test the
     * added target is a bare block match on the stone, which is only right where the original target
     * would have matched that stone anyway. So it is asked, once, here: for the rule tests whose answer
     * depends on the block alone. A random test (a chance to match) is never evaluated, and never added.
     */
    @Override
    public boolean receives(RuleTest original, Block stone) {
        final boolean blockOnly = original instanceof TagMatchTest || original instanceof BlockMatchTest
                || original instanceof BlockStateMatchTest || original instanceof AlwaysTrueTest;
        return blockOnly && original.test(stone.defaultBlockState(), UNUSED);
    }

    /** Our rules as this era's targets, in order. */
    static List<OreConfiguration.TargetBlockState> targetsOf(List<OreSite.Rule> rules) {
        final List<OreConfiguration.TargetBlockState> out = new ArrayList<>();
        for (OreSite.Rule rule : rules) {
            switch (rule) {
                case OreSite.Swallow swallow -> {
                    for (Block form : swallow.forms()) {
                        out.add(OreConfiguration.target(new BlockMatchTest(form), swallow.becomes().defaultBlockState()));
                    }
                }
                case OreSite.Receive receive -> out.add(OreConfiguration.target(
                        new BlockMatchTest(receive.stone()), receive.becomes().defaultBlockState()));
            }
        }
        return out;
    }

    /**
     * {@code bindValue} is protected in vanilla and opened by the access widener / transformer. Anything
     * holding this holder, the placed features included, reads through to the new value.
     */
    @SuppressWarnings({"unchecked", "rawtypes"})
    static void rebind(Holder.Reference<ConfiguredFeature<?, ?>> holder, FeatureConfiguration config) {
        final Feature<?> feature = holder.value().feature();
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

        /** Always: the Feature instance is kept as it is, whoever wrote it, and only its config changes. */
        @Override
        public boolean rebuildable(String injector) {
            return true;
        }

        @Override
        public void prepend(List<Rule> rules) {
            final OreConfiguration current = config();
            final List<OreConfiguration.TargetBlockState> merged = targetsOf(rules);
            merged.addAll(current.targetStates);
            rebind(holder, new OreConfiguration(List.copyOf(merged), current.size, current.discardChanceOnAirExposure));
        }
    }
}
