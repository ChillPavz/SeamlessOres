package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.worldgen.BastionSafeOreFeature;
import com.chillpavz.seamlessores.worldgen.NetherGemFeature;
import com.chillpavz.seamlessores.worldgen.OreTargetInjector;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.event.server.ServerAboutToStartEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.registries.RegisterEvent;

/**
 * Forge entrypoint.
 *
 * <p>Forge 52 predates the EventBus 8 rework used at 1.21.11, so this is closer to the NeoForge
 * module than to the Forge one on that branch: the mod bus comes from
 * {@link FMLJavaModLoadingContext} rather than a {@code BusGroup}, and there is no static
 * {@code BUS} field on events. {@link RegisterEvent} and {@link BuildCreativeModeTabContentsEvent}
 * are BOTH mod-bus here; the latter only moved to the game bus later. Getting the bus wrong fails
 * SILENTLY at runtime, so keep the two groups straight.
 *
 * <p><b>Cloth Config has a Forge build at this version</b> (15.0.140), so config works exactly as it
 * does on Fabric and NeoForge, from the same annotated data class. The hand-written screen the
 * 1.21.11 branch needs does not exist here and must not be copied back.
 */
@Mod(Constants.MOD_ID)
public class SeamlessOresForge {

    public SeamlessOresForge() {

        SeamlessOres.init();

        // Before worldgen runs, and before anything reads SeamlessOresConfig.
        SeamlessOresConfigData.register();

        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        modBus.addListener(SeamlessOresForge::onRegister);
        modBus.addListener(SeamlessOresForge::onBuildTabContents);
        // Forge 1.20.1 cannot gate a loot table on a mod being present, so each supported mod's
        // tables ship as their own built-in datapack and are offered only when it is loaded.
        // See SeamlessOresDataPacks. Mod bus: AddPackFindersEvent implements IModBusEvent.
        modBus.addListener(SeamlessOresDataPacks::addPackFinders);

        // Game bus: worldgen registries are datapack-loaded per world, so this is the point where
        // they exist and no chunk has been generated yet.
        MinecraftForge.EVENT_BUS.addListener(SeamlessOresForge::onServerAboutToStart);

        // Client-only: the screen classes must never be loaded on a dedicated server, so the
        // reference lives behind this guard in a separate class.
        if (FMLEnvironment.dist == Dist.CLIENT) {
            SeamlessOresConfigScreenRegistrar.register();
        }
    }

    private static void onServerAboutToStart(ServerAboutToStartEvent event) {

        OreTargetInjector.inject(event.getServer().registryAccess());
    }

    private static void onRegister(RegisterEvent event) {

        // Blocks must be in place before the paired BlockItems are built, and RegisterEvent fires
        // once per registry, so this method is entered many times - event.register only runs the
        // callback for the registry it names.
        event.register(Registries.BLOCK,
                helper -> SeamlessOresContent.registerBlocks(helper::register));
        event.register(Registries.ITEM,
                helper -> SeamlessOresContent.registerItems(helper::register));
        event.register(Registries.CREATIVE_MODE_TAB,
                helper -> SeamlessOresContent.registerCreativeTab(helper::register));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks.
        event.register(Registries.FEATURE,
                helper -> BastionSafeOreFeature.register(helper::register));
        event.register(Registries.FEATURE,
                helper -> NetherGemFeature.register(helper::register));
    }

    private static void onBuildTabContents(BuildCreativeModeTabContentsEvent event) {

        if (!event.getTabKey().equals(SeamlessOresContent.TAB)) {
            return;
        }
        for (var item : SeamlessOresContent.creativeTabItems()) {
            event.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
        }
    }
}
