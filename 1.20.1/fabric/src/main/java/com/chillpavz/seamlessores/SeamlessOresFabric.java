package com.chillpavz.seamlessores;

import java.lang.reflect.Method;
import com.chillpavz.seamlessores.content.VariantIds;
import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.worldgen.BastionSafeOreFeature;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.registries.Registries;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.RetiredBlocks;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerChunkEvents;
import com.chillpavz.seamlessores.worldgen.CinnabarOreFeature;
import com.chillpavz.seamlessores.worldgen.CinnabarVeins;
import com.chillpavz.seamlessores.worldgen.NetherGemFeature;
import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import com.chillpavz.seamlessores.worldgen.Worldgen;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;

import java.util.List;

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
                BuiltInRegistries.BLOCK::get);
        // Ids 6.0.0 renamed (VariantIds): an old world's blocks and an old inventory's items convert on load.
        addRenamedAliases(BuiltInRegistries.BLOCK, "blocks");
        addRenamedAliases(BuiltInRegistries.ITEM, "items");
        ServerChunkEvents.CHUNK_LOAD.register((level, chunk) ->
                level.getServer().execute(() -> RetiredBlocks.convertChunk(level, chunk)));
        SeamlessOresContent.registerCreativeTabs(
                (id, tab) -> Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, id, tab));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks.
        BastionSafeOreFeature.register((id, feature) ->
                Registry.register(BuiltInRegistries.FEATURE, id, feature));
        NetherGemFeature.register((id, feature) ->
                Registry.register(BuiltInRegistries.FEATURE, id, feature));
        // Vanilla Backport's cinnabar veins: the type is registered always, because the data names it.
        CinnabarOreFeature.register((id, feature) ->
                Registry.register(BuiltInRegistries.FEATURE, id, feature));
        // Each cinnabar variant's mirrored veins, in Vanilla Backport's Sulfur Caves only. A variant
        // exists only with that mod (and its ore's), so this adds nothing without them.
        for (var variant : SeamlessOresContent.variants()) {
            if (variant.host() != HostStone.CINNABAR) {
                continue;
            }
            for (var id : CinnabarVeins.placedFeatures(variant)) {
                BiomeModifications.addFeature(BiomeSelectors.includeByKey(SulfurCaves.BIOME),
                        GenerationStep.Decoration.UNDERGROUND_ORES, ResourceKey.create(Registries.PLACED_FEATURE, id));
            }
        }

        // Ruby and sapphire in basalt deltas. This is the ONE place the mod adds a feature rather
        // than extending one, so it needs the per-loader biome API - NeoForge does the same job with
        // a biome_modifier JSON. Gated on Mythic Upgrades being present, matching the load
        // conditions on the feature JSON itself; without it the blocks do not exist.
        if (net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("mythicupgrades")) {
            for (String gem : new String[]{"ruby", "sapphire"}) {
                ResourceKey<PlacedFeature> key = ResourceKey.create(Registries.PLACED_FEATURE,
                        new ResourceLocation(Constants.MOD_ID, gem + "_deltas"));
                BiomeModifications.addFeature(
                        BiomeSelectors.includeByKey(Biomes.BASALT_DELTAS),
                        GenerationStep.Decoration.UNDERGROUND_ORES, key);
            }
        }

        // CreativeModeTab.Output is protected, so items cannot be added via displayItems from outside
        // vanilla - each loader has its own event for this. itemgroup.v1.ItemGroupEvents /
        // modifyEntriesEvent is the pre-26.1 spelling; it became creativetab.v1.CreativeModeTabEvents
        // / modifyOutputEvent at 26.1. FabricItemGroupEntries implements CreativeModeTab.Output, so
        // the body is unchanged.
        // Two tabs: the game's own rock, and the stones other mods add (registered only with one).
        for (var tab : List.of(SeamlessOresContent.TAB, SeamlessOresContent.MODDED_TAB)) {
            ItemGroupEvents.modifyEntriesEvent(tab).register(output -> {
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
     * Fabric API's registry aliases (FabricRegistry.addAlias) came after the Fabric API this band builds
     * against, so the call is looked up on the registry at run time. With an older Fabric API installed,
     * the ids 6.0.0 renamed do not convert, and that is said once per registry.
     */
    private static void addRenamedAliases(Registry<?> registry, String name) {
        final Method addAlias;
        try {
            addAlias = registry.getClass().getMethod("addAlias", ResourceLocation.class, ResourceLocation.class);
        } catch (NoSuchMethodException e) {
            Constants.LOG.warn("This Fabric API cannot alias registry ids; {} from before Seamless Ores 6.0.0"
                    + " will not convert. Update Fabric API to keep them", name);
            return;
        }
        VariantIds.addAliases((old, now) -> {
            try {
                addAlias.invoke(registry, ResourceLocation.tryParse(old), ResourceLocation.tryParse(now));
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException(e);
            }
        }, id -> registry.containsKey(ResourceLocation.tryParse(id)), name);
    }
}
