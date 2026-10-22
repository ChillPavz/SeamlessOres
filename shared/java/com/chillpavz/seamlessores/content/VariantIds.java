package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.function.BiConsumer;
import java.util.function.Predicate;

/**
 * Every variant's block id, and the ids an earlier release shipped that 6.0.0 renamed.
 *
 * <p>6.0.0 names every variant by one rule, {@code <stone>_<ore>_ore} with each half's mod in front by
 * its full id and the game's left out ({@code create_limestone_techreborn_silver_ore}). The generator
 * applies it (shared/tools/placed.py) and writes the result to seamlessores/ids.json
 * (shared/tools/renamed.py), so this side never names a variant itself and the two cannot drift.
 *
 * <p>A world or an inventory from an earlier release still holds the old ids. Each loader registers
 * them as registry aliases of the new ones ({@link #addAliases}), so placed blocks and item stacks
 * convert on load. A shipped id never changes meaning: where the rule would hand one to another block,
 * the pair keeps its shipped id instead.
 *
 * <p>Asked by host name ({@code HostStone.name()}) and ore key ({@code OreType.key()}), the same in
 * every band.
 */
public final class VariantIds {

    private VariantIds() {}

    private static final String FILE = "/seamlessores/ids.json";

    private static Map<String, String> ids;

    private static Map<String, String> renamed;

    private static boolean warned;

    /**
     * The variant's id path. Where the jar's ids.json does not list the pair (the generator and the Java
     * side disagree on what exists), its pre-6.0.0 id {@code legacy}, said once: the block registers,
     * only drawn without its model.
     */
    public static String path(String host, String oreKey, String legacy) {
        load();
        final String path = ids.get(host + "|" + oreKey);
        if (path != null) {
            return path;
        }
        synchronized (VariantIds.class) {
            if (!warned) {
                warned = true;
                Constants.LOG.warn("{} does not list {} with {}; registering it as {} (further misses not logged)",
                        FILE, host, oreKey, legacy);
            }
        }
        return legacy;
    }

    /** Shipped old id path -> its new one. */
    public static Map<String, String> renamed() {
        load();
        return renamed;
    }

    /**
     * Adds an alias (old full id, new full id) through {@code add} for every renamed id whose new block
     * {@code registered} says is there, each fenced off: a loader that refuses one leaves that id
     * unconverted and says so once. Call after our blocks and items are registered.
     */
    public static void addAliases(BiConsumer<String, String> add, Predicate<String> registered, String registry) {
        int added = 0;
        int failed = 0;
        for (Map.Entry<String, String> entry : renamed().entrySet()) {
            final String old = Constants.MOD_ID + ":" + entry.getKey();
            final String now = Constants.MOD_ID + ":" + entry.getValue();
            if (!registered.test(now)) {
                continue;
            }
            try {
                add.accept(old, now);
                added++;
            } catch (RuntimeException e) {
                if (failed++ == 0) {
                    Constants.LOG.warn("Could not map the old id {} to {} in {}; old blocks with that id will be lost",
                            old, now, registry, e);
                }
            }
        }
        if (added + failed > 0) {
            Constants.LOG.info("Mapped {} ids from earlier releases to their new {} ({} failed)", added, registry, failed);
        }
    }

    private static synchronized void load() {
        if (ids != null) {
            return;
        }
        final Map<String, String> byPair = new HashMap<>();
        final Map<String, String> oldToNew = new HashMap<>();
        try (InputStream in = VariantIds.class.getResourceAsStream(FILE)) {
            if (in == null) {
                Constants.LOG.error("{} is missing from the jar; variants take their pre-6.0.0 ids", FILE);
            } else {
                final JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
                for (Map.Entry<String, JsonElement> entry : root.getAsJsonObject("ids").entrySet()) {
                    byPair.put(entry.getKey(), entry.getValue().getAsString());
                }
                for (Map.Entry<String, JsonElement> entry : root.getAsJsonObject("renamed").entrySet()) {
                    oldToNew.put(entry.getKey(), entry.getValue().getAsString());
                }
            }
        } catch (Exception e) {
            Constants.LOG.error("Could not read {}; variants take their pre-6.0.0 ids", FILE, e);
        }
        renamed = Collections.unmodifiableMap(oldToNew);
        ids = Collections.unmodifiableMap(byPair);
    }
}
