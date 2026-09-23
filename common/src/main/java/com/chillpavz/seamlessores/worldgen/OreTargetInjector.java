package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.feature.AbstractOreFeature;
import net.minecraft.world.level.levelgen.feature.BlockReplacement;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.OreFeature;
import net.minecraft.world.level.levelgen.feature.ScatteredOreFeature;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockMatchTest;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/**
 * Makes the seamless variants actually generate, by extending the target list of the ore features
 * that already exist rather than adding features of our own.
 *
 * <h2>Why this preserves vanilla distribution exactly</h2>
 * A vanilla ore feature is a list of (RuleTest -&gt; BlockState) replacements. At every candidate
 * position it reads the block that is actually there, walks the list, and places the state of the
 * <b>first</b> replacement whose test matches. We only add replacements; the feature, its placement,
 * its {@code size} and its {@code discard_chance_on_air_exposure} are untouched. So the same positions
 * become ore, in the same vein shapes, in the same number.
 *
 * <h2>Each added replacement is the ORIGINAL test AND the host stone</h2>
 * For every replacement a feature already has, and every variant standing in for the ore it places,
 * we add {@code all_of(original test, block_match host) -> variant}. A variant can therefore only
 * appear exactly where vanilla would have placed that very ore in that very block, whatever the
 * original test says. That matters from 26.3, where vanilla's own targets are height dependent: tuff
 * receives the STONE ore above y=0 and the DEEPSLATE ore below y=8 (the new
 * {@code height_specific_ore_replaceables} tag). Our tuff variants stand in for the deepslate ore, so
 * they appear where vanilla puts deepslate ore in tuff and nowhere else, and a mod whose deepslate
 * target is plain {@code deepslate_ore_replaceables} (which no longer holds tuff) gets no tuff ore,
 * exactly like vanilla.
 *
 * <p>The Nether hosts are the deliberate exception. Vanilla's nether features match netherrack only,
 * so a wrapped test could never match basalt or blackstone; those variants keep a plain
 * {@code block_match host}, which ADDS ore, behind their own config switches and dials.
 *
 * <h2>Why the replacements must be PREPENDED</h2>
 * First match wins. If ours came after vanilla's, vanilla's would always match first.
 *
 * <h2>Why this runs at server start rather than being shipped as JSON</h2>
 * A static override of {@code data/minecraft/worldgen/feature/ore_*.json} would replace those files
 * wholesale and clobber any other mod or datapack that customises them. Patching the loaded registry
 * composes with whatever else is present instead.
 */
public final class OreTargetInjector {

    private OreTargetInjector() {}

    /**
     * Patches every ore feature in the given (already datapack-loaded) registries.
     *
     * <p>Safe to call more than once: a feature that already places one of our blocks is skipped for
     * that block, so re-entering cannot stack duplicate replacements.
     */
    public static void inject(RegistryAccess registries) {

        final Map<OreVariant, Block> ours = SeamlessOresContent.blocks();
        if (ours.isEmpty()) {
            Constants.LOG.warn("No ore variants registered - skipping worldgen injection");
            return;
        }

        // Which enabled variants stand in for each block. Resolved once, here at server start, where
        // every mod's blocks exist. Config gates GENERATION only, never registration.
        final Map<Block, List<OreVariant>> byEquivalent = new IdentityHashMap<>();
        for (OreVariant variant : ours.keySet()) {
            if (!SeamlessOresConfig.isHostEnabled(variant.host().name())) {
                continue;
            }
            // Each third-party ore has its own toggle, and Silent's Gems' nether gems a separate one,
            // because those ADD ore where its overworld gems only restyle.
            if (variant.ore().requiredModId() != null
                    && !SeamlessOresConfig.isModOreEnabled(
                            variant.ore().requiredModId(), variant.host().tier() == OreTier.NETHER)) {
                continue;
            }
            final Block equivalent = variant.vanillaEquivalent();
            if (equivalent != null) {
                byEquivalent.computeIfAbsent(equivalent, block -> new ArrayList<>()).add(variant);
            }
        }

        final Registry<Feature> features = registries.lookupOrThrow(Registries.FEATURE);
        int patchedFeatures = 0;
        int addedTargets = 0;
        int resizedFeatures = 0;

        // Collected first: we rebind while iterating.
        for (Holder.Reference<Feature> holder : features.listElements().toList()) {

            final Feature feature = holder.value();
            if (!(feature instanceof AbstractOreFeature ore)) {
                continue;
            }
            // Only the two vanilla ore classes are rebuilt. A mod's own subclass may carry state or a
            // constructor contract we cannot reproduce, so it is left exactly as it is.
            final Class<?> kind = feature.getClass();
            if (kind != OreFeature.class && kind != ScatteredOreFeature.class) {
                continue;
            }

            final List<BlockReplacement> targets = ore.targetStates();
            final List<BlockReplacement> extra = new ArrayList<>();
            final List<OreVariant> extraVariants = new ArrayList<>();
            for (BlockReplacement target : targets) {
                for (OreVariant variant : byEquivalent.getOrDefault(target.state().getBlock(), List.of())) {
                    final Block ourBlock = ours.get(variant);
                    if (containsBlock(targets, ourBlock)) {
                        continue;   // already injected, e.g. a second world load in the same session
                    }
                    final RuleTest host = new BlockMatchTest(variant.host().block());
                    final RuleTest test = variant.host().tier() == OreTier.NETHER
                            ? host
                            : RuleTest.allOf(target.target(), host);
                    extra.add(new BlockReplacement(test, ourBlock.defaultBlockState()));
                    extraVariants.add(variant);
                }
            }

            // Zinc vein size is independent of everything above: it applies even when the zinc
            // RESTYLE is switched off, because it is about how much zinc exists, not how it looks.
            int size = resizedIfZinc(targets, ore.size());
            // Nether veins get scaled by a percentage of the feature's own size. Applied only to the
            // features that gained a basalt/blackstone target, so it cannot touch the overworld.
            final OreVariant netherAdded = firstNetherVariant(extraVariants);
            if (netherAdded != null) {
                final int percent = SeamlessOresConfig.netherVeinSizeFor(netherAdded.ore().requiredModId());
                if (percent < 100) {
                    size = Math.max(1, Math.round(size * percent / 100.0f));
                }
            }

            if (extra.isEmpty() && size == ore.size()) {
                continue;
            }

            // PREPEND - see the class javadoc. Ours first, then the feature's untouched replacements.
            final List<BlockReplacement> merged = new ArrayList<>(extra);
            merged.addAll(targets);
            rebind(holder, rebuild(kind, List.copyOf(merged), size, ore.discardChanceOnAirExposure(),
                    netherAdded != null));

            patchedFeatures++;
            addedTargets += extra.size();
            if (size != ore.size()) {
                resizedFeatures++;
                Constants.LOG.info("Worldgen: {} vein size {} -> {}",
                        netherAdded != null ? "nether" : "zinc", ore.size(), size);
            }
        }

        Constants.LOG.info("Worldgen: added {} ore targets across {} features ({} resized)",
                addedTargets, patchedFeatures, resizedFeatures);

        // Copper is thinned separately, and NOT from here. It edits placement COUNTS by rebinding
        // a placed feature to a new instance, which has to happen before ChunkGenerator builds its
        // feature-order table or chunk decoration dies on an index of -1. It therefore runs from
        // ChunkGeneratorMixin at the head of validate(); this call only reports a thinning that
        // should have happened and did not. See CopperDensityInjector and ChunkGeneratorMixin.
        CopperDensityInjector.warnIfNeverRan();

        // The large copper and iron veins are material rules, not features, so this pass never sees
        // them. See VeinOreInjector.
        VeinOreInjector.inject(registries);
    }

    /**
     * The same kind of feature with the merged replacements. A feature that gained a Nether host
     * becomes our bastion-safe stand-in, which declines to convert a bastion's own blocks and
     * otherwise places exactly what {@link OreFeature} would.
     */
    private static Feature rebuild(Class<?> kind, List<BlockReplacement> targets, int size, float discard,
                                   boolean needsBastionGuard) {
        if (kind == ScatteredOreFeature.class) {
            return new ScatteredOreFeature(targets, size, discard);
        }
        return needsBastionGuard
                ? new BastionSafeOreFeature(targets, size, discard)
                : new OreFeature(targets, size, discard);
    }

    /**
     * Create's zinc feature, resized - or the feature's own size for everything else.
     *
     * <p>Matched on what the feature actually PLACES rather than on its name, so a pack that renames
     * or re-declares Create's feature is still handled.
     */
    private static int resizedIfZinc(List<BlockReplacement> targets, int size) {
        if (SeamlessOresConfig.zincVeinSize == SeamlessOresConfig.CREATE_ZINC_VEIN_SIZE) {
            return size;
        }
        for (BlockReplacement target : targets) {
            final Identifier id = BuiltInRegistries.BLOCK.getKey(target.state().getBlock());
            if (id != null && "create".equals(id.getNamespace()) && id.getPath().endsWith("zinc_ore")) {
                return SeamlessOresConfig.zincVeinSize;
            }
        }
        return size;
    }

    /**
     * The first variant we are adding that sits in a Nether host, or null if none does. A feature
     * places a single ore, so every Nether target added to it comes from the same mod.
     */
    private static OreVariant firstNetherVariant(List<OreVariant> added) {
        for (OreVariant variant : added) {
            if (variant.host().tier() == OreTier.NETHER) {
                return variant;
            }
        }
        return null;
    }

    private static boolean containsBlock(List<BlockReplacement> targets, Block block) {
        for (BlockReplacement target : targets) {
            if (target.state().getBlock() == block) {
                return true;
            }
        }
        return false;
    }

    /**
     * Swaps the value behind a registry entry. {@code Holder.Reference#bindValue} is protected in
     * vanilla and is opened by our access widener (Fabric) / access transformer (NeoForge). Anything
     * already holding this Holder - the placed features that reference it - reads through to the new
     * value.
     */
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void rebind(Holder.Reference<Feature> holder, Feature replacement) {
        ((Holder.Reference) holder).bindValue(replacement);
    }
}
