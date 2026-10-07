package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.content.OreType;
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
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
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
        SeamlessOresContent.registerCreativeTab(
                (id, tab) -> Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, id, tab));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks.
        BastionSafeOreFeature.register((id, feature) ->
                Registry.register(BuiltInRegistries.FEATURE, id, feature));
        NetherGemFeature.register((id, feature) ->
                Registry.register(BuiltInRegistries.FEATURE, id, feature));

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

        // CreativeModeTab.Output is protected, so items cannot be added via displayItems from outside
        // vanilla - each loader has its own event for this. This is the ONE Fabric API rename between
        // 1.21.11 and 26.x: the itemgroup.v1.ItemGroupEvents / modifyEntriesEvent pair here becomes
        // creativetab.v1.CreativeModeTabEvents / modifyOutputEvent at 26.1+. FabricItemGroupEntries
        // implements CreativeModeTab.Output, so the body is unchanged.
        ItemGroupEvents.modifyEntriesEvent(SeamlessOresContent.TAB).register(output -> {
            for (var item : SeamlessOresContent.creativeTabItems()) {
                output.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
            }
        });

        // Worldgen registries are datapack-loaded per world, so the injection has to happen once the
        // server exists and before any chunk is generated.
        ServerLifecycleEvents.SERVER_STARTING.register(
                server -> OreTargetInjector.inject(server.registryAccess()));
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
