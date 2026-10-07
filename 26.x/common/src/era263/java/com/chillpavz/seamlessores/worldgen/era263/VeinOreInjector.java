package com.chillpavz.seamlessores.worldgen.era263;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import com.chillpavz.seamlessores.worldgen.SulfurCaves;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.material.condition.BiomeCondition;
import net.minecraft.world.level.levelgen.material.condition.MaterialCondition;
import net.minecraft.world.level.levelgen.material.condition.NotCondition;
import net.minecraft.world.level.levelgen.material.rule.ConditionRule;
import net.minecraft.world.level.levelgen.material.rule.MaterialRule;
import net.minecraft.world.level.levelgen.material.rule.OreVeinRule;

import java.util.Map;
import java.util.Optional;

/**
 * Fixes the ore placed in the large copper and iron veins.
 *
 * <h2>Why this exists as a separate thing from {@link OreTargetInjector}</h2>
 * There are two ore systems in Minecraft. Features are the familiar one. The other builds the big
 * copper and iron veins during noise generation, before any feature runs. From 26.3 those veins are
 * DATA: {@code worldgen/material_rule/overworld/copper_ore_vein.json} and {@code iron_ore_vein.json},
 * each an {@link OreVeinRule} naming its ore block and its FILLER block:
 *
 * <pre>
 *   copper_ore_vein   ore copper_ore           filler granite
 *   iron_ore_vein     ore deepslate_iron_ore   filler tuff
 * </pre>
 *
 * So vanilla itself builds "copper ore embedded in granite" and "deepslate-textured iron ore embedded
 * in tuff": two of the most visible mismatches in the game, large and dense.
 *
 * <h2>Matched on what the rule places, not on its name</h2>
 * Any ore vein rule whose filler is one of our host stones and whose ore is one our variants stand in
 * for is patched, so a datapack that adds or re-declares veins is handled the same way.
 *
 * <h2>Balance</h2>
 * Unchanged, exactly. Only the block state placed at positions that were already ore changes. The
 * rule is a record, so the entry is rebound to a copy with every other field kept.
 *
 * <p>Material rules are compiled when a level's random state is created, which is after server start,
 * so rebinding here is in time.
 */
public final class VeinOreInjector {

    private VeinOreInjector() {}

    public static void inject(RegistryAccess registries) {

        if (!SeamlessOresConfig.oreVeins) {
            return;
        }
        final Map<OreVariant, Block> ours = SeamlessOresContent.blocks();
        final Registry<MaterialRule> rules = registries.lookupOrThrow(Registries.MATERIAL_RULE);

        for (Holder.Reference<MaterialRule> holder : rules.listElements().toList()) {
            if (!(holder.value() instanceof OreVeinRule vein)) {
                continue;
            }
            final Block ore = vein.oreBlock().getBlock();
            if (SeamlessOresContent.variantOf(ore) != null) {
                continue;   // already patched this session
            }
            final Block filler = vein.fillerBlock().getBlock();
            final Block variant = variantFor(ours, filler, ore);
            if (variant == null) {
                continue;   // a vein in a stone we have no variant for: vanilla's ore is already right
            }
            rebind(holder, new OreVeinRule(variant.defaultBlockState(), vein.rawOreBlock(), vein.fillerBlock(),
                    vein.rawOreChance(), vein.density(), vein.richness(), vein.fillerGap()));
            Constants.LOG.info("Worldgen: {} vein ore -> {}", holder.key().identifier(), variant);
        }
    }

    /**
     * Wraps every ore vein rule so that it does not apply inside the Sulfur Caves. The overworld
     * rule runs the veins BEFORE the biome's sulfur and cinnabar bands, so a vein crossing the caves
     * would otherwise leave its filler, ore and raw blocks standing in them; with the condition the
     * position falls through to the bands like the rest of the cave. Runs after {@link #inject}, so
     * it wraps the restyled rule. See {@link SulfurCaves}.
     */
    public static void keepOutOfSulfurCaves(RegistryAccess registries) {
        if (!SulfurCaves.active()) {
            return;
        }
        final Optional<Holder.Reference<Biome>> biome =
                registries.lookupOrThrow(Registries.BIOME).get(SulfurCaves.BIOME);
        if (biome.isEmpty()) {
            return;
        }
        final MaterialCondition outside = new NotCondition(new BiomeCondition(HolderSet.direct(biome.get())));
        int wrapped = 0;
        for (Holder.Reference<MaterialRule> holder :
                registries.lookupOrThrow(Registries.MATERIAL_RULE).listElements().toList()) {
            if (holder.value() instanceof OreVeinRule vein) {
                rebind(holder, new ConditionRule(outside, vein));
                SulfurCaves.addVein(vein.oreBlock(), vein.rawOreBlock(), vein.fillerBlock());
                wrapped++;
            }
        }
        Constants.LOG.info("Worldgen: {} ore vein rules kept out of the Sulfur Caves", wrapped);
    }

    /** Our variant for this filler stone that stands in for this ore, or null. */
    private static Block variantFor(Map<OreVariant, Block> ours, Block filler, Block ore) {
        for (Map.Entry<OreVariant, Block> entry : ours.entrySet()) {
            final OreVariant variant = entry.getKey();
            if (variant.host().block() == filler && variant.vanillaEquivalent() == ore) {
                return entry.getValue();
            }
        }
        return null;
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void rebind(Holder.Reference<MaterialRule> holder, MaterialRule replacement) {
        ((Holder.Reference) holder).bindValue(replacement);
    }
}
