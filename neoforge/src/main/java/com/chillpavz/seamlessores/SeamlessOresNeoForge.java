package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.ClothConfigBootstrap;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.platform.Services;
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

        // Cloth Config is OPTIONAL on NeoForge (it has no NeoForge build for this Minecraft
        // version), so every Cloth call is behind this guard and inside ClothConfigBootstrap, which
        // is the only class here that names a Cloth type. Without it the mod runs on
        // SeamlessOresConfig's defaults and has no config screen; worldgen is unaffected, because
        // config gates injection and never registration.
        if (Services.PLATFORM.isModLoaded(ClothConfigBootstrap.MOD_ID)) {
            ClothConfigBootstrap.init(container);
        } else {
            Constants.LOG.info("Cloth Config is not installed, so Seamless Ores is using its default"
                    + " settings and has no config screen. Install Cloth Config to change them.");
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

        // FMLEnvironment.getDist() is a METHOD on 26.x, not a field.
        if (FMLEnvironment.getDist() == Dist.CLIENT) {
            SeamlessOresNeoForgeClient.init();
        }
    }

    private void onServerAboutToStart(ServerAboutToStartEvent event) {

        Worldgen.era().injectOreTargets(event.getServer().registryAccess());
    }

    private void onRegister(RegisterEvent event) {

        // Blocks must be in place before the paired BlockItems are built, and RegisterEvent fires
        // once per registry, so this method is entered twice - guard on which registry we were given.
        event.register(Registries.BLOCK,
                helper -> SeamlessOresContent.registerBlocks(helper::register));
        event.register(Registries.ITEM,
                helper -> SeamlessOresContent.registerItems(helper::register));
        event.register(Registries.CREATIVE_MODE_TAB,
                helper -> SeamlessOresContent.registerCreativeTab(helper::register));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks. Up to
        // 26.2 a feature type is a Feature in FEATURE; from 26.3 it is its codec, in FEATURE_TYPE.
        registerFeatureTypes(event, Worldgen.era());
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void registerFeatureTypes(RegisterEvent event, WorldgenEra era) {
        event.register((ResourceKey) era.featureTypeRegistry(),
                helper -> era.registerFeatureTypes(((RegisterEvent.RegisterHelper<Object>) helper)::register));
    }

    private void onBuildCreativeTabs(BuildCreativeModeTabContentsEvent event) {

        if (!event.getTabKey().equals(SeamlessOresContent.TAB)) {
            return;
        }
        for (var item : SeamlessOresContent.creativeTabItems()) {
            event.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
        }
    }
}
