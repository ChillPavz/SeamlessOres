package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.OreGeology;
import com.chillpavz.seamlessores.content.OreTier;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.BuiltInRegistries;
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
 * <p>These versions have no all-of rule test, so the added target is a plain match on the stone, and
 * it is only added next to a target that accepts that stone anyway ({@link WorldgenEra#receives}) and
 * that no earlier target of the same list shadows: first match wins, so a target behind another that
 * already takes the stone never places its ore there, and a match on the stone put in front of the list
 * would take that position from the earlier one. Malum's cthonic gold is the case: its feature places
 * cthonic gold on the deepslate replaceables, then plain deepslate gold on the same tag, so its gold
 * never lands in tuff, and its own code reads the FIRST target to decide whether to grow clusters.
 *
 * <h2>Two sources of targets, one pass</h2>
 * <ul>
 *   <li><b>The game's own rock</b>, by tier: granite, diorite and andesite take the stone form of an ore,
 *       tuff the deepslate one. Basalt and blackstone are the deliberate exception: the game's nether
 *       features match netherrack only, so their variants are added wherever a vein reaches them
 *       ({@link OreSite.Add}), which ADDS ore, behind their own switches and dials. A Nether feature
 *       that already takes basalt or blackstone is restyled there like any other.</li>
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
            final Block source = variant.sourceBlock();
            if (source != null) {
                byOre.computeIfAbsent(source, b -> new ArrayList<>()).add(
                        new Pairing(variant, host.block(), placed, tier == OreTier.NETHER, placed != entry.getValue()));
            }
        }

        // The ores each stone swallows: every form becomes the variant, or the stone where it never forms.
        for (HostStone host : HostStone.ALL) {
            final Block stone = host.present() ? host.block() : null;
            if (stone == null) {
                continue;
            }
            for (OreType ore : host.swallows()) {
                final OreVariant variant = new OreVariant(host, ore);
                final Block becomes = host.refused().contains(ore) ? stone : ours.get(variant);
                if (becomes == null || !enabled(host, ore, false)) {
                    continue;
                }
                for (var form : ore.forms()) {
                    BuiltInRegistries.BLOCK.getOptional(form).ifPresent(block -> byOre
                            .computeIfAbsent(block, b -> new ArrayList<>())
                            .add(new Pairing(variant, stone, becomes, false, false)));
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
        int foreign = 0;
        int refusedByOption = 0;
        for (OreSite site : era.oreSites(registries)) {
            final Set<OreSite.Rule> rules = new LinkedHashSet<>();
            final List<OreSite.Target> targets = site.targets();
            OreVariant netherAdded = null;
            int refusedHere = 0;
            for (int i = 0; i < targets.size(); i++) {
                final OreSite.Target target = targets.get(i);
                for (Pairing pairing : byOre.getOrDefault(target.state().getBlock(), List.of())) {
                    final boolean receives = era.receives(target.test(), pairing.stone());
                    if (pairing.adds() && !receives) {
                        rules.add(new OreSite.Add(pairing.stone(), pairing.becomes()));
                        if (netherAdded == null) {
                            netherAdded = pairing.variant();
                        }
                    } else if (receives && !shadowed(era, targets, i, pairing.stone())
                            && rules.add(new OreSite.Receive(target.test(), pairing.stone(), pairing.becomes()))
                            && pairing.byOption()) {
                        refusedHere++;
                    }
                }
            }

            // Read before the rebuild: afterwards the site reports the size it was given.
            final int own = site.size();
            // Zinc vein size is independent of everything above: it applies even when the zinc
            // RESTYLE is switched off, because it is about how much zinc exists, not how it looks.
            // A foreign configuration computes its own size (IE and Mekanism read it from their server
            // config), and no dial has anything to say about it.
            int size = site.foreign() ? own : resizedIfZinc(site);
            // Nether veins are scaled by a percentage of the feature's own size, only on features that
            // gained a basalt or blackstone target, so it cannot touch the overworld. Which dial applies
            // depends on who owns the ore; a feature places a single ore, so the first is representative.
            if (netherAdded != null && !site.foreign()) {
                final int percent = SeamlessOresConfig.netherVeinSizeFor(netherAdded.ore().requiredModId());
                if (percent < 100) {
                    size = Math.max(1, Math.round(size * percent / 100.0f));
                }
            }

            if (rules.isEmpty() && size == own) {
                continue;
            }
            if (!site.rebuildable(NAME) || placesOurs(site)) {
                continue;   // a feature that cannot be rebuilt, or already done (a second world this session)
            }
            site.rebuild(new ArrayList<>(rules), size, netherAdded != null);
            patched++;
            added += rules.size();
            refusedByOption += refusedHere;
            if (site.foreign()) {
                foreign++;
            }
            if (size != own) {
                resized++;
                // Say WHICH dial did it: two independent settings reach this line.
                Constants.LOG.info("Worldgen: {} vein size {} -> {}",
                        netherAdded != null ? "nether" : "zinc", own, size);
            }
        }
        Constants.LOG.info("{}: added {} ore targets across {} features ({} resized, {} not minecraft:ore)",
                NAME, added, patched, resized, foreign);
        if (SeamlessOresConfig.geology) {
            Constants.LOG.info("Worldgen: geology refuses {} of those ore targets (the rock stays rock)",
                    refusedByOption);
        }
    }

    /** Whether a target before index {@code i} already takes {@code stone}: first match wins. */
    private static boolean shadowed(WorldgenEra era, List<OreSite.Target> targets, int i, Block stone) {
        for (int j = 0; j < i; j++) {
            if (era.receives(targets.get(j).test(), stone)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Whether a host's variants of this ore generate: the host's own switch, and the ore's mod's one.
     * {@code addsOre}: some mods put their Nether variants, which ADD ore, behind a switch of their own.
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
            final var id = BuiltInRegistries.BLOCK.getKey(target.state().getBlock());
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
