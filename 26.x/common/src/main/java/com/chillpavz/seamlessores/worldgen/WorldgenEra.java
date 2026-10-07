package com.chillpavz.seamlessores.worldgen;

import com.google.gson.JsonObject;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.placement.CountPlacement;

import java.util.function.BiConsumer;
import java.util.function.UnaryOperator;

/**
 * The worldgen code whose Minecraft API changed shape at 26.3, behind one interface.
 *
 * <p>Up to 26.2 an ore feature is a {@code Feature} instance configured by a
 * {@code ConfiguredFeature}, the large veins are hard-coded in {@code OreVeinifier}, and
 * {@code CountPlacement} keeps its count in a field. From 26.3 a feature type is a codec, ore features
 * are data in {@code Registries.FEATURE}, veins are material rules, and the count is a record
 * accessor. Each side lives in its own era folder ({@code src/era261}, {@code src/era263}) and is
 * loaded by name, so one jar carries both and links only the one that matches the running game.
 */
public interface WorldgenEra {

    /** For the log line, e.g. {@code Era263}. */
    String name();

    /** The registry our two feature types go into: {@code FEATURE} up to 26.2, {@code FEATURE_TYPE} from 26.3. */
    ResourceKey<? extends Registry<?>> featureTypeRegistry();

    /** The same registry, as the built-in instance (Fabric registers into it directly); null for none. */
    Registry<?> builtInFeatureTypes();

    /** Hands over the bastion-safe ore and nether gem feature types, whatever their era's form. */
    void registerFeatureTypes(BiConsumer<Identifier, Object> sink);

    /** Adds the variant targets to every ore feature, then restyles the large veins. Server start. */
    void injectOreTargets(RegistryAccess registries);

    /** The upper bound of a count placement's provider, or -1 when it cannot be read. */
    int maxCount(CountPlacement placement);

    /**
     * Re-encodes one feature ({@code CONFIGURED_FEATURE} up to 26.2, {@code FEATURE} from 26.3) through
     * its own codec, hands the JSON to {@code edit}, and decodes and rebinds the result. {@code edit}
     * returns null to leave the feature as it is. False when the feature is absent or unchanged.
     */
    boolean rewriteFeature(RegistryAccess registries, Identifier id, UnaryOperator<JsonObject> edit);
}
