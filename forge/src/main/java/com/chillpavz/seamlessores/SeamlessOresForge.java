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
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.event.server.ServerAboutToStartEvent;
import net.minecraftforge.eventbus.api.bus.BusGroup;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.config.ModConfigEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;
import net.minecraftforge.registries.RegisterEvent;

/**
 * Forge entrypoint.
 *
 * <p>Forge 61 is on EventBus 8, which is a different shape from both older Forge and NeoForge:
 * {@code @Mod} takes a NO-ARG constructor, there is no {@code IEventBus} and no
 * {@code FMLJavaModLoadingContext}. Mod-bus events are subscribed through the mod's own
 * {@link BusGroup} via {@code SomeEvent.getBus(group)}, while game-bus events expose a static
 * {@code BUS} field. Tell the two apart by whether the event implements {@code IModBusEvent};
 * getting it wrong fails SILENTLY at runtime.
 *
 * <p>{@link RegisterEvent} and {@link ModConfigEvent} are mod bus; {@link ServerAboutToStartEvent}
 * and {@link BuildCreativeModeTabContentsEvent} are game bus.
 */
@Mod(Constants.MOD_ID)
public class SeamlessOresForge {

    public SeamlessOresForge() {

        SeamlessOres.init();

        ModLoadingContext context = ModLoadingContext.get();
        context.registerConfig(ModConfig.Type.COMMON, SeamlessOresConfigData.SPEC);

        BusGroup modBus = context.getActiveContainer().getModBusGroup();
        // Nothing here is needed before registration - every option gates worldgen, which runs at
        // server start - so Forge's missing STARTUP config type costs this mod nothing.
        ModConfigEvent.Loading.getBus(modBus).addListener(event -> applyIfOurs(event.getConfig()));
        ModConfigEvent.Reloading.getBus(modBus).addListener(event -> applyIfOurs(event.getConfig()));
        RegisterEvent.getBus(modBus).addListener(SeamlessOresForge::onRegister);

        BuildCreativeModeTabContentsEvent.BUS.addListener(SeamlessOresForge::onBuildTabContents);
        // Worldgen registries are datapack-loaded per world, so this is the point where they exist
        // and no chunk has been generated yet.
        ServerAboutToStartEvent.BUS.addListener(SeamlessOresForge::onServerAboutToStart);

        // Client-only: the screen classes must never be loaded on a dedicated server, so the
        // reference lives behind this guard in a separate class. FMLEnvironment.dist is a FIELD on
        // classic Forge; NeoForge 26.x made it the method getDist().
        if (FMLEnvironment.dist == Dist.CLIENT) {
            SeamlessOresConfigScreenRegistrar.register();
        }
    }

    private static void applyIfOurs(ModConfig config) {
        if (config.getSpec() == SeamlessOresConfigData.SPEC) {
            SeamlessOresConfigData.applyToRuntime();
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
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks.
        event.register(Registries.FEATURE,
                helper -> BastionSafeOreFeature.register(helper::register));
        event.register(Registries.FEATURE,
                helper -> NetherGemFeature.register(helper::register));
    }

    private static void onBuildTabContents(BuildCreativeModeTabContentsEvent event) {

        if (!event.getTabKey().equals(SeamlessOresContent.NATURAL_BLOCKS)) {
            return;
        }
        for (var item : SeamlessOresContent.creativeTabItems()) {
            event.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
        }
    }
}
