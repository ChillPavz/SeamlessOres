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
import java.util.List;
import java.util.Map;

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

    /** Runs at server start, alongside the ore target injection, before any chunk is generated. */
    public static void inject(RegistryAccess registries) {

        final Registry<PlacedFeature> placed = registries.registryOrThrow(Registries.PLACED_FEATURE);
        int changed = 0;

        for (Holder.Reference<PlacedFeature> holder : placed.holders().toList()) {
            final ResourceLocation id = holder.key().location();
            if (!"minecraft".equals(id.getNamespace())) {
                continue;
            }
            final java.util.function.IntSupplier dial = SCALED.get(id.getPath());
            if (dial == null) {
                continue;
            }
            final int percent = dial.getAsInt();
            if (percent >= 100) {
                continue;               // exact no-op: nothing is rebound
            }

            final PlacedFeature feature = holder.value();
            final List<PlacementModifier> rebuilt = new ArrayList<>(feature.placement().size());
            boolean scaled = false;

            for (PlacementModifier modifier : feature.placement()) {
                if (modifier instanceof CountPlacement counted) {
                    // SCALE what is actually there rather than writing a number of our own: a
                    // datapack may already have changed vanilla's 16, and overwriting that would
                    // silently undo it. Both bounds are read so a non-constant provider still
                    // scales sensibly; vanilla's is a constant, so min == max == 16.
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
                continue;
            }
            // Same mechanism as the ore target injection: rebind the registry entry rather than
            // mutate a record's final list. Anything already holding this Holder - the biome
            // feature lists - reads through to the new value.
            ((Holder.Reference<PlacedFeature>) holder)
                    .bindValue(new PlacedFeature(feature.feature(), List.copyOf(rebuilt)));
            changed++;
        }

        if (changed > 0) {
            Constants.LOG.info("Worldgen: thinned {} copper feature(s)", changed);
        }
    }
}
