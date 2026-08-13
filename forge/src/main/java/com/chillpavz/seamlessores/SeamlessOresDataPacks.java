package com.chillpavz.seamlessores;

import net.minecraft.network.chat.Component;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraftforge.event.AddPackFindersEvent;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.resource.PathPackResources;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * Ships each supported mod's loot tables as its own built-in datapack, enabled only when that mod
 * is actually installed.
 *
 * <h2>Why this exists, and why only on Forge</h2>
 * The loot table for a modded variant names that mod's item, so it can only be read when the mod is
 * present. Every other loader can say so in the file itself:
 * <ul>
 *   <li><b>Fabric</b> gates loot tables with {@code fabric:load_conditions} - its resource
 *       conditions module mixes into {@code LootManager} precisely for this.</li>
 *   <li><b>NeoForge and Forge from 1.21</b> gate them too, because loot tables became a datapack
 *       registry and go through the patched {@code RegistryDataLoader}.</li>
 *   <li><b>Forge 1.20.1 does NOT.</b> Grepping Forge 47's own sources, {@code
 *       CraftingHelper.processConditions} is called from {@code RecipeManager}, {@code
 *       ConditionalRecipe} and {@code ConditionalAdvancement} - and nowhere else. Loot tables go
 *       through {@code ForgeHooks.getLootTableDeserializer}, which parses straight to Gson with no
 *       condition check at all.</li>
 * </ul>
 * An unknown item id then throws at parse time ({@code GsonHelper.convertToItem} does
 * {@code orElseThrow}), so each affected table logs {@code Couldn't parse element loot_tables:...}
 * on every world load. With the eight mods this branch supports on Forge that is 167 error lines
 * for a player who installed none of them, which is the normal case. Nothing breaks - the blocks do
 * not exist either - but it reads as a broken mod and would be reported as one.
 *
 * <h2>How it works</h2>
 * The generator writes those tables to {@code packs/<modid>/data/...} inside this jar instead of to
 * the main {@code data/} tree, each with its own {@code pack.mcmeta}. Here they are offered to the
 * game as built-in datapacks, one per mod, and only for mods that are loaded. A pack that is never
 * offered is never read, so an absent mod costs nothing and logs nothing.
 *
 * <p>They are registered as {@code required = true} so the player cannot switch them off and get
 * silently oreless variants; a built-in pack of ours is not a style choice.
 *
 * <p>{@code AddPackFindersEvent} is a MOD BUS event ({@code IModBusEvent}) and Forge fires it for
 * {@code SERVER_DATA} from both {@code ServerPacksSource} and {@code CreateWorldScreen}, so this
 * covers dedicated servers, opening a world, and the world-creation screen alike.
 */
public final class SeamlessOresDataPacks {

    private SeamlessOresDataPacks() {}

    /**
     * Mods whose loot tables ship as their own pack. Must match the generator's
     * CONDITIONAL_LOOT_MODULES_BY_MOD entries that include "forge".
     *
     * <p>A mod listed here with no pack folder in the jar is skipped quietly, which is what makes
     * this safe to keep in step with the generator by hand: the folder's absence is the fact, not
     * this list.
     */
    private static final List<String> PACKED_MODS = List.of(
            "create", "create_new_age", "tfmg", "energizedpower",
            "mythicupgrades", "powah", "silentgear", "silentgems");

    public static void addPackFinders(AddPackFindersEvent event) {
        if (event.getPackType() != PackType.SERVER_DATA) {
            return;
        }
        for (String modId : PACKED_MODS) {
            if (!ModList.get().isLoaded(modId)) {
                continue;
            }
            final Path root = packRoot(modId);
            if (root == null || !Files.isDirectory(root)) {
                Constants.LOG.warn("No built-in datapack for '{}' in this jar - its ore variants "
                        + "will have no loot table. Expected packs/{}/", modId, modId);
                continue;
            }
            final String id = Constants.MOD_ID + "_" + modId;
            final Pack pack = Pack.readMetaAndCreate(
                    "builtin/" + id,
                    Component.literal("Seamless Ores: " + modId),
                    true,                                   // required: not the player's choice
                    unused -> new PathPackResources(id, true, root),
                    PackType.SERVER_DATA,
                    Pack.Position.TOP,
                    PackSource.BUILT_IN);
            if (pack == null) {
                Constants.LOG.warn("Built-in datapack for '{}' has no readable pack.mcmeta", modId);
                continue;
            }
            event.addRepositorySource(consumer -> consumer.accept(pack));
            Constants.LOG.debug("Enabled built-in loot datapack for {}", modId);
        }
    }

    /** The {@code packs/<modid>} directory inside our own mod file, or null if it cannot be found. */
    private static Path packRoot(String modId) {
        try {
            return ModList.get().getModFileById(Constants.MOD_ID).getFile()
                    .findResource("packs/" + modId);
        } catch (RuntimeException failure) {
            Constants.LOG.warn("Could not locate packs/{} inside the mod file", modId, failure);
            return null;
        }
    }
}
