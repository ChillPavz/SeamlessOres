package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Makes the seamless variants actually generate, by extending the target list of the ore features
 * that already exist rather than adding features of our own.
 *
 * <h2>Why this preserves vanilla distribution exactly</h2>
 * A vanilla {@code minecraft:ore} feature is a list of (RuleTest -&gt; BlockState) pairs. At every
 * candidate position {@code OreFeature.doPlace} reads the block that is actually there, walks the
 * target list, and places the state of the <b>first</b> matching entry. We only add entries; the
 * feature, its placement, its {@code size} and its {@code discard_chance_on_air_exposure} are
 * untouched. So the same positions become ore, in the same vein shapes, in the same number - a
 * block that becomes granite iron ore was already going to be iron ore. Total ore is unchanged.
 *
 * <p>Two consequences fall out of this for free:
 * <ul>
 *   <li>A vein crossing a granite/stone boundary blends by itself, because the target is chosen per
 *       position from the block actually present. There is no seam to fix.</li>
 *   <li>Any feature that places a given vanilla ore is patched, including the small/buried/large
 *       variants - and features added or overridden by other mods, since we read the live registry.</li>
 * </ul>
 *
 * <h2>Why the targets must be PREPENDED</h2>
 * First match wins. Our {@code block_match granite} and vanilla's {@code tag_match
 * stone_ore_replaceables} both match granite, so if ours came second vanilla would always win and
 * nothing would change.
 *
 * <h2>Why this runs at server start rather than being shipped as JSON</h2>
 * A static override of {@code data/minecraft/worldgen/configured_feature/ore_*.json} would replace
 * those files wholesale, clobbering any other mod or datapack that customises them (worldgen
 * overhaul packs do exactly this). Patching the loaded registry composes with whatever else is
 * present instead of fighting it, and it is what will let runtime-declared modded ores work later.
 */
public final class OreTargetInjector {

    private OreTargetInjector() {}

    /**
     * Patches every ore feature in the given (already datapack-loaded) registries.
     *
     * <p>Safe to call more than once - a variant already present in a feature's target list is
     * skipped, so re-entering on a second world load cannot stack duplicate targets.
     */
    public static void inject(RegistryAccess registries) {

        final Map<OreVariant, Block> ours = SeamlessOresContent.blocks();
        if (ours.isEmpty()) {
            Constants.LOG.warn("No ore variants registered - skipping worldgen injection");
            return;
        }

        final Registry<ConfiguredFeature<?, ?>> features = registries.lookupOrThrow(Registries.CONFIGURED_FEATURE);
        int patchedFeatures = 0;
        int addedTargets = 0;
        int resizedFeatures = 0;

        // listElements() gives Holder.Reference rather than the bare value, which is what lets us
        // swap the entry. Collected first: we rebind while iterating, and streaming lazily over a
        // registry we are mutating is asking for trouble.
        for (Holder.Reference<ConfiguredFeature<?, ?>> holder : features.listElements().toList()) {

            final ConfiguredFeature<?, ?> feature = holder.value();
            if (!(feature.config() instanceof OreConfiguration ore)) {
                continue;
            }

            final List<OreConfiguration.TargetBlockState> extra = new ArrayList<>();
            for (Map.Entry<OreVariant, Block> entry : ours.entrySet()) {
                final OreVariant variant = entry.getKey();
                final Block ourBlock = entry.getValue();

                if (containsBlock(ore.targetStates, ourBlock)) {
                    continue;   // already injected, e.g. a second world load in the same session
                }
                // Config gates GENERATION only, never registration - the blocks exist regardless.
                // Note basalt and blackstone are the balance-relevant ones: they ADD ore, because
                // vanilla's nether features match netherrack only.
                if (!SeamlessOresConfig.isHostEnabled(variant.host().name())) {
                    continue;
                }
                // Each third-party ore has its own toggle. This was hardcoded to the zinc one
                // while zinc was the only modded ore, which would have silently put Mythic Upgrades
                // under a setting labelled "Create".
                if (variant.ore().requiredModId() != null
                        && !SeamlessOresConfig.isModOreEnabled(variant.ore().requiredModId())) {
                    continue;
                }
                // Only patch features that actually place the ore this variant stands in for. That
                // keeps us out of ore_dirt, ore_gravel and anything else that happens to be an
                // OreConfiguration. Resolved here, at server start, where every mod's registry
                // entries exist - a gated variant's equivalent always resolves by construction.
                final Block equivalent = variant.vanillaEquivalent();
                if (equivalent == null || !containsBlock(ore.targetStates, equivalent)) {
                    continue;
                }
                extra.add(OreConfiguration.target(
                        new BlockMatchTest(variant.host().block()), ourBlock.defaultBlockState()));
            }

            // Zinc vein size is independent of everything above: it applies even when the zinc
            // RESTYLE is switched off, because it is about how much zinc exists, not how it looks.
            final int size = resizedIfZinc(ore);

            if (extra.isEmpty() && size == ore.size) {
                continue;
            }

            // PREPEND - see the class javadoc. Ours first, then vanilla's untouched entries.
            final List<OreConfiguration.TargetBlockState> merged = new ArrayList<>(extra);
            merged.addAll(ore.targetStates);

            rebind(holder, feature, new OreConfiguration(
                    List.copyOf(merged), size, ore.discardChanceOnAirExposure), placesNetherHost(extra));

            patchedFeatures++;
            addedTargets += extra.size();
            if (size != ore.size) {
                resizedFeatures++;
                Constants.LOG.info("Worldgen: zinc vein size {} -> {}", ore.size, size);
            }
        }

        Constants.LOG.info("Worldgen: added {} ore targets across {} features ({} resized)",
                addedTargets, patchedFeatures, resizedFeatures);

        // Configured features are only half the story - the large copper/iron veins come from
        // OreVeinifier during noise generation and are invisible to this registry pass.
        VeinOreInjector.inject();
    }

    /**
     * Create's zinc feature, resized - or the feature's own size for everything else.
     *
     * <p>Matched on what the feature actually PLACES rather than on its name, exactly like the
     * target injection above, so a pack that renames or re-declares Create's feature is still
     * handled. See {@link SeamlessOresConfig#zincVeinSize} for why this setting exists at all.
     */
    private static int resizedIfZinc(OreConfiguration ore) {
        if (SeamlessOresConfig.zincVeinSize == SeamlessOresConfig.CREATE_ZINC_VEIN_SIZE) {
            return ore.size;                                    // configured to Create's own value
        }
        for (OreConfiguration.TargetBlockState target : ore.targetStates) {
            final Identifier id = BuiltInRegistries.BLOCK.getKey(target.state.getBlock());
            if (id != null && "create".equals(id.getNamespace()) && id.getPath().endsWith("zinc_ore")) {
                return SeamlessOresConfig.zincVeinSize;
            }
        }
        return ore.size;
    }

    /** Whether any of the targets we are adding sits in a nether host, i.e. basalt or blackstone. */
    private static boolean placesNetherHost(List<OreConfiguration.TargetBlockState> extra) {
        for (OreConfiguration.TargetBlockState target : extra) {
            final Identifier id = BuiltInRegistries.BLOCK.getKey(target.state.getBlock());
            if (id != null && (id.getPath().startsWith("basalt_") || id.getPath().startsWith("blackstone_"))) {
                return true;
            }
        }
        return false;
    }

    private static boolean containsBlock(List<OreConfiguration.TargetBlockState> targets, Block block) {
        for (OreConfiguration.TargetBlockState target : targets) {
            if (target.state.getBlock() == block) {
                return true;
            }
        }
        return false;
    }

    /**
     * Swaps the value behind a registry entry. {@code Holder.Reference#bindValue} is protected in
     * vanilla and is opened by our access widener (Fabric) / access transformer (NeoForge).
     * <p>
     * Rebinding rather than editing {@code OreConfiguration.targetStates} is deliberate: that field
     * is final and holds a Codec-decoded immutable list. Anything already holding this Holder - the
     * placed features that reference it - reads through to the new value automatically.
     */
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void rebind(Holder.Reference<ConfiguredFeature<?, ?>> holder,
                               ConfiguredFeature<?, ?> original,
                               OreConfiguration replacement,
                               boolean needsBastionGuard) {

        // Features that gained a basalt/blackstone target get our stand-in feature instead of
        // minecraft:ore, so they can decline to convert a bastion's own blocks. It takes the same
        // OreConfiguration and delegates straight back to Feature.ORE everywhere else, so nothing
        // about the distribution changes - see BastionSafeOreFeature.
        Feature<?> feature = original.feature();
        if (needsBastionGuard && BastionSafeOreFeature.get() != null && feature == Feature.ORE) {
            feature = BastionSafeOreFeature.get();
        }
        final ConfiguredFeature<?, ?> patched = new ConfiguredFeature((Feature) feature, replacement);
        ((Holder.Reference) holder).bindValue(patched);
    }
}
