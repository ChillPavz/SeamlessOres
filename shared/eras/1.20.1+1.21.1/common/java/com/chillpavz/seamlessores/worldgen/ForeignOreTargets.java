package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.mojang.serialization.JsonOps;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.lang.reflect.Constructor;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.RecordComponent;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Reads and rewrites the ore target list of a feature configuration that is NOT vanilla's
 * {@link OreConfiguration}.
 *
 * <h2>Why this exists</h2>
 * {@link OreSideInjector} works by extending the target list of the ore features that already
 * exist, which assumes those features carry an {@code OreConfiguration}. Almost every mod's ore
 * does. <b>Immersive Engineering's does not:</b> its features are
 * {@code immersiveengineering:ie_ore}, configured by IE's own record
 * {@code IEOreFeature$IEOreFeatureConfig(List<TargetBlockState> targetList, VeinType type)}, which
 * keeps vanilla's target states inside a config type of its own so that the vein size, the count
 * and the height range can come from IE's server config rather than from the JSON.
 *
 * <p>Read from its jar rather than assumed: {@code IEOreFeature.place} builds a plain
 * {@code OreConfiguration(targetList, getSize(), getAirExposure())} and hands it to
 * {@code Feature.ORE}. So the list means exactly what it means in vanilla, first match wins, and
 * prepending our host-matched entries changes which texture a position gets and nothing else.
 *
 * <h2>Why it is an allowlist rather than "any config with a target list"</h2>
 * A config type we have not read is a config type whose list we do not know the meaning of: another
 * mod could pick from it at random, or use it as a filter rather than a substitution table, and our
 * entries would then change how much ore exists. Adding a mod here means reading its feature first.
 * The cost of the allowlist is that a rename upstream silently stops the support working, which is
 * why BandWorldgen warns when the mod is present and nothing of its was patched.
 *
 * <p>Everything here is reflection, so no mod is ever on our compile classpath, and everything is
 * guarded: a failure disables the foreign path for that class, logs once, and leaves the feature
 * exactly as it was.
 */
public final class ForeignOreTargets {

    private ForeignOreTargets() {}

    /** Mining Master's configuration: a record of (List of TargetWeightedState, float). */
    private static final String GEM_CONFIG =
            "org.infernalstudios.miningmaster.world.features.config.GemOreFeatureConfig";

    /**
     * Feature config classes whose target list has been read from the mod's own jar and confirmed to
     * be vanilla's substitution table. Class NAMES, so nothing is loaded when the mod is absent.
     */
    private static final Set<String> SUPPORTED = Set.of(
            "blusunrize.immersiveengineering.common.world.IEOreFeature$IEOreFeatureConfig",
            // Mekanism's mekanism:ore. Read from its jar the same way IE's was:
            // ResizableOreFeatureConfig(List<TargetBlockState> targetStates, OreVeinType, IntSupplier
            // size, FloatSupplier discardChanceOnAirExposure) is a record with exactly one target
            // list, and ResizableOreFeature.doPlace iterates that list and BREAKS on the first
            // match before setting the block, which is vanilla's substitution table exactly. So
            // prepending our host-matched entries changes which texture a position gets and nothing
            // about how much ore exists. Its size and air-exposure suppliers read Mekanism's server
            // config and are passed through untouched by withTargets.
            "mekanism.common.world.ResizableOreFeatureConfig",
            // Mining Master's miningmaster:ore_gem_feature. Read from its jar: GemOreFeature.place walks
            // targetStates in order, and on the first test that matches the block at the position it
            // sets one state picked at random from that entry's list, then stops. So it is a
            // substitution table for a single block, and prepending our entries changes which texture
            // the position gets and nothing about how many gems exist. Its entries hold a weighted list
            // where vanilla's hold one state, hence readGems and gemsWithTargets.
            GEM_CONFIG);

    /** Classes that failed once, so the failure is logged once rather than per feature per load. */
    private static final Set<String> FAILED = ConcurrentHashMap.newKeySet();

    /** True if this config is one we know how to read. */
    public static boolean isSupported(FeatureConfiguration config) {
        return config != null && SUPPORTED.contains(config.getClass().getName());
    }

    /**
     * This config's ore targets, or <b>null</b> if they cannot be read.
     *
     * <p>The list is returned as the mod holds it. It is never modified in place: the record's field
     * is final and the list itself is the Codec's immutable one.
     */
    public static List<OreConfiguration.TargetBlockState> read(FeatureConfiguration config) {
        if (!isSupported(config)) {
            return null;
        }
        try {
            if (config.getClass().getName().equals(GEM_CONFIG)) {
                return readGems(config);
            }
            final RecordComponent component = targetComponent(config.getClass());
            if (component == null) {
                return failed(config, "no single List<TargetBlockState> component");
            }
            final Object value = component.getAccessor().invoke(config);
            if (!(value instanceof List<?> list)) {
                return failed(config, "the target component is not a List");
            }
            for (Object element : list) {
                if (!(element instanceof OreConfiguration.TargetBlockState)) {
                    return failed(config, "the target list holds " + element.getClass().getName());
                }
            }
            @SuppressWarnings("unchecked")
            final List<OreConfiguration.TargetBlockState> targets =
                    (List<OreConfiguration.TargetBlockState>) list;
            return targets;
        } catch (Throwable t) {
            return failed(config, t.toString());
        }
    }

    /**
     * A copy of this config carrying {@code targets} in place of its own list, or <b>null</b> if one
     * cannot be built. Every other component is passed through untouched, so IE's vein type - which
     * is what its size, count and height range are read from - survives.
     */
    public static FeatureConfiguration withTargets(FeatureConfiguration config,
                                                   List<OreConfiguration.TargetBlockState> targets) {
        if (!isSupported(config)) {
            return null;
        }
        try {
            final Class<?> type = config.getClass();
            if (type.getName().equals(GEM_CONFIG)) {
                return gemsWithTargets(config, targets);
            }
            final RecordComponent[] components = type.getRecordComponents();
            final RecordComponent target = targetComponent(type);
            if (components == null || target == null) {
                return failed(config, "not a record with a single target list");
            }
            // MATCHED BY NAME, NEVER BY REFERENCE. Class.getRecordComponents() builds a fresh array
            // of fresh RecordComponent objects on every call, so the component returned by
            // targetComponent() is never the same object as its twin in this array and an identity
            // test silently matches nothing. What that produced was worse than a crash: every
            // argument came from the original config, the "replacement" was an exact copy with our
            // targets dropped, the rebind counted as a success, and Immersive Engineering's
            // variants existed, were named, were textured, had loot and generated NOWHERE. Only a
            // client run with IE installed could see it, and one did.
            final String name = target.getName();
            final Class<?>[] parameterTypes = new Class<?>[components.length];
            final Object[] arguments = new Object[components.length];
            for (int i = 0; i < components.length; i++) {
                parameterTypes[i] = components[i].getType();
                arguments[i] = components[i].getName().equals(name)
                        ? targets
                        : components[i].getAccessor().invoke(config);
            }
            final Constructor<?> canonical = type.getDeclaredConstructor(parameterTypes);
            canonical.setAccessible(true);
            final Object rebuilt = canonical.newInstance(arguments);
            if (!(rebuilt instanceof FeatureConfiguration replacement)) {
                return failed(config, "the rebuilt instance is not a FeatureConfiguration");
            }
            // READ IT BACK. A config we rebuild by reflection is exactly the kind of thing that can
            // come back subtly wrong while every step reports success, so the one fact that matters
            // is asserted here rather than assumed: the replacement carries the list we asked for.
            // Sabotage test: match the component by reference again and this fires.
            final List<OreConfiguration.TargetBlockState> back = read(replacement);
            if (back == null || back.size() != targets.size()) {
                return failed(config, "the rebuilt config did not keep the new target list ("
                        + (back == null ? "unreadable" : back.size() + " of " + targets.size()) + ")");
            }
            return replacement;
        } catch (Throwable t) {
            return failed(config, t.toString());
        }
    }

    /**
     * Mining Master's list, flattened: one vanilla target per state of each entry. Its {@code states}
     * field already repeats a state by its weight, so the flat list keeps the odds.
     */
    private static List<OreConfiguration.TargetBlockState> readGems(FeatureConfiguration config)
            throws ReflectiveOperationException {
        final List<OreConfiguration.TargetBlockState> flat = new ArrayList<>();
        for (Object entry : (List<?>) config.getClass().getMethod("targetStates").invoke(config)) {
            final RuleTest test = (RuleTest) entry.getClass().getField("target").get(entry);
            for (Object state : (List<?>) entry.getClass().getField("states").get(entry)) {
                flat.add(OreConfiguration.target(test, (BlockState) state));
            }
        }
        return flat;
    }

    /**
     * The flat list back in Mining Master's shape: one entry per test, weight 1 per listed state, so a test
     * several gems share (its random feature, in a stone our rules added) keeps picking among them. Tests
     * are compared by their encoded form, since each of our rules builds its own object.
     */
    private static FeatureConfiguration gemsWithTargets(FeatureConfiguration config,
                                                        List<OreConfiguration.TargetBlockState> targets)
            throws ReflectiveOperationException {
        final Class<?> type = config.getClass();
        final Class<?> entryType = Class.forName(GEM_CONFIG + "$TargetWeightedState", false, type.getClassLoader());
        final Class<?> weightedType = Class.forName(GEM_CONFIG + "$WeightedState", false, type.getClassLoader());
        final Constructor<?> entry = entryType.getDeclaredConstructor(RuleTest.class, List.class);
        final Constructor<?> weighted = weightedType.getDeclaredConstructor(BlockState.class, int.class);
        entry.setAccessible(true);
        weighted.setAccessible(true);
        final Map<String, List<Object>> byTest = new LinkedHashMap<>();
        final Map<String, RuleTest> tests = new LinkedHashMap<>();
        for (OreConfiguration.TargetBlockState target : targets) {
            final String key = RuleTest.CODEC.encodeStart(JsonOps.INSTANCE, target.target).result()
                    .map(Object::toString).orElseGet(() -> "#" + System.identityHashCode(target.target));
            tests.putIfAbsent(key, target.target);
            byTest.computeIfAbsent(key, k -> new ArrayList<>()).add(weighted.newInstance(target.state, 1));
        }
        final List<Object> entries = new ArrayList<>();
        for (Map.Entry<String, List<Object>> test : byTest.entrySet()) {
            entries.add(entry.newInstance(tests.get(test.getKey()), test.getValue()));
        }
        final Object discard = type.getMethod("discardChanceOnAirExposure").invoke(config);
        final Object rebuilt = type.getDeclaredConstructor(List.class, float.class).newInstance(entries, discard);
        if (!(rebuilt instanceof FeatureConfiguration replacement)) {
            return failed(config, "the rebuilt instance is not a FeatureConfiguration");
        }
        final List<OreConfiguration.TargetBlockState> back = read(replacement);
        if (back == null || back.size() != targets.size()) {
            return failed(config, "the rebuilt config did not keep the new target list");
        }
        return replacement;
    }

    /**
     * The one record component declared as {@code List<TargetBlockState>}, or null if the class has
     * no such component or more than one, in which case which list to edit would be a guess.
     */
    private static RecordComponent targetComponent(Class<?> type) {
        final RecordComponent[] components = type.getRecordComponents();
        if (components == null) {
            return null;
        }
        RecordComponent found = null;
        for (RecordComponent component : components) {
            if (!List.class.isAssignableFrom(component.getType())) {
                continue;
            }
            if (!(component.getGenericType() instanceof ParameterizedType parameterized)) {
                continue;
            }
            final Type[] arguments = parameterized.getActualTypeArguments();
            if (arguments.length == 1 && arguments[0] == OreConfiguration.TargetBlockState.class) {
                if (found != null) {
                    return null;                    // two candidates, so neither is unambiguous
                }
                found = component;
            }
        }
        return found;
    }

    /** Logs once per config class and returns null, so the feature is left untouched. */
    private static <T> T failed(FeatureConfiguration config, String why) {
        final String name = config.getClass().getName();
        if (FAILED.add(name)) {
            Constants.LOG.warn("Worldgen: cannot extend the ore targets of {} ({}). "
                    + "Its variants will not generate; everything else is unaffected.", name, why);
        }
        return null;
    }
}
