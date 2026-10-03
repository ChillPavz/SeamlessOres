package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import net.minecraft.core.RegistryAccess;
import net.minecraft.resources.Identifier;

import java.util.function.UnaryOperator;

/**
 * Turns ore left standing in a Lush Caves clay or moss patch into clay or moss. Worldgen only.
 *
 * <h2>The seam</h2>
 * Lush Caves lay their floor and ceiling patches ({@code clay_with_dripleaves},
 * {@code clay_pool_with_dripleaves}, {@code moss_patch}, {@code moss_patch_ceiling}) after the ores,
 * replacing only the blocks in {@code #lush_ground_replaceable} / {@code #moss_replaceable}, and
 * {@code ore_clay} (Lush Caves only) buries clay blobs after every metal ore. Each skips ore, so iron
 * or coal sits bare in the middle of a clay floor or a moss carpet.
 *
 * <h2>The fix, and what it costs</h2>
 * The four patches are pointed at a tag of ours that is their own tag plus {@code #c:ores}, and
 * {@code ore_clay} gains a first target {@code tag_match c:ores -> clay}. <b>This removes the ore it
 * touches</b>, the deliberate exception to "total ore unchanged", behind its own switch.
 *
 * <p><b>The vanilla tags are never edited.</b> Bone meal on moss uses {@code moss_patch_bonemeal},
 * a different feature on the same {@code #moss_replaceable}; widening that tag would let bone meal
 * eat ore and end the trick of bone-mealing moss to find it. Moss is one block deep, so the ore layer
 * beneath a carpet is still there to find.
 *
 * <p>A feature whose replaceable set a pack has already changed is left alone: our tag only stands
 * in for vanilla's.
 *
 * <h2>Why through the codec</h2>
 * The patch configuration has a different shape on each version this jar serves: a class holding a
 * {@code TagKey} on 26.1.x, a record holding a {@code HolderSet} on 26.2, and the feature itself on
 * 26.3. Their JSON is the same apart from a {@code config} wrapper up to 26.2, so each feature is
 * encoded with its own codec, edited as JSON and decoded again (see
 * {@link WorldgenEra#rewriteFeature}), with no reflection into any of the three.
 */
public final class LushCavesInjector {

    private LushCavesInjector() {
    }

    private static final String MOSS_TAG = "#minecraft:moss_replaceable";
    private static final String CLAY_TAG = "#minecraft:lush_ground_replaceable";
    private static final String OUR_MOSS_TAG = "#" + Constants.MOD_ID + ":lush_moss_replaceable";
    private static final String OUR_CLAY_TAG = "#" + Constants.MOD_ID + ":lush_clay_replaceable";
    private static final String ORES_TAG = "c:ores";

    public static void inject(RegistryAccess registries, WorldgenEra era) {
        if (!SeamlessOresConfig.lushCaves) {
            Constants.LOG.info("Worldgen: Lush Caves clay and moss left as vanilla (switched off)");
            return;
        }
        int changed = 0;
        changed += patch(registries, era, "moss_patch", MOSS_TAG, OUR_MOSS_TAG);
        changed += patch(registries, era, "moss_patch_ceiling", MOSS_TAG, OUR_MOSS_TAG);
        changed += patch(registries, era, "clay_with_dripleaves", CLAY_TAG, OUR_CLAY_TAG);
        changed += patch(registries, era, "clay_pool_with_dripleaves", CLAY_TAG, OUR_CLAY_TAG);
        changed += rewrite(registries, era, "ore_clay", LushCavesInjector::clayTakesOre);
        Constants.LOG.info("Worldgen: Lush Caves clay and moss take stranded ore in {} of 5 features",
                changed);
    }

    private static int patch(RegistryAccess registries, WorldgenEra era, String path, String vanillaTag,
                             String ourTag) {
        return rewrite(registries, era, path, json -> {
            final JsonObject body = body(json, "replaceable");
            if (body == null) {
                return null;
            }
            final JsonElement current = body.get("replaceable");
            if (current.isJsonPrimitive() && ourTag.equals(current.getAsString())) {
                return null;                                    // already ours: a second server start
            }
            if (!current.isJsonPrimitive() || !vanillaTag.equals(current.getAsString())) {
                Constants.LOG.info("Worldgen: minecraft:{} replaces {} rather than {}, left alone",
                        path, current, vanillaTag);
                return null;
            }
            body.addProperty("replaceable", ourTag);
            return json;
        });
    }

    /** Prepends {@code tag_match c:ores -> clay} ahead of vanilla's base-stone target. */
    private static JsonObject clayTakesOre(JsonObject json) {
        final JsonObject body = body(json, "targets");
        if (body == null || !body.get("targets").isJsonArray()) {
            return null;
        }
        final JsonArray targets = body.getAsJsonArray("targets");
        if (targets.isEmpty() || !targets.get(0).isJsonObject()) {
            return null;
        }
        JsonElement clay = null;
        for (JsonElement entry : targets) {
            final JsonObject target = entry.getAsJsonObject().getAsJsonObject("target");
            if (target != null && target.has("tag") && ORES_TAG.equals(target.get("tag").getAsString())) {
                return null;                                    // already ours: a second server start
            }
            final JsonElement state = entry.getAsJsonObject().get("state");
            if (clay == null && isClay(state)) {
                clay = state;
            }
        }
        if (clay == null) {
            Constants.LOG.info("Worldgen: minecraft:ore_clay places no clay, left alone");
            return null;
        }
        final JsonObject test = new JsonObject();
        test.addProperty("predicate_type", "minecraft:tag_match");
        test.addProperty("tag", ORES_TAG);
        final JsonObject first = new JsonObject();
        first.add("state", clay.deepCopy());
        first.add("target", test);
        final JsonArray merged = new JsonArray();
        merged.add(first);
        merged.addAll(targets);
        body.add("targets", merged);
        return json;
    }

    /** A block state as either codec writes it: {@code "minecraft:clay"} or {@code {"Name": ...}}. */
    private static boolean isClay(JsonElement state) {
        if (state instanceof JsonPrimitive primitive) {
            return "minecraft:clay".equals(primitive.getAsString());
        }
        return state instanceof JsonObject object && object.has("Name")
                && "minecraft:clay".equals(object.get("Name").getAsString());
    }

    /** The object holding {@code key}: the root from 26.3, the {@code config} wrapper before it. */
    private static JsonObject body(JsonObject json, String key) {
        if (json.has(key)) {
            return json;
        }
        final JsonElement config = json.get("config");
        return config instanceof JsonObject object && object.has(key) ? object : null;
    }

    private static int rewrite(RegistryAccess registries, WorldgenEra era, String path,
                               UnaryOperator<JsonObject> edit) {
        try {
            return era.rewriteFeature(registries, Identifier.withDefaultNamespace(path), edit) ? 1 : 0;
        } catch (RuntimeException e) {
            // A pack's own feature type that does not round-trip, or a codec change: leave vanilla's
            // seam rather than stop the server.
            Constants.LOG.warn("Worldgen: minecraft:{} could not be rewritten, left as it is", path, e);
            return 0;
        }
    }
}
