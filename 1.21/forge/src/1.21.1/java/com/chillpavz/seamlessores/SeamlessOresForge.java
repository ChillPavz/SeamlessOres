package com.chillpavz.seamlessores;

import com.chillpavz.seamlessores.content.VariantIds;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.item.Item;
import net.minecraftforge.registries.ForgeRegistry;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.IForgeRegistry;
import net.minecraftforge.registries.MissingMappingsEvent;
import java.util.List;
import com.chillpavz.seamlessores.config.SeamlessOresConfigData;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.content.RetiredBlocks;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraftforge.event.level.ChunkEvent;
import com.chillpavz.seamlessores.worldgen.BastionSafeOreFeature;
import com.chillpavz.seamlessores.worldgen.CopperDensityInjector;
import com.chillpavz.seamlessores.worldgen.CinnabarOreFeature;
import com.chillpavz.seamlessores.worldgen.NetherGemFeature;
import com.chillpavz.seamlessores.worldgen.Worldgen;
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

        // Game bus: worldgen registries are datapack-loaded per world, so this is the point where
        // they exist and no chunk has been generated yet.
        MinecraftForge.EVENT_BUS.addListener(SeamlessOresForge::onServerAboutToStart);
        // Game bus: a world saved before 6.0.0 that Forge still reports ids missing from (the aliases resolve them).
        MinecraftForge.EVENT_BUS.addListener(SeamlessOresForge::onMissingMappings);
        // A loaded chunk's retired placeholders become their stone, on the server thread after the load.
        MinecraftForge.EVENT_BUS.addListener((ChunkEvent.Load event) -> {
            if (event.getLevel() instanceof ServerLevel level) {
                level.getServer().execute(() -> RetiredBlocks.convertChunk(level, event.getChunk()));
            }
        });

        // Client-only: the screen classes must never be loaded on a dedicated server, so the
        // reference lives behind this guard in a separate class.
        if (FMLEnvironment.dist == Dist.CLIENT) {
            SeamlessOresConfigScreenRegistrar.register();
        }
    }

    private static void onServerAboutToStart(ServerAboutToStartEvent event) {

        // Copper is thinned here as well as by ChunkGeneratorMixin, which this module registers too
        // (MixinConfigs). Forge fires this event before the levels exist, which is before the
        // feature-order table is built, so the rebind is safe from here; that is not true on Fabric.
        // The two passes are idempotent against each other, so copper is thinned once, and this one
        // still does it if the mixin ever fails to apply. It must come BEFORE onServerStarting(),
        // which warns if no thinning ever happened. See CopperDensityInjector.thinAtServerStart.
        CopperDensityInjector.thinAtServerStart(event.getServer().registryAccess());
        Worldgen.onServerStarting(event.getServer().registryAccess());
    }

    private static void onRegister(RegisterEvent event) {

        // Blocks must be in place before the paired BlockItems are built, and RegisterEvent fires
        // once per registry, so this method is entered many times - event.register only runs the
        // callback for the registry it names.
        event.register(Registries.BLOCK,
                helper -> SeamlessOresContent.registerBlocks(helper::register));
        event.register(Registries.ITEM,
                helper -> SeamlessOresContent.registerItems(helper::register));
        // Ids an earlier release registered and this one no longer builds: placeholders that become their stone.
        event.register(Registries.BLOCK, helper -> RetiredBlocks.registerBlocks(helper::register));
        event.register(Registries.ITEM, helper -> RetiredBlocks.registerItems(helper::register, BuiltInRegistries.BLOCK::get));
        // Ids 6.0.0 renamed (VariantIds): an old world's blocks and an old inventory's items convert on load.
        event.register(Registries.BLOCK, helper -> VariantIds.addAliases(
                (old, now) -> ((ForgeRegistry<Block>) ForgeRegistries.BLOCKS).addAlias(ResourceLocation.tryParse(old), ResourceLocation.tryParse(now)),
                id -> ForgeRegistries.BLOCKS.containsKey(ResourceLocation.tryParse(id)), "blocks"));
        event.register(Registries.ITEM, helper -> VariantIds.addAliases(
                (old, now) -> ((ForgeRegistry<Item>) ForgeRegistries.ITEMS).addAlias(ResourceLocation.tryParse(old), ResourceLocation.tryParse(now)),
                id -> ForgeRegistries.ITEMS.containsKey(ResourceLocation.tryParse(id)), "items"));
        event.register(Registries.CREATIVE_MODE_TAB,
                helper -> SeamlessOresContent.registerCreativeTabs(helper::register));
        // Stands in for minecraft:ore on the nether features so bastions keep their own blocks.
        event.register(Registries.FEATURE,
                helper -> BastionSafeOreFeature.register(helper::register));
        event.register(Registries.FEATURE,
                helper -> NetherGemFeature.register(helper::register));
        // Vanilla Backport's cinnabar veins: the type is registered always, because the data names it.
        event.register(Registries.FEATURE,
                helper -> CinnabarOreFeature.register(helper::register));
    }

    private static void onBuildTabContents(BuildCreativeModeTabContentsEvent event) {

        // Two tabs: the game's own rock, and the stones other mods add.
        if (!event.getTabKey().equals(SeamlessOresContent.TAB) && !event.getTabKey().equals(SeamlessOresContent.MODDED_TAB)) {
            return;
        }
        for (var item : SeamlessOresContent.creativeTabItems(event.getTabKey())) {
            event.accept(new ItemStack(item), CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
        }
    }

    /**
     * A world saved before 6.0.0 lists our renamed ids in its registry snapshot. The aliases added at
     * registration already resolve them; this maps any Forge still reports missing to the new block.
     */
    private static void onMissingMappings(MissingMappingsEvent event) {
        remap(event.getMappings(Registries.BLOCK, Constants.MOD_ID), ForgeRegistries.BLOCKS);
        remap(event.getMappings(Registries.ITEM, Constants.MOD_ID), ForgeRegistries.ITEMS);
    }

    private static <T> void remap(List<MissingMappingsEvent.Mapping<T>> mappings, IForgeRegistry<T> registry) {
        for (MissingMappingsEvent.Mapping<T> mapping : mappings) {
            final String now = VariantIds.renamed().get(mapping.getKey().getPath());
            final T target = now == null ? null : registry.getValue(ResourceLocation.tryParse(Constants.MOD_ID + ":" + now));
            if (target != null) {
                mapping.remap(target);
            }
        }
    }
}
