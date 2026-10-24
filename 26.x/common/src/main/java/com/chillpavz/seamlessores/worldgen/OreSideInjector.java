package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.MatrixAliases;
import com.chillpavz.seamlessores.content.OreGeology;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Makes the variants generate where ore lands in a host stone, by extending the target list of the
 * ore features that already exist rather than adding features of our own.
 *
 * <h2>Why this preserves the ore's own distribution exactly</h2>
 * An ore feature is a list of (rule test -&gt; block) targets. At every candidate position it reads the
 * block that is actually there, walks the list, and places the block of the <b>first</b> target whose
 * test matches. We only add targets; the feature, its placement, its size and its air exposure are
 * untouched. So the same positions become ore, in the same vein shapes, in the same number: a block
 * that becomes granite iron ore was already going to be iron ore.
 *
 * <p>Each added target fires only where the feature would have placed that very ore AND the block is
 * the host stone ({@link OreSite.Receive}), so it inherits every height rule the original has,
 * including 26.3's height-specific tuff split. Before 26.3 there is no all-of test, so the era adds a
 * plain match on the stone, and only next to a target that accepts that stone anyway
 * ({@link WorldgenEra#receives}).
 *
 * <h2>Two sources of targets, one pass</h2>
 * <ul>
 *   <li><b>The game's own rock</b>, by tier: granite, diorite and andesite take the stone form of an ore,
 *       tuff the deepslate one. Basalt and blackstone are the deliberate exception: the game's nether
 *       features match netherrack only, so their variants are added wherever a vein reaches them
 *       ({@link OreSite.Add}), which ADDS ore, behind their own switches and dials. Dripstone and
 *       cinnabar have mechanisms of their own and never get a target here.</li>
 *   <li><b>The ores a stone swallows</b> (see {@link HostStone}): several of the stones other mods place
 *       are in the ore replaceables tags, so any ore feature that runs AFTER such a stone places its
 *       plain ore inside it. Every form of a swallowed ore gets a target, the variant or, where the
 *       fixed geology rule refuses the pair, the stone itself. The stone side
 *       ({@link StoneSideInjector}) covers the opposite order, so the result does not depend on load
 *       order.</li>
 * </ul>
 *
 * <h2>Why this runs at server start rather than being shipped as JSON</h2>
 * A static override of the game's ore features would replace those files wholesale and clobber any
 * other mod or datapack that customises them (worldgen overhaul packs do exactly this). Patching the
 * loaded registry composes with whatever else is present instead.
 */
public final class OreSideInjector {

    static final String NAME = "Ore side";

    private OreSideInjector() {}

    /**
     * What a target placing one ore block gains: {@code becomes} where that ore lands in {@code stone}.
     * {@code adds}: wherever the vein reaches the stone. {@code byOption}: the geology option refused it.
     */
    private record Pairing(OreVariant variant, Block stone, Block becomes, boolean adds, boolean byOption) {}

    /**
     * Patches every ore site in the given (already datapack-loaded) registries. Safe to call more than
     * once: a site that already places one of our blocks is left as it is.
     */
    public static void inject(RegistryAccess registries, WorldgenEra era) {

        final Map<OreVariant, Block> ours = SeamlessOresContent.blocks();
        final Map<Block, List<Pairing>> byOre = new IdentityHashMap<>();

        // The game's own rock, by tier. Config gates GENERATION only, never registration.
        for (Map.Entry<OreVariant, Block> entry : ours.entrySet()) {
            final OreVariant variant = entry.getKey();
            final HostStone host = variant.host();
            final OreTier tier = host.tier();
            if (host.placedBy() != null || !(tier == OreTier.STONE || tier == OreTier.DEEPSLATE || tier == OreTier.NETHER)
                    || host.block() == null || !enabled(host, variant.ore(), tier == OreTier.NETHER)) {
                continue;
            }
            // The geology option may refuse the pair: then the rock stays rock (see OreGeology).
            final Block placed = SeamlessOresConfig.geology && OreGeology.optional(host.name(), variant.ore().key())
                    ? host.block() : entry.getValue();
            pair(byOre, variant.source(),
                    new Pairing(variant, host.block(), placed, tier == OreTier.NETHER, placed != entry.getValue()));
        }

        // The game's own rock: a modded ore the fixed geology rule refuses there has no variant, and where
        // its feature reaches the rock, the rock stays rock (OreGeology). Basalt and blackstone need nothing:
        // their variants ADD ore, so a refused one is simply never added.
        for (HostStone host : HostStone.ALL) {
            final OreTier tier = host.tier();
            if (host.placedBy() != null || !(tier == OreTier.STONE || tier == OreTier.DEEPSLATE) || host.block() == null) {
                continue;
            }
            for (OreType ore : host.rockRefused()) {
                if (!enabled(host, ore, false)) {
                    continue;
                }
                final OreVariant variant = new OreVariant(host, ore);
                final Pairing refusal = new Pairing(variant, host.block(), host.block(), false, false);
                pair(byOre, variant.source(), refusal);
            }
        }

        // The ores each stone swallows: every form becomes the variant, or the stone where it never forms.
        // While the retired Seamless Ores: Matrix is installed it places these under its own ids.
        if (!MatrixAliases.oldModInstalled()) {
            for (HostStone host : HostStone.ALL) {
                final Block stone = host.present() ? host.block() : null;
                if (stone == null) {
                    continue;
                }
                for (OreType ore : host.swallows()) {
                    final OreVariant variant = new OreVariant(host, ore);
                    // The game's own rock that another mod also lays (Create's dripstone): the option's refusals hold too.
                final boolean byOption = host.placedBy() == null && SeamlessOresConfig.geology
                        && OreGeology.optional(host.name(), ore.key());
                final Block becomes = host.refused().contains(ore) || byOption ? stone : ours.get(variant);
                    // A stone in no ore tag (ModdedPairs.addsOre) is given a target of its own wherever a vein reaches
                    // it; an ore it refuses is simply never added.
                    final boolean adds = host.addsOre();
                    if (becomes == null || adds && becomes == stone || !enabled(host, ore, false)) {
                        continue;
                    }
                    for (Identifier form : ore.forms()) {
                        pair(byOre, form, new Pairing(variant, stone, becomes, adds, byOption));
                    }
                }
            }
        }
        if (byOre.isEmpty() && SeamlessOresConfig.zincVeinSize == SeamlessOresConfig.CREATE_ZINC_VEIN_SIZE) {
            Constants.LOG.info("{}: no host stone is installed and switched on, nothing to do", NAME);
            return;
        }

        int patched = 0;
        int added = 0;
        int resized = 0;
        int refusedByOption = 0;
        int refusedFixed = 0;
        for (OreSite site : era.oreSites(registries)) {
            final Set<OreSite.Rule> rules = new LinkedHashSet<>();
            OreVariant netherAdded = null;
            int refusedHere = 0;
            int fixedHere = 0;
            for (OreSite.Target target : site.targets()) {
                for (Pairing pairing : byOre.getOrDefault(target.state().getBlock(), List.of())) {
                    if (pairing.adds()) {
                        rules.add(new OreSite.Add(pairing.stone(), pairing.becomes()));
                        // Only a Nether vein is scaled by the Nether dials; a stone that adds ore elsewhere
                        // (ModdedPairs.addsOre) keeps the feature's own size.
                        if (netherAdded == null && pairing.variant().host().tier() == OreTier.NETHER) {
                            netherAdded = pairing.variant();
                        }
                    } else if (era.receives(target.test(), pairing.stone())
                            && rules.add(new OreSite.Receive(target.test(), pairing.stone(), pairing.becomes()))
                            && pairing.becomes() == pairing.stone()) {
                        if (pairing.byOption()) {
                            refusedHere++;
                        } else if (pairing.variant().host().placedBy() == null) {
                            fixedHere++;
                        }
                    }
                }
            }

            // Read before the rebuild: afterwards the site reports the size it was given.
            final int own = site.size();
            // Zinc vein size is independent of everything above: it applies even when the zinc
            // RESTYLE is switched off, because it is about how much zinc exists, not how it looks.
            int size = resizedIfZinc(site);
            // Nether veins are scaled by a percentage of the feature's own size, only on features that
            // gained a basalt or blackstone target, so it cannot touch the overworld. Which dial applies
            // depends on who owns the ore; a feature places a single ore, so the first is representative.
            if (netherAdded != null) {
                final int percent = SeamlessOresConfig.netherVeinSizeFor(netherAdded.ore().requiredModId());
                if (percent < 100) {
                    size = Math.max(1, Math.round(size * percent / 100.0f));
                }
            }

            if (rules.isEmpty() && size == own) {
                continue;
            }
            if (!site.rebuildable(NAME) || placesOurs(site)) {
                continue;   // a mod's own feature class, or already done (a second world in this session)
            }
            site.rebuild(new ArrayList<>(rules), size, netherAdded != null);
            patched++;
            added += rules.size();
            refusedByOption += refusedHere;
            refusedFixed += fixedHere;
            if (size != own) {
                resized++;
                // Say WHICH dial did it: two independent settings reach this line.
                Constants.LOG.info("Worldgen: {} vein size {} -> {}",
                        netherAdded != null ? "nether" : "zinc", own, size);
            }
        }
        Constants.LOG.info("{}: added {} ore targets across {} ore features ({} resized)", NAME, added, patched, resized);
        Constants.LOG.info("Worldgen: geology keeps the game's own rock in {} ore targets (modded ores, fixed)",
                refusedFixed);
        if (SeamlessOresConfig.geology) {
            Constants.LOG.info("Worldgen: geology refuses {} of those ore targets (the rock stays rock)",
                    refusedByOption);
        }
    }

    private static void pair(Map<Block, List<Pairing>> byOre, Identifier ore, Pairing pairing) {
        BuiltInRegistries.BLOCK.getOptional(ore).ifPresent(block ->
                byOre.computeIfAbsent(block, b -> new ArrayList<>()).add(pairing));
    }

    /**
     * Whether a host's variants of this ore generate: the host's own switch, and the ore's mod's one.
     * {@code addsOre}: Silent's Gems and Tech Reborn put the Nether variants, which ADD ore, behind a
     * switch of their own.
     */
    static boolean enabled(HostStone host, OreType ore, boolean addsOre) {
        return SeamlessOresConfig.isHostEnabled(host.name())
                && (ore.requiredModId() == null || SeamlessOresConfig.isModOreEnabled(ore.requiredModId(), addsOre));
    }

    /**
     * Create's zinc feature, resized, or the site's own size for everything else. Matched on what the
     * feature actually PLACES rather than on its name, so a pack that renames or re-declares Create's
     * feature is still handled. See {@link SeamlessOresConfig#zincVeinSize} for why this setting exists.
     */
    private static int resizedIfZinc(OreSite site) {
        if (SeamlessOresConfig.zincVeinSize == SeamlessOresConfig.CREATE_ZINC_VEIN_SIZE) {
            return site.size();
        }
        for (OreSite.Target target : site.targets()) {
            final Identifier id = BuiltInRegistries.BLOCK.getKey(target.state().getBlock());
            if ("create".equals(id.getNamespace()) && id.getPath().endsWith("zinc_ore")) {
                return SeamlessOresConfig.zincVeinSize;
            }
        }
        return site.size();
    }

    /** Whether a site already places one of our blocks: patched before, by either injector. */
    static boolean placesOurs(OreSite site) {
        for (OreSite.Target target : site.targets()) {
            if (SeamlessOresContent.variantOf(target.state().getBlock()) != null) {
                return true;
            }
        }
        return false;
    }
}
