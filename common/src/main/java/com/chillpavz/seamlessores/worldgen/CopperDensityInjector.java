package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.levelgen.placement.CountPlacement;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.levelgen.placement.PlacementModifier;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

/**
 * Thins vanilla's copper, which is the one place this mod changes overworld ore AMOUNTS.
 *
 * <h2>Why copper needs this at all</h2>
 * Read out of the 1.20.1 client jar, vanilla runs copper through two separate placed features:
 * <ul>
 *   <li>{@code ore_copper} -&gt; {@code ore_copper_small}: 16 attempts per chunk at size 10, in
 *       <b>every biome</b>.</li>
 *   <li>{@code ore_copper_large}: 16 attempts per chunk at size 20, in <b>dripstone caves and
 *       nowhere else</b> - one biome of sixty-four.</li>
 * </ul>
 * Dripstone caves therefore get both, and the extra sixteen veins are double size, which works out
 * at roughly three times the copper of any other biome. That is why they read as solid copper, and
 * it is vanilla behaviour rather than anything this mod does.
 *
 * <p>The mod does make it <i>look</i> worse though, and honestly so: {@code OreVeinifier} packs the
 * big copper veins with GRANITE filler, so once our variants restyle that ore to match, a vein stops
 * reading as scattered blobs in granite and starts reading as one continuous mass. Same count, same
 * positions, far more visible.
 *
 * <h2>Why count and not size</h2>
 * Same reasoning as {@code netherOreRarity}: fewer veins keeps each one worth mining out, whereas
 * shrinking every vein makes every find unsatisfying.
 *
 * <h2>This is NOT a restyle, and it is the only overworld setting that is not</h2>
 * Every other overworld toggle in this mod changes how ore looks. These two change how much there
 * is, so they belong on the store page beside {@code netherVeinSize} and {@code zincVeinSize}.
 * Setting either to 100 is an exact no-op - the feature is not rebound at all.
 */
public final class CopperDensityInjector {

    private CopperDensityInjector() {}

    /**
     * The two features, by registry key, and the dial that governs each.
     *
     * <p>Matched on the KEY here rather than on what the feature places, which is the opposite of
     * what {@link OreTargetInjector} does and is deliberate. Both of these place the same block, so
     * "what does it place" cannot tell them apart: the only thing that distinguishes ordinary copper
     * from the dripstone-only large veins is which feature it is. They are vanilla features with
     * stable ids, and a pack that re-declares them under its own name is opting out, which is the
     * right outcome for a setting that edits vanilla's numbers.
     */
    private static final Map<String, java.util.function.IntSupplier> SCALED = Map.of(
            "ore_copper", () -> SeamlessOresConfig.overworldCopper,
            "ore_copper_large", () -> SeamlessOresConfig.dripstoneCopper);

    /**
     * Placed features already thinned, held weakly and by IDENTITY.
     *
     * <p>The pass runs once per world load, so without this a second load in the same session would
     * read the count it just wrote and thin it again: 16 -> 12 -> 9. Identity rather than equality
     * because two separate loads legitimately produce equal-valued features that still both need
     * thinning, and weak because the worldgen registries are rebuilt per world and the old holders
     * must be collectable.
     */
    private static final Set<PlacedFeature> ALREADY_THINNED =
            Collections.newSetFromMap(new WeakHashMap<>());

    /** True once this has actually rebound something, so a dial that stopped working is visible. */
    private static volatile boolean ranAtLeastOnce = false;

    /**
     * Thins copper at server start, from {@link OreTargetInjector#inject}.
     *
     * <p><b>Why server start is the right moment AT THIS VERSION, and a mixin is not.</b>
     * Thinning rebinds a registry entry to a NEW {@code PlacedFeature} instance, which is only safe
     * while nothing has indexed the old one. What indexes them is {@code FeatureSorter}, through
     * {@code ChunkGenerator.featuresPerStep}.
     *
     * <p>At 1.20.1 that field is a {@code Suppliers.memoize(...)} built in the constructor, and the
     * ONLY thing that reads it is {@code applyBiomeDecoration}. Read out of the 1.20.1 client jar:
     * one {@code getfield} of {@code featuresPerStep}, inside that method. So the table is built at
     * the first chunk decoration, which is always after the server-start hook, and a rebind here is
     * seen by the table rather than missed by it.
     *
     * <p><b>1.20.1 has no {@code ChunkGenerator.validate()} at all.</b> That method, which exists
     * only to force the supplier during level load, arrives later; on the branches that have it the
     * table is built BEFORE server start and copper must be thinned from a mixin at its head, or
     * chunk decoration dies on {@code IndexOutOfBoundsException: Index -1}. Both halves were
     * measured, not reasoned: 4.0.0 crashes on 1.21.4 and 1.21.1 Fabric and does not crash here,
     * with 25 freshly decorated chunks in the same harness run. And 4.0.1's mixin, ported down to
     * this branch, could not apply: its target does not exist, which on Fabric is a hard crash at
     * launch and on Forge a silent no-op. <b>Do not port that mixin back to this branch.</b> See
     * the maintainer notes on the copper-thinning crash.
     */
    public static void thinAtServerStart(RegistryAccess registries) {

        final Registry<PlacedFeature> placed = registries.registryOrThrow(Registries.PLACED_FEATURE);
        int changed = 0;

        // The registry rather than each biome's list: every biome reads its features through these
        // same holders, so one pass covers every dimension, and a NeoForge biome modifier that
        // replaced a biome's feature list still reads through to the value rebound here.
        for (Holder.Reference<PlacedFeature> holder : placed.holders().toList()) {
            if (thin(holder)) {
                changed++;
            }
        }

        if (changed > 0) {
            ranAtLeastOnce = true;
            Constants.LOG.info("Worldgen: thinned {} copper feature(s)", changed);
        }
    }

    /** Rebinds one holder if it is a copper feature that a dial actually changes. False otherwise. */
    private static boolean thin(Holder<PlacedFeature> holder) {

        // A biome can hold an inline feature with no registry key; those are not vanilla's copper.
        if (!(holder instanceof Holder.Reference<PlacedFeature> reference)) {
            return false;
        }
        final ResourceLocation id = reference.key().location();
        if (!"minecraft".equals(id.getNamespace())) {
            return false;
        }
        final java.util.function.IntSupplier dial = SCALED.get(id.getPath());
        if (dial == null) {
            return false;
        }
        final int percent = dial.getAsInt();
        if (percent >= 100) {
            return false;               // exact no-op: nothing is rebound
        }

        final PlacedFeature feature = reference.value();
        synchronized (ALREADY_THINNED) {
            if (ALREADY_THINNED.contains(feature)) {
                return false;
            }
        }

        final List<PlacementModifier> rebuilt = new ArrayList<>(feature.placement().size());
        boolean scaled = false;

        for (PlacementModifier modifier : feature.placement()) {
            if (modifier instanceof CountPlacement counted) {
                // SCALE what is actually there rather than writing a number of our own: a datapack
                // may already have changed vanilla's 16, and overwriting that would silently undo
                // it. Both bounds are read so a non-constant provider still scales sensibly;
                // vanilla's is a constant, so min == max == 16. getMaxValue became maxInclusive at
                // 26.x. NOTE THE FIELD ACCESS: on this branch CountPlacement is a plain class
                // with a private final IntProvider FIELD opened by the access widener /
                // transformer, and its count(RandomSource, BlockPos) method is something else
                // entirely. It only becomes a record with a count() accessor at 26.3, so copying
                // 26.3's call down here does not compile.
                final int before = counted.count.getMaxValue();
                final int after = Math.max(0, Math.round(before * percent / 100.0F));
                if (after == before) {
                    rebuilt.add(modifier);
                    continue;
                }
                rebuilt.add(CountPlacement.of(after));
                scaled = true;
                Constants.LOG.info("Worldgen: {} vein count {} -> {} ({}%)",
                        id.getPath(), before, after, percent);
            } else {
                rebuilt.add(modifier);
            }
        }

        if (!scaled) {
            return false;
        }

        final PlacedFeature replacement = new PlacedFeature(feature.feature(), List.copyOf(rebuilt));
        synchronized (ALREADY_THINNED) {
            ALREADY_THINNED.add(replacement);
        }
        // Rebind the registry entry rather than mutate a record's final list. Anything already
        // holding this Holder - the biome feature lists - reads through to the new value, and at
        // this version nothing has indexed the old instance yet: the feature-order table is built
        // lazily at the first chunk decoration, after this runs.
        ((Holder.Reference<PlacedFeature>) reference).bindValue(replacement);
        return true;
    }

    /**
     * Warns if the thinning never ran, called from the server-start injection.
     *
     * <p>A dial that quietly stopped working is invisible: the only symptom would be vanilla copper
     * density, which nobody would report as a bug. This is the line that makes it visible. Not an
     * error, because at 100/100 there is genuinely nothing to do. Sabotage test: take the
     * thinAtServerStart call out of OreTargetInjector and the warning fires on the next world load.
     */
    public static void warnIfNeverRan() {
        if (ranAtLeastOnce) {
            return;
        }
        if (SeamlessOresConfig.overworldCopper >= 100 && SeamlessOresConfig.dripstoneCopper >= 100) {
            return;                     // both dials off; nothing was supposed to happen
        }
        Constants.LOG.warn("Worldgen: the copper dials are set to {}% and {}% but no copper feature"
                        + " was thinned, so copper is at vanilla density. Everything else in the mod"
                        + " is unaffected.",
                SeamlessOresConfig.overworldCopper, SeamlessOresConfig.dripstoneCopper);
    }
}
