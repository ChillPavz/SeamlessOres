package com.chillpavz.seamlessores.worldgen.era261;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.worldgen.OreSite;
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
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.placement.CountPlacement;
import net.minecraft.world.level.levelgen.structure.templatesystem.AlwaysTrueTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockStateMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.TagMatchTest;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BiConsumer;
import java.util.function.UnaryOperator;

/**
 * Minecraft 26.1, 26.1.1, 26.1.2 and 26.2: feature types are {@code Feature} instances in
 * {@code FEATURE}, and the count placement keeps its provider in a field the access widener opens. A
 * feature's ore targets live in its configuration, so the CONFIGURED feature is rebuilt, around the
 * very same Feature instance, and rebound in {@code Registries.CONFIGURED_FEATURE}. Rebinding never
 * touches a placed feature, so the feature-order table stays valid.
 * Loaded by name from {@code Worldgen}; never named in shared code.
 */
public final class Era261 implements WorldgenEra {

    /** Seeded, and only handed to rule tests that never read it; see {@link #receives}. */
    private static final RandomSource UNUSED = RandomSource.create(0L);

    private static final AtomicBoolean LAYERED_FAILED = new AtomicBoolean();

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
    public List<OreSite> oreSites(RegistryAccess registries) {
        final Registry<ConfiguredFeature<?, ?>> features = registries.lookupOrThrow(Registries.CONFIGURED_FEATURE);
        final List<OreSite> sites = new ArrayList<>();
        // Collected first: the injectors rebind while iterating.
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
     * These versions have no all-of rule test, so the added target is a bare block match on the stone,
     * which is only right where the original target would have matched that stone anyway. So it is
     * asked, once, here: for the rule tests whose answer depends on the block alone. A random test (a
     * chance to match) is never evaluated, and never added.
     */
    @Override
    public boolean receives(RuleTest original, Block stone) {
        final boolean blockOnly = original instanceof TagMatchTest || original instanceof BlockMatchTest
                || original instanceof BlockStateMatchTest || original instanceof AlwaysTrueTest;
        return blockOnly && original.test(stone.defaultBlockState(), UNUSED);
    }

    @Override
    public void injectVeins(RegistryAccess registries) {
        // The large copper and iron veins are hard-coded in OreVeinifier, invisible to the registries.
        VeinOreInjector.inject();
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

    /**
     * Our rules as this era's targets, in order. A swallow rule is one target per form of the ore (first
     * match wins, so the result is the same); an ore side rule is a block match on the stone, once per
     * stone and result: without the original test, two of them would be the same target.
     */
    static List<OreConfiguration.TargetBlockState> targetsOf(List<OreSite.Rule> rules) {
        final List<OreConfiguration.TargetBlockState> out = new ArrayList<>();
        final Set<List<Block>> matched = new HashSet<>();
        for (OreSite.Rule rule : rules) {
            switch (rule) {
                case OreSite.Swallow swallow -> {
                    for (Block form : swallow.forms()) {
                        out.add(OreConfiguration.target(new BlockMatchTest(form), swallow.becomes().defaultBlockState()));
                    }
                }
                case OreSite.Receive receive -> stoneMatch(out, matched, receive.stone(), receive.becomes());
                case OreSite.Add add -> stoneMatch(out, matched, add.stone(), add.becomes());
            }
        }
        return out;
    }

    private static void stoneMatch(List<OreConfiguration.TargetBlockState> out, Set<List<Block>> matched,
                                   Block stone, Block becomes) {
        if (matched.add(List.of(stone, becomes))) {
            out.add(OreConfiguration.target(new BlockMatchTest(stone), becomes.defaultBlockState()));
        }
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
            final List<OreConfiguration.TargetBlockState> merged = targetsOf(rules);
            merged.addAll(current.targetStates);
            Feature<?> feature = holder.value().feature();
            if (bastionSafe && BastionSafeOreFeature.get() != null && feature == Feature.ORE) {
                feature = BastionSafeOreFeature.get();
            }
            rebind(holder, feature, new OreConfiguration(List.copyOf(merged), size, current.discardChanceOnAirExposure));
        }
    }
}
