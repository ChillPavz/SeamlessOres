package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.worldgen.BastionSafeOreFeature;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.registries.Registries;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import com.chillpavz.seamlessores.worldgen.NetherGemFeature;
import com.chillpavz.seamlessores.worldgen.OreTargetInjector;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;

public class SeamlessOresFabric implements ModInitializer {

    @Override
    public void onInitialize() {

        SeamlessOres.init();

        // Before worldgen runs, and before anything reads SeamlessOresConfig.
        SeamlessOresConfigData.register();

        SeamlessOresContent.registerBlocks((id, block) -> Registry.register(BuiltInRegistries.BLOCK, id, block));
        SeamlessOresContent.registerItems((id, item) -> Registry.register(BuiltInRegistries.ITEM, id, item));
        SeamlessOresContent.registerCreativeTab(
                (id, tab) -> Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, id, tab));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks.
        BastionSafeOreFeature.register((id, feature) ->
                Registry.register(BuiltInRegistries.FEATURE, id, feature));
        NetherGemFeature.register((id, feature) ->
                Registry.register(BuiltInRegistries.FEATURE, id, feature));

        // Ruby and sapphire in basalt deltas. This is the ONE place the mod adds a feature rather
        // than extending one, so it needs the per-loader biome API - NeoForge does the same job with
        // a biome_modifier JSON. Gated on Mythic Upgrades being present, matching the load
        // conditions on the feature JSON itself; without it the blocks do not exist.
        if (net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("mythicupgrades")) {
            for (String gem : new String[]{"ruby", "sapphire"}) {
                ResourceKey<PlacedFeature> key = ResourceKey.create(Registries.PLACED_FEATURE,
                        Identifier.fromNamespaceAndPath(Constants.MOD_ID, gem + "_deltas"));
                BiomeModifications.addFeature(
                        BiomeSelectors.includeByKey(Biomes.BASALT_DELTAS),
                        GenerationStep.Decoration.UNDERGROUND_ORES, key);
            }
        }

        // CreativeModeTab.Output is protected, so items cannot be added via displayItems from outside
        // vanilla - each loader has its own event for this. On 26.x the Fabric API class is
        // CreativeModeTabEvents; the older ItemGroupEvents is gone.
        CreativeModeTabEvents.modifyOutputEvent(SeamlessOresContent.TAB).register(output -> {
            for (var item : SeamlessOresContent.creativeTabItems()) {
                output.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
            }
        });

        // Worldgen registries are datapack-loaded per world, so the injection has to happen once the
        // server exists and before any chunk is generated.
        ServerLifecycleEvents.SERVER_STARTING.register(
                server -> OreTargetInjector.inject(server.registryAccess()));
    }
}
