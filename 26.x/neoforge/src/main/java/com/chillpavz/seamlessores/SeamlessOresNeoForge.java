package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.content.MatrixAliases;
import net.minecraft.core.registries.BuiltInRegistries;
import net.neoforged.bus.api.EventPriority;
import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.config.SeamlessOresConfigScreen;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.worldgen.Worldgen;
import com.chillpavz.seamlessores.worldgen.WorldgenEra;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLEnvironment;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import net.neoforged.neoforge.registries.RegisterEvent;

@Mod(Constants.MOD_ID)
public class SeamlessOresNeoForge {

    public SeamlessOresNeoForge(IEventBus eventBus, ModContainer container) {

        SeamlessOres.init();

        // Before worldgen runs, and before anything reads SeamlessOresConfig. Cloth Config is a
        // required dependency on both loaders, so this is the same call as on Fabric.
        SeamlessOresConfigData.register();
        // The Config button is client-only and lives in its own class, so a dedicated server never
        // loads a class that references screen types.
        if (FMLEnvironment.getDist() == Dist.CLIENT) {
            SeamlessOresConfigScreen.register(container);
        }

        eventBus.addListener(this::onRegister);
        // LOWEST: every mod's blocks are in by then, the ores the Matrix aliases may point at included.
        eventBus.addListener(EventPriority.LOWEST, this::onRegisterLast);
        // BuildCreativeModeTabContentsEvent implements IModBusEvent, so it belongs on the MOD bus.
        // Putting a mod-bus event on the game bus (or vice versa) fails SILENTLY at runtime.
        eventBus.addListener(this::onBuildCreativeTabs);

        // ServerAboutToStartEvent is a GAME bus event (it does not implement IModBusEvent), so it
        // goes on NeoForge.EVENT_BUS, not the mod bus handed to this constructor. Worldgen
        // registries are datapack-loaded per world, so this is the point where they exist and no
        // chunk has been generated yet.
        NeoForge.EVENT_BUS.addListener(this::onServerAboutToStart);

        // FMLEnvironment.getDist() is a METHOD on 26.x, not a field.
        if (FMLEnvironment.getDist() == Dist.CLIENT) {
            SeamlessOresNeoForgeClient.init();
        }
    }

    private void onServerAboutToStart(ServerAboutToStartEvent event) {

        Worldgen.onServerStarting(event.getServer().registryAccess());
    }

    private void onRegister(RegisterEvent event) {

        // Blocks must be in place before the paired BlockItems are built, and RegisterEvent fires
        // once per registry, so this method is entered twice - guard on which registry we were given.
        event.register(Registries.BLOCK,
                helper -> SeamlessOresContent.registerBlocks(helper::register));
        event.register(Registries.ITEM,
                helper -> SeamlessOresContent.registerItems(helper::register));
        event.register(Registries.CREATIVE_MODE_TAB,
                helper -> SeamlessOresContent.registerCreativeTabs(helper::register));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks. Up to
        // 26.2 a feature type is a Feature in FEATURE; from 26.3 it is its codec, in FEATURE_TYPE.
        registerFeatureTypes(event, Worldgen.era());
    }

    /**
     * Maps the retired Seamless Ores: Matrix ids to ours, blocks and items, so its blocks in a world or
     * an inventory convert instead of vanishing. Skipped while that mod is still installed, since an
     * alias may not shadow a live id.
     */
    private void onRegisterLast(RegisterEvent event) {
        if (MatrixAliases.oldModInstalled()) {
            return;
        }
        if (event.getRegistryKey().equals(Registries.BLOCK)) {
            MatrixAliases.addAll(MatrixAliases.all(), BuiltInRegistries.BLOCK::addAlias, "blocks");
        } else if (event.getRegistryKey().equals(Registries.ITEM)) {
            MatrixAliases.addAll(MatrixAliases.all(), BuiltInRegistries.ITEM::addAlias, "items");
        }
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void registerFeatureTypes(RegisterEvent event, WorldgenEra era) {
        event.register((ResourceKey) era.featureTypeRegistry(),
                helper -> era.registerFeatureTypes(((RegisterEvent.RegisterHelper<Object>) helper)::register));
    }

    private void onBuildCreativeTabs(BuildCreativeModeTabContentsEvent event) {

        // Two tabs: the game's own rock, and the stones other mods add.
        if (!event.getTabKey().equals(SeamlessOresContent.TAB) && !event.getTabKey().equals(SeamlessOresContent.MODDED_TAB)) {
            return;
        }
        for (var item : SeamlessOresContent.creativeTabItems(event.getTabKey())) {
            event.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
        }
    }
}
