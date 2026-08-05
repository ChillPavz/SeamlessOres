package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.config.SeamlessOresConfigScreen;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.worldgen.BastionSafeOreFeature;
import com.chillpavz.seamlessores.worldgen.OreTargetInjector;
import net.minecraft.core.registries.Registries;
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

        // Before worldgen runs, and before anything reads SeamlessOresConfig.
        SeamlessOresConfigData.register();

        // The config SCREEN is client-only and lives in its own class, so the server never loads a
        // class that references GUI types. FMLEnvironment.getDist() is a METHOD on 26.x, not a field.
        if (FMLEnvironment.getDist() == Dist.CLIENT) {
            SeamlessOresConfigScreen.register(container);
        }

        eventBus.addListener(this::onRegister);
        // BuildCreativeModeTabContentsEvent implements IModBusEvent, so it belongs on the MOD bus.
        // Putting a mod-bus event on the game bus (or vice versa) fails SILENTLY at runtime.
        eventBus.addListener(this::onBuildCreativeTabs);

        // ServerAboutToStartEvent is a GAME bus event (it does not implement IModBusEvent), so it
        // goes on NeoForge.EVENT_BUS, not the mod bus handed to this constructor. Worldgen
        // registries are datapack-loaded per world, so this is the point where they exist and no
        // chunk has been generated yet.
        NeoForge.EVENT_BUS.addListener(this::onServerAboutToStart);
    }

    private void onServerAboutToStart(ServerAboutToStartEvent event) {

        OreTargetInjector.inject(event.getServer().registryAccess());
    }

    private void onRegister(RegisterEvent event) {

        // Blocks must be in place before the paired BlockItems are built, and RegisterEvent fires
        // once per registry, so this method is entered twice - guard on which registry we were given.
        event.register(Registries.BLOCK,
                helper -> SeamlessOresContent.registerBlocks(helper::register));
        event.register(Registries.ITEM,
                helper -> SeamlessOresContent.registerItems(helper::register));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks.
        event.register(Registries.FEATURE,
                helper -> BastionSafeOreFeature.register(helper::register));
    }

    private void onBuildCreativeTabs(BuildCreativeModeTabContentsEvent event) {

        if (!event.getTabKey().equals(SeamlessOresContent.NATURAL_BLOCKS)) {
            return;
        }
        for (var item : SeamlessOresContent.creativeTabItems()) {
            event.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
        }
    }
}
