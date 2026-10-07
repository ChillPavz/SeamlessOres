package com.chillpavz.seamlessores.worldgen.era261;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;

import java.util.function.BiConsumer;

/**
 * A plain ore vein that places only while the cinnabar host is switched on. See
 * {@code OreTier.CINNABAR}: these veins ADD ore to the Sulfur Caves' cinnabar (26.2), so they need a
 * switch, and a data-driven {@code minecraft:ore} cannot read one. Everything else is vanilla's ore
 * feature. Registered on 26.1 as well, where nothing uses it.
 */
public class CinnabarOreFeature extends Feature<OreConfiguration> {

    public static final Identifier ID = Identifier.fromNamespaceAndPath(Constants.MOD_ID, "cinnabar_ore");

    private static CinnabarOreFeature instance;

    public CinnabarOreFeature() {
        super(OreConfiguration.CODEC);
    }

    public static void register(BiConsumer<Identifier, Feature<?>> sink) {
        if (instance == null) {
            instance = new CinnabarOreFeature();
            sink.accept(ID, instance);
        }
    }

    @Override
    public boolean place(FeaturePlaceContext<OreConfiguration> context) {
        // The data attempts each vein at three times the default count; the slider keeps a share.
        return SeamlessOresConfig.isHostEnabled("cinnabar")
                && context.random().nextInt(SeamlessOresConfig.CINNABAR_AMOUNT_MAX) < SeamlessOresConfig.cinnabarAmount
                && Feature.ORE.place(context);
    }
}
