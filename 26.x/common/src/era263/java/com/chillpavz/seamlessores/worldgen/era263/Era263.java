package com.chillpavz.seamlessores.worldgen.era263;

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
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.AbstractOreFeature;
import net.minecraft.world.level.levelgen.feature.BlockReplacement;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.OreFeature;
import net.minecraft.world.level.levelgen.feature.ScatteredOreFeature;
import net.minecraft.world.level.levelgen.placement.CountPlacement;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.BiConsumer;
import java.util.function.UnaryOperator;

/**
 * Minecraft 26.3: a feature type is its codec, registered in {@code FEATURE_TYPE} (from 26.3
 * {@code FEATURE} holds the ore features themselves, as data), and the count placement is a record. An
 * ore feature carries its own targets: there is no ConfiguredFeature, and the feature itself is what
 * gets rebuilt and rebound in {@code Registries.FEATURE}.
 * Loaded by name from {@code Worldgen}; never named in shared code.
 */
public final class Era263 implements WorldgenEra {

    /** Mod subclasses already reported, so each is logged once per session rather than per world. */
    private static final Set<String> REPORTED = ConcurrentHashMap.newKeySet();

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
        CinnabarOreFeature.register(sink::accept);
    }

    @Override
    public List<OreSite> oreSites(RegistryAccess registries) {
        final Registry<Feature> features = registries.lookupOrThrow(Registries.FEATURE);
        final List<OreSite> sites = new ArrayList<>();
        // Collected first: the injectors rebind while iterating.
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

    @Override
    public void injectVeins(RegistryAccess registries) {
        // The large copper and iron veins are material rules, not features.
        VeinOreInjector.inject(registries);
        VeinOreInjector.keepOutOfSulfurCaves(registries);
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

    private record FeatureSite(Holder.Reference<Feature> holder, AbstractOreFeature ore) implements OreSite {

        @Override
        public String name() {
            return holder.key().identifier().toString();
        }

        @Override
        public List<Target> targets() {
            return ore.targetStates().stream().map(r -> new Target(r.target(), r.state())).toList();
        }

        @Override
        public int size() {
            return ore.size();
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
         * Rebinds the holder to the same kind of feature with the rules in FRONT of its own targets. A
         * plain ore feature that gained a Nether host becomes our bastion-safe stand-in, which declines to
         * convert a bastion's own blocks and otherwise places exactly what {@link OreFeature} would.
         *
         * <p>Rebinding a {@code Holder<Feature>} is safe after the feature-order table exists: the
         * PlacedFeature that owns this holder is untouched, so the table's key still matches. Rebinding
         * a PlacedFeature would not be. Never do that from here.
         */
        @Override
        @SuppressWarnings({"unchecked", "rawtypes"})
        public void rebuild(List<Rule> rules, int size, boolean bastionSafe) {
            final List<BlockReplacement> merged = new ArrayList<>();
            for (Rule rule : rules) {
                merged.add(replacement(rule));
            }
            merged.addAll(ore.targetStates());
            final List<BlockReplacement> targets = List.copyOf(merged);
            final float discard = ore.discardChanceOnAirExposure();
            final Feature rebuilt = ore.getClass() == ScatteredOreFeature.class
                    ? new ScatteredOreFeature(targets, size, discard)
                    : bastionSafe ? new BastionSafeOreFeature(targets, size, discard) : new OreFeature(targets, size, discard);
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
                case Add add -> new BlockReplacement(new BlockMatchTest(add.stone()), add.becomes().defaultBlockState());
            };
        }
    }
}
