package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.content.VariantIds;
import com.chillpavz.seamlessores.content.MatrixAliases;
import net.fabricmc.fabric.api.event.registry.FabricRegistry;
import net.fabricmc.fabric.api.event.registry.RegistryEntryAddedCallback;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.worldgen.CinnabarVeins;
import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.content.RetiredBlocks;
import com.chillpavz.seamlessores.worldgen.Worldgen;
import com.chillpavz.seamlessores.worldgen.WorldgenEra;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.registries.Registries;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerChunkEvents;
import net.fabricmc.fabric.api.resource.v1.ResourceLoader;
import net.fabricmc.fabric.api.resource.v1.pack.PackActivationType;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.ModContainer;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;

import java.util.Set;
import java.util.TreeSet;

public class SeamlessOresFabric implements ModInitializer {

    @Override
    public void onInitialize() {

        SeamlessOres.init();

        // Before worldgen runs, and before anything reads SeamlessOresConfig.
        SeamlessOresConfigData.register();

        SeamlessOresContent.registerBlocks((id, block) -> Registry.register(BuiltInRegistries.BLOCK, id, block));
        SeamlessOresContent.registerItems((id, item) -> Registry.register(BuiltInRegistries.ITEM, id, item));
        // Ids an earlier release registered and this one no longer builds: placeholders that become their stone.
        RetiredBlocks.registerBlocks((id, block) -> Registry.register(BuiltInRegistries.BLOCK, id, block));
        RetiredBlocks.registerItems((id, item) -> Registry.register(BuiltInRegistries.ITEM, id, item),
                BuiltInRegistries.BLOCK::getValue);
        // Ids 6.0.0 renamed (VariantIds): an old world's blocks and an old inventory's items convert on load.
        VariantIds.addAliases((old, now) -> ((FabricRegistry) BuiltInRegistries.BLOCK).addAlias(Identifier.tryParse(old), Identifier.tryParse(now)),
                id -> BuiltInRegistries.BLOCK.containsKey(Identifier.tryParse(id)), "blocks");
        VariantIds.addAliases((old, now) -> ((FabricRegistry) BuiltInRegistries.ITEM).addAlias(Identifier.tryParse(old), Identifier.tryParse(now)),
                id -> BuiltInRegistries.ITEM.containsKey(Identifier.tryParse(id)), "items");
        ServerChunkEvents.CHUNK_LOAD.register((level, chunk, generated) ->
                level.getServer().execute(() -> RetiredBlocks.convertChunk(level, chunk)));
        SeamlessOresContent.registerCreativeTabs(
                (id, tab) -> Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, id, tab));
        registerMatrixAliases();
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks. Up to
        // 26.2 a feature type is a Feature in FEATURE; from 26.3 it is its codec, in FEATURE_TYPE.
        registerFeatureTypes(Worldgen.era());

        registerModTagPacks();

        // Ruby and sapphire in basalt deltas. This is the ONE place the mod adds a feature rather
        // than extending one, so it needs the per-loader biome API - NeoForge does the same job with
        // a biome_modifier JSON. Gated on Mythic Upgrades being present, matching the load
        // conditions on the feature JSON itself; without it the blocks do not exist.
        if (FabricLoader.getInstance().isModLoaded("mythicupgrades")) {
            for (String gem : new String[]{"ruby", "sapphire"}) {
                ResourceKey<PlacedFeature> key = ResourceKey.create(Registries.PLACED_FEATURE,
                        Identifier.fromNamespaceAndPath(Constants.MOD_ID, gem + "_deltas"));
                BiomeModifications.addFeature(
                        BiomeSelectors.includeByKey(Biomes.BASALT_DELTAS),
                        GenerationStep.Decoration.UNDERGROUND_ORES, key);
            }
        }

        // Cinnabar veins in the Sulfur Caves (26.2 and up), for each cinnabar variant registered here;
        // on 26.1 there are none. NeoForge attaches the same placed features with biome modifiers.
        for (OreVariant variant : SeamlessOresContent.variants()) {
            if (variant.host().tier() != OreTier.CINNABAR) {
                continue;
            }
            // One per feature of the ore it mirrors; see CinnabarVeins.
            for (Identifier id : CinnabarVeins.placedFeatures(variant)) {
                BiomeModifications.addFeature(BiomeSelectors.includeByKey(SulfurCaves.BIOME),
                        GenerationStep.Decoration.UNDERGROUND_ORES,
                        ResourceKey.create(Registries.PLACED_FEATURE, id));
            }
        }

        // CreativeModeTab.Output is protected, so items cannot be added via displayItems from outside
        // vanilla - each loader has its own event for this. On 26.x the Fabric API class is
        // CreativeModeTabEvents; the older ItemGroupEvents is gone.
        // Two tabs: the game's own rock, and the stones other mods add.
        for (var tab : List.of(SeamlessOresContent.TAB, SeamlessOresContent.MODDED_TAB)) {
            CreativeModeTabEvents.modifyOutputEvent(tab).register(output -> {
                for (var item : SeamlessOresContent.creativeTabItems(tab)) {
                    output.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
                }
            });
        }

        // Worldgen registries are datapack-loaded per world, so the injection has to happen once the
        // server exists and before any chunk is generated.
        ServerLifecycleEvents.SERVER_STARTING.register(
                server -> Worldgen.onServerStarting(server.registryAccess()));
    }

    /**
     * Maps the retired Seamless Ores: Matrix ids to ours, blocks and items, so its blocks in a world or
     * an inventory convert instead of vanishing. Skipped while that mod is still installed, since an
     * alias may not shadow a live id. A target from another mod may register after us (Fabric's order
     * between mods is not fixed), so that alias waits for its block; Fabric only warns about a missing
     * target, but it would warn once per variant.
     */
    private static void registerMatrixAliases() {
        if (MatrixAliases.oldModInstalled()) {
            return;
        }
        final List<MatrixAliases.Alias> now = new ArrayList<>();
        final Map<Identifier, List<MatrixAliases.Alias>> later = new HashMap<>();
        for (MatrixAliases.Alias alias : MatrixAliases.all()) {
            // Both: a mod may register its blocks well before their items (Create does).
            if (BuiltInRegistries.BLOCK.containsKey(alias.target()) && BuiltInRegistries.ITEM.containsKey(alias.target())) {
                now.add(alias);
            } else {
                later.computeIfAbsent(alias.target(), id -> new ArrayList<>()).add(alias);
            }
        }
        addMatrixAliases(now);
        if (!later.isEmpty()) {
            RegistryEntryAddedCallback.event(BuiltInRegistries.ITEM).register((rawId, id, item) -> {
                // A block's item registers after the block, so both aliases can go in together.
                final List<MatrixAliases.Alias> waiting = later.remove(id);
                if (waiting != null) {
                    addMatrixAliases(waiting);
                }
            });
        }
    }

    private static void addMatrixAliases(List<MatrixAliases.Alias> aliases) {
        if (aliases.isEmpty()) {
            return;
        }
        MatrixAliases.addAll(aliases, ((FabricRegistry) BuiltInRegistries.BLOCK)::addAlias, "blocks");
        MatrixAliases.addAll(aliases, ((FabricRegistry) BuiltInRegistries.ITEM)::addAlias, "items");
    }

    @SuppressWarnings("unchecked")
    private static void registerFeatureTypes(WorldgenEra era) {
        final Registry<Object> registry = (Registry<Object>) era.builtInFeatureTypes();
        if (registry != null) {
            era.registerFeatureTypes((id, type) -> Registry.register(registry, id, type));
        }
    }

    /**
     * Enables each supported mod's c:ores/&lt;material&gt; tag entries only when that mod is loaded.
     *
     * <p>Fabric's {@code tags_populated} resource condition counts a tag as populated as soon as any
     * file names it, even when every entry in it is optional and absent. A tag that only this mod
     * fills, such as c:ores/nickel for another mod's nickel variants, would therefore let recipes
     * gated on it load in a world without that mod, with an ingredient that matches nothing, and some
     * mods crash on those. Fabric applies no resource conditions to tag files, so each mod's entries
     * ship in a built-in data pack of their own, {@code resourcepacks/<modid>/} in this jar, and only
     * the packs of mods that are actually loaded are registered here. Always enabled, so worlds
     * created before this change pick them up too.
     */
    private static void registerModTagPacks() {
        final ModContainer self = FabricLoader.getInstance().getModContainer(Constants.MOD_ID).orElse(null);
        if (self == null) {
            Constants.LOG.error("Seamless Ores cannot find its own mod container, so no modded ore tags are loaded");
            return;
        }
        final Set<String> mods = new TreeSet<>();
        for (OreType ore : OreType.ALL) {
            if (ore.requiredModId() != null) {
                mods.add(ore.requiredModId());
            }
        }
        for (String modId : mods) {
            if (!FabricLoader.getInstance().isModLoaded(modId) || self.findPath("resourcepacks/" + modId).isEmpty()) {
                continue;
            }
            final String name = FabricLoader.getInstance().getModContainer(modId)
                    .map(container -> container.getMetadata().getName()).orElse(modId);
            if (!ResourceLoader.registerBuiltinPack(
                    Identifier.fromNamespaceAndPath(Constants.MOD_ID, modId), self,
                    Component.literal("Seamless Ores: " + name + " ore tags"),
                    PackActivationType.ALWAYS_ENABLED)) {
                Constants.LOG.warn("Could not register the {} ore tag pack, so its variants miss their c:ores tags", name);
            }
        }
    }
}
